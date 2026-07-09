import logging
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.config import FRONTEND_DIR
from backend.database.session import Base, engine, get_db
from backend.models.task import Task
from backend.models.user import User, UserRole
from backend.models.schemas import ComuColeResponse
from backend.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_teacher,
    get_current_parent,
)
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
    import os
    db_url = os.getenv("DATABASE_URL", "NOT_SET")
    logger.info(f"[startup] DATABASE_URL={db_url}")
    Base.metadata.create_all(bind=engine, checkfirst=True)


@app.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "code": current_user.code,
        "role": current_user.role.value,
        "full_name": current_user.full_name,
        "año": current_user.año,
        "seccion": current_user.seccion.value if current_user.seccion else None,
        "color_aula": current_user.color_aula.value if current_user.color_aula else None,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/register")
async def register(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    data = await request.json()

    code = data.get("code")
    password = data.get("password")
    role = data.get("role")
    full_name = data.get("full_name")
    año = data.get("año")
    seccion = data.get("seccion")
    color_aula = data.get("color_aula")

    if not code or not password or not role:
        raise HTTPException(status_code=400, detail="Faltan campos requeridos")

    if role not in ("teacher", "parent"):
        raise HTTPException(status_code=400, detail="Rol inválido")

    existing = db.query(User).filter(User.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="El código ya está registrado")

    user = User(
        code=code,
        password_hash=hash_password(password),
        role=UserRole(role),
        full_name=full_name,
    )

    if role == "parent":
        if año:
            user.año = int(año)
        if seccion:
            user.seccion = Seccion(seccion)
        if color_aula:
            user.color_aula = ColorAula(color_aula)

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "ok": True,
        "user_id": user.id,
        "role": user.role.value,
        "año": user.año,
        "seccion": user.seccion.value if user.seccion else None,
        "color_aula": user.color_aula.value if user.color_aula else None,
    }


@app.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    data = await request.json()

    code = data.get("code")
    password = data.get("password")
    role = data.get("role")

    if not code or not password:
        raise HTTPException(status_code=400, detail="Faltan credenciales")

    user = db.query(User).filter(User.code == code).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if role and user.role.value != role:
        raise HTTPException(
            status_code=403,
            detail=f"Esta cuenta está registrada como {user.role.value}. Usa el perfil correcto.",
        )

    access_token = create_access_token(data={"sub": user.code})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value,
        "full_name": user.full_name,
    }


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
async def marcar_revisada(
    current_user: User = Depends(get_current_parent),
    db: Session = Depends(get_db),
) -> dict[str, bool | int]:
    current_user.points = (current_user.points or 0) + 1
    db.commit()
    db.refresh(current_user)
    return {"ok": True, "puntos": current_user.points or 0}


@app.post("/marcar-cumplida")
async def marcar_cumplida(
    current_user: User = Depends(get_current_parent),
    db: Session = Depends(get_db),
) -> dict[str, bool | int]:
    current_user.points = (current_user.points or 0) + 2
    db.commit()
    db.refresh(current_user)
    return {"ok": True, "puntos": current_user.points or 0}


@app.get("/ranking")
async def get_ranking(db: Session = Depends(get_db)) -> dict[str, list[dict[str, int | str]]]:
    padres = db.query(User).filter(User.role == UserRole.parent).all()
    ranking = [
        {"puesto": i + 1, "id": u.code, "puntos": u.points or 0}
        for i, u in enumerate(sorted(padres, key=lambda x: x.points or 0, reverse=True)[:20])
    ]
    return {"ranking": ranking}


@app.get("/me/tasks")
async def get_my_tasks(
    current_user: User = Depends(get_current_parent),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Task)

    if current_user.año and current_user.seccion and current_user.color_aula:
        query = query.filter(
            (Task.año == current_user.año)
            & (Task.seccion == current_user.seccion)
            & (Task.color_aula == current_user.color_aula)
        )
    else:
        query = query.filter(Task.parent_id == current_user.id)

    tasks = query.all()
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "points": t.points,
                "año": t.año,
                "seccion": t.seccion.value if t.seccion else None,
                "color_aula": t.color_aula.value if t.color_aula else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ]
    }


@app.post("/tasks")
async def create_task(
    request: Request,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
) -> dict:
    data = await request.json()
    title = data.get("title")
    description = data.get("description")
    año = data.get("año")
    seccion = data.get("seccion")
    color_aula = data.get("color_aula")
    file_url = data.get("file_url")

    if not title:
        raise HTTPException(status_code=400, detail="El título es requerido")

    task = Task(
        title=title,
        description=description,
        teacher_id=current_user.id,
        año=int(año) if año else None,
        seccion=seccion,
        color_aula=color_aula,
        file_url=file_url,
        status="pending",
        points=0,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "ok": True,
        "task_id": task.id,
        "title": task.title,
        "description": task.description,
        "año": task.año,
        "seccion": task.seccion.value if task.seccion else None,
        "color_aula": task.color_aula.value if task.color_aula else None,
        "status": task.status,
    }


@app.get("/teacher/tasks")
async def get_teacher_tasks(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
) -> dict:
    tasks = db.query(Task).filter(Task.teacher_id == current_user.id).all()
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "points": t.points,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ]
    }


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
