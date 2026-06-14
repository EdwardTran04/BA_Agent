import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

class Config:
    # Database Settings: Defaults to a local SQLite database for easy zero-config startup,
    # but can be easily changed to PostgreSQL via environment variables.
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ba_agent.db")
    
    # AI Provider configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # OpenRouter configurations
    OPENROUTER_API_KEY_STAGE2 = os.getenv("OPENROUTER_API_KEY_STAGE2", "")
    OPENROUTER_MODEL_STAGE2 = os.getenv("OPENROUTER_MODEL_STAGE2", "meta-llama/llama-3.3-70b-instruct:free")

    OPENROUTER_API_KEY_STAGE3 = os.getenv("OPENROUTER_API_KEY_STAGE3", "")
    OPENROUTER_MODEL_STAGE3 = os.getenv("OPENROUTER_MODEL_STAGE3", "meta-llama/llama-3.3-70b-instruct:free")
    
    # Active AI Provider: "openai" or "gemini" (defaults to "openai" if key is set, otherwise fallbacks or is configured)
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
    
    # File storage configuration
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

config = Config()
