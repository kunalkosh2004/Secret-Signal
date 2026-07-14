"""
Secret Signal Backend — FastAPI application entry point.
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.rooms.router import router as rooms_router
from app.game_engine.router import router as games_router
from app.chat.router import router as chat_router
from app.voting.router import router as votes_router
from app.analytics.router import router as analytics_router
from app.rooms import repository as room_repository
from app.core.exceptions import AppException

from app.db.session import SessionLocal
from app.websocket.handlers import (
    authenticate_websocket,
    authorize_room_connection,
    broadcast_room_state,
    handle_message,
    send_chat_history_to_user,
    send_game_state_to_user,
)
from app.websocket.manager import manager

app = FastAPI(title="Secret Signal Backend")

@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
    )


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    room_code: str,
):
    room_code = room_code.strip().upper()

    async with SessionLocal() as db:
        user, user_id = await authenticate_websocket(
            db=db,
            token=token,
        )

        if user is None or user_id is None:
            await websocket.close(code=1008)
            return

        is_authorized = await authorize_room_connection(
            db=db,
            room_code=room_code,
            user_id=user_id,
        )

        if not is_authorized:
            await websocket.close(code=1008)
            return

        await manager.connect(
            room_code=room_code,
            user_id=user_id,
            websocket=websocket,
        )
        await broadcast_room_state(
            db=db,
            room_code=room_code,
        )

        await send_chat_history_to_user(
            db=db,
            websocket=websocket,
            room_code=room_code,
        )

        try:
            await send_game_state_to_user(
                db=db,
                websocket=websocket,
                room_code=room_code,
                user_id=user_id,
            )
        except RuntimeError:
            pass

        try:
            while True:
                message = await websocket.receive_json()

                await handle_message(
                    db=db,
                    websocket=websocket,
                    room_code=room_code,
                    user_id=user_id,
                    message=message,
                )

        except WebSocketDisconnect:
            await manager.async_disconnect(
                room_code=room_code,
                user_id=user_id,
                websocket=websocket,
            )

            room = await room_repository.get_by_code(
                db,
                room_code,
            )

            if room is not None and room.status == "waiting":
                await room_repository.set_player_ready(
                    db,
                    room_id=room.id,
                    user_id=user_id,
                    is_ready=False,
                )

            await broadcast_room_state(
                db=db,
                room_code=room_code,
            )

        except RuntimeError:
            await manager.async_disconnect(
                room_code=room_code,
                user_id=user_id,
                websocket=websocket,
            )

        except Exception:
            await manager.async_disconnect(
                room_code=room_code,
                user_id=user_id,
                websocket=websocket,
            )
# ---------------------------------------------------------------------------
# CORS — Cross-Origin Resource Sharing
# ---------------------------------------------------------------------------
# During development:
#   Frontend:  http://localhost:5173
#   Backend:   http://localhost:8000
#
# These are DIFFERENT ORIGINS (different ports).
# Without CORS, the browser blocks frontend JavaScript from calling the backend.
#
# For production, replace the list with the actual frontend domain(s).
# Do NOT use ["*"] (allow all origins) if you send cookies or credentials,
# because the browser will reject credentialed requests with wildcard origins.
#
# If you switch to HttpOnly cookies for auth, you MUST:
#   - Set allow_origins to the exact frontend origin (not "*")
#   - Set allow_credentials = True
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:4173",   # Vite preview
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(games_router)
app.include_router(chat_router)
app.include_router(votes_router)
app.include_router(analytics_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}
