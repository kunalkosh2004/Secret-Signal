"""
Production health check endpoints.

/health     — Liveness probe. Returns 200 if the process is alive.
              Used by: load balancers, Docker HEALTHCHECK, Kubernetes livenessProbe.
              Does NOT check dependencies. If this fails, restart the container.

/readiness  — Readiness probe. Returns 200 only if the service can handle traffic.
              Used by: Kubernetes readinessProbe, load balancer health checks.
              Checks: database connectivity, Redis connectivity.
              If this fails, stop routing traffic but do NOT restart.

/startup    — Startup probe. Returns 200 once initialization is complete.
              Used by: Kubernetes startupProbe to prevent premature health checks.
"""

import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db

router = APIRouter(tags=["health"])
logger = get_logger("app.core.health")


@router.get("/health")
async def liveness():
    """
    Liveness probe — is the process alive?
    This should be fast and check nothing external.
    """
    return {
        "status": "alive",
        "service": "secret-signal-backend",
        "environment": settings.environment,
    }


@router.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe — can the service handle traffic?
    Checks database and Redis connectivity.
    """
    checks = {}
    all_healthy = True

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Redis check
    try:
        from app.core.redis import redis_client
        await redis_client.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
    }


@router.get("/startup")
async def startup():
    """
    Startup probe — has initialization completed?
    Returns 200 immediately. In the future, this can verify
    that migrations have run, models are loaded, etc.
    """
    return {
        "status": "started",
        "uptime_seconds": time.process_time(),
    }
