from backend.action_contract import to_guide_action
from backend.schemas import ActionPayload, AIResponsePayload


def test_safety_block_maps_to_show_alert():
    payload = AIResponsePayload(
        intent="safety_block",
        spoken_response="Medication dosing requires physician authorization.",
        action=None,
    )

    out = to_guide_action(payload, context={})

    assert out.action_cmd == "show_alert"
    assert out.parameters["severity"] == "warning"
    assert out.parameters["message"] == payload.spoken_response
    assert out.spoken_response == payload.spoken_response


def test_home_navigation_maps_to_navigate_home():
    payload = AIResponsePayload(
        intent="navigate",
        spoken_response="Going home.",
        action=ActionPayload(type="open_screen", params={"screen": "home"}),
    )

    out = to_guide_action(payload, context={})

    assert out.action_cmd == "navigate_home"
    assert out.parameters == {"screen": "home"}


def test_open_screen_navigation_is_carried_as_read_step_for_non_home_screens():
    payload = AIResponsePayload(
        intent="navigate",
        spoken_response="Opening the central line checklist.",
        action=ActionPayload(type="open_screen", params={"screen": "central_line_checklist"}),
    )

    out = to_guide_action(payload, context={})

    assert out.action_cmd == "read_step"
    assert out.parameters["screen"] == "central_line_checklist"
    assert out.parameters["action_type"] == "open_screen"


def test_rag_answer_maps_to_read_step_with_sources():
    payload = AIResponsePayload(
        intent="rag",
        spoken_response="Use maximal sterile barrier precautions.",
        action=None,
    )

    out = to_guide_action(
        payload,
        context={},
        sources=["CDC CLABSI Prevention Summary"],
    )

    assert out.action_cmd == "read_step"
    assert out.parameters["sources"] == ["CDC CLABSI Prevention Summary"]
