from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load root-level first, then backend-local overrides.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", str(BACKEND_DIR / "chroma_db"))
    docs_path: str = os.getenv("DOCS_PATH", str(BACKEND_DIR / "docs"))
    mock_patient_db_path: str = os.getenv(
        "MOCK_PATIENT_DB_PATH", str(BACKEND_DIR / "data" / "mock_patients.json")
    )
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
