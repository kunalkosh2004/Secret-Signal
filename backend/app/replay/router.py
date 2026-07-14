"""Replay Engine — REST API endpoints.

Endpoints:
    GET /api/v1/replay/{game_id}           — Full replay timeline
    GET /api/v1/replay/{game_id}/snapshot   — State at a specific event
    GET /api/v1/replay/{game_id}/events     — Raw events (for debugging)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.game_engine import repository as game_repository
from app.rooms import repository as room_repository
from app.users.models import User
from app.replay.engine import ReplayEngine

router = APIRouter(
    prefix="/api/v1/replay",
    tags=["replay"],
)

engine = ReplayEngine()


@router.get("/{game_id}")
async def get_replay_timeline(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the complete replay timeline for a finished game.

    Returns all events in deterministic order, enriched with
    actor names and relative timestamps.
    """
    game = await game_repository.get_by_id(db, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    # Only allow replay for completed games
    if game.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Replay is only available for completed games",
        )

    # Verify user is a member of the room
    room = await room_repository.get_by_id(db, game.room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = await room_repository.get_player(
        db, room_id=room.id, user_id=current_user.id,
    )
    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="Not a member of this room",
        )

    try:
        timeline = await engine.build_timeline(db, game_id)
        return timeline.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build replay: {str(exc)}",
        )


@router.get("/{game_id}/snapshot")
async def get_state_snapshot(
    game_id: int,
    sequence_number: int = Query(..., ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get reconstructed game state at a specific sequence number.

    Useful for debugging and the event inspector.
    """
    game = await game_repository.get_by_id(db, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    room = await room_repository.get_by_id(db, game.room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = await room_repository.get_player(
        db, room_id=room.id, user_id=current_user.id,
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    try:
        snapshot = await engine.get_state_at(db, game_id, sequence_number)
        return snapshot.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build snapshot: {str(exc)}",
        )


@router.get("/{game_id}/events")
async def get_raw_events(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get raw events for a game (debugging endpoint).

    Returns the events in deterministic order without enrichment.
    """
    game = await game_repository.get_by_id(db, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    room = await room_repository.get_by_id(db, game.room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = await room_repository.get_player(
        db, room_id=room.id, user_id=current_user.id,
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    from app.events import repository as event_repository
    events = await event_repository.get_game_events(db, game_id)

    return [
        {
            "sequence_number": e.sequence_number,
            "event_type": e.event_type,
            "actor_id": e.actor_id,
            "round_number": e.round_number,
            "payload": e.payload,
            "metadata": e.event_metadata,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
