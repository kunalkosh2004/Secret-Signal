"""
Play a full game with kunal@test1.com + 3 others.
Uses DB to set ready state (avoids WS disconnect reset).
"""

import asyncio
import json
import random
import httpx
import websockets

BASE = "http://localhost:8000/api/v1"
WS_BASE = "ws://localhost:8000/ws"
PASSWORD = "testpass123"

HOST = {"username": "KunalHost", "email": "kunal_host@play.com"}
PLAYERS = [
    {"username": "PlayerAlpha", "email": "alpha@play.com"},
    {"username": "PlayerBeta", "email": "beta@play.com"},
    {"username": "PlayerGamma", "email": "gamma@play.com"},
]

HOST_TOKEN = None
HOST_ID = None
player_tokens = {}
player_ids = {}
room_code = None
game_id = None


async def drain(ws, timeout=1.5):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=timeout)
    except Exception:
        pass


async def ws_send_collect(ws, msg, timeout=3):
    await ws.send(json.dumps(msg))
    try:
        return await asyncio.wait_for(ws.recv(), timeout=timeout)
    except Exception:
        return None


async def main():
    global HOST_TOKEN, HOST_ID, room_code, game_id

    async with httpx.AsyncClient() as client:
        # === 1. Login kunal@test1.com ===
        print("=== 1. Login kunal@test1.com ===")
        res = await client.post(
            f"{BASE}/auth/login",
            json={"email": "kunal@test1.com", "password": "kunal1234"},
        )
        if res.status_code != 200:
            print(f"  FATAL: {res.status_code} {res.text}")
            return
        d = res.json()
        HOST_TOKEN = d["access_token"]
        HOST_ID = d["user"]["id"]
        print(f"  Logged in as {d['user']['username']} (id={HOST_ID})")

        # === 2. Signup 3 other players ===
        print("\n=== 2. Signup 3 players ===")
        for p in PLAYERS:
            res = await client.post(
                f"{BASE}/auth/signup",
                json={
                    "username": p["username"],
                    "email": p["email"],
                    "password": PASSWORD,
                },
            )
            if res.status_code in (200, 201):
                d = res.json()
                player_tokens[p["email"]] = d["access_token"]
                player_ids[p["email"]] = d["user"]["id"]
                print(f"  [+] {p['username']} id={d['user']['id']}")
            elif res.status_code == 409:
                res2 = await client.post(
                    f"{BASE}/auth/login",
                    json={"email": p["email"], "password": PASSWORD},
                )
                if res2.status_code == 200:
                    d = res2.json()
                    player_tokens[p["email"]] = d["access_token"]
                    player_ids[p["email"]] = d["user"]["id"]
                    print(f"  [=] {p['username']} id={d['user']['id']}")
                else:
                    print(f"  [!] {p['username']} login failed")
                    return
            else:
                print(f"  [!] {p['username']} failed: {res.status_code}")
                return

        all_user_ids = [HOST_ID] + list(player_ids.values())
        all_tokens = {HOST_TOKEN: HOST_ID}
        all_tokens.update({v: k for k, v in player_ids.items()})

        # === 3. Create room ===
        print("\n=== 3. Create room ===")
        res = await client.post(
            f"{BASE}/rooms",
            json={"max_players": 8, "settings": {}},
            headers={"Authorization": f"Bearer {HOST_TOKEN}"},
        )
        if res.status_code not in (200, 201):
            print(f"  FATAL: {res.status_code} {res.text}")
            return
        room_code = res.json()["code"]
        print(f"  Room: {room_code}")

        # === 4. Join room ===
        print("\n=== 4. Join room ===")
        for p in PLAYERS:
            res = await client.post(
                f"{BASE}/rooms/join",
                json={"code": room_code},
                headers={"Authorization": f"Bearer {player_tokens[p['email']]}"},
            )
            print(f"  {p['username']}: {'OK' if res.status_code == 200 else 'FAIL'}")

        # === 5. Set all players ready via DB ===
        print("\n=== 5. Set all players ready via DB ===")
        from app.db.session import SessionLocal
        from app.rooms import repository as room_repo

        async with SessionLocal() as db:
            room = await room_repo.get_by_code(db, room_code)
            if room:
                for uid in all_user_ids:
                    try:
                        await room_repo.set_player_ready(
                            db, room_id=room.id, user_id=uid, is_ready=True
                        )
                    except Exception as e:
                        print(f"  Ready failed for {uid}: {e}")
                print(f"  All {len(all_user_ids)} players set ready")
            else:
                print("  FATAL: Room not found in DB")
                return

        # === 6. Start game ===
        print("\n=== 6. Start game ===")
        res = await client.post(
            f"{BASE}/games/{room_code}/start",
            headers={"Authorization": f"Bearer {HOST_TOKEN}"},
        )
        if res.status_code not in (200, 201):
            print(f"  FATAL: {res.status_code} {res.text}")
            return
        game_id = res.json()["id"]
        print(f"  Game ID: {game_id}")

        # === 7. Connect all via WS and collect events ===
        print("\n=== 7. WS Connect + collect events ===")
        ws_conns = {}

        # Connect host
        ws = await websockets.connect(
            f"{WS_BASE}?token={HOST_TOKEN}&room_code={room_code}"
        )
        ws_conns["host"] = ws
        await drain(ws, timeout=3)
        print("  Host connected")

        # Connect players
        for p in PLAYERS:
            ws = await websockets.connect(
                f"{WS_BASE}?token={player_tokens[p['email']]}&room_code={room_code}"
            )
            ws_conns[p["email"]] = ws
            await drain(ws, timeout=3)
            print(f"  {p['username']} connected")

        # Wait for auto-advance through role_assignment (6s) and round_start (5s)
        print("\n  Waiting 14s for auto-advance to interaction...")
        await asyncio.sleep(14)

        # Drain events
        for ws in ws_conns.values():
            await drain(ws, timeout=2)

        # Try advancing to interaction (might already be there)
        res = await client.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": "interaction"},
            headers={"Authorization": f"Bearer {HOST_TOKEN}"},
        )
        print(f"  -> interaction: {res.status_code}")

        await asyncio.sleep(1)
        for ws in ws_conns.values():
            await drain(ws, timeout=2)

        # === 8. Send messages during interaction ===
        print("\n=== 8. Interaction - Chat ===")
        phrases = [
            "I think we should visit Italy for the food.",
            "What about going to France this summer?",
            "Japan has beautiful cherry blossoms in spring.",
            "Have you ever been to Brazil?",
            "Germany has great history and culture.",
            "I love Mexican food, it's flavorful.",
            "Australia is on my bucket list.",
            "Egypt has amazing ancient pyramids.",
            "Thailand is a great destination.",
            "Canada has stunning scenery.",
            "Let's work together on this.",
            "I noticed something interesting.",
            "That's a good point, I agree.",
            "I'm not sure about that approach.",
            "We should consider all options.",
            "Does anyone like Asian food?",
            "I had Italian pasta last night.",
            "The weather in Spain is nice.",
            "We need more info before deciding.",
            "What does everyone think?",
        ]

        for p in PLAYERS + [HOST]:
            ws = ws_conns["host"] if p == HOST else ws_conns[p["email"]]
            name = "Host" if p == HOST else p["username"]
            for i in range(5):
                msg = random.choice(phrases)
                await ws_send_collect(ws, {"type": "SEND_MESSAGE", "content": msg})
                await asyncio.sleep(0.3)
            await drain(ws, timeout=1)
            print(f"  {name}: sent 5 messages")

        await asyncio.sleep(2)

        # === 9. Advance to discussion ===
        print("\n=== 9. Advance to discussion ===")
        for ws in ws_conns.values():
            await drain(ws, timeout=1)
        res = await client.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": "discussion"},
            headers={"Authorization": f"Bearer {HOST_TOKEN}"},
        )
        print(f"  -> discussion: {res.status_code}")
        await asyncio.sleep(1)
        for ws in ws_conns.values():
            await drain(ws, timeout=2)

        # === 10. Discussion messages ===
        print("\n=== 10. Discussion ===")
        disc = [
            "I'm suspicious of the person mentioning countries.",
            "I noticed someone asking questions earlier.",
            "That's a good observation.",
            "Let's think about who is the coordinator.",
            "I think we should vote carefully.",
            "The coordinator is trying to blend in.",
            "I have suspicions about one player.",
            "Let's discuss before voting.",
        ]
        for p in PLAYERS + [HOST]:
            ws = ws_conns["host"] if p == HOST else ws_conns[p["email"]]
            name = "Host" if p == HOST else p["username"]
            for i in range(3):
                msg = random.choice(disc)
                await ws_send_collect(ws, {"type": "SEND_MESSAGE", "content": msg})
                await asyncio.sleep(0.3)
            await drain(ws, timeout=1)
            print(f"  {name}: discussed")

        await asyncio.sleep(1)

        # === 11. Advance to voting ===
        print("\n=== 11. Advance to voting ===")
        for ws in ws_conns.values():
            await drain(ws, timeout=1)
        res = await client.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": "voting"},
            headers={"Authorization": f"Bearer {HOST_TOKEN}"},
        )
        print(f"  -> voting: {res.status_code}")
        await asyncio.sleep(1)
        for ws in ws_conns.values():
            await drain(ws, timeout=2)

        # === 12. Cast votes ===
        print("\n=== 12. Cast votes ===")
        for p in PLAYERS + [HOST]:
            uid = HOST_ID if p == HOST else player_ids[p["email"]]
            others = [x for x in all_user_ids if x != uid]
            target = random.choice(others)
            ws = ws_conns["host"] if p == HOST else ws_conns[p["email"]]
            name = "Host" if p == HOST else p["username"]
            await ws_send_collect(
                ws, {"type": "CAST_VOTE", "payload": {"target_user_id": target}}
            )
            print(f"  {name} voted for {target}")
            await asyncio.sleep(0.8)

        # Wait for auto-advance (voting -> result -> game_over)
        print("\n=== 13. Waiting for auto-advance ===")
        await asyncio.sleep(5)
        for ws in ws_conns.values():
            await drain(ws, timeout=3)

        # Try advancing to result if needed
        res = await client.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": "result"},
            headers={"Authorization": f"Bearer {HOST_TOKEN}"},
        )
        print(f"  -> result: {res.status_code}")
        await asyncio.sleep(3)
        for ws in ws_conns.values():
            await drain(ws, timeout=3)

        # Try advancing to game_over if needed
        res = await client.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": "game_over"},
            headers={"Authorization": f"Bearer {HOST_TOKEN}"},
        )
        print(f"  -> game_over: {res.status_code}")
        await asyncio.sleep(2)

        # Close all WS
        for ws in ws_conns.values():
            await ws.close()

        print(f"\n{'=' * 50}")
        print("  GAME COMPLETE!")
        print(f"  GAME ID: {game_id}")
        print(f"  Room Code: {room_code}")
        print(f"  Host: kunal@test1.com (asd123kunal, id={HOST_ID})")
        print(f"  Players: {[p['username'] for p in PLAYERS]}")
        print(f"  Analysis: http://localhost:5173/game/{game_id}/analysis")
        print(f"{'=' * 50}")


if __name__ == "__main__":
    asyncio.run(main())
