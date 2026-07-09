from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.rooms import repository as room_repository
from app.db.session import get_db
from app.rooms.service import (
    create_room as create_room_service,
    join_room as join_room_service,
    leave_room as leave_room_service,
)
from app.users.models import User
from app.rooms.schemas import (
    CreateRoomRequest,
    JoinRoomRequest,
    RoomResponse,
)


router = APIRouter(
    prefix="/api/v1/rooms",
    tags=["rooms"],
)

@router.post(
    "",
    status_code=201,
    response_model=RoomResponse,
)
async def create_room(
    request: CreateRoomRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_room_service(
        db=db,
        host_id=current_user.id,
        request=request,
    )

@router.post(
    "/join",
    response_model=RoomResponse,
)
async def join_room(
    request: JoinRoomRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await join_room_service(
            db=db,
            code=request.code,
            user_id=current_user.id,
        )

    except ValueError as exc:
        message = str(exc)

        status_code = 400

        if message == "Room not found":
            status_code = 404

        elif message == "User is already in this room":
            status_code = 409

        elif message == "Room is full":
            status_code = 409

        raise HTTPException(
            status_code=status_code,
            detail=message,
        )

@router.get(
    "/{code}",
    response_model=RoomResponse,
)
async def get_room(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = await room_repository.get_by_code(
        db,
        code.strip().upper(),
    )

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    return room

@router.post(
    "/{code}/leave",
    response_model=RoomResponse,
)
async def leave_room(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await leave_room_service(
            db=db,
            code=code.strip().upper(),
            user_id=current_user.id,
        )

    except ValueError as exc:
        message = str(exc)

        status_code = 400

        if message == "Room not found":
            status_code = 404

        raise HTTPException(
            status_code=status_code,
            detail=message,
        )