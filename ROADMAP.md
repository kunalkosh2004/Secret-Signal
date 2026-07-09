# Secret Signal — Development Roadmap

## Legend

- **`status`** — ✅ = done, ⭐ = now, 🔵 = next, 🟢 = soon, ⚪ = later

---

## Phase 1 — Rooms & Real-Time Connection ✅

> **Goal**: Players can create/join rooms and see each other in real time.

| # | Task | status |
|---|------|--------|
| 1.1 | Room SQLAlchemy model (`Room`, `RoomPlayer`) | ✅ |
| 1.2 | Room Pydantic schemas | ✅ |
| 1.3 | Room repository | ✅ |
| 1.4 | Room service (create, join, leave) | ✅ |
| 1.5 | Room REST router (`POST /rooms`, `POST /rooms/join`, `GET /rooms/{code}`, `POST /rooms/{code}/leave`) | ✅ |
| 1.6 | Alembic migration for rooms + room_players | ✅ |
| 1.7 | WebSocket ConnectionManager | ✅ |
| 1.8 | WebSocket authentication + room authorization | ✅ |
| 1.9 | `/ws` endpoint | ✅ |
| 1.10 | `ROOM_STATE` broadcast on connect/disconnect | ✅ |
| 1.11 | Room TypeScript types + API service | ✅ |
| 1.12 | `useWebSocket` hook (all events: ROOM_STATE, GAME_START, ROLE_ASSIGNMENT, PHASE_CHANGED, GAME_STATE) | ✅ |
| 1.13 | `RoomPage.tsx` — player list, room code, leave, host start, ready toggle | ✅ |
| 1.14 | `LobbyPage.tsx` wired to real backend | ✅ |
| 1.15 | `/room/:code` route | ✅ |

---

## Phase 2 — Game Engine Core

> **Goal**: A game can start, assign roles, and run through a complete round.

### 2.1 Backend: Game state machine

| # | Task | status |
|---|------|--------|
| 2.1.1 | `Game` + `GamePlayer` models | ✅ |
| 2.1.2 | Game schemas | ✅ |
| 2.1.3 | Phase state machine (`GamePhase`, `VALID_TRANSITIONS`, `can_transition`) | ✅ |
| 2.1.4 | `start_game()` + `assign_roles()` + `advance_phase()` | ✅ |
| 2.1.5 | `POST /games/{room_code}/start` endpoint | ✅ |
| 2.1.6 | `PLAYER_READY` WebSocket event | ✅ |
| 2.1.7 | `GAME_START` + `ROLE_ASSIGNMENT` WebSocket events | ✅ |
| 2.1.8 | Game migrations | ✅ |
| 2.1.9 | `PHASE_CHANGED` WebSocket event | ✅ |
| 2.1.10 | Host-only phase advance endpoint | ✅ |
| 2.1.11 | Active-game reconnect recovery | ✅ |
| 2.1.12 | `check_win_condition()` | 🔵 |

> **Note**: `check_win_condition()` needs design decisions (how Coordinator wins, how Detective wins, max rounds, score thresholds, mission/voting impact).

### 2.2 Backend: Missions

| # | Task | status |
|---|------|--------|
| 2.2.1 | Mission model | 🔵 |
| 2.2.2 | Mission schemas | 🔵 |
| 2.2.3 | Mission service (`generate_missions`, `check_mission_completion`) | 🔵 |
| 2.2.4 | Mission WS integration | 🔵 |

### 2.3 Frontend: Game page

| # | Task | status |
|---|------|--------|
| 2.3.1 | `GamePage.tsx` — main game UI with phase-aware content, WS event handling, reconnect | ✅ |
| 2.3.2 | `PhaseBanner.tsx` — animated phase display with color coding per phase | ✅ |
| 2.3.3 | `RoleReveal.tsx` — animated card-flip reveal with role description | ✅ |
| 2.3.4 | `/game/:code` route | ✅ |
| 2.3.5 | Ready toggle in RoomPage + `PLAYER_READY` WS integration | ✅ |
| 2.3.6 | GAME_START → auto-navigate from RoomPage to GamePage | ✅ |

### 2.4 Animations

| # | Task | status |
|---|------|--------|
| 2.4.1 | Fade-in, fade-in-up, slide-down, scale-in for page content | ✅ |
| 2.4.2 | Pulse-dot for connection status | ✅ |
| 2.4.3 | Role-reveal card flip (3D rotateY) | ✅ |
| 2.4.4 | Phase-enter slide animation | ✅ |
| 2.4.5 | Shake animation for errors | ✅ |
| 2.4.6 | Pulse-glow for accent buttons | ✅ |
| 2.4.7 | Staggered player list entries | ✅ |

---

## Phase 3 — Chat & Interaction

> **Goal**: Players can send and reply to messages in real time.

### 3.1 Backend: Chat

| # | Task | status |
|---|------|--------|
| 3.1.1 | Message model (`Message` with room_id, user_id, content, created_at) | ✅ |
| 3.1.2 | Chat schemas + repository (`create_message`, `get_room_messages`) | ✅ |
| 3.1.3 | `SEND_MESSAGE` WebSocket handler + `MESSAGE_SENT` broadcast | ✅ |
| 3.1.4 | `GET /api/v1/rooms/{code}/messages` — chat history endpoint | ✅ |
| 3.1.5 | Chat message model migration | 🔵 |
| 3.1.6 | `REPLY_TO_MESSAGE` + `ADD_REACTION` WS handlers | 🟢 |

### 3.2 Frontend: Chat UI

| # | Task | status |
|---|------|--------|
| 3.2.1 | Chat types (`ChatMessage`, `MESSAGE_SENT` event) | ✅ |
| 3.2.2 | `ChatPanel.tsx` — message list + send input, wired into GamePage | ✅ |
| 3.2.3 | Reply-to threading + reaction UI | 🟢 |

---

## Phase 4 — Voting & Accusations

> **Goal**: Players can vote and the coordinator can be accused.

### 4.1 Backend: Voting

| # | Task | status |
|---|------|--------|
| 4.1.1 | Vote + Accusation models | 🟢 |
| 4.1.2 | WS handler: `CAST_VOTE` | 🟢 |
| 4.1.3 | WS handler: `SUBMIT_ACCUSATION` | 🟢 |
| 4.1.4 | Tally logic (`count_votes`, `resolve_accusation`) | 🟢 |

### 4.2 Frontend: Voting UI

| # | Task | status |
|---|------|--------|
| 4.2.1 | `VotePanel.tsx` — vote for player | 🟢 |
| 4.2.2 | `AccusationPanel.tsx` — coordinator accusation | 🟢 |
| 4.2.3 | `ResultsReveal.tsx` — vote tally reveal animation | 🟢 |

---

## Phase 5 — Scoring & Game End

> **Goal**: Games end with a winner and score summary.

| # | Task | status |
|---|------|--------|
| 5.1 | Scoring logic — coordinator vs detective/citizen points | 🟢 |
| 5.2 | `GAME_OVER` phase — broadcast results | 🟢 |
| 5.3 | `GameOverScreen.tsx` — winner reveal, stats, play-again | 🟢 |

---

## Phase 6 — Testing

| # | Task | status |
|---|------|--------|
| 6.1 | Backend unit tests: auth, rooms, game engine | ⚪ |
| 6.2 | Backend integration tests | ⚪ |
| 6.3 | Frontend tests: room flow, game page | ⚪ |
| 6.4 | E2E: signup → create room → join → ready → start → play | ⚪ |

---

## Phase 7 — Deferred

| # | Task | status |
|---|------|--------|
| 7.1 | ML suspicion scoring model | ⚪ |
| 7.2 | AI analysis dashboard | ⚪ |
| 7.3 | Docker optimization | ⚪ |
| 7.4 | Production deployment (K8s) | ⚪ |
| 7.5 | Monitoring | ⚪ |
| 7.6 | Refresh tokens | ⚪ |
| 7.7 | Rate limiting | ⚪ |

---

## Immediate Next Steps

```
1. Wire up START GAME button in RoomPage  (2.3 — REST call to POST /games/{code}/start)
2. Missions backend                       (2.2 — models, generate, evaluate)
3. check_win_condition()                  (2.1.12 — needs design decisions)
4. Chat model migration + reply/react     (3.1.5-3.1.6)
5. Voting backend + frontend              (Phase 4)
6. Scoring + game over                    (Phase 5)
```

Currently: rooms work with real-time ready sync, chat is functional, game can be started via REST API, roles assigned, phases advanced. Next is wiring the START GAME button and building the mission system.
