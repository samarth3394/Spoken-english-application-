"""
Aspire English Hub - WebSocket Manager
========================================
Manages WebSocket connections for real-time features.
"""

from fastapi import WebSocket
from typing import Dict, Set, Optional
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages all WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # user_id -> WebSocket
        self.call_rooms: Dict[str, Set[str]] = {}  # call_id -> set of user_ids

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        # Remove from any call rooms
        for call_id, users in list(self.call_rooms.items()):
            if user_id in users:
                users.discard(user_id)
                if not users:
                    del self.call_rooms[call_id]
        logger.info(f"WebSocket disconnected: {user_id}")

    async def send_to_user(self, user_id: str, message: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Send error to {user_id}: {str(e)}")
                self.disconnect(user_id)

    async def broadcast(self, message: dict, exclude: str = None):
        disconnected = []
        for uid, ws in self.active_connections.items():
            if uid != exclude:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(uid)
        for uid in disconnected:
            self.disconnect(uid)

    def join_call_room(self, call_id: str, user_id: str):
        if call_id not in self.call_rooms:
            self.call_rooms[call_id] = set()
        self.call_rooms[call_id].add(user_id)

    def leave_call_room(self, call_id: str, user_id: str):
        if call_id in self.call_rooms:
            self.call_rooms[call_id].discard(user_id)
            if not self.call_rooms[call_id]:
                del self.call_rooms[call_id]

    async def send_to_call_room(self, call_id: str, message: dict, exclude: str = None):
        users = self.call_rooms.get(call_id, set())
        for uid in users:
            if uid != exclude:
                await self.send_to_user(uid, message)

    def get_call_partner(self, call_id: str, user_id: str) -> Optional[str]:
        users = self.call_rooms.get(call_id, set())
        for uid in users:
            if uid != user_id:
                return uid
        return None

    def is_online(self, user_id: str) -> bool:
        return user_id in self.active_connections

    def get_online_count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()
