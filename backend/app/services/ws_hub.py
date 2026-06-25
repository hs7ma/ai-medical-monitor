import asyncio
import json
from typing import Set

from fastapi import WebSocket


class WebSocketHub:
    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections.discard(ws)

    async def broadcast_vitals(self, data: dict):
        message = json.dumps({"type": "vitals", "data": data})
        dead = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        async with self._lock:
            for ws in dead:
                self._connections.discard(ws)

    async def broadcast_alert(self, alert: dict):
        message = json.dumps({"type": "alert", "data": alert})
        dead = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        async with self._lock:
            for ws in dead:
                self._connections.discard(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


ws_hub = WebSocketHub()
