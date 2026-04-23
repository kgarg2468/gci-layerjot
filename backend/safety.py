from __future__ import annotations

from typing import Optional


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def safety_check(transcript: str, context: dict) -> Optional[str]:
    if context.get("patient_id") is None and _contains_any(
        transcript,
        ["patient", "vitals", "heart rate", "labs", "blood", "pressure", "spo2"],
    ):
        return "I don't have an active patient loaded. Please select a patient first."

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

    return None
