"""Environment-based application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    """Simple settings loaded from environment variables."""

    app_name: str = os.getenv("APP_NAME", "AI Revenue Recovery Agent")
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./revenue_recovery.db")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))

    # LLM / Ollama configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    enable_llm: bool = os.getenv("ENABLE_LLM", "true").lower() in ("true", "1", "yes")
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "3.0"))


settings = Settings()

