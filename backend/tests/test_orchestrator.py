from __future__ import annotations

import asyncio
from types import SimpleNamespace

from langchain_core.messages import AIMessage

import backend.orchestrator as orchestrator
from backend.orchestrator import run_agent
from backend.schemas import AIResponsePayload


class _StubLLM:
    def __init__(self, response):
        self._response = response

    async def ainvoke(self, _messages):
        return self._response


def _set_api_key(monkeypatch, api_key: str) -> None:
    monkeypatch.setattr(orchestrator, "settings", SimpleNamespace(openai_api_key=api_key))


def test_prompts_module_exports_expected_constants():
    from backend.prompts import ROUTER_SYSTEM_PROMPT, SYNTHESIS_SYSTEM_PROMPT

    assert ROUTER_SYSTEM_PROMPT
    assert SYNTHESIS_SYSTEM_PROMPT


def test_graph_builder_exists():
    graph = orchestrator._graph()

    assert graph is not None


def test_safety_block_short_circuits():
    out = asyncio.run(run_agent("diagnose this patient", {"patient_id": "PAT-123"}))

    assert isinstance(out, AIResponsePayload)
    assert out.intent == "safety_block"


def test_graph_navigate_returns_open_screen(monkeypatch):
    _set_api_key(monkeypatch, "fake")
    monkeypatch.setattr(
        orchestrator,
        "_build_router_llm",
        lambda: _StubLLM(
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "open_screen",
                        "args": {"screen_name": "central_line_checklist"},
                        "id": "tool-1",
                    }
                ],
            )
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "_build_synthesis_llm",
        lambda: _StubLLM(
            AIResponsePayload(
                intent="navigate",
                spoken_response="Opening the central line checklist.",
                action=None,
            )
        ),
    )

    out = asyncio.run(run_agent("open the central line checklist", {"patient_id": "PAT-123"}))

    assert out.intent == "navigate"
    assert out.action is not None
    assert out.action.type == "open_screen"
    assert out.action.params["screen"] == "central_line_checklist"
    assert out.debug is not None
    assert out.debug.tool_calls == ["open_screen"]


def test_graph_navigate_backfills_missing_screen_param(monkeypatch):
    _set_api_key(monkeypatch, "fake")
    monkeypatch.setattr(
        orchestrator,
        "_build_router_llm",
        lambda: _StubLLM(
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "open_screen",
                        "args": {"screen_name": "central_line_checklist"},
                        "id": "tool-1b",
                    }
                ],
            )
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "_build_synthesis_llm",
        lambda: _StubLLM(
            AIResponsePayload(
                intent="navigate",
                spoken_response="Opening the central line checklist.",
                action={"type": "open_screen", "params": {}},
            )
        ),
    )

    out = asyncio.run(run_agent("open the central line checklist", {"patient_id": "PAT-123"}))

    assert out.intent == "navigate"
    assert out.action is not None
    assert out.action.type == "open_screen"
    assert out.action.params["screen"] == "central_line_checklist"


def test_graph_retrieve_returns_grounded_patient_data(monkeypatch):
    _set_api_key(monkeypatch, "fake")
    monkeypatch.setattr(
        orchestrator,
        "_build_router_llm",
        lambda: _StubLLM(
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_patient_vitals",
                        "args": {"patient_id": "PAT-123"},
                        "id": "tool-2",
                    }
                ],
            )
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "_build_synthesis_llm",
        lambda: _StubLLM(
            AIResponsePayload(
                intent="retrieve_data",
                spoken_response="The patient's heart rate is 96 beats per minute.",
                action=None,
            )
        ),
    )

    out = asyncio.run(run_agent("what is the patient's heart rate", {"patient_id": "PAT-123"}))

    assert out.intent == "retrieve_data"
    assert "96" in out.spoken_response
    assert out.debug is not None
    assert out.debug.tool_calls == ["get_patient_vitals"]
    assert out.debug.tool_inputs == [{"patient_id": "PAT-123"}]


def test_graph_rag_uses_protocol_tool(monkeypatch):
    _set_api_key(monkeypatch, "fake")
    monkeypatch.setattr(
        orchestrator,
        "_build_router_llm",
        lambda: _StubLLM(
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "query_protocol",
                        "args": {"query": "what sterile precautions are required"},
                        "id": "tool-3",
                    }
                ],
            )
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "_build_synthesis_llm",
        lambda: _StubLLM(
            AIResponsePayload(
                intent="rag",
                spoken_response="Maintain sterile barrier precautions before insertion.",
                action=None,
            )
        ),
    )

    out = asyncio.run(run_agent("what sterile precautions are required", {"patient_id": "PAT-123"}))

    assert out.intent == "rag"
    assert "sterile" in out.spoken_response.lower()
    assert out.debug is not None
    assert out.debug.tool_calls == ["query_protocol"]


def test_offline_fallback_is_deterministic_and_uses_expanded_seed_data(monkeypatch):
    _set_api_key(monkeypatch, "")

    context = {"patient_id": "PAT-125"}
    first = asyncio.run(run_agent("what is the patient's heart rate", context))
    second = asyncio.run(run_agent("what is the patient's heart rate", context))

    assert first.intent == "retrieve_data"
    assert second.intent == "retrieve_data"
    assert first.spoken_response == second.spoken_response
    assert "112" in first.spoken_response
    assert first.debug is not None
    assert first.debug.tool_calls == []
