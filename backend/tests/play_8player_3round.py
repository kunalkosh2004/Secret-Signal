"""
Play a full 8-player, 3-round game of Secret Signal.
Users: Alice(9), Bob(10), Charlie(11), Dave(12), Eve(13), Frank(14), Grace(15), Henry(16)
All use password: testpass123

Usage: cd backend && uv run python play_8player_3round.py
"""
import asyncio
import json
import random
import sys
import os
import httpx
import websockets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = "http://localhost:8000/api/v1"
WS_BASE = "ws://localhost:8000/ws"
PASSWORD = "testpass123"

USERS = [
    {"id": 9,  "username": "Alice",   "email": "alice@test.com"},
    {"id": 10, "username": "Bob",     "email": "bob@test.com"},
    {"id": 11, "username": "Charlie", "email": "charlie@test.com"},
    {"id": 12, "username": "Dave",    "email": "dave@test.com"},
    {"id": 13, "username": "Eve",     "email": "eve@test.com"},
    {"id": 14, "username": "Frank",   "email": "frank@test.com"},
    {"id": 15, "username": "Grace",   "email": "grace@test.com"},
    {"id": 16, "username": "Henry",   "email": "henry@test.com"},
]

CHAT_MESSAGES = [
    "I think we should visit Italy for the food.",
    "What about France this summer?",
    "Japan has beautiful cherry blossoms.",
    "Have you been to Brazil?",
    "Germany has great culture.",
    "I love Mexican food.",
    "Australia is on my list.",
    "Egypt has amazing pyramids.",
    "Thailand is a great destination.",
    "Canada has stunning scenery.",
    "Italy pizza is the best in the world.",
    "France has the best wine.",
    "Japan's technology is incredible.",
    "Brazil has the best football.",
    "Germany's engineering is top notch.",
    "I want to try authentic Mexican tacos.",
    "Australia's beaches are amazing.",
    "Egypt's history is fascinating.",
    "Thailand's temples are beautiful.",
    "Canada's nature is breathtaking.",
]

DISCUSSION_MESSAGES = [
    "I'm suspicious of someone here.",
    "Who do you think is the coordinator?",
    "Let's discuss before voting.",
    "I noticed unusual behavior.",
    "We need to vote carefully.",
    "I think it's obvious who it is.",
    "Don't trust the quiet ones.",
    "The coordinator is hiding in plain sight.",
    "I have my suspicions about a few people.",
    "Let's think about who asked the most questions.",
]


async def drain(ws, timeout=1.5):
    msgs = []
    try:
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
            msgs.append(json.loads(msg))
    except Exception:
        pass
    return msgs


async def ws_send(ws, msg, timeout=3):
    await ws.send(json.dumps(msg))
    try:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def main():
    async with httpx.AsyncClient() as client:

        # =========================================================
        # 1. LOGIN ALL 8 USERS
        # =========================================================
        print("\n[1] LOGIN 8 USERS")
        tokens = {}
        user_ids = {}

        for u in USERS:
            res = await client.post(f"{BASE}/auth/login", json={
                "email": u["email"], "password": PASSWORD
            })
            if res.status_code == 200:
                d = res.json()
                tokens[u["email"]] = d["access_token"]
                user_ids[u["email"]] = d["user"]["id"]
                print(f"  ✓ {u['username']} logged in (id={d['user']['id']})")
            else:
                print(f"  ✗ {u['username']} login failed: {res.status_code} {res.text}")

        if len(tokens) < 8:
            print(f"ERROR: Only {len(tokens)} users logged in. Need 8.")
            return

        host_email = USERS[0]["email"]
        host_token = tokens[host_email]

        # =========================================================
        # 2. CREATE ROOM WITH 3-ROUND SETTINGS
        # =========================================================
        print("\n[2] CREATE ROOM (3 rounds, custom timers)")
        settings = {
            "max_rounds": 3,
            "phase_durations": {
                "role_assignment": 4,
                "round_start": 4,
                "interaction": 60,
                "discussion": 45,
                "result": 8,
            }
        }
        res = await client.post(f"{BASE}/rooms",
                                json={"max_players": 8, "settings": settings},
                                headers={"Authorization": f"Bearer {host_token}"})
        if res.status_code != 201:
            print(f"ERROR creating room: {res.status_code} {res.text}")
            return
        room_code = res.json()["code"]
        print(f"  ✓ Room created: {room_code}")
        print(f"  Settings: {json.dumps(res.json()['settings'], indent=2)}")

        # =========================================================
        # 3. ALL 8 USERS JOIN ROOM
        # =========================================================
        print("\n[3] JOIN ROOM")
        for u in USERS[1:]:
            res = await client.post(f"{BASE}/rooms/join",
                                    json={"code": room_code},
                                    headers={"Authorization": f"Bearer {tokens[u['email']]}"})
            status = "✓" if res.status_code == 200 else "✗"
            print(f"  {status} {u['username']} joined ({res.status_code})")

        # =========================================================
        # 4. READY UP ALL PLAYERS (via DB)
        # =========================================================
        print("\n[4] READY UP")
        from app.db.session import SessionLocal
        from app.rooms import repository as room_repo

        async with SessionLocal() as db:
            room = await room_repo.get_by_code(db, room_code)
            for u in USERS:
                uid = user_ids[u["email"]]
                await room_repo.set_player_ready(db, room_id=room.id, user_id=uid, is_ready=True)
            players = await room_repo.get_players_with_ready_state(db, room_id=room.id)
            print(f"  ✓ {len(players)} players ready")

        # =========================================================
        # 5. START GAME
        # =========================================================
        print("\n[5] START GAME")
        res = await client.post(f"{BASE}/games/{room_code}/start",
                                headers={"Authorization": f"Bearer {host_token}"})
        if res.status_code != 201:
            print(f"ERROR starting game: {res.status_code} {res.text}")
            return
        game_data = res.json()
        game_id = game_data["id"]
        print(f"  ✓ Game started: id={game_id}, phase={game_data['phase']}, round={game_data['round_number']}")
        print(f"  max_rounds={game_data.get('max_rounds', 'N/A')}")

        # =========================================================
        # 6. CONNECT WEBSOCKETS
        # =========================================================
        print("\n[6] CONNECT WEBSOCKETS")
        ws_conns = {}
        for u in USERS:
            token = tokens[u["email"]]
            try:
                ws = await websockets.connect(f"{WS_BASE}?token={token}&room_code={room_code}")
                ws_conns[u["email"]] = ws
                await drain(ws, timeout=3)
                print(f"  ✓ {u['username']} connected")
            except Exception as e:
                print(f"  ✗ {u['username']} WS failed: {e}")

        if len(ws_conns) < 8:
            print(f"WARNING: Only {len(ws_conns)} WS connections established")

        # =========================================================
        # PLAY 3 ROUNDS
        # =========================================================
        for round_num in range(1, 4):
            print(f"\n{'='*60}")
            print(f"  ROUND {round_num} of 3")
            print(f"{'='*60}")

            # --- Wait for auto-advance to interaction ---
            print(f"\n  [{round_num}.1] WAITING FOR PHASE ADVANCES...")
            await asyncio.sleep(10)
            for ws in ws_conns.values():
                await drain(ws, timeout=2)

            # Force advance to interaction if needed
            res = await client.post(f"{BASE}/games/{game_id}/advance-phase",
                                    json={"next_phase": "interaction"},
                                    headers={"Authorization": f"Bearer {host_token}"})
            if res.status_code == 200:
                print("  ✓ Advanced to interaction")
            await asyncio.sleep(1)
            for ws in ws_conns.values():
                await drain(ws, timeout=2)

            # --- Chat during interaction ---
            print(f"\n  [{round_num}.2] INTERACTION CHAT")
            for u in USERS:
                ws = ws_conns.get(u["email"])
                if not ws:
                    continue
                for i in range(3):
                    msg = random.choice(CHAT_MESSAGES)
                    await ws_send(ws, {"type": "SEND_MESSAGE", "content": msg})
                    await asyncio.sleep(0.2)
                await drain(ws, timeout=1)
                print(f"  ✓ {u['username']} sent 3 messages")

            # --- Advance to discussion ---
            print(f"\n  [{round_num}.3] ADVANCE → DISCUSSION")
            for ws in ws_conns.values():
                await drain(ws, timeout=1)
            res = await client.post(f"{BASE}/games/{game_id}/advance-phase",
                                    json={"next_phase": "discussion"},
                                    headers={"Authorization": f"Bearer {host_token}"})
            print(f"  {'✓' if res.status_code == 200 else '✗'} Advance to discussion ({res.status_code})")
            await asyncio.sleep(1)
            for ws in ws_conns.values():
                await drain(ws, timeout=2)

            # --- Discussion chat ---
            print(f"\n  [{round_num}.4] DISCUSSION CHAT")
            for u in USERS:
                ws = ws_conns.get(u["email"])
                if not ws:
                    continue
                msg = random.choice(DISCUSSION_MESSAGES)
                await ws_send(ws, {"type": "SEND_MESSAGE", "content": msg})
                await asyncio.sleep(0.2)
                await drain(ws, timeout=1)
                print(f"  ✓ {u['username']} sent discussion message")

            # --- Advance to voting ---
            print(f"\n  [{round_num}.5] ADVANCE → VOTING")
            for ws in ws_conns.values():
                await drain(ws, timeout=1)
            res = await client.post(f"{BASE}/games/{game_id}/advance-phase",
                                    json={"next_phase": "voting"},
                                    headers={"Authorization": f"Bearer {host_token}"})
            print(f"  {'✓' if res.status_code == 200 else '✗'} Advance to voting ({res.status_code})")
            await asyncio.sleep(1)
            for ws in ws_conns.values():
                await drain(ws, timeout=2)

            # --- Cast votes ---
            print(f"\n  [{round_num}.6] CAST VOTES")
            all_uids = list(user_ids.values())
            for u in USERS:
                uid = user_ids[u["email"]]
                others = [x for x in all_uids if x != uid]
                target = random.choice(others)
                ws = ws_conns.get(u["email"])
                if not ws:
                    continue
                await ws_send(ws, {"type": "CAST_VOTE", "payload": {"target_user_id": target}})
                await asyncio.sleep(0.5)
                print(f"  ✓ {u['username']} voted for user {target}")

            # --- Wait for auto-advance voting → result ---
            print(f"\n  [{round_num}.7] WAITING FOR VOTE TALLY + RESULT...")
            await asyncio.sleep(5)
            for ws in ws_conns.values():
                await drain(ws, timeout=3)

            # --- Advance to next round or game over ---
            if round_num < 3:
                print(f"\n  [{round_num}.8] ADVANCE → ROUND {round_num + 1}")
                for ws in ws_conns.values():
                    await drain(ws, timeout=1)
                res = await client.post(f"{BASE}/games/{game_id}/advance-phase",
                                        json={"next_phase": "round_start"},
                                        headers={"Authorization": f"Bearer {host_token}"})
                print(f"  {'✓' if res.status_code == 200 else '✗'} Advance to round_start ({res.status_code})")
                await asyncio.sleep(1)
                for ws in ws_conns.values():
                    await drain(ws, timeout=2)
            else:
                # Last round — advance to game_over
                print(f"\n  [{round_num}.8] ADVANCE → GAME OVER")
                for ws in ws_conns.values():
                    await drain(ws, timeout=1)
                res = await client.post(f"{BASE}/games/{game_id}/advance-phase",
                                        json={"next_phase": "game_over"},
                                        headers={"Authorization": f"Bearer {host_token}"})
                print(f"  {'✓' if res.status_code == 200 else '✗'} Advance to game_over ({res.status_code})")
                await asyncio.sleep(3)
                for ws in ws_conns.values():
                    await drain(ws, timeout=3)

        # =========================================================
        # VERIFY GAME STATE
        # =========================================================
        print(f"\n{'='*60}")
        print("  GAME COMPLETE — VERIFYING")
        print(f"{'='*60}")

        from app.db.session import SessionLocal as SL
        from app.game_engine import repository as game_repo
        from app.training import repository as training_repo
        from app.analytics import service as analytics_svc

        async with SL() as db:
            game = await game_repo.get_by_id(db, game_id=game_id)
            print(f"\n  Game ID:       {game.id}")
            print(f"  Status:        {game.status}")
            print(f"  Phase:         {game.phase}")
            print(f"  Round:         {game.round_number}")
            print(f"  Max Rounds:    {game.max_rounds}")

            game_players = await game_repo.get_game_players(db, game_id=game_id)
            print(f"\n  Players ({len(game_players)}):")
            for gp in game_players:
                await client.get(f"{BASE}/auth/me",
                                 headers={"Authorization": f"Bearer {host_token}"})
                # Just print role and score
                print(f"    User {gp.user_id}: role={gp.role}, score={gp.score}")

            # Training data
            training = await training_repo.get_game_training_data(db, game_id=game_id)
            print(f"\n  Training records: {len(training)}")

            # Analytics
            try:
                analysis = await analytics_svc.analyze_game(db, game_id=game_id)
                print("\n  Analytics Summary:")
                print(f"    {analysis.summary}")
                print(f"    Winner: {analysis.winner}")
                print(f"    Players analyzed: {len(analysis.players)}")
                for p in analysis.players:
                    print(f"      {p.username} ({p.role}): msgs={p.message_count}, "
                          f"replies={p.reply_count}, reactions={p.reaction_count}, "
                          f"suspicion={p.suspicion_score:.1f}")
            except Exception as e:
                print(f"  Analytics error: {e}")

        # =========================================================
        # CLOSE WEBSOCKETS
        # =========================================================
        for ws in ws_conns.values():
            try:
                await ws.close()
            except Exception:
                pass

        # =========================================================
        # FINAL OUTPUT
        # =========================================================
        print(f"\n{'='*60}")
        print("  GAME COMPLETE")
        print(f"{'='*60}")
        print(f"  Game ID:            {game_id}")
        print(f"  Room Code:          {room_code}")
        print("  Players:            8")
        print("  Rounds Played:      3")
        print("")
        print("  AI Analysis Endpoint:")
        print(f"    GET  /api/v1/analytics/game/{game_id}")
        print(f"    GET  /api/v1/ml/predict/{game_id}")
        print("")
        print("  Full URL:")
        print(f"    http://localhost:8000/api/v1/analytics/game/{game_id}")
        print(f"    http://localhost:8000/api/v1/ml/predict/{game_id}")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
