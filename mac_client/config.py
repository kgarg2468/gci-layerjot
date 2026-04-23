from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


CLIENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CLIENT_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env")


@dataclass(frozen=True)
class ClientSettings:
    backend_ws_url: str = os.getenv("BACKEND_WS_URL", "ws://127.0.0.1:8000/ws")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    stt_model: str = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
    stt_language: str = os.getenv("STT_LANGUAGE", "en")
    max_record_seconds: int = int(os.getenv("MAX_RECORD_SECONDS", "20"))
    sample_rate: int = int(os.getenv("SAMPLE_RATE", "16000"))
    default_patient_id: str = os.getenv("DEFAULT_PATIENT_ID", "PAT-123")
    default_screen: str = os.getenv("DEFAULT_SCREEN", "home")


settings = ClientSettings()
