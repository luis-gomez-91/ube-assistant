from pydantic import BaseModel
from typing import List, Optional
from app.schemas.base_schema import Response

class Asignatura(BaseModel):
    asignatura: str
    horas: int | float
    creditos: Optional[int] = None

class DataMalla(BaseModel):
    nivel_malla: str
    asignaturas: List[Asignatura]

class Malla(Response):
    data: List[DataMalla]
