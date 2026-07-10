# Secret Signal — Project Status & Next Steps

A detailed walkthrough of what this project is, how it works, what's been built, and what comes next.

---

## What We Are Building

Secret Signal is a real-time multiplayer social deduction game for 4–8 players. Unlike traditional social deduction games based on elimination (like Mafia or Werewolf), this game focuses on **social influence and behavioral manipulation**.

### The Core Idea

One player secretly becomes the **Coordinator**. The Coordinator receives hidden missions each round — things like "make three players mention a country" or "get someone to change their opinion." The Coordinator must manipulate the conversation to complete these missions without being caught.

Meanwhile, a **Detective** and **Citizens** are trying to figure out who the Coordinator is. The Detective has limited investigation abilities. Citizens also have their own small secret objectives (like "make someone disagree with you"), which makes everyone look a little suspicious — making the real Coordinator harder to find.

### The Roles

**Coordinator** — The hidden antagonist. Receives secret missions each round. Earns points by completing missions and surviving incorrect accusations. Must influence conversations naturally without revealing their identity.

**Detective** — The primary investigator. Has limited special abilities (e.g., checking whether the Coordinator is among a group of players, viewing behavioral hints). Must use abilities strategically to narrow down suspects.

**Citizens** — Everyone else. Each gets a small private objective each round (e.g., "get 2 reactions on your messages"). These objectives make citizens act somewhat suspiciously, creating cover for the Coordinator.

### How a Game Plays Out

1. Players join a private room (4–8 players)
2. Each player receives a hidden role
3. A public conversation prompt is shown (e.g., "You receive ₹10 crore but must live in one city forever. Which city?")
4. Players chat in real-time, secretly trying to complete their objectives
5. After a set time, the interaction phase ends
6. Players discuss and analyze behavior — who changed topics, who asked leading questions, who seemed to influence others
7. Players vote to accuse someone or skip
8. Wrong accusations reward the Coordinator team. Correct ones reward the Investigator team
9. Scores update, next round begins (4 rounds total)
10. Final scores, all roles, missions, and voting history are revealed

---



## How the System Works



### Architecture Overview

```
                    React + TypeScript (Vite)
                            │
                  REST API + WebSocket
                            │
                      FastAPI Backend
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
      Game Engine         Redis          PostgreSQL
          │
          │
     Domain Events
          │
          ▼
    Analytics Pipeline
          │
          ▼
     ML Feature Store
          │
          ▼
      ML Training
          │
          ▼
    Inference Service
```

The backend is the **authoritative source of game state**. Clients never store or compute game logic — they send intentions through WebSocket events, the backend validates everything, updates state, and broadcasts accepted changes. No client can cheat.

### Tech Stack


| Layer          | Technology                                                                |
| -------------- | ------------------------------------------------------------------------- |
| Frontend       | React 19, TypeScript 6, Vite 8, Tailwind CSS 4, Zustand 5, React Router 7 |
| Backend        | Python 3.14, FastAPI, Pydantic, SQLAlchemy 2 (async), Alembic, asyncpg    |
| Auth           | JWT (PyJWT + bcrypt), Google OAuth (google-auth)                          |
| Data           | PostgreSQL 15, Redis 7                                                    |
| Infrastructure | Docker Compose, Makefile                                                  |




### Database Schema (What Tables Exist)

```
users
├── id (auto-increment primary key)
├── username (unique, indexed)
├── email (unique, indexed)
├── password_hash (nullable for OAuth-only users)
├── is_active, is_verified
└── created_at, updated_at

auth_identities
├── id
├── user_id → users.id
├── provider ("google")
├── provider_subject (Google user ID)
└── provider_email

rooms
├── id
├── code (6-char alphanumeric, unique)
├── host_id → users.id
├── status ("waiting", "in_game", "finished")
├── max_players (default 8)
├── settings (JSON)
└── created_at

room_players
├── room_id → rooms.id
├── user_id → users.id
├── joined_at
└── is_ready

games
├── id
├── room_id → rooms.id
├── status ("active", "finished")
├── round_number
├── phase (current game phase)
└── created_at

game_players
├── game_id → games.id
├── user_id → users.id
├── role ("coordinator", "detective", "citizen")
├── score
└── joined_at

missions
├── id
├── game_id → games.id
├── assigned_to_user_id → users.id
├── mission_type, title, description
├── target_value, current_value
├── status ("active", "completed", "failed")
├── round_number
└── created_at, completed_at

messages
├── id
├── room_id → rooms.id
├── user_id → users.id
├── content (text)
└── created_at

votes
├── id
├── game_id → games.id
├── round_number
├── voter_user_id → users.id
├── target_user_id → users.id
└── created_at
```



### How Authentication Works

1. **Signup**: User sends username/email/password to `POST /api/v1/auth/signup`. Backend checks uniqueness, hashes password with bcrypt, creates user, returns JWT token.
2. **Login**: User sends email/password to `POST /api/v1/auth/login`. Backend looks up user by email, verifies bcrypt hash, returns JWT.
3. **JWT Storage**: Frontend stores token in localStorage. All subsequent requests include `Authorization: Bearer <token>` header.
4. **User Lookup**: `GET /api/v1/auth/me` decodes JWT, looks up user, returns profile.
5. **Google OAuth**: Frontend redirects to `GET /api/v1/auth/google/login`. Backend generates state token (stored in Redis with 300s TTL), redirects to Google. Google redirects back. Backend exchanges code for tokens, verifies ID token signature, creates/links user, returns JWT.
6. **Security**: JWT signed with HS256 using a secret key from `.env`. Tokens expire after 60 minutes. Passwords hashed with bcrypt (never stored in plaintext).



### How Rooms and Lobby Work

1. **Create Room**: Authenticated user calls `POST /api/v1/rooms`. Backend generates unique 6-char code, creates room, adds user as host.
2. **Join Room**: Another user calls `POST /api/v1/rooms/join` with the code. Backend validates room status (must be "waiting"), checks capacity, prevents duplicate joins.
3. **Waiting Lobby**: Frontend connects via WebSocket (`/ws?token=<jwt>&room_code=<code>`). Backend authenticates, authorizes room membership, connects to manager, broadcasts room state. Players see who's in the room and their ready status.
4. **Ready System**: Players toggle ready via WebSocket `PLAYER_READY` event. Host auto-readies. Start button requires all non-host players ready + minimum 3 players.
5. **Start Game**: Host calls `POST /api/v1/rooms/{code}/start`. Backend validates, creates game, assigns roles, generates missions, broadcasts `GAME_START`.



### How the Game Loop Works

The game progresses through a strict state machine:

```
WAITING
    ↓
ROLE_ASSIGNMENT
    ↓
ROUND_START
    ↓
INTERACTION
    ↓
MISSION_EVALUATION
    ↓
DISCUSSION
    ↓
VOTING
    ↓
ROUND_RESULT
    ↓
NEXT_ROUND ──────────┐
    │                 │
    └─────────────────┘

After final round:

ROUND_RESULT
    ↓
GAME_OVER
    ↓
ROLE_REVEAL
    ↓
AI_ANALYSIS
```

Only legal transitions are allowed. The backend validates every transition and rejects invalid state changes. The `VALID_TRANSITIONS` dict in `backend/app/game_engine/state_machine.py` defines the allowed paths.

**Phase breakdown:**

- **ROLE_ASSIGNMENT** (6 seconds): Each player sees their role with an elaborate reveal animation (shuffle → sealing → flip → revealed).
- **ROUND_START**: Shows the public conversation prompt for this round.
- **INTERACTION**: Real-time chat via WebSocket. Players type messages, which are persisted and broadcast. The Coordinator receives missions and tries to complete them. Citizens also complete their own objectives.
- **MISSION_EVALUATION**: Backend checks mission completion, updates scores.
- **DISCUSSION**: Players analyze behavior — who changed topics, who asked leading questions, who influenced others.
- **VOTING**: Players vote for a suspect or skip. Backend prevents double-voting and self-voting. Results are tallied and broadcast.
- **ROUND_RESULT**: Shows voting results, mission outcomes, updated scores.
- **GAME_OVER → ROLE_REVEAL → AI_ANALYSIS**: Final scores compared, winning team announced, all roles and history revealed.



### How WebSocket Communication Works

The protocol uses JSON messages with a standard envelope:

```json
{
  "event": "MESSAGE_SENT",
  "request_id": "uuid",
  "room_id": "uuid",
  "timestamp": "2026-07-08T10:30:00Z",
  "payload": {}
}
```

**Client → Server events:**

- `PLAYER_READY` — Toggle ready status
- `SEND_MESSAGE` — Send chat message
- `CAST_VOTE` — Vote for a player
- `LEAVE_ROOM` — Leave the room

**Server → Client events:**

- `ROOM_STATE` — Full room + player list update
- `PLAYER_JOINED` / `PLAYER_LEFT` — Player connection changes
- `PLAYER_READY_CHANGED` — Ready status update
- `MESSAGE_SENT` — New chat message
- `REACTION_ADDED` — Message reaction
- `ROUND_STARTED` — New round begins
- `TIMER_UPDATED` — Round timer update
- `MISSION_ASSIGNED` — New mission for coordinator
- `MISSION_PROGRESS` — Mission progress update
- `VOTE_UPDATED` — Voting status update
- `ACCUSATION_RESULT` — Accusation outcome
- `ROUND_ENDED` — Round completion
- `GAME_ENDED` — Game over
- `PHASE_CHANGED` — Game phase transition

The `useWebSocket` hook on the frontend handles auto-reconnect (2s delay), event dispatching, optimistic chat messages with server reconciliation, and connection state tracking.

---



## What Has Been Built



### Backend — Fully Implemented

Every backend module has real business logic, proper error handling, async database access, and Pydantic validation. There are no stubs or placeholders — everything works.

#### `backend/app/auth/` — Authentication System


| File               | What It Does                                                                                                                                                                                                                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `security.py`      | Password hashing with bcrypt (via passlib), JWT token creation and decoding with PyJWT. Tokens include user ID and expiration claims.                                                                                                                                           |
| `service.py`       | `signup()` — checks username/email uniqueness, hashes password, creates user, returns JWT. `login()` — looks up user by email, verifies password, returns JWT. `handle_google_callback()` — handles OAuth flow: checks if identity exists, creates user if new, links accounts. |
| `dependencies.py`  | `get_current_user()` — extracts JWT from `Authorization: Bearer` header, decodes it, looks up user. Used as FastAPI dependency on protected routes. `require_active_user()` — checks `is_active` flag.                                                                          |
| `router.py`        | Six endpoints: `POST /signup`, `POST /login`, `POST /logout`, `GET /me`, `GET /google/login` (redirects to Google), `GET /google/callback` (handles OAuth redirect with state validation). Also handles Google account linking flow.                                            |
| `models.py`        | `AuthIdentity` table: tracks external auth providers (Google) linked to users. Unique constraint on `(provider, provider_subject)`.                                                                                                                                             |
| `schemas.py`       | `SignupRequest`, `LoginRequest`, `TokenResponse` with validators (username length/sanitization, email normalization, password min-length).                                                                                                                                      |
| `repository.py`    | `get_identity()`, `create_identity()` — async queries against `AuthIdentity` table.                                                                                                                                                                                             |
| `oauth/google.py`  | `build_authorization_url()` — constructs Google OAuth URL. `verify_google_token()` — exchanges code for tokens, validates ID token signature using Google's public keys.                                                                                                        |
| `oauth/schemas.py` | `GoogleUserInfo` Pydantic model with `sub`, `email`, `email_verified`, `name`, `picture`.                                                                                                                                                                                       |




#### `backend/app/users/` — User Management


| File            | What It Does                                                                                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `models.py`     | `User` table: `id` (auto-increment), `username` (unique, indexed), `email` (unique, indexed), `password_hash` (nullable for OAuth-only), `is_active`, `is_verified`, `created_at`, `updated_at`. |
| `schemas.py`    | `UserResponse` Pydantic model (id, username, email, created_at) with `from_attributes` config.                                                                                                   |
| `repository.py` | Async CRUD: `get_by_id`, `get_by_email`, `get_by_username`, `create`, `update`. All with proper commit/refresh.                                                                                  |
| `service.py`    | `get_user_by_id()`, `get_user_by_email()`, `get_user_by_username()` — User lookup. `update_username()` — username changes with uniqueness check. `get_user_stats()` — user profile with stats.                                                                                                                            |




#### `backend/app/rooms/` — Room Management


| File            | What It Does                                                                                                                                                                                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `models.py`     | `Room` table: `id`, `code` (6-char alphanumeric, unique), `host_id` → users.id, `status`, `max_players`, `settings` (JSON), `created_at`. `RoomPlayer` junction table: `room_id`, `user_id`, `joined_at`, `is_ready`. Unique constraint on `(room_id, user_id)`. |
| `schemas.py`    | `CreateRoomRequest`, `JoinRoomRequest` (with code normalization to uppercase), `RoomResponse` (with `from_attributes`).                                                                                                                                          |
| `repository.py` | `get_by_code`, `create`, `add_player`, `remove_player`, `get_player`, `count_players`, `get_players`, `set_player_ready`, `get_players_with_ready_state`, `get_by_id` — all async.                                                                               |
| `service.py`    | `create_room()` — generates unique 6-char code, creates room + adds host. `join_room()` — validates room status, checks duplicates/capacity, adds player. `leave_room()` — validates membership, prevents host from leaving.                                     |
| `router.py`     | `POST /` (create), `POST /join` (join), `GET /{code}` (get room), `POST /{code}/leave` (leave) — all with auth.                                                                                                                                                  |




#### `backend/app/game_engine/` — Game Logic and State Machine


| File               | What It Does                                                                                                                                                                                                                                                                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `state_machine.py` | `GamePhase` enum with 9 phases (WAITING, ROLE_ASSIGNMENT, ROUND_START, INTERACTION, MISSION_EVALUATION, DISCUSSION, VOTING, ROUND_RESULT, GAME_OVER). `VALID_TRANSITIONS` dict defines legal transitions. `can_transition()` and `validate_transition()` enforce the rules.                                                                       |
| `models.py`        | `Game` table: `id`, `room_id`, `status`, `round_number`, `phase`, `created_at`. `GamePlayer` table: `game_id`, `user_id`, `role`, `score`, `joined_at`. Unique constraint on `(game_id, user_id)`.                                                                                                                                                |
| `schemas.py`       | `AdvancePhaseRequest`, `RoundState`, `GameState`, `RoleAssignment`, `WinConditionResult`.                                                                                                                                                                                                                                                         |
| `repository.py`    | `get_by_room_id`, `create_game`, `add_game_player`, `get_game_players`, `get_game_player`, `get_by_id`, `get_player_by_role` — all async.                                                                                                                                                                                                         |
| `service.py`       | `assign_roles()` — distributes coordinator + detective + citizens. `start_game()` — validates host + readiness, creates game + roles + missions. `advance_phase()` — validates transition, increments round, generates new missions. `check_win_condition()` — coordinator wins at 5+ completed missions, investigation team wins after 5 rounds. |
| `router.py`        | `POST /{room_code}/start` (starts game, broadcasts via WebSocket), `POST /{game_id}/advance-phase` (advances phase, broadcasts, tallies votes, checks win condition, sends missions to coordinator).                                                                                                                                              |




#### `backend/app/chat/` — Chat System


| File            | What It Does                                                                                                                             |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `models.py`     | `Message` table: `id`, `room_id`, `user_id`, `content` (Text), `created_at`.                                                             |
| `schemas.py`    | `ChatMessageResponse`, `SendMessageRequest`.                                                                                             |
| `repository.py` | `create_message()` — creates with flush/refresh. `get_room_messages()` — joins User for username, ordered by created_at, limited to 100. |
| `router.py`     | `GET /api/v1/rooms/{room_code}/messages` — lists messages with membership check (403 if not a member).                                   |


Note: Chat does not have a `service.py`. Message creation logic lives in the WebSocket handler instead.

#### `backend/app/voting/` — Voting System


| File            | What It Does                                                                                                                                                                            |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `models.py`     | `Vote` table: `id`, `game_id`, `round_number`, `voter_user_id`, `target_user_id`, `created_at`. Unique constraint on `(game_id, round_number, voter_user_id)` — prevents double voting. |
| `schemas.py`    | `CastVoteRequest`, `VoteTally`, `VoteResults`.                                                                                                                                          |
| `repository.py` | `create_vote`, `has_voted`, `get_votes_for_round`, `tally_votes` (with GROUP BY and COUNT) — all async.                                                                                 |
| `service.py`    | `cast_vote()` — prevents double-voting and self-voting. `tally_votes()` — aggregates into `VoteResults`.                                                                                |
| `router.py`     | Two endpoints: `GET /{game_id}/round/{round_number}` (vote tally for a round), `GET /{game_id}` (all votes for a game). Used by AI analysis dashboard.                                                                                          |




#### `backend/app/missions/` — Mission System


| File            | What It Does                                                                                                                                                                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `models.py`     | `Mission` table: `id`, `game_id`, `assigned_to_user_id`, `mission_type`, `title`, `description`, `target_value`, `current_value`, `status`, `round_number`, `created_at`, `completed_at`.                                                               |
| `schemas.py`    | `MissionState` (with `from_attributes`), `MissionProgress`.                                                                                                                                                                                             |
| `repository.py` | `create_mission`, `get_game_missions`, `get_by_id`, `update_mission_progress`, `get_user_missions`, `get_active_mission_by_type`, `count_completed_missions` — all async.                                                                               |
| `service.py`    | `generate_missions()` — samples from templates, avoids duplicates per round. `check_mission_completion()` — verifies completion. `get_mission_progress()` — returns progress. `increment_mission_progress()` — caps at target_value and auto-completes. |




#### `backend/app/websocket/` — Real-Time Communication


| File          | What It Does                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `manager.py`  | `ConnectionManager` class: `connect()` (accepts + stores), `disconnect()` (removes by room/user), `send_to_user()` (targeted send with exception handling), `broadcast_to_room()` (sends to all, cleans dead connections). Singleton `manager` instance.                                                                                                                                                                                |
| `handlers.py` | `handle_message()` — dispatches `PLAYER_READY`, `SEND_MESSAGE`, `CAST_VOTE` with full business logic: validates, persists, broadcasts, checks missions/win conditions. `authenticate_websocket()` — decodes token, looks up user. `authorize_room_connection()` — checks room membership. `broadcast_room_state()` — broadcasts room + player state. `send_game_state_to_user()` — sends game state, role, missions to connecting user. |




#### `backend/app/core/` — Configuration and Utilities


| File            | What It Does                                                                                                                                                                            |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config.py`     | `Settings` class via pydantic-settings, loads from `.env`. Database URL, JWT secret/algorithm/expiry, Google OAuth credentials, Redis URL, frontend URL. Singleton `settings` instance. |
| `exceptions.py` | Custom exception hierarchy: `AppException` base, `NotFoundError` (404), `ConflictError` (409), `UnauthorizedError` (401), `ForbiddenError` (403), `ValidationError` (422).              |
| `redis.py`      | Async Redis client with OAuth state storage (300s TTL) for Google login and account linking flows.                                                                                      |




#### `backend/app/db/` — Database Layer


| File         | What It Does                                                                                                                                          |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `base.py`    | `Base` declarative base class using SQLAlchemy's `DeclarativeBase`. All models inherit from this.                                                     |
| `session.py` | `create_async_engine` with `echo=True` for SQL logging, `SessionLocal` async sessionmaker, `get_db` async generator for FastAPI dependency injection. |


---



### Frontend — Fully Implemented

The frontend is fully built with a polished dark/hacker terminal aesthetic. Every feature module has real working code with error handling, loading states, and responsive design.

#### `src/app/` — App Shell


| File         | What It Does                                                                                                                                                     |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `App.tsx`    | Loads auth from localStorage on mount via `useAuthStore.loadFromStorage()`. Renders router with a CRT scanline overlay effect.                                   |
| `router.tsx` | Eight routes: Landing (`/`), Auth (`/auth`), Google Callback (`/auth/google/callback`), Lobby (`/lobby`), Room (`/room/:code`), Game (`/game/:code`), AI Analysis (`/game/:gameId/analysis`), 404 (`*`). |




#### `src/features/auth/` — Authentication (11 files, all implemented)


| File                     | What It Does                                                                                                                                                                       |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AuthPage.tsx`           | Toggle between login/signup forms. Stores auth in Zustand, navigates to lobby on success.                                                                                          |
| `authApi.ts`             | API client: `signup()`, `login()`, `getCurrentUser()`, `beginGoogleLogin()` (redirects to backend), `logout()` (client-side clear). Generic `request()` helper with error parsing. |
| `authValidation.ts`      | Client-side validation: username 2–30 chars, email regex, password min 8 chars, confirm match. `validateSignupForm()` and `validateLoginForm()` composite validators.              |
| `AuthLayout.tsx`         | Two-column layout: left has branding + decorative node visualization, right has form slot. Responsive (single column on mobile).                                                   |
| `LoginForm.tsx`          | Email/password form with client validation, server error display, Google OAuth button, "forgot password (coming soon)" placeholder.                                                |
| `SignupForm.tsx`         | Username/email/password/confirm form with live password strength indicators (uppercase, lowercase, number, length).                                                                |
| `PasswordField.tsx`      | Reusable password input with show/hide toggle, error display, optional hint text.                                                                                                  |
| `AuthModeSwitch.tsx`     | Toggle between "Create account" / "Log in" links.                                                                                                                                  |
| `GoogleAuthButton.tsx`   | Button that calls `beginGoogleLogin()`.                                                                                                                                            |
| `GoogleCallbackPage.tsx` | Handles OAuth redirect, extracts `access_token` from query params, verifies user, handles errors.                                                                                  |
| `auth.types.ts`          | Complete type definitions matching backend API contracts.                                                                                                                          |




#### `src/features/landing/` — Landing Page (10 files, all implemented)


| File                   | What It Does                                                                                                                                                     |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LandingPage.tsx`      | Composes Navbar + 7 section components + Footer.                                                                                                                 |
| `HeroSection.tsx`      | Big hero with tagline "INFLUENCE THE CONVERSATION. HIDE YOUR INTENT. FIND THE SIGNAL.", auth-aware PLAY NOW button, animated concentric rings with player nodes. |
| `GamePreview.tsx`      | Shows a sample game round with player list, chat log, and mission card.                                                                                          |
| `GamePreviewCard.tsx`  | Card showing a secret mission with progress bar.                                                                                                                 |
| `PlayerAvatar.tsx`     | Avatar with initials, optional coordinator glow effect.                                                                                                          |
| `ProgressBar.tsx`      | Simple progress bar component.                                                                                                                                   |
| `HowItWorks.tsx`       | 4-step flow: Join Room → Get Role → Talk & Observe → Accuse & Reveal.                                                                                            |
| `RolesSection.tsx`     | Three role cards: Coordinator (red), Detective (blue), Citizen (green) with objectives and abilities.                                                            |
| `RoundExample.tsx`     | 5-step example round flow from prompt to result.                                                                                                                 |
| `AIAnalysisTeaser.tsx` | Example suspicion analysis with player percentages. Now links to real AI analysis page after completing a game.                                                                                                                          |
| `FinalCTA.tsx`         | Bottom call-to-action with auth-aware PLAY button.                                                                                                               |




#### `src/features/room/` — Room & Lobby (5 files, all implemented)


| File            | What It Does                                                                                                                                                                                                                                                                       |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RoomPage.tsx`  | 311 lines. Full game lobby: room code display + copy to clipboard, connection status, player list with host badge + ready status, ready toggle button, start game (host only, min 3 players, all non-host ready), leave room. Handles `GAME_START` event to navigate to game page. |
| `roomApi.ts`    | `createRoom()`, `joinRoom()`, `getRoom()`, `leaveRoom()` with auth headers from Zustand store.                                                                                                                                                                                     |
| `gameApi.ts`    | `startGame()`, `advancePhase()` with auth headers.                                                                                                                                                                                                                                 |
| `room.types.ts` | `CreateRoomRequest`, `JoinRoomRequest`, `RoomResponse`, `RoomPlayer`, `RoomStateEvent`, `RoleAssignmentEvent`, `PhaseChangedEvent`, `WsServerEvent` (discriminated union of 11 event types), `WsClientEvent` (4 event types).                                                      |
| `game.types.ts` | `GameStateEvent`, `GameStartEvent`, `GameOverEvent` (with optional `scores` array), `GameScore`, `MissionAssignmentEvent`, `MissionData`, `MissionProgressEvent`, `VoteTally`, `VoteResults`, `VoteResultsEvent`, `VoteCastEvent`.                                                                                             |




#### `src/features/game/` — Game Loop (6 files, all implemented)


| File               | What It Does                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GamePage.tsx`     | 569 lines. The most complex component. Full game phase loop: `role_assignment → round_start → interaction → evaluation → discussion → voting → result → next_round/game_over`. WebSocket integration for real-time updates. Auth gating + room metadata fetch. Handles role assignment, phase changes, mission assignment/progress, vote results/casts, game over. Auto-advance from role_assignment after 6 seconds. Host-only phase advancement controls. Renders different UI per phase. Game over phase now shows final scores and links to AI analysis. |
| `RoleReveal.tsx`   | 188 lines. Elaborate 4-stage reveal animation: (1) Shuffle (2s) — cycling through role names, (2) Sealing (1.5s) — animated envelope with "S" seal, (3) Flip (1.5s) — 3D card flip, (4) Revealed — shows role with description. Role-specific colors: coordinator (red), detective (cyan), citizen (gray).                                                                                                                                                                                  |
| `VotePanel.tsx`    | 141 lines. Dual-mode: active voting shows player list with vote buttons, selected state, disabled after voting. Results mode shows winner announcement, tally bars with progress visualization, most-votes highlighting.                                                                                                                                                                                                                                                                    |
| `MissionPanel.tsx` | Shows coordinator's secret missions with title, description, progress bar, completion status.                                                                                                                                                                                                                                                                                                                                                                                               |
| `ScoreBoard.tsx`   | Reusable scoreboard component showing players ranked by score with rank, role, and points. Used in game over phase and AI analysis page.                                                                                                                                                                                                                                                                                                                                                     |
| `PhaseBanner.tsx`  | Color-coded phase indicator (each phase has unique color: yellow/blue/cyan/purple/orange/red/green/gray).                                                                                                                                                                                                                                                                                                                                                                                   |




#### `src/features/chat/` — Chat (2 files, all implemented)


| File            | What It Does                                                                                                                                                           |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ChatPanel.tsx` | 79 lines. Real-time chat with message list, auto-scroll to bottom, current user messages styled differently (accent tint, right-aligned), input form with send button. |
| `chat.types.ts` | `ChatMessage`, `ChatMessageSentEvent`.                                                                                                                                 |




#### `src/features/analysis/` — AI Analysis (3 files, all implemented)


| File             | What It Does                                                                                                                                                                 |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AnalysisPage.tsx` | Full post-game analysis page: AI summary, coordination score, player behavior profiles sorted by suspicion, round-by-round message activity charts, voting patterns breakdown. |
| `analysisApi.ts` | API client: `getGameAnalysis(gameId)` — fetches analysis data from backend `/api/v1/analytics/{gameId}`.                                                                       |
| `analysis.types.ts` | `PlayerAnalysis`, `RoundBreakdown`, `GameAnalysis` types matching backend API response.                                                                                       |




#### `src/hooks/` — Custom Hooks


| File              | What It Does                                                                                                                                                                                                                                                                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `useWebSocket.ts` | 210 lines. Full WebSocket management: auto-reconnect (2s delay), handles 11 server event types + 4 client event types, optimistic chat message insertion with server reconciliation, connection state tracking. Returns `isConnected`, all event states, `chatMessages`, `sendMessage()`. Connects to `ws://localhost:8000/ws?token=...&room_code=...`. |




#### `src/stores/` — State Management


| File           | What It Does                                                                                                                                                                                                                                  |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `authStore.ts` | Zustand store: `user`, `token`, `isAuthenticated`. Actions: `setAuth()` (persists to localStorage), `logout()` (clears localStorage), `loadFromStorage()` (hydrates on app start). Storage keys: `secret_signal_token`, `secret_signal_user`. |




#### `src/components/` — Shared Components


| File                | What It Does                                                                                                                                                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `layout/Navbar.tsx` | Sticky top nav with logo, nav links (How It Works, Roles, About — all link to `/`), auth-aware right section (username + logout when authenticated, "Play Now" when not). Mobile hamburger button (UI only — menu drawer not implemented). |
| `layout/Footer.tsx` | Simple footer with branding, tagline, 3 placeholder links (all `href="#"`), version number.                                                                                                                                                |
| `ui/Button.tsx`     | Reusable button with 3 variants: accent (default), outline, ghost. Supports `asChild` pattern. Uses `forwardRef` and `clsx`.                                                                                                               |




#### `src/index.css` — Styling

207 lines of Tailwind CSS 4 configuration with:

- Custom dark color palette (gray-50 through gray-950, all very dark tones)
- Red accent color system (`--color-accent: #ef4444`)
- Custom font family (SF Mono, Fira Code, etc.)
- Utility classes: `bg-grid`, `bg-grid-large`, `bg-scanlines`, `glow-red`, `glow-cyan`, `glow-green`
- 10 keyframe animations: `fade-in`, `fade-in-up`, `slide-down`, `scale-in`, `pulse-dot`, `role-reveal`, `phase-enter`, `shake`, `seal-glow`, `card-flip`
- 3D card helpers: `preserve-3d`, `backface-hidden`, `rotate-y-180`

---



## What Needs to Be Built



### Immediate — Gaps in the Current MVP

These are things that were missing or incomplete in the current codebase. They have been fixed to make the game fully playable.

#### 1. Voting REST Endpoints (`backend/app/voting/router.py`)

**Status:** COMPLETED

- `GET /api/v1/votes/{game_id}/round/{round_number}` — Get vote tally for a specific round
- `GET /api/v1/votes/{game_id}` — Get all votes for a game (for post-game review)
- These endpoints are used by the AI analysis dashboard



#### 2. Users Service (`backend/app/users/service.py`)

**Status:** COMPLETED

- `get_user_by_id()`, `get_user_by_email()`, `get_user_by_username()` — User lookup
- `update_username()` — Allow username changes with uniqueness check
- `get_user_stats()` — Return user profile with stats (games played, wins, etc.)
- This is used for profile pages and player statistics



#### 3. Chat History on Room Join

**Current state:** When a player joins a room via WebSocket, they only see messages sent after they connected. Old messages are lost.

**What to build:**

- In `send_game_state_to_user()` in `backend/app/websocket/handlers.py`, also send the last 50–100 messages from the room
- On the frontend, initialize `chatMessages` in `useWebSocket.ts` with these messages instead of starting empty
- This requires adding a message history payload to the WebSocket connection flow



#### 4. Server-Side Round Timer

**Current state:** Rounds rely on the host manually advancing phases. There is no automatic timer.

**What to build:**

- Add a `phase_started_at` timestamp to the Game model
- Add a `phase_duration_seconds` setting to room/game settings
- In `advance_phase()`, check if the phase has exceeded its duration
- Add a background task (or use Redis TTL) to auto-advance phases when time runs out
- Broadcast `TIMER_UPDATED` events to the frontend with remaining time
- Frontend already has the `TIMER_UPDATED` event type wired up but nothing triggers it



#### 5. Mission Evaluation Integration

**Current state:** Missions are generated and stored, but there is no automatic evaluation during the interaction phase. Mission completion is not tied to player actions.

**What to build:**

- In the WebSocket `SEND_MESSAGE` handler, after persisting a message, check if the message content matches any active mission patterns for that user
- For example, if a mission is "get 3 players to mention a country", parse the message for country names and increment the mission counter
- This requires defining mission evaluation rules per mission type in `backend/app/missions/service.py`
- Connect this to the `MISSION_PROGRESS` WebSocket event so the coordinator sees real-time updates



#### 6. Frontend Error Handling Improvements

**Current state:** Backend errors return raw JSON. Frontend shows some errors but many 500s are shown to users without helpful messages.

**What to build:**

- Add a global error interceptor in the frontend API client (`authApi.ts` has the pattern, but other API calls don't use it)
- Map backend error codes to user-friendly messages
- Add toast notifications for non-critical errors (e.g., "Failed to send message, retrying...")
- Handle WebSocket disconnection gracefully in the game page (currently shows a blank state)



#### 7. WebSocket Reconnection for Mid-Game

**Current state:** The `useWebSocket` hook has basic reconnection (2s delay), but if a player disconnects mid-game, they lose all state (role, missions, chat history).

**What to build:**

- On reconnect, the backend should resend the player's role, active missions, and recent chat history
- `send_game_state_to_user()` already handles this partially, but it needs to also send:
  - The player's current role assignment
  - Active missions with progress
  - Last 50 messages
  - Current round/phase state
- Frontend needs to properly merge reconnection data with existing state



#### 8. Score Calculation (`backend/app/game_engine/service.py`)

**Status:** COMPLETED

- `calculate_final_scores()` — Computes scores for all players when game ends
- Coordinator: +10 per completed mission, +5 per incorrect accusation (others voted wrong person)
- Investigation team (Detective + Citizens): +10 per correct accusation (coordinator voted out)
- Scores are stored on `GamePlayer.score` and broadcast with `GAME_OVER` event



#### 9. AI/ML Analysis Module (`backend/app/analytics/`)

**Status:** COMPLETED

- `service.py` — Behavioral feature extraction: message frequency, question count, topic initiations, voting accuracy, suspicion scoring
- `router.py` — `GET /api/v1/analytics/{game_id}` endpoint returns full game analysis with player profiles, voting patterns, coordination score, and AI summary
- Players are sorted by suspicion score with detailed round breakdowns
- Used by the frontend AI Analysis page (`/game/:gameId/analysis`)

---



### Phase 2 — Production Multiplayer Features

These features move the game from a development prototype to a production-ready multiplayer system.

#### 1. Redis-Backed Room State

Currently, room state is read from PostgreSQL on every WebSocket message. This works for development but won't scale.

**What to build:**

- Store room state (player list, ready status, connection status) in Redis hashes
- Use Redis pub/sub for broadcasting state changes between WebSocket connections
- Keep PostgreSQL as the source of truth for persistence, but use Redis for real-time reads
- This allows multiple backend instances to share state



#### 2. Player Presence Tracking

Currently, the backend knows who's connected via WebSocket, but this isn't exposed to other players reliably.

**What to build:**

- Track "last seen" timestamp in Redis for each player
- Broadcast presence updates (online/away/disconnected) to the room
- Show visual indicators in the frontend (green dot = online, gray = disconnected)
- This helps players know who's still in the game during discussions



#### 3. Spectator Support

Currently, only players in the room can connect. There's no way to watch a game.

**What to build:**

- Add a `spectator` role to room_players (separate from player roles)
- Spectators receive all broadcasts but cannot send messages or vote
- Frontend renders a spectator view (read-only chat, no action buttons)
- Useful for streaming, tournaments, and debugging



#### 4. Game Event Logging

**Status:** COMPLETED (table exists, events are logged)

The `game_events` table (`backend/app/events/models.py`) logs: message sent, vote cast, phase change, mission progress, game over. Events are created in the WebSocket handler and game engine. The analytics module (`analytics/service.py`) reads these events for behavioral analysis.



#### 5. Rate Limiting

Currently, there is no rate limiting on API endpoints or WebSocket messages.

**What to build:**

- Add rate limiting middleware to FastAPI (e.g., using `slowapi` or Redis-based token bucket)
- Limit API endpoints: 30 requests/minute per user
- Limit WebSocket messages: 10 messages/second per connection
- Prevent spam and abuse



#### 6. Improved Matchmaking

Currently, players must share room codes manually. There's no matchmaking system.

**What to build:**

- Add a matchmaking queue: players join a queue, backend groups them into games
- Match by skill level (based on win/loss record) if available
- Auto-create rooms and assign roles when enough players are queued
- WebSocket-based queue updates (position in queue, estimated wait time)

---



### Phase 3 — AI/ML System

The AI system analyzes player behavior to answer: **Can a model identify the Coordinator from behavioral patterns?**

#### 1. Behavioral Feature Extraction

Extract structured features from game data for ML models.

**Features to extract:**

- Message frequency per player per round
- Response timing (how quickly a player responds to others)
- Conversation initiation (who starts new topics)
- Topic changes (how often a player shifts the conversation)
- Semantic similarity between messages (using sentence embeddings)
- Reaction patterns (who reacts to whom)
- Voting alignment (who votes with whom)
- Interaction frequency (who talks to whom most)
- Mission success correlation
- Player-to-player influence patterns



#### 2. Player Interaction Datasets

Build structured datasets from game event logs.

**What to build:**

- ETL pipeline to transform `game_events` into feature vectors
- Player-level datasets: one row per player per round
- Game-level datasets: aggregated features per game
- Export to pandas DataFrames or Parquet files for ML training



#### 3. Baseline Anomaly Detection

Start with unsupervised methods to flag unusual behavior.

**Approach:**

- Isolation Forest on behavioral features
- Flag players whose behavior deviates significantly from the group
- This gives a "suspicion score" without labeled training data



#### 4. Coordinator Classification Model

Supervised model to predict who is the Coordinator.

**Approach:**

- Gradient boosting (XGBoost/LightGBM) on labeled game data
- Features: all behavioral features from step 1
- Label: whether the player was the Coordinator
- Train on historical game data where Coordinator identity is known



#### 5. Message Embedding Pipeline

Semantic analysis of player messages.

**Approach:**

- Use Sentence Transformers to embed each message
- Compare message semantics across players
- Detect coordinated messaging patterns (Coordinator trying to subtly influence)
- Detect topic manipulation (Coordinator steering conversation)



#### 6. Suspicion Scoring

Real-time suspicion probability per player per round.

**What to build:**

- Model inference endpoint: given current round features, output suspicion probability for each player
- Update scores after each message or phase change
- Store suspicion history per game for post-game analysis



#### 7. Post-Game AI Dashboard

Show players how the AI analyzed the game.

**What to build:**

- Suspicion timeline chart: line chart showing each player's suspicion score across rounds
- Behavior highlights: notable moments the AI flagged
- Feature importance: which behaviors contributed most to the AI's predictions
- Compare AI's top suspect to the actual Coordinator

---



### Phase 4 — Distributed Architecture

Scale the system beyond a single server for production deployment.

#### 1. Event Streaming

Replace direct database writes with event streaming for high-throughput logging.

**What to build:**

- Kafka or Redis Streams for game events
- Backend publishes events to the stream
- Analytics consumers process events asynchronously
- Decouples game server from analytics pipeline



#### 2. Independent Analytics Consumers

Process game events without blocking the game server.

**What to build:**

- Separate service that reads from the event stream
- Processes events into feature vectors in real-time
- Stores features in a data warehouse (ClickHouse or similar)
- Triggers ML model retraining on schedule



#### 3. ML Inference Service

Separate service for model predictions.

**What to build:**

- FastAPI service loaded with trained models
- REST endpoint: `POST /predict` with game features, returns suspicion scores
- Game server calls inference service during rounds
- Model versioning and A/B testing support



#### 4. Model Monitoring

Track model performance and drift over time.

**What to build:**

- Log model predictions alongside actual outcomes
- Calculate accuracy, precision, recall over time
- Alert on significant performance degradation
- Retrain pipeline triggered by monitoring alerts



#### 5. Horizontal WebSocket Scaling

Multiple backend instances handling WebSocket connections.

**What to build:**

- Sticky sessions (route player to same backend instance)
- Redis pub/sub for cross-instance broadcasting
- Connection registry in Redis (which instance handles which player)
- Graceful instance shutdown (migrate connections before stopping)



#### 6. Kubernetes Deployment

Container orchestration for production.

**What to build:**

- Dockerfiles for backend, frontend, ML service
- Kubernetes deployments, services, ingress
- Horizontal pod autoscaler based on WebSocket connection count
- ConfigMaps and Secrets for environment variables
- Persistent volumes for PostgreSQL and Redis



#### 7. Distributed Tracing and Observability

Monitor system health across services.

**What to build:**

- OpenTelemetry instrumentation for all services
- Trace WebSocket message flow through the system
- Prometheus metrics: connection count, message latency, error rates
- Grafana dashboards for real-time monitoring
- Alerting on high latency, error spikes, or connection drops

---



## Development Setup



### Prerequisites

- Python 3.14+
- Node.js 18+
- Docker and Docker Compose
- uv (Python package manager)



### Quick Start

```bash
# 1. Clone and configure
git clone <repo-url>
cd Secret-Signal
cp .env.example .env
# Edit .env — at minimum ensure POSTGRES_PASSWORD matches your Docker setup

# 2. Start databases
docker compose up -d postgres redis

# 3. Set up backend
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# Backend runs at http://localhost:8000
# API docs at http://localhost:8000/docs

# 4. Set up frontend (new terminal)
cd frontend/frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

