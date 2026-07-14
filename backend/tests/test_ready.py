import asyncio
import json

import websockets


TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwiZXhwIjoxNzgzNjE4NTQ0fQ.6g3TsNI0zQ0NbPHU4LdanWvR_1CXvOd74EvsuGiT4sc"
ROOM_CODE = "W53D68"


async def main():
    url = (
        f"ws://127.0.0.1:8000/ws"
        f"?token={TOKEN}"
        f"&room_code={ROOM_CODE}"
    )

    async with websockets.connect(url) as websocket:
        print("Connected")

        initial_message = await websocket.recv()
        initial_data = json.loads(initial_message)

        print("\nINITIAL STATE")
        print(
            json.dumps(
                initial_data,
                indent=2,
            )
        )

        await websocket.send(
            json.dumps(
                {
                    "type": "PLAYER_READY",
                    "payload": {
                        "ready": True,
                    },
                }
            )
        )

        print("\nPLAYER_READY sent")

        while True:
            message = await websocket.recv()
            data = json.loads(message)

            print(f"\nReceived: {data.get('type')}")

            if data.get("type") == "ROOM_STATE":
                print(
                    json.dumps(
                        data,
                        indent=2,
                    )
                )

                current_player = next(
                    (
                        player
                        for player in data["players"]
                        if player["is_ready"] is True
                    ),
                    None,
                )

                if current_player is not None:
                    print(
                        "\nPLAYER_READY test successful"
                    )
                    break


asyncio.run(main())