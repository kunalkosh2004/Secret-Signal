"""8-user 5-round game with randomized messages and Signal AI scans."""
import asyncio
import random
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
    (14, "frank@test.com"),
    (15, "grace@test.com"),
    (16, "henry@test.com"),
]

CHAT_POOL = [
    "I think we should focus on the mission.",
    "Who do you all suspect?",
    "I am definitely not the coordinator.",
    "Has anyone noticed anything suspicious?",
    "Let's work together on this.",
    "I trust most of you here.",
    "Be careful who you vote for.",
    "The coordinator is probably staying quiet.",
    "I have been very active this round.",
    "Why is someone so quiet today?",
    "I think it might be the person who voted weirdly.",
    "We need more information before voting.",
    "I noticed someone changed their story.",
    "This is getting intense.",
    "I agree with the previous point.",
    "Can someone explain their reasoning?",
    "I am suspicious of the quiet ones.",
    "Let me share what I observed.",
    "The evidence points to someone specific.",
    "I think we should narrow it down.",
    "Trust me, I know what I am doing.",
    "The coordinator is playing it smart.",
    "We cannot afford a wrong vote.",
    "I have a theory about who it is.",
    "Listen carefully before you vote.",
    "Some of you are acting strange.",
    "I voted based on behavior patterns.",
    "The coordinator slipped up already.",
    "We need to coordinate our votes.",
    "I am 90 percent sure about someone.",
    "Let us review the conversation.",
    "Someone is definitely hiding something.",
    "I will reveal my suspicions soon.",
    "The quietest person is often suspicious.",
    "I have been tracking behavior closely.",
    "My gut feeling says it is someone specific.",
    "We should consider all possibilities.",
    "I am not buying what someone said earlier.",
    "The coordinator is likely among the vocal ones.",
    "Let us think about who benefits most.",
    "I noticed a contradiction in someone's logic.",
    "The voting pattern was very telling.",
    "I think we have a mole among us.",
    "Trust goes both ways in this game.",
    "I will vote based on evidence, not feelings.",
    "The coordinator must be sweating right now.",
    "We are running out of rounds.",
    "I feel confident about my read.",
    "Someone needs to step up and lead.",
    "The truth will come out eventually.",
]

DISCUSSION_POOL = [
    "After thinking about it, I suspect the coordinator.",
    "Let us compare notes on suspicious behavior.",
    "I noticed someone avoided answering a question.",
    "The coordinator is definitely among the quiet ones.",
    "I think we should focus on voting patterns.",
    "Whoever is the coordinator played well.",
    "I have been analyzing everyone's messages.",
    "The coordinator might have slipped up.",
    "We need to vote with high confidence.",
    "I am narrowing down my suspects.",
    "The evidence is pointing in one direction.",
    "I trust my analysis of this round.",
    "The coordinator is trying to blend in.",
    "Let us discuss the most suspicious moments.",
    "I think the coordinator overplayed their hand.",
    "We should target the most suspicious player.",
    "My analysis shows a clear pattern.",
    "The coordinator made a critical mistake.",
    "I am confident in my assessment.",
    "Let us finalize our votes carefully.",
]


async def http_get(c, path, headers):
    r = await c.get(f"{BASE}{path}", headers=headers)
    return r


async def main():
    import httpx
    async with httpx.AsyncClient(timeout=30) as c:
        # Login all 8 users
        tokens = {}
        for uid, email in USERS:
            r = await c.post(f"{BASE}/auth/login", json={"email": email, "password": PW})
            assert r.status_code == 200, f"Login {email}: {r.status_code} {r.text}"
            tokens[uid] = r.json()["access_token"]
        print(f"Logged in {len(USERS)} users")

        host_uid = USERS[0][0]
        host_token = tokens[host_uid]
        h = {"Authorization": f"Bearer {host_token}"}

        # Create room with 5 rounds
        r = await c.post(f"{BASE}/rooms", json={
            "max_players": 8,
            "settings": {
                "max_rounds": 5,
                "phase_durations": {
                    "role_assignment": 3,
                    "round_start": 3,
                    "interaction": 15,
                    "discussion": 15,
                    "result": 5,
                },
            },
        }, headers=h)
        assert r.status_code == 201, f"Create room: {r.status_code} {r.text}"
        room_code = r.json()["code"]
        print(f"Room: {room_code}")

        # Join all other users
        for uid, email in USERS[1:]:
            r = await c.post(f"{BASE}/rooms/join", json={"code": room_code},
                            headers={"Authorization": f"Bearer {tokens[uid]}"})
            assert r.status_code == 200, f"Join {email}: {r.status_code} {r.text}"
        print(f"All {len(USERS)} players joined")

        # Ready all players via DB
        from app.db.session import SessionLocal
        from app.rooms import repository as room_repo
        async with SessionLocal() as db:
            room = await room_repo.get_by_code(db, room_code)
            for uid, _ in USERS:
                await room_repo.set_player_ready(db, room_id=room.id, user_id=uid, is_ready=True)
            await db.commit()
        print("All players ready")

        # Start game
        r = await c.post(f"{BASE}/games/{room_code}/start", headers=h)
        assert r.status_code == 201, f"Start game: {r.status_code} {r.text}"
        game_id = r.json()["id"]
        print(f"\nGame started! ID: {game_id}")

        # Wait for auto-advance to interaction
        print("Waiting for role assignment + round start (6s)...")
        await asyncio.sleep(8)

        from app.chat import repository as chat_repo
        from app.events import repository as event_repo
        from app.game_engine import repository as game_repo
        from app.training import repository as training_repo
        from app.voting import repository as vote_repo
        from app.signal_ai.service import generate_signal_report

        for rnd in range(1, 6):
            print(f"\n{'='*50}")
            print(f"  ROUND {rnd}/5")
            print(f"{'='*50}")

            # Check phase
            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                print(f"  Phase: {game.phase}, Round: {game.round_number}")
                current_phase = game.phase

            # Advance to interaction if needed
            if current_phase != "interaction":
                r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                                 json={"next_phase": "interaction"}, headers=h)
                print(f"  -> interaction: {r.status_code}")

            # === INTERACTION PHASE: Randomized messages ===
            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                total_msgs = 0

                for uid, _ in USERS:
                    gp = await game_repo.get_game_player(db, game_id=game_id, user_id=uid)
                    # Randomize: 5-40 messages per user
                    msg_count = random.randint(5, 40)

                    for _ in range(msg_count):
                        content = random.choice(CHAT_POOL)
                        msg = await chat_repo.create_message(
                            db, room_id=room.id, user_id=uid, content=content,
                        )
                        await event_repo.create_event(
                            db, game_id=game_id, round_number=rnd,
                            event_type="message_sent", user_id=uid,
                            payload={"message_id": msg.id, "content": content},
                        )
                        # Training data
                        if gp:
                            has_reply = random.random() < 0.3
                            reply_role = None
                            if has_reply:
                                others = [u for u, _ in USERS if u != uid]
                                rp = await game_repo.get_game_player(
                                    db, game_id=game_id, user_id=random.choice(others),
                                )
                                if rp:
                                    reply_role = rp.role
                            await training_repo.create_training_message(
                                db, game_id=game_id, user_id=uid, role=gp.role,
                                phase=game.phase, content=content,
                                round_number=rnd,
                                has_reply=has_reply, reply_to_role=reply_role,
                            )

                    total_msgs += msg_count
                    print(f"    {email.split('@')[0]:>8}: {msg_count} messages")

                await db.commit()
            print(f"  Total messages this round: {total_msgs}")

            # === DISCUSSION PHASE ===
            r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                             json={"next_phase": "discussion"}, headers=h)
            print(f"  -> discussion: {r.status_code}")

            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                for uid, _ in USERS:
                    gp = await game_repo.get_game_player(db, game_id=game_id, user_id=uid)
                    # 1-3 discussion messages per user
                    for _ in range(random.randint(1, 3)):
                        content = random.choice(DISCUSSION_POOL)
                        msg = await chat_repo.create_message(
                            db, room_id=room.id, user_id=uid, content=content,
                        )
                        await event_repo.create_event(
                            db, game_id=game_id, round_number=rnd,
                            event_type="message_sent", user_id=uid,
                            payload={"message_id": msg.id, "content": content},
                        )
                        if gp:
                            await training_repo.create_training_message(
                                db, game_id=game_id, user_id=uid, role=gp.role,
                                phase=game.phase, content=content,
                                round_number=rnd,
                            )
                await db.commit()

            # === SIGNAL AI SCAN ===
            async with SessionLocal() as db:
                coordinator = await game_repo.get_player_by_role(
                    db, game_id=game_id, role="coordinator",
                )
                detective = await game_repo.get_player_by_role(
                    db, game_id=game_id, role="detective",
                )
                detective_uid = detective.user_id if detective else USERS[1][0]

                report = await generate_signal_report(db, game_id, detective_uid)
                print("\n  SIGNAL AI REPORT:")
                print(f"    Scan ID: {report.scan_id}")
                print(f"    Model: {report.model_version}")
                if report.most_suspicious:
                    ms = report.most_suspicious
                    print(f"    Most Suspicious: {ms.username} "
                          f"({ms.suspicion_score:.1f}%)")
                for sp in report.all_players[:3]:
                    print(f"    {sp.username}: suspicion={sp.suspicion_score:.1f}% "
                          f"({sp.confidence.value})")
                    for m in sp.behavior_metrics[:2]:
                        print(f"      - {m.label}: {m.value:.2f} (norm={m.normalized:.2f})")

            # === VOTING PHASE ===
            r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                             json={"next_phase": "voting"}, headers=h)
            print(f"\n  -> voting: {r.status_code}")

            # Cast votes — avoid the coordinator so game runs all 5 rounds
            async with SessionLocal() as db:
                coordinator = await game_repo.get_player_by_role(
                    db, game_id=game_id, role="coordinator",
                )
                coord_uid = coordinator.user_id if coordinator else None
                all_uids = [uid for uid, _ in USERS]

                # Never vote for coordinator — game continues all 5 rounds
                for uid, _ in USERS:
                    others = [x for x in all_uids if x != uid and x != coord_uid]
                    if not others:
                        others = [x for x in all_uids if x != uid]
                    target = random.choice(others)
                    await vote_repo.create_vote(
                        db, game_id=game_id, round_number=rnd,
                        voter_user_id=uid, target_user_id=target,
                    )
                await db.commit()
            print("  8 votes cast")

            # === RESULT PHASE ===
            r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                             json={"next_phase": "result"}, headers=h)
            print(f"  -> result: {r.status_code}")

            # Check if game ended
            async with SessionLocal() as db:
                game = await game_repo.get_by_id(db, game_id)
                if game.status == "completed":
                    print(f"  Game ended at round {rnd}!")
                    break

            # Advance to next round or game over
            if rnd < 5:
                r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                                 json={"next_phase": "round_start"}, headers=h)
                print(f"  -> round_start: {r.status_code}")
                print("  Waiting for auto-advance...")
                await asyncio.sleep(8)
            else:
                r = await c.post(f"{BASE}/games/{game_id}/advance-phase",
                                 json={"next_phase": "game_over"}, headers=h)
                print(f"  -> game_over: {r.status_code}")

        # Final results
        async with SessionLocal() as db:
            game = await game_repo.get_by_id(db, game_id)
            players = await game_repo.get_game_players(db, game_id=game_id)
            from app.users.service import get_user_by_id

            print(f"\n{'='*50}")
            print("  GAME COMPLETE")
            print(f"{'='*50}")
            print(f"  Game ID:     {game.id}")
            print(f"  Room Code:   {room_code}")
            print(f"  Status:      {game.status}")
            print(f"  Phase:       {game.phase}")
            print(f"  Rounds:      {game.round_number}/{game.max_rounds}")
            print("\n  Players:")
            for gp in players:
                user = await get_user_by_id(db, gp.user_id)
                tag = " ***COORDINATOR***" if gp.role == "coordinator" else ""
                print(f"    {user.username:>10} (id={gp.user_id}): "
                      f"role={gp.role:15} score={gp.score}{tag}")
            print("\n  Endpoints:")
            print(f"    Analysis: http://localhost:8000/api/v1/analytics/{game_id}")
            print(f"    Replay:   http://localhost:8000/api/v1/replay/{game_id}")
            print(f"    Frontend: http://localhost:5173/game/{room_code}/analysis")

asyncio.run(main())
