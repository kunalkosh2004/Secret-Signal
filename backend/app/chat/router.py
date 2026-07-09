from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.chat.repository import get_room_messages
from app.chat.schemas import ChatMessageResponse
from app.rooms import repository as room_repository
from app.users.models import User


router = APIRouter(
    prefix="/api/v1/rooms/{room_code}/messages",
    tags=["chat"],
)


@router.get("", response_model=list[ChatMessageResponse])
async def list_messages(
    room_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = await room_repository.get_by_code(db, room_code.strip().upper())

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = await room_repository.get_player(
        db,
        room_id=room.id,
        user_id=current_user.id,
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this room",
        )

    messages = await get_room_messages(db, room_id=room.id)

    return [
        ChatMessageResponse(
            id=msg.id,
            user_id=msg.user_id,
            username=username,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg, username in messages
    ]
