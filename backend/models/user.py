from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from backend.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    año = Column(Integer, nullable=True)
    seccion = Column(String, nullable=True)
    color_aula = Column(String, nullable=True)
    points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
