from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from backend.config import settings


@lru_cache(maxsize=1)
def _load_mock_db() -> dict:
    db_path = Path(settings.mock_patient_db_path)
    if not db_path.exists():
        return {}
    with db_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _patient_record(patient_id: str, patient: dict) -> dict:
    return {"patient_id": patient_id, **patient}


def _all_patient_records() -> list[dict]:
    return [_patient_record(patient_id, patient) for patient_id, patient in _load_mock_db().items()]


def _normalize(text: Any) -> str:
    return str(text or "").strip().lower()


def _tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"\W+", text.lower()) if token]


def _is_all_patients_query(query: str) -> bool:
    return any(
        phrase in query
        for phrase in [
            "all patients",
            "list patients",
            "patient list",
            "patients in our care",
            "patients right now",
            "census",
        ]
    )


def _room_from_query(query: str) -> str | None:
    match = re.search(r"\broom\s+([a-z0-9-]+)\b", query, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower()


def _has_central_line(record: dict) -> bool:
    return bool(record.get("central_line", {}).get("present"))


def _has_abnormal_vitals(record: dict) -> bool:
    vitals = record.get("vitals", {})
    heart_rate = vitals.get("heart_rate")
    spo2 = vitals.get("spo2")
    temperature = vitals.get("temperature")
    respiratory_rate = vitals.get("respiratory_rate")
    blood_pressure = vitals.get("blood_pressure")

    if isinstance(heart_rate, (int, float)) and (heart_rate < 60 or heart_rate > 100):
        return True
    if isinstance(spo2, (int, float)) and spo2 < 95:
        return True
    if isinstance(temperature, (int, float)) and (temperature < 36.0 or temperature >= 38.0):
        return True
    if isinstance(respiratory_rate, (int, float)) and (
        respiratory_rate < 12 or respiratory_rate > 20
    ):
        return True

    if isinstance(blood_pressure, str):
        bp_match = re.match(r"^\s*(\d+)\s*/\s*(\d+)\s*$", blood_pressure)
        if bp_match:
            systolic = int(bp_match.group(1))
            diastolic = int(bp_match.group(2))
            if systolic >= 140 or diastolic >= 90:
                return True

    return False


def _record_search_text(record: dict) -> str:
    return json.dumps(record, sort_keys=True).lower()


def _search_records(query: str, records: list[dict]) -> list[dict]:
    normalized_query = _normalize(query)
    tokens = [
        token
        for token in _tokenize(normalized_query)
        if token
        not in {
            "what",
            "who",
            "which",
            "tell",
            "me",
            "the",
            "is",
            "are",
            "in",
            "our",
            "with",
            "patient",
            "patients",
        }
    ]

    if not tokens:
        return []

    scored: list[tuple[int, dict]] = []
    for record in records:
        search_text = _record_search_text(record)
        score = sum(1 for token in tokens if token in search_text)
        if score > 0:
            scored.append((score, record))

    scored.sort(key=lambda item: (-item[0], item[1]["patient_id"]))
    return [record for _, record in scored]


def _build_patient_query_response(query: str, records: list[dict], note: str | None = None) -> dict:
    return {
        "query": query,
        "source": "mock_patient_db",
        "record_count": len(records),
        "records": records,
        "note": note,
    }


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


@tool
def query_patient_records(query: str, patient_id: str | None = None) -> dict:
    """
    Search or retrieve read-only patient records from the mock patient database.
    Use for census, room lookup, patient profile, labs, central-line status, or flexible patient-data questions.
    """
    records = _all_patient_records()
    normalized_query = _normalize(query)

    if patient_id:
        patient = _load_mock_db().get(patient_id)
        if not patient:
            return _build_patient_query_response(
                query=query,
                records=[],
                note=f"Patient {patient_id} not found.",
            )
        return _build_patient_query_response(
            query=query,
            records=[_patient_record(patient_id, patient)],
        )

    if _is_all_patients_query(normalized_query):
        return _build_patient_query_response(query=query, records=records)

    room = _room_from_query(normalized_query)
    if room:
        matches = [record for record in records if _normalize(record.get("room")) == room]
        return _build_patient_query_response(query=query, records=matches)

    if "central line" in normalized_query or "central lines" in normalized_query:
        matches = [record for record in records if _has_central_line(record)]
        return _build_patient_query_response(query=query, records=matches)

    if "abnormal" in normalized_query and "vital" in normalized_query:
        matches = [record for record in records if _has_abnormal_vitals(record)]
        return _build_patient_query_response(query=query, records=matches)

    matches = _search_records(query=normalized_query, records=records)
    return _build_patient_query_response(
        query=query,
        records=matches,
        note=None if matches else "No matching patient records found.",
    )
