import asyncio
from typing import List
import json

class SSEManager:
    """
    Manages active SSE connections for real-time signaling.
    """
    def __init__(self):
        self.listeners: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        """
        Accept and store a new client SSE connection via a Queue.
        """
        q = asyncio.Queue()
        self.listeners.append(q)
        print(f"SSE client connected. Total active connections: {len(self.listeners)}")
        return q

    def unsubscribe(self, q: asyncio.Queue):
        """
        Remove a client SSE connection from active list.
        """
        if q in self.listeners:
            self.listeners.remove(q)
            print(f"SSE client disconnected. Total active connections: {len(self.listeners)}")

    async def broadcast(self, message: dict):
        """
        Send a JSON message to all currently connected clients.
        """
        data = json.dumps(message)
        for q in self.listeners:
            await q.put(data)

# Single global instance for import across routes/services
manager = SSEManager()
