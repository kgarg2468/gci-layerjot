from backend.procedure import build_procedure_summary, detect_procedure_alert


def test_detects_hand_hygiene_not_confirmed_before_gloving():
    alert = detect_procedure_alert(
        transcript="can I move to gloving now",
        context={
            "procedure_active": True,
            "procedure_id": "insert",
            "current_step_id": 4,
            "current_step_title": "Gloving",
            "completed_step_ids": [1],
        },
    )

    assert alert is not None
    assert alert.action_cmd == "show_alert"
    assert alert.parameters["severity"] == "warning"
    assert "hand hygiene" in alert.spoken_response.lower()


def test_build_procedure_summary_scores_completion_and_missed_steps():
    summary = build_procedure_summary(
        {
            "procedure_id": "insert",
            "procedure_name": "Central Line Insertion",
            "started_at": "2026-04-29T10:00:00Z",
            "completed_at": "2026-04-29T10:12:00Z",
            "total_steps": 9,
            "completed_step_ids": [1, 2, 3, 4, 5, 6, 8, 9],
            "ai_events": [
                {
                    "event_type": "warning",
                    "message": "Dressing verification was delayed.",
                }
            ],
        }
    )

    assert summary.action_cmd == "end_procedure"
    assert summary.parameters["procedure_id"] == "insert"
    assert summary.parameters["compliance_score"] == 89
    assert summary.parameters["missed_step_ids"] == [7]
    assert "missed 1 step" in summary.spoken_response.lower()
