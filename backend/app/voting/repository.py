from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.voting.models import Vote


async def create_vote(
    db: AsyncSession,
    game_id: int,
    round_number: int,
    voter_user_id: int,
    target_user_id: int,
) -> Vote:
    vote = Vote(
        game_id=game_id,
        round_number=round_number,
        voter_user_id=voter_user_id,
        target_user_id=target_user_id,
    )

    db.add(vote)

    await db.flush()

    return vote


async def has_voted(
    db: AsyncSession,
    game_id: int,
    round_number: int,
    voter_user_id: int,
) -> bool:
    result = await db.execute(
        select(Vote).where(
            Vote.game_id == game_id,
            Vote.round_number == round_number,
            Vote.voter_user_id == voter_user_id,
        )
    )

    return result.scalar_one_or_none() is not None


async def get_votes_for_round(
    db: AsyncSession,
    game_id: int,
    round_number: int,
) -> list[Vote]:
    result = await db.execute(
        select(Vote).where(
            Vote.game_id == game_id,
            Vote.round_number == round_number,
        )
    )

    return list(result.scalars().all())


async def tally_votes(
    db: AsyncSession,
    game_id: int,
    round_number: int,
) -> list[tuple[int, int]]:
    result = await db.execute(
        select(
            Vote.target_user_id,
            func.count(Vote.id),
        )
        .where(
            Vote.game_id == game_id,
            Vote.round_number == round_number,
        )
        .group_by(Vote.target_user_id)
        .order_by(func.count(Vote.id).desc())
    )

    return list(result.all())
