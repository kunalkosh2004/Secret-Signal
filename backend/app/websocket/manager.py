"""
WebSocket ConnectionManager with Redis presence tracking.

The in-memory dict is kept for fast local lookups (broadcast speed),
while Redis tracks presence for cross-process visibility and reconnect recovery.
"""

from collections import defaultdict

from fastapi import WebSocket

from app.core.redis_presence import track_presence, remove_presence


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[
            str,
            dict[int, WebSocket],
        ] = defaultdict(dict)

    async def connect(
        self,
        room_code: str,
        user_id: int,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()
        self.active_connections[room_code][user_id] = websocket
        await track_presence(room_code, user_id)

    def disconnect(
        self,
        room_code: str,
        user_id: int,
        websocket: WebSocket | None = None,
    ) -> None:
        room_connections = self.active_connections.get(room_code)

        if room_connections is None:
            return

        current = room_connections.get(user_id)
        if current is not None and (websocket is None or current is websocket):
            room_connections.pop(user_id, None)

        if not room_connections:
            self.active_connections.pop(room_code, None)

    async def async_disconnect(
        self,
        room_code: str,
        user_id: int,
        websocket: WebSocket | None = None,
    ) -> None:
        """Disconnect and remove Redis presence."""
        self.disconnect(room_code, user_id, websocket)
        await remove_presence(room_code, user_id)

    async def send_to_user(
        self,
        room_code: str,
        user_id: int,
        message: dict,
    ) -> bool:
        room_connections = self.active_connections.get(
            room_code,
            {},
        )

        websocket = room_connections.get(user_id)

        if websocket is None:
            return False

        try:
            await websocket.send_json(message)
            return True
        except Exception:
            self.disconnect(room_code, user_id)
            return False

    async def broadcast_to_room(
        self,
        room_code: str,
        message: dict,
    ) -> None:
        room_connections = self.active_connections.get(
            room_code,
            {},
        )

        dead_connections: list[int] = []

        for user_id, websocket in room_connections.items():
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.append(user_id)

        for user_id in dead_connections:
            self.disconnect(room_code, user_id)


manager = ConnectionManager()
