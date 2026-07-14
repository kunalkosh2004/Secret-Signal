"""Replay Engine — Core event processing and state reconstruction.

The ReplayEngine is the heart of the event sourcing system. It:

1. Loads immutable events in deterministic order (by sequence_number)
2. Replays them sequentially
3. Reconstructs game state at any point in time
4. Emits replay snapshots for the frontend

Design principles:
- Events are the single source of truth
- Never read live game state during replay
- Deterministic: same events → same state, every time
- Stateless: the engine holds no mutable state between calls

Future integration points:
- ML Feature Extraction: feed replay events into feature pipeline
- Spectator Mode: live events stream through the same engine
- Debugging: step through events one at a time, inspect state
- Dataset Export: replay → feature extraction → CSV/Parquet
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.events import repository as event_repository
from app.game_engine import repository as game_repository
from app.users import repository as user_repository
from app.replay.schemas import (
    ReplayEvent,
    ReplayGameInfo,
    ReplayPlayer,
    ReplayStateSnapshot,
    ReplayTimeline,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Event category mapping — determines timeline icon/color
# ---------------------------------------------------------------------------

EVENT_CATEGORIES: dict[str, str] = {
    "game_started": "game_start",
    "role_assigned": "role",
    "round_started": "round_start",
    "message_sent": "message",
    "message_replied": "message",
    "reaction_added": "reaction",
    "reaction_removed": "reaction",
    "mission_assigned": "mission",
    "mission_progress": "mission",
    "mission_completed": "mission",
    "vote_cast": "vote",
    "voting_finished": "vote",
    "phase_changed": "phase",
    "game_over": "game_end",
    "player_joined": "player",
    "player_left": "player",
    "player_ready": "player",
    "discussion_started": "phase",
    "round_ended": "round_end",
}

EVENT_LABELS: dict[str, str] = {
    "game_started": "Game Started",
    "role_assigned": "Role Assigned",
    "round_started": "Round Started",
    "message_sent": "Message",
    "message_replied": "Reply",
    "reaction_added": "Reaction",
    "reaction_removed": "Reaction Removed",
    "mission_assigned": "Mission Assigned",
    "mission_progress": "Mission Progress",
    "mission_completed": "Mission Completed",
    "vote_cast": "Vote Cast",
    "voting_finished": "Voting Finished",
    "phase_changed": "Phase Changed",
    "game_over": "Game Over",
    "player_joined": "Player Joined",
    "player_left": "Player Left",
    "player_ready": "Player Ready",
    "discussion_started": "Discussion Started",
    "round_ended": "Round Ended",
}


# ---------------------------------------------------------------------------
# Replay Engine
# ---------------------------------------------------------------------------

class ReplayEngine:
    """Processes immutable events to reconstruct game history.

    Usage:
        engine = ReplayEngine()
        timeline = await engine.build_timeline(db, game_id=42)
        snapshot = await engine.get_state_at(db, game_id=42, sequence_number=15)
    """

    async def build_timeline(
        self,
        db: AsyncSession,
        game_id: int,
    ) -> ReplayTimeline:
        """Build a complete replay timeline for a game.

        This is the primary entry point for the replay API.
        It loads all events, enriches them with actor names and
        relative timestamps, and returns a structured timeline.
        """
        game = await game_repository.get_by_id(db, game_id)
        if game is None:
            raise ValueError(f"Game {game_id} not found")

        room = None
        from app.rooms import repository as room_repository
        room = await room_repository.get_by_id(db, game.room_id)

        # Load all events in deterministic order
        events = await event_repository.get_game_events(db, game_id)

        # Load players
        game_players = await game_repository.get_game_players(db, game_id)
        player_map: dict[int, ReplayPlayer] = {}
        for gp in game_players:
            user = await user_repository.get_by_id(db, gp.user_id)
            player_map[gp.user_id] = ReplayPlayer(
                user_id=gp.user_id,
                username=user.username if user else str(gp.user_id),
                role=gp.role,
                score=gp.score,
            )

        # Compute relative timestamps
        started_at = None
        if events:
            started_at = events[0].created_at

        replay_events: list[ReplayEvent] = []
        for event in events:
            # Relative time from game start
            relative_time = 0.0
            if started_at and event.created_at:
                delta = event.created_at - started_at
                relative_time = delta.total_seconds()

            actor_name = None
            if event.actor_id and event.actor_id in player_map:
                actor_name = player_map[event.actor_id].username

            category = EVENT_CATEGORIES.get(event.event_type, "other")
            label = EVENT_LABELS.get(event.event_type, event.event_type)

            replay_events.append(ReplayEvent(
                sequence_number=event.sequence_number,
                event_type=event.event_type,
                actor_id=event.actor_id,
                actor_name=actor_name,
                round_number=event.round_number,
                payload=event.payload or {},
                metadata=event.event_metadata or {},
                timestamp=event.created_at,
                relative_time_seconds=relative_time,
                label=label,
                category=category,
            ))

        # Determine winner from game_over event
        winner = None
        reason = None
        for event in events:
            if event.event_type == "game_over":
                winner = (event.payload or {}).get("winner")
                reason = (event.payload or {}).get("reason")
                break

        total_rounds = game.round_number

        duration = 0.0
        if events and len(events) >= 2:
            delta = events[-1].created_at - events[0].created_at
            duration = delta.total_seconds()

        game_info = ReplayGameInfo(
            game_id=game.id,
            room_code=room.code if room else "",
            status=game.status,
            max_rounds=game.max_rounds,
            total_events=len(events),
            started_at=started_at,
            ended_at=events[-1].created_at if events else None,
            players=list(player_map.values()),
            winner=winner,
            reason=reason,
        )

        return ReplayTimeline(
            game=game_info,
            events=replay_events,
            total_events=len(replay_events),
            total_rounds=total_rounds,
            duration_seconds=duration,
        )

    async def get_state_at(
        self,
        db: AsyncSession,
        game_id: int,
        sequence_number: int,
    ) -> ReplayStateSnapshot:
        """Reconstruct game state at a specific sequence number.

        This replays events up to (and including) the given sequence
        number and returns the resulting state. Used for debugging
        and the event inspector.
        """
        events = await event_repository.get_game_events(db, game_id)

        # Filter to events up to the target sequence
        relevant = [e for e in events if e.sequence_number <= sequence_number]

        # Load players
        game_players = await game_repository.get_game_players(db, game_id)

        # Reconstruct state
        phase = "role_assignment"
        round_number = 1
        messages_sent = 0
        votes_cast = 0
        missions_active = 0
        missions_completed = 0

        for event in relevant:
            if event.event_type == "phase_changed":
                phase = (event.payload or {}).get("to_phase", phase)
                round_number = event.round_number or round_number
            elif event.event_type == "round_started":
                round_number = event.round_number or round_number
            elif event.event_type == "message_sent":
                messages_sent += 1
            elif event.event_type == "vote_cast":
                votes_cast += 1
            elif event.event_type == "mission_progress":
                status = (event.payload or {}).get("status", "")
                if status == "completed":
                    missions_completed += 1
                else:
                    missions_active += 1
            elif event.event_type == "game_over":
                phase = "game_over"

        players = []
        for gp in game_players:
            user = await user_repository.get_by_id(db, gp.user_id)
            players.append(ReplayPlayer(
                user_id=gp.user_id,
                username=user.username if user else str(gp.user_id),
                role=gp.role,
                score=gp.score,
            ))

        return ReplayStateSnapshot(
            sequence_number=sequence_number,
            round_number=round_number,
            phase=phase,
            players=players,
            messages_sent=messages_sent,
            votes_cast=votes_cast,
            missions_active=missions_active,
            missions_completed=missions_completed,
        )
