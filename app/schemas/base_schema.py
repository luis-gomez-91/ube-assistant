from pydantic import BaseModel


class Response(BaseModel):
    status: str

class Error(Response):
    message: str

class Matricular(Response):
    message: str

class Consulta(BaseModel):
    query: str