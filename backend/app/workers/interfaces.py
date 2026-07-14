"""
Background worker architecture for Secret Signal.

This module defines the interfaces and job types for future
background processing. The actual worker implementation (Celery,
ARQ, or custom) is NOT yet implemented.

Job Types:
  1. Replay Generation    — Build replay timeline after game ends
  2. Signal AI Analysis   — Run Signal AI scan during gameplay
  3. Statistics Update    — Update player statistics after game
  4. Cleanup              — Remove expired rooms, sessions, stale data
  5. Notification         — Send email/push notifications
  6. ML Retraining        — Retrain the ML model with new data
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class JobPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class JobResult:
    """Result of a background job execution."""
    job_id: str
    status: JobStatus
    result: Any = None
    error: str | None = None
    attempts: int = 0
    max_retries: int = 3


@dataclass
class JobDefinition:
    """Defines a background job to be queued."""
    job_type: str
    payload: dict
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    retry_delay_seconds: int = 30
    timeout_seconds: int = 300


# =============================================================================
# Worker Interface
# =============================================================================
class BaseWorker(ABC):
    """
    Abstract base class for background workers.

    Future implementations:
      - ARQ (async Redis queue) — recommended for this stack
      - Celery with Redis broker
      - Custom asyncio worker with Redis pub/sub
    """

    @abstractmethod
    async def start(self) -> None:
        """Initialize the worker (connect to broker, etc.)."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully shut down the worker."""
        ...

    @abstractmethod
    async def enqueue(self, job: JobDefinition) -> str:
        """Submit a job to the queue. Returns job_id."""
        ...

    @abstractmethod
    async def get_status(self, job_id: str) -> JobStatus:
        """Check the status of a job."""
        ...


# =============================================================================
# Job Handlers (future implementation stubs)
# =============================================================================
class ReplayGenerationJob:
    """
    Generates a replay timeline after a game ends.

    Trigger: game_over event via WebSocket handler
    Input: game_id
    Output: replay timeline stored in game_events table
    Estimated duration: 1-5 seconds (depends on event count)
    """

    async def execute(self, game_id: int) -> JobResult:
        raise NotImplementedError("Worker not yet implemented")


class SignalAIAnalysisJob:
    """
    Runs Signal AI analysis for a game round.

    Trigger: phase transition to discussion/voting
    Input: game_id, round_number
    Output: Signal AI report stored in signal_ai_reports table
    Estimated duration: 2-10 seconds (ML inference)
    """

    async def execute(self, game_id: int, round_number: int) -> JobResult:
        raise NotImplementedError("Worker not yet implemented")


class StatisticsUpdateJob:
    """
    Updates player statistics after a game completes.

    Trigger: game_over event
    Input: game_id
    Output: Updated player profiles in training_messages table
    Estimated duration: <1 second
    """

    async def execute(self, game_id: int) -> JobResult:
        raise NotImplementedError("Worker not yet implemented")


class CleanupJob:
    """
    Periodic cleanup of stale data.

    Trigger: Cron schedule (every hour)
    Input: none
    Actions:
      - Remove rooms with status 'waiting' older than 24h
      - Remove expired JWT blacklist entries from Redis
      - Archive completed games older than 90 days
    Estimated duration: 5-30 seconds
    """

    async def execute(self) -> JobResult:
        raise NotImplementedError("Worker not yet implemented")


class MLRetrainingJob:
    """
    Retrains the ML model with accumulated training data.

    Trigger: Cron schedule (weekly) or manual trigger
    Input: training_messages table
    Output: Updated model.pkl
    Estimated duration: 30-120 seconds
    """

    async def execute(self) -> JobResult:
        raise NotImplementedError("Worker not yet implemented")
