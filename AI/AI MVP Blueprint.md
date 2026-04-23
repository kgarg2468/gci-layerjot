# GCI AI System - Quick MVP Blueprint

Source: distilled from `AI System Design.md` for the fastest working vertical slice.

## 1. MVP Goal
Ship a **working voice-to-action loop** on XREAL + Unity + local Mac backend that can:
- listen after wake word,
- transcribe one utterance,
- call the backend over WebSocket,
- decide between tool call vs direct response,
- speak response via Android TTS,
- optionally trigger one Unity action.

Success metric: end-to-end response in **<2 seconds** for common requests.

## 2. Scope (Keep It Small)
### In scope
- Porcupine wake word (on-device)
- Android SpeechRecognizer (single-shot STT)
- Unity Context Manager (minimal fields)
- One persistent WebSocket channel
- FastAPI WebSocket endpoint (`/ws`)
- LangChain orchestrator with structured JSON output
- 3 tools only:
  - `get_patient_vitals(patient_id)`
  - `open_screen(screen_name)`
  - `query_protocol(query)`
- ChromaDB RAG with 1-2 seed protocol docs
- Android TTS + Unity ActionExecutor for `open_screen`
- Safety layer (3 hard rules)

### Out of scope (for v2)
- Real EHR/FHIR integration
- Streaming STT and streaming LLM output
- Multi-agent planning
- Full checklist mutation flows
- Medication guidance / diagnosis support

## 3. MVP Architecture

```text
XREAL Unity/Android
  Mic -> Porcupine -> Android STT -> Context Manager -> WebSocket Client
                                             ^                |
                                             |                v
                                  Android TTS <- AIResponse <- FastAPI /ws
                                                          |
                                                    LangChain Agent
                                                 /        |        \
                                   get_patient_vitals  open_screen  query_protocol
                                                          |
                                                      ChromaDB
```

## 4. Minimal Contracts

### Device -> Backend
```json
{
  "type": "ai_request",
  "session_id": "test-001",
  "timestamp": "2026-04-09T00:00:00Z",
  "payload": {
    "transcript": "what is the patient's heart rate",
    "context": {
      "patient_id": "PAT-123",
      "current_screen": "home",
      "current_step": null,
      "procedure_active": false,
      "session_id": "test-001"
    }
  }
}
```

### Backend -> Device
```json
{
  "type": "ai_response",
  "session_id": "test-001",
  "timestamp": "2026-04-09T00:00:01Z",
  "payload": {
    "intent": "retrieve_data",
    "spoken_response": "The patient's heart rate is 96 beats per minute.",
    "action": null
  }
}
```

## 5. MVP Intents
Use only these for v1:
- `retrieve_data`
- `navigate`
- `rag`
- `clarify`
- `safety_block`
- `error`

## 6. Safety Gate (Must Have)
Implement before LLM call:
- no patient-data response if `patient_id` is null,
- no diagnosis intent,
- no medication dosing advice.

If violated, return:
```json
{
  "intent": "safety_block",
  "spoken_response": "I can't help with that request. Please consult the attending physician.",
  "action": null
}
```

## 7. Project Skeleton

```text
backend/
  main.py
  orchestrator.py
  safety.py
  schemas.py
  tools/
    __init__.py
    patient_tools.py
    ui_tools.py
    protocol_tools.py
  rag/
    ingest.py
    pipeline.py
  data/mock_patients.json
  docs/clabsi_prevention_bundle.pdf
  requirements.txt
```

## 8. First 3 Demo Prompts
1. "Hey GCI, what is the patient's heart rate?"
- expected: `get_patient_vitals` tool call + spoken value.

2. "Hey GCI, open the central line checklist."
- expected: `navigate` intent + `action.type = open_screen`.

3. "Hey GCI, what sterile precautions are required before insertion?"
- expected: `query_protocol` tool call + short RAG summary.

## 9. Fast Build Order (1-2 Days)
1. Backend WebSocket echo with fixed JSON response.
2. Unity client send/receive + TTS playback.
3. Add context injection.
4. Add LangChain + structured JSON output validation.
5. Add 3 tools.
6. Add safety pre-check.
7. Add RAG ingest + retriever.
8. Run latency pass and trim prompt/tool overhead.

## 10. Definition of Done
MVP is done when all are true:
- device wake word -> STT -> backend -> TTS works reliably,
- at least one tool call path and one action path succeed,
- malformed/unsafe queries fail safely,
- average latency for test prompts is under 2s on local Wi-Fi.

## 11. Practical Defaults
- LLM: `gpt-4o`, `temperature=0`
- Embeddings: `text-embedding-3-small`
- Chroma `k=3`
- Porcupine sensitivity `0.5`
- TTS rate `1.1`

---

If you want, next step is generating the actual backend starter files in this exact structure so you can run `uvicorn` immediately.

---

# Finish GCI MVP v0/v1 — Codex-Ready Execution Plan

## Context

Work on this MVP stopped mid-implementation. Backend is ~85% done (FastAPI `/ws`, schemas, safety, 3 tools, RAG pipeline, 6 basic tests). mac_client is ~75% done (push-to-talk, OpenAI Whisper STT, macOS `say` TTS, WebSocket client with backoff). What's missing: the orchestrator is a hand-rolled `bind_tools` loop rather than a real agent framework, RAG ingest is a manual script, seed data has only 1 patient and 1 protocol, test coverage has gaps, and the 3 blueprint demo prompts have never been verified end-to-end.

This plan finishes v0/v1 so the 3 blueprint demo prompts work end-to-end via the macOS client, the pytest suite passes cleanly without network access, and the orchestrator is migrated to **LangGraph** to unblock v2 work (checklist mutation, multi-turn state, streaming) without a rewrite.

**Decisions locked in:**
- Client target: macOS desktop push-to-talk (no Android/XREAL pivot in v1).
- Agent framework: **LangGraph** — state graph with `safety → router → tool_executor → synthesis`.
- DoD: 3 demo prompts e2e, full pytest passes, RAG auto-ingests on startup.
- Seed data: expand to 3 patients + 2 protocol docs.

**Out of scope (explicit):** Porcupine wake word, Android/Unity/XREAL port, streaming STT/TTS, multi-agent planning, checklist mutation, hard <2s latency gate (we instrument, don't gate).

**Reference:** See §4 (contracts), §5 (intents), §6 (safety), §8 (demo prompts), §11 (defaults) above.

---

## Ground rules for the executor

1. Follow these steps **in order**. Each step is atomic and independently testable — commit at each step boundary.
2. Preserve the existing public API of `run_agent(transcript: str, context: dict) -> AIResponsePayload`. `main.py` must not change how it calls the orchestrator.
3. Do not modify `backend/safety.py`, `backend/schemas.py`, `backend/tools/*` logic — only read/reuse.
4. No new runtime dependencies outside those listed in Step 1.1 and Step 4.1.
5. All tests must run offline — mock the LLM path; do not require `OPENAI_API_KEY` for pytest.
6. **Do not** add Porcupine, streaming, Android hooks, checklist state, or multi-turn memory — these are v2.

---

## Step 1 — Migrate orchestrator to LangGraph

**Goal:** Replace the manual `bind_tools` + `_execute_tools` loop in `backend/orchestrator.py` with a LangGraph `StateGraph` of 4 nodes, preserving current behavior and all output guards.

### 1.1 — Add dependency

Edit `backend/requirements.txt`. Append:

```
langgraph==0.0.55
pytest-asyncio==0.23.5
```

Reinstall: `pip install -r backend/requirements.txt`.

### 1.2 — Extract prompts to `backend/prompts.py` (new file)

Move `ROUTER_SYSTEM_PROMPT` (currently `backend/orchestrator.py:19-25`) and `SYNTHESIS_SYSTEM_PROMPT` (currently `backend/orchestrator.py:28-49`) verbatim into a new module `backend/prompts.py`. Export both as module-level constants. Do not change the prompt text.

### 1.3 — Rewrite `backend/orchestrator.py`

Full replacement. The file should implement exactly this structure:

```python
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from backend.config import settings
from backend.prompts import ROUTER_SYSTEM_PROMPT, SYNTHESIS_SYSTEM_PROMPT
from backend.safety import safety_check
from backend.schemas import ActionPayload, AIResponsePayload, DebugPayload, fallback_payload
from backend.tools import TOOL_REGISTRY

LOGGER = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    transcript: str
    context: dict
    messages: List[BaseMessage]
    tool_results: List[Dict[str, Any]]
    safety_violation: Optional[str]
    final_payload: Optional[AIResponsePayload]


def _build_router_llm() -> ChatOpenAI:
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.openai_api_key or None,
    )
    return llm.bind_tools(list(TOOL_REGISTRY.values()), tool_choice="auto")


def _build_synthesis_llm():
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.openai_api_key or None,
    )
    return llm.with_structured_output(AIResponsePayload)


# ---- Node implementations ----

async def _safety_node(state: AgentState) -> AgentState:
    violation = safety_check(state["transcript"], state["context"])
    if violation:
        state["safety_violation"] = violation
        state["final_payload"] = AIResponsePayload(
            intent="safety_block",
            spoken_response=violation,
            action=None,
        )
    return state


async def _router_node(state: AgentState) -> AgentState:
    router_llm = _build_router_llm()
    route_messages: List[BaseMessage] = [
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Transcript: {state['transcript']}\n"
                f"Context JSON:\n{json.dumps(state['context'], indent=2)}"
            )
        ),
    ]
    ai_message = await router_llm.ainvoke(route_messages)
    state["messages"] = route_messages + [ai_message]
    return state


async def _tool_executor_node(state: AgentState) -> AgentState:
    last = state["messages"][-1]
    tool_calls = list(getattr(last, "tool_calls", []) or [])
    results: List[Dict[str, Any]] = []
    new_messages: List[BaseMessage] = []

    for tc in tool_calls:
        tool_name = tc.get("name")
        tool_args = tc.get("args", {}) or {}
        tool = TOOL_REGISTRY.get(tool_name)
        if tool is None:
            result = {"error": f"Unknown tool: {tool_name}"}
        else:
            try:
                result = await tool.ainvoke(tool_args)
            except Exception as exc:  # pragma: no cover
                LOGGER.exception("Tool execution failed: %s", tool_name)
                result = {"error": f"Tool failed: {exc}"}
        results.append({"name": tool_name, "args": tool_args, "result": result})
        new_messages.append(
            ToolMessage(
                content=json.dumps(result),
                tool_call_id=tc.get("id", tool_name),
                name=tool_name,
            )
        )

    state["messages"] = state["messages"] + new_messages
    state["tool_results"] = results
    return state


async def _synthesis_node(state: AgentState) -> AgentState:
    synthesis_llm = _build_synthesis_llm()
    tool_results = state.get("tool_results", [])
    synth_messages: List[BaseMessage] = [
        SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Transcript: {state['transcript']}\n"
                f"Context:\n{json.dumps(state['context'], indent=2)}\n\n"
                f"Tool results (JSON):\n{json.dumps(tool_results, indent=2)}"
            )
        ),
    ]
    candidate: AIResponsePayload = await synthesis_llm.ainvoke(synth_messages)
    state["final_payload"] = _enforce_output_guards(candidate, tool_results)
    return state


# ---- Conditional edges ----

def _route_after_safety(state: AgentState) -> str:
    return END if state.get("safety_violation") else "router"


def _route_after_router(state: AgentState) -> str:
    last = state["messages"][-1]
    tool_calls = list(getattr(last, "tool_calls", []) or [])
    return "tool_executor" if tool_calls else "synthesis"


# ---- Graph build (module-level singleton) ----

def _build_graph():
    g = StateGraph(AgentState)
    g.add_node("safety_gate", _safety_node)
    g.add_node("router", _router_node)
    g.add_node("tool_executor", _tool_executor_node)
    g.add_node("synthesis", _synthesis_node)
    g.add_edge(START, "safety_gate")
    g.add_conditional_edges("safety_gate", _route_after_safety, {END: END, "router": "router"})
    g.add_conditional_edges(
        "router", _route_after_router,
        {"tool_executor": "tool_executor", "synthesis": "synthesis"},
    )
    g.add_edge("tool_executor", "synthesis")
    g.add_edge("synthesis", END)
    return g.compile()


_GRAPH = None


def _graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_graph()
    return _GRAPH


# ---- Output guards (ported verbatim from prior implementation) ----

def _enforce_output_guards(
    candidate: AIResponsePayload,
    tool_results: List[Dict[str, Any]],
) -> AIResponsePayload:
    tool_names = [item["name"] for item in tool_results]

    if candidate.intent == "retrieve_data" and "get_patient_vitals" not in tool_names:
        return AIResponsePayload(
            intent="clarify",
            spoken_response=(
                "I need to verify patient data first. Please ask again and confirm the active patient."
            ),
            action=None,
        )

    if candidate.action and candidate.action.type != "open_screen":
        candidate.action = None

    if candidate.intent == "navigate" and candidate.action is None:
        for result in tool_results:
            if result["name"] == "open_screen" and isinstance(result["result"], dict):
                screen = result["result"].get("screen")
                if screen:
                    candidate.action = ActionPayload(type="open_screen", params={"screen": screen})
                    break

    return candidate


# ---- Heuristic fallback (unchanged behavior) ----

def _heuristic_fallback(transcript: str, context: dict) -> AIResponsePayload:
    # Port this function verbatim from the previous orchestrator.py lines 98-155.
    # No logic changes.
    ...


# ---- Public entry point ----

async def run_agent(transcript: str, context: dict) -> AIResponsePayload:
    # Safety first (fast, deterministic, zero-cost).
    violation = safety_check(transcript, context)
    if violation:
        return AIResponsePayload(intent="safety_block", spoken_response=violation, action=None)

    # Offline dev path.
    if not settings.openai_api_key:
        LOGGER.warning("OPENAI_API_KEY not set — using heuristic fallback orchestrator.")
        payload = _heuristic_fallback(transcript, context)
        payload.debug = DebugPayload(tool_called=None, tool_calls=[], tool_inputs=[])
        return payload

    # LangGraph path.
    try:
        initial_state: AgentState = {
            "transcript": transcript,
            "context": context,
            "messages": [],
            "tool_results": [],
            "safety_violation": None,
            "final_payload": None,
        }
        final_state = await _graph().ainvoke(initial_state)
        payload: AIResponsePayload = final_state["final_payload"]
        tool_results = final_state.get("tool_results") or []
        payload.debug = DebugPayload(
            tool_called=tool_results[0]["name"] if tool_results else None,
            tool_calls=[item["name"] for item in tool_results],
            tool_inputs=[item["args"] for item in tool_results],
        )
        return payload
    except Exception:  # pragma: no cover
        LOGGER.exception("Agent execution failed.")
        return fallback_payload()
```

**Verbatim port:** `_heuristic_fallback` must be copied line-for-line from the existing `backend/orchestrator.py:98-155` (no logic changes). `_enforce_output_guards` must match the existing `backend/orchestrator.py:158-190` (no logic changes).

**Acceptance for Step 1:**
- `python -c "from backend.orchestrator import run_agent, _graph; _graph()"` succeeds.
- Existing `backend/tests/test_safety.py` and `backend/tests/test_tools.py` still pass unchanged.
- `grep -n "AgentExecutor\|create_tool_calling_agent" backend/` returns nothing.

---

## Step 2 — Auto-run RAG ingest on backend startup

**Goal:** A fresh clone (no `backend/chroma_db/`) + `./scripts/run_demo.sh` should just work without requiring a manual `python -m backend.rag.ingest`.

### 2.1 — Add `is_ingested()` helper

Edit `backend/rag/ingest.py`. Add at module scope:

```python
from pathlib import Path
from backend.config import settings

def is_ingested() -> bool:
    """True if the Chroma DB directory exists and contains its SQLite artifact."""
    db_dir = Path(settings.chroma_db_path)
    sqlite_file = db_dir / "chroma.sqlite3"
    return db_dir.is_dir() and sqlite_file.exists()
```

### 2.2 — Add FastAPI lifespan to `backend/main.py`

Replace `app = FastAPI(title="GCI Mac MVP Backend", version="0.1.0")` at `backend/main.py:27` with:

```python
from contextlib import asynccontextmanager
from backend.rag.ingest import ingest_docs, is_ingested


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if not settings.openai_api_key:
            LOGGER.info("RAG ingest: skipped (no OPENAI_API_KEY set).")
        elif is_ingested():
            LOGGER.info("RAG ingest: skipped (chroma_db already populated).")
        else:
            LOGGER.info("RAG ingest: building vector store from backend/docs ...")
            ingest_docs()
            LOGGER.info("RAG ingest: built.")
    except Exception:
        LOGGER.exception("RAG ingest failed at startup — falling back to text search.")
    yield


app = FastAPI(title="GCI Mac MVP Backend", version="0.1.0", lifespan=lifespan)
```

### 2.3 — Patch the exception fallback in `main.py` to include latency

At `backend/main.py:135-144`, the generic `Exception` branch builds `fallback_payload()` with no `debug.latency_ms`. Update it to populate `latency_ms=0` (the work was never timed) so clients can rely on the field always being present:

```python
fb = fallback_payload()
fb.debug = DebugPayload(latency_ms=0)
fallback = AIResponseEnvelope(
    type="ai_response",
    session_id="unknown",
    timestamp=now_iso8601(),
    payload=fb,
)
```

**Acceptance for Step 2:**
- `rm -rf backend/chroma_db && ./scripts/run_backend.sh` logs `RAG ingest: building ...` then `RAG ingest: built.`
- Stopping and restarting the server logs `RAG ingest: skipped (chroma_db already populated).`
- With `OPENAI_API_KEY` unset, logs `RAG ingest: skipped (no OPENAI_API_KEY set).` and server starts cleanly.

---

## Step 3 — Expand seed data

### 3.1 — Add patients to `backend/data/mock_patients.json`

Current file has one patient (PAT-123). Add two more with distinct vitals and matching schema (personal / vitals / labs / central_line objects).

- **PAT-124** — John Smith, DOB 1962-07-14, MRN MRN-10042, Room 7B, admission 2026-04-18. Vitals: HR=72, BP="118/76", SpO2=98, Temp=36.8, RR=14. Labs: WBC=7.2, Hgb=13.4, Platelets=210, Creatinine=0.9, blood_cultures="pending". Central line: present=false (null insertion fields).
- **PAT-125** — Maria Chen, DOB 1978-11-02, MRN MRN-10051, Room 3A, admission 2026-04-20. Vitals: HR=112, BP="142/90", SpO2=93, Temp=38.4, RR=22 (borderline/unwell). Labs: WBC=14.1, Hgb=10.8, Platelets=165, Creatinine=1.3, blood_cultures="positive". Central line: present=true, insertion_date=2026-04-21, site="right IJ", days_in=2.

Exact field names must match PAT-123's shape exactly — copy PAT-123 as the template.

### 3.2 — Add a second protocol doc

Create `backend/docs/sample_hand_hygiene_protocol.txt` with ~300–500 chars describing a WHO-5-moments hand-hygiene protocol. Distinct vocabulary from CLABSI doc so retrieval can differentiate. Example outline:

```
Hand Hygiene Protocol (WHO 5 Moments)

Perform hand hygiene at these five moments:
1. Before touching a patient.
2. Before a clean or aseptic procedure.
3. After body fluid exposure risk.
4. After touching a patient.
5. After touching patient surroundings.

Use alcohol-based hand rub for at least 20 seconds. Use soap and water for visibly soiled hands or after contact with spore-forming organisms. Remove jewelry before scrubbing.
```

**Acceptance for Step 3:** `jq '. | length' backend/data/mock_patients.json` reports 3. `ls backend/docs/*.txt` shows two files.

---

## Step 4 — Test coverage + pytest config

### 4.1 — Add `backend/pytest.ini` (new file)

```ini
[pytest]
testpaths = tests
pythonpath = ..
asyncio_mode = auto
```

### 4.2 — Extend `backend/tests/test_tools.py`

Add two new test functions at the end of the existing file:

```python
def test_query_protocol_returns_results(monkeypatch):
    from backend.rag import pipeline
    monkeypatch.setattr(
        pipeline, "query_protocol_docs",
        lambda q, top_k=3: [{"content": "sterile draping required", "source": "x", "score": 0.9}],
    )
    from backend.tools.protocol_tools import query_protocol
    out = query_protocol.invoke({"query": "draping"})
    assert out["query"] == "draping"
    assert len(out["results"]) == 1
    assert "sterile draping" in out["results"][0]["content"]


def test_query_protocol_handles_empty(monkeypatch):
    from backend.rag import pipeline
    monkeypatch.setattr(pipeline, "query_protocol_docs", lambda q, top_k=3: [])
    from backend.tools.protocol_tools import query_protocol
    out = query_protocol.invoke({"query": ""})
    assert out["results"] == []
```

### 4.3 — New file `backend/tests/test_orchestrator.py`

```python
import pytest
from backend.orchestrator import run_agent
from backend.schemas import AIResponsePayload


@pytest.mark.asyncio
async def test_safety_block_short_circuits(monkeypatch):
    monkeypatch.setattr("backend.config.settings.openai_api_key", "fake", raising=False)
    out = await run_agent("diagnose this patient", {"patient_id": "PAT-123"})
    assert isinstance(out, AIResponsePayload)
    assert out.intent == "safety_block"


@pytest.mark.asyncio
async def test_heuristic_fallback_navigate(monkeypatch):
    monkeypatch.setattr("backend.config.settings.openai_api_key", "", raising=False)
    out = await run_agent("open the central line checklist", {"patient_id": "PAT-123"})
    assert out.intent == "navigate"
    assert out.action is not None
    assert out.action.type == "open_screen"
    assert out.action.params["screen"] == "central_line_checklist"


@pytest.mark.asyncio
async def test_heuristic_fallback_retrieve(monkeypatch):
    monkeypatch.setattr("backend.config.settings.openai_api_key", "", raising=False)
    out = await run_agent("what is the patient's heart rate", {"patient_id": "PAT-123"})
    assert out.intent == "retrieve_data"
    assert "beats per minute" in out.spoken_response.lower() or "bpm" in out.spoken_response.lower()


@pytest.mark.asyncio
async def test_heuristic_fallback_rag(monkeypatch):
    monkeypatch.setattr("backend.config.settings.openai_api_key", "", raising=False)
    out = await run_agent("what sterile precautions are required", {"patient_id": "PAT-123"})
    assert out.intent == "rag"
    assert len(out.spoken_response) > 0
```

### 4.4 — New file `backend/tests/test_schemas.py`

```python
from backend.schemas import AIRequestEnvelope, AIResponseEnvelope, fallback_payload


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
    p = fallback_payload("boom")
    assert p.intent == "error"
    assert "boom" in p.spoken_response or p.spoken_response
```

### 4.5 — Run full suite

```
cd backend && pytest
```

**Acceptance for Step 4:** `pytest` exits 0 with no skips, no network calls, no `OPENAI_API_KEY` required. Minimum 14 tests total (3 existing safety + 3 existing tools + 2 new tools + 4 new orchestrator + 2 new schemas).

---

## Step 5 — mac_client polish

### 5.1 — Reconnect-once on WebSocket closure

Edit `mac_client/ws_client.py`. Replace the body of `send_ai_request` with a version that catches `websockets.ConnectionClosed` on both `send` and `recv`, reconnects once via `self.connect()`, and retries exactly once before re-raising:

```python
async def send_ai_request(self, transcript: str, context: dict, session_id: str) -> Dict[str, Any]:
    import websockets as _ws  # local alias to avoid shadowing

    envelope = {
        "type": "ai_request",
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {"transcript": transcript, "context": context},
    }

    async def _attempt() -> Dict[str, Any]:
        if self._ws is None:
            await self.connect()
        await self._ws.send(json.dumps(envelope))
        while True:
            raw = await self._ws.recv()
            message = json.loads(raw)
            if message.get("type") == "ai_response":
                return message
            if message.get("type") == "error":
                raise RuntimeError(message.get("payload", {}).get("message", "Unknown backend error"))

    try:
        return await _attempt()
    except _ws.ConnectionClosed:
        self._ws = None
        await self.connect()
        return await _attempt()
```

### 5.2 — Print `debug.latency_ms` in client REPL

Edit `mac_client/client.py` around line 129. After the existing `print(f"[RESPONSE] {spoken}")` (line 130), insert:

```python
debug = payload.get("debug") or {}
latency = debug.get("latency_ms")
if latency is not None:
    print(f"[LATENCY] {latency} ms")
```

### 5.3 — TTS: no change

`mac_client/tts.py` uses a blocking `subprocess.run`, but `client.py:135` already invokes it via `asyncio.to_thread(speak, spoken)`, so the event loop is not blocked. **Leave `tts.py` unchanged.**

**Acceptance for Step 5:** Demo run prints `[LATENCY] <n> ms` on every response. Killing the backend mid-session and restarting it lets the client recover on the next prompt (one reconnect, success).

---

## Step 6 — End-to-end verification

### 6.1 — Cold-start demo (with API key)

```
export OPENAI_API_KEY=...   # required
cd /Users/krishgarg/Documents/Projects/gci
rm -rf backend/chroma_db
./scripts/run_demo.sh
```

Expected backend log sequence:
1. `RAG ingest: building vector store from backend/docs ...`
2. `RAG ingest: built.`
3. `WebSocket client connected.`

In the client REPL, run the 3 blueprint prompts:

| # | Input | Expected intent | Expected action | Expected spoken |
|---|---|---|---|---|
| 1 | `/text what is the patient's heart rate` | `retrieve_data` | `null` | mentions a BPM number from PAT-123 vitals |
| 2 | `/text open the central line checklist` | `navigate` | `{type: open_screen, params: {screen: central_line_checklist}}` | short confirmation |
| 3 | `/text what sterile precautions are required before insertion` | `rag` | `null` | summary containing content from `sample_clabsi_protocol.txt` |

Each response must print `[LATENCY] <n> ms`.

Also test `/patient PAT-125` then `/text what is the patient's heart rate` — should return PAT-125's HR (112), confirming seed data expansion wired through.

### 6.2 — Mic path smoke test

With the client still running, press Enter, speak "what is the patient's heart rate", press Enter. Confirm `[STT]` prints a plausible transcription and the flow completes with TTS playback.

### 6.3 — Offline (no-API-key) path

```
unset OPENAI_API_KEY
./scripts/run_backend.sh
```

Confirm log: `OPENAI_API_KEY not set — using heuristic fallback orchestrator.` The mac_client itself still requires an `OPENAI_API_KEY` for Whisper STT; use `/text` commands only when testing this path. All 3 prompts must still return correct intents via the heuristic path.

### 6.4 — Test suite

```
cd backend && pytest -v
```

Expect `14 passed` (or more) with zero failures, zero errors, zero skips.

---

## Step 7 — Commit boundaries

Suggested git commits (one per step, in order):

1. `feat(backend): extract orchestrator prompts to prompts.py`
2. `feat(backend): migrate orchestrator to LangGraph state machine`
3. `feat(backend): auto-run RAG ingest on FastAPI startup`
4. `feat(backend): expand mock patients and add hand hygiene protocol`
5. `test(backend): add pytest config + orchestrator/schema/protocol tests`
6. `feat(mac_client): reconnect once on WS closure + print latency`
7. `docs: record v0/v1 verification run` (optional — demo output in a scratch file)

---

## Files touched (summary)

| File | Change | Owner step |
|---|---|---|
| `backend/requirements.txt` | +langgraph, +pytest-asyncio | 1.1 |
| `backend/prompts.py` | **NEW** — extracted prompts | 1.2 |
| `backend/orchestrator.py` | Full rewrite to LangGraph | 1.3 |
| `backend/rag/ingest.py` | Add `is_ingested()` | 2.1 |
| `backend/main.py` | Add lifespan; fix exception latency | 2.2, 2.3 |
| `backend/data/mock_patients.json` | +PAT-124, +PAT-125 | 3.1 |
| `backend/docs/sample_hand_hygiene_protocol.txt` | **NEW** | 3.2 |
| `backend/pytest.ini` | **NEW** | 4.1 |
| `backend/tests/test_tools.py` | +2 protocol tool tests | 4.2 |
| `backend/tests/test_orchestrator.py` | **NEW** — 4 tests | 4.3 |
| `backend/tests/test_schemas.py` | **NEW** — 2 tests | 4.4 |
| `mac_client/ws_client.py` | One-shot reconnect in send | 5.1 |
| `mac_client/client.py` | Print latency_ms | 5.2 |

## Definition of Done

- `cd backend && pytest` → all green, no skips, no network calls.
- `rm -rf backend/chroma_db && ./scripts/run_demo.sh` (with `OPENAI_API_KEY`) auto-ingests RAG and serves all 3 blueprint demo prompts correctly.
- With `OPENAI_API_KEY` unset, backend still responds correctly for the 3 demo prompts via the heuristic fallback.
- Every `ai_response` includes a populated `debug.latency_ms`, printed by the client.
- `backend/orchestrator.py` contains a `StateGraph` with nodes `safety_gate`, `router`, `tool_executor`, `synthesis` and no manual `_execute_tools` orchestration loop.
- `mac_client/ws_client.py` survives one backend restart mid-session without crashing the client.
