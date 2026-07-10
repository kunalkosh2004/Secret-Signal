from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.users.models import User
from app.analytics import service as analytics_service
from app.game_engine import repository as game_repository
from app.rooms import repository as room_repository


router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"],
)


@router.get("/{game_id}")
async def get_game_analysis(
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

    if game.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Game is not completed yet",
        )

    analysis = await analytics_service.analyze_game(
        db=db,
        game_id=game_id,
    )

    return {
        "game_id": analysis.game_id,
        "total_rounds": analysis.total_rounds,
        "completed_missions": analysis.completed_missions,
        "winner": analysis.winner,
        "summary": analysis.summary,
        "coordination_score": analysis.coordination_score,
        "voting_patterns": analysis.voting_patterns,
        "players": [
            {
                "user_id": p.user_id,
                "role": p.role,
                "message_count": p.message_count,
                "questions_asked": p.questions_asked,
                "topic_initiations": p.topic_initiations,
                "avg_message_length": p.avg_message_length,
                "suspicion_score": p.suspicion_score,
                "voting_accuracy": p.voting_accuracy,
                "round_breakdown": p.round_breakdown,
            }
            for p in analysis.players
        ],
    }
