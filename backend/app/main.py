"""
Secret Signal Backend — FastAPI application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.core.exceptions import AppException

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


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}
