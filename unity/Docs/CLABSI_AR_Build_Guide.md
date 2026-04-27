# AR Health — CLABSI Prevention AR Glasses
## Full Project Build Guide — All Phases

**Institution:** Chapman University · Grand Challenges Initiative  
**Partner:** LayerJot (Mentors: Soren Harner, Etay Gafni)  
**Team:** AB Owusu-Agyemang · Arthur Shurtleff · Jack Baker · Krish Garg · Noelle Tulabing · Zaara Batla

---

## Background

**Problem:** Central Line-Associated Bloodstream Infections (CLABSIs) cause ~250,000 infections annually in the US and are a leading cause of death in ICU patients. They are preventable with proper sterile technique, but human error and knowledge decay between trainings lead to inconsistent adherence.

**Solution:** An Android application built in Unity running on XREAL AR glasses that provides real-time, hands-free, step-by-step procedural guidance during central line insertion, maintenance, and removal — with an AI assistant that can be spoken to naturally for clarifications, safety alerts, and suggestions.

**Primary Hardware:** XREAL One Pro ($499 + $99 camera) — 1080p, 120Hz, 600 nits, Bose audio, USB-C, 84g, 12MP camera. Processed by XREAL Beam Pro (Android). Budget alternative: XREAL Air 2 Pro ($299, no camera).

---

## Contents

- [System Architecture Overview](#system-architecture-overview)
- [Phase 1 — Core Unity App](#phase-1--core-unity-app--ui-shell-checklists-voice--tts)
- [Phase 2 — XREAL Glasses Integration](#phase-2--xreal-glasses-integration--nrsdk-hud-overlay-camera)
- [Phase 3 — AI Backend](#phase-3--ai-backend--fastapi-langchain-rag-gpt-4o)
- [Phase 4 — Full Integration](#phase-4--full-integration--websocket-safety-alerts-camera-ai)
- [Phase 5 — Polish & Safety](#phase-5--polish--safety--offline-multilingual-hipaa-testing)
- [Ethics & Equity Considerations](#ethics--equity-considerations)
- [Key References](#key-references)

---

## System Architecture Overview

The system connects two major layers: the Android/Unity frontend running on XREAL glasses, and a Mac-hosted FastAPI backend that handles AI reasoning.

| Layer | Technology | Responsibility |
|---|---|---|
| AR Glasses | XREAL One Pro + NRSDK | HUD display, mic, camera |
| Mobile App | Unity + Android SDK | UI, checklist engine, TTS, voice nav |
| Wake Word | Porcupine | Hands-free AI trigger |
| Connectivity | WebSocket (NativeWebSocket) | Real-time bidirectional messaging |
| AI Backend | FastAPI + Python (Mac) | Request routing, agent orchestration |
| Agent | LangChain | Intent router, safety gate, tool executor |
| Knowledge | ChromaDB + RAG | CLABSI protocols, CDC guidelines |
| LLM | GPT-4o (OpenAI) | Conversational AI reasoning |

**Signal flow:**
```
XREAL Glasses → Mic → Porcupine wake word → Android STT → Context Manager
→ WebSocket Client → Mac FastAPI Server → LangChain Agent → GPT-4o
→ action_cmd + spoken_response → Android TTS + Unity AR overlay
```

---

## Phase 1 — Core Unity App — UI Shell, Checklists, Voice & TTS

**Goal:** A fully functional Android app (no glasses required yet) with all three procedure checklists, voice navigation, TTS step readout, and local procedure log. This phase validates all UI logic before adding hardware complexity.

### Key Deliverables

- Home page with logo, Procedures, Log, Settings, and Exit buttons
- Procedures page with Insert, Maintenance, and Remove options
- Reusable checklist component with step progression logic
- All three procedure checklists (Insert 9 steps, Maintenance 6 steps, Remove 7 steps)
- Voice command navigation ("Next", "Done", "Home", "Procedures")
- TTS reads each step aloud automatically on display
- Local SQLite/PlayerPrefs procedure log with timestamps
- Settings page (Appearance, Terms of Service, Privacy Policy)
- Mute/unmute for audio prompts

### Build Tasks

**Project & UI**
- Create Unity 3D project, set Android build target
- Design and build Home screen UI
- Build Procedures page with 3 buttons
- Build reusable `StepChecklist` component
- Implement step progression (one at a time, enforce order)
- Build Settings page UI and sub-pages

**Checklists**
- Add Insert procedure checklist data (sterile field setup, hand hygiene, site prep, gloving, draping, catheter placement, line confirmation, dressing verification, completion)
- Add Maintenance procedure checklist data (dressing inspection, hand hygiene, dressing change, line flush, site inspection, completion)
- Add Remove procedure checklist data (hand hygiene, clamp line, remove catheter, apply pressure, dress site, line removed confirmation, completion)

**Voice & Audio**
- Integrate Android TTS (`TextToSpeech` API)
- Auto-trigger TTS on new step display
- Implement Android STT for voice navigation
- Map voice commands to navigation actions
- Add fallback tap/gesture navigation

**Data & Logging**
- Create local procedure log database
- Build Procedure Log page (list view + detail view)
- Store per-procedure: steps completed, timestamps, AI alerts

### Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Android STT latency | Test early; have tap fallback ready from day 1 |
| TTS pacing | Allow manual re-read trigger in addition to auto-play |
| Step skip attempts | Hard-block skip at the controller level, not just UI |

---

## Phase 2 — XREAL Glasses Integration — NRSDK, HUD Overlay, Camera

**Goal:** Port the working Android app to the XREAL glasses. Configure the NRSDK, render the checklist UI on the right-lens HUD, validate hands-free usability, and wire up the XREAL Eye camera for later AI use.

### Key Deliverables

- App running on XREAL glasses via NRSDK
- Checklist UI rendered as AR overlay on the HUD
- Overlay positioned non-obtrusively (right lens, lower quadrant)
- AI alert popup overlay working on HUD
- Readability validated (font size ≥14pt, high contrast)
- XREAL camera feed accessible from Unity
- Microphone input routed through XREAL hardware
- Full hands-free procedure run tested on glasses

### Build Tasks

**NRSDK Setup**
- Import NRSDK into Unity project
- Configure Android manifest (camera, mic, USB permissions)
- Set up XREAL glasses pairing and display output
- Port existing canvas UI to NRSDK WorldSpace canvas

**HUD & Overlay**
- Position HUD overlay in non-obstructive area (right lens, lower quadrant)
- Test text readability on physical glasses
- Adjust font size, contrast, brightness as needed
- Add AR overlay popup for AI alerts and warnings
- Display step progress indicator on HUD

**Hardware Integration**
- Wire XREAL camera feed to Unity texture
- Route XREAL microphone to Android STT pipeline
- Test full voice navigation on glasses hardware
- Test all three procedure checklists end-to-end on glasses
- Document any NRSDK rendering limitations

### Risks & Mitigations

| Risk | Mitigation |
|---|---|
| HUD readability | Test contrast in bright clinical lighting; use white text on dark translucent panel |
| NRSDK canvas mode | WorldSpace canvas requires different coordinate system than Screen Space — plan for refactor |
| USB-C passthrough | Beam Pro must stay connected during procedures; test cable management |

---

## Phase 3 — AI Backend — FastAPI, LangChain, RAG, GPT-4o

**Goal:** Build and test the Python AI backend in isolation on Mac before connecting to Unity. This includes the WebSocket server, LangChain agent pipeline, ChromaDB knowledge base with CLABSI protocols, and GPT-4o integration.

### Key Deliverables

- FastAPI WebSocket server running locally on Mac
- LangChain agent: Intent Router → Safety Gate → Tool Executor
- ChromaDB populated with CDC CLABSI guidelines and sterile technique protocols
- RAG pipeline retrieving relevant context per query
- GPT-4o generating accurate, domain-specific responses
- Context manager maintaining session state across turns
- JSON `action_cmd` + `spoken_response` output format defined
- Fully tested via curl/Postman before Unity connection

### Build Tasks

**Backend Server**
- Set up Python virtual environment (FastAPI, LangChain, ChromaDB, openai)
- Build FastAPI app with WebSocket endpoint
- Implement Intent Router (classify: question / navigation / alert)
- Implement Safety Gate (reject unsafe or out-of-scope requests)
- Implement Tool Executor (trigger AR action commands)
- Integrate OpenAI GPT-4o via LangChain

**Knowledge Base**
- Collect and preprocess CLABSI protocol documents (CDC, Chi et al.)
- Chunk and embed documents into ChromaDB
- Build RAG retriever (top-k context injection into prompt)

**Agent Design**
- Implement Context Manager (session history, current step tracking)
- Define `action_cmd` schema (`next_step`, `show_alert`, `read_step`, `flag_breach`, etc.)
- Write system prompt enforcing clinical safety boundaries
- Test all intents manually before Unity integration

### Action Command Schema (draft)

```json
{
  "action_cmd": "show_alert",
  "parameters": {
    "severity": "warning",
    "message": "Hand hygiene not confirmed before gloving."
  },
  "spoken_response": "Please confirm hand hygiene was performed before putting on sterile gloves."
}
```

### Risks & Mitigations

| Risk | Mitigation |
|---|---|
| GPT-4o latency | Target <2s response; cache common safety alerts locally |
| RAG hallucination | Always inject retrieved context; do not rely on model memory alone |
| Safety gate over-blocking | Tune iteratively; log all blocked requests for review |
| Network dependency | Plan local LLM fallback (e.g. Ollama + Llama 3) for offline clinical environments |

---

## Phase 4 — Full Integration — WebSocket, Safety Alerts, Camera AI

**Goal:** Connect the Unity frontend to the Mac AI backend via WebSocket. Wire up the full voice-to-AI pipeline end-to-end, add real-time safety alert overlays, and integrate camera-based breach detection.

### Key Deliverables

- Unity WebSocket client connected to FastAPI backend
- Full voice pipeline: XREAL mic → Porcupine → STT → backend → GPT-4o → TTS
- AI responses displayed as AR overlay popups in real time
- AI safety alerts logged to procedure log with timestamps
- Camera feed analyzed for sterile field breaches
- Post-procedure AI summary (missed steps, compliance score, time elapsed)
- Procedure log updated with all AI observations
- End-to-end test of all three procedures with AI active

### Build Tasks

**Unity WebSocket Client**
- Add `NativeWebSocket` to Unity project
- Implement WebSocket client (connect, send, receive, auto-reconnect)
- Wire STT output to WebSocket send pipeline
- Parse `action_cmd` JSON responses in Unity
- Map action commands to Unity AR actions (advance step, show alert, etc.)
- Route `spoken_response` to Android TTS
- Display AI alert as HUD overlay popup with auto-dismiss timeout

**Voice Pipeline**
- Integrate Porcupine wake word detection in Unity/Android
- Add visual/audio cue when wake word detected
- Wire full pipeline: wake word → STT → WebSocket → backend → response

**Camera AI**
- Implement camera frame capture and send to backend
- Add computer vision endpoint in FastAPI for breach detection
- Run inference asynchronously (do not block step progression)

**Logging & Reporting**
- Implement AI log capture (all alerts, warnings, timestamps per procedure)
- Build post-procedure summary generation (LLM summarization call)
- Write compliance score calculation logic
- Full integration test: Insert, Maintenance, Remove with live AI

### Risks & Mitigations

| Risk | Mitigation |
|---|---|
| WebSocket reconnect | Implement exponential backoff; show user indicator when disconnected |
| Camera analysis latency | Run inference async; never block step progression on AI response |
| Wake word false positives | Tune Porcupine sensitivity; add confirmation cue before STT activates |
| AI hallucination on camera | Flag detections as advisory only; human remains decision-maker at all times |

---

## Phase 5 — Polish & Safety — Offline Mode, Multilingual, HIPAA, Testing

**Goal:** Harden the app for real clinical environments. Ensure it works fully offline, meets HIPAA data handling requirements, supports multiple languages, and passes end-to-end testing across all hardware and procedure types.

### Key Deliverables

- Full offline mode: checklists, TTS, and graceful AI fallback
- Multilingual support (Spanish minimum; additional languages as resources allow)
- Visual aids to reduce language dependency for critical steps
- HIPAA-compliant data handling (no PII stored without consent, encrypted logs)
- Camera recording consent flow implemented
- Clear on-screen indicator of AI confidence and limitations
- Passed full end-to-end test suite on physical XREAL glasses (all use cases UC-01 through UC-30)
- User documentation and quick-start guide for clinical staff

### Build Tasks

**Offline Mode**
- Store all checklists as local JSON (no network required)
- Cache TTS audio files for all steps
- Implement graceful AI degradation when backend unreachable
- Pre-generate canned safety responses for the most critical alert types
- Add network status indicator in HUD

**Multilingual & Accessibility**
- Add multilingual step text and TTS (i18n framework)
- Add visual diagram overlays for critical procedural steps
- Review all UI copy for plain-language clarity

**HIPAA & Privacy**
- Audit all data storage for HIPAA compliance
- Implement log encryption at rest
- Add camera consent dialog before recording begins
- Add persistent AI disclaimer overlay ("AI is advisory — human oversight required")

**Testing**
- Write and run full test checklist covering all 30 use cases
- Test on Android without glasses (mobile-only mode)
- Test with XREAL glasses connected (all three procedures)
- Performance test: memory, battery, thermal on Beam Pro
- Test offline mode end-to-end with no network connection
- Test exit and re-launch state persistence

**Documentation**
- Create clinical staff quick-start guide
- Document AI boundaries and limitations for institutional use

### Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Offline AI quality | Pre-generate canned safety responses for the most critical alert types |
| HIPAA scope creep | Involve a compliance advisor early; document every data touchpoint |
| Translation accuracy | Use professional medical translation, not auto-translate, for clinical step text |
| Battery life | Profile GPU load from NRSDK; target ≥4hr continuous use on Beam Pro |

---

## Ethics & Equity Considerations

### Cost Accessibility
AR hardware cost ($499–$598) may exclude lower-income clinical settings. The team should maintain compatibility with the budget XREAL Air 2 Pro ($299) and monitor hardware price trajectories. Long-term, advocate for institutional procurement pathways.

### Language Barriers
Clinical staff and patients may not be English-proficient. The app must include multilingual step text and TTS at minimum in Spanish. Visual aids should reduce language dependency for the most critical procedural steps.

### Patient Privacy & HIPAA
Camera recording during procedures captures sensitive clinical environments. Strict informed consent must be obtained before recording begins. All stored logs must be encrypted, de-identified where possible, and handled per HIPAA guidelines.

### AI Accountability
The AI assistant is not 100% accurate and must never replace human clinical judgment. All AI outputs should be framed as advisory. The app must display a persistent disclaimer and maintain clear human oversight. All AI boundaries must be documented in policy.

---

## Key References

1. CDC. (2024). Central Line-associated Bloodstream Infection (CLABSI) Basics.
2. Chi et al. (2024). Development of best evidence-based practice protocols for CVC placement and maintenance to reduce CLABSI.
3. Huang et al. (2018). The use of augmented reality glasses in central line simulation.
4. Suzuki et al. (2021). Learning effectiveness of using AR technology in central venous access procedure.
5. Zhao et al. (2020). SSVEP Stimulus Layout Effect on Accuracy of BCIs in AR Glasses.

---

*AR Health · Chapman University Grand Challenges Initiative · In partnership with LayerJot*
