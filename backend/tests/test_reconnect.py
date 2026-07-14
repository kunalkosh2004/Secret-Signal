import asyncio

from app.db.session import SessionLocal
from app.game_engine.service import advance_phase
from app.game_engine.state_machine import GamePhase


GAME_ID = 1  # replace with your actual game id


async def main():
    async with SessionLocal() as db:
        print("\n1. Testing valid transition")

        game = await advance_phase(
            db=db,
            game_id=GAME_ID,
            next_phase=GamePhase.ROUND_START,
        )

        print(f"Success: game {game.id} is now in phase '{game.phase}'")

        print("\n2. Testing invalid transition")

        try:
            await advance_phase(
                db=db,
                game_id=GAME_ID,
                next_phase=GamePhase.VOTING,
            )

        except ValueError as exc:
            print(f"Correctly rejected: {exc}")


asyncio.run(main())
