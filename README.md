# Dr. Matrícula - UBE Chatbot 🎓

## Descripción del Proyecto
**Dr. Matrícula** es un asistente virtual inteligente diseñado para la Universidad Bolivariana del Ecuador (UBE), construido para optimizar el proceso de matrícula y brindar información detallada a estudiantes y prospectos. El chatbot utiliza modelos de lenguaje avanzados y herramientas específicas para responder a consultas sobre carreras, mallas curriculares, precios, cupos disponibles y procesos de admisión.

---

## Características Principales
- **Chat Inteligente:** Asistencia automatizada con respuestas precisas y contextuales.
- **Información de Carreras:** Detalle completo sobre las carreras de pregrado y postgrado de la UBE, incluyendo precios, modalidades y sesiones.
- **Mallas Curriculares:** Acceso instantáneo a las asignaturas de cada semestre (o "período").
- **Disponibilidad de Cupos:** Consulta de grupos y horarios disponibles para cada carrera.
- **Guía de Matrícula:** Soporte paso a paso para el proceso de admisión y matrícula.
- **Integración con API UBE:** Conectividad con la API interna de la universidad para obtener información en tiempo real.

---

## Tecnologías Utilizadas
- **Python 🐍:** Lenguaje de programación principal.
- **FastAPI:** Framework web para construir la API.
- **LangChain:** Framework para el desarrollo de aplicaciones basadas en modelos de lenguaje.
- **Google Gemini 2.0 Flash:** Modelo de lenguaje para la inteligencia del chatbot.
- **Meta-Llama 3.3-70B-Instruct:** Modelo clasificador para la detección de carreras.
- **Pydantic:** Librería para la validación de datos.
- **Httpx & Requests:** Librerías para realizar peticiones HTTP.
- **python-dotenv:** Para la gestión de variables de entorno.
- **Logging:** Para el registro de eventos y depuración.

---

## Estructura del Proyecto
```
.
├── app/
│   ├── routers/
│   │   ├── ventas_route.py       # Puntos de entrada de la API para ventas/chat
│   │   └── prueba_route.py       # Router de prueba
│   ├── schemas/
│   │   ├── base_schema.py        # Modelos de datos base
│   │   ├── carreras_schema.py    # Modelo para datos de carreras
│   │   ├── grupos_schema.py      # Modelo para datos de grupos
│   │   └── malla_schema.py       # Modelo para datos de mallas curriculares
│   └── services/
│       └── ventas_service.py     # Lógica para la conexión con la API de UBE
├── agents/
│   └── ventas.py                 # Lógica principal del agente LangChain, herramientas y LLM
├── config.py                     # Carga de variables de entorno en constantes
├── main.py                       # Punto de entrada principal de la aplicación FastAPI
├── utils.py                      # Funciones de utilidad como formateo de texto y clasificación de carreras
├── .env.example                  # Archivo de ejemplo de variables de entorno
└── requirements.txt              # Dependencias del proyecto
```

---

## Configuración del Entorno y Ejecución

1. **Clonar el repositorio:**
    ```
    git clone [URL_DEL_REPOSITORIO]
    cd [nombre_del_directorio]
    ```
    
2. **Crear y activar un entorno virtual:**
    ```
    python -m venv venv
    # En Windows:
    .\venv\Scripts\activate
    # En macOS/Linux:
    source venv/bin/activate
    ```
    
3. **Instalar las dependencias:**     
    ```
    pip install -r requirements.txt
    ```
    
4. **Configurar las variables de entorno:** Crea un archivo `.env` en la raíz del proyecto y copia las variables del archivo `.env.example`, reemplazando los valores `[TU_CLAVE]` con tus credenciales.
    `.env`
    
    ```
    GEMINI_API_KEY=[TU_CLAVE_DE_GEMINI]
    API_BASE_URL=[URL_DE_LA_API_DE_UBE]
    TOKEN_LLAMA=[TU_TOKEN_DE_LLAMA]
    # Opcional: WhatsApp Business API
    WHATSAPP_TOKEN=[TU_TOKEN_DE_WHATSAPP]
    WHATSAPP_PHONE_NUMBER_ID=[TU_ID_DE_NUMERO]
    WHATSAPP_VERIFY_TOKEN=[TU_TOKEN_DE_VERIFICACION]
    ```
    
5. **Ejecutar la aplicación:**    
    ```
    uvicorn main:app --reload
    ```
    
    La API estará disponible en `http://127.0.0.1:8000`. Puedes acceder a la documentación interactiva en `http://127.0.0.1:8000/docs`.