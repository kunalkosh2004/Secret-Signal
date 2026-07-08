# Continue Here — Next Steps

## What's already done

- **Frontend**: Auth page, login/signup forms, validation, routing (`/auth`), lobby placeholder
- **Backend scaffold**: All files created, all stubs raise `NotImplementedError` — nothing actually works yet

## Your job: make the backend actually authenticate people

Do these steps **in order**. Each step builds on the previous one.

---

### 1. Install backend dependencies

```bash
cd backend
pip install -e ".[dev]"
pip install "passlib[bcrypt]" pyjwt pydantic-settings httpx
```

### 2. Start PostgreSQL and Redis

```bash
docker compose up -d postgres redis
```

### 3. Set up your `.env` file

```bash
cp .env.example .env
```

Edit `.env` — at minimum ensure `DATABASE_URL` or the Postgres vars are correct.

### 4. Open `backend/app/` in your editor

Every file that needs your code has `# TODO` comments. Start at the bottom of the dependency chain and work up:

---

## Implementation Order

### Layer 1 — Database & models

| Step | File | What to do |
|---|---|---|
| 1 | `app/db/base.py` | Already done — just `DeclarativeBase` |
| 2 | `app/db/session.py` | Create async engine + session factory + `get_db` dependency |
| 3 | `app/users/models.py` | Create the `User` SQLAlchemy model (id, username, email, password_hash, etc.) |
| 4 | `app/core/config.py` | Create `Settings` class reading from `.env` |

**Test it:** `alembic init migrations`, wire up `env.py`, run `alembic revision --autogenerate`, inspect, then `alembic upgrade head`. Verify with `psql`.

### Layer 2 — Repository (data access)

| Step | File | What to do |
|---|---|---|
| 5 | `app/users/repository.py` | Implement `get_by_email`, `get_by_username`, `get_by_id`, `create` |

### Layer 3 — Security utilities

| Step | File | What to do |
|---|---|---|
| 6 | `app/auth/security.py` | Implement `hash_password` (bcrypt via passlib) |
| 7 | `app/auth/security.py` | Implement `verify_password` |
| 8 | `app/auth/security.py` | Implement `create_access_token` (JWT via pyjwt) |
| 9 | `app/auth/security.py` | Implement `decode_access_token` |

### Layer 4 — Dependencies

| Step | File | What to do |
|---|---|---|
| 10 | `app/auth/dependencies.py` | Implement `get_current_user` (extract JWT → look up user) |

### Layer 5 — Service (business logic)

| Step | File | What to do |
|---|---|---|
| 11 | `app/auth/service.py` | Implement `signup` (check uniqueness → hash → create → token → return) |
| 12 | `app/auth/service.py` | Implement `login` (find user → verify password → token → return) |

### Layer 6 — Router (HTTP endpoints)

| Step | File | What to do |
|---|---|---|
| 13 | `app/auth/router.py` | Replace stubs: wire `signup`, `login`, `me` to real service calls |
| 14 | `app/auth/router.py` | Wire `logout` (at minimum clear-token semantics) |

**Test it:** `uvicorn app.main:app --reload`, hit `/docs`, try signup + login manually.

### Layer 7 — Connect frontend

| Step | File | What to do |
|---|---|---|
| 15 | `frontend/.../auth/services/authApi.ts` | Replace stub bodies with real `fetch()` calls to your backend |

### Layer 8 — Google OAuth (optional, do later)

| Step | File | What to do |
|---|---|---|
| 16 | `app/auth/oauth/google.py` | Implement authorization URL, token exchange, ID token validation |
| 17 | `app/auth/oauth/schemas.py` | Fill in `GoogleUserInfo` |

---

## Key files to reference

| What you need | Read this first |
|---|---|
| What each backend file does | `backend/app/auth/README.md` (full educational guide) |
| Frontend API contract | `frontend/.../auth/types/auth.types.ts` |
| Frontend service stubs | `frontend/.../auth/services/authApi.ts` |
| Frontend validation rules | `frontend/.../auth/validation/authValidation.ts` |
| CORS configuration | `backend/app/main.py` |
| Env variable docs | `.env.example` |

## Quick sanity check

After each step, run:

```bash
cd backend && python3 -c "from app.main import app; print('OK')"
```

and:

```bash
cd frontend/frontend && npm run build
```

If both pass, you're good.
