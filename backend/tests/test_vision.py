from backend.vision import analyze_camera_frame


def test_camera_frame_metadata_can_flag_breach_without_blocking():
    result = analyze_camera_frame(
        {
            "image_jpeg_base64": "not-a-real-image-for-test",
            "context": {"procedure_id": "insert", "current_step_title": "Gloving"},
            "metadata": {
                "simulated_breach": True,
                "breach_type": "non_sterile_contact",
                "confidence": 0.82,
            },
        }
    )

    assert result.action_cmd == "flag_breach"
    assert result.parameters["breach_type"] == "non_sterile_contact"
    assert result.parameters["confidence"] == 0.82
    assert result.parameters["advisory"] is True


def test_camera_frame_without_detection_returns_read_step_advisory():
    result = analyze_camera_frame(
        {
            "image_jpeg_base64": "not-a-real-image-for-test",
            "context": {"procedure_id": "insert"},
            "metadata": {},
        }
    )

    assert result.action_cmd == "read_step"
    assert result.parameters["status"] == "no_breach_detected"
