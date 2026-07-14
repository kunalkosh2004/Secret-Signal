# Secret Signal — Deployment Architecture

## MVP Deployment Targets

Secret Signal uses a **split deployment** strategy for the MVP. Each component is hosted on the platform best suited for it, minimizing infrastructure management while maintaining production quality.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    INTERNET                           │
│                                                       │
│   ┌─────────────┐          ┌─────────────────────┐   │
│   │   Vercel     │          │     Railway          │   │
│   │  (Frontend)  │◄────────►│    (Backend)         │   │
│   │              │  HTTPS   │                      │   │
│   │  React SPA   │          │  FastAPI + WebSocket │   │
│   │  via nginx   │          │  Uvicorn workers     │   │
│   └─────────────┘          └──────────┬──────────┘   │
│                                        │               │
│                    ┌───────────────────┼──────────┐   │
│                    │                   │          │   │
│            ┌───────▼──────┐   ┌───────▼──────┐   │   │
│            │ Neon Postgres │   │ Upstash Redis│   │   │
│            │ (Managed DB)  │   │ (Managed)    │   │   │
│            └──────────────┘   └──────────────┘   │   │
│                                                    │   │
└─────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Frontend → Vercel

**Why Vercel:**
- Zero-config deployment for React/Vite projects
- Global CDN (Edge Network) — fast for worldwide players
- Automatic preview deployments for every PR
- Built-in SSL certificates
- Free tier covers MVP traffic

**Configuration:**
- Build command: `cd frontend/frontend && npm run build`
- Output directory: `frontend/frontend/dist`
- Environment variables:
  - `VITE_API_URL` → Railway backend URL (e.g., `https://secret-signal-api.up.railway.app`)
  - `VITE_WS_URL` → WebSocket URL (e.g., `wss://secret-signal-api.up.railway.app/ws`)

**CORS:** The backend must allow the Vercel domain (e.g., `https://secret-signal.vercel.app`)

---

### 2. Backend → Railway

**Why Railway:**
- Supports WebSockets natively (critical for real-time games)
- Automatic SSL/TLS
- Built-in PostgreSQL and Redis add-ons (but we use external for independence)
- Simple Dockerfile-based deployment
- Affordable for a single-developer project

**Configuration:**
- Deploy from Dockerfile: `infrastructure/docker/Dockerfile.backend`
- Environment variables (set in Railway dashboard):
  - `DATABASE_URL` → Neon connection string
  - `REDIS_URL` → Upstash REST URL
  - `SECRET_KEY` → Random 64-char string
  - `FRONTEND_URL` → Vercel deployment URL
  - `ENVIRONMENT=production`
  - `LOG_LEVEL=info`

**Resources:**
- Starter plan ($5/month): 512MB RAM, 1 vCPU
- Scales to 1GB RAM if needed for ML inference

---

### 3. PostgreSQL → Neon

**Why Neon:**
- Serverless PostgreSQL (scales to zero when idle — free)
- Automatic branching for schema migrations
- Connection pooling built in
- Point-in-time recovery
- Generous free tier (512MB storage, 24/7 compute)

**Configuration:**
- Create a project at neon.tech
- Connection string format: `postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require`
- The `?sslmode=require` parameter is critical for production

**Important:** Neon provides connection pooling via PgBouncer. Set pool size to 10-20 for the async driver.

---

### 4. Redis → Upstash

**Why Upstash:**
- Serverless Redis (pay per request, very cheap)
- REST API + Redis protocol support
- Global replication option
- Built-in rate limiting primitives
- No server to manage

**Configuration:**
- Create a database at upstash.com
- Copy the `REDIS_URL` from the dashboard
- The URL includes authentication — treat as a secret

**Redis Usage in Secret Signal:**
- WebSocket presence tracking
- Rate limiting (sliding window)
- JWT token blacklisting
- Game timer state
- Session cache

---

### 5. ML Models → Separate Deployment (Future)

**Options:**
- Railway worker service (same project, different process)
- Modal.com (serverless GPU, pay-per-inference)
- Replicate (model hosting)

For the MVP, the ML model is loaded into the backend process memory. This is acceptable because:
- scikit-learn models are small (<10MB)
- Inference is fast (<100ms)
- Single model serves all players

---

## Deployment Steps

### First-time Setup

```bash
# 1. Create a Neon database and note the connection string
# 2. Create an Upstash Redis instance and note the URL
# 3. Push code to GitHub
# 4. Connect Railway to the GitHub repo
# 5. Set environment variables in Railway dashboard
# 6. Deploy — Railway builds the Docker image automatically
# 7. Run migrations via Railway shell:
#    railway run alembic upgrade head
# 8. Connect Vercel to the same GitHub repo
# 9. Set VITE_API_URL and VITE_WS_URL in Vercel dashboard
# 10. Deploy — Vercel builds and serves the frontend
```

### Subsequent Deployments

- **Push to main** → Railway auto-deploys backend, Vercel auto-deploys frontend
- **Open PR** → Vercel creates a preview deployment with a unique URL
- **Database migrations** → Must be run manually after backend deploy:
  ```bash
  railway run alembic upgrade head
  ```

---

## Environment Variables

### Backend (Railway)
| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string |
| `REDIS_URL` | Yes | Upstash Redis URL |
| `SECRET_KEY` | Yes | JWT signing key (random 64 chars) |
| `FRONTEND_URL` | Yes | Vercel deployment URL |
| `ENVIRONMENT` | Yes | `production` |
| `LOG_LEVEL` | No | `info` (default) |
| `GOOGLE_CLIENT_ID` | No | For Google OAuth |
| `GOOGLE_CLIENT_SECRET` | No | For Google OAuth |

### Frontend (Vercel)
| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Railway backend base URL |
| `VITE_WS_URL` | Yes | WebSocket URL (wss://...) |

---

## Cost Estimate (MVP)

| Service | Plan | Monthly Cost |
|---------|------|-------------|
| Vercel | Hobby (free) | $0 |
| Railway | Starter | $5 |
| Neon | Free tier | $0 |
| Upstash | Pay-as-you-go | ~$0-5 |
| **Total** | | **$5-10/month** |

---

## Scaling Considerations

When traffic grows beyond MVP:

1. **Railway** → Upgrade to Pro plan (more RAM/CPU) or add replicas
2. **Neon** → Upgrade to Launch plan for always-on compute
3. **Upstash** → Enable global replication for worldwide latency
4. **Vercel** → Automatically scales (CDN), upgrade if hitting function limits
5. **Move Redis** → Consider a dedicated Redis Cloud instance for WebSocket scaling
6. **Move PostgreSQL** → Consider dedicated instances for connection pooling at scale

At 100K concurrent players, you would need:
- Multiple backend instances behind a load balancer
- Redis Cluster for horizontal scaling
- PostgreSQL with read replicas
- CDN for static assets (already handled by Vercel)
- Dedicated ML inference servers
