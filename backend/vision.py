from __future__ import annotations

from backend.schemas import GuideActionPayload


def analyze_camera_frame(payload: dict) -> GuideActionPayload:
    """Return an advisory CV result.

    This demo path accepts metadata-driven detections so Unity/backend integration can
    be tested before a real sterile-field CV model is available.
    """
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}

    if metadata.get("simulated_breach") or metadata.get("breach_detected"):
        breach_type = metadata.get("breach_type") or "sterile_field_breach"
        confidence = float(metadata.get("confidence", 0.5))
        message = "Possible sterile field breach detected. Treat this as advisory and verify before continuing."
        return GuideActionPayload(
            action_cmd="flag_breach",
            parameters={
                "severity": "warning",
                "message": message,
                "breach_type": breach_type,
                "confidence": confidence,
                "advisory": True,
                "procedure_id": context.get("procedure_id"),
                "current_step_id": context.get("current_step_id"),
            },
            spoken_response=message,
        )

    return GuideActionPayload(
        action_cmd="read_step",
        parameters={
            "status": "no_breach_detected",
            "advisory": True,
            "procedure_id": context.get("procedure_id"),
            "current_step_id": context.get("current_step_id"),
        },
        spoken_response="No camera-based breach is detected. Continue following the checklist.",
    )
