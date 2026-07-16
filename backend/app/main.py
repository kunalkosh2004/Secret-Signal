"""
Secret Signal Backend — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.rooms.router import router as rooms_router
from app.game_engine.router import router as games_router
from app.chat.router import router as chat_router
from app.voting.router import router as votes_router
from app.analytics.router import router as analytics_router
from app.replay.router import router as replay_router
from app.rooms import repository as room_repository
from app.core.exceptions import AppException
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.security_middleware import SecurityHeadersMiddleware, RequestIDMiddleware
from app.core.health import router as health_router

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
from sqlalchemy import text
from app.db.session import engine

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
setup_logging()
logger = get_logger("app.main")


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown events
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: runs on startup and shutdown."""
    logger.info(
        "secret_signal_backend_starting",
        extra={
            "environment": settings.environment,
            "debug": settings.debug,
        },
    )
    yield
    logger.info("secret_signal_backend_shutting_down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Secret Signal Backend",
    description="Real-time multiplayer social deduction game API",
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware (order matters — last added = first executed)
# ---------------------------------------------------------------------------
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    logger.info("websocket_connecting", extra={"room_code": room_code})

    async with SessionLocal() as db:
        user, user_id = await authenticate_websocket(
            db=db,
            token=token,
        )

        if user is None or user_id is None:
            logger.warning("websocket_auth_failed", extra={"room_code": room_code})
            await websocket.close(code=1008)
            return

        is_authorized = await authorize_room_connection(
            db=db,
            room_code=room_code,
            user_id=user_id,
        )

        if not is_authorized:
            logger.warning(
                "websocket_not_authorized",
                extra={
                    "room_code": room_code,
                    "user_id": user_id,
                },
            )
            await websocket.close(code=1008)
            return

        await manager.connect(
            room_code=room_code,
            user_id=user_id,
            websocket=websocket,
        )
        logger.info(
            "websocket_connected",
            extra={
                "room_code": room_code,
                "user_id": user_id,
            },
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

                async with SessionLocal() as db:
                    await handle_message(
                        db=db,
                        websocket=websocket,
                        room_code=room_code,
                        user_id=user_id,
                        message=message,
                    )

        except WebSocketDisconnect:
            logger.info(
                "websocket_disconnected",
                extra={
                    "room_code": room_code,
                    "user_id": user_id,
                },
            )
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
            logger.exception(
                "websocket_unhandled_error",
                extra={
                    "room_code": room_code,
                    "user_id": user_id,
                },
            )
            await manager.async_disconnect(
                room_code=room_code,
                user_id=user_id,
                websocket=websocket,
            )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
@app.get("/db-test")
async def db_test():
    async with engine.connect() as conn:
        from app.core.config import settings

        print("=" * 80)
        print("Endpoint DB URL repr:", repr(settings.DATABASE_URL))
        print("Endpoint DB URL len :", len(settings.DATABASE_URL))
        print("=" * 80)
        result = await conn.execute(text("SELECT 1"))
        return {"result": result.scalar()}
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(games_router)
app.include_router(chat_router)
app.include_router(votes_router)
app.include_router(analytics_router)
app.include_router(replay_router)
