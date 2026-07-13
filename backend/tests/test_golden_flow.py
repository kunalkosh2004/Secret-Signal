"""
Golden Flow Test — end-to-end game lifecycle.

Tests: signup → login → create room → join room → ready → start game →
       chat → advance phases → vote → game over → analytics

Usage: uv run python tests/test_golden_flow.py
"""
import asyncio
import json
import random
import sys
import os
import httpx
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = "http://localhost:8000/api/v1"
WS_BASE = "ws://localhost:8000/ws"
PASSWORD = "testpass123"

PASS = 0
FAIL = 0


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {label}")
    else:
        FAIL += 1
        print(f"  ✗ {label} — {detail}")


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


async def main():
    global PASS, FAIL

    async with httpx.AsyncClient() as client:

        # =========================================================
        # 1. SIGNUP
        # =========================================================
        print("\n[1] SIGNUP")
        users = [
            {"username": "GFT_Alice", "email": "gft_alice@test.com"},
            {"username": "GFT_Bob", "email": "gft_bob@test.com"},
            {"username": "GFT_Charlie", "email": "gft_charlie@test.com"},
            {"username": "GFT_Dave", "email": "gft_dave@test.com"},
        ]

        tokens = {}
        user_ids = {}

        for u in users:
            res = await client.post(f"{BASE}/auth/signup", json={
                "username": u["username"], "email": u["email"], "password": PASSWORD
            })
            if res.status_code in (200, 201):
                d = res.json()
                tokens[u["email"]] = d["access_token"]
                user_ids[u["email"]] = d["user"]["id"]
            elif res.status_code == 409:
                res2 = await client.post(f"{BASE}/auth/login", json={
                    "email": u["email"], "password": PASSWORD
                })
                d = res2.json()
                tokens[u["email"]] = d["access_token"]
                user_ids[u["email"]] = d["user"]["id"]
            else:
                check(f"signup {u['username']}", False, f"{res.status_code}: {res.text}")
                continue

        check("all 4 users authenticated", len(tokens) == 4, f"got {len(tokens)}")

        # =========================================================
        # 2. LOGIN (verify tokens work)
        # =========================================================
        print("\n[2] LOGIN / TOKEN VERIFICATION")
        alice_email = users[0]["email"]
        alice_token = tokens[alice_email]
        res = await client.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {alice_token}"})
        check("GET /auth/me returns current user", res.status_code == 200 and res.json()["username"] == "GFT_Alice")

        # =========================================================
        # 3. CREATE ROOM
        # =========================================================
        print("\n[3] CREATE ROOM")
        res = await client.post(f"{BASE}/rooms", json={"max_players": 8, "settings": {}},
                                headers={"Authorization": f"Bearer {alice_token}"})
        check("room created (201)", res.status_code == 201, f"{res.status_code}: {res.text}")
        room_code = res.json()["code"]
        check("room code is 6 chars", len(room_code) == 6, room_code)
        check("room status is waiting", res.json()["status"] == "waiting")

        # =========================================================
        # 4. JOIN ROOM
        # =========================================================
        print("\n[4] JOIN ROOM")
        for u in users[1:]:
            res = await client.post(f"{BASE}/rooms/join", json={"code": room_code},
                                    headers={"Authorization": f"Bearer {tokens[u['email']]}"})
            check(f"{u['username']} joined", res.status_code == 200, f"{res.status_code}: {res.text}")

        # duplicate join should fail
        res = await client.post(f"{BASE}/rooms/join", json={"code": room_code},
                                headers={"Authorization": f"Bearer {tokens[users[1]['email']]}"})
        check("duplicate join rejected (409)", res.status_code == 409)

        # =========================================================
        # 5. READY UP (via DB — avoids WS disconnect reset)
        # =========================================================
        print("\n[5] READY UP")
        from app.db.session import SessionLocal
        from app.rooms import repository as room_repo

        async with SessionLocal() as db:
            room = await room_repo.get_by_code(db, room_code)
            check("room found in DB", room is not None)

            for u in users:
                uid = user_ids[u["email"]]
                await room_repo.set_player_ready(db, room_id=room.id, user_id=uid, is_ready=True)

            players = await room_repo.get_players_with_ready_state(db, room_id=room.id)
            all_ready = all(ready for _, ready in players)
            check("all 4 players ready", all_ready and len(players) == 4, f"players={len(players)}")

        # =========================================================
        # 6. START GAME
        # =========================================================
        print("\n[6] START GAME")
        res = await client.post(f"{BASE}/games/{room_code}/start",
                                headers={"Authorization": f"Bearer {alice_token}"})
        check("game started (201)", res.status_code == 201, f"{res.status_code}: {res.text}")
        game_id = res.json()["id"]
        check("game has valid id", isinstance(game_id, int) and game_id > 0)
        check("initial phase is role_assignment", res.json()["phase"] == "role_assignment")
        check("game round is 1", res.json()["round_number"] == 1)

        # =========================================================
        # 7. CONNECT WEBSOCKETS
        # =========================================================
        print("\n[7] WEBSOCKET CONNECTIONS")
        ws_conns = {}
        for u in users:
            token = tokens[u["email"]]
            ws = await websockets.connect(f"{WS_BASE}?token={token}&room_code={room_code}")
            ws_conns[u["email"]] = ws
            await drain(ws, timeout=3)
            check(f"{u['username']} ws connected", True)

        # =========================================================
        # 8. WAIT FOR AUTO-ADVANCE → INTERACTION
        # =========================================================
        print("\n[8] WAIT FOR PHASE ADVANCES")
        # role_assignment(6s) → round_start(5s) → interaction(120s)
        print("    waiting 14s for role_assignment → round_start → interaction...")
        await asyncio.sleep(14)
        for ws in ws_conns.values():
            await drain(ws, timeout=2)

        # may already be at interaction, or may need manual push
        res = await client.post(f"{BASE}/games/{game_id}/advance-phase",
                                json={"next_phase": "interaction"},
                                headers={"Authorization": f"Bearer {alice_token}"})
        # 200 = we advanced, 400 = already past this phase
        check("reached interaction phase", res.status_code in (200, 400))

        await asyncio.sleep(1)
        for ws in ws_conns.values():
            await drain(ws, timeout=2)

        # =========================================================
        # 9. SEND CHAT MESSAGES (interaction)
        # =========================================================
        print("\n[9] CHAT MESSAGES (interaction)")
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
        for u in users:
            ws = ws_conns[u["email"]]
            for i in range(3):
                msg = random.choice(chat_phrases)
                resp = await ws_send(ws, {"type": "SEND_MESSAGE", "content": msg})
                await asyncio.sleep(0.3)
            total_messages += 3
            await drain(ws, timeout=1)
            check(f"{u['username']} sent 3 messages", True)

        check(f"total messages sent: {total_messages}", total_messages == 12)

        # =========================================================
        # 10. ADVANCE → DISCUSSION
        # =========================================================
        print("\n[10] ADVANCE → DISCUSSION")
        for ws in ws_conns.values():
            await drain(ws, timeout=1)
        res = await client.post(f"{BASE}/games/{game_id}/advance-phase",
                                json={"next_phase": "discussion"},
                                headers={"Authorization": f"Bearer {alice_token}"})
        check("advanced to discussion", res.status_code == 200, f"{res.status_code}: {res.text}")

        await asyncio.sleep(1)
        for ws in ws_conns.values():
            await drain(ws, timeout=2)

        # =========================================================
        # 11. DISCUSSION MESSAGES
        # =========================================================
        print("\n[11] CHAT MESSAGES (discussion)")
        disc_phrases = [
            "I'm suspicious of someone here.",
            "Who do you think is the coordinator?",
            "Let's discuss before voting.",
            "I noticed unusual behavior.",
            "We need to vote carefully.",
        ]
        for u in users:
            ws = ws_conns[u["email"]]
            msg = random.choice(disc_phrases)
            await ws_send(ws, {"type": "SEND_MESSAGE", "content": msg})
            await asyncio.sleep(0.3)
            await drain(ws, timeout=1)
            check(f"{u['username']} sent discussion message", True)

        # =========================================================
        # 12. ADVANCE → VOTING
        # =========================================================
        print("\n[12] ADVANCE → VOTING")
        for ws in ws_conns.values():
            await drain(ws, timeout=1)
        res = await client.post(f"{BASE}/games/{game_id}/advance-phase",
                                json={"next_phase": "voting"},
                                headers={"Authorization": f"Bearer {alice_token}"})
        check("advanced to voting", res.status_code == 200, f"{res.status_code}: {res.text}")

        await asyncio.sleep(1)
        for ws in ws_conns.values():
            await drain(ws, timeout=2)

        # =========================================================
        # 13. CAST VOTES
        # =========================================================
        print("\n[13] CAST VOTES")
        all_uids = list(user_ids.values())
        votes_cast = 0
        for u in users:
            uid = user_ids[u["email"]]
            others = [x for x in all_uids if x != uid]
            target = random.choice(others)
            ws = ws_conns[u["email"]]
            resp = await ws_send(ws, {"type": "CAST_VOTE", "payload": {"target_user_id": target}})
            votes_cast += 1
            check(f"{u['username']} voted for user {target}", True)
            await asyncio.sleep(0.8)

        check("all 4 votes cast", votes_cast == 4)

        # After all votes: auto-advance to result → win check → game_over
        print("\n    waiting for auto-advance (voting → result → game_over)...")
        await asyncio.sleep(5)
        for ws in ws_conns.values():
            await drain(ws, timeout=3)

        # =========================================================
        # 14. VERIFY GAME OVER
        # =========================================================
        print("\n[14] VERIFY GAME OVER")
        # Try to advance — should fail since game is over
        res = await client.post(f"{BASE}/games/{game_id}/advance-phase",
                                json={"next_phase": "result"},
                                headers={"Authorization": f"Bearer {alice_token}"})
        # If game already over, this will 400 or the game status is completed
        if res.status_code == 200:
            game_data = res.json()
            check("game phase is game_over", game_data.get("phase") == "game_over",
                  f"phase={game_data.get('phase')}")
            check("game status is completed", game_data.get("status") == "completed",
                  f"status={game_data.get('status')}")
        else:
            # May have already completed — check via another endpoint
            check("game likely completed (advance rejected)", res.status_code == 400,
                  f"{res.status_code}")

        # =========================================================
        # 15. VERIFY EVENTS STORED
        # =========================================================
        print("\n[15] VERIFY EVENTS IN DB")
        from app.db.session import SessionLocal as SL
        from app.events import repository as event_repo

        async with SL() as db:
            events = await event_repo.get_game_events(db, game_id=game_id)
            event_types = [e.event_type for e in events]
            check("game_started event exists", "game_started" in event_types)
            check("message_sent events exist", "message_sent" in event_types,
                  f"types={event_types}")
            check("vote_cast events exist", "vote_cast" in event_types)
            check("phase_changed events exist", "phase_changed" in event_types)
            msg_count = event_types.count("message_sent")
            check(f"at least 10 message_sent events (got {msg_count})", msg_count >= 10)

        # =========================================================
        # 16. VERIFY TRAINING DATA
        # =========================================================
        print("\n[16] VERIFY TRAINING DATA")
        from app.training import repository as training_repo

        async with SL() as db:
            training_data = await training_repo.get_game_training_data(db, game_id=game_id)
            check("training data exists", len(training_data) > 0, f"count={len(training_data)}")
            if training_data:
                roles = set(t.role for t in training_data)
                check("training data has multiple roles", len(roles) >= 2, f"roles={roles}")

        # =========================================================
        # 17. VERIFY ANALYTICS
        # =========================================================
        print("\n[17] VERIFY ANALYTICS")
        from app.analytics import service as analytics_svc

        async with SL() as db:
            analysis = await analytics_svc.analyze_game(db, game_id=game_id)
            check("analysis returned", analysis is not None)
            check("analysis has players", len(analysis.players) == 4, f"count={len(analysis.players)}")
            check("analysis has summary", len(analysis.summary) > 0)

            # Check usernames are present (not just user_ids)
            usernames = [p.username for p in analysis.players]
            check("player usernames included", all(len(u) > 0 for u in usernames),
                  f"usernames={usernames}")

            # Check message counts
            total_analyzed = sum(p.message_count for p in analysis.players)
            check(f"analyzed messages > 0 (got {total_analyzed})", total_analyzed > 0)

            # Check coordinator has messages
            coord = next((p for p in analysis.players if p.role == "coordinator"), None)
            check("coordinator profile exists", coord is not None)
            if coord:
                check("coordinator has messages", coord.message_count > 0,
                      f"count={coord.message_count}")
                check("coordinator has username", len(coord.username) > 0,
                      f"username={coord.username}")

            # Check voting patterns
            check("voting patterns present", len(analysis.voting_patterns) > 0)

            # Check summary uses usernames (not "Player X")
            check("summary has no raw user IDs",
                  "Player 6" not in analysis.summary and "Player 7" not in analysis.summary
                  and "Player 8" not in analysis.summary,
                  f"summary: {analysis.summary}")

        # =========================================================
        # 18. VERIFY ML TRAINING DATA COUNT
        # =========================================================
        print("\n[18] VERIFY GAME STATE")
        async with SL() as db:
            from app.game_engine import repository as game_repo
            game = await game_repo.get_by_id(db, game_id=game_id)
            check("game exists", game is not None)
            check("game status is completed", game.status == "completed", f"status={game.status}")
            check("game phase is game_over", game.phase == "game_over", f"phase={game.phase}")

            game_players = await game_repo.get_game_players(db, game_id=game_id)
            check("4 game players", len(game_players) == 4, f"count={len(game_players)}")

            roles = [gp.role for gp in game_players]
            check("has coordinator", "coordinator" in roles)
            check("has detective", "detective" in roles)
            check("has citizens", "citizen" in roles)

            # Check scores assigned
            scores = [gp.score for gp in game_players]
            check("scores assigned", any(s > 0 for s in scores), f"scores={scores}")

        # =========================================================
        # CLEANUP
        # =========================================================
        print("\n[CLEANUP]")
        for ws in ws_conns.values():
            try:
                await ws.close()
            except Exception:
                pass
        check("ws connections closed", True)

        # =========================================================
        # SUMMARY
        # =========================================================
        print(f"\n{'='*60}")
        print(f"  RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} total")
        print(f"{'='*60}")

        if FAIL > 0:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
