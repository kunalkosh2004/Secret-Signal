"""
Simulate a full game with chat messages to populate the analytics.
Usage: uv run python -m tests.simulate_game
"""

import asyncio
import json
import random
import httpx

BASE = "http://localhost:8000/api/v1"
WS_BASE = "ws://localhost:8000/api/v1/ws"

SIGNUP_EMAILS = [f"player_{i}@test.com" for i in range(1, 6)]
PASSWORD = "testpass123"

tokens = {}
user_ids = {}


async def signup(email, idx):
    async with httpx.AsyncClient() as cl:
        res = await cl.post(
            f"{BASE}/auth/signup",
            json={"username": f"Player{idx}", "email": email, "password": PASSWORD},
        )
        if res.status_code == 201:
            tok = res.json()["access_token"]
            uid = res.json()["user"]["id"]
            print(f"  Created {email}: user_id={uid}")
            tokens[email] = tok
            user_ids[email] = uid
            return tok, uid
        elif res.status_code == 409:
            print(f"  User {email} exists, logging in")
            res = await cl.post(
                f"{BASE}/auth/login",
                json={"email": email, "password": PASSWORD},
            )
            tok = res.json()["access_token"]
            uid = res.json()["user"]["id"]
            tokens[email] = tok
            user_ids[email] = uid
            return tok, uid
        else:
            print(f"  Failed for {email}: {res.text}")
            return None, None


async def create_room(tok):
    async with httpx.AsyncClient() as cl:
        res = await cl.post(
            f"{BASE}/rooms",
            json={"max_players": 8},
            headers={"Authorization": f"Bearer {tok}"},
        )
        if res.status_code == 201:
            code = res.json()["code"]
            print(f"  Created room: {code}")
            return code
        print(f"  Room creation failed: {res.text}")
        return None


async def join_room(code, tok):
    async with httpx.AsyncClient() as cl:
        res = await cl.post(
            f"{BASE}/rooms/join",
            json={"code": code},
            headers={"Authorization": f"Bearer {tok}"},
        )
        if res.status_code == 200:
            return True
        print(f"  Join failed: {res.text}")
        return False


async def start_game(code, tok):
    async with httpx.AsyncClient() as cl:
        res = await cl.post(
            f"{BASE}/games/{code}/start",
            headers={"Authorization": f"Bearer {tok}"},
        )
        if res.status_code == 201:
            game_id = res.json()["id"]
            print(f"  Started game {game_id}")
            return game_id
        print(f"  Start game failed: {res.text}")
        return None


async def advance_phase(game_id, next_phase, tok):
    async with httpx.AsyncClient() as cl:
        res = await cl.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": next_phase},
            headers={"Authorization": f"Bearer {tok}"},
        )
        if res.status_code == 200:
            print(f"  -> {next_phase}")
            return True
        print(f"  Advance to {next_phase} failed: {res.text}")
        return False


async def ws_send_messages(room_code, email):
    import websockets
    token = tokens[email]
    ws_url = f"{WS_BASE}/{room_code}?token={token}"
    phrases = [
        "I think we need to be careful.",
        "Anyone got info?",
        "It seems someone is lying.",
        "I have a feeling about that.",
        "Let's work together.",
        "Interesting observation.",
        "What does everyone think?",
        "My gut says something is off.",
        "Let's share what we know.",
        "I noticed something suspicious.",
        "That was an interesting comment.",
        "I'm not sure who to trust.",
    ]
    async with websockets.connect(ws_url) as ws:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
        except:
            pass
        num = random.randint(2, 4)
        for _ in range(num):
            p = random.choice(phrases)
            await ws.send(json.dumps({"type": "SEND_MESSAGE", "content": p}))
            try:
                await asyncio.wait_for(ws.recv(), timeout=2)
            except:
                pass
            await asyncio.sleep(0.3 + 0.5 * random.random())
        await asyncio.sleep(0.5)
        try:
            while True:
                m = await asyncio.wait_for(ws.recv(), timeout=0.3)
        except:
            pass


async def ws_cast_vote(room_code, email, target_id):
    import websockets
    token = tokens[email]
    ws_url = f"{WS_BASE}/{room_code}?token={token}"
    async with websockets.connect(ws_url) as ws:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
        except:
            pass
        await ws.send(json.dumps({"type": "CAST_VOTE", "target_user_id": target_id}))
        await asyncio.sleep(0.5)
        try:
            while True:
                m = await asyncio.wait_for(ws.recv(), timeout=0.3)
        except:
            pass


async def get_room_players(code, tok):
    async with httpx.AsyncClient() as cl:
        res = await cl.get(
            f"{BASE}/rooms/{code}",
            headers={"Authorization": f"Bearer {tok}"},
        )
        if res.status_code == 200:
            return res.json()
        return None


async def main():
    print("1. Signing up / logging in players...")
    tok0 = None
    for i, email in enumerate(SIGNUP_EMAILS, start=1):
        tok, uid = await signup(email, i)
        if i == 1:
            tok0 = tok
    assert tok0 is not None

    print("\n2. Creating room, joning all players...")
    code = await create_room(tok0)
    assert code is not None
    for i, email in enumerate(SIGNUP_EMAILS[1:], start=2):
        ok = await join_room(code, tokens[email])
        print(f"  Player{i} joined: {ok}")

    print("\n3. Starting the game...")
    game_id = await start_game(code, tok0)
    assert game_id is not None
    print(f"\n  GAME ID: {game_id}  (room code: {code})")

    print("\n4. Simulating game play...")
    await asyncio.sleep(1)

    print("  role_assignment -> round_start")
    await advance_phase(game_id, "round_start", tok0)
    await asyncio.sleep(0.5)

    print("  round_start -> interaction")
    await advance_phase(game_id, "interaction", tok0)
    await asyncio.sleep(0.5)

    print("  Sending messages during interaction...")
    tasks = [ws_send_messages(code, e) for e in SIGNUP_EMAILS]
    await asyncio.gather(*tasks)

    print("  interaction -> discussion")
    await advance_phase(game_id, "discussion", tok0)
    await asyncio.sleep(0.5)

    print("  Sending messages during discussion...")
    tasks = [ws_send_messages(code, e) for e in SIGNUP_EMAILS]
    await asyncio.gather(*tasks)

    print("  discussion -> voting")
    await advance_phase(game_id, "voting", tok0)
    await asyncio.sleep(0.5)

    # Get players
    room_data = await get_room_players(code, tok0)
    plist = room_data.get("players", []) if room_data else []
    pids = [p["id"] for p in plist]
    print(f"  Players: {pids}")

    print("  Casting votes...")
    for i, email in enumerate(SIGNUP_EMAILS):
        uid = user_ids[email]
        others = [x for x in pids if x != uid]
        target = random.choice(others) if others else pids[0]
        await ws_cast_vote(code, email, target)
        await asyncio.sleep(0.5)
    await asyncio.sleep(1)

    print("  voting -> result")
    await advance_phase(game_id, "result", tok0)
    await asyncio.sleep(2)

    print("  result -> game_over")
    await advance_phase(game_id, "game_over", tok0)
    await asyncio.sleep(2)

    print(f"\n  COMPLETE! Game ID: {game_id}")
    print(f"  Analysis: http://localhost:8000/api/v1/analytics/{game_id}")


if __name__ == "__main__":
    asyncio.run(main())
