# Secret Signal — Authentication Architecture

> **Audience:** You know Python but are learning web authentication.
> This guide explains every piece and why it exists, end-to-end.

---

## Table of Contents

1. [What happens when you click "Play Now"](#1-what-happens-when-you-click-play-now)
2. [React Router and the `/auth` page](#2-react-router-and-the-auth-page)
3. [AuthPage, LoginForm, and SignupForm state](#3-authpage-loginform-and-signupform-state)
4. [Frontend validation](#4-frontend-validation)
5. [The API service layer](#5-the-api-service-layer)
6. [POST /auth/signup — what the backend does](#6-post-authsignup--what-the-backend-does)
7. [Pydantic schema validation](#7-pydantic-schema-validation)
8. [The service layer](#8-the-service-layer)
9. [The repository layer](#9-the-repository-layer)
10. [SQLAlchemy models](#10-sqlalchemy-models)
11. [PostgreSQL storage](#11-postgresql-storage)
12. [Why Alembic is needed](#12-why-alembic-is-needed)
13. [Password hashing (conceptual)](#13-password-hashing-conceptual)
14. [Login verification (conceptual)](#14-login-verification-conceptual)
15. [Access tokens and sessions](#15-access-tokens-and-sessions)
16. [How `/auth/me` identifies the current user](#16-how-authme-identifies-the-current-user)
17. [Google OAuth end-to-end](#17-google-oauth-end-to-end)
18. [How the frontend knows you're authenticated](#18-how-the-frontend-knows-youre-authenticated)
19. [Authentication vs. Authorization](#19-authentication-vs-authorization)
20. [Security Learning Notes](#20-security-learning-notes)
21. [Token strategy trade-offs](#21-token-strategy-trade-offs)
22. [Alembic setup guide](#22-alembic-setup-guide)
23. [Testing plan](#23-testing-plan)

---

## 1. What happens when you click "Play Now"

On the landing page, every "Play Now" button links to `/auth`:

```tsx
<Link to="/auth">PLAY NOW</Link>
```

React Router intercepts this click, matches `/auth` in the route table (no page reload), and renders `<AuthPage />`.

All three "Play Now" locations are updated:
- **Navbar** → `/auth`
- **HeroSection** → `/auth`
- **FinalCTA** → `/auth`

---

## 2. React Router and the `/auth` page

The router is defined in `frontend/frontend/src/app/router.tsx`.

Before:
```
/         → LandingPage
/play     → PlayPlaceholder
*         → NotFound
```

After:
```
/         → LandingPage
/auth     → AuthPage        ← new
/lobby    → LobbyPlaceholder ← new (future lobby)
*         → NotFound
```

The `/play` route was replaced. The `PlayPlaceholder` component still exists on disk but is no longer routed. It can be deleted later or repurposed.

`LobbyPlaceholder` shows a "coming soon" message. The real lobby is for a future task.

---

## 3. AuthPage, LoginForm, and SignupForm state

### AuthPage

File: `features/auth/pages/AuthPage.tsx`

Manages one piece of state: `mode` — either `'login'` or `'signup'`.

Renders:
- **Header** changes based on mode
- **LoginForm** or **SignupForm** depending on mode
- **AuthModeSwitch** at the bottom (the "Already have an account? Log in" toggle)

### LoginForm

File: `features/auth/components/LoginForm.tsx`

State:
- `email`, `password` — form field values
- `errors` — field-level validation errors
- `submitting` — true during API call (disables inputs, changes button text)
- `serverError` — error message from the API

On submit:
1. Runs `validateLoginForm()` (frontend validation)
2. If valid, calls `login()` from `authApi.ts`
3. If the API throws, displays the error message
4. If the API succeeds, calls `onSuccess()` which navigates to `/lobby`

### SignupForm

File: `features/auth/components/SignupForm.tsx`

State: `username`, `email`, `password`, `confirmPassword`, plus `errors`, `submitting`, `serverError`.

Has a password requirements section that turns green as each requirement is met (visual feedback).

Both forms use `noValidate` on the `<form>` element to disable the browser's built-in validation tooltips, since we provide custom validation.

---

## 4. Frontend validation

File: `features/auth/validation/authValidation.ts`

Centralised validation functions:

| Function | Checks |
|---|---|
| `validateUsername` | Not empty, 2-30 chars |
| `validateEmail` | Basic `@` and dot structure |
| `validatePassword` | Not empty, min 8 chars |
| `validateConfirmPassword` | Matches password |
| `validateSignupForm` | Runs all signup validations, returns `FormErrors` |
| `validateLoginForm` | Runs email + password validation |

**Why validate on the frontend if the backend validates anyway?**

- Instant feedback — the user doesn't wait for a round-trip to the server
- Reduces unnecessary network requests
- BUT: frontend validation is NOT security. Anyone can bypass it (curl, Postman, browser DevTools). The backend is the real gatekeeper.

---

## 5. The API service layer

File: `features/auth/services/authApi.ts`

Each function maps to a future backend endpoint:

```typescript
signup(data: SignupRequest): Promise<AuthResponse>
login(data: LoginRequest): Promise<AuthResponse>
logout(): Promise<void>
getCurrentUser(): Promise<UserResponse>
beginGoogleLogin(): void  // redirects to backend OAuth endpoint
```

Currently every function throws a `not implemented` error because the backend endpoints don't exist yet.

When you implement them, replace the body with `fetch()` (or your chosen HTTP client) calls. The function signatures won't change — only the implementation.

---

## 6. POST /auth/signup — what the backend does

When the frontend calls `POST /api/v1/auth/signup`, this is the flow:

1. **FastAPI receives the request** — matches the path and method to the route handler in `auth/router.py`.
2. **Pydantic validates the body** — the JSON is parsed into a `SignupRequest` schema. If fields are missing or invalid, FastAPI returns 422 automatically.
3. **The handler calls the service** — `auth_service.signup(db, request)`.
4. **The service normalises the email** — converts to lowercase so `Alice@Example.com` and `alice@example.com` match.
5. **The service checks uniqueness** — queries the user repository for existing email and username.
6. **The service hashes the password** — calls `security.hash_password(plaintext)` which returns a bcrypt hash.
7. **The service creates the user** — calls `user_repository.create(db, ...)` which does `INSERT INTO users (...)`.
8. **The service creates a token** — calls `security.create_access_token({"sub": user_id})` which returns a JWT.
9. **The service returns the response** — `TokenResponse(user=user_data, access_token=token)`.
10. **FastAPI serialises the response** — converts the Pydantic model to JSON and sends it with status 201.
11. **The frontend receives the response** — stores the token, updates auth state, navigates to `/lobby`.

---

## 7. Pydantic schema validation

Pydantic schemas (in `auth/schemas.py` and `users/schemas.py`) define:

- What fields the API accepts (request schemas)
- What fields the API returns (response schemas)
- Validation rules (email format, string lengths, etc.)

Example: `SignupRequest` might look like:

```python
class SignupRequest(BaseModel):
    username: str = Field(min_length=2, max_length=30, pattern=r"^\w+$")
    email: EmailStr
    password: str = Field(min_length=8)
```

`EmailStr` is a Pydantic type that validates the string looks like an email address.

The `field_validator` decorator lets you add custom validation, e.g., normalising email to lowercase.

**Why Pydantic?**
- Type coercion and validation happen automatically
- Errors have standard formatting that FastAPI returns as 422 responses
- IDE autocompletion works on validated data

---

## 8. The service layer

File: `auth/service.py`

The service layer contains **business logic**. It:

- Orchestrates multi-step operations (check → hash → create → tokenise)
- Calls the repository layer for data access
- Calls the security layer for hashing and token creation
- Raises domain exceptions (`ConflictError`, `UnauthorizedError`)
- Never touches the HTTP request/response objects
- Never returns raw database models to the router (converts to schemas)

Why not put all this in the route handler? Separation of concerns:
- **Router** → HTTP concerns (status codes, headers, response format)
- **Service** → Business logic (what happens when someone signs up)
- **Repository** → Data access (how to query/store users)

A route handler should be thin:

```python
@router.post("/signup", status_code=201)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.signup(db, request)
    return result
```

---

## 9. The repository layer

File: `auth/repository.py` and `users/repository.py`

The repository layer contains **database queries**. It:

- Uses SQLAlchemy `select()` statements
- Returns model instances or `None`
- Never contains business logic like password hashing
- Never calls other repositories or services

```python
async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
```

Why a separate repository? Historically, this makes testing easier — you can mock the repository when testing the service. For this project, the main benefit is keeping queries organised in one place.

---

## 10. SQLAlchemy models

File: `users/models.py`

SQLAlchemy models map Python classes to PostgreSQL tables.

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(onupdate=func.now())
```

Key points:
- `Mapped[str]` is SQLAlchemy 2.0's type annotation syntax
- `server_default=func.now()` — the database sets this, not Python
- `onupdate=func.now()` — auto-updates on every row modification
- `password_hash: str | None` — nullable, because Google OAuth users may not have a password
- Unique constraints on `username` and `email` prevent duplicates at the database level

---

## 11. PostgreSQL storage

The `docker-compose.yml` starts a PostgreSQL 15 container on port 5432 with:
- User: `postgres`
- Password: `postgres`
- Database: `secret_signal`

Data is persisted in a Docker volume `postgres_data` so it survives container restarts.

---

## 12. Why Alembic is needed

SQLAlchemy models define tables in Python, but the actual tables live in PostgreSQL. You need some way to keep them in sync.

**Alembic** is a database migration tool. It compares your SQLAlchemy models (the desired state) to the actual database (the current state) and generates SQL to bridge the gap.

Workflow:
1. Define or change a model in Python
2. Run `alembic revision --autogenerate -m "description"`
   → Alembic creates a migration file in `migrations/versions/`
3. **Always inspect the generated migration** — autogenerate can make mistakes
4. Run `alembic upgrade head`
   → Alembic applies the migration to the database

Migration files are committed to Git. They serve as a version history of your database schema.

---

## 13. Password hashing (conceptual)

**Never store passwords directly.**

When a user signs up:
```
password: "hunter2"
```
                   ↓
```
password_hash: "$2b$12$LJ3m4yPnV2ViKLMNOPqRsO5kLm7Xy..."
```

The hash is a **one-way** function. You cannot reverse it to get the original password.

### Hashing vs. Encryption

| Feature | Hashing | Encryption |
|---|---|---|
| Reversible? | No (one-way) | Yes (two-way with a key) |
| Purpose | Password storage | Data secrecy |
| Example | bcrypt, argon2 | AES, RSA |

### What is a salt?

A **salt** is a random value added to each password before hashing:

```
hash(password + random_salt)
```

Without a salt:
- Two users with the same password have the same hash
- Attackers can pre-compute hashes of common passwords (rainbow tables)

With a salt:
- Each user's hash is unique even with the same password
- Attacker must crack each hash individually

Bcrypt and argon2 handle salting automatically — you don't need to manage it.

### Why not SHA-256 alone?

SHA-256 is designed to be **fast**. Attackers can try billions of passwords per second with GPUs.

Bcrypt is designed to be **slow** (configurable work factor). It also incorporates a salt automatically.

For Secret Signal: Use bcrypt via the `passlib` library.

---

## 14. Login verification (conceptual)

When a user logs in:
```
email: "alice@example.com"
password: "hunter2"
```

1. Backend finds the user by email
2. Backend retrieves `password_hash` from the database
3. Backend calls `verify_password("hunter2", stored_hash)`
4. Internally, the function extracts the salt from the stored hash, re-hashes the input with that salt, and compares

```python
pwd_context.verify("hunter2", "$2b$12$LJ3m4yPnV2ViKLMNOPqRsO5kLm7Xy...")
# True if matches, False otherwise
```

**Important:** Return a generic error for both "user not found" and "wrong password":

```
Invalid email or password.
```

This prevents attackers from knowing whether an email is registered (account enumeration).

---

## 15. Access tokens and sessions

After successful login, the backend needs to tell the frontend "this request is authenticated for future requests."

The plan: **JWT (JSON Web Token)** access tokens.

### What is a JWT?

A JWT is three Base64-encoded parts separated by dots:

```
header.payload.signature
```

The payload is JSON:
```json
{
  "sub": "user-uuid-here",
  "exp": 1712345678
}
```

The **signature** proves the token was issued by your server. Anyone who has your secret key can verify the token hasn't been tampered with.

**Important:** The payload is **not encrypted**. It's only Base64-encoded. Anyone with the token can read the payload. Never put secrets in a JWT.

### Token flow:

1. **Login**: Backend creates a JWT, returns it to the frontend
2. **Frontend stores it** (in memory, localStorage, or sessionStorage — see trade-offs below)
3. **Frontend sends it** in the `Authorization` header:
   ```
   Authorization: Bearer <jwt>
   ```
4. **Backend validates it** on every protected route (via the `get_current_user` dependency)
5. **Token expires** — the `exp` claim contains the expiration timestamp

---

## 16. How `/auth/me` identifies the current user

`GET /api/v1/auth/me` is a protected endpoint.

It uses the `get_current_user` dependency:

```python
async def get_current_user(token = Depends(oauth2_scheme), db = Depends(get_db)):
    # 1. Extract token from Authorization header
    # 2. Decode and validate the JWT (check signature, not expired)
    # 3. Extract `sub` claim (user ID)
    # 4. Look up user by ID in the database
    # 5. Return the User object
    # 6. If any step fails → 401 Unauthorized
```

The handler then returns the user's data:

```python
@router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
```

This is how the frontend can check: "Is the user still logged in?" on page refresh.

---

## 17. Google OAuth end-to-end

### What is OAuth?

OAuth is a delegated authorization protocol. In Secret Signal, "Continue with Google" means:
- You (the user) want to log into Secret Signal
- Google vouches for your identity
- Secret Signal trusts Google's vouching

### The flow:

```
Frontend                    Backend                     Google
   │                          │                          │
   │ 1. Click "Continue       │                          │
   │    with Google"          │                          │
   │──┐                       │                          │
   │  │ beginGoogleLogin()    │                          │
   │←─┘                       │                          │
   │                          │                          │
   │ 2. Redirect to           │                          │
   │    GET /auth/google/login│                          │
   │─────────────────────────>│                          │
   │                          │                          │
   │                          │ 3. Generate state param  │
   │                          │    (random, stored in    │
   │                          │     Redis with TTL)      │
   │                          │                          │
   │                          │ 4. Redirect to Google    │
   │    < 302 Redirect        │                          │
   │                          │                          │
   │ 5. Browser follows       │                          │
   │    redirect to Google    │                          │
   │────────────────────────────────────────────────────>│
   │                          │                          │
   │                          │                          │ 6. User logs in
   │                          │                          │    (on Google)
   │                          │                          │
   │                          │ 7. Google redirects to   │
   │                          │    /auth/google/callback │
   │                          │    ?code=abc&state=xyz   │
   │    <─────────────────────│──────────────────────────│
   │                          │                          │
   │                          │ 8. Verify state matches  │
   │                          │ 9. Exchange code for     │
   │                          │    tokens (POST to       │
   │                          │    Google's token API)   │
   │                          │                          │
   │                          │ 10. Validate ID token    │
   │                          │     (check signature,    │
   │                          │      iss, aud, sub)      │
   │                          │                          │
   │                          │ 11. Find or create user  │
   │                          │     + auth_identity      │
   │                          │                          │
   │                          │ 12. Create app session/  │
   │                          │     token                │
   │                          │                          │
   │    < 302 Redirect        │                          │
   │    to FRONTEND_URL       │                          │
   │    with session          │                          │
   │                          │                          │
   │ 13. App loads,           │                          │
   │     calls GET /auth/me   │                          │
   │─────────────────────────>│                          │
   │                          │                          │
   │    < UserResponse        │                          │
   │                          │                          │
```

### Key concepts:

- **State parameter**: A random value generated by your backend, stored temporarily, and verified when Google redirects back. Prevents CSRF attacks on the callback.
- **Authorization code**: A one-time code Google gives your backend, which is exchanged for tokens. This happens server-to-server, so the tokens are never exposed to the browser.
- **ID token**: A JWT signed by Google containing the user's identity claims (`sub`, `email`, `name`, etc.). Your backend validates the signature using Google's public keys.
- **`sub` (subject)**: A stable, unique identifier for the user at Google. This is what you store in `auth_identities.provider_subject`.

### Why `provider_subject` over email?

Google's `sub` claim never changes for a given Google account. Email addresses can change. If you identify users only by email, and someone changes their Google email, they'd appear as a different user.

---

## 18. How the frontend knows you're authenticated

After successful login/signup:

1. **Backend returns** `{ user, accessToken }`
2. **Frontend stores** the access token (in-memory or localStorage)
3. **Frontend sets** the `Authorization: Bearer <token>` header on subsequent requests
4. **On page refresh**, the frontend calls `GET /auth/me` to check if the token is still valid
5. **If valid**, the user data is loaded into the auth store
6. **If invalid/expired**, the user is redirected to `/auth`

This is not yet implemented — it requires:
- An auth store (Zustand) to hold the current user state
- Token storage logic
- A protected route wrapper component
- An API interceptor that adds the Authorization header

---

## 19. Authentication vs. Authorization

| Concept | Question it answers | Secret Signal example |
|---|---|---|
| **Authentication** | "Who are you?" | "This WebSocket connection belongs to player Kunal (user_id=42)" |
| **Authorization** | "What are you allowed to do?" | "Can Kunal see the Coordinator's secret mission? (No, Kunal is a Citizen)" |

### Authentication examples in Secret Signal:
- Logging in with email/password
- Verifying the JWT on the `/auth/me` endpoint
- Identifying which player sent a chat message

### Authorization examples in Secret Signal:
- Is this user the room host? → Only the host can start the game.
- Can this player vote now? → Only if the voting phase is active.
- Can this player see this private mission? → Only the Coordinator sees their mission.
- Can this player kick another player? → Only the host can kick.

Authentication happens once (at login). Authorization happens on every protected operation.

---

## 20. Security Learning Notes

### Why passwords must never be stored directly
If an attacker breaches the database and finds plaintext passwords, they can:
- Log into those users' Secret Signal accounts
- Try those same email/password combinations on other services (credential stuffing)

### Password hashing vs. encryption
- **Hashing** is one-way. You cannot recover the original password from a hash.
- **Encryption** is two-way. If someone has the encryption key, they can decrypt.
- Passwords should always be **hashed**, never encrypted.

### Salts
A random value prepended to each password before hashing. Ensures identical passwords produce different hashes. Makes rainbow table attacks infeasible.

### Why fast hashes (SHA-256, MD5) are unsuitable
Modern GPUs can compute billions of SHA-256 hashes per second. A password like "password123" would be cracked in milliseconds. Bcrypt/argon2 are deliberately **slow** (configurable work factor).

### Why HTTPS is required (in production)
Without HTTPS, anyone on the same network can intercept the password in transit (packet sniffing). For local development, HTTP is acceptable, but production MUST have TLS.

### Why frontend validation is not security
Frontend validation is a UX convenience. Anyone can:
- Open browser DevTools and modify the JavaScript
- Use curl/Postman to send arbitrary HTTP requests
- Disable JavaScript entirely

The backend must validate everything again.

### Why JWT payloads are readable
A JWT's payload is Base64-encoded, not encrypted. Anyone with the token can decode it. Never store secrets (passwords, API keys, personal data) in a JWT.

### Access token expiration
JWTs should have short lifetimes (15-30 minutes) so that a stolen token is only useful for a limited time.

### Refresh token purpose
A refresh token is a longer-lived credential used to obtain new access tokens without asking the user to log in again. It should be stored in an HttpOnly cookie (not accessible to JavaScript).

### HttpOnly cookies
Cookies that JavaScript cannot read. If you store the refresh token in an HttpOnly cookie, an XSS attack cannot steal it.

### Secure cookie flag
Tells the browser to only send the cookie over HTTPS. Never send it over HTTP.

### SameSite behavior
`SameSite=Lax` or `SameSite=Strict` prevents the cookie from being sent on cross-site requests, mitigating CSRF attacks.

### CSRF (Cross-Site Request Forgery)
An attacker tricks your browser into making a request to Secret Signal's backend while you're logged in. Mitigations:
- SameSite cookies
- CSRF tokens (for cookie-based auth)
- The OAuth `state` parameter (prevents CSRF on the callback)

### XSS (Cross-Site Scripting)
An attacker injects malicious JavaScript into a page. If the auth token is in localStorage, the injected script can steal it. If the token is in an HttpOnly cookie, it's safe.

### CORS (Cross-Origin Resource Sharing)
During development:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

These are different origins (different ports). The browser blocks cross-origin requests by default. CORS headers tell the browser it's OK.

Configuration in `main.py`:
```python
allow_origins=["http://localhost:5173"]
```

If you use cookies for auth, you MUST use a specific origin (not `*`) and set `allow_credentials=True`.

### OAuth state parameter
A random value your backend generates before redirecting to Google. When Google redirects back, you verify the state matches. This prevents an attacker from forging a callback request.

### OIDC nonce
Like `state`, but specifically for OpenID Connect. Prevents replay attacks on the ID token.

### Account linking risks
If a user signs up with email/password (creating User A), then later tries to "Continue with Google" using a different email, what happens? Does it create User B or link to User A? This needs careful design to prevent account takeover.

### Email normalization
Always lowercase emails before storage and comparison. `Alice@Example.com` and `alice@example.com` should be the same user.

### Rate limiting
Login attempts should be rate-limited (e.g., 5 attempts per minute per IP). Prevents brute-force password guessing.

### Generic login errors
Always return "Invalid email or password" instead of "User not found" or "Wrong password". The latter helps attackers enumerate valid emails.

### Secrets in environment variables
Never hardcode secrets in source code. Use `.env` files (gitignored) or environment variables.

### Why Google client secret must never be in the React bundle
Vite variables prefixed with `VITE_` are bundled into JavaScript files served to the browser. Anyone can view them. The Google client secret would be exposed to every visitor.

---

## 21. Token strategy trade-offs

| Strategy | How it works | Pros | Cons |
|---|---|---|---|
| **Short-lived access token only** | Frontend stores JWT, sends in Authorization header. Token expires in 15-30 min. | Simple to implement. No server-side session storage. | User must log in again every 30 min. No way to revoke tokens server-side (except changing the secret key). |
| **Access + refresh token** | Access token (15 min) + refresh token (7 days). Frontend stores access in memory, refresh in localStorage. | Refresh token can be revoked server-side. Better UX (no frequent logins). | More complex. Refresh token in localStorage is XSS-vulnerable. |
| **Access token + HttpOnly refresh cookie** | Refresh token stored in an HttpOnly, Secure, SameSite cookie. JavaScript can't read it. | XSS can't steal the refresh token. Best security of the JS-frontend options. | Requires careful CORS setup. Backend needs a `/refresh` endpoint. Slightly more complex. |
| **Server-side sessions** | Session ID stored in cookie. All session data on the server (Redis). | Easy to revoke. No JWT complexity. | Requires stateful storage. Harder to scale horizontally (but Redis solves this). |

**Recommendation for Secret Signal:** Start with **short-lived access token + HttpOnly refresh cookie** (strategy 3). It's secure, teaches the important concepts, and works well for a game where sessions are relatively short.

---

## 22. Alembic setup guide

Alembic is already in `pyproject.toml` as a dependency. You need to initialize it:

```bash
cd backend
pip install -e ".[dev]"
alembic init migrations
```

This creates a `migrations/` directory and an `alembic.ini` file.

Edit `alembic.ini` to point to your database:

```
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/secret_signal
```

Edit `migrations/env.py` to import your models' metadata:

```python
from app.db.base import Base
target_metadata = Base.metadata

# Import all models so they register on Base.metadata
from app.users.models import User  # noqa: F401
from app.auth.models import AuthIdentity  # noqa: F401
```

Then, after defining your models:

```bash
# Generate a migration
alembic revision --autogenerate -m "create users table"

# ALWAYS inspect the generated file in migrations/versions/
# Autogenerate is helpful but not perfect

# Apply the migration
alembic upgrade head

# Verify in PostgreSQL
psql -h localhost -U postgres -d secret_signal -c "\dt"
psql -h localhost -U postgres -d secret_signal -c "\d users"
```

---

## 23. Testing plan

### Frontend (if testing framework is configured)

**Signup form:**
- Shows validation errors for empty fields
- Shows password mismatch error
- Disables submit button during submission
- Shows server error on API failure

**Login form:**
- Shows validation errors for empty fields
- Shows server error on API failure
- Mode switch toggles between login/signup

**AuthPage:**
- Renders login mode by default
- Toggles to signup mode
- Navigates after successful auth

### Backend (to write as you implement)

**POST /signup:**
- Successful signup returns 201 with user + token
- Duplicate email returns 409
- Duplicate username returns 409
- Invalid email returns 422
- Weak password returns 422
- Password hash is not returned in response
- Password hash != plaintext password

**POST /login:**
- Successful login returns 200 with user + token
- Wrong password returns 401
- Nonexistent user returns 401 (same generic message)
- Inactive user returns 403

**GET /me:**
- Valid token returns user data
- Missing token returns 401
- Expired token returns 401
- Invalid token returns 401

**Google OAuth:**
- Successful callback creates user + identity
- Successful callback returns auth response
- Returning user is identified by `provider_subject`
- Invalid state parameter returns 401
- Invalid Google response returns 401

---

## Implementation Order Checklist

> **Your turn.** Implement each piece in this order.

1. Understand the `users` table design (read `users/models.py`)
2. Create the SQLAlchemy `User` model (implement `users/models.py`)
3. Create the `AuthIdentity` model for OAuth linking
4. Set up Alembic (run `alembic init migrations`, configure `env.py`)
5. Generate and inspect the migration (`alembic revision --autogenerate`)
6. Start PostgreSQL (`docker compose up -d postgres`)
7. Apply the migration (`alembic upgrade head`)
8. Verify the table in PostgreSQL (`psql` or `\dt`)
9. Implement user repository methods (`users/repository.py`)
10. Learn password hashing with passlib (read `auth/security.py`, then implement)
11. Implement signup in `auth/service.py`
12. Test signup manually (curl or FastAPI docs at `/docs`)
13. Implement password verification in `auth/security.py`
14. Implement login in `auth/service.py`
15. Implement JWT creation and decoding in `auth/security.py`
16. Implement `get_current_user` dependency in `auth/dependencies.py`
17. Implement `GET /auth/me`
18. Connect frontend signup form to real API
19. Connect frontend login form to real API
20. Add logout (clear token on frontend)
21. Learn Google OAuth (read `auth/oauth/google.py`)
22. Implement Google login backend
23. Implement Google callback backend
24. Add authentication tests

---

**Reference files:**

| File | Purpose |
|---|---|
| `frontend/.../auth/pages/AuthPage.tsx` | Auth page with mode toggle |
| `frontend/.../auth/components/LoginForm.tsx` | Login form UI + validation |
| `frontend/.../auth/components/SignupForm.tsx` | Signup form UI + validation |
| `frontend/.../auth/services/authApi.ts` | API service boundary (stubs) |
| `frontend/.../auth/validation/authValidation.ts` | Centralised validation rules |
| `backend/app/auth/router.py` | API route stubs |
| `backend/app/auth/schemas.py` | Request/response schemas (stubs) |
| `backend/app/auth/service.py` | Business logic skeleton |
| `backend/app/auth/security.py` | Hashing + JWT stubs |
| `backend/app/auth/dependencies.py` | Auth dependency skeleton |
| `backend/app/auth/README.md` | This document |
