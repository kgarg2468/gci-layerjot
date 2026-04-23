from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict

import websockets

from mac_client.config import settings


class BackendWSClient:
    def __init__(self) -> None:
        self._ws = None

    async def connect(self) -> None:
        backoff = [1, 2, 4, 8, 16]
        last_error: Exception | None = None

        for wait_seconds in backoff:
            try:
                self._ws = await websockets.connect(settings.backend_ws_url)
                return
            except Exception as exc:  # pragma: no cover - network failures
                last_error = exc
                await asyncio.sleep(wait_seconds)

        raise RuntimeError(f"Unable to connect to backend websocket: {last_error}")

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()

    async def send_ai_request(self, transcript: str, context: dict, session_id: str) -> Dict[str, Any]:
        envelope = {
            "type": "ai_request",
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "transcript": transcript,
                "context": context,
            },
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
        except websockets.ConnectionClosed:
            self._ws = None
            await self.connect()
            return await _attempt()
