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
