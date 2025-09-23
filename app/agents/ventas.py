from langchain.agents import tool
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain import hub
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GEMINI_API_KEY
from app.services.ventas_service import fetch_carreras, fetch_malla, fetch_grupos
from app.schemas.carreras_schema import Carreras
from app.utils import formatear_texto_carreras
from langchain_core.beta.runnables.context import Context
from app.utils import get_id_by_name

# clasificador basado en prompts

class CarrerasManager:
    def __init__(self):
        self.carreras: Carreras = None

    async def get_carreras(self) -> Carreras:
        if not self.carreras:
            self.carreras: Carreras = await fetch_carreras()
        return self.carreras

carreras_manager = CarrerasManager()

@tool
async def listar_carreras(nombre_carrera: str = None) -> str:
    """
    Retorna un resumen completo de las carreras de la UBE.
    Retorna informacion de carreras especificas segun se solicita.
    Incluye:
    - Nombre de la carrera
    - Precios
    - Sesiones
    - Modalidades
    """

    carreras: Carreras = await carreras_manager.get_carreras()

    if nombre_carrera:
        id_carrera = get_id_by_name(carreras.data, nombre_carrera)
        if not id_carrera:
            return "Lo siento, no encontré esa carrera en nuestra base de datos. ¿Podrías verificar si está bien escrita o puedo listarte todas las carreras disponibles?"

    grado = formatear_texto_carreras(carreras.data.grado, "grado")
    postgrado = formatear_texto_carreras(carreras.data.postgrado, "postgrado")
    response = f"""{grado}\n\n{postgrado}\nLos IDS usalos para apuntar a otro endpont de ser necesario, no los muestres en la conversacion con el usuario."""
    return response

@tool
async def listar_malla(nombre_carrera: str) -> str:
    """
        Esta tool se activa cuando el usuario pregunta por la malla curricular de una carrera.
        Cada periodo es equivalente a un semestre academico.

        Ejemplo de uso:
        - Mensaje del usuario: "¿Cuál es la malla de la carrera de Derecho?"
        - Mensaje del usuario: "¿Dame las asignaturas de la carrera de Derecho?"
    """
    carreras: Carreras = await carreras_manager.get_carreras()
    id_carrera = get_id_by_name(carreras.data, nombre_carrera)

    if not id_carrera:
        return "Lo siento, no encontré esa carrera en nuestra base de datos. ¿Podrías verificar si está bien escrita o puedo listarte todas las carreras disponibles?"

    malla_instance = await fetch_malla(id_carrera)
    malla = malla_instance.data

    if not malla:
        return "No hay malla disponible para esta carrera."

    result = f"La Malla curricular de la carrera es la siguiente:\n"
    
    for nivel in malla:
        result += f"\n### Período: {nivel.nivel_malla}"
        result += f"\nLas asignaturas de este período son:"

        for asig in nivel.asignaturas:
            result += f"\n- Asignatura: {asig.asignatura}"
            result += f"\n  - Horas: {asig.horas}"
            if asig.creditos is not None:
                result += f"\n  - Créditos: {asig.creditos}"
    result += "\n"

    return result

@tool
async def listar_grupos(nombre_carrera: str) -> str:
    """
    Esta tool se activa cuando el usuario pregunta por los grupos o cupos disponibles de una carrera específica.

    Ejemplo de uso:
    - "¿Qué grupos hay para la carrera de Fisioterapia?"
    - "Cursos disonibles?"
    """

    carreras: Carreras = await carreras_manager.get_carreras()
    id_carrera = get_id_by_name(carreras.data, nombre_carrera)

    if not id_carrera:
        return "Lo siento, no encontré esa carrera en nuestra base de datos. ¿Podrías verificar si está bien escrita o puedo listarte todas las carreras disponibles?"


    grupos_instance = await fetch_grupos(id_carrera)
    grupos = grupos_instance.data

    if not grupos:
        return "No hay grupos disponibles que inicien clase proximamente."

    result = f"Los grupos disponibles son:"
    result = "\n".join(
        f"- Paralelo: {grupo.nombre}, Fecha de inicio de clases aproximado: {grupo.fecha_inicio}, Sesion: {grupo.sesion}, Modalidad: {grupo.modalidad}"
        for grupo in grupos
    )
    return result  

tools = [listar_carreras, listar_malla, listar_grupos]

# El prompt del sistema que define el rol del agente
system_prompt_template = """
    Eres un asistente llamado "Dr. Matrícula" que trabaja para la Universidad Bolivariana del Ecuador (UBE).  
    Tu función es exclusivamente brindar información sobre:  
    - Carreras de la UBE (pregrado y postgrado)  
    - Matrículas y requisitos  
    - Mallas curriculares  
    - Grupos disponibles  
    - Procesos de admisión  

    No eres un asistente general ni respondes a temas fuera de la UBE.  
    Cualquier otra consulta será manejada por la skill `default`.  
"""

prompt_template = PromptTemplate.from_template(system_prompt_template)
prompt = hub.pull("hwchase17/openai-functions-agent")
prompt.messages[0].prompt.template = system_prompt_template

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.1,  # Menos variabilidad en respuestas
    # max_tokens=2000   # Limitar tokens para evitar respuestas muy largas
)

# Crea el agente
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

agent = create_openai_functions_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(
#     agent=agent, 
#     tools=tools, 
#     verbose=True,
#     memory=memory
# )


memorias = {}

def get_agent(user_id: str):
    if user_id not in memorias:
        memorias[user_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        memory=memorias[user_id]
    )
    return agent_executor


# from langchain_core.runnables.passthrough import RunnablePassthrough
# from langchain_core.output_parsers.string import StrOutputParser


# chain = (
#     Context.setter("input")
#     | {
#         "context": RunnablePassthrough() | Context.setter("context"),
#         "question": RunnablePassthrough(),
#     }
#     | PromptTemplate.from_template("{context} {question}")
#     | StrOutputParser()
#     | {
#         "result": RunnablePassthrough(),
#         "context": Context.getter("context"),
#         "input": Context.getter("input"),
#     }
# )