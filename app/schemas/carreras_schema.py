from .base_schema import Response
from pydantic import BaseModel
from typing import List, Optional
from langgraph.graph import StateGraph, MessagesState


class Precios(BaseModel):
    inscripcion: float = None
    matricula: float = None
    numero_cuotas: int = None
    homologacion: Optional[float] = None

class Carrera(BaseModel):
    id: int
    nombre: str
    sesiones: List[str]
    modalidades: List[str]
    precios: Optional[Precios] = None

class DataCarreras(BaseModel):
    grado: List[Carrera]
    postgrado: List[Carrera]

class Carreras(Response):
    data: DataCarreras
