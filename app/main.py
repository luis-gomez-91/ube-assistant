import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import logging
from api_helper import health_check


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno del archivo .env
# Esta línea debe ejecutarse antes de cualquier importación de otros módulos
# que dependan de estas variables, como el router de ventas.
load_dotenv()

from fastapi import FastAPI
from app.routers import ventas_route
from app.routers import prueba_route


# Inicializa FastAPI
# app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Iniciando Dr. Matrícula - UBE Chatbot")
    
    # Verificar conectividad con la API
    try:
        is_healthy = await health_check()
        if is_healthy:
            logger.info("✅ API UBE está funcionando correctamente")
        else:
            logger.warning("⚠️  API UBE no responde - algunas funciones podrían fallar")
    except Exception as e:
        logger.error(f"❌ Error al verificar API UBE: {e}")
    
    # Verificar variables de entorno críticas
    required_env_vars = ["GEMINI_API_KEY", "API_BASE_URL", "TOKEN_LLAMA"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Variables de entorno faltantes: {missing_vars}")
        raise RuntimeError(f"Variables de entorno requeridas no encontradas: {missing_vars}")
    else:
        logger.info("✅ Variables de entorno configuradas correctamente")
    
    yield
    
    # Shutdown
    logger.info("🔄 Cerrando Dr. Matrícula - UBE Chatbot")

# Inicializar FastAPI con configuración mejorada
app = FastAPI(
    title="Dr. Matrícula - UBE Chatbot",
    description="""
    🎓 **Asistente Inteligente para Matrículas UBE**
    
    Dr. Matrícula es tu asistente personal para todo lo relacionado con:
    - Información detallada de carreras
    - Grupos y horarios disponibles
    - Mallas curriculares completas
    - Proceso de matrícula paso a paso
    - Requisitos de admisión
    
    **Funcionalidades principales:**
    - Chat inteligente con IA
    - Búsqueda de carreras por nombre
    - Información de precios y modalidades
    - Consulta de cupos disponibles
    - Guía de matrícula automatizada
    """,
    version="2.0.0",
    contact={
        "name": "Universidad Bolivariana del Ecuador",
        "url": "https://ube.edu.ec",
        "email": "admisiones@ube.edu.ec"
    },
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {"status": "success", "message": "WhatsApp Chatbot activo"}

# Incluir router
app.include_router(ventas_route.router)
app.include_router(prueba_route.router)
