# Secret Signal Backend --- Development Progress

## Overview

This document summarizes the backend work completed so far for **Secret
Signal**.

The backend currently supports authentication, PostgreSQL persistence,
room management, authenticated WebSockets, real-time room state, player
readiness, game creation, role assignment, game start, phase
transitions, phase broadcasts, and active-game reconnect recovery.

The current roadmap position is near the end of **Phase 2.1 --- Backend
Game State Machine**.

------------------------------------------------------------------------

## 1. Backend Foundation

### Technology stack

-   FastAPI
-   PostgreSQL
-   SQLAlchemy AsyncSession
-   Alembic
-   Pydantic
-   JWT authentication
-   WebSockets
-   Docker Compose
-   Redis container prepared for later use

Typical development server command:

``` bash
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --reload-exclude '.venv/**'
```

The `.venv` exclusion prevents WatchFiles from repeatedly restarting the
server because of changes detected inside installed packages.

------------------------------------------------------------------------

## 2. Authentication System

Completed work includes:

-   User model
-   AuthIdentity model
-   Signup flow
-   Login flow
-   Password hashing
-   JWT access-token creation and decoding
-   Protected FastAPI routes
-   `get_current_user` dependency
-   Google authentication dependency/setup work

Protected HTTP routes use the authenticated user dependency. WebSocket
authentication validates the JWT during connection setup, extracts the
user ID, loads the user, and then verifies room membership.

------------------------------------------------------------------------

## 3. Database and Infrastructure

Docker Compose is used for PostgreSQL and Redis.

Containers:

``` text
secret_signal_postgres
secret_signal_redis
```

PostgreSQL was tested directly with `psql`, and Alembic is used for
schema migrations.

Models registered with Alembic include:

-   User
-   AuthIdentity
-   Room
-   RoomPlayer
-   Game
-   GamePlayer

------------------------------------------------------------------------

## 4. Room System

### Room model

The Room model contains:

-   `id`
-   `code`
-   `host_id`
-   `status`
-   `max_players`
-   `settings`
-   `created_at`

Room codes are secure random six-character uppercase alphanumeric
values.

### RoomPlayer model

The RoomPlayer model stores:

-   `id`
-   `room_id`
-   `user_id`
-   `joined_at`
-   `is_ready`

A unique constraint prevents duplicate membership for the same user and
room.

### Room repository

Implemented repository functions include:

-   `get_by_code`
-   `get_by_id`
-   `create`
-   `add_player`
-   `remove_player`
-   `get_player`
-   `count_players`
-   `get_players`
-   `get_players_with_ready_state`
-   `set_player_ready`

### Room service

Create-room logic generates a unique room code, creates the room, and
automatically adds the host.

Join-room logic checks that the room exists, is waiting, is not full,
and that the user is not already a member.

Leave-room logic checks membership and prevents the host from leaving
through the normal player-leave path.

### Room REST API

Implemented routes:

``` text
POST /api/v1/rooms
POST /api/v1/rooms/join
GET  /api/v1/rooms/{code}
POST /api/v1/rooms/{code}/leave
```

------------------------------------------------------------------------

## 5. WebSocket Room System

The WebSocket system is centered around:

``` text
app/websocket/manager.py
app/websocket/handlers.py
```

The connection manager tracks sockets by room code and user ID, supports
room broadcasts, and supports private messages to individual users.

Connection flow:

``` text
Client connects with token and room_code
        ↓
JWT is decoded
        ↓
User is loaded
        ↓
Room membership is verified
        ↓
Connection is accepted
```

The backend broadcasts authoritative `ROOM_STATE` events containing room
details and player readiness.

------------------------------------------------------------------------

## 6. PLAYER_READY --- Roadmap 2.1.6

The `PLAYER_READY` feature is implemented and tested.

Client event:

``` json
{
  "type": "PLAYER_READY",
  "payload": {
    "ready": true
  }
}
```

Flow:

``` text
Receive PLAYER_READY
        ↓
Validate payload.ready is boolean
        ↓
Load room
        ↓
Update RoomPlayer.is_ready
        ↓
Commit database change
        ↓
Broadcast ROOM_STATE
```

If a player disconnects while the room is still waiting, readiness
resets to `false`.

Testing confirmed:

-   `ready=true` is persisted.
-   Updated `ROOM_STATE` is broadcast.
-   Disconnect from a waiting room resets readiness to `false`.

**Roadmap item 2.1.6 is complete.**

------------------------------------------------------------------------

## 7. Game Engine Models --- Roadmap 2.1.1

### Game model

Fields:

-   `id`
-   `room_id`
-   `status`
-   `round_number`
-   `phase`
-   `created_at`

Initial state:

``` text
status = active
round_number = 1
phase = role_assignment
```

### GamePlayer model

Fields:

-   `id`
-   `game_id`
-   `user_id`
-   `role`
-   `score`
-   `joined_at`

A unique constraint prevents duplicate users in the same game.

------------------------------------------------------------------------

## 8. Game Repository

Implemented functions:

-   `get_by_room_id`
-   `get_by_id`
-   `create_game`
-   `add_game_player`
-   `get_game_players`
-   `get_game_player`

Game creation uses `flush()` so the service can create the game, create
all GamePlayer rows, update the room status, and commit the complete
operation as one transaction.

------------------------------------------------------------------------

## 9. Role Assignment --- Roadmap 2.1.4

`assign_roles()` is implemented.

Minimum players:

``` text
3
```

Current distribution:

``` text
1 Coordinator
1 Detective
Remaining players → Citizens
```

The user list is copied and shuffled before roles are assigned.

------------------------------------------------------------------------

## 10. Start Game Flow

`start_game()` validates:

1.  The room exists.
2.  The requester is the room host.
3.  The room is in `waiting`.
4.  No game already exists for the room.
5.  Enough players exist for role assignment.

Then it:

``` text
loads room players
        ↓
assigns roles
        ↓
creates Game
        ↓
creates GamePlayer rows
        ↓
changes room.status to in_game
        ↓
commits transaction
```

Endpoint:

``` text
POST /api/v1/games/{room_code}/start
```

Only the host can start the game.

------------------------------------------------------------------------

## 11. GAME_START and ROLE_ASSIGNMENT

When a game starts, clients receive a public `GAME_START` event.

Each player's role is sent privately with `ROLE_ASSIGNMENT`.

Example private event:

``` json
{
  "type": "ROLE_ASSIGNMENT",
  "game_id": 1,
  "role": "detective"
}
```

Roles are not broadcast publicly.

------------------------------------------------------------------------

## 12. Game State Machine --- Roadmap 2.1.3

Current phases:

``` text
WAITING
    ↓
ROLE_ASSIGNMENT
    ↓
ROUND_START
    ↓
INTERACTION
    ↓
EVALUATION
    ↓
DISCUSSION
    ↓
VOTING
    ↓
RESULT
    ↓
ROUND_START or GAME_OVER
```

The state machine uses `GamePhase`, `VALID_TRANSITIONS`,
`can_transition()`, and `validate_transition()`.

Invalid phase jumps are rejected.

------------------------------------------------------------------------

## 13. Phase Advancement --- Roadmap 2.1.4

`advance_phase()` is implemented.

It:

1.  Loads the game.
2.  Converts the stored phase to `GamePhase`.
3.  Validates the requested transition.
4.  Updates the phase.
5.  Increments `round_number` for `RESULT → ROUND_START`.
6.  Marks the game completed when entering `GAME_OVER`.
7.  Commits the change.

------------------------------------------------------------------------

## 14. Host-Only Phase Advancement API

Endpoint:

``` text
POST /api/v1/games/{game_id}/advance-phase
```

Flow:

``` text
JWT authentication
        ↓
Game lookup
        ↓
Room lookup
        ↓
Host authorization
        ↓
State-machine validation
        ↓
Database update
        ↓
PHASE_CHANGED broadcast
```

Host requests work, while non-host requests return `403 Forbidden`. This
authorization behavior was tested.

------------------------------------------------------------------------

## 15. PHASE_CHANGED WebSocket Event

After a successful phase update, connected room clients receive a
`PHASE_CHANGED` event containing game ID, status, round number, and
phase.

The complete REST → service → PostgreSQL → WebSocket pipeline was tested
successfully.

------------------------------------------------------------------------

## 16. Active-Game Reconnect Recovery

Reconnect recovery is implemented and tested.

When a player reconnects to a room already in a game, the backend
restores:

-   `ROOM_STATE`
-   `GAME_STATE`
-   The reconnecting player's private `ROLE_ASSIGNMENT`

This ensures a reconnecting player can rebuild the game UI without
exposing other players' roles.

------------------------------------------------------------------------

## 17. Testing Completed

Completed tests include:

-   Multi-player WebSocket connections
-   Room-state synchronization
-   Game start
-   Private role delivery
-   Active-game reconnect recovery
-   Valid phase transition
-   Invalid phase transition rejection
-   Host-only phase advancement
-   Non-host `403` rejection
-   `PHASE_CHANGED` WebSocket delivery
-   `PLAYER_READY`
-   Ready reset after disconnect

------------------------------------------------------------------------

## 18. Current Roadmap Status

### Phase 1 --- Room System

**Status: Complete for the backend foundation used by the current
game-engine work.**

### Phase 2.1 --- Backend Game State Machine

  Task                                 Status
  ------------------------------------ ---------------------
  2.1.1 Game + GamePlayer models       Complete
  2.1.2 Game schemas                   Complete
  2.1.3 Phase state machine            Complete
  2.1.4 `start_game()`                 Complete
  2.1.4 `assign_roles()`               Complete
  2.1.4 `advance_phase()`              Complete
  2.1.4 `check_win_condition()`        Pending
  2.1.5 Start-game endpoint            Complete
  2.1.6 PLAYER_READY                   Complete and tested
  2.1.7 GAME_START + ROLE_ASSIGNMENT   Complete
  2.1.8 Game migrations                Complete

The main unfinished part of Phase 2.1 is:

``` text
check_win_condition()
```

The exact win-condition rules must be defined before implementation.
Current code does not yet contain mission results, voting results, or a
defined score/round threshold, so arbitrary victory rules should not be
invented.

------------------------------------------------------------------------

## 19. Immediate Next Work

The immediate next task is:

``` text
Phase 2.1.4
└── check_win_condition()
```

Before implementation, define:

-   How the Coordinator wins
-   How the Detective wins
-   Whether Citizens share a team result
-   How mission completion affects victory
-   How voting affects victory
-   Whether there is a fixed maximum number of rounds
-   Whether score thresholds determine the winner

After Phase 2.1 is complete, continue with:

``` text
Phase 2.2 — Coordinator Missions
        ↓
Mission model
Mission schemas
Mission service
Mission generation
Mission completion checking
Mission progress
```

Then:

``` text
Phase 2.3 — Frontend Game Page
```

followed by:

``` text
Phase 3 — Chat and Interaction
```

------------------------------------------------------------------------

## 20. Architecture Established

### Router layer

Responsible for HTTP input/output, dependency injection, HTTP status
codes, and mapping service errors to responses.

### Service layer

Responsible for business rules, role assignment, game-start
orchestration, phase progression, and future win-condition logic.

### Repository layer

Responsible for SQLAlchemy queries and persistence.

### WebSocket handler layer

Responsible for real-time event validation, invoking backend behavior,
and broadcasting authoritative state.

### Connection manager

Responsible for active socket tracking, room broadcasts, and private
per-user messages.

This separation should be maintained while missions, voting, chat, and
scoring are added.

------------------------------------------------------------------------

## 21. Current High-Level Flow

``` text
Authentication
      ↓
Room creation / join
      ↓
Authenticated WebSocket connection
      ↓
ROOM_STATE synchronization
      ↓
PLAYER_READY updates
      ↓
Host starts game
      ↓
Game + GamePlayers created
      ↓
Roles assigned
      ↓
GAME_START broadcast
      ↓
Private ROLE_ASSIGNMENT
      ↓
Game phase state machine
      ↓
Host advances phase
      ↓
PHASE_CHANGED broadcast
      ↓
Reconnect recovery
      ↓
Next: define and implement check_win_condition()
```

------------------------------------------------------------------------

## Summary

The Secret Signal backend now has a strong multiplayer foundation:
authentication, room lifecycle, authenticated real-time connections,
readiness tracking, game creation, role assignment, game start, private
role events, state-machine validation, host-only phase progression,
real-time phase broadcasts, and reconnect recovery.

The immediate focus is to finish roadmap item **2.1.4** by defining and
implementing `check_win_condition()`. After that, development can move
into **Phase 2.2 --- Coordinator Missions**.
