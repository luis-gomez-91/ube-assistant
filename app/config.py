import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = os.getenv("API_BASE_URL")
TOKEN_LLAMA = os.getenv("TOKEN_LLAMA")
