"""Signal AI — Behavior Analysis Service.

This module contains the rule-based placeholder implementation of the
BehaviorAnalysisService.  It is designed so that replacing it with a
real ML inference service requires changes ONLY in this file.

Architecture (current):
    Game Events ──► Feature Extraction ──► Rule-Based Scoring ──► SignalAIReport

Architecture (future ML):
    Game Events ──► Feature Extraction ──► Feature Store ──► ML Model ──► SignalAIReport
                                                        ▲
                                                        │
                                                  Training Pipeline

The frontend and WebSocket contracts remain identical regardless of
which backend strategy is used.
"""

from __future__ import annotations

import random
import uuid
import logging
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.signal_ai.models import (
    BehaviorMetric,
    ConfidenceLevel,
    PlayerSuspicion,
    SignalAIConfig,
    SignalAIReport,
)
from app.game_engine import repository as game_repository
from app.events import repository as event_repository
from app.voting import repository as vote_repository
from app.missions import repository as mission_repository
from app.users import repository as user_repository
from app.chat import repository as chat_repository
from app.chat import reaction_repository

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _extract_player_features(
    player_events: list[dict],
    all_events_by_others: dict[int, list[dict]],
    player_id: int,
    total_players: int,
    game_phase: str,
) -> dict:
    """Extract raw behavioral features for a single player.

    Returns a dict of feature_name -> numeric value.
    This function is the primary integration point for future ML.
    A real model would consume these same features from a Feature Store.
    """
    total = len(player_events)
    if total == 0:
        return _empty_features()

    # --- Message features ---
    lengths = []
    word_counts = []
    question_count = 0
    topic_shift_count = 0
    caps_count = 0

    TOPIC_SHIFTERS = [
        "but", "however", "actually", "wait", "no", "well",
        "okay so", "let me", "i think", "what if", "hang on",
        "hold on", "sorry", "btw", "by the way", "anyway",
    ]
    QUESTION_MARKERS = [
        "who", "what", "where", "when", "why", "how",
        "do you", "did you", "can you", "could you",
        "is there", "are you", "don't you",
    ]

    for ev in player_events:
        content = ev.get("content", "")
        if not content:
            continue
        lengths.append(len(content))
        word_counts.append(len(content.split()))
        if "?" in content:
            question_count += 1
        content_lower = content.lower()
        for shifter in TOPIC_SHIFTERS:
            if shifter in content_lower:
                topic_shift_count += 1
                break
        words = content.split()
        if words and all(w.isupper() and len(w) > 1 for w in words):
            caps_count += 1

    avg_length = sum(lengths) / len(lengths) if lengths else 0
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
    question_ratio = question_count / total if total > 0 else 0
    topic_shift_ratio = topic_shift_count / total if total > 0 else 0

    # --- Social features ---
    replies_received = 0
    unique_repliers: set[int] = set()
    for other_id, other_events in all_events_by_others.items():
        if other_id == player_id:
            continue
        for ev in other_events:
            if ev.get("reply_to_user_id") == player_id:
                replies_received += 1
                unique_repliers.add(other_id)

    # --- Interaction centrality (simplified) ---
    # How many different players did this player interact with?
    interaction_partners: set[int] = set()
    for ev in player_events:
        if ev.get("reply_to_user_id"):
            interaction_partners.add(ev["reply_to_user_id"])
    for other_id, other_events in all_events_by_others.items():
        if other_id == player_id:
            continue
        for ev in other_events:
            if ev.get("reply_to_user_id") == player_id:
                interaction_partners.add(other_id)

    interaction_centrality = (
        len(interaction_partners) / max(total_players - 1, 1)
    )

    # --- Conversation initiation ---
    # Count messages that start a new thread (not replies)
    conversation_starts = sum(
        1 for ev in player_events if not ev.get("reply_to_user_id")
    )

    # --- Voting features ---
    # (Computed externally, passed in)

    return {
        "total_messages": total,
        "avg_message_length": avg_length,
        "avg_words_per_message": avg_words,
        "question_ratio": question_ratio,
        "topic_shift_count": topic_shift_count,
        "topic_shift_ratio": topic_shift_ratio,
        "caps_count": caps_count,
        "replies_received": replies_received,
        "unique_repliers": len(unique_repliers),
        "interaction_centrality": interaction_centrality,
        "interaction_partners": len(interaction_partners),
        "conversation_starts": conversation_starts,
    }


def _empty_features() -> dict:
    return {
        "total_messages": 0,
        "avg_message_length": 0,
        "avg_words_per_message": 0,
        "question_ratio": 0,
        "topic_shift_count": 0,
        "topic_shift_ratio": 0,
        "caps_count": 0,
        "replies_received": 0,
        "unique_repliers": 0,
        "interaction_centrality": 0,
        "interaction_partners": 0,
        "conversation_starts": 0,
    }


# ---------------------------------------------------------------------------
# Suspicion scoring (rule-based)
# ---------------------------------------------------------------------------

def _compute_suspicion_score(
    features: dict,
    all_features: dict[int, dict],
    round_number: int,
    max_rounds: int,
) -> tuple[float, ConfidenceLevel, list[str]]:
    """Compute a suspicion score (0-100) with confidence and reasons.

    This is the rule-based placeholder.  A future ML model would
    replace this function's body while keeping the same signature.

    The scoring intentionally includes noise and becomes more
    accurate in later rounds (more data = less noise).
    """
    score = 0.0
    reasons: list[str] = []

    # --- Factor 1: Message activity (0-20 points) ---
    total_msgs = features["total_messages"]
    all_msg_counts = [f["total_messages"] for f in all_features.values()]
    max_msgs = max(all_msg_counts) if all_msg_counts else 1
    if max_msgs > 0:
        relative_activity = total_msgs / max_msgs
        activity_score = relative_activity * 20
        score += activity_score
        if total_msgs > 0:
            reasons.append(
                f"Sent {total_msgs} messages "
                f"({relative_activity:.0%} of most active player)"
            )

    # --- Factor 2: Conversation initiation (0-15 points) ---
    conv_starts = features["conversation_starts"]
    all_conv_starts = [f["conversation_starts"] for f in all_features.values()]
    max_conv = max(all_conv_starts) if all_conv_starts else 1
    if max_conv > 0:
        initiation_score = (conv_starts / max_conv) * 15
        score += initiation_score
        if conv_starts >= 3:
            reasons.append(f"Started {conv_starts} conversations")

    # --- Factor 3: Social reach / centrality (0-20 points) ---
    centrality = features["interaction_centrality"]
    centrality_score = centrality * 20
    score += centrality_score
    unique_repliers = features["unique_repliers"]
    if unique_repliers >= 3:
        reasons.append(
            f"Received replies from {unique_repliers} unique players"
        )

    # --- Factor 4: Topic shifting (0-15 points) ---
    topic_count = features["topic_shift_count"]
    if topic_count >= 3:
        score += 15
        reasons.append(f"Shifted conversation topic {topic_count} times")
    elif topic_count >= 1:
        score += topic_count * 5
        reasons.append(f"Shifted conversation topic {topic_count} time(s)")

    # --- Factor 5: Question asking (0-10 points) ---
    q_ratio = features["question_ratio"]
    if q_ratio > 0.3:
        score += 10
        reasons.append("Asks disproportionately many questions")
    elif q_ratio > 0.15:
        score += 5

    # --- Factor 6: Message length anomaly (0-10 points) ---
    avg_len = features["avg_message_length"]
    all_lengths = [f["avg_message_length"] for f in all_features.values()]
    overall_avg = sum(all_lengths) / len(all_lengths) if all_lengths else 0
    if overall_avg > 0:
        if avg_len > overall_avg * 1.5:
            score += 10
            reasons.append("Messages significantly longer than average")
        elif avg_len < overall_avg * 0.5:
            score += 7
            reasons.append("Messages significantly shorter than average")

    # --- Factor 7: Influence score (0-10 points) ---
    # Coordinator often steers discussion toward mission-related topics
    if topic_count >= 2 and conv_starts >= 2:
        influence = min(10, topic_count * 3 + conv_starts * 2)
        score += influence
        reasons.append("Influenced mission-related discussion")

    # --- Round-based confidence adjustment ---
    # More rounds = more data = higher confidence, less noise
    round_progress = round_number / max(max_rounds, 1)
    noise_range = SignalAIConfig.NOISE_RANGE * (1 - round_progress * 0.5)
    noise = random.uniform(-noise_range, noise_range) * 100
    score += noise

    # Clamp
    score = max(0.0, min(100.0, score))

    # Confidence based on data availability
    if round_progress >= 0.75:
        confidence = ConfidenceLevel.HIGH
    elif round_progress >= 0.4:
        confidence = ConfidenceLevel.MEDIUM
    else:
        confidence = ConfidenceLevel.LOW

    # Cap confidence
    if confidence == ConfidenceLevel.HIGH and score > 85:
        score = min(score, SignalAIConfig.MAX_CONFIDENCE_CAP * 100)

    # Trim reasons to top 5
    reasons = reasons[:5]

    return round(score, 1), confidence, reasons


# ---------------------------------------------------------------------------
# Behavior metrics formatting
# ---------------------------------------------------------------------------

def _build_behavior_metrics(
    features: dict,
    all_features: dict[int, dict],
) -> list[BehaviorMetric]:
    """Convert raw features into normalized BehaviorMetric objects."""
    metrics = []

    def _norm(val: float, key: str) -> float:
        all_vals = [f.get(key, 0) for f in all_features.values()]
        max_val = max(all_vals) if all_vals else 1
        return val / max_val if max_val > 0 else 0

    metrics.append(BehaviorMetric(
        name="message_count",
        label="Messages Sent",
        value=features["total_messages"],
        normalized=_norm(features["total_messages"], "total_messages"),
    ))
    metrics.append(BehaviorMetric(
        name="avg_message_length",
        label="Avg Message Length",
        value=features["avg_message_length"],
        normalized=_norm(features["avg_message_length"], "avg_message_length"),
    ))
    metrics.append(BehaviorMetric(
        name="question_ratio",
        label="Question Ratio",
        value=features["question_ratio"],
        normalized=features["question_ratio"],
    ))
    metrics.append(BehaviorMetric(
        name="topic_shifts",
        label="Topic Shifts",
        value=features["topic_shift_count"],
        normalized=_norm(features["topic_shift_count"], "topic_shift_count"),
    ))
    metrics.append(BehaviorMetric(
        name="interaction_centrality",
        label="Interaction Centrality",
        value=features["interaction_centrality"],
        normalized=features["interaction_centrality"],
    ))
    metrics.append(BehaviorMetric(
        name="replies_received",
        label="Replies Received",
        value=features["replies_received"],
        normalized=_norm(features["replies_received"], "replies_received"),
    ))
    metrics.append(BehaviorMetric(
        name="conversation_starts",
        label="Conversation Starts",
        value=features["conversation_starts"],
        normalized=_norm(features["conversation_starts"], "conversation_starts"),
    ))

    return metrics


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

async def generate_signal_report(
    db: AsyncSession,
    game_id: int,
    detective_id: int,
) -> SignalAIReport:
    """Generate a Signal AI analysis report for the detective.

    This is the primary entry point.  A future ML service would
    implement this same function signature with real inference logic.

    TODO: Replace rule-based scoring with ML pipeline:
        1. Extract features via _extract_player_features()
        2. Store in Feature Store (Redis / Postgres)
        3. Query ML model for predictions
        4. Format as SignalAIReport
    """
    game = await game_repository.get_by_id(db, game_id)
    if game is None:
        raise ValueError("Game not found")

    game_players = await game_repository.get_game_players(db, game_id)
    if not game_players:
        raise ValueError("No players found for game")

    all_events = await event_repository.get_game_events(db, game_id)

    # Group message events by player
    messages_by_player: dict[int, list[dict]] = defaultdict(list)
    for event in all_events:
        if event.event_type == "message_sent":
            uid = event.actor_id
            payload = event.payload or {}
            messages_by_player[uid].append({
                "content": payload.get("content", ""),
                "reply_to_user_id": payload.get("reply_to_user_id"),
                "round": event.round_number,
            })

    # Filter to current round only (more data = more accurate later)
    current_round = game.round_number
    round_events: dict[int, list[dict]] = {}
    for uid, evts in messages_by_player.items():
        round_events[uid] = [e for e in evts if e.get("round") == current_round]

    # Also include all historical events for cross-round features
    all_round_events: dict[int, list[dict]] = dict(messages_by_player)

    total_players = len(game_players)

    # Extract features for each player
    all_features: dict[int, dict] = {}
    for gp in game_players:
        uid = gp.user_id
        # Use all historical features for better accuracy in later rounds
        all_features[uid] = _extract_player_features(
            player_events=all_round_events.get(uid, []),
            all_events_by_others={
                k: v for k, v in all_round_events.items() if k != uid
            },
            player_id=uid,
            total_players=total_players,
            game_phase=game.phase,
        )

    # Compute suspicion for each OTHER player (not the detective)
    detective_player = next(
        (gp for gp in game_players if gp.user_id == detective_id), None,
    )
    if detective_player is None:
        raise ValueError("Detective not found in game")

    # Get usernames
    user_map: dict[int, str] = {}
    for gp in game_players:
        user = await user_repository.get_by_id(db, gp.user_id)
        user_map[gp.user_id] = user.username if user else str(gp.user_id)

    # Compute suspicion scores
    player_suspicions: list[PlayerSuspicion] = []
    for gp in game_players:
        if gp.user_id == detective_id:
            continue  # Don't score the detective themselves

        features = all_features.get(gp.user_id, _empty_features())
        suspicion, confidence, reasons = _compute_suspicion_score(
            features=features,
            all_features=all_features,
            round_number=current_round,
            max_rounds=game.max_rounds,
        )

        metrics = _build_behavior_metrics(features, all_features)

        player_suspicions.append(PlayerSuspicion(
            user_id=gp.user_id,
            username=user_map.get(gp.user_id, str(gp.user_id)),
            role_visible="unknown",
            suspicion_score=suspicion,
            confidence=confidence,
            reasons=reasons,
            behavior_metrics=metrics,
        ))

    # Sort by suspicion descending
    player_suspicions.sort(key=lambda p: p.suspicion_score, reverse=True)

    most_suspicious = player_suspicions[0] if player_suspicions else None

    # Scan usage (stored in Redis by the WS handler before calling this)
    # These are passed in from the handler's Redis reads
    scans_used = 0  # Placeholder; actual value set by caller
    scans_remaining = SignalAIConfig.MAX_SCANS_PER_MATCH

    return SignalAIReport(
        scan_id=str(uuid.uuid4()),
        game_id=game_id,
        round_number=current_round,
        detective_id=detective_id,
        most_suspicious=most_suspicious,
        all_players=player_suspicions,
        scans_used=scans_used,
        scans_remaining=scans_remaining,
        model_version="SignalAI v0.1",
        generated_at=datetime.now(timezone.utc),
    )
