from __future__ import annotations

from typing import Iterable

from backend.schemas import AIResponsePayload, GuideActionPayload


def _base_parameters(payload: AIResponsePayload) -> dict:
    params: dict = {}
    if payload.action is not None:
        params.update(payload.action.params)
        params["action_type"] = payload.action.type
    return params


def to_guide_action(
    payload: AIResponsePayload,
    context: dict,
    sources: Iterable[str] | None = None,
) -> GuideActionPayload:
    """Translate internal MVP payloads to the build-guide action_cmd contract."""
    parameters = _base_parameters(payload)
    if sources:
        parameters["sources"] = list(sources)

    if payload.intent in {"safety_block", "error"}:
        parameters.setdefault("severity", "warning" if payload.intent == "safety_block" else "error")
        parameters.setdefault("message", payload.spoken_response)
        return GuideActionPayload(
            action_cmd="show_alert",
            parameters=parameters,
            spoken_response=payload.spoken_response,
        )

    if payload.action and payload.action.type == "open_screen":
        screen = str(payload.action.params.get("screen", ""))
        if screen in {"home", "HomeScreen"}:
            parameters = {"screen": "home"}
            return GuideActionPayload(
                action_cmd="navigate_home",
                parameters=parameters,
                spoken_response=payload.spoken_response,
            )

        return GuideActionPayload(
            action_cmd="read_step",
            parameters=parameters,
            spoken_response=payload.spoken_response,
        )

    severity = parameters.get("severity")
    if severity in {"warning", "critical"}:
        parameters.setdefault("message", payload.spoken_response)
        return GuideActionPayload(
            action_cmd="show_alert",
            parameters=parameters,
            spoken_response=payload.spoken_response,
        )

    return GuideActionPayload(
        action_cmd="read_step",
        parameters=parameters,
        spoken_response=payload.spoken_response,
    )
