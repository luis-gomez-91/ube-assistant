from fastapi import APIRouter
from app.schemas.base_schema import Consulta
from app.agents.ventas import get_agent


router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"]
)


@router.post("/chat")
async def chat_con_agente(consulta: Consulta, user_id: str):
    try:
        agent_executor = get_agent(user_id)
        response = await agent_executor.ainvoke({"input": consulta.query})
        return {"respuesta": response["output"]}
    except Exception as e:
        return {"error": str(e)}