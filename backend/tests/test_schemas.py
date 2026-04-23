from backend.schemas import AIRequestEnvelope, fallback_payload


def test_ai_request_envelope_roundtrip():
    raw = {
        "type": "ai_request",
        "session_id": "test-001",
        "timestamp": "2026-04-09T00:00:00Z",
        "payload": {
            "transcript": "what is the patient's heart rate",
            "context": {
                "patient_id": "PAT-123",
                "current_screen": "home",
                "current_step": None,
                "procedure_active": False,
                "session_id": "test-001",
            },
        },
    }

    env = AIRequestEnvelope.model_validate(raw)

    assert env.payload.transcript == "what is the patient's heart rate"
    assert env.payload.context.patient_id == "PAT-123"


def test_fallback_payload_is_error_intent():
    payload = fallback_payload("boom")

    assert payload.intent == "error"
    assert "boom" in payload.spoken_response
