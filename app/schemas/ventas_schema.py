from pydantic import BaseModel

class MessageRequest(BaseModel):
    mensaje: str