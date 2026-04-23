from __future__ import annotations

import asyncio
import json

from websockets.exceptions import ConnectionClosedOK
from websockets.frames import Close

from mac_client.ws_client import BackendWSClient


def _closed_exc() -> ConnectionClosedOK:
    return ConnectionClosedOK(Close(1000, ""), Close(1000, ""), True)


class _FakeWebSocket:
    def __init__(self, *, send_exception=None, recv_exception=None, recv_messages=None):
        self._send_exception = send_exception
        self._recv_exception = recv_exception
        self._recv_messages = list(recv_messages or [])
        self.sent_payloads = []

    async def send(self, payload: str) -> None:
        self.sent_payloads.append(payload)
        if self._send_exception is not None:
            exc = self._send_exception
            self._send_exception = None
            raise exc

    async def recv(self) -> str:
        if self._recv_exception is not None:
            exc = self._recv_exception
            self._recv_exception = None
            raise exc
        if not self._recv_messages:
            raise AssertionError("recv called with no queued messages")
        return self._recv_messages.pop(0)


def test_send_ai_request_reconnects_once_after_send_close(monkeypatch):
    first_ws = _FakeWebSocket(send_exception=_closed_exc())
    second_ws = _FakeWebSocket(
        recv_messages=[
            json.dumps(
                {
                    "type": "ai_response",
                    "payload": {"spoken_response": "ok"},
                }
            )
        ]
    )
    websockets = iter([first_ws, second_ws])
    connect_calls = 0

    async def fake_connect(self):
        nonlocal connect_calls
        connect_calls += 1
        self._ws = next(websockets)

    monkeypatch.setattr(BackendWSClient, "connect", fake_connect)
    client = BackendWSClient()

    result = asyncio.run(client.send_ai_request("hi", {"patient_id": "PAT-123"}, "sess-1"))

    assert result["type"] == "ai_response"
    assert connect_calls == 2
    assert len(second_ws.sent_payloads) == 1


def test_send_ai_request_reconnects_once_after_recv_close(monkeypatch):
    first_ws = _FakeWebSocket(recv_exception=_closed_exc())
    second_ws = _FakeWebSocket(
        recv_messages=[
            json.dumps(
                {
                    "type": "ai_response",
                    "payload": {"spoken_response": "ok"},
                }
            )
        ]
    )
    websockets = iter([first_ws, second_ws])
    connect_calls = 0

    async def fake_connect(self):
        nonlocal connect_calls
        connect_calls += 1
        self._ws = next(websockets)

    monkeypatch.setattr(BackendWSClient, "connect", fake_connect)
    client = BackendWSClient()

    result = asyncio.run(client.send_ai_request("hi", {"patient_id": "PAT-123"}, "sess-1"))

    assert result["type"] == "ai_response"
    assert connect_calls == 2
    assert len(first_ws.sent_payloads) == 1
    assert len(second_ws.sent_payloads) == 1
