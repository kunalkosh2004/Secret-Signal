from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.users.models import User
from app.voting import service as voting_service
from app.game_engine import repository as game_repository
from app.rooms import repository as room_repository


router = APIRouter(
    prefix="/api/v1/votes",
    tags=["votes"],
)


@router.get("/{game_id}/round/{round_number}")
async def get_vote_results(
    game_id: int,
    round_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    game = await game_repository.get_by_id(db, game_id)

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Game not found",
        )

    room = await room_repository.get_by_id(db, game.room_id)

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    membership = await room_repository.get_player(
        db, room_id=room.id, user_id=current_user.id
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="Not a member of this room",
        )

    results = await voting_service.tally_votes(
        db=db,
        game_id=game_id,
        round_number=round_number,
    )

    return results


@router.get("/{game_id}")
async def get_all_votes(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    game = await game_repository.get_by_id(db, game_id)

    if game is None:
        raise HTTPException(
            status_code=404,
            detail="Game not found",
        )

    room = await room_repository.get_by_id(db, game.room_id)

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    membership = await room_repository.get_player(
        db, room_id=room.id, user_id=current_user.id
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="Not a member of this room",
        )

    all_results = []
    for r in range(1, game.round_number + 1):
        results = await voting_service.tally_votes(
            db=db,
            game_id=game_id,
            round_number=r,
        )
        all_results.append(results)

    return all_results
