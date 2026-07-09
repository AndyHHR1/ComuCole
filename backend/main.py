import logging
import os
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import FRONTEND_DIR
from backend.models.schemas import ComuColeResponse
from backend.services.docx_processor import extraer_texto_docx
from backend.services.gemini_service import procesar_documento_con_gemini

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ComuCole API",
    description="Backend MVP para procesamiento de documentos escolares con IA.",
    version="0.1.0",
)

ranking_store: dict[str, int] = defaultdict(int)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check para monitoreo."""
    return {"status": "ok"}


@app.post("/procesar-docx", response_model=ComuColeResponse)
async def procesar_docx(archivo: UploadFile = File(...)) -> JSONResponse:
    """Procesa un .docx cargado por el docente y devuelve JSON estructurado."""
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
    except RuntimeError as exc:
        logger.exception("Error procesando documento con Gemini")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado procesando documento")
        raise HTTPException(status_code=500, detail=f"Error inesperado: {exc}") from exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@app.post("/marcar-revisada")
async def marcar_revisada(request: Request) -> dict[str, bool | int]:
    """Marca la tarea como revisada y suma 1 punto al ranking."""
    data = await request.json()
    parent_id = data.get("parent_id", "anon")
    ranking_store[parent_id] += 1
    return {"ok": True, "puntos": ranking_store[parent_id]}


@app.post("/marcar-cumplida")
async def marcar_cumplida(request: Request) -> dict[str, bool | int]:
    """Marca la tarea como cumplida y suma 2 puntos al ranking."""
    data = await request.json()
    parent_id = data.get("parent_id", "anon")
    ranking_store[parent_id] += 2
    return {"ok": True, "puntos": ranking_store[parent_id]}


@app.get("/ranking")
async def get_ranking() -> dict[str, list[dict[str, int | str]]]:
    """Obtiene la tabla de posiciones del aula."""
    ordenado = sorted(ranking_store.items(), key=lambda x: x[1], reverse=True)
    return {
        "ranking": [
            {"puesto": i + 1, "id": pid, "puntos": pts}
            for i, (pid, pts) in enumerate(ordenado[:20])
        ]
    }


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
