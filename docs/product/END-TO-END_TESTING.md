# END-TO-END_TESTING

This repo is on `main`, and at handoff time local `main` matched `origin/main` at:

```text
4d1198278cfecb10901e78cb35066acd53a29811
```

Repository:

```text
https://github.com/kgarg2468/gci-layerjot.git
```

Use `unity/` as the CLABSI app project. `XREALSDK/` is the XREAL SDK/sample reference project, not the main app to test.

## What This Runs

The system has two parts:

1. Unity Android app in `unity/`
   - Checklist UI
   - Android speech recognition for commands and AI questions
   - Android TTS
   - AI WebSocket client
   - AI alert/action executor

2. Python backend on a laptop in `backend/`
   - FastAPI WebSocket server at `/ws`
   - LangChain/OpenAI orchestration
   - RAG over CLABSI protocol docs
   - Safety checks
   - `action_cmd` responses for Unity

The glasses/Android device must connect to the laptop over local Wi-Fi.

## Important Networking Detail

Do not use `127.0.0.1` from the glasses. On Android, `127.0.0.1` means the Android device itself, not the backend laptop.

Use the laptop's Wi-Fi LAN IP instead:

```text
ws://LAPTOP_IP:8000/ws
```

Example:

```text
ws://192.168.1.42:8000/ws
```

The backend must also be started with `--host 0.0.0.0`; the included `scripts/run_backend.sh` binds to `127.0.0.1`, which is only for same-machine testing.

## Backend Setup

On the backend laptop:

```bash
git clone https://github.com/kgarg2468/gci-layerjot.git
cd gci-layerjot

python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r mac_client/requirements.txt

cp .env.example .env
```

Edit `.env` and set:

```text
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0
```

Find the laptop IP:

```bash
ipconfig getifaddr en0
```

If that prints nothing, try:

```bash
ifconfig | grep "inet "
```

Start the backend for glasses testing:

```bash
export PYTHONPATH="$PWD"
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Keep this terminal open while testing.

Health check from another device on the same Wi-Fi:

```text
http://LAPTOP_IP:8000/health
```

Expected response:

```json
{"status":"ok"}
```

If the health check fails, check that both devices are on the same Wi-Fi, VPN is off, and the laptop firewall allows incoming connections on port `8000`.

## Optional Backend Smoke Test

From the backend laptop, this confirms the AI WebSocket works before Unity is involved:

```bash
.venv/bin/python - <<'PY'
import asyncio, json, websockets

async def main():
    async with websockets.connect("ws://127.0.0.1:8000/ws") as ws:
        await ws.send(json.dumps({
            "type": "ai_request",
            "session_id": "zara-smoke-test",
            "timestamp": "2026-05-07T00:00:00Z",
            "payload": {
                "transcript": "what is the patient's heart rate",
                "context": {
                    "session_id": "zara-smoke-test",
                    "patient_id": "PAT-123",
                    "current_screen": "home",
                    "procedure_active": False
                }
            }
        }))
        print(await ws.recv())

asyncio.run(main())
PY
```

You should see an `ai_response` with `spoken_response` and an `action_cmd`.

## Unity Setup

1. Open Unity Hub.
2. Use Unity `6000.4.0f1`.
3. Open the repo's `unity/` folder as the project.
4. Let Unity finish importing packages.
5. Open `Assets/Scenes/SampleScene.unity`.
6. Go to `File -> Build Settings`.
7. Switch platform to `Android`.
8. Use a normal Android build first if possible, then test with the XREAL/Beam Pro setup.

The key script for backend connection is:

```text
unity/Assets/Scripts/AI/AiWebSocketClient.cs
```

Its serialized `backendUrl` default is:

```text
ws://127.0.0.1:8000/ws
```

Before building to Android/glasses, select the GameObject with `AiWebSocketClient` in the scene and set `Backend Url` to:

```text
ws://LAPTOP_IP:8000/ws
```

If the scene does not already have AI objects wired in, add an empty GameObject named `AIBackend` and attach:

```text
AiWebSocketClient
AiContextProvider
AiActionExecutor
```

For visible alerts, add or verify an alert UI object with:

```text
AiAlertOverlay
CanvasGroup
Text assigned to messageText
```

The app shows backend connection state through `AiBackendStatusIndicator` if that component is wired to a UI Text.

## Build And Run On Glasses

1. Start the backend first.
2. Confirm `http://LAPTOP_IP:8000/health` returns `{"status":"ok"}`.
3. In Unity, confirm `AiWebSocketClient.backendUrl` uses `ws://LAPTOP_IP:8000/ws`.
4. Connect the Android device / Beam Pro used with the XREAL glasses.
5. Build and Run from Unity.
6. Grant microphone permission when prompted.
7. Put on/connect the glasses and confirm the app is visible.
8. Confirm the app shows `AI online` if the status indicator is present.

## Manual Test Script

Test local app flow first:

1. Open the app.
2. Tap `Procedures`.
3. Start `Insert`.
4. Use voice or buttons for:
   - `next`
   - `done`
   - `home`
   - `procedures`
5. Confirm steps advance in order and cannot be skipped incorrectly.

Test AI questions:

1. Press the mic/listen button.
2. Ask: `what is the patient's heart rate`
   - Expected: backend returns patient vitals for `PAT-123`; Unity speaks the answer.
3. Ask: `open central line checklist`
   - Expected: backend returns a navigation/read action; Unity should handle the `action_cmd`.
4. Ask: `what sterile precautions are required before insertion`
   - Expected: backend returns a CLABSI/sterile technique answer from RAG.
5. Ask: `what medication dose should I give`
   - Expected: safety block. Unity should show/speak a warning, not dosing advice.

Test procedure-aware alerts:

1. Start an insertion procedure.
2. Before completing hand hygiene, ask something like:
   - `can I move to gloving now`
3. Expected: backend returns `show_alert` asking to confirm required prior steps.

## Expected Backend Response Shape

Unity should prefer these top-level fields:

```json
{
  "type": "ai_response",
  "schema_version": "clabsi-ar.v1",
  "session_id": "sess-001",
  "timestamp": "2026-05-07T00:00:00Z",
  "action_cmd": "show_alert",
  "parameters": {
    "severity": "warning",
    "message": "Please confirm hand hygiene before continuing."
  },
  "spoken_response": "Please confirm hand hygiene before continuing.",
  "payload": {
    "intent": "safety_block",
    "spoken_response": "Please confirm hand hygiene before continuing.",
    "action": null
  }
}
```

Supported `action_cmd` values:

```text
next_step
prev_step
show_alert
read_step
flag_breach
end_procedure
navigate_home
```

## Troubleshooting

If Unity says AI offline:

1. Make sure backend was started with `--host 0.0.0.0`.
2. Make sure Unity uses `ws://LAPTOP_IP:8000/ws`, not `127.0.0.1`.
3. Open `http://LAPTOP_IP:8000/health` from the Android device browser.
4. Check laptop firewall/VPN.
5. Watch the backend terminal for `WebSocket client connected`.

If speech does not work:

1. Confirm Android microphone permission was granted.
2. Test tapping the mic/listen button.
3. Try clear command phrases: `next`, `done`, `home`, `procedures`.
4. Unknown voice text is sent to AI; known command phrases are handled locally.

If AI answers fail:

1. Confirm `.env` has `OPENAI_API_KEY`.
2. Restart the backend after editing `.env`.
3. Check the backend terminal logs.
4. Try the optional backend smoke test above.

If RAG/protocol answers are weak on first run:

1. Keep the backend running through startup; it may ingest `backend/docs`.
2. Confirm `backend/chroma_db/` exists after startup.
3. Ask the sterile precautions prompt again.

## Files To Know

```text
readme.md
docs/product/ai-action-contract.md
docs/product/CLABSI_AR_Build_Guide_v2.md
backend/main.py
backend/orchestrator.py
backend/safety.py
unity/Assets/Scripts/AI/AiWebSocketClient.cs
unity/Assets/Scripts/AI/AiActionExecutor.cs
unity/Assets/Scripts/AI/AiModels.cs
unity/Assets/Scripts/Voice/VoiceService.cs
unity/Assets/Scenes/SampleScene.unity
```

## Notes

- This is a demo prototype, not a clinical product.
- AI output is advisory only.
- Do not enter real patient data.
- Use mock patient `PAT-123` for tests.
- The Mac terminal client in `mac_client/` is useful for backend demos, but it is not the glasses app.
