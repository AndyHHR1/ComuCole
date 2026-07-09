import os
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.models.schemas import ComuColeResponse
from backend.services.docx_processor import extraer_texto_docx
from backend.services.gemini_service import procesar_documento_con_gemini

app = FastAPI(
    title="ComuCole API",
    description="Backend MVP para procesamiento de documentos escolares con IA.",
    version="0.1.0",
)

ranking_store = defaultdict(int)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/procesar-docx", response_model=ComuColeResponse)
async def procesar_docx(archivo: UploadFile = File(...)):
    if not archivo.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .docx")

    contenido = await archivo.read()

    tmp_path = Path("/tmp") / f"comucole_{archivo.filename}"
    tmp_path.write_bytes(contenido)

    try:
        texto_crudo = extraer_texto_docx(str(tmp_path))
        if not texto_crudo.strip():
            raise HTTPException(status_code=422, detail="El documento .docx está vacío o no contiene texto.")

        resultado = procesar_documento_con_gemini(texto_crudo)
        return JSONResponse(content=resultado)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@app.post("/marcar-revisada")
async def marcar_revisada(request: Request):
    data = await request.json()
    parent_id = data.get("parent_id", "anon")
    ranking_store[parent_id] += 1
    return {"ok": True, "puntos": ranking_store[parent_id]}


@app.post("/marcar-cumplida")
async def marcar_cumplida(request: Request):
    data = await request.json()
    parent_id = data.get("parent_id", "anon")
    ranking_store[parent_id] += 2
    return {"ok": True, "puntos": ranking_store[parent_id]}


@app.get("/ranking")
async def get_ranking():
    ordenado = sorted(ranking_store.items(), key=lambda x: x[1], reverse=True)
    return {
        "ranking": [
            {"puesto": i + 1, "id": pid, "puntos": pts}
            for i, (pid, pts) in enumerate(ordenado[:20])
        ]
    }


frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
