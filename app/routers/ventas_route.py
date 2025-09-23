# routers/ventas.py
import os
import asyncio
import time
from fastapi import APIRouter
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY
from app.schemas.ventas_schema import MessageRequest
from app.schemas.grupos_schema import Grupos as GruposSchema
from app.schemas.malla_schema import Malla, DataMalla
from api_helper import fetch_carreras, fetch_grupos, fetch_malla, matricular
from utils import get_id_by_name, formatear_texto_carreras, get_id_by_name_hybrid
from langchain_community.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from typing import List

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"]
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.1,  # Menos variabilidad en respuestas
    # max_tokens=2000   # Limitar tokens para evitar respuestas muy largas
)

# Cache global para carreras
carreras_cache = None
cache_time = None
CACHE_DURATION = 300  # 5 minutos

def run_async(coroutine):
    """Helper para ejecutar funciones async de manera síncrona."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coroutine)
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)  # 30 segundos timeout
        else:
            return loop.run_until_complete(coroutine)
    except Exception as e:
        print(f"Error en run_async: {e}")
        return None

def get_carreras_cache():
    """Cache con timeout para carreras."""
    global carreras_cache, cache_time
    current_time = time.time()
    
    if carreras_cache is None or (cache_time and current_time - cache_time > CACHE_DURATION):
        print("🔄 Actualizando cache de carreras...")
        carreras_cache = run_async(fetch_carreras())
        cache_time = current_time
    
    return carreras_cache

def list_carreras_tool(input: str = None):
    """Lista todas las carreras disponibles."""
    try:
        carreras = get_carreras_cache()
        if not carreras or not carreras.data:
            return "❌ No hay carreras disponibles en este momento."
        
        # Crear resumen más conciso
        grado_count = len(carreras.data.grado)
        postgrado_count = len(carreras.data.postgrado)
        
        response = f"""🎓 **OFERTA ACADÉMICA UBE**

📚 **CARRERAS DE GRADO ({grado_count} disponibles):**
• Biomedicina • Derecho • Enfermería • Fisioterapia
• Odontología • Psicología • Sistemas Inteligentes
• Administración • Educación • Economía • Contabilidad
• Y muchas más...

🎯 **MAESTRÍAS ({postgrado_count} disponibles):**
• Educación • Derecho • Administración • Tecnología
• Salud • Negocios • Y especializaciones innovadoras

💡 **¿Te interesa alguna área específica?**
Pregúntame por ejemplo: "información de medicina" o "maestrías en educación"
"""
        return response.strip()
        
    except Exception as e:
        print(f"Error en list_carreras_tool: {e}")
        return "❌ Error temporal. Intenta de nuevo en unos momentos."

def get_carrera_info_tool(input: str):
    """Información detallada de una carrera específica."""
    if not input or len(input.strip()) < 3:
        return "❓ Por favor especifica el nombre de la carrera que te interesa."
    
    try:
        carreras = get_carreras_cache()
        if not carreras or not carreras.data:
            return "❌ No hay información de carreras disponible."
            
        carrera_id = get_id_by_name_hybrid(carreras.data, input, llm)
        
        if carrera_id == 0 or carrera_id is None:
            return f"❓ No encontré la carrera '{input}'. Verifica el nombre o pregunta '¿qué carreras tienen?' para ver todas las opciones."
        
        # Buscar carrera
        carrera_info = None
        tipo = ""
        
        for carrera in carreras.data.grado:
            if carrera.id == carrera_id:
                carrera_info = carrera
                tipo = "GRADO"
                break
                
        if not carrera_info:
            for carrera in carreras.data.postgrado:
                if carrera.id == carrera_id:
                    carrera_info = carrera
                    tipo = "POSTGRADO"
                    break
        
        if not carrera_info:
            return f"❌ No encontré información de '{input}'."
        
        # Formatear respuesta concisa
        info = f"🎓 **{carrera_info.nombre}** ({tipo})\n\n"
        
        if carrera_info.precios:
            info += "💰 **COSTOS:**\n"
            info += f"• Inscripción: ${carrera_info.precios.inscripcion}\n"
            info += f"• Matrícula: ${carrera_info.precios.matricula}\n"
            info += f"• Cuotas: {carrera_info.precios.numero_cuotas}\n\n"
        
        if carrera_info.modalidades:
            info += f"🏫 **Modalidades:** {', '.join(carrera_info.modalidades)}\n"
        
        if carrera_info.sesiones:
            info += f"⏰ **Horarios:** {', '.join(carrera_info.sesiones)}\n\n"
        
        info += "❓ ¿Quieres ver grupos disponibles, malla curricular o proceder con la matrícula?"
        
        return info
        
    except Exception as e:
        print(f"Error en get_carrera_info_tool: {e}")
        return f"❌ Error al buscar información de '{input}'. Intenta de nuevo."

def get_grupos_tool(input: str):
    """Grupos disponibles para una carrera."""
    try:
        carreras = get_carreras_cache()
        if not carreras:
            return "❌ No hay información disponible."
            
        carrera_id = get_id_by_name(carreras.data, input)
        if carrera_id == 0:
            return f"❓ No encontré la carrera '{input}'."
        
        grupos: GruposSchema = run_async(fetch_grupos(carrera_id))
        if not grupos or not grupos.data:
            return f"❌ No hay grupos disponibles para '{input}' actualmente."
        
        info = f"👥 **GRUPOS - {input.upper()}**\n\n"
        for i, grupo in enumerate(grupos.data[:3], 1):  # Limitar a 3 grupos
            info += f"**Grupo {i}:** {grupo.nombre}\n"
            # info += f"• ⏰ {grupo.horario}\n"
            info += f"• 🏫 {grupo.modalidad}\n"
            info += f"• 👥 {grupo.capacidad} cupos\n\n"
        
        if len(grupos.data) > 3:
            info += f"... y {len(grupos.data) - 3} grupos más disponibles.\n\n"
            
        info += "¿Te interesa algún grupo para matricularte?"
        return info
        
    except Exception as e:
        print(f"Error en get_grupos_tool: {e}")
        return "❌ Error al consultar grupos. Intenta de nuevo."

def get_malla_tool(input: str):
    """Malla curricular de una carrera."""
    try:
        carreras = get_carreras_cache()
        if not carreras:
            return "No hay información disponible."
                     
        carrera_id = get_id_by_name(carreras.data, input)
        if carrera_id == 0:
            return f"No encontré la carrera '{input}'."
                 
        malla: Malla = run_async(fetch_malla(carrera_id))
        if not malla or not malla.data:
            return f"No hay malla curricular disponible para '{input}'."
                 
        # Calcular estadísticas
        total_niveles = len(malla.data)
        total_asignaturas = sum(len(nivel.asignaturas) for nivel in malla.data)
        
        info = f"MALLA CURRICULAR - {input.upper()}\n\n"
        info += f"Resumen: {total_asignaturas} asignaturas en {total_niveles} niveles\n\n"
                 
        # Mostrar información por niveles (limitado para brevedad)
        niveles_mostrados = 0
        for nivel_data in malla.data:
            if niveles_mostrados >= 2:  # Mostrar máximo 2 niveles
                break
                
            info += f"{nivel_data.nivel_malla}:\n"
            
            # Mostrar hasta 4 asignaturas por nivel
            asignaturas_mostradas = 0
            for asignatura in nivel_data.asignaturas:
                if asignaturas_mostradas >= 4:
                    break
                    
                asig_info = f"• {asignatura.asignatura}"
                if asignatura.creditos:
                    asig_info += f" ({asignatura.creditos} créditos)"
                elif asignatura.horas:
                    asig_info += f" ({asignatura.horas} horas)"
                
                info += asig_info + "\n"
                asignaturas_mostradas += 1
            
            # Mostrar si hay más asignaturas
            asignaturas_restantes = len(nivel_data.asignaturas) - asignaturas_mostradas
            if asignaturas_restantes > 0:
                info += f"• ... y {asignaturas_restantes} asignaturas más\n"
            
            info += "\n"
            niveles_mostrados += 1
        
        # Mostrar si hay más niveles
        niveles_restantes = total_niveles - niveles_mostrados
        if niveles_restantes > 0:
            info += f"... y {niveles_restantes} niveles adicionales\n\n"
                 
        info += "¿Te gustaría proceder con la matrícula de esta carrera?"
        return info
             
    except Exception as e:
        print(f"Error en get_malla_tool: {e}")
        return "Error al consultar malla curricular."

# También puedes crear una versión más detallada si necesitas toda la información
def get_malla_tool_detailed(input: str):
    """Versión detallada de la malla curricular."""
    try:
        carreras = get_carreras_cache()
        if not carreras:
            return "No hay información disponible."
                     
        carrera_id = get_id_by_name(carreras.data, input)
        if carrera_id == 0:
            return f"No encontré la carrera '{input}'."
                 
        malla: Malla = run_async(fetch_malla(carrera_id))
        if not malla or not malla.data:
            return f"No hay malla curricular disponible para '{input}'."
        
        # Construir respuesta completa
        info = f"MALLA CURRICULAR COMPLETA - {input.upper()}\n"
        info += "=" * 50 + "\n\n"
        
        for nivel_data in malla.data:
            info += f"{nivel_data.nivel_malla}\n"
            info += "-" * len(nivel_data.nivel_malla) + "\n"
            
            for asignatura in nivel_data.asignaturas:
                asig_line = f"• {asignatura.asignatura}"
                
                # Agregar información adicional si está disponible
                details = []
                if asignatura.creditos:
                    details.append(f"{asignatura.creditos} créditos")
                if asignatura.horas:
                    details.append(f"{asignatura.horas} horas")
                
                if details:
                    asig_line += f" ({', '.join(details)})"
                
                info += asig_line + "\n"
            
            info += "\n"
        
        # Estadísticas finales
        total_asignaturas = sum(len(nivel.asignaturas) for nivel in malla.data)
        total_creditos = sum(
            sum(asig.creditos or 0 for asig in nivel.asignaturas)
            for nivel in malla.data
        )
        
        info += f"RESUMEN:\n"
        info += f"• Total de asignaturas: {total_asignaturas}\n"
        if total_creditos > 0:
            info += f"• Total de créditos: {total_creditos}\n"
        info += f"• Niveles: {len(malla.data)}\n\n"
        
        info += "¿Te interesa matricularte en esta carrera?"
        return info
                 
    except Exception as e:
        print(f"Error en get_malla_tool_detailed: {e}")
        return "Error al consultar malla curricular detallada."

# Función auxiliar para extraer información específica de la malla
def get_malla_summary(malla_data: List[DataMalla]) -> dict:
    """Extrae un resumen estadístico de la malla curricular."""
    summary = {
        "total_niveles": len(malla_data),
        "total_asignaturas": 0,
        "total_creditos": 0,
        "total_horas": 0,
        "niveles": []
    }
    
    for nivel in malla_data:
        nivel_info = {
            "nombre": nivel.nivel_malla,
            "asignaturas": len(nivel.asignaturas),
            "creditos": sum(asig.creditos or 0 for asig in nivel.asignaturas),
            "horas": sum(float(asig.horas) if asig.horas else 0 for asig in nivel.asignaturas)
        }
        
        summary["niveles"].append(nivel_info)
        summary["total_asignaturas"] += nivel_info["asignaturas"]
        summary["total_creditos"] += nivel_info["creditos"]
        summary["total_horas"] += nivel_info["horas"]
    
    return summary

# Versión optimizada para el chatbot (más concisa)
def get_malla_tool_optimized(input: str):
    """Versión optimizada para respuestas de chatbot."""
    try:
        carreras = get_carreras_cache()
        if not carreras:
            return "No hay información disponible."
                     
        carrera_id = get_id_by_name(carreras.data, input)
        if carrera_id == 0:
            return f"No encontré la carrera '{input}'."
                 
        malla: Malla = run_async(fetch_malla(carrera_id))
        if not malla or not malla.data:
            return f"No hay malla curricular disponible para '{input}'."
        
        # Generar resumen
        summary = get_malla_summary(malla.data)
        
        info = f"PLAN DE ESTUDIOS - {input.upper()}\n\n"
        info += f"Total: {summary['total_asignaturas']} materias"
        
        if summary['total_creditos'] > 0:
            info += f", {summary['total_creditos']} créditos"
        
        info += f" en {summary['total_niveles']} niveles\n\n"
        
        # Mostrar primeros niveles como muestra
        for i, nivel in enumerate(summary['niveles'][:2]):
            info += f"{nivel['nombre']}: {nivel['asignaturas']} materias\n"
        
        if len(summary['niveles']) > 2:
            info += f"... y {len(summary['niveles']) - 2} niveles más\n"
        
        info += "\nEjemplos de materias:\n"
        
        # Mostrar algunas materias de ejemplo
        materias_ejemplo = []
        count = 0
        for nivel in malla.data:
            for asignatura in nivel.asignaturas:
                if count >= 3:  # Solo 3 ejemplos
                    break
                materias_ejemplo.append(asignatura.asignatura)
                count += 1
            if count >= 3:
                break
        
        for materia in materias_ejemplo:
            info += f"• {materia}\n"
        
        info += "\n¿Te interesa matricularte en esta carrera?"
        return info
                 
    except Exception as e:
        print(f"Error en get_malla_tool_optimized: {e}")
        return "Error al consultar plan de estudios."

def process_matricula_tool(input: str = None):
    """Procesa solicitud de matrícula."""
    try:
        result = run_async(matricular())
        
        if result and result.status == "success":
            return """🎉 **¡MATRÍCULA INICIADA!**

✅ Tu solicitud ha sido procesada exitosamente.

📋 **PRÓXIMOS PASOS:**
• Revisa tu correo para confirmación
• Completa el pago de matrícula
• Presenta documentos requeridos

📞 **Contacto:** admisiones@ube.edu.ec
¿Necesitas ayuda con algo más?"""
        else:
            return """⚠️ **PROBLEMA CON MATRÍCULA**

Por favor contacta directamente:
📧 admisiones@ube.edu.ec
📞 (593) 2-xxx-xxxx

¿Puedo ayudarte con otra consulta?"""
                   
    except Exception as e:
        print(f"Error en process_matricula_tool: {e}")
        return "❌ Error en matrícula. Contacta admisiones@ube.edu.ec"

def admissions_requirements_tool(input: str = None):
    """Requisitos de admisión."""
    return """📋 **REQUISITOS DE ADMISIÓN UBE**

📄 **DOCUMENTOS NECESARIOS:**
• Cédula (original + copia)
• Título bachiller apostillado
• Certificado de votación
• 2 fotos carné
• Formulario de inscripción

⚙️ **PROCESO:**
1. Entregar documentos
2. Pagar inscripción
3. Entrevista (si aplica)
4. Confirmación de cupo

📅 **Inscripciones abiertas todo el año**

¿Tienes alguna pregunta específica sobre el proceso?"""

def default_skill_tool(input: str = None):
    """Herramienta por defecto para saludos y consultas fuera de alcance."""
    return """👋 **¡Hola! Soy Dr. Matrícula de la UBE**

🎯 **TE PUEDO AYUDAR CON:**
• 📚 Información de carreras
• 👥 Grupos y horarios
• 📖 Mallas curriculares  
• 📝 Proceso de matrícula
• 📋 Requisitos de admisión

💬 **PREGÚNTAME:**
• "¿Qué carreras tienen?"
• "Información de medicina"
• "Quiero matricularme"
• "¿Qué documentos necesito?"

¿En qué puedo ayudarte hoy?"""

# Herramientas simplificadas
tools = [
    Tool.from_function(
        func=list_carreras_tool,
        name="list_carreras",
        description="Para mostrar todas las carreras cuando pregunten por la oferta académica general"
    ),
    Tool.from_function(
        func=get_carrera_info_tool,
        name="get_carrera_info", 
        description="Para información específica de una carrera mencionada por el usuario"
    ),
    Tool.from_function(
        func=get_grupos_tool,
        name="get_grupos",
        description="Para consultar grupos y horarios de una carrera específica"
    ),
    Tool.from_function(
        func=get_malla_tool,
        name="get_malla",
        description="Para consultar materias/plan de estudios de una carrera"
    ),
    Tool.from_function(
        func=process_matricula_tool,
        name="process_matricula",
        description="Para procesar una solicitud de matrícula"
    ),
    Tool.from_function(
        func=admissions_requirements_tool,
        name="admissions_requirements",
        description="Para información sobre requisitos y documentos"
    ),
    Tool.from_function(
        func=default_skill_tool,
        name="default_skill",
        description="Para saludos o consultas fuera del alcance de matrículas UBE"
    )
]

# Prompt más simple y directo
prompt_template = PromptTemplate(
    template="""Eres Dr. Matrícula, asistente de la Universidad Bolivariana del Ecuador.

IMPORTANTE: Responde SIEMPRE siguiendo exactamente este formato:

Thought: [Qué herramienta necesito usar]
Action: [Nombre de la herramienta]  
Action Input: [Input para la herramienta]
Observation: [Resultado]
Thought: [Análisis del resultado]
Final Answer: [Respuesta final al usuario]

Herramientas: {tools}
Nombres: {tool_names}

Pregunta: {input}
{agent_scratchpad}""",
    input_variables=["tools", "tool_names", "input", "agent_scratchpad"]
)

# Crear agente con configuración más estricta
agent = create_react_agent(llm, tools, prompt_template)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=2,  # Máximo 2 iteraciones
    max_execution_time=30,  # 30 segundos máximo
    return_intermediate_steps=False
)

@router.post("/chat")
async def chat_endpoint(request: MessageRequest):
    """Endpoint principal del chat."""
    user_msg = request.mensaje.strip()
    
    if not user_msg:
        return {"respuesta": "Por favor escribe tu pregunta."}
    
    try:
        print(f"🔵 Usuario: {user_msg}")
        
        # Ejecutar con timeout
        start_time = time.time()
        response = agent_executor.invoke({"input": user_msg})
        execution_time = time.time() - start_time
        
        print(f"⏱️ Tiempo de ejecución: {execution_time:.2f}s")
        
        final_answer = response.get("output", "").strip()
        
        if not final_answer or "Agent stopped" in final_answer:
            # Fallback directo basado en palabras clave
            final_answer = handle_fallback(user_msg)
        
        print(f"🟢 Respuesta: {final_answer[:100]}...")
        return {"respuesta": final_answer}
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"respuesta": handle_fallback(user_msg)}

def handle_fallback(user_msg: str):
    """Manejo de fallback basado en palabras clave."""
    msg_lower = user_msg.lower()
    
    if any(word in msg_lower for word in ["hola", "buenos", "buenas", "saludo"]):
        return default_skill_tool()
    elif any(word in msg_lower for word in ["carrera", "estudios", "que tienen", "oferta"]):
        return list_carreras_tool()
    elif any(word in msg_lower for word in ["requisito", "documento", "admision"]):
        return admissions_requirements_tool()
    elif any(word in msg_lower for word in ["matricula", "inscrib", "apunt"]):
        return process_matricula_tool()
    else:
        return """👋 Soy Dr. Matrícula de la UBE.

¿Te puedo ayudar con:
• 📚 Información de carreras
• 📝 Proceso de matrícula  
• 📋 Requisitos de admisión

¿Qué te interesa saber?"""

@router.get("/test")
async def test_endpoint():
    """Test rápido del sistema."""
    try:
        result = list_carreras_tool()
        return {
            "status": "success",
            "message": "Sistema funcionando",
            "sample": result[:200] + "..."
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
        }