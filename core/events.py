"""
Event system for real-time streaming to the UI.
Uses asyncio.Queue so SSE clients can subscribe to progress.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncIterator


class EventBus:
    """Simple pub/sub event bus for streaming orchestration progress."""

    def __init__(self):
        self._queues: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._queues:
            self._queues.remove(q)

    async def publish(self, event_type: str, data: dict):
        msg = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        dead = []
        for q in self._queues:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self.unsubscribe(q)

    async def stream(self, q: asyncio.Queue) -> AsyncIterator[dict]:
        """Generator for SSE."""
        try:
            while True:
                msg = await q.get()
                yield msg
                if msg.get("type") == "complete":
                    break
        except asyncio.CancelledError:
            pass
        finally:
            self.unsubscribe(q)


# Global singleton
bus = EventBus()
