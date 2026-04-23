from backend.safety import safety_check


def test_blocks_patient_query_without_patient_id():
    msg = safety_check("what is the patient heart rate", {"patient_id": None})
    assert msg is not None
    assert "active patient" in msg.lower()


def test_blocks_diagnosis_request():
    msg = safety_check("can you diagnose this condition", {"patient_id": "PAT-123"})
    assert msg is not None
    assert "diagnos" in msg.lower()


def test_allows_safe_question():
    msg = safety_check("open the central line checklist", {"patient_id": "PAT-123"})
    assert msg is None
