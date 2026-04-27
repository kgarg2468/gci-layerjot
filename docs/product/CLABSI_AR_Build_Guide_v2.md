# AR Health — CLABSI Prevention AR Glasses

## Full Project Build Guide — All Phases

**Institution:** Chapman University · Grand Challenges Initiative  
**Partner:** LayerJot (Mentors: Soren Harner, Etay Gafni)  
**Team:** AB Owusu-Agyemang · Arthur Shurtleff · Jack Baker · Krish Garg · Noelle Tulabing · Zaara Batla

---

## Work Split Summary

This guide is divided between two parallel workstreams. Use the ownership labels throughout each phase to know who picks up each task.

| 🟦 Zaara — Unity / Android / XREAL | 🟧 Teammate — AI Backend / Python |
| :---- | :---- |
| Phase 1 — Core Unity app (UI, checklists, TTS, voice nav, log) | Phase 3 — FastAPI server, LangChain agent, ChromaDB, GPT-4o |
| Phase 2 — XREAL glasses, NRSDK, HUD overlay | Phase 4 (backend) — WebSocket server, camera CV endpoint, AI log/summary |
| Phase 4 (Unity) — WebSocket client, action\_cmd parsing, HUD alert popups | Phase 5 (AI) — Offline LLM fallback, AI disclaimer, canned safety responses |
| Phase 5 (non-AI) — Offline checklists, multilingual, HIPAA audit, testing | Deployment strategy — local vs cloud inference tradeoffs |

**Integration contract:** The two sides meet at the WebSocket boundary in Phase 4\. The agreed-upon JSON format (`action_cmd` \+ `spoken_response`) is the handshake — define this schema together at the start of Phase 3 so both sides can build against it independently.

---

## Background

**Problem:** Central Line-Associated Bloodstream Infections (CLABSIs) cause \~250,000 infections annually in the US and are a leading cause of death in ICU patients. They are preventable with proper sterile technique, but human error and knowledge decay between trainings lead to inconsistent adherence.

**Solution:** An Android application built in Unity running on XREAL AR glasses that provides real-time, hands-free, step-by-step procedural guidance during central line insertion, maintenance, and removal — with an AI assistant that can be spoken to naturally for clarifications, safety alerts, and suggestions.

**Primary Hardware:** XREAL One Pro ($499 \+ $99 camera) — 1080p, 120Hz, 600 nits, Bose audio, USB-C, 84g, 12MP camera. Processed by XREAL Beam Pro (Android). Budget alternative: XREAL Air 2 Pro ($299, no camera).

---

## Contents

- [System Architecture Overview](#system-architecture-overview)  
- [Phase 1 — Core Unity App](#phase-1--core-unity-app--ui-shell-checklists-voice--tts) 🟦 Zaara  
- [Phase 2 — XREAL Glasses Integration](#phase-2--xreal-glasses-integration--nrsdk-hud-overlay-camera) 🟦 Zaara  
- [Phase 3 — AI Backend](#phase-3--ai-backend--fastapi-langchain-rag-gpt-4o) 🟧 Teammate  
- [Phase 4 — Full Integration](#phase-4--full-integration--websocket-safety-alerts-camera-ai) 🟦🟧 Both  
- [Phase 5 — Polish & Safety](#phase-5--polish--safety--offline-multilingual-hipaa-testing) 🟦🟧 Both  
- [Ethics & Equity Considerations](#ethics--equity-considerations)  
- [Key References](#key-references)

---

## System Architecture Overview

The system connects two major layers: the Android/Unity frontend running on XREAL glasses (🟦 Zaara), and a Mac-hosted FastAPI backend that handles AI reasoning (🟧 Teammate).

| Layer | Technology | Responsibility | Owner |
| :---- | :---- | :---- | :---- |
| AR Glasses | XREAL One Pro \+ NRSDK | HUD display, mic, camera | 🟦 Zaara |
| Mobile App | Unity \+ Android SDK | UI, checklist engine, TTS, voice nav | 🟦 Zaara |
| Wake Word | Porcupine | Hands-free AI trigger | 🟦 Zaara |
| Connectivity | WebSocket (NativeWebSocket) | Real-time bidirectional messaging | 🟦🟧 Both |
| AI Backend | FastAPI \+ Python (Mac) | Request routing, agent orchestration | 🟧 Teammate |
| Agent | LangChain | Intent router, safety gate, tool executor | 🟧 Teammate |
| Knowledge | ChromaDB \+ RAG | CLABSI protocols, CDC guidelines | 🟧 Teammate |
| LLM | GPT-4o (OpenAI) | Conversational AI reasoning | 🟧 Teammate |

**Signal flow:**

XREAL Glasses → Mic → Porcupine wake word → Android STT → Context Manager

→ WebSocket Client → Mac FastAPI Server → LangChain Agent → GPT-4o

→ action\_cmd \+ spoken\_response → Android TTS \+ Unity AR overlay

\[← 🟦 Zaara owns this half ──────────────┤├─────────── 🟧 Teammate owns this half →\]

---

## Phase 1 — Core Unity App — UI Shell, Checklists, Voice & TTS

### 🟦 Zaara

**Goal:** A fully functional Android app (no glasses required yet) with all three procedure checklists, voice navigation, TTS step readout, and local procedure log. This phase validates all UI logic before adding hardware complexity.

🟧 **Teammate note:** No dependencies on Phase 1 — you can start Phase 3 in parallel. The only thing to align on early is the `action_cmd` JSON schema so Zaara can stub out the Unity-side parser while you build the backend.

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

### Build Tasks — 🟦 Zaara

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
- Build Procedure Log page (list view \+ detail view)  
- Store per-procedure: steps completed, timestamps, AI alerts

### Risks & Mitigations

| Risk | Mitigation |
| :---- | :---- |
| Android STT latency | Test early; have tap fallback ready from day 1 |
| TTS pacing | Allow manual re-read trigger in addition to auto-play |
| Step skip attempts | Hard-block skip at the controller level, not just UI |

---

## Phase 2 — XREAL Glasses Integration — NRSDK, HUD Overlay, Camera

### 🟦 Zaara

**Goal:** Port the working Android app to the XREAL glasses. Configure the NRSDK, render the checklist UI on the right-lens HUD, validate hands-free usability, and wire up the XREAL Eye camera for later AI use.

🟧 **Teammate note:** No dependencies on Phase 2\. The camera feed exposed here will be consumed by your Phase 4 breach detection endpoint — just agree on the frame format (JPEG bytes over WebSocket) before Phase 4 starts.

### Key Deliverables

- App running on XREAL glasses via NRSDK  
- Checklist UI rendered as AR overlay on the HUD  
- Overlay positioned non-obtrusively (right lens, lower quadrant)  
- AI alert popup overlay working on HUD  
- Readability validated (font size ≥14pt, high contrast)  
- XREAL camera feed accessible from Unity  
- Microphone input routed through XREAL hardware  
- Full hands-free procedure run tested on glasses

### Build Tasks — 🟦 Zaara

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
| :---- | :---- |
| HUD readability | Test contrast in bright clinical lighting; use white text on dark translucent panel |
| NRSDK canvas mode | WorldSpace canvas requires different coordinate system than Screen Space — plan for refactor |
| USB-C passthrough | Beam Pro must stay connected during procedures; test cable management |

---

## Phase 3 — AI Backend — FastAPI, LangChain, RAG, GPT-4o

### 🟧 Teammate

**Goal:** Build and test the Python AI backend in isolation on Mac before connecting to Unity. This includes the WebSocket server, LangChain agent pipeline, ChromaDB knowledge base with CLABSI protocols, and GPT-4o integration. This maps directly to your system diagram.

🟦 **Zaara note:** No Unity work is blocked on Phase 3 — build Phases 1 & 2 in parallel. The one shared dependency is the `action_cmd` JSON schema — agree on this with your teammate at the start so you can stub the Unity-side parser early without waiting for the real backend.

### Your system diagram mapped to this phase

| Your diagram component | Build guide task |
| :---- | :---- |
| Multimodal Interaction Pipeline | Voice → STT wired in Phase 4; LLM reasoning built here |
| Backend AI Architecture (FastAPI WebSocket) | FastAPI WebSocket server |
| LLM Agent System — Intent Router | LangChain Intent Router |
| LLM Agent System — Safety Gate | LangChain Safety Gate |
| LLM Agent System — Tool Executor | LangChain Tool Executor |
| Knowledge & Context Management (RAG \+ ChromaDB) | ChromaDB \+ RAG pipeline \+ Context Manager |
| Deployment Strategy (local vs cloud) | GPT-4o integration \+ local LLM fallback plan |
| Real-Time App Control | action\_cmd schema → consumed by Unity in Phase 4 |

### Key Deliverables

- FastAPI WebSocket server running locally on Mac  
- LangChain agent: Intent Router → Safety Gate → Tool Executor  
- ChromaDB populated with CDC CLABSI guidelines and sterile technique protocols  
- RAG pipeline retrieving relevant context per query  
- GPT-4o generating accurate, domain-specific responses  
- Context manager maintaining session state across turns  
- JSON `action_cmd` \+ `spoken_response` output format defined and shared with Zaara  
- Fully tested via curl/Postman before Unity connection

### Build Tasks — 🟧 Teammate

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
- Define and publish `action_cmd` schema — share with Zaara before Phase 4  
- Write system prompt enforcing clinical safety boundaries  
- Test all intents manually before Unity integration

**Deployment**

- Evaluate local inference (Ollama \+ Llama 3\) vs GPT-4o cloud for latency/cost  
- Document tradeoffs and recommended approach for team review

### Action Command Schema (define together, build against independently)

{

  "action\_cmd": "show\_alert",

  "parameters": {

    "severity": "warning",

    "message": "Hand hygiene not confirmed before gloving."

  },

  "spoken\_response": "Please confirm hand hygiene was performed before putting on sterile gloves."

}

Supported `action_cmd` values: `next_step`, `prev_step`, `show_alert`, `read_step`, `flag_breach`, `end_procedure`, `navigate_home`

### Risks & Mitigations

| Risk | Mitigation |
| :---- | :---- |
| GPT-4o latency | Target \<2s response; cache common safety alerts locally |
| RAG hallucination | Always inject retrieved context; do not rely on model memory alone |
| Safety gate over-blocking | Tune iteratively; log all blocked requests for review |
| Network dependency | Plan local LLM fallback (e.g. Ollama \+ Llama 3\) for offline clinical environments |

---

## Phase 4 — Full Integration — WebSocket, Safety Alerts, Camera AI

### 🟦🟧 Both — split by layer

**Goal:** Connect the Unity frontend to the Mac AI backend via WebSocket. Wire up the full voice-to-AI pipeline end-to-end, add real-time safety alert overlays, and integrate camera-based breach detection.

This is the integration phase. Both sides build against the agreed `action_cmd` schema. Zaara owns the Unity client; teammate owns the FastAPI server side and camera CV endpoint.

### Key Deliverables

- Unity WebSocket client connected to FastAPI backend (🟦 Zaara)  
- FastAPI WebSocket server accepting Unity connections (🟧 Teammate)  
- Full voice pipeline: XREAL mic → Porcupine → STT → backend → GPT-4o → TTS (🟦🟧 Both)  
- AI responses displayed as AR overlay popups in real time (🟦 Zaara)  
- AI safety alerts logged to procedure log with timestamps (🟦🟧 Both)  
- Camera feed analyzed for sterile field breaches (🟧 Teammate)  
- Post-procedure AI summary — missed steps, compliance score, time elapsed (🟧 Teammate)  
- Procedure log updated with all AI observations (🟦 Zaara)  
- End-to-end test of all three procedures with AI active (🟦🟧 Both)

### Build Tasks — 🟦 Zaara (Unity client side)

- Add `NativeWebSocket` to Unity project  
- Implement WebSocket client (connect, send, receive, auto-reconnect with backoff)  
- Wire STT output to WebSocket send pipeline  
- Parse `action_cmd` JSON responses in Unity  
- Map action commands to Unity AR actions (advance step, show alert, read step, etc.)  
- Route `spoken_response` to Android TTS  
- Display AI alert as HUD overlay popup with auto-dismiss timeout  
- Integrate Porcupine wake word detection in Unity/Android  
- Add visual/audio cue when wake word is detected  
- Implement camera frame capture and send to backend (JPEG bytes)  
- Display post-procedure summary on completion screen  
- Log all AI alerts and warnings to local procedure log

### Build Tasks — 🟧 Teammate (backend side)

- Confirm FastAPI WebSocket server accepts Unity client connections  
- Handle incoming voice text messages and route through LangChain agent  
- Return `action_cmd` \+ `spoken_response` JSON to Unity client  
- Add computer vision endpoint for sterile field breach detection (receives JPEG frames)  
- Run CV inference asynchronously (never block step progression)  
- Build post-procedure summary generation (LLM summarization call)  
- Write compliance score calculation logic (steps completed vs total, time per step)  
- Log all agent decisions and alerts server-side for debugging

### Risks & Mitigations

| Risk | Mitigation |
| :---- | :---- |
| WebSocket reconnect | Implement exponential backoff on Unity side; show user indicator when disconnected |
| Camera analysis latency | Run CV inference async on backend; never block step progression on AI response |
| Wake word false positives | Tune Porcupine sensitivity; add confirmation audio cue before STT activates |
| AI hallucination on camera | Flag detections as advisory only; human remains decision-maker at all times |
| Schema mismatch | Agree on `action_cmd` schema before either side builds Phase 4 — put it in a shared doc |

---

## Phase 5 — Polish & Safety — Offline Mode, Multilingual, HIPAA, Testing

### 🟦🟧 Both — split by concern

**Goal:** Harden the app for real clinical environments. Ensure it works fully offline, meets HIPAA data handling requirements, supports multiple languages, and passes end-to-end testing across all hardware and procedure types.

### Key Deliverables

- Full offline mode: checklists, TTS, and graceful AI fallback (🟦🟧 Both)  
- Multilingual support — Spanish minimum (🟦 Zaara)  
- Visual aids to reduce language dependency for critical steps (🟦 Zaara)  
- HIPAA-compliant data handling — encrypted logs, consent flow (🟦 Zaara)  
- Clear on-screen AI confidence indicator and disclaimer (🟦🟧 Both)  
- Passed full end-to-end test suite on physical XREAL glasses, UC-01 through UC-30 (🟦🟧 Both)  
- Clinical staff quick-start documentation (🟦🟧 Both)

### Build Tasks — 🟦 Zaara

**Offline Mode (Unity side)**

- Store all checklists as local JSON (no network required)  
- Cache TTS audio files for all steps  
- Implement graceful UI state when backend is unreachable  
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
- Test with XREAL glasses connected (all three procedures end-to-end)  
- Performance test: memory, battery, thermal on Beam Pro  
- Test offline mode end-to-end with no network connection  
- Test exit and re-launch state persistence

### Build Tasks — 🟧 Teammate

**Offline AI Fallback**

- Pre-generate canned safety responses for the most critical alert types  
- Package canned responses for Unity to load locally when backend unreachable  
- Evaluate and document local LLM option (Ollama \+ Llama 3\) as full offline fallback

**Documentation**

- Document AI system boundaries and limitations for institutional use  
- Document deployment options (local Mac vs cloud) with tradeoffs

### Risks & Mitigations

| Risk | Mitigation |
| :---- | :---- |
| Offline AI quality | Pre-generate canned safety responses for critical alerts; package with app |
| HIPAA scope creep | Involve a compliance advisor early; document every data touchpoint |
| Translation accuracy | Use professional medical translation — not auto-translate — for clinical step text |
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
