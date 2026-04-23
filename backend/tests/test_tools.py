from backend.tools.patient_tools import get_patient_vitals
from backend.tools.protocol_tools import query_protocol
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


def test_query_protocol_returns_results(monkeypatch):
    monkeypatch.setattr(
        "backend.tools.protocol_tools.query_protocol_docs",
        lambda query, top_k=3: [
            {
                "content": "Sterile draping is required before insertion.",
                "source": "sample.txt",
                "score": 0.9,
            }
        ],
    )

    result = query_protocol.invoke({"query": "draping"})

    assert result["query"] == "draping"
    assert len(result["results"]) == 1
    assert "Sterile draping" in result["results"][0]["content"]


def test_query_protocol_handles_empty(monkeypatch):
    monkeypatch.setattr("backend.tools.protocol_tools.query_protocol_docs", lambda query, top_k=3: [])

    result = query_protocol.invoke({"query": ""})

    assert result["results"] == []
