"""
Golden Flow Test — end-to-end game lifecycle.

Tests: signup → login → create room → join room → ready → start game →
       chat → advance phases → vote → game over → analytics
"""

import asyncio
import json
import random
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


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


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


@pytest.fixture(scope="module")
async def client():
    async with httpx.AsyncClient() as c:
        yield c


@pytest.fixture(scope="module")
async def authenticated_users(client):
    tokens = {}
    user_ids = {}
    for u in USERS:
        res = await client.post(
            f"{BASE}/auth/signup",
            json={"username": u["username"], "email": u["email"], "password": PASSWORD},
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
            pytest.fail(f"signup {u['username']} failed: {res.status_code} {res.text}")
    return tokens, user_ids


class TestGoldenFlow:
    tokens: dict = None
    user_ids: dict = None
    room_code: str = None
    game_id: int = None

    @pytest.mark.asyncio
    async def test_01_signup(self, authenticated_users):
        tokens, user_ids = authenticated_users
        type(self).tokens = tokens
        type(self).user_ids = user_ids
        assert len(tokens) == 4, f"got {len(tokens)} users"

    @pytest.mark.asyncio
    async def test_02_token_verification(self, client):
        res = await client.get(
            f"{BASE}/auth/me",
            headers={"Authorization": f"Bearer {self.tokens[USERS[0]['email']]}"},
        )
        assert res.status_code == 200
        assert res.json()["username"] == "GFT_Alice"

    @pytest.mark.asyncio
    async def test_03_create_room(self, client):
        res = await client.post(
            f"{BASE}/rooms",
            json={"max_players": 8, "settings": {}},
            headers={"Authorization": f"Bearer {self.tokens[USERS[0]['email']]}"},
        )
        assert res.status_code == 201, f"{res.status_code}: {res.text}"
        data = res.json()
        assert len(data["code"]) == 6, f"room code={data['code']}"
        assert data["status"] == "waiting"
        type(self).room_code = data["code"]

    @pytest.mark.asyncio
    async def test_04_join_room(self, client):
        for u in USERS[1:]:
            res = await client.post(
                f"{BASE}/rooms/join",
                json={"code": self.room_code},
                headers={"Authorization": f"Bearer {self.tokens[u['email']]}"},
            )
            assert res.status_code == 200, (
                f"{u['username']}: {res.status_code} {res.text}"
            )

        # duplicate join should fail
        res = await client.post(
            f"{BASE}/rooms/join",
            json={"code": self.room_code},
            headers={"Authorization": f"Bearer {self.tokens[USERS[1]['email']]}"},
        )
        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_05_ready_up(self):
        from app.db.session import SessionLocal
        from app.rooms import repository as room_repo

        async with SessionLocal() as db:
            room = await room_repo.get_by_code(db, self.room_code)
            assert room is not None

            for u in USERS:
                uid = self.user_ids[u["email"]]
                await room_repo.set_player_ready(
                    db, room_id=room.id, user_id=uid, is_ready=True
                )

            players = await room_repo.get_players_with_ready_state(db, room_id=room.id)
            all_ready = all(ready for _, ready in players)
            assert all_ready and len(players) == 4, (
                f"players={len(players)} ready={all_ready}"
            )

    @pytest.mark.asyncio
    async def test_06_start_game(self, client):
        res = await client.post(
            f"{BASE}/games/{self.room_code}/start",
            headers={"Authorization": f"Bearer {self.tokens[USERS[0]['email']]}"},
        )
        assert res.status_code == 201, f"{res.status_code}: {res.text}"
        data = res.json()
        assert isinstance(data["id"], int) and data["id"] > 0
        assert data["phase"] == "role_assignment"
        assert data["round_number"] == 1
        type(self).game_id = data["id"]

    @pytest.mark.asyncio
    async def test_07_websocket_connections(self):
        ws_conns = {}
        for u in USERS:
            ws = await websockets.connect(
                f"{WS_BASE}?token={self.tokens[u['email']]}&room_code={self.room_code}"
            )
            ws_conns[u["email"]] = ws
            await drain(ws, timeout=3)

        yield ws_conns

        for ws in ws_conns.values():
            try:
                await ws.close()
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_08_advance_to_interaction(self, client):
        # Wait for auto-advance: role_assignment(6s) → round_start(5s) → interaction(120s)
        await asyncio.sleep(14)

        res = await client.post(
            f"{BASE}/games/{self.game_id}/advance-phase",
            json={"next_phase": "interaction"},
            headers={"Authorization": f"Bearer {self.tokens[USERS[0]['email']]}"},
        )
        assert res.status_code in (200, 400), f"{res.status_code}: {res.text}"

    @pytest.mark.asyncio
    async def test_09_chat_messages_interaction(self, client):
        ws_conns = {}
        for u in USERS:
            ws = await websockets.connect(
                f"{WS_BASE}?token={self.tokens[u['email']]}&room_code={self.room_code}"
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

    @pytest.mark.asyncio
    async def test_10_advance_to_discussion(self, client):
        res = await client.post(
            f"{BASE}/games/{self.game_id}/advance-phase",
            json={"next_phase": "discussion"},
            headers={"Authorization": f"Bearer {self.tokens[USERS[0]['email']]}"},
        )
        assert res.status_code == 200, f"{res.status_code}: {res.text}"

    @pytest.mark.asyncio
    async def test_11_chat_messages_discussion(self, client):
        ws_conns = {}
        for u in USERS:
            ws = await websockets.connect(
                f"{WS_BASE}?token={self.tokens[u['email']]}&room_code={self.room_code}"
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

    @pytest.mark.asyncio
    async def test_12_advance_to_voting(self, client):
        res = await client.post(
            f"{BASE}/games/{self.game_id}/advance-phase",
            json={"next_phase": "voting"},
            headers={"Authorization": f"Bearer {self.tokens[USERS[0]['email']]}"},
        )
        assert res.status_code == 200, f"{res.status_code}: {res.text}"

    @pytest.mark.asyncio
    async def test_13_cast_votes(self, client):
        ws_conns = {}
        for u in USERS:
            ws = await websockets.connect(
                f"{WS_BASE}?token={self.tokens[u['email']]}&room_code={self.room_code}"
            )
            ws_conns[u["email"]] = ws
            await drain(ws, timeout=3)

        all_uids = list(self.user_ids.values())
        votes_cast = 0
        for u in USERS:
            uid = self.user_ids[u["email"]]
            others = [x for x in all_uids if x != uid]
            target = random.choice(others)
            ws = ws_conns[u["email"]]
            await ws_send(
                ws, {"type": "CAST_VOTE", "payload": {"target_user_id": target}}
            )
            votes_cast += 1
            await asyncio.sleep(0.8)

        assert votes_cast == 4

        # Wait for auto-advance to result → game_over
        await asyncio.sleep(5)

        for ws in ws_conns.values():
            try:
                await ws.close()
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_14_verify_game_over(self, client):
        res = await client.post(
            f"{BASE}/games/{self.game_id}/advance-phase",
            json={"next_phase": "result"},
            headers={"Authorization": f"Bearer {self.tokens[USERS[0]['email']]}"},
        )
        if res.status_code == 200:
            data = res.json()
            assert data.get("phase") == "game_over", f"phase={data.get('phase')}"
            assert data.get("status") == "completed", f"status={data.get('status')}"
        else:
            assert res.status_code == 400, f"{res.status_code}"

    @pytest.mark.asyncio
    async def test_15_verify_events(self):
        from app.db.session import SessionLocal as SL
        from app.events import repository as event_repo

        async with SL() as db:
            events = await event_repo.get_game_events(db, game_id=self.game_id)
            event_types = [e.event_type for e in events]
            assert "game_started" in event_types
            assert "message_sent" in event_types, f"types={event_types}"
            assert "vote_cast" in event_types
            assert "phase_changed" in event_types
            msg_count = event_types.count("message_sent")
            assert msg_count >= 10, f"got {msg_count}"

    @pytest.mark.asyncio
    async def test_16_verify_training_data(self):
        from app.db.session import SessionLocal as SL
        from app.training import repository as training_repo

        async with SL() as db:
            training_data = await training_repo.get_game_training_data(
                db, game_id=self.game_id
            )
            assert len(training_data) > 0, f"count={len(training_data)}"
            roles = set(t.role for t in training_data)
            assert len(roles) >= 2, f"roles={roles}"

    @pytest.mark.asyncio
    async def test_17_verify_analytics(self):
        from app.db.session import SessionLocal as SL
        from app.analytics import service as analytics_svc

        async with SL() as db:
            analysis = await analytics_svc.analyze_game(db, game_id=self.game_id)
            assert analysis is not None
            assert len(analysis.players) == 4, f"count={len(analysis.players)}"
            assert len(analysis.summary) > 0

            usernames = [p.username for p in analysis.players]
            assert all(len(u) > 0 for u in usernames), f"usernames={usernames}"

            total_analyzed = sum(p.message_count for p in analysis.players)
            assert total_analyzed > 0, f"total={total_analyzed}"

            coord = next((p for p in analysis.players if p.role == "coordinator"), None)
            assert coord is not None
            assert coord.message_count > 0, f"count={coord.message_count}"
            assert len(coord.username) > 0, f"username={coord.username}"

            assert len(analysis.voting_patterns) > 0

            assert "Player 6" not in analysis.summary
            assert "Player 7" not in analysis.summary
            assert "Player 8" not in analysis.summary

    @pytest.mark.asyncio
    async def test_18_verify_game_state(self):
        from app.db.session import SessionLocal as SL
        from app.game_engine import repository as game_repo

        async with SL() as db:
            game = await game_repo.get_by_id(db, game_id=self.game_id)
            assert game is not None
            assert game.status == "completed", f"status={game.status}"
            assert game.phase == "game_over", f"phase={game.phase}"

            game_players = await game_repo.get_game_players(db, game_id=self.game_id)
            assert len(game_players) == 4, f"count={len(game_players)}"

            roles = [gp.role for gp in game_players]
            assert "coordinator" in roles
            assert "detective" in roles
            assert "citizen" in roles

            scores = [gp.score for gp in game_players]
            assert any(s > 0 for s in scores), f"scores={scores}"
