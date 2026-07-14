"""Signal AI — Pydantic response models.

These models define the contract between the BehaviorAnalysisService
and the WebSocket handler / frontend.  They are pure dataTransfer
objects — no ORM mapping, no DB tables.

The architecture is designed so that a future ML inference service
can return the same shapes without any frontend changes.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Confidence enum
# ---------------------------------------------------------------------------

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Behavioral feature primitives
# ---------------------------------------------------------------------------

class BehaviorMetric(BaseModel):
    """A single quantified behavioral observation."""

    name: str = Field(
        ...,
        description="Machine-readable feature key, e.g. 'message_count'",
    )
    label: str = Field(
        ...,
        description="Human-readable label, e.g. 'Messages Sent'",
    )
    value: float = Field(
        ...,
        description="Raw numeric value of the metric.",
    )
    normalized: float = Field(
        ...,
        description="Value normalized to 0-1 range relative to all players.",
    )


# ---------------------------------------------------------------------------
# Per-player suspicion entry
# ---------------------------------------------------------------------------

class PlayerSuspicion(BaseModel):
    """One player's entry in the Signal AI report."""

    user_id: int
    username: str
    role_visible: str = Field(
        ...,
        description=(
            "The role the scanning detective *thinks* this player might have. "
            "Always 'unknown' — Signal AI never reveals actual roles."
        ),
    )
    suspicion_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="0-100 suspicion score. Higher = more likely coordinator.",
    )
    confidence: ConfidenceLevel = Field(
        ...,
        description="How confident the model is in this suspicion score.",
    )
    reasons: list[str] = Field(
        default_factory=list,
        description=(
            "Explainable reasons for the suspicion score. "
            "Each reason should be a human-readable sentence."
        ),
    )
    behavior_metrics: list[BehaviorMetric] = Field(
        default_factory=list,
        description="Quantified behavioral features for this player.",
    )


# ---------------------------------------------------------------------------
# Top-level Signal AI report
# ---------------------------------------------------------------------------

class SignalAIReport(BaseModel):
    """Complete output of a Signal AI scan.

    This is the object sent to the detective over WebSocket.
    A future ML service returns the same shape.
    """

    scan_id: str = Field(
        ...,
        description="Unique identifier for this scan instance.",
    )
    game_id: int
    round_number: int
    detective_id: int

    most_suspicious: Optional[PlayerSuspicion] = Field(
        None,
        description="The player the model considers most suspicious.",
    )
    all_players: list[PlayerSuspicion] = Field(
        default_factory=list,
        description="Suspicion entries for every other player in the game.",
    )

    scans_used: int = Field(
        ...,
        description="Number of scans the detective has used this match.",
    )
    scans_remaining: int = Field(
        ...,
        description="Number of scans the detective can still use.",
    )

    model_version: str = Field(
        default="SignalAI v0.1",
        description="Version identifier for the analysis model.",
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of when this report was generated.",
    )


# ---------------------------------------------------------------------------
# Scan status responses (for error / cooldown cases)
# ---------------------------------------------------------------------------

class ScanStatus(BaseModel):
    """Returned when a scan cannot proceed."""

    status: str = Field(
        ...,
        description="'error' or 'cooldown'.",
    )
    message: str
    scans_used: int = 0
    scans_remaining: int = 4


# ---------------------------------------------------------------------------
# Game balance constants
# ---------------------------------------------------------------------------

class SignalAIConfig:
    """Tunable game-balance constants.

    These are class-level constants for now.  A future version could
    load them from a database table or environment variables.
    """

    MAX_SCANS_PER_MATCH: int = 4
    SCANS_PER_ROUND: int = 1
    COOLDOWN_SECONDS: int = 0  # No time cooldown; round-based only
    MAX_CONFIDENCE_CAP: float = 0.95  # Never exceed 95% confidence
    NOISE_RANGE: float = 0.12  # +/- 12% random noise for imperfection
