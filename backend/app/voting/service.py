from sqlalchemy.ext.asyncio import AsyncSession

from app.game_engine import repository as game_repository
from app.voting import repository as vote_repository
from app.voting.models import Vote
from app.voting.schemas import VoteResults, VoteTally


async def cast_vote(
    db: AsyncSession,
    game_id: int,
    round_number: int,
    voter_user_id: int,
    target_user_id: int,
) -> Vote:
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

    vote = await vote_repository.create_vote(
        db,
        game_id=game_id,
        round_number=round_number,
        voter_user_id=voter_user_id,
        target_user_id=target_user_id,
    )

    return vote


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

    coordinator = await game_repository.get_player_by_role(
        db=db,
        game_id=game_id,
        role="coordinator",
    )
    coordinator_identified = False
    coordinator_user_id = None
    if coordinator and tallies:
        top_target = max(tallies, key=lambda t: t[1])[0]
        if top_target == coordinator.user_id:
            coordinator_identified = True
            coordinator_user_id = coordinator.user_id

    return VoteResults(
        round_number=round_number,
        total_votes=total_votes,
        tallies=[
            VoteTally(target_user_id=user_id, count=count)
            for user_id, count in tallies
        ],
        coordinator_identified=coordinator_identified,
        coordinator_user_id=coordinator_user_id,
    )
