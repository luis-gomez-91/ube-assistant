from langchain.agents import tool
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain import hub
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GEMINI_API_KEY, TOKEN_LLAMA, OPENAI_API_KEY
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
    Los IDS usalos para apuntar a otro endpont de ser necesario, no los muestres en la conversacion con el usuario.

    Incluye:
    - Nombre de la carrera.
    - Precios de inscripcion, matricula y nuemro de cuotas.
    - Sesiones.
    - Modalidades.
    """

    carreras: Carreras = await carreras_manager.get_carreras()

    if nombre_carrera:
        id_carrera = get_id_by_name(carreras.data, nombre_carrera)
        if not id_carrera:
            return "Lo siento, no encontré esa carrera en nuestra base de datos. ¿Podrías verificar si está bien escrita o puedo listarte todas las carreras disponibles?"

    grado = formatear_texto_carreras(carreras.data.grado, "grado")
    postgrado = formatear_texto_carreras(carreras.data.postgrado, "postgrado")
    response = f"""{grado}\n\n{postgrado}\nLos IDS usalos para apuntar a otro endpont de ser necesario, no los muestres en la conversacion con el usuario."""
     
    preguntas_sugeridas = """
    ¿Quieres que te muestre solo las carreras de pregrado o de postgrado?
    ¿Deseas conocer los requisitos de ingreso para alguna de estas carreras?
    ¿Quieres saber la duración promedio de una carrera o maestría?
    ¿Quieres que te muestre qué carreras están disponibles en modalidad online o híbrida?
    ¿Deseas que te organice las carreras por áreas (salud, tecnología, educación, negocios)?
    ¿Quieres información sobre becas o facilidades de pago?
    ¿Te interesa que te cuente sobre la salida laboral de alguna carrera?
    ¿Quieres que te muestre los grupos disponibles próximos a iniciar clases?
    """

    response = f"""
    {grado}

    {postgrado}

    Preguntas sugeridas para continuar:
    {preguntas_sugeridas}
    """
    
    return response

@tool
async def listar_malla(nombre_carrera: str) -> str:
    """
        Esta tool se activa cuando el usuario pregunta por la malla curricular de una carrera.
        Cada periodo es equivalente a un semestre academico.

        Ejemplo de uso:
        - "¿Cuál es la malla de la carrera de Derecho?"
        - "¿Dame las asignaturas de la carrera de Derecho?"
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

    preguntas_sugeridas = """
    ¿Quieres que te dé una descripción más detallada de alguna asignatura?
    ¿Deseas saber la duración total de la carrera?
    ¿Quieres que te muestre el perfil de egreso de esta carrera?
    ¿Quieres conocer en qué modalidades (presencial, online, híbrida) se ofrece esta carrera?
    ¿Quieres que te muestre las oportunidades laborales al finalizar la carrera?
    ¿Te interesa conocer los precios o facilidades de pago de esta carrera?
    """

    result += f"\nPreguntas sugeridas para continuar:\n{preguntas_sugeridas}"
    return result

@tool
async def listar_grupos(nombre_carrera: str) -> str:
    """
    Esta tool se activa cuando el usuario pregunta por:
    - Los grupos o cupos disponibles de una carrera específica.
    - Las modalidades de estudio de una carrera.
    - Los precios de una carrera.
    - La matrícula o inscripción en una carrera.

    Ejemplo de uso:
    - "¿Qué grupos hay para la carrera de Fisioterapia?"
    - "¿Qué modalidades tiene la carrera de Derecho?"
    - "¿Cuánto cuesta estudiar Psicología?"
    - "Quiero matricularme en Enfermería"
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

    preguntas_sugeridas = """
    ¿Quieres que te muestre el proceso de matrícula paso a paso?
    ¿Deseas saber si hay facilidades de pago o becas disponibles?
    ¿Quieres comparar esta carrera con otra para ver precios y modalidades?
    ¿Quieres que te muestre las fechas exactas de inscripción?
    ¿Deseas información sobre requisitos para matricularte en esta carrera?
    """

    result += f"\n\nPreguntas sugeridas para continuar:\n{preguntas_sugeridas}"
    return result  

tools = [listar_carreras, listar_malla, listar_grupos]

# El prompt del sistema que define el rol del agente
system_prompt_template = """
    Eres "Dr. Matrícula", un asistente especializado que trabaja para la Universidad Bolivariana del Ecuador (UBE).

    FUNCIÓN ESPECÍFICA:
    Tu única función es brindar información precisa y útil sobre:
    - Carreras de pregrado y postgrado de la UBE
    - Procesos de matrícula y requisitos de admisión
    - Mallas curriculares detalladas
    - Grupos y horarios disponibles
    - Información académica y administrativa de la UBE

    INSTRUCCIONES IMPORTANTES:
    1. SOLO respondes consultas relacionadas con la UBE
    2. Para cualquier tema NO relacionado con la UBE, responde: "Soy Dr. Matrícula, especializado únicamente en información de la UBE. Para otros temas, consulta con un asistente general."
    3. Sé cordial, profesional y preciso en tus respuestas
    4. Si no tienes información específica, sugiere al usuario contactar directamente a la UBE
    5. Utiliza las herramientas disponibles para obtener información actualizada

    TONO: Profesional, amigable y servicial.
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

# from langchain_openai import ChatOpenAI

# llm = ChatOpenAI(
#     model="meta-llama/llama-3.3-70b-instruct",   # modelo disponible en OpenRouter
#     openai_api_key=TOKEN_LLAMA,
#     openai_api_base="https://openrouter.ai/api/v1",  # base URL de OpenRouter
#     temperature=0.1,
#     max_tokens=2000,
# )


# llm = ChatOpenAI(
#     model="gpt-4o-mini",
#     openai_api_key=OPENAI_API_KEY,
#     temperature=0.1,
#     max_tokens=2000
# )

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