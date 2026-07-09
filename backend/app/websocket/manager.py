from collections import defaultdict

from fastapi import WebSocket


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
    
    def disconnect(
        self,
        room_code: str,
        user_id: int,
    ) -> None:
        room_connections = self.active_connections.get(room_code)

        if room_connections is None:
            return

        room_connections.pop(user_id, None)

        if not room_connections:
            self.active_connections.pop(room_code, None)
    
    async def broadcast_to_room(
        self,
        room_code: str,
        message: dict,
    ) -> None:
        room_connections = self.active_connections.get(
            room_code,
            {},
        )

        for websocket in room_connections.values():
            await websocket.send_json(message)

manager = ConnectionManager()