from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
import enum
from backend.database.session import Base


class UserRole(str, enum.Enum):
    teacher = "teacher"
    parent = "parent"


class Seccion(str, enum.Enum):
    a = "A"
    b = "B"
    c = "C"


class ColorAula(str, enum.Enum):
    rojo = "Rojo"
    azul = "Azul"
    verde = "Verde"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    full_name = Column(String, nullable=True)
    año = Column(Integer, nullable=True)
    seccion = Column(Enum(Seccion), nullable=True)
    color_aula = Column(Enum(ColorAula), nullable=True)
    points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
