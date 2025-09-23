from pydantic import BaseModel
from .base_schema import Response
from typing import List

class GrupoData(BaseModel):
    carrera: str
    nombre: str
    fecha_inicio: str
    fecha_fin: str
    capacidad: int
    sesion: str
    modalidad: str
    nivel: str

class Grupos(Response):
    data: List[GrupoData]