from app.schemas.carreras_schema import DataCarreras, Carrera
from openai import OpenAI
import json
from config import TOKEN_LLAMA
from typing import List


def get_id_by_name(carreras: DataCarreras, mensaje: str) -> int | None:
    """
    Extrae el nombre de la carrera de un mensaje y devuelve su ID.
    El modelo de IA actúa como un clasificador.
    """

    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=TOKEN_LLAMA,
    )

    prompts = {}
    for x in carreras.grado:
        prompts[x.id] = x.nombre
    for x in carreras.postgrado:
        prompts[x.id] = x.nombre

    # print(f"PROMPTS: {prompts}")

    classifier_prompt = """
    Eres un clasificador de carreras.
    Tu tarea es extraer el nombre de la carrera del mensaje del usuario y encontrar la coincidencia más cercana en la siguiente lista.
    Si encuentras una coincidencia, responde únicamente con el ID correspondiente en formato JSON.
    Si no hay una coincidencia clara, o si el mensaje no contiene una carrera, responde con el ID 0.
    Lista de carreras:
    {prompts_str}
    
    Responde ÚNICAMENTE en formato JSON, con la llave "id". Ejemplo de respuesta:
    {{"id": 123}}
    """

    prompts_str = json.dumps(prompts, indent=2, ensure_ascii=False)

    messages = [
        {"role": "system", "content": classifier_prompt.format(prompts_str=prompts_str)},
        {"role": "user", "content": f"Mensaje a clasificar: {mensaje}"}
    ]

    try:
        classification = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0 
        )
        
        response_json = json.loads(classification.choices[0].message.content)
        category_id = int(response_json.get("id", None))
        
        return category_id
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error al procesar la respuesta del modelo: {e}")
        return None
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return None
    

def formatear_texto_carreras(carreras: List[Carrera], tipo: str):
    msg = f"**Las carreras de {tipo} son:**\n"

    for carrera in carreras:
        sesiones = ", ".join(carrera.sesiones) if carrera.sesiones else "No disponible"
        modalidades = ", ".join(carrera.modalidades) if carrera.modalidades else "No disponible"

        msg += f"\nNombre de la carrera: {carrera.nombre}."

        if carrera.precios:
            msg += "\n1. Precios de la carrera:"
            msg += f"\n - Inscripcion: {carrera.precios.inscripcion or 'No disponible'}"
            msg += f"\n - Matricula: {carrera.precios.matricula or 'No disponible'}"
            msg += f"\n - Cantidad de cuotas: {carrera.precios.numero_cuotas or 'No disponible'}"
            msg += f"\n - Precio Homologación: {carrera.precios.homologacion or 'No disponible'}"
        
        msg += f"\n2. Sesiones: {sesiones}."
        msg += f"\n3. Modalidades: {modalidades}.\n"

    return msg