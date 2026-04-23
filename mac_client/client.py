from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from mac_client.audio import record_push_to_talk
from mac_client.config import settings
from mac_client.context import ClientContext
from mac_client.stt import OpenAITranscriber
from mac_client.tts import speak
from mac_client.ws_client import BackendWSClient


HELP_TEXT = """
Commands:
  [Enter]             Record push-to-talk voice query
  /text <message>     Send typed transcript
  /patient <id|none>  Set patient id in context
  /screen <name>      Set current screen in context
  /state              Print current context
  /quit               Exit client
""".strip()


def _apply_action(context: ClientContext, action: dict[str, Any] | None) -> None:
    if not action:
        return

    action_type = action.get("type")
    params = action.get("params", {})

    if action_type == "open_screen":
        screen = params.get("screen")
        if isinstance(screen, str) and screen:
            context.current_screen = screen
            print(f"[ACTION] Updated current_screen -> {screen}")
            return

    print(f"[ACTION] Unsupported action ignored: {action}")


async def _capture_transcript(transcriber: OpenAITranscriber) -> str:
    audio_path = Path(tempfile.gettempdir()) / f"gci-{uuid4()}.wav"
    try:
        await asyncio.to_thread(
            record_push_to_talk,
            audio_path,
            settings.sample_rate,
            1,
            settings.max_record_seconds,
        )
        transcript = await transcriber.transcribe(audio_path)
        return transcript
    finally:
        if audio_path.exists():
            audio_path.unlink(missing_ok=True)


async def run() -> None:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to run the mac_client.")

    context = ClientContext.create_default()
    ws_client = BackendWSClient()
    transcriber = OpenAITranscriber()

    await ws_client.connect()

    print("GCI Mac Client started.")
    print(f"Connected to: {settings.backend_ws_url}")
    print(HELP_TEXT)

    try:
        while True:
            raw = await asyncio.to_thread(input, "gci> ")
            command = raw.strip()

            if command == "/quit":
                break

            if command == "/state":
                print(context.to_payload())
                continue

            if command.startswith("/patient "):
                patient_value = command.split(" ", 1)[1].strip()
                context.patient_id = None if patient_value.lower() == "none" else patient_value
                print(f"[STATE] patient_id -> {context.patient_id}")
                continue

            if command.startswith("/screen "):
                screen = command.split(" ", 1)[1].strip()
                context.current_screen = screen
                print(f"[STATE] current_screen -> {context.current_screen}")
                continue

            if command.startswith("/text "):
                transcript = command.split(" ", 1)[1].strip()
            else:
                try:
                    transcript = await _capture_transcript(transcriber)
                    print(f"[STT] {transcript}")
                except Exception as exc:
                    print(f"[STT ERROR] {exc}")
                    continue

            if not transcript:
                print("[WARN] Empty transcript, skipping.")
                continue

            try:
                response = await ws_client.send_ai_request(
                    transcript=transcript,
                    context=context.to_payload(),
                    session_id=context.session_id,
                )
            except Exception as exc:
                print(f"[WS ERROR] {exc}")
                continue

            payload = response.get("payload", {})
            intent = payload.get("intent", "unknown")
            spoken = payload.get("spoken_response", "")
            action = payload.get("action")

            print(f"[INTENT] {intent}")
            print(f"[RESPONSE] {spoken}")
            debug = payload.get("debug") or {}
            latency = debug.get("latency_ms")
            if latency is not None:
                print(f"[LATENCY] {latency} ms")
            if action is not None:
                print(f"[ACTION] {action}")

            _apply_action(context, action)
            await asyncio.to_thread(speak, spoken)

    finally:
        await ws_client.close()


if __name__ == "__main__":
    asyncio.run(run())
