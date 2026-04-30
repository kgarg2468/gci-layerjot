from fastapi.testclient import TestClient

import backend.main as main


def test_ws_ai_response_includes_guide_action_fields(monkeypatch):
    async def fake_run_agent(transcript, context):
        from backend.schemas import AIResponsePayload

        return AIResponsePayload(
            intent="safety_block",
            spoken_response="Please confirm hand hygiene before continuing.",
            action=None,
        )

    monkeypatch.setattr(main, "run_agent", fake_run_agent)

    client = TestClient(main.app)
    with client.websocket_connect("/ws") as ws:
        ws.send_json(
            {
                "type": "ai_request",
                "session_id": "sess-1",
                "timestamp": "2026-04-29T10:00:00Z",
                "payload": {
                    "transcript": "can I skip hand hygiene",
                    "context": {
                        "session_id": "sess-1",
                        "patient_id": "PAT-123",
                        "current_screen": "StepChecklistScreen",
                    },
                },
            }
        )
        message = ws.receive_json()

    assert message["type"] == "ai_response"
    assert message["schema_version"] == "clabsi-ar.v1"
    assert message["action_cmd"] == "show_alert"
    assert message["parameters"]["severity"] == "warning"
    assert message["spoken_response"] == "Please confirm hand hygiene before continuing."
    assert message["payload"]["intent"] == "safety_block"


def test_ws_camera_frame_returns_flag_breach():
    client = TestClient(main.app)
    with client.websocket_connect("/ws") as ws:
        ws.send_json(
            {
                "type": "camera_frame",
                "session_id": "sess-vision",
                "timestamp": "2026-04-29T10:00:00Z",
                "payload": {
                    "image_jpeg_base64": "test",
                    "context": {"session_id": "sess-vision", "procedure_id": "insert"},
                    "metadata": {
                        "simulated_breach": True,
                        "breach_type": "sterile_field_contact",
                        "confidence": 0.91,
                    },
                },
            }
        )
        message = ws.receive_json()

    assert message["type"] == "ai_response"
    assert message["action_cmd"] == "flag_breach"
    assert message["parameters"]["breach_type"] == "sterile_field_contact"
    assert message["parameters"]["advisory"] is True


def test_ws_procedure_complete_returns_summary():
    client = TestClient(main.app)
    with client.websocket_connect("/ws") as ws:
        ws.send_json(
            {
                "type": "procedure_complete",
                "session_id": "sess-summary",
                "timestamp": "2026-04-29T10:00:00Z",
                "payload": {
                    "procedure_id": "maintenance",
                    "procedure_name": "Central Line Maintenance",
                    "total_steps": 6,
                    "completed_step_ids": [1, 2, 3, 4, 5, 6],
                    "ai_events": [],
                },
            }
        )
        message = ws.receive_json()

    assert message["type"] == "ai_response"
    assert message["action_cmd"] == "end_procedure"
    assert message["parameters"]["compliance_score"] == 100
    assert "100%" in message["spoken_response"]
