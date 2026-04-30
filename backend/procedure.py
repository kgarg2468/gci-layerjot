from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.schemas import GuideActionPayload


def _as_int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    out: list[int] = []
    for item in value:
        try:
            out.append(int(item))
        except (TypeError, ValueError):
            continue
    return sorted(set(out))


def _elapsed_minutes(started_at: str | None, completed_at: str | None) -> int | None:
    if not started_at or not completed_at:
        return None
    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, int((end - start).total_seconds() // 60))


def detect_procedure_alert(transcript: str, context: dict) -> GuideActionPayload | None:
    lowered = transcript.lower()
    if not context.get("procedure_active"):
        return None

    current_title = str(context.get("current_step_title") or "").lower()
    completed = set(_as_int_list(context.get("completed_step_ids")))
    procedure_id = context.get("procedure_id")

    if procedure_id == "insert" and ("gloving" in current_title or "glove" in lowered):
        if 2 not in completed:
            message = "Please confirm hand hygiene was completed before sterile gloving."
            return GuideActionPayload(
                action_cmd="show_alert",
                parameters={
                    "severity": "warning",
                    "message": message,
                    "risk": "hand_hygiene_not_confirmed",
                    "current_step_id": context.get("current_step_id"),
                },
                spoken_response=message,
            )

    if "skip" in lowered and any(word in lowered for word in ["sterile", "dressing", "hygiene"]):
        message = "Do not skip required sterile technique confirmations. Continue only after the step is complete."
        return GuideActionPayload(
            action_cmd="show_alert",
            parameters={
                "severity": "warning",
                "message": message,
                "risk": "attempted_required_step_skip",
                "current_step_id": context.get("current_step_id"),
            },
            spoken_response=message,
        )

    return None


def build_procedure_summary(payload: dict) -> GuideActionPayload:
    total_steps = int(payload.get("total_steps") or 0)
    completed = _as_int_list(payload.get("completed_step_ids"))
    expected = set(range(1, total_steps + 1)) if total_steps > 0 else set(completed)
    missed = sorted(expected.difference(completed))
    completed_count = len(set(completed).intersection(expected)) if expected else len(completed)
    compliance_score = int(round((completed_count / total_steps) * 100)) if total_steps else 0
    elapsed = _elapsed_minutes(payload.get("started_at"), payload.get("completed_at"))
    ai_events = payload.get("ai_events") if isinstance(payload.get("ai_events"), list) else []

    procedure_name = payload.get("procedure_name") or payload.get("procedure_id") or "procedure"
    if missed:
        step_phrase = "step" if len(missed) == 1 else "steps"
        spoken = (
            f"{procedure_name} complete with {compliance_score}% compliance; "
            f"missed {len(missed)} {step_phrase}."
        )
    else:
        spoken = f"{procedure_name} complete with {compliance_score}% compliance."

    if elapsed is not None:
        spoken += f" Elapsed time was {elapsed} minutes."

    return GuideActionPayload(
        action_cmd="end_procedure",
        parameters={
            "procedure_id": payload.get("procedure_id"),
            "procedure_name": procedure_name,
            "compliance_score": compliance_score,
            "missed_step_ids": missed,
            "completed_step_ids": completed,
            "total_steps": total_steps,
            "elapsed_minutes": elapsed,
            "ai_event_count": len(ai_events),
            "ai_events": ai_events,
        },
        spoken_response=spoken,
    )
