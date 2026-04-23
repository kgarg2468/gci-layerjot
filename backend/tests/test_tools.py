from backend.tools.patient_tools import get_patient_vitals, query_patient_records
from backend.tools.protocol_tools import query_protocol
from backend.tools.ui_tools import open_screen


def test_get_patient_vitals_success():
    result = get_patient_vitals.invoke({"patient_id": "PAT-123"})
    assert result["heart_rate"] == 96


def test_query_patient_records_finds_patient_by_room():
    result = query_patient_records.invoke({"query": "room 3A"})

    assert result["record_count"] == 1
    assert result["records"][0]["patient_id"] == "PAT-125"
    assert result["records"][0]["name"] == "Maria Chen"
    assert result["records"][0]["room"] == "3A"


def test_query_patient_records_lists_all_patients():
    result = query_patient_records.invoke({"query": "all patients"})

    assert result["record_count"] == 3
    assert {record["patient_id"] for record in result["records"]} == {
        "PAT-123",
        "PAT-124",
        "PAT-125",
    }


def test_query_patient_records_filters_central_lines():
    result = query_patient_records.invoke({"query": "which patients have central lines"})

    assert result["record_count"] == 2
    assert {record["patient_id"] for record in result["records"]} == {"PAT-123", "PAT-125"}
    assert all(record["central_line"]["present"] is True for record in result["records"])


def test_query_patient_records_unknown_query_returns_no_matches():
    result = query_patient_records.invoke({"query": "patient with purple shoes"})

    assert result["record_count"] == 0
    assert result["records"] == []
    assert result["source"] == "mock_patient_db"


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
