# Secret Signal — Development Roadmap

## Legend

- **`status`** — ✅ = done, ⭐ = now, 🔵 = next, 🟢 = soon, ⚪ = later

---

## Phase 1 — Rooms & Real-Time Connection ✅

> **Goal**: Players can create/join rooms and see each other in real time.

### Backend

| # | Task | status |
|---|------|--------|
| 1.1 | Room SQLAlchemy model (`Room`, `RoomPlayer`) | ✅ |
| 1.2 | Room Pydantic schemas (`RoomResponse`, `CreateRoomRequest`, `JoinRoomRequest`) | ✅ |
| 1.3 | Room repository (get_by_code, create, add_player, remove_player, get_players, etc.) | ✅ |
| 1.4 | Room service (create_room with code generation, join_room with validation, leave_room) | ✅ |
| 1.5 | Room REST router (`POST /rooms`, `POST /rooms/join`, `GET /rooms/{code}`, `POST /rooms/{code}/leave`) | ✅ |
| 1.6 | Alembic migration for rooms + room_players tables | ✅ |
| 1.7 | WebSocket ConnectionManager (connect, disconnect, broadcast_to_room) | ✅ |
| 1.8 | WebSocket authentication (JWT decode + user lookup) | ✅ |
| 1.9 | WebSocket room authorization (membership check) | ✅ |
| 1.10 | `/ws` endpoint with token + room_code query params | ✅ |
| 1.11 | `ROOM_STATE` broadcast on connect/disconnect | ✅ |

### Frontend

| # | Task | status |
|---|------|--------|
| 1.12 | Room TypeScript types | ✅ |
| 1.13 | Room API service (`createRoom`, `joinRoom`, `getRoom`, `leaveRoom`) | ✅ |
| 1.14 | `useWebSocket` hook (auto-connect, JWT auth, ROOM_STATE listener, cleanup) | ✅ |
| 1.15 | `RoomPage.tsx` — player list, room code copy, connection status, leave room, host start | ✅ |
| 1.16 | `LobbyPage.tsx` wired to real backend (create/join with loading + error states) | ✅ |
| 1.17 | `/room/:code` route in router | ✅ |

---

## Phase 2 — Game Engine Core

> **Goal**: A game can start, assign roles, and run through a complete round.

### 2.1 Backend: Game state machine

| # | Task | priority | est |
|---|------|----------|-----|
| 2.1.1 | Create `backend/app/game_engine/models.py` — `Game` model (`id`, `room_id`, `status`, `round_number`, `phase`, `created_at`) | ⭐ | 20m |
| 2.1.2 | Create `backend/app/game_engine/schemas.py` — `GameState`, `RoundState`, `RoleAssignment` | ⭐ | 15m |
| 2.1.3 | Implement `backend/app/game_engine/state_machine.py` — phases enum (`WAITING`, `ROLE_ASSIGNMENT`, `ROUND_START`, `INTERACTION`, `EVALUATION`, `DISCUSSION`, `VOTING`, `RESULT`, `GAME_OVER`) with valid transitions | ⭐ | 30m |
| 2.1.4 | Implement `backend/app/game_engine/service.py` — `start_game`, `assign_roles`, `advance_phase`, `check_win_condition` | ⭐ | 40m |
| 2.1.5 | Create `backend/app/game_engine/router.py` — `POST /games/{room_code}/start` (host only) | ⭐ | 15m |
| 2.1.6 | Add `PLAYER_READY` WebSocket event handler + ready state tracking | 🔵 | 20m |
| 2.1.7 | Wire game start to WebSocket: broadcast `GAME_START` + `ROLE_ASSIGNMENT` events | 🔵 | 20m |
| 2.1.8 | Add `games` + `game_players` table migration | ⭐ | 10m |

### 2.2 Backend: Coordinator missions

| # | Task | priority | est |
|---|------|----------|-----|
| 2.2.1 | Create `backend/app/missions/models.py` — `Mission` model (`id`, `game_id`, `round_number`, `description`, `coordinator_id`, `is_completed`) | 🔵 | 15m |
| 2.2.2 | Create `backend/app/missions/service.py` — `generate_missions`, `check_mission_completion`, `get_mission_progress` | 🔵 | 25m |
| 2.2.3 | Create `backend/app/missions/schemas.py` — `MissionResponse`, `MissionProgress` | 🔵 | 10m |

### 2.3 Frontend: Game page

| # | Task | priority | est |
|---|------|----------|-----|
| 2.3.1 | Create `features/game/pages/GamePage.tsx` — main game UI layout (chat panel, mission display, player list, phase banner) | ⭐ | 1h |
| 2.3.2 | Create `features/game/components/PhaseBanner.tsx` — shows current phase with animation | 🔵 | 20m |
| 2.3.3 | Create `features/game/components/RoleReveal.tsx` — role card shown at game start | 🔵 | 15m |
| 2.3.4 | Create `features/game/components/MissionDisplay.tsx` — shows coordinator's secret mission (only to coordinator) | 🔵 | 15m |
| 2.3.5 | Add `/game/:roomCode` route to `router.tsx` | ⭐ | 5m |
| 2.3.6 | Connect `RoomPage.tsx` "START GAME" button to `POST /games/{code}/start` | ⭐ | 10m |

---

## Phase 3 — Chat & Interaction

> **Goal**: Players can send and reply to messages in real time.

### 3.1 Backend: Chat

| # | Task | priority | est |
|---|------|----------|-----|
| 3.1.1 | Create `backend/app/chat/models.py` — `Message` model (`id`, `game_id`, `room_id`, `sender_id`, `parent_id`, `content`, `created_at`), `Reaction` model | 🔵 | 20m |
| 3.1.2 | Implement WS handlers for `SEND_MESSAGE`, `REPLY_TO_MESSAGE`, `ADD_REACTION` | 🔵 | 25m |
| 3.1.3 | Implement server events `NEW_MESSAGE`, `NEW_REPLY`, `NEW_REACTION` | 🔵 | 15m |

### 3.2 Frontend: Chat UI

| # | Task | priority | est |
|---|------|----------|-----|
| 3.2.1 | Create `features/chat/components/ChatPanel.tsx` — message list, reply threading, reactions | 🔵 | 45m |
| 3.2.2 | Create `features/chat/components/MessageInput.tsx` — send + reply-to UI | 🔵 | 20m |
| 3.2.3 | Create `features/chat/components/MessageBubble.tsx` — styled message with reply chain | 🔵 | 15m |

---

## Phase 4 — Voting & Accusations

> **Goal**: Players can vote and the coordinator can be accused.

### 4.1 Backend: Voting

| # | Task | priority | est |
|---|------|----------|-----|
| 4.1.1 | Create `backend/app/voting/models.py` — `Vote` model, `Accusation` model | 🟢 | 15m |
| 4.1.2 | Implement WS handler for `CAST_VOTE` during voting phase | 🟢 | 15m |
| 4.1.3 | Implement WS handler for `SUBMIT_ACCUSATION` during evaluation phase | 🟢 | 15m |
| 4.1.4 | Implement tally logic — `count_votes`, `resolve_accusation` | 🟢 | 20m |

### 4.2 Frontend: Voting UI

| # | Task | priority | est |
|---|------|----------|-----|
| 4.2.1 | Create `features/voting/components/VotePanel.tsx` — list players to vote for | 🟢 | 25m |
| 4.2.2 | Create `features/voting/components/AccusationPanel.tsx` — coordinator accusation form | 🟢 | 20m |
| 4.2.3 | Create `features/voting/components/ResultsReveal.tsx` — vote tally reveal animation | 🟢 | 20m |

---

## Phase 5 — Scoring & Game End

> **Goal**: Games end with a winner and score summary.

| # | Task | priority | est |
|---|------|----------|-----|
| 5.1 | Implement scoring logic — coordinator points vs. detective/citizen points | 🟢 | 20m |
| 5.2 | Implement `GAME_OVER` phase — broadcast results, award XP/score | 🟢 | 15m |
| 5.3 | Create `features/game/components/GameOverScreen.tsx` — winner reveal, stats, play-again button | 🟢 | 30m |

---

## Phase 6 — Testing & Polish

> **Goal**: Confidence that everything works.

| # | Task | priority | est |
|---|------|----------|-----|
| 6.1 | Write backend unit tests for auth (signup, login, edge cases) | ⚪ | 30m |
| 6.2 | Write backend unit tests for rooms (create, join, leave, duplicates) | ⚪ | 20m |
| 6.3 | Write backend unit tests for game engine (state transitions, role assignment, win conditions) | ⚪ | 40m |
| 6.4 | Write backend integration tests for auth + rooms (API-level tests) | ⚪ | 30m |
| 6.5 | Set up frontend test framework (Vitest + React Testing Library) | ⚪ | 15m |
| 6.6 | Write frontend tests for room flow | ⚪ | 30m |
| 6.7 | End-to-end flow test: signup → create room → join room → start game | ⚪ | 20m |

---

## Phase 7 — Deferred (future)

| # | Task | priority |
|---|------|----------|
| 7.1 | ML suspicion scoring model | ⚪ |
| 7.2 | AI analysis + metrics dashboard | ⚪ |
| 7.3 | Docker optimization (multi-stage builds) | ⚪ |
| 7.4 | Production deployment (K8s manifests) | ⚪ |
| 7.5 | Monitoring (logs, metrics, alerts) | ⚪ |
| 7.6 | Analytics pipeline | ⚪ |
| 7.7 | Remember me / refresh token rotation | ⚪ |
| 7.8 | Rate limiting | ⚪ |

---

## Immediate Next Steps

```
Game Engine (backend):
  1. Game model + game_players table + migration    (2.1.1, 2.1.8)
  2. Phase state machine                              (2.1.3)
  3. start_game + assign_roles service                (2.1.4)
  4. POST /games/{room_code}/start endpoint           (2.1.5)
  5. PLAYER_READY WS event                            (2.1.6)
  6. GAME_START WS broadcast                          (2.1.7)

Frontend:
  7. GamePage + route + role reveal + phase banner   (2.3.1–2.3.5)
  8. Wire "START GAME" button in RoomPage             (2.3.6)
```

After this, a player can: create room → invite → ready up → host starts game → roles are assigned → game UI appears. Chat and voting build on that foundation.
