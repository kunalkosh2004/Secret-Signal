import asyncio
import json
import urllib.request

import websockets


HOST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwiZXhwIjoxNzgzNjExMzk5fQ.h4gmdwopnnj8OHaIcBMcLr8sVeO_-yx8W2EoiT4oInw"
PLAYER_2_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3IiwiZXhwIjoxNzgzNjExNDEyfQ.bVOgQfxHGqwNFe9Y-ElUz8C1CBc-QFk4sHbUWsLJGrA"
PLAYER_3_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4IiwiZXhwIjoxNzgzNjExNjIzfQ.nZhqO8H3lqmJR-u2cSJU2LajoHSNAv4Er0azVpsMpLM"

ROOM_CODE = "9UDKSA"


async def listen_to_events(
    name: str,
    token: str,
    connected_event: asyncio.Event,
):
    url = (
        f"ws://127.0.0.1:8000/ws"
        f"?token={token}"
        f"&room_code={ROOM_CODE}"
    )

    async with websockets.connect(url) as websocket:
        print(f"{name}: Connected")

        connected_event.set()

        initial_message = await websocket.recv()

        print(f"\n{name}: Initial event")

        print(
            json.dumps(
                json.loads(initial_message),
                indent=2,
            )
        )

        connected_event.set()

        for _ in range(2):
            message = await websocket.recv()

            data = json.loads(message)

            print(
                f"\n{name}: Received"
            )

            print(
                json.dumps(
                    data,
                    indent=2,
                )
            )


def start_game_request():
    url = (
        f"http://127.0.0.1:8000"
        f"/api/v1/games/{ROOM_CODE}/start"
    )

    request = urllib.request.Request(
        url=url,
        method="POST",
        headers={
            "Authorization": f"Bearer {HOST_TOKEN}",
        },
    )

    with urllib.request.urlopen(request) as response:
        body = response.read().decode()

        print("\nSTART GAME RESPONSE:")

        print(
            json.dumps(
                json.loads(body),
                indent=2,
            )
        )


async def main():
    host_connected = asyncio.Event()
    player_2_connected = asyncio.Event()
    player_3_connected = asyncio.Event()

    tasks = [
        asyncio.create_task(
            listen_to_events(
                "HOST",
                HOST_TOKEN,
                host_connected,
            )
        ),
        asyncio.create_task(
            listen_to_events(
                "PLAYER 2",
                PLAYER_2_TOKEN,
                player_2_connected,
            )
        ),
        asyncio.create_task(
            listen_to_events(
                "PLAYER 3",
                PLAYER_3_TOKEN,
                player_3_connected,
            )
        ),
    ]

    await asyncio.gather(
        host_connected.wait(),
        player_2_connected.wait(),
        player_3_connected.wait(),
    )

    print("\nAll players connected.")

    await asyncio.sleep(1)

    await asyncio.to_thread(
        start_game_request
    )

    await asyncio.gather(*tasks)


asyncio.run(main())