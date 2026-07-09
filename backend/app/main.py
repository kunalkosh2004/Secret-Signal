"""
Secret Signal Backend — FastAPI application entry point.
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.rooms.router import router as rooms_router
from app.core.exceptions import AppException

from app.db.session import SessionLocal
from app.websocket.handlers import (
    authenticate_websocket,
    authorize_room_connection,
    broadcast_room_state,
    handle_message,
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
        user = await authenticate_websocket(
            db=db,
            token=token,
        )

        if user is None:
            await websocket.close(code=1008)
            return

        is_authorized = await authorize_room_connection(
            db=db,
            room_code=room_code,
            user_id=user.id,
        )

        if not is_authorized:
            await websocket.close(code=1008)
            return

        await manager.connect(
            room_code=room_code,
            user_id=user.id,
            websocket=websocket,
        )
        await broadcast_room_state(
            db=db,
            room_code=room_code,
        )

        try:
            while True:
                message = await websocket.receive_json()

                await handle_message(
                    websocket=websocket,
                    room_code=room_code,
                    user_id=user.id,
                    message=message,
                )

        except WebSocketDisconnect:
            manager.disconnect(
                room_code=room_code,
                user_id=user.id,
            )
            await broadcast_room_state(
                db=db,
                room_code=room_code,
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


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}
