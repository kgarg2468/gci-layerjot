from backend.tools.patient_tools import get_patient_vitals
from backend.tools.ui_tools import open_screen


def test_get_patient_vitals_success():
    result = get_patient_vitals.invoke({"patient_id": "PAT-123"})
    assert result["heart_rate"] == 96


def test_open_screen_success():
    result = open_screen.invoke({"screen_name": "central_line_checklist"})
    assert result["status"] == "success"
    assert result["screen"] == "central_line_checklist"


def test_open_screen_invalid():
    result = open_screen.invoke({"screen_name": "unknown_screen"})
    assert "error" in result
