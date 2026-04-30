# GCI Mac-Only MVP

This repository now includes a Mac-only two-process MVP:
- `backend`: FastAPI WebSocket server + LangChain orchestrator + safety + tools + RAG
- `mac_client`: terminal push-to-talk voice client with OpenAI STT + macOS TTS (`say`)

Product references for coding agents live in [`docs/`](docs/), including the CLABSI AR glasses use cases, implementation checklist, and full AR build guide.

## 1) Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r mac_client/requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`.

## 2) Optional RAG ingest

```bash
python3 -m backend.rag.ingest
```

## 3) Run

Single command:

```bash
./scripts/run_demo.sh
```

Or separate terminals:

```bash
./scripts/run_backend.sh
./scripts/run_client.sh
```

## 4) Client commands

- `[Enter]`: push-to-talk voice query
- `/text <message>`: typed query path
- `/patient <id|none>`: update context patient
- `/screen <name>`: update context screen
- `/state`: print current context
- `/quit`: exit

## 5) Acceptance checks

1. `what is the patient's heart rate` -> `retrieve_data`
2. `open central line checklist` -> `navigate` + `open_screen`
3. `what sterile precautions are required before insertion` -> `rag`
4. Diagnosis or dosing prompts -> `safety_block`
