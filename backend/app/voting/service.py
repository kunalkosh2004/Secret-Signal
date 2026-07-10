from sqlalchemy.ext.asyncio import AsyncSession

from app.voting import repository as vote_repository
from app.voting.schemas import VoteResults, VoteTally


async def cast_vote(
    db: AsyncSession,
    game_id: int,
    round_number: int,
    voter_user_id: int,
    target_user_id: int,
) -> None:
    already_voted = await vote_repository.has_voted(
        db,
        game_id=game_id,
        round_number=round_number,
        voter_user_id=voter_user_id,
    )

    if already_voted:
        raise ValueError("You have already voted this round")

    if voter_user_id == target_user_id:
        raise ValueError("You cannot vote for yourself")

    await vote_repository.create_vote(
        db,
        game_id=game_id,
        round_number=round_number,
        voter_user_id=voter_user_id,
        target_user_id=target_user_id,
    )

    await db.commit()


async def tally_votes(
    db: AsyncSession,
    game_id: int,
    round_number: int,
) -> VoteResults:
    tallies = await vote_repository.tally_votes(
        db,
        game_id=game_id,
        round_number=round_number,
    )

    total_votes = sum(count for _, count in tallies)

    return VoteResults(
        round_number=round_number,
        total_votes=total_votes,
        tallies=[
            VoteTally(target_user_id=user_id, count=count)
            for user_id, count in tallies
        ],
    )
