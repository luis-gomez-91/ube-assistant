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
    Retorna información de carreras específicas según se solicita.
    Los IDS se usan solo para apuntar a otro endpoint de ser necesario,
    no se muestran en la conversación con el usuario.

    Incluye:
    - Nombre de la carrera.
    - Precios de inscripción, matrícula y número de cuotas.
    - Sesiones.
    - Modalidades.
    """

    carreras: Carreras = await carreras_manager.get_carreras()

    # if nombre_carrera:
    #     id_carrera = get_id_by_name(carreras.data, nombre_carrera)
    #     print(f"ID. DE LA CARRERA: {id_carrera}")
    #     if not id_carrera:
    #         f"""
    #             Pregunta si desea conocer información de carreras parecidas a {nombre_carrera}
    #         """
    #         return "Lo siento, no encontré esa carrera en nuestra base de datos. ¿Podrías verificar si está bien escrita o prefieres que te muestre todas las carreras disponibles?"

    grado = formatear_texto_carreras(carreras.data.grado, "grado")
    postgrado = formatear_texto_carreras(carreras.data.postgrado, "postgrado")

    # Preguntas sugeridas mejoradas
    preguntas_sugeridas = """
    ¿Prefieres que te muestre únicamente las carreras de pregrado o las de postgrado?
    ¿Quieres conocer los requisitos de ingreso para una carrera en particular?
    ¿Te interesa saber la duración promedio de una carrera o una maestría?
    ¿Quieres ver cuáles carreras están disponibles en modalidad online, presencial o híbrida?
    ¿Prefieres que te organice las carreras por áreas como salud, tecnología, educación o negocios?
    ¿Quieres información sobre becas, descuentos o facilidades de pago?
    ¿Te interesa conocer las oportunidades laborales de una carrera específica?
    ¿Deseas que te muestre los grupos y fechas de inicio más cercanos?
    ¿Quieres que te sugiera carreras relacionadas a tus intereses?
    ¿Te gustaría comparar dos carreras para ver cuál se ajusta mejor a lo que buscas?
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

@tool
async def requisitos_matriculacion(nombre_carrera: str = None) -> str:
    """
    Retorna los requisitos de matriculación en la UBE.
    Puede mostrar requisitos generales o específicos para una carrera en particular.
    """

    # Requisitos generales
    requisitos_generales = """
    Requisitos generales para matriculación:
    - Copia de cédula de identidad o pasaporte.
    - Certificado de votación (para mayores de 18 años).
    - Título de bachiller o acta de grado (apostillado si es extranjero).
    - Certificado de notas del colegio.
    - 2 fotografías tamaño carnet.
    - Pago de inscripción y matrícula según corresponda.
    """

    # Obtener todas las carreras
    carreras_obj = await carreras_manager.get_carreras()
    
    # Normalizamos la lista de carreras (grados + postgrados)
    todas_carreras = []
    if hasattr(carreras_obj.data, 'grado'):
        todas_carreras.extend(carreras_obj.data.grado)
    if hasattr(carreras_obj.data, 'postgrado'):
        todas_carreras.extend(carreras_obj.data.postgrado)

    if nombre_carrera:
        id_carrera = get_id_by_name(carreras_obj.data, nombre_carrera)
        if not id_carrera:
            return f"No encontré la carrera '{nombre_carrera}'. ¿Quieres que te muestre los requisitos generales?"

        # Aquí podrías agregar requisitos específicos por carrera si los tienes
        return f"Requisitos específicos para {nombre_carrera}:\n\n{requisitos_generales}\n\n(Pueden variar según la carrera, confirma con admisiones)."

    # Preguntas sugeridas para el usuario
    preguntas_sugeridas = """
    ¿Quieres que te muestre los costos de inscripción y matrícula?
    ¿Deseas conocer las fechas de inicio de clases?
    ¿Quieres que te muestre carreras en modalidad online para facilitar tu ingreso?
    ¿Deseas saber si puedes aplicar a becas o descuentos en la matrícula?
    """

    response = f"""
    {requisitos_generales}

    Preguntas sugeridas para continuar:
    {preguntas_sugeridas}
    """

    return response

@tool
async def matricular(nombre_carrera: str) -> str:
    """
    Simula la matriculación de una carrera en la UBE.
    Retorna un mensaje de confirmación y un link de pago.
    """

    if not nombre_carrera:
        return "Por favor, indica el nombre de la carrera que deseas matricular."

    # Aquí podrías agregar validaciones reales usando get_id_by_name si quieres
    # id_carrera = get_id_by_name(await carreras_manager.get_carreras(), nombre_carrera)
    # if not id_carrera:
    #     return f"No encontré la carrera '{nombre_carrera}'. Verifica el nombre."

    # Generar mensaje de confirmación y link de pago de ejemplo
    link_pago = f"https://ube.edu.ec/pago/matricula?carrera={nombre_carrera.replace(' ', '%20')}&token=EJEMPLO123"

    response = f"""
        ¡Matricula realizada exitosamente para la carrera '{nombre_carrera}'! 🎓

        Para completar el proceso, realiza tu pago en el siguiente link:
        {link_pago}

        Recuerda que tu matrícula se confirmará una vez recibido el pago.
    """

    return response


@tool
async def default_tool(query: str = None) -> str:
    """
    Skill por defecto que responde cuando el usuario hace consultas
    fuera del alcance definido (carreras, grupos, mallas, matrículas de la UBE).
    """
    return (
        "Soy Dr. Matrícula, especializado únicamente en información de la UBE. "
        "No puedo resolver preguntas como operaciones matemáticas u otros temas externos. "
        "¿Quieres que te muestre información sobre nuestras carreras o procesos de matrícula?\n\n"
        "Si deseas más información puedes comunicarte por:\n"
        "- 📲 WhatsApp: https://api.whatsapp.com/send/?phone=593989758382&text=Me+gustar%C3%ADa+saber+informaci%C3%B3n+sobre+las+carreras&type=phone_number&app_absent=0\n"
        "- 🌐 Página oficial: https://ube.edu.ec/"
    )


tools = [listar_carreras, listar_malla, listar_grupos, default_tool, requisitos_matriculacion, matricular]

# El prompt del sistema que define el rol del agente
system_prompt_template = """
    Eres "Dr. Matrícula", un agente virtual de la Universidad Bolivariana del Ecuador (UBE).

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

    Si la pregunta no está relacionada con UBE, utiliza siempre la herramienta default_tool.
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

