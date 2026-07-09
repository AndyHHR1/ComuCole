import logging
import os
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.config import FRONTEND_DIR
from backend.database.session import Base, engine, get_db
from backend.models.user import User, UserRole
from backend.models.task import Task
from backend.models.schemas import ComuColeResponse
from backend.services.docx_processor import extraer_texto_docx
from backend.services.gemini_service import procesar_documento_con_gemini

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ComuCole API",
    description="Backend MVP para procesamiento de documentos escolares con IA.",
    version="0.1.0",
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/procesar-docx", response_model=ComuColeResponse)
async def procesar_docx(archivo: UploadFile = File(...)) -> JSONResponse:
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
async def marcar_revisada(request: Request, db: Session = Depends(get_db)) -> dict[str, bool | int]:
    data = await request.json()
    parent_id = data.get("parent_id", "anon")
    user = db.query(User).filter(User.code == str(parent_id)).first()
    if user and user.role == UserRole.parent:
        user.points = (user.points or 0) + 1
        db.commit()
        db.refresh(user)
        return {"ok": True, "puntos": user.points or 0}
    return {"ok": True, "puntos": 0}


@app.post("/marcar-cumplida")
async def marcar_cumplida(request: Request, db: Session = Depends(get_db)) -> dict[str, bool | int]:
    data = await request.json()
    parent_id = data.get("parent_id", "anon")
    user = db.query(User).filter(User.code == str(parent_id)).first()
    if user and user.role == UserRole.parent:
        user.points = (user.points or 0) + 2
        db.commit()
        db.refresh(user)
        return {"ok": True, "puntos": user.points or 0}
    return {"ok": True, "puntos": 0}


@app.get("/ranking")
async def get_ranking(db: Session = Depends(get_db)) -> dict[str, list[dict[str, int | str]]]:
    padres = db.query(User).filter(User.role == UserRole.parent).all()
    ranking = [
        {"puesto": i + 1, "id": u.code, "puntos": u.points or 0}
        for i, u in enumerate(sorted(padres, key=lambda x: x.points or 0, reverse=True)[:20])
    ]
    return {"ranking": ranking}


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
