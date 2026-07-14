"""5-user 3-round game — HTTP + DB only, zero websocket connections."""

import asyncio
import random
import httpx
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = "http://localhost:8000/api/v1"
PW = "testpass123"
USERS = [
    (9, "alice@test.com"),
    (10, "bob@test.com"),
    (11, "charlie@test.com"),
    (12, "dave@test.com"),
    (13, "eve@test.com"),
]
CHATS = [
    "Italy is beautiful this time of year.",
    "Japan has amazing food.",
    "France has great culture.",
    "Brazil is on my bucket list.",
    "Germany has lovely architecture.",
    "Canada is so vast and wild.",
    "Thailand is incredibly affordable.",
    "Australia has unique wildlife.",
    "Egypt is full of history.",
    "Mexico has the best tacos.",
    "I think Italy is the best choice.",
    "What about somewhere in Asia?",
    "We should decide soon.",
    "I trust most of you here.",
    "Be careful who you pick.",
    "I have a strong feeling about someone.",
    "Let's discuss carefully.",
    "Who do you think is suspicious?",
    "I am not the coordinator.",
    "Vote wisely everyone.",
]
DISC = [
    "I'm suspicious of one person here.",
    "Who is the coordinator among us?",
    "Let's discuss before we vote.",
    "I noticed something odd earlier.",
    "We need to vote carefully.",
    "I think I know who it is.",
    "Trust me on this one.",
    "Let's not make a mistake.",
    "The coordinator is clever.",
    "We should focus on the evidence.",
]


async def main():
    async with httpx.AsyncClient(timeout=30) as c:
        # Login
        tokens = {}
        for uid, email in USERS:
            r = await c.post(
                f"{BASE}/auth/login", json={"email": email, "password": PW}
            )
            assert r.status_code == 200, f"Login {email}: {r.status_code}"
            tokens[uid] = r.json()["access_token"]
        h = {"Authorization": f"Bearer {tokens[9]}"}

        # Create room
        r = await c.post(
            f"{BASE}/rooms",
            json={
                "max_players": 5,
                "settings": {
                    "max_rounds": 3,
                    "phase_durations": {
                        "role_assignment": 3,
                        "round_start": 3,
                        "interaction": 8,
                        "discussion": 8,
                        "result": 5,
                    },
                },
            },
            headers=h,
        )
        assert r.status_code == 201, f"Create room: {r.status_code} {r.text}"
        room_code = r.json()["code"]
        print(f"Room: {room_code}")

        # Join
        for uid, email in USERS[1:]:
            r = await c.post(
                f"{BASE}/rooms/join",
                json={"code": room_code},
                headers={"Authorization": f"Bearer {tokens[uid]}"},
            )
            assert r.status_code == 200

        # Ready via DB
        from app.db.session import SessionLocal
        from app.rooms import repository as room_repo

        async with SessionLocal() as db:
            room = await room_repo.get_by_code(db, room_code)
            for uid, _ in USERS:
                await room_repo.set_player_ready(
                    db, room_id=room.id, user_id=uid, is_ready=True
                )
            await db.commit()

        # Start game
        r = await c.post(f"{BASE}/games/{room_code}/start", headers=h)
        assert r.status_code == 201, f"Start game: {r.status_code} {r.text}"
        game_id = r.json()["id"]
        print(f"Game ID: {game_id}")

        # Wait for auto-advance: role_assignment(3) + round_start(3) = 6s
        # Then interaction auto-starts. We need to wait for it.
        print("Waiting for auto-advance to interaction...")
        await asyncio.sleep(8)

        from app.chat import repository as chat_repo
        from app.events import repository as event_repo
        from app.game_engine import repository as game_repo
        from app.training import repository as training_repo
        from app.voting import repository as vote_repo

        for rnd in range(1, 4):
            print(f"\n--- Round {rnd} ---")

            # Check current phase
            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                print(f"  Current phase: {game.phase}, round: {game.round_number}")

            # If phase is not interaction yet, advance to it
            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                current = game.phase

            if current != "interaction":
                r = await c.post(
                    f"{BASE}/games/{game_id}/advance-phase",
                    json={"next_phase": "interaction"},
                    headers=h,
                )
                print(f"  → interaction: {r.status_code}")

            # Store chat messages
            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                for uid, _ in USERS:
                    gp = await game_repo.get_game_player(
                        db, game_id=game_id, user_id=uid
                    )
                    for _ in range(3):
                        content = random.choice(CHATS)
                        msg = await chat_repo.create_message(
                            db, room_id=room.id, user_id=uid, content=content
                        )
                        await event_repo.create_event(
                            db,
                            game_id=game_id,
                            round_number=game.round_number,
                            event_type="message_sent",
                            user_id=uid,
                            payload={"message_id": msg.id, "content": content},
                        )
                        if gp:
                            has_reply = random.random() < 0.25
                            reply_role = None
                            if has_reply:
                                others_gp = [u for u, _ in USERS if u != uid]
                                rp = await game_repo.get_game_player(
                                    db,
                                    game_id=game_id,
                                    user_id=random.choice(others_gp),
                                )
                                if rp:
                                    reply_role = rp.role
                            await training_repo.create_training_message(
                                db,
                                game_id=game_id,
                                user_id=uid,
                                role=gp.role,
                                phase=game.phase,
                                content=content,
                                round_number=game.round_number,
                                has_reply=has_reply,
                                reply_to_role=reply_role,
                            )
                await db.commit()
            print("  15 chat messages stored")

            # Advance to discussion
            r = await c.post(
                f"{BASE}/games/{game_id}/advance-phase",
                json={"next_phase": "discussion"},
                headers=h,
            )
            print(f"  → discussion: {r.status_code}")

            # Store discussion messages
            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                for uid, _ in USERS:
                    gp = await game_repo.get_game_player(
                        db, game_id=game_id, user_id=uid
                    )
                    content = random.choice(DISC)
                    msg = await chat_repo.create_message(
                        db, room_id=room.id, user_id=uid, content=content
                    )
                    await event_repo.create_event(
                        db,
                        game_id=game_id,
                        round_number=game.round_number,
                        event_type="message_sent",
                        user_id=uid,
                        payload={"message_id": msg.id, "content": content},
                    )
                    if gp:
                        await training_repo.create_training_message(
                            db,
                            game_id=game_id,
                            user_id=uid,
                            role=gp.role,
                            phase=game.phase,
                            content=content,
                            round_number=game.round_number,
                        )
                await db.commit()
            print("  5 discussion messages stored")

            # Advance to voting
            r = await c.post(
                f"{BASE}/games/{game_id}/advance-phase",
                json={"next_phase": "voting"},
                headers=h,
            )
            print(f"  → voting: {r.status_code}")

            # Cast votes — avoid the coordinator so game continues all 3 rounds
            async with SessionLocal() as db:
                coordinator = await game_repo.get_player_by_role(
                    db, game_id=game_id, role="coordinator"
                )
                coord_uid = coordinator.user_id if coordinator else None
                all_uids = [uid for uid, _ in USERS]

                for uid, _ in USERS:
                    others = [x for x in all_uids if x != uid and x != coord_uid]
                    if not others:
                        others = [x for x in all_uids if x != uid]
                    target = random.choice(others)
                    await vote_repo.create_vote(
                        db,
                        game_id=game_id,
                        round_number=rnd,
                        voter_user_id=uid,
                        target_user_id=target,
                    )
                await db.commit()
            print(f"  5 votes cast (coordinator id={coord_uid} avoided)")

            # Advance to result
            r = await c.post(
                f"{BASE}/games/{game_id}/advance-phase",
                json={"next_phase": "result"},
                headers=h,
            )
            print(f"  → result: {r.status_code}")

            # Check if game ended
            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                if game.status == "completed":
                    print(f"  Game ended early at round {rnd}!")
                    break

            # Advance to next round or game over
            if rnd < 3:
                r = await c.post(
                    f"{BASE}/games/{game_id}/advance-phase",
                    json={"next_phase": "round_start"},
                    headers=h,
                )
                print(f"  → round_start: {r.status_code}")
                # Wait for auto-advance from round_start → interaction
                await asyncio.sleep(8)
            else:
                r = await c.post(
                    f"{BASE}/games/{game_id}/advance-phase",
                    json={"next_phase": "game_over"},
                    headers=h,
                )
                print(f"  → game_over: {r.status_code}")

        # Print results
        async with SessionLocal() as db:
            game = await game_repo.get_by_id(db, game_id)
            players = await game_repo.get_game_players(db, game_id=game_id)
            from app.users.service import get_user_by_id

            print(f"\n{'=' * 50}")
            print("GAME COMPLETE")
            print(f"{'=' * 50}")
            print(f"Game ID:      {game.id}")
            print(f"Room Code:    {room_code}")
            print(f"Status:       {game.status}")
            print(f"Phase:        {game.phase}")
            print(f"Rounds:       {game.round_number}/{game.max_rounds}")
            print("\nPlayers:")
            for gp in players:
                user = await get_user_by_id(db, gp.user_id)
                print(
                    f"  {user.username} (id={gp.user_id}): role={gp.role}, score={gp.score}"
                )
            print("\nEndpoints:")
            print(
                f"  Analytics: GET http://localhost:8000/api/v1/analytics/game/{game_id}"
            )
            print(
                f"  ML Predict: GET http://localhost:8000/api/v1/ml/predict/{game_id}"
            )


asyncio.run(main())
