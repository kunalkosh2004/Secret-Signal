import asyncio
import json

import websockets


TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwiZXhwIjoxNzgzNTk3Mjc0fQ.ZcVl4d6rMqzL4KcpZHgYhXHbNHVeKcGWaTQTlq4TytY"
ROOM_CODE = "UCR6T0"


async def main():
    url = (
        f"ws://127.0.0.1:8000/ws"
        f"?token={TOKEN}"
        f"&room_code={ROOM_CODE}"
    )

    async with websockets.connect(url) as websocket:
        print("Connected")

        message = await websocket.recv()

        data = json.loads(message)

        print(
            json.dumps(
                data,
                indent=2,
            )
        )


asyncio.run(main())