import os
from dotenv import load_dotenv
from groq import Groq

# Load .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ─────────────────────────────────────────────
# API Keys & Client
# ─────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "llama-3.3-70b-versatile"
WHISPER_MODEL = "whisper-large-v3"

ALLOWED_EXTENSIONS = [".pdf", ".mp3", ".mp4", ".wav", ".m4a"]

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory stores
document_store = {}    # { filename: extracted_text }
timestamp_store = {}   # { filename: [ {start, end, text}, ... ] }
