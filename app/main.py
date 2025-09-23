import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import logging
from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()

from fastapi import FastAPI
from app.routers import ventas_route

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Iniciando Dr. Matrícula - UBE Chatbot")
    
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

origins = [
    "http://localhost:3000",           # Next.js dev
    "http://127.168.15.27:3000",          # Next.js dev alternativo
]

# IMPORTANTE: CORS debe ir ANTES de otros middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Específico
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "success", "message": "WhatsApp Chatbot activo"}

# Incluir router
app.include_router(ventas_route.router)