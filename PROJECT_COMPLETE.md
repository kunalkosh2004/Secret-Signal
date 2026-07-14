# Secret Signal — Complete Project Summary

> *"Influence the conversation. Hide your intent. Find the signal."*

A real-time multiplayer social deduction game for 4–8 players, built with FastAPI, React, PostgreSQL, Redis, WebSockets, and production-grade infrastructure.

---

## Table of Contents

- [What Is Secret Signal](#what-is-secret-signal)
- [How the Game Works](#how-the-game-works)
- [Tech Stack](#tech-stack)
- [Project at a Glance](#project-at-a-glance)
- [Architecture](#architecture)
- [Backend](#backend)
- [Frontend](#frontend)
- [Infrastructure](#infrastructure)
- [Game State Machine](#game-state-machine)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [ML & Signal AI](#ml--signal-ai)
- [Event Sourcing & Replay](#event-sourcing--replay)
- [Operations Dashboard](#operations-dashboard)
- [CI/CD Pipeline](#cicd-pipeline)
- [Development Setup](#development-setup)
- [Testing & Games Played](#testing--games-played)
- [Roadmap](#roadmap)
- [Key Files](#key-files)

---

## What Is Secret Signal

Secret Signal is a **social deduction game** where players try to identify a hidden Coordinator through behavioral analysis, not elimination. Unlike Mafia or Werewolf, every player stays in the game for all rounds — the tension comes from manipulation, suspicion, and reading other players' chat patterns.

**Key Differentiators:**
- No player elimination — everyone participates every round
- Coordinator receives hidden missions (e.g., "make players mention a country")
- Detective has limited investigation ability (Signal AI scans)
- Citizens also get small private objectives — everyone looks suspicious
- AI-powered post-game analysis breaks down every player's behavior
- Full replay engine to rewatch games event-by-event

---

## How the Game Works

1. **Room Setup** — Host creates a room, 4–8 players join, everyone readies up
2. **Role Assignment** (6s) — Each player sees their role with an animated reveal:
   - **Coordinator** (1 player): Receives secret missions each round
   - **Detective** (1 player): Can run Signal AI scans to identify the Coordinator
   - **Citizens** (6 players): Also receive small private objectives
3. **Round Start** (5s) — Shows the public conversation prompt
4. **Interaction** (120s) — Real-time chat where the Coordinator tries to complete missions without being caught. Everyone messages, reacts, and tries to figure out who's who
5. **Discussion** (90s) — Players accuse each other, share Signal AI results, debate
6. **Voting** — Players vote to accuse someone or skip. Majority accusation ends the game early
7. **Result** (10s) — Shows votes, mission outcomes, round scores
8. Repeat for 4 rounds, then **Game Over** with role reveal and AI analysis

**Scoring:** The Coordinator's team scores if missions complete undetected. The Investigator team scores if the Coordinator is identified.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19, TypeScript 6, Vite 8 | SPA with real-time game UI |
| **Styling** | Tailwind CSS 4 | Dark theme with animations |
| **State** | Zustand 5 | Client-side state management |
| **Routing** | React Router 7 | 11 client routes |
| **Backend** | FastAPI, Python 3.12+ | Async REST API + WebSocket server |
| **ORM** | SQLAlchemy 2 (async) | Database access via asyncpg |
| **Migrations** | Alembic | 20 schema migrations |
| **Auth** | JWT (PyJWT) + bcrypt | Email/password + Google OAuth |
| **Cache/PubSub** | Redis 7 | Rate limiting, presence, timers, sessions |
| **Database** | PostgreSQL 15 | 10+ tables, full relational model |
| **ML** | scikit-learn, NumPy, joblib | Behavioral anomaly detection |
| **ML Tracking** | MLflow | Model versioning and metrics |
| **Docker** | Multi-stage builds | Backend (~150MB) + Frontend (~25MB) |
| **Orchestration** | Docker Compose | 8 services across 3 profiles |
| **Reverse Proxy** | NGINX | SPA serving, API/WS proxy, security headers |
| **CI/CD** | GitHub Actions | Lint, test, build, security scan |
| **Monitoring** | Prometheus + Grafana | Metrics + dashboards |
| **Logging** | Loki | Structured log aggregation |
| **Tracing** | OpenTelemetry + Tempo | Distributed request tracing |
| **Linting** | Ruff, ESLint, Prettier | Code quality |

---

## Project at a Glance

| Metric | Count |
|--------|-------|
| Python source files | 117 |
| TypeScript/TSX files | 89 |
| Database tables | 10 |
| Alembic migrations | 20 |
| REST API endpoints | 18+ |
| WebSocket event types | 17 server / 6 client |
| Docker services | 8 (across 3 profiles) |
| Grafana dashboards | 2 (Platform Overview, Infrastructure) |
| GitHub Actions jobs | 6 |
| Games tested end-to-end | 8+ (3, 5, and 8 players) |
| Total lines of code | ~15,000+ |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         INTERNET                                  │
│                                                                    │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐    │
│  │   Frontend    │    │     Backend       │    │   Data Layer  │    │
│  │               │    │                   │    │               │    │
│  │  React 19     │◄──►│  FastAPI           │◄──►│  PostgreSQL   │    │
│  │  Vite 8       │    │  Uvicorn           │    │  Redis        │    │
│  │  Tailwind 4   │    │  WebSocket         │    │               │    │
│  │  Zustand 5    │    │  20 modules        │    │               │    │
│  │  NGINX (prod) │    │  3 middleware      │    │               │    │
│  └──────────────┘    └──────────────────┘    └──────────────┘    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    Observability                          │    │
│  │  Prometheus → Grafana  |  Loki  |  Tempo + OTel          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                      CI/CD                                │    │
│  │  GitHub Actions: Lint → Test → Build → Security → Deploy │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Backend Module Map

```
backend/app/
├── main.py                 # FastAPI entry point, WebSocket endpoint, middleware stack
├── core/                   # Config, health, logging, Redis utils, security middleware
├── auth/                   # JWT + Google OAuth authentication
├── users/                  # User profiles and management
├── rooms/                  # Room creation, joining, leaving
├── game_engine/            # State machine, role assignment, win conditions
├── chat/                   # Messaging with reactions
├── voting/                 # Vote casting and tallying
├── missions/               # Mission generation and tracking
├── events/                 # Event sourcing (immutable game events)
├── analytics/              # Post-game behavioral analysis
├── signal_ai/              # Real-time AI behavior analysis
├── replay/                 # Event replay engine
├── training/               # ML training data collection
├── ml/                     # ML model integration
├── websocket/              # Connection manager + event handlers
├── db/                     # SQLAlchemy engine + session
└── workers/                # Background job interfaces
```

### Frontend Feature Map

```
frontend/src/
├── app/                    # Router, App shell
├── features/
│   ├── landing/            # 10-component marketing landing page
│   ├── auth/               # Login, signup, Google OAuth, forgot password
│   ├── room/               # Room lobby, player list, ready system
│   ├── game/               # Game loop, role reveal, voting, missions
│   ├── chat/               # Real-time chat panel
│   ├── analysis/           # Post-game AI analysis page
│   ├── replay/             # Event replay timeline
│   └── admin/              # 20-component operations dashboard
├── components/             # Navbar, Footer, Button
├── hooks/                  # useWebSocket (auto-reconnect, event dispatch)
├── stores/                 # Zustand auth store
└── pages/                  # Lobby, NotFound, PlayPlaceholder
```

---

## Backend

### 20 Application Modules

| Module | Files | Purpose |
|--------|-------|---------|
| `core` | 11 | Config, health probes, structured logging, Redis utils, middleware |
| `auth` | 11 | JWT creation/validation, Google OAuth, signup/login/logout |
| `users` | 5 | User CRUD, profile management |
| `rooms` | 6 | Room lifecycle (create, join, leave, ready up) |
| `game_engine` | 8 | State machine, role assignment, phase advancement, win conditions |
| `chat` | 7 | Real-time messaging, message reactions |
| `voting` | 6 | Vote casting (no double-vote, no self-vote), tallying |
| `missions` | 5 | Mission generation, progress tracking, completion |
| `events` | 3 | Immutable game events with sequence numbers |
| `analytics` | 3 | Post-game behavioral feature extraction (500+ lines) |
| `signal_ai` | 3 | Real-time suspicion scoring, behavior metrics, scan limits |
| `replay` | 4 | Event replay engine with state reconstruction |
| `training` | 3 | ML training data collection |
| `ml` | 2 | scikit-learn model integration |
| `websocket` | 3 | Connection manager, 1200-line event handler, room broadcasts |
| `db` | 3 | Async SQLAlchemy engine, session factory |
| `workers` | 2 | Background job interfaces (replay, ML, cleanup) |

### Key Backend Features

**Structured Logging** (`core/logging.py`):
- JSON logs in production (machine-parseable)
- Colored dev logs locally (human-readable)
- Context variables: `request_id`, `user_id`, `game_id`, `room_id`

**Security Middleware** (`core/security_middleware.py`):
- 7 security headers on every response (CSP, X-Frame-Options, etc.)
- Automatic request ID injection (UUID-based)
- Structured request logging with duration tracking

**Health Endpoints** (`core/health.py`):
- `GET /health` — Liveness (is the process alive?)
- `GET /readiness` — Readiness (can it handle traffic? checks DB + Redis)
- `GET /startup` — Startup (initialization complete?)

**Redis Usage**:
| Pattern | Purpose |
|---------|---------|
| `rate_limit:{user_id}:{endpoint}` | Sliding window rate limiting |
| `blacklist:{jti}` | JWT token revocation |
| `game:{id}:state` | Game state cache |
| `game:{id}:timer` | Phase timer with TTL |
| `room:{code}:users` | WebSocket presence (Set) |
| `user:{id}:rooms` | Room membership (Set) |

---

## Frontend

### 11 Client Routes

| Path | Component | Purpose |
|------|-----------|---------|
| `/` | LandingPage | Marketing page with features, how-it-works, CTA |
| `/auth` | AuthPage | Login/Signup with Google OAuth |
| `/auth/google/callback` | GoogleCallbackPage | OAuth token exchange |
| `/lobby` | LobbyPage | Game lobby (create/join rooms) |
| `/room/:code` | RoomPage | Room waiting lobby with ready system |
| `/game/:code` | GamePage | Full game loop (569 lines) |
| `/game/:gameId/analysis` | AnalysisPage | Post-game AI analysis |
| `/game/:gameId/replay` | ReplayPage | Event-by-event replay |
| `/admin/*` | AdminRouter | 9-page operations dashboard |
| `*` | NotFound | 404 page |

### 10 Frontend Feature Modules

| Module | Components | Purpose |
|--------|-----------|---------|
| `landing` | 10 components | Marketing page with HeroSection, GamePreview, HowItWorks, RolesSection |
| `auth` | 6 components | AuthPage, LoginForm, SignupForm, GoogleAuthButton, ForgotPassword |
| `room` | RoomPage | Room lobby, player avatars, ready system, game settings |
| `game` | 6 components | GamePage, RoleReveal (4-stage animation), VotePanel, MissionPanel, ScoreBoard, SignalAIAnalysisPanel |
| `chat` | ChatPanel | Real-time chat with auto-scroll, message reactions |
| `analysis` | AnalysisPage | AI summary, coordination score, behavior profiles per player |
| `replay` | 4 components | ReplayPage, ReplayTimeline, ReplayControls, ReplayInspector |
| `admin` | 15 components + 9 pages | Full dark-theme operations dashboard |
| `components` | Navbar, Footer, Button | Shared UI components |
| `stores` | authStore | Zustand store with localStorage persistence |

### useWebSocket Hook

The `useWebSocket` hook (`hooks/useWebSocket.ts`, 210 lines) manages:
- Auto-reconnection with exponential backoff
- 11 server event types dispatched to handlers
- Optimistic chat message updates
- Token change detection (reconnect on re-login)
- Connection state tracking

---

## Infrastructure

### Docker

**Backend Dockerfile** — 2-stage multi-stage build:
```
Stage 1 (builder): python:3.12-slim + gcc + libpq-dev → pip install
Stage 2 (runtime): python:3.12-slim + libpq5 → only runtime deps
Final size: ~150MB
Security: non-root user (secretsignal)
Healthcheck: curl http://localhost:8000/health
```

**Frontend Dockerfile** — 3-stage build:
```
Stage 1 (deps): node:20-alpine → npm ci
Stage 2 (build): node:20-alpine → npm run build (Vite)
Stage 3 (runtime): nginx:1.27-alpine → serve /dist
Final size: ~25MB
```

### Docker Compose (8 services, 3 profiles)

**Core (always):** postgres, redis, backend, frontend
**Monitoring profile:** prometheus, grafana, loki, tempo
**Tools profile:** adminer, redis-commander

```bash
docker compose up -d                            # Core only
docker compose --profile monitoring up -d       # + Observability
docker compose --profile tools up -d            # + DB browsers
docker compose --profile monitoring --profile tools up -d  # Everything
```

### NGINX Reverse Proxy

- Serves React frontend as static files
- Proxies `/api/*` to backend
- Proxies `/ws` with WebSocket upgrade headers (600s timeout)
- SPA fallback for React Router
- Security headers, gzip, asset caching

### Monitoring Stack

| Tool | Port | Purpose |
|------|------|---------|
| Prometheus | 9090 | Metrics collection (15s scrape interval) |
| Grafana | 3001 | Dashboard visualization |
| Loki | 3100 | Log aggregation |
| Tempo | 3200 | Distributed tracing |

**Grafana Dashboards:**
- Platform Overview: request rate, error rate, latency, active rooms/connections, Signal AI metrics
- Infrastructure: PostgreSQL/Redis health, connections, memory, operations

---

## Game State Machine

```
                    ┌──────────────────────────┐
                    │        WAITING            │
                    │   (lobby, players join)   │
                    └────────────┬─────────────┘
                                 │ host clicks Start
                    ┌────────────▼─────────────┐
                    │    ROLE_ASSIGNMENT (6s)   │
                    │   (role reveal animation) │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │      ROUND_START (5s)     │
                    │  (conversation prompt)    │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │     INTERACTION (120s)    │
                    │   (real-time chat phase)  │
                    │   (mission completion)    │
                    └────────────┬─────────────┘
                                 │ timer expires
                    ┌────────────▼─────────────┐
                    │     DISCUSSION (90s)      │
                    │  (players accuse/debate)  │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │        VOTING             │
                    │  (accuse or skip, manual) │
                    └────────────┬─────────────┘
                                 │ votes tallied
                    ┌────────────▼─────────────┐
                    │       RESULT (10s)        │
                    │  (scores, vote breakdown) │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │      GAME_OVER            │
                    │  (role reveal, AI stats)  │
                    └──────────────────────────┘
```

---

## API Reference

### REST Endpoints (`/api/v1/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Liveness probe |
| `GET` | `/readiness` | No | Readiness probe (DB + Redis) |
| `GET` | `/startup` | No | Startup probe |
| `POST` | `/auth/signup` | No | Register (email/password) |
| `POST` | `/auth/login` | No | Login, returns JWT |
| `POST` | `/auth/logout` | Yes | Revoke JWT |
| `GET` | `/auth/me` | Yes | Current user profile |
| `GET` | `/auth/google/login` | No | Google OAuth redirect URL |
| `GET` | `/auth/google/callback` | No | Google OAuth callback |
| `POST` | `/rooms/` | Yes | Create room (returns 6-char code) |
| `POST` | `/rooms/join` | Yes | Join room by code |
| `GET` | `/rooms/{code}` | Yes | Get room details + players |
| `POST` | `/rooms/{code}/leave` | Yes | Leave room |
| `POST` | `/rooms/{code}/start` | Yes | Start game (host only) |
| `POST` | `/games/{id}/advance-phase` | Yes | Advance game phase |
| `GET` | `/rooms/{code}/messages` | Yes | Get chat history (last 100) |
| `GET` | `/votes/{id}/round/{n}` | Yes | Vote tally for a round |
| `GET` | `/votes/{id}` | Yes | All votes for a game |
| `GET` | `/analytics/{id}` | Yes | Full game analysis |
| `GET` | `/replay/{id}` | Yes | Replay timeline (1100+ events) |
| `GET` | `/replay/{id}/snapshot` | Yes | State at any point |
| `GET` | `/replay/{id}/events` | Yes | Events with filters |

### WebSocket Events

**Client → Server:**
| Event | Payload | Description |
|-------|---------|-------------|
| `PLAYER_READY` | `{is_ready: bool}` | Toggle ready state |
| `SEND_MESSAGE` | `{content: string}` | Send chat message |
| `CAST_VOTE` | `{target_user_id?: number}` | Vote to accuse or skip |
| `ADD_REACTION` | `{message_id, emoji}` | React to a message |
| `SIGNAL_AI_SCAN` | `{}` | Run Signal AI scan (detective only) |
| `LEAVE_ROOM` | `{}` | Leave current room |

**Server → Client:**
| Event | Description |
|-------|-------------|
| `ROOM_STATE` | Updated room with all players and ready states |
| `PLAYER_JOINED` | New player joined the room |
| `PLAYER_LEFT` | Player left the room |
| `PLAYER_READY_CHANGED` | A player toggled ready |
| `MESSAGE_SENT` | New chat message |
| `REACTION_ADDED` | Message reaction |
| `ROUND_STARTED` | New round begins |
| `TIMER_UPDATED` | Phase timer countdown |
| `MISSION_ASSIGNED` | New mission for a player |
| `MISSION_PROGRESS` | Mission progress update |
| `VOTE_UPDATED` | Voting results update |
| `ACCUSATION_RESULT` | Accusation outcome |
| `ROUND_ENDED` | Round summary |
| `GAME_ENDED` | Final results |
| `PHASE_CHANGED` | Game phase transition |
| `SIGNAL_AI_REPORT` | Signal AI scan results |
| `ERROR` | Error message |

---

## Database Schema

### 10 Tables

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│    users     │    │ auth_identities  │    │    rooms     │
│─────────────│    │──────────────────│    │─────────────│
│ id (PK)     │◄───│ user_id (FK)     │    │ id (PK)     │
│ username     │    │ provider         │    │ code (6chr) │
│ email        │    │ provider_subject │    │ host_id(FK) │
│ password_hash│    └──────────────────┘    │ status      │
│ is_active    │                            │ max_players │
│ is_verified  │    ┌──────────────────┐    │ settings    │
│ created_at   │    │  room_players    │    └──────┬──────┘
│ updated_at   │    │──────────────────│           │
└──────────────┘    │ room_id (FK)     │    ┌──────▼──────┐
                    │ user_id (FK)     │    │    games     │
                    │ is_ready         │    │─────────────│
                    └──────────────────┘    │ id (PK)     │
                                            │ room_id(FK) │
┌─────────────┐    ┌──────────────────┐    │ status      │
│game_players │    │    missions      │    │ round_number│
│─────────────│    │──────────────────│    │ phase       │
│ game_id(FK) │    │ game_id (FK)     │    │ created_at  │
│ user_id(FK) │    │ assigned_to(FK)  │    └─────────────┘
│ role        │    │ mission_type     │
│ score       │    │ title, desc      │    ┌─────────────┐
│ joined_at   │    │ target_value     │    │game_events  │
└─────────────┘    │ current_value    │    │─────────────│
                   │ status           │    │ game_id(FK) │
┌─────────────┐    └──────────────────┘    │ seq_number  │
│   votes     │                            │ event_type  │
│─────────────│    ┌──────────────────┐    │ actor_id(FK)│
│ game_id(FK) │    │    messages      │    │ payload     │
│ round_number│    │──────────────────│    │ metadata    │
│ voter (FK)  │    │ room_id (FK)     │    │ created_at  │
│ target (FK) │    │ user_id (FK)     │    └─────────────┘
│ created_at  │    │ content          │
└─────────────┘    │ reply_to_id      │
                   │ created_at       │
                   └──────────────────┘
```

---

## ML & Signal AI

### How Signal AI Works

The Detective can run **Signal AI scans** (max 4 per game, 1 per round) that analyze player behavior and return suspicion scores.

**Scoring Algorithm** (rule-based, designed to be replaced with ML):
1. Message volume analysis — unusually high/low message counts
2. Average message length — coordinator may write longer messages
3. Question frequency — coordinators ask fewer questions
4. Topic initiation — coordinators follow conversation, don't lead
5. Reply ratio — coordinators reply less to others
6. Reaction patterns — reaction frequency analysis
7. Consistency scoring — behavioral deviation from player baseline

**Output:**
```json
{
  "most_suspicious": {"name": "Grace", "suspicion_score": 67.7, "confidence": "medium"},
  "all_players": [
    {"name": "Grace", "suspicion_score": 67.7, "behavior_metrics": [...]},
    {"name": "Henry", "suspicion_score": 57.6, "behavior_metrics": [...]}
  ]
}
```

### ML Pipeline

- **Model**: Isolation Forest + Gradient Boosting (17 features)
- **Training**: 75 labeled game samples, 73.3% accuracy
- **Artifacts**: `backend/ml_models/model.pkl`, `backend/ml_models/best_model.json`
- **Tracking**: MLflow (SQLite backend)
- **Future**: Replace rule-based scoring with real-time ML inference

---

## Event Sourcing & Replay

### Event Model

Every game action is recorded as an immutable event:

```python
class GameEvent:
    game_id: int           # Which game
    sequence_number: int   # Monotonic, unique per game (deterministic order)
    round_number: int      # Which round
    event_type: str        # e.g., "message_sent", "vote_cast", "signal_ai_scan"
    actor_id: int          # Who performed the action
    payload: dict          # Event-specific data
    metadata: dict         # Additional context
```

### Replay Engine

- **`build_timeline()`**: Loads all events, enriches with actor names, computes relative timestamps
- **`get_state_at(sequence_number)`**: Reconstructs complete game state at any point in time
- **18 event types** mapped to 6 categories: game, chat, social, voting, signal, mission

### Verified Data

Game ID 52 (8 players, 5 rounds):
- **1,100 events** recorded
- 5 Signal AI scans with increasing suspicion scores
- Full analytics with voting patterns and coordination scores

---

## Operations Dashboard

A full dark-themed admin dashboard at `/admin` with 9 pages:

| Page | Content |
|------|---------|
| Overview | 12 metric cards, 3 charts, recent matches, activity feed |
| Matches | Full match list with filters |
| Match Detail | Per-game deep dive (placeholder) |
| Analytics | 7 chart types: messages, votes, phases, players, coordination, timeline |
| Signal AI | Model metrics, feature importance, scan history |
| Replay Engine | Event statistics, replay counts |
| Infrastructure | Service status, Redis/PostgreSQL donuts |
| Logs | Structured log viewer |
| Settings | Placeholder for configuration |

---

## CI/CD Pipeline

```
Push to main / Open PR
       │
       ├─► backend-lint      (ruff check + format)
       ├─► frontend-lint     (eslint + tsc --noEmit)
       │
       ├─► backend-test      (pytest + PostgreSQL 15 + Redis 7)
       ├─► frontend-build    (vite build + upload artifact)
       │
       ├─► docker-build      (Buildx for both images, depends on tests)
       │
       └─► security          (pip-audit + npm audit)
```

**Key features:**
- PostgreSQL and Redis run as GitHub Actions service containers
- Docker builds use GitHub Actions cache (GHA backend)
- Frontend build artifacts uploaded for 7-day retention
- Security scanning catches known vulnerabilities before deploy

---

## Development Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker + Docker Compose

### Quick Start
```bash
# Clone and configure
git clone <repo>
cp .env.example .env          # Edit with your values

# Start databases
docker compose up -d postgres redis

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend/frontend
npm install
npm run dev
```

### Available at

| URL | Service |
|-----|---------|
| `http://localhost:5173` | Frontend (Vite dev) |
| `http://localhost:8000` | Backend API |
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/health` | Health check |
| `http://localhost:3000` | Frontend (Docker) |
| `http://localhost:3001` | Grafana (monitoring) |
| `http://localhost:8080` | Adminer (tools) |
| `http://localhost:8081` | Redis Commander (tools) |

### Test Accounts

| Email | Password | User ID |
|-------|----------|---------|
| alice@test.com | testpass123 | 9 |
| bob@test.com | testpass123 | 10 |
| charlie@test.com | testpass123 | 11 |
| dave@test.com | testpass123 | 12 |
| eve@test.com | testpass123 | 13 |
| frank@test.com | testpass123 | 14 |
| grace@test.com | testpass123 | 15 |
| henry@test.com | testpass123 | 16 |
| kunal@test1.com | kunal1234 | 6 |

---

## Testing & Games Played

### Golden Flow Test
`backend/tests/test_golden_flow.py` — 431-line end-to-end test covering:
- User signup and login
- Room creation and joining
- Ready up and game start
- WebSocket connections (3 players)
- Chat message sending
- Phase advancement through all phases
- Voting and vote tallying
- Game over with scores
- Event storage verification
- Training data verification
- Analytics endpoint

### Games Played

| Game ID | Players | Rounds | Room | Result |
|---------|---------|--------|------|--------|
| 46 | 5 | 3 | WUEZ7S | Coordinator won |
| 47 | 3 | 1 | — | Investigation team won |
| 51 | 8 | 1 | 8VQBJI | Henry (coordinator) identified in round 1 |
| 52 | 8 | 5 | 6L6806 | Alice (coordinator) survived all 5 rounds, won |

---

## Roadmap

### Phase 1 — Multiplayer MVP ✅ COMPLETE
- [x] User authentication (JWT + Google OAuth)
- [x] Room creation and joining
- [x] Waiting lobby with ready system
- [x] Role assignment with animated reveal
- [x] Real-time chat via WebSocket
- [x] Mission system
- [x] Round state machine with auto-advancing timers
- [x] Voting and accusation system
- [x] Score calculation
- [x] Game event logging
- [x] AI analytics module
- [x] Replay engine
- [x] Signal AI behavior analysis
- [x] Admin dashboard
- [x] Configurable game settings
- [x] Reactions (10 emojis)
- [x] Reply-to-message
- [x] Mobile responsive design
- [x] Forgot password flow

### Phase 2 — Production Infrastructure ✅ COMPLETE
- [x] Docker multi-stage builds (backend + frontend)
- [x] Docker Compose with 8 services, 3 profiles
- [x] NGINX reverse proxy (SPA + API + WebSocket)
- [x] Structured logging (JSON production / colored dev)
- [x] Security middleware (7 headers + request ID)
- [x] Health endpoints (liveness, readiness, startup)
- [x] Prometheus + Grafana monitoring
- [x] Loki log aggregation
- [x] Tempo distributed tracing
- [x] OpenTelemetry collector config
- [x] CI/CD pipeline (6 jobs)
- [x] Environment configuration (.env.example)
- [x] Background worker architecture
- [x] Deployment documentation
- [x] Kubernetes migration guide

### Phase 3 — AI/ML System (PLANNED)
- [ ] Real-time ML inference replacing rule-based scoring
- [ ] Behavioral feature store
- [ ] Model retraining pipeline
- [ ] Sentence transformer message embeddings
- [ ] Post-game AI coaching

### Phase 4 — Distributed Architecture (FUTURE)
- [ ] Event streaming (Kafka/Redis Streams)
- [ ] Independent analytics consumers
- [ ] ML inference microservice
- [ ] Horizontal WebSocket scaling
- [ ] Kubernetes deployment
- [ ] Multi-region deployment

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI entry point, WebSocket, middleware stack |
| `backend/app/core/config.py` | All environment variables |
| `backend/app/core/logging.py` | Structured logging with context vars |
| `backend/app/core/health.py` | Health/readiness/startup probes |
| `backend/app/core/security_middleware.py` | Security headers + request ID |
| `backend/app/game_engine/state_machine.py` | Phase enum + transitions |
| `backend/app/game_engine/service.py` | Game logic (418 lines) |
| `backend/app/websocket/handlers.py` | WebSocket event handlers (1261 lines) |
| `backend/app/websocket/manager.py` | Connection manager |
| `backend/app/signal_ai/service.py` | Signal AI analysis (488 lines) |
| `backend/app/analytics/service.py` | Post-game analysis (514 lines) |
| `backend/app/replay/engine.py` | Replay engine (277 lines) |
| `backend/app/workers/interfaces.py` | Background job architecture |
| `frontend/frontend/src/app/router.tsx` | Client routes (11 routes) |
| `frontend/frontend/src/features/game/pages/GamePage.tsx` | Game loop (569 lines) |
| `frontend/frontend/src/hooks/useWebSocket.ts` | WebSocket management (210 lines) |
| `docker-compose.yml` | Full development stack |
| `infrastructure/docker/Dockerfile.backend` | Backend Docker image |
| `infrastructure/docker/Dockerfile.frontend` | Frontend Docker image |
| `infrastructure/nginx/frontend.conf` | NGINX configuration |
| `.github/workflows/ci.yml` | CI/CD pipeline |
| `.env.example` | Environment variable reference |
| `INFRASTRUCTURE.md` | Infrastructure guide (728 lines) |
| `README.md` | Project overview (602 lines) |
| `PROJECT_STATUS.md` | Detailed status (1021 lines) |

---

*Built by Kunal Koshta. Secret Signal is open source under the MIT License.*
