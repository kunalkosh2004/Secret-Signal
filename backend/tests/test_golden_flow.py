"""
Golden Flow Test — end-to-end game lifecycle.

Tests: signup → login → create room → join room → ready → start game →
       chat → advance phases → vote → game over → analytics
"""

import asyncio
import json
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import httpx
import websockets

BASE = "http://localhost:8000/api/v1"
WS_BASE = "ws://localhost:8000/ws"
PASSWORD = "testpass123"

USERS = [
    {"username": "GFT_Alice", "email": "gft_alice@test.com"},
    {"username": "GFT_Bob", "email": "gft_bob@test.com"},
    {"username": "GFT_Charlie", "email": "gft_charlie@test.com"},
    {"username": "GFT_Dave", "email": "gft_dave@test.com"},
]


async def drain(ws, timeout=1.5):
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=timeout)
    except Exception:
        pass


async def ws_send(ws, msg, timeout=3):
    await ws.send(json.dumps(msg))
    try:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(raw) if raw else None
    except Exception:
        return None


@pytest.mark.asyncio
async def test_golden_flow():
    from app.db.session import SessionLocal
    from app.rooms import repository as room_repo
    from app.game_engine import repository as game_repo
    from app.events import repository as event_repo
    from app.training import repository as training_repo
    from app.analytics import service as analytics_svc

    tokens = {}
    user_ids = {}

    async with httpx.AsyncClient() as client:
        # =========================================================
        # 1. SIGNUP
        # =========================================================
        for u in USERS:
            res = await client.post(
                f"{BASE}/auth/signup",
                json={
                    "username": u["username"],
                    "email": u["email"],
                    "password": PASSWORD,
                },
            )
            if res.status_code in (200, 201):
                d = res.json()
                tokens[u["email"]] = d["access_token"]
                user_ids[u["email"]] = d["user"]["id"]
            elif res.status_code == 409:
                res2 = await client.post(
                    f"{BASE}/auth/login",
                    json={"email": u["email"], "password": PASSWORD},
                )
                d = res2.json()
                tokens[u["email"]] = d["access_token"]
                user_ids[u["email"]] = d["user"]["id"]
            else:
                pytest.fail(
                    f"signup {u['username']} failed: {res.status_code} {res.text}"
                )

        assert len(tokens) == 4, f"got {len(tokens)} users"
        print("[1] SIGNUP — 4 users authenticated")

        # =========================================================
        # 2. TOKEN VERIFICATION
        # =========================================================
        alice_token = tokens[USERS[0]["email"]]
        res = await client.get(
            f"{BASE}/auth/me",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert res.status_code == 200
        assert res.json()["username"] == "GFT_Alice"
        print("[2] TOKEN VERIFICATION — OK")

        # =========================================================
        # 3. CREATE ROOM
        # =========================================================
        res = await client.post(
            f"{BASE}/rooms",
            json={"max_players": 8, "settings": {}},
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert res.status_code == 201, res.text
        room_code = res.json()["code"]
        assert len(room_code) == 6
        assert res.json()["status"] == "waiting"
        print(f"[3] CREATE ROOM — code={room_code}")

        # =========================================================
        # 4. JOIN ROOM
        # =========================================================
        for u in USERS[1:]:
            res = await client.post(
                f"{BASE}/rooms/join",
                json={"code": room_code},
                headers={"Authorization": f"Bearer {tokens[u['email']]}"},
            )
            assert res.status_code == 200, f"{u['username']}: {res.text}"

        res = await client.post(
            f"{BASE}/rooms/join",
            json={"code": room_code},
            headers={"Authorization": f"Bearer {tokens[USERS[1]['email']]}"},
        )
        assert res.status_code == 409
        print("[4] JOIN ROOM — all players joined, duplicate rejected")

        # =========================================================
        # 5. READY UP
        # =========================================================
        async with SessionLocal() as db:
            room = await room_repo.get_by_code(db, room_code)
            assert room is not None

            for u in USERS:
                uid = user_ids[u["email"]]
                await room_repo.set_player_ready(
                    db, room_id=room.id, user_id=uid, is_ready=True
                )

            players = await room_repo.get_players_with_ready_state(db, room_id=room.id)
            all_ready = all(ready for _, ready in players)
            assert all_ready and len(players) == 4
        print("[5] READY UP — all 4 players ready")

        # =========================================================
        # 6. START GAME
        # =========================================================
        res = await client.post(
            f"{BASE}/games/{room_code}/start",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert res.status_code == 201, res.text
        game_id = res.json()["id"]
        assert isinstance(game_id, int) and game_id > 0
        assert res.json()["phase"] == "role_assignment"
        assert res.json()["round_number"] == 1
        print(f"[6] START GAME — id={game_id}")

        # =========================================================
        # 7. WAIT FOR AUTO-ADVANCE → INTERACTION
        # =========================================================
        await asyncio.sleep(14)

        res = await client.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": "interaction"},
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert res.status_code in (200, 400), res.text
        print("[7] ADVANCE TO INTERACTION — OK")

        # =========================================================
        # 8. CHAT MESSAGES (interaction)
        # =========================================================
        ws_conns = {}
        for u in USERS:
            ws = await websockets.connect(
                f"{WS_BASE}?token={tokens[u['email']]}&room_code={room_code}"
            )
            ws_conns[u["email"]] = ws
            await drain(ws, timeout=3)

        chat_phrases = [
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
        ]

        total_messages = 0
        for u in USERS:
            ws = ws_conns[u["email"]]
            for _ in range(3):
                msg = random.choice(chat_phrases)
                await ws_send(ws, {"type": "SEND_MESSAGE", "content": msg})
                await asyncio.sleep(0.3)
            total_messages += 3
            await drain(ws, timeout=1)

        assert total_messages == 12

        for ws in ws_conns.values():
            try:
                await ws.close()
            except Exception:
                pass
        print("[8] CHAT (interaction) — 12 messages sent")

        # =========================================================
        # 9. ADVANCE → DISCUSSION
        # =========================================================
        res = await client.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": "discussion"},
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert res.status_code == 200, res.text
        print("[9] ADVANCE TO DISCUSSION — OK")

        # =========================================================
        # 10. DISCUSSION MESSAGES
        # =========================================================
        ws_conns = {}
        for u in USERS:
            ws = await websockets.connect(
                f"{WS_BASE}?token={tokens[u['email']]}&room_code={room_code}"
            )
            ws_conns[u["email"]] = ws
            await drain(ws, timeout=3)

        disc_phrases = [
            "I'm suspicious of someone here.",
            "Who do you think is the coordinator?",
            "Let's discuss before voting.",
            "I noticed unusual behavior.",
            "We need to vote carefully.",
        ]
        for u in USERS:
            ws = ws_conns[u["email"]]
            msg = random.choice(disc_phrases)
            await ws_send(ws, {"type": "SEND_MESSAGE", "content": msg})
            await asyncio.sleep(0.3)
            await drain(ws, timeout=1)

        for ws in ws_conns.values():
            try:
                await ws.close()
            except Exception:
                pass
        print("[10] CHAT (discussion) — messages sent")

        # =========================================================
        # 11. ADVANCE → VOTING
        # =========================================================
        res = await client.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": "voting"},
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert res.status_code == 200, res.text
        print("[11] ADVANCE TO VOTING — OK")

        # =========================================================
        # 12. CAST VOTES
        # =========================================================
        ws_conns = {}
        for u in USERS:
            ws = await websockets.connect(
                f"{WS_BASE}?token={tokens[u['email']]}&room_code={room_code}"
            )
            ws_conns[u["email"]] = ws
            await drain(ws, timeout=3)

        all_uids = list(user_ids.values())
        votes_cast = 0
        for u in USERS:
            uid = user_ids[u["email"]]
            others = [x for x in all_uids if x != uid]
            target = random.choice(others)
            ws = ws_conns[u["email"]]
            await ws_send(
                ws, {"type": "CAST_VOTE", "payload": {"target_user_id": target}}
            )
            votes_cast += 1
            await asyncio.sleep(0.8)

        assert votes_cast == 4
        await asyncio.sleep(5)

        for ws in ws_conns.values():
            try:
                await ws.close()
            except Exception:
                pass
        print("[12] CAST VOTES — 4 votes cast")

        # =========================================================
        # 13. VERIFY GAME OVER
        # =========================================================
        res = await client.post(
            f"{BASE}/games/{game_id}/advance-phase",
            json={"next_phase": "result"},
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        if res.status_code == 200:
            data = res.json()
            assert data.get("phase") == "game_over"
            assert data.get("status") == "completed"
        else:
            assert res.status_code == 400
        print("[13] GAME OVER — verified")

    # =============================================================
    # 14. VERIFY EVENTS (needs fresh DB session outside client)
    # =============================================================
    async with SessionLocal() as db:
        events = await event_repo.get_game_events(db, game_id=game_id)
        event_types = [e.event_type for e in events]
        assert "game_started" in event_types
        assert "message_sent" in event_types
        assert "vote_cast" in event_types
        assert "phase_changed" in event_types
        msg_count = event_types.count("message_sent")
        assert msg_count >= 10
    print(f"[14] EVENTS — {len(event_types)} event types, {msg_count} messages")

    # =============================================================
    # 15. VERIFY TRAINING DATA
    # =============================================================
    async with SessionLocal() as db:
        training_data = await training_repo.get_game_training_data(db, game_id=game_id)
        assert len(training_data) > 0
        roles = set(t.role for t in training_data)
        assert len(roles) >= 2
    print(f"[15] TRAINING DATA — {len(training_data)} records, roles={roles}")

    # =============================================================
    # 16. VERIFY ANALYTICS
    # =============================================================
    async with SessionLocal() as db:
        analysis = await analytics_svc.analyze_game(db, game_id=game_id)
        assert analysis is not None
        assert len(analysis.players) == 4
        assert len(analysis.summary) > 0

        usernames = [p.username for p in analysis.players]
        assert all(len(u) > 0 for u in usernames)

        total_analyzed = sum(p.message_count for p in analysis.players)
        assert total_analyzed > 0

        coord = next((p for p in analysis.players if p.role == "coordinator"), None)
        assert coord is not None
        assert coord.message_count > 0
        assert len(coord.username) > 0

        assert len(analysis.voting_patterns) > 0

        assert "Player 6" not in analysis.summary
        assert "Player 7" not in analysis.summary
        assert "Player 8" not in analysis.summary
    print(
        f"[16] ANALYTICS — {total_analyzed} messages analyzed, {len(analysis.players)} players"
    )

    # =============================================================
    # 17. VERIFY GAME STATE
    # =============================================================
    async with SessionLocal() as db:
        game = await game_repo.get_by_id(db, game_id=game_id)
        assert game is not None
        assert game.status == "completed"
        assert game.phase == "game_over"

        game_players = await game_repo.get_game_players(db, game_id=game_id)
        assert len(game_players) == 4

        roles = [gp.role for gp in game_players]
        assert "coordinator" in roles
        assert "detective" in roles
        assert "citizen" in roles

        scores = [gp.score for gp in game_players]
        assert any(s > 0 for s in scores)
    print(f"[17] GAME STATE — completed, roles={roles}, scores={scores}")
