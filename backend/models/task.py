from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.database.session import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    año = Column(Integer, nullable=True)
    seccion = Column(String, nullable=True)
    color_aula = Column(String, nullable=True)
    status = Column(String, default="pending")
    points = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
