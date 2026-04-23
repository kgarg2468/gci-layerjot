from __future__ import annotations

import asyncio
from pathlib import Path

from openai import AsyncOpenAI

from mac_client.config import settings


class OpenAITranscriber:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for STT transcription.")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe(self, audio_file: Path) -> str:
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                with audio_file.open("rb") as handle:
                    response = await self._client.audio.transcriptions.create(
                        model=settings.stt_model,
                        file=handle,
                        language=settings.stt_language,
                    )
                text = (response.text or "").strip()
                if not text:
                    raise RuntimeError("Transcription returned empty text.")
                return text
            except Exception as exc:  # pragma: no cover - network failures
                last_error = exc
                await asyncio.sleep(2**attempt)

        raise RuntimeError(f"STT transcription failed: {last_error}")
