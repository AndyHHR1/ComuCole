from pydantic import BaseModel, Field


class ComuColeResponse(BaseModel):
    resumen_sesion: str = Field(..., description="Resumen amigable y ejecutivo de la sesión (máximo 2 párrafos)")
    tarea: str = Field(..., description="Instrucción exacta de la tarea para casa")
    materiales: list[str] = Field(default_factory=list, description="Lista de útiles o recursos solicitados")
    semaforo: str = Field(..., description="Clasificación del tiempo: rojo, amarillo o verde")
    categoria: str = Field(..., description="Clasificación del trabajo: cognitivo, manual o psicomotriz")
