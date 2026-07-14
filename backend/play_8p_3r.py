"""Fast 8-player 3-round game — HTTP + DB only, no websockets."""
import asyncio, json, random, httpx, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = "http://localhost:8000/api/v1"
PASSWORD = "testpass123"
USERS = [
    (9,"alice@test.com"),(10,"bob@test.com"),(11,"charlie@test.com"),
    (12,"dave@test.com"),(13,"eve@test.com"),(14,"frank@test.com"),
    (15,"grace@test.com"),(16,"henry@test.com"),
]

CHATS = [
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
DISC = [
    "I'm suspicious of someone here.",
    "Who do you think is the coordinator?",
    "Let's discuss before voting.",
    "I noticed unusual behavior.",
    "We need to vote carefully.",
]

async def main():
    async with httpx.AsyncClient() as c:
        # Login all
        tokens = {}
        for uid, email in USERS:
            r = await c.post(f"{BASE}/auth/login", json={"email": email, "password": PASSWORD})
            assert r.status_code == 200, f"Login failed for {email}: {r.status_code}"
            tokens[uid] = r.json()["access_token"]
        host_token = tokens[9]
        h = {"Authorization": f"Bearer {host_token}"}

        # Create room with 3 rounds, short timers
        r = await c.post(f"{BASE}/rooms", json={
            "max_players": 8,
            "settings": {"max_rounds": 3, "phase_durations": {
                "role_assignment": 3, "round_start": 3,
                "interaction": 10, "discussion": 10, "result": 5,
            }}
        }, headers=h)
        assert r.status_code == 201
        room_code = r.json()["code"]
        print(f"Room: {room_code}")

        # Join all
        for uid, email in USERS[1:]:
            r = await c.post(f"{BASE}/rooms/join", json={"code": room_code},
                            headers={"Authorization": f"Bearer {tokens[uid]}"})
            assert r.status_code == 200

        # Ready up via DB
        from app.db.session import SessionLocal
        from app.rooms import repository as room_repo
        async with SessionLocal() as db:
            room = await room_repo.get_by_code(db, room_code)
            for uid, _ in USERS:
                await room_repo.set_player_ready(db, room_id=room.id, user_id=uid, is_ready=True)

        # Start game
        r = await c.post(f"{BASE}/games/{room_code}/start", headers=h)
        assert r.status_code == 201, f"Start failed: {r.status_code} {r.text}"
        game_id = r.json()["id"]
        print(f"Game ID: {game_id}")

        # Wait for auto-advance role_assignment(3) + round_start(3) = 6s
        print("Waiting for role assignment + round start...")
        await asyncio.sleep(8)

        # Play 3 rounds
        for rnd in range(1, 4):
            print(f"\n--- Round {rnd} ---")

            # Interaction
            r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                             json={"next_phase": "interaction"}, headers=h)
            print(f"  → interaction: {r.status_code}")

            # Write chat messages directly to DB (faster than WS)
            from app.chat import repository as chat_repo
            from app.events import repository as event_repo
            from app.game_engine import repository as game_repo
            from app.training import repository as training_repo

            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                for uid, _ in USERS:
                    gp = await game_repo.get_game_player(db, game_id=game_id, user_id=uid)
                    for _ in range(3):
                        msg = await chat_repo.create_message(db, room_id=room.id, user_id=uid, content=random.choice(CHATS))
                        await event_repo.create_event(db, game_id=game_id, round_number=game.round_number,
                                                       event_type="message_sent", user_id=uid,
                                                       payload={"message_id": msg.id, "content": msg.content})
                        if gp:
                            has_reply = random.random() < 0.2
                            reply_role = None
                            if has_reply:
                                others = [u for u, _ in USERS if u != uid]
                                reply_uid = random.choice(others)
                                rp = await game_repo.get_game_player(db, game_id=game_id, user_id=reply_uid)
                                if rp: reply_role = rp.role
                            await training_repo.create_training_message(db, game_id=game_id, user_id=uid,
                                role=gp.role, phase=game.phase, content=msg.content,
                                round_number=game.round_number, has_reply=has_reply, reply_to_role=reply_role)
                await db.commit()
            print(f"  24 chat messages stored")

            # Discussion
            r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                             json={"next_phase": "discussion"}, headers=h)
            print(f"  → discussion: {r.status_code}")

            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                for uid, _ in USERS:
                    gp = await game_repo.get_game_player(db, game_id=game_id, user_id=uid)
                    msg = await chat_repo.create_message(db, room_id=room.id, user_id=uid, content=random.choice(DISC))
                    await event_repo.create_event(db, game_id=game_id, round_number=game.round_number,
                                                   event_type="message_sent", user_id=uid,
                                                   payload={"message_id": msg.id, "content": msg.content})
                    if gp:
                        await training_repo.create_training_message(db, game_id=game_id, user_id=uid,
                            role=gp.role, phase=game.phase, content=msg.content,
                            round_number=game.round_number)
                await db.commit()
            print(f"  8 discussion messages stored")

            # Voting
            r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                             json={"next_phase": "voting"}, headers=h)
            print(f"  → voting: {r.status_code}")

            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                all_uids = [uid for uid, _ in USERS]
                for uid, _ in USERS:
                    others = [x for x in all_uids if x != uid]
                    target = random.choice(others)
                    from app.voting import repository as vote_repo
                    await vote_repo.create_vote(db, game_id=game_id, round_number=game.round_number,
                                                 voter_user_id=uid, target_user_id=target)
                    await event_repo.create_event(db, game_id=game_id, round_number=game.round_number,
                                                   event_type="vote_cast", user_id=uid,
                                                   payload={"target_user_id": target})
                await db.commit()
            print(f"  8 votes cast")

            # Advance to result
            r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                             json={"next_phase": "result"}, headers=h)
            print(f"  → result: {r.status_code}")

            # Next round or game over
            if rnd < 3:
                r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                                 json={"next_phase": "round_start"}, headers=h)
                print(f"  → round_start: {r.status_code}")
            else:
                r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                                 json={"next_phase": "game_over"}, headers=h)
                print(f"  → game_over: {r.status_code}")

        # Final status
        async with SessionLocal() as db:
            from app.game_engine import repository as game_repo
            game = await game_repo.get_by_id(db, game_id)
            players = await game_repo.get_game_players(db, game_id=game_id)

            print(f"\n{'='*50}")
            print(f"GAME COMPLETE")
            print(f"{'='*50}")
            print(f"Game ID:      {game.id}")
            print(f"Room Code:    {room_code}")
            print(f"Status:       {game.status}")
            print(f"Phase:        {game.phase}")
            print(f"Rounds:       {game.round_number}")
            print(f"Max Rounds:   {game.max_rounds}")
            print(f"\nPlayers:")
            for gp in players:
                print(f"  User {gp.user_id}: role={gp.role}, score={gp.score}")
            print(f"\nAI Analysis Endpoints:")
            print(f"  GET http://localhost:8000/api/v1/analytics/game/{game_id}")
            print(f"  GET http://localhost:8000/api/v1/ml/predict/{game_id}")

asyncio.run(main())
