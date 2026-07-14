# Secret Signal — Infrastructure Guide

A comprehensive guide to the production infrastructure powering Secret Signal.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Docker](#docker)
3. [Docker Compose](#docker-compose)
4. [Reverse Proxy (NGINX)](#reverse-proxy-nginx)
5. [Environment Configuration](#environment-configuration)
6. [Structured Logging](#structured-logging)
7. [Health Endpoints](#health-endpoints)
8. [Observability](#observability)
9. [Metrics (Prometheus)](#metrics-prometheus)
10. [Dashboards (Grafana)](#dashboards-grafana)
11. [Log Aggregation (Loki)](#log-aggregation-loki)
12. [Distributed Tracing (OpenTelemetry + Tempo)](#distributed-tracing-opentelemetry--tempo)
13. [Background Workers](#background-workers)
14. [CI/CD (GitHub Actions)](#cicd-github-actions)
15. [Security](#security)
16. [Redis Strategy](#redis-strategy)
17. [PostgreSQL Strategy](#postgresql-strategy)
18. [Deployment](#deployment)
19. [Scaling](#scaling)
20. [Kubernetes Migration](#kubernetes-migration)
21. [Teaching Section](#teaching-section)

---

## Architecture Overview

```
                         ┌─────────────────┐
                         │    Internet      │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │              │
              ┌─────▼─────┐ ┌────▼────┐  ┌──────▼──────┐
              │  Vercel    │ │ Railway │  │  Managed    │
              │  Frontend  │ │ Backend │  │  Services   │
              │  (React)   │ │ (API)   │  │  (DB+Redis) │
              └───────────┘ └────┬────┘  └──────┬──────┘
                                 │              │
                           ┌─────┼─────┐        │
                           │     │     │        │
                    ┌──────▼┐ ┌─▼──┐ ┌─▼──┐ ┌──▼───┐
                    │Neon   │ │Upst│ │Prom│ │Grafan│
                    │Postgres│ │ash │ │ethe│ │a     │
                    └───────┘ └────┘ └────┘ └──────┘
```

### Local Development

```
docker compose up -d          ← PostgreSQL + Redis
cd backend && uvicorn ...     ← Backend (port 8000)
cd frontend/frontend && npm run dev  ← Frontend (port 5173)

# Or with Docker:
docker compose up -d          ← Everything including frontend
```

### Ports

| Service | Local Port | Docker Port | Description |
|---------|-----------|-------------|-------------|
| Frontend | 5173 (dev) / 3000 (docker) | 3000 | React app |
| Backend | 8000 | 8000 | FastAPI |
| PostgreSQL | 5433 | 5432 | Database |
| Redis | 6379 | 6379 | Cache/state |
| Prometheus | 9090 | 9090 | Metrics (monitoring profile) |
| Grafana | 3001 | 3000 | Dashboards (monitoring profile) |
| Loki | 3100 | 3100 | Logs (monitoring profile) |
| Tempo | 3200 | 3200 | Traces (monitoring profile) |

---

## Docker

### Why Containers?

Containers package an application with all its dependencies into a single unit that runs identically everywhere. The backend needs Python 3.12, specific pip packages, and system libraries for asyncpg. Without containers, installing these on a different machine might fail due to version mismatches. A Docker image contains everything pre-installed.

### Backend Dockerfile

`infrastructure/docker/Dockerfile.backend` uses a **multi-stage build**:

```
Stage 1 (builder):  Install system deps + Python deps into a virtual env
Stage 2 (runtime):  Copy only the virtual env + app code into a slim image
```

**Why multi-stage?**
- Builder stage has gcc, libpq-dev, and other build tools (~200MB)
- Runtime stage only has libpq5 (~20MB)
- Final image is ~150MB instead of ~400MB
- Fewer packages = fewer security vulnerabilities

### Frontend Dockerfile

`infrastructure/docker/Dockerfile.frontend` uses a **three-stage build**:

```
Stage 1 (deps):    npm ci — install node_modules
Stage 2 (build):   npm run build — create /dist with bundled JS/CSS
Stage 3 (runtime): nginx:alpine — serve the static /dist files
```

The final image is ~25MB (nginx + static files only). No Node.js in production.

### .dockerignore

Prevents unnecessary files from reaching the Docker build context. Without this, Docker would copy .git/, node_modules/, .venv/, and other large directories into the build context, slowing down builds.

---

## Docker Compose

### Why Compose?

Docker Compose defines and runs multi-container applications. Instead of running `docker run postgres...` then `docker run redis...` then remembering all the flags, Compose captures everything in a single declarative file.

### Service Dependencies

```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
```

The `condition: service_healthy` ensures the backend doesn't start until PostgreSQL and Redis pass their health checks. Without this, the backend would crash on startup trying to connect to a database that isn't ready.

### Profiles

Docker Compose profiles allow you to start subsets of services:

```bash
docker compose up -d                          # Core services only
docker compose --profile monitoring up -d     # + Prometheus, Grafana, Loki, Tempo
docker compose --profile tools up -d          # + Adminer, Redis Commander
docker compose --profile monitoring --profile tools up -d  # Everything
```

### Volumes

Named volumes (`postgres_data`, `redis_data`) persist data across container restarts. Without volumes, restarting the PostgreSQL container would destroy all game data.

---

## Reverse Proxy (NGINX)

### Why a Reverse Proxy?

In production, users don't connect directly to the backend process. Instead:

1. **NGINX** listens on port 80/443 (standard HTTP/HTTPS)
2. It serves the React frontend as static files
3. It proxies `/api/*` requests to the backend
4. It proxies `/ws` connections to the backend (WebSocket upgrade)
5. It handles SSL termination, compression, and security headers

This means the backend never deals with SSL, static file serving, or compression. It only handles business logic.

### WebSocket Proxying

WebSocket connections require special HTTP headers to "upgrade" from HTTP to WebSocket:

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

Without these headers, the WebSocket connection would fail silently.

### SPA Fallback

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

React Router handles client-side routing (`/game/ABC123`, `/admin`, etc.). But these paths don't exist as files on disk. NGINX's `try_files` directive returns `index.html` for any path that doesn't match a real file, letting React Router handle the routing.

---

## Environment Configuration

### Variable Separation

| Variable | Frontend | Backend | Docker | Description |
|----------|----------|---------|--------|-------------|
| `VITE_API_URL` | Bundled at build | - | - | Backend URL for API calls |
| `VITE_WS_URL` | Bundled at build | - | - | WebSocket URL |
| `DATABASE_URL` | - | Used | Passed | PostgreSQL connection |
| `SECRET_KEY` | - | Used | Passed | JWT signing key |
| `POSTGRES_PASSWORD` | - | - | Used | DB container password |

**Critical rule:** Variables prefixed with `VITE_` are embedded in the frontend JavaScript bundle. Anyone can see them in browser DevTools. Never put secrets in `VITE_` variables.

### .env.example

The `.env.example` file documents every variable without containing real secrets. It serves as:
- Documentation for new developers
- A template to copy from
- A reference for what each variable does

---

## Structured Logging

### Why Structured Logs?

Traditional logs look like:
```
2025-01-15 10:30:00 INFO: Game 42 started with 8 players
```

Structured logs look like:
```json
{"timestamp":"2025-01-15T10:30:00Z","level":"INFO","service":"backend","message":"game_started","game_id":42,"player_count":8}
```

Structured logs can be:
- **Parsed by machines** (Loki, Elasticsearch, Datadog)
- **Filtered by field** (show me all logs for game_id=42)
- **Correlated** across services (trace a request through frontend → backend → database)
- **Alerted on** (count ERROR logs per minute)

### Context Variables

```python
from app.core.logging import request_id_var, game_id_var

# Set once per request — accessible anywhere in the call stack
request_id_var.set("abc123")
game_id_var.set(42)

# Any module can read these without passing them as parameters
logger.info("message_sent")  # Automatically includes request_id and game_id
```

### Production vs Development

In **development**, logs are human-readable colored output:
```
10:30:00 INFO     app.game_engine: game_started
```

In **production**, logs are JSON for machine parsing:
```json
{"timestamp":"...","level":"INFO","message":"game_started",...}
```

---

## Health Endpoints

### Three Types of Health Checks

| Endpoint | Purpose | What It Checks | Failure Action |
|----------|---------|----------------|----------------|
| `/health` | Liveness | Process is alive | Restart the container |
| `/readiness` | Readiness | Can handle traffic | Stop routing traffic |
| `/startup` | Startup | Initialization complete | Wait before checking |

**Liveness** (`/health`): The simplest check. If this returns 500, the process is broken and should be restarted. It checks nothing external — just "am I alive?"

**Readiness** (`/readiness`): Returns 200 only if the service can handle requests. Checks database and Redis connectivity. If the database is down, this returns 503, telling the load balancer to stop sending traffic until the DB recovers.

**Startup** (`/startup`): Used during container startup to prevent premature health checks. The container starts, loads ML models, runs initialization, and only then returns 200 on `/startup`.

---

## Observability

### The Three Pillars

| Pillar | Tool | What It Answers | Data Type |
|--------|------|-----------------|-----------|
| **Metrics** | Prometheus | "How much?" "How fast?" | Numbers (counters, gauges, histograms) |
| **Logs** | Loki | "What happened?" | Text (structured events) |
| **Traces** | Tempo | "Where did time go?" | Spans (request paths through services) |

### Why These Are Different

- **Metrics** tell you "error rate went up" but not why
- **Logs** tell you "user X got a 500 error" but not which downstream service caused it
- **Traces** tell you "this request took 3 seconds because the database query was slow"

All three are needed for complete observability.

---

## Metrics (Prometheus)

### Why Prometheus?

Prometheus **pulls** metrics from your application (scrapes an HTTP endpoint). This is different from pushing logs (Loki) or traces (Tempo). Pull-based monitoring means:
- Prometheus decides how often to scrape (every 15s)
- Your app doesn't need to know about monitoring infrastructure
- If your app is down, Prometheus knows (scrape fails)

### Metric Types

```
Counter   — only goes up (total_requests, total_errors)
Gauge     — goes up and down (active_connections, queue_depth)
Histogram — distribution of values (request_duration_seconds)
Summary    — calculated quantiles (p50, p95, p99 latency)
```

### Future Backend Metrics

Once `prometheus-fastapi-instrumentator` is added:

```
http_requests_total{method="GET", handler="/api/v1/rooms", status="200"}
http_request_duration_seconds{method="POST", handler="/api/v1/auth/login"}
active_websocket_connections
websocket_messages_total{type="chat"}
signal_ai_requests_total
game_events_total{type="message_sent"}
active_rooms
```

---

## Dashboards (Grafana)

### Why Grafana?

Grafana visualizes Prometheus metrics as graphs, tables, and alerts. It's the "screen" you look at to understand system health. Prometheus stores the data; Grafana makes it human-readable.

### Dashboards Included

| Dashboard | Shows |
|-----------|-------|
| Platform Overview | Request rate, error rate, latency, active rooms/connections |
| Infrastructure | PostgreSQL/Redis health, connections, memory, operations |
| Gameplay (future) | Games started, round progression, win rates, mission completion |
| Signal AI (future) | Analysis requests, inference latency, model accuracy |
| Backend Performance | Per-endpoint latency, throughput, error breakdown |

### Access

```bash
docker compose --profile monitoring up -d
open http://localhost:3001  # Grafana (admin / admin)
```

---

## Log Aggregation (Loki)

### Why Loki Instead of the ELK Stack?

ELK (Elasticsearch, Logstash, Kibana) is powerful but heavy — Elasticsearch requires significant memory and disk. Loki is a lightweight alternative that:
- Uses the same query language as Prometheus (LogQL)
- Stores logs in object storage (S3, GCS, or local filesystem)
- Doesn't index log content — only labels (like Prometheus)
- Runs as a single binary

### How Logs Flow

```
Backend (structured JSON) → Promtail/Alloy → Loki → Grafana
```

The backend writes structured JSON logs. A log collector (Promtail) watches log files and sends them to Loki. Grafana queries Loki for display.

---

## Distributed Tracing (OpenTelemetry + Tempo)

### Why Tracing?

When a user sends a chat message, the request flows through:
1. Frontend → WebSocket → Backend
2. Backend → Authenticate (JWT decode)
3. Backend → Database (INSERT message)
4. Backend → Redis (update presence)
5. Backend → WebSocket broadcast (push to all clients)

Without tracing, you can't see which step is slow. With tracing, you see:

```
[Total: 45ms]
  JWT decode:     2ms
  DB INSERT:      12ms  ← bottleneck?
  Redis update:   3ms
  WS broadcast:   28ms  ← or here?
```

### OpenTelemetry

OpenTelemetry is a vendor-neutral standard for collecting traces. The backend would add the `opentelemetry-sdk` package, which automatically instruments FastAPI, SQLAlchemy, and Redis calls. Traces are exported to the OpenTelemetry Collector, which forwards them to Tempo.

### Why Vendor-Neutral?

If you start with Tempo but later switch to Datadog or Jaeger, you only change the exporter configuration — not the instrumentation code in your application.

---

## Background Workers

### Why Workers?

Some tasks are too slow for a web request:
- **ML model retraining** (minutes)
- **Replay generation** (seconds, but shouldn't block the API)
- **Email notifications** (network I/O)
- **Cleanup of stale data** (periodic, not triggered by users)

Workers run these tasks asynchronously in the background.

### Recommended Stack

**ARQ** (Async Redis Queue) is recommended for Secret Signal because:
- Built on Redis (already in the stack)
- Native async/await support
- Lightweight (no Celery/RabbitMQ complexity)
- Supports job priorities, retries, and rate limiting

---

## CI/CD (GitHub Actions)

### Pipeline Stages

```
Push to main
    │
    ├──► Backend Lint (ruff check + format)
    ├──► Frontend Lint (eslint + tsc)
    │
    ├──► Backend Tests (pytest + PostgreSQL + Redis)
    ├──► Frontend Build (npm build)
    │
    ├──► Docker Build (backend + frontend images)
    │
    └──► Security Scan (pip-audit + npm audit)
```

### Why Each Stage Matters

- **Lint first** — catches style issues in seconds, before running expensive tests
- **Tests with services** — PostgreSQL and Redis run as GitHub Actions service containers, matching production behavior
- **Docker build** — verifies the Dockerfile works, catches dependency issues
- **Security scan** — catches known vulnerabilities in dependencies before they reach production

### PR Preview Deployments

Vercel automatically creates a preview URL for every pull request. This means:
- Code reviewers can test changes before merging
- No "works on my machine" issues
- Every PR gets its own isolated environment

---

## Security

### Secret Management

| Secret | Storage | Where Used |
|--------|---------|------------|
| `SECRET_KEY` | Railway env vars | Backend JWT signing |
| `DATABASE_URL` | Railway env vars | Backend DB connection |
| `REDIS_URL` | Railway env vars | Backend Redis connection |
| `GOOGLE_CLIENT_SECRET` | Railway env vars | OAuth flow |
| `VITE_API_URL` | Vercel env vars | Frontend (NOT a secret) |

**Rules:**
1. Never commit `.env` files to git (`.gitignore` excludes them)
2. Never put secrets in `VITE_` prefixed variables
3. Use different secrets for development, staging, and production
4. Rotate secrets periodically

### Security Headers

The `SecurityHeadersMiddleware` adds headers to every response:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-Frame-Options` | `SAMEORIGIN` | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Content-Security-Policy` | Restrictive | Prevents injected scripts |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits referrer info |
| `Permissions-Policy` | Deny all | Disables camera/mic/geo |

### CORS

CORS (Cross-Origin Resource Sharing) controls which domains can call the API. In production, the backend only allows requests from the Vercel frontend domain. Without CORS, any website could make API calls on behalf of your users.

---

## Redis Strategy

### Key Patterns

```
# Rate limiting (sliding window)
rate_limit:{user_id}:{endpoint}     → sorted set of timestamps

# Token blacklist (JWT revocation)
blacklist:{jti}                      → "1" with TTL = token expiry

# Game state cache
game:{game_id}:state                 → JSON game state
game:{game_id}:timer                 → Timer key with TTL

# WebSocket presence
room:{room_code}:users              → Set of user IDs
user:{user_id}:rooms                → Set of room codes

# Session cache
session:{user_id}                   → JSON user profile (TTL = 1h)
```

### Memory Management

Redis is configured with `maxmemory 256mb` and `allkeys-lru` eviction. When memory is full, Redis automatically evicts the least recently used keys. This prevents Redis from crashing while keeping hot data in memory.

---

## PostgreSQL Strategy

### Connection Pooling

The async driver (asyncpg) creates a connection pool. This matters because:
- Each connection consumes ~10MB of memory on the database server
- Creating a new connection takes ~50ms (TCP handshake + SSL)
- PostgreSQL has a max connection limit (typically 100)

With connection pooling, 20 Python connections can serve 100+ concurrent requests because not every request needs a database connection simultaneously.

### Migration Workflow

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

**Never skip migrations.** Each migration must be applied in order. In production, run migrations before deploying the new code version.

### Indexes

Key indexes for performance:
- `game_events(game_id, sequence_number)` — replay queries
- `messages(room_id, created_at)` — chat history
- `votes(game_id, round_number)` — vote tallying
- `game_players(game_id, user_id)` — player lookups

### Backup Strategy

For managed services (Neon, Railway):
- Enable automatic daily backups
- Test restore periodically
- Keep 7 days of backups minimum

For self-hosted:
```bash
# Daily backup script
pg_dump -h localhost -U postgres secret_signal | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip -c backup_20250115.sql.gz | psql -h localhost -U postgres secret_signal
```

---

## Deployment

### MVP: Managed Services

```
Frontend  → Vercel     (CDN, SSL, preview deploys)
Backend   → Railway    (Docker, WebSocket support, auto-deploy)
Database  → Neon       (Serverless PostgreSQL, free tier)
Redis     → Upstash    (Serverless Redis, pay-per-request)
```

**Why these services?**
- **Zero DevOps burden** — no servers to patch or monitor
- **Automatic scaling** — handle traffic spikes without intervention
- **Generous free/cheap tiers** — $5-10/month total for MVP
- **Built-in features** — SSL, backups, monitoring included

### Production: Kubernetes

See `infrastructure/docs/kubernetes-migration.md` for the full migration guide.

---

## Scaling

### Current: Single Server

```
One backend process (uvicorn) serving all requests.
One PostgreSQL instance (Neon) storing all data.
One Redis instance (Upstash) caching hot data.
```

This handles ~1000 concurrent users comfortably.

### Next: Vertical Scaling

```
Upgrade Railway plan → more RAM/CPU for the backend
Upgrade Neon plan → always-on compute, more storage
```

This handles ~10K concurrent users.

### Future: Horizontal Scaling

```
Multiple backend instances behind a load balancer
PostgreSQL with read replicas
Redis Cluster for horizontal sharding
CDN for static assets (already handled by Vercel)
```

This handles ~100K concurrent users.

### Scaling to 100K Concurrent Players

At this scale:

1. **Load Balancer** distributes WebSocket connections across 10-20 backend instances
2. **Redis Cluster** shards presence data across multiple nodes
3. **PostgreSQL** uses read replicas for analytics; primary for writes
4. **CDN** (Vercel) serves the frontend from edge locations worldwide
5. **ML inference** moves to dedicated GPU servers
6. **Game rooms** are pinned to specific backend instances (WebSocket affinity)
7. **Monitoring** scales with dedicated Prometheus/Grafana infrastructure
8. **Logs** ship to a managed Loki/S3 setup
9. **Traces** go to a Tempo instance with S3 backend

The key insight: at scale, the bottleneck is usually **WebSocket fanout** (broadcasting to thousands of connections per game room). Solutions include:
- Redis Pub/Sub for cross-instance message routing
- Sharding games across instances by room code
- Using a message broker (NATS, Kafka) for high-throughput event distribution

---

## Kubernetes Migration

See `infrastructure/docs/kubernetes-migration.md` for:
- Complete manifest examples (Deployments, Services, Ingress, HPA)
- StatefulSet configurations for PostgreSQL and Redis
- Kustomize overlays for dev/staging/prod
- Step-by-step migration procedure from managed services

**Key principle:** Don't migrate to Kubernetes until you have a specific reason. Managed services handle 99% of use cases.

---

## File Structure

```
Secret-Signal/
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile.backend        # Backend multi-stage build
│   │   └── Dockerfile.frontend       # Frontend multi-stage build
│   ├── nginx/
│   │   └── frontend.conf             # NGINX reverse proxy config
│   ├── prometheus/
│   │   ├── prometheus.yml            # Scrape configuration
│   │   └── alerts.yml                # Alert rules
│   ├── grafana/
│   │   ├── provisioning/
│   │   │   ├── datasources/
│   │   │   │   └── datasources.yml   # Auto-configure data sources
│   │   │   └── dashboards/
│   │   │       └── dashboards.yml    # Auto-load dashboard files
│   │   └── dashboards/
│   │       ├── platform-overview.json
│   │       └── infrastructure.json
│   ├── loki/
│   │   └── loki-config.yml
│   ├── tempo/
│   │   └── tempo-config.yml
│   ├── opentelemetry/
│   │   └── otel-collector-config.yml
│   ├── scripts/                      # Future operational scripts
│   ├── monitoring/                   # Future monitoring setup
│   ├── kubernetes/
│   │   ├── base/                     # Base manifests
│   │   └── overlays/                 # Environment overrides
│   └── docs/
│       ├── deployment.md             # Deployment architecture
│       └── kubernetes-migration.md   # K8s migration guide
├── backend/
│   └── app/
│       ├── core/
│       │   ├── config.py             # Environment variables
│       │   ├── logging.py            # Structured logging
│       │   ├── health.py             # Health endpoints
│       │   └── security_middleware.py # Headers + request ID
│       └── workers/
│           └── interfaces.py         # Background job architecture
├── docker-compose.yml                # Full development stack
├── .env.example                      # Documented env template
├── .dockerignore                     # Docker build context filter
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline
├── Makefile                          # Development commands
└── INFRASTRUCTURE.md                 # This document
```
