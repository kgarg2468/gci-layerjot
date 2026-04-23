from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

from backend.config import settings


@lru_cache(maxsize=1)
def _load_mock_db() -> dict:
    db_path = Path(settings.mock_patient_db_path)
    if not db_path.exists():
        return {}
    with db_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@tool
def get_patient_vitals(patient_id: str) -> dict:
    """
    Retrieve current vital signs for a patient.
    Use when asked about heart rate, blood pressure, SpO2, temperature, or respiratory rate.
    """
    patient = _load_mock_db().get(patient_id)
    if not patient:
        return {"error": f"Patient {patient_id} not found"}

    vitals = patient.get("vitals", {})
    return {
        "patient_id": patient_id,
        "heart_rate": vitals.get("heart_rate"),
        "blood_pressure": vitals.get("blood_pressure"),
        "spo2": vitals.get("spo2"),
        "temperature": vitals.get("temperature"),
        "respiratory_rate": vitals.get("respiratory_rate"),
        "timestamp": vitals.get("last_updated"),
    }
