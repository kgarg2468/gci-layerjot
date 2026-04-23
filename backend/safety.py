from __future__ import annotations

from typing import Optional


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _is_explicit_population_or_lookup_query(text: str) -> bool:
    lowered = text.lower()
    return _contains_any(
        lowered,
        [
            "all patients",
            "list patients",
            "patient list",
            "patients in our care",
            "patients right now",
            "which patients",
            "what patient",
            "who is in room",
            "who's in room",
            "room ",
            "central lines",
        ],
    )


def _is_ambiguous_single_patient_query(text: str) -> bool:
    lowered = text.lower()
    if _is_explicit_population_or_lookup_query(lowered):
        return False

    return _contains_any(
        lowered,
        [
            "the patient",
            "patient's",
            "vitals",
            "heart rate",
            "labs",
            "blood",
            "pressure",
            "spo2",
        ],
    )


def safety_check(transcript: str, context: dict) -> Optional[str]:
    if _contains_any(
        transcript,
        ["diagnose", "diagnosis", "what disease", "what condition", "is it"],
    ):
        return "I can't make clinical diagnoses. Please consult the attending physician."

    if _contains_any(
        transcript,
        ["dose", "dosage", "how much medication", "prescribe"],
    ):
        return (
            "Medication dosing requires physician authorization. "
            "I can show protocol information, but I can't advise dosing."
        )

    if context.get("patient_id") is None and _is_ambiguous_single_patient_query(transcript):
        return "I don't have an active patient loaded. Please select a patient first."

    return None
