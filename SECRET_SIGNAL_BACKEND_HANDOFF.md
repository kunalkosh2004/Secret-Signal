# Secret Signal Backend --- Development Handoff

## Purpose

This document summarizes the backend work completed so far for Secret
Signal, especially the game engine, mission system, WebSocket
integration, win conditions, and remaining work.

## Current Backend Architecture

The backend uses FastAPI, PostgreSQL, async SQLAlchemy sessions,
Alembic, Redis, JWT authentication, and WebSockets.

Main modules involved:

    app/
    ├── auth/
    ├── users/
    ├── rooms/
    ├── game_engine/
    ├── missions/
    ├── chat/
    └── websocket/

## Work Completed

### Auth and Users

- JWT-based registration, login, and token refresh.
- Google OAuth sign-in with auth identities table.
- `/me` endpoint for session validation.

### Room system

- Room + RoomPlayer models, schemas, repository, service, REST router.
- Create, join, leave room endpoints.
- Player ready state (is_ready column on room_players).
- Room lifecycle: waiting → in_game → completed.

### WebSocket infrastructure

- ConnectionManager with per-room, per-user WebSocket tracking.
- JWT-based WebSocket authentication + room membership authorization.
- Dead-connection handling: broadcast_to_room and send_to_user catch
  exceptions per-connection and clean up stale sockets instead of
  crashing the entire broadcast.
- Reconnect recovery: on WS connect, sends GAME_STATE + ROLE_ASSIGNMENT
  + current-round MISSION_ASSIGNMENT (Coordinator only).

### WebSocket events

Public room events:
- ROOM_STATE
- GAME_START
- PHASE_CHANGED
- MESSAGE_SENT
- GAME_OVER
- ERROR

Private player events:
- ROLE_ASSIGNMENT

Private Coordinator events:
- MISSION_ASSIGNMENT
- MISSION_PROGRESS

### Game engine

- Game + GamePlayer models with phase, round_number, score tracking.
- Phase state machine with valid transitions:
  WAITING → ROLE_ASSIGNMENT → ROUND_START → INTERACTION → EVALUATION
  → DISCUSSION → VOTING → RESULT → (ROUND_START | GAME_OVER)
- `assign_roles()`: random assignment of coordinator, detective, citizens.
- `start_game()`: creates Game + GamePlayer rows + Coordinator missions,
  sets room.status = in_game, commit in single transaction.
- `advance_phase()`: validates transitions, increments round on
  RESULT→ROUND_START, generates new-round missions, blocks after
  MAX_ROUNDS=5, rejects completed games.
- `POST /games/{room_code}/start` REST endpoint.
- `POST /games/{game_id}/advance-phase` REST endpoint.
- `PLAYER_READY` WS handler with room.status == "waiting" guard.
- `check_win_condition()` called from:
  - `advance_phase()` when entering RESULT phase.
  - SEND_MESSAGE handler when a mission completes.

### Mission system

- Mission model with game_id, assigned_to_user_id, mission_type, title,
  description, target_value, current_value, status, round_number,
  created_at, completed_at.
- Repository: create, get_by_id, get_game_missions, get_user_missions,
  get_active_mission_by_type, count_completed_missions,
  update_mission_progress.
- `generate_missions()`: idempotent per game+round (returns existing if
  already generated), uses flush (caller owns commit).
- `increment_mission_progress()`: caps at target_value, auto-completes
  when target reached, returns updated mission or None.
- `check_mission_completion()`: standalone completion check.
- `get_mission_progress()`: returns progress for all missions in a round.

Current mission templates:
- `send_messages`: "Send 5 messages during the interaction phase."
  (Temporary — only send_messages is measurable with current Message
  model. No reply, recipient, or interaction tracking yet.)

Win conditions:
- Coordinator wins after 5 completed missions total.
- Investigation Team wins when round 5 reaches RESULT and Coordinator
  has < 5 completed missions.
- Game-over: game.status = completed, game.phase = game_over,
  room.status = completed, GAME_OVER broadcast with winner + reason.

### Chat system

- Message model with room_id, user_id, content, created_at.
- Repository: create_message (flush not commit), get_room_messages.
- REST endpoint: GET /api/v1/rooms/{code}/messages (auth + membership).
- SEND_MESSAGE WS handler with:
  - Non-empty content validation.
  - Completed-game rejection (rollback if already flushed).
  - Mission progress integration (increment send_messages for
    Coordinator).
  - Win condition check on mission completion.
  - Private MISSION_PROGRESS event to Coordinator.
  - Broadcast MESSAGE_SENT to room.
  - Game-over handling: if win condition met, sets game + room status,
    broadcasts GAME_OVER.
  - Transaction rollback on failure.

### Post-game guards

- SEND_MESSAGE rejected after game completion.
- advance_phase() rejects completed games.
- PLAYER_READY rejected when room.status != "waiting".

## Migration Status

Current Alembic migrations:

    08bd7494cde1 — Initial users table
    61b930199a5d — Add auth identities table
    1d0aff38d16f — Update auth identity fields
    6b8b0e6b6de3 — Add rooms and room_players tables
    0f1543e7d899 — Add ready state to room_players
    ddb29766c614 — Add missions table
    89a683953033 — Migrate missions to new structure
    3f29ac731b68 — Add messages table (chat)              ← current head

Note: branches 83d303602384 / 1fa1609502dd were created locally but
never applied to the database; they are not ancestors of the current head.
The real chain goes through 0f1543e7d899 → ddb29766c614 → 89a683953033
→ 3f29ac731b68.

## Important Design Decisions Already Made

- Mission information is private to the Coordinator.
- Role information is private per player.
- Mission generation participates in caller-owned transactions.
- Repository writes should generally flush rather than independently
  commit when part of larger workflows.
- Missions are scoped by round.
- Mission generation is idempotent per game and round.
- Only measurable mission types should be generated.
- Current mission generation is one send_messages mission per round.
- Coordinator victory target is 5 completed missions total.
- Maximum rounds is 5.
- If round 5 ends without the Coordinator mission target, the
  Investigation Team wins.
- Completed games reject chat and phase advancement.
- Terminal room state is completed, not waiting.
- Replay behavior is intentionally deferred.
- broadcast_to_room is resilient to individual dead WebSocket
  connections (try/except per socket, dead cleanup after loop).

## What Needs To Be Done Next

### Immediate

1.  Phase-specific SEND_MESSAGE validation — only allow during intended
    interaction phases (e.g. INTERACTION, DISCUSSION).
2.  Handle GAME_OVER in reconnect recovery for completed games.

### Voting system

A full voting system remains to be implemented:
1.  Voting model (cast_votes or similar).
2.  Alembic migration.
3.  Voting repository.
4.  Voting service.
5.  Vote submission WS event.
6.  Duplicate-vote prevention.
7.  Phase restrictions (VOTING phase only).
8.  Vote tallying.
9.  Coordinator identification result.
10. Win-condition integration for correct identification.

This is one of the largest remaining gameplay systems.

### Scoring

A complete scoring system needs rules and implementation. Possible work
includes score events, score history, mission rewards, Investigation
Team rewards, penalties, final score calculation, and leaderboard
delivery.

### Mission system expansion

The current backend supports only send_messages missions. To restore
receive_replies and unique_interactions, add measurable interaction data
such as reply_to_message_id, recipient_user_id, mentions, reactions, or
a dedicated interaction event model.

Then add repository queries, progress handlers, mission templates,
balanced targets, and potentially weighted or phase-specific mission
selection.

### Phase-specific action validation

The state machine validates phase transitions, but player actions also
need phase restrictions. Examples:

    SEND_MESSAGE → only in intended interaction phases
    VOTE → only in voting phase
    MISSION progress → only when mission rules permit

A centralized action/phase validation layer may be useful.

### Reconnect recovery improvements

Current recovery restores game state, role, and current Coordinator
missions.

Future recovery should consider recent chat history, timer state, voting
state, vote eligibility, completed-game state, and final winner/reason.

### Timers and automatic phase progression

If rounds are timed, implement server-authoritative phase deadlines,
Redis-backed or durable timer state, automatic transitions,
reconnect-safe remaining time, timer events, and expiry handling.

### Replay / Play Again

Replay is not implemented. Decide whether replay creates a new Game for
the same Room or creates a new Room. If reusing a Room, review
get_by_room_id() assumptions and any game uniqueness constraints.

### Automated testing

Add automated tests for mission generation, mission idempotency,
progress, completion, round scoping, privacy, reconnect recovery, both
victory paths, maximum rounds, post-game guards, ready-state guards,
authorization, transaction rollback, and concurrent mission updates.

## Recommended Development Order

    1. Alembic merge migration + messages table migration     ← NOW
    2. phase-specific SEND_MESSAGE validation
    3. reconnect GAME_OVER recovery
    4. automated tests for current game and mission system
    5. voting system design
    6. voting database model and migration
    7. voting repository and service
    8. voting WS events
    9. correct-identification win condition
    10. scoring system
    11. timers and automatic phase progression
    12. richer chat interactions (reply, reactions, mentions)
    13. additional mission types
    14. replay / play-again flow
    15. frontend integration polish
