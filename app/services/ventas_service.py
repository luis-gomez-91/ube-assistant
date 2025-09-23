import requests
from schemas.carreras_schema import Carreras, DataCarreras
from schemas.grupos_schema import Grupos
from schemas.malla_schema import Malla
from schemas.base_schema import Matricular
from config import API_URL
import httpx


async def fetch_carreras() -> Carreras:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}carreras")
        r.raise_for_status()
        data = r.json()
        # print(data)
        return Carreras(**data)


async def fetch_grupos(id_carrera: int):
    response = requests.get(f"{API_URL}grupos/{id_carrera}")
    response.raise_for_status()
    data = response.json()
    grupos_instance = Grupos(**data)
    return grupos_instance

async def fetch_malla(id_carrera: int) -> Malla:
    response = requests.get(f"{API_URL}malla/{id_carrera}")
    response.raise_for_status()
    data = response.json()
    # print(data)
    malla_instance = Malla(**data)
    return malla_instance

async def matricular():
    response = requests.post(f"{API_URL}matricular", json={"aprove": True})
    response.raise_for_status()
    data = response.json()
    malla_instance = Matricular(**data)
    return malla_instance