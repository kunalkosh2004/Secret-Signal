# Secret Signal Backend --- Authentication Progress

This document summarizes the backend authentication work completed so
far for the **Secret Signal** project.

## 1. Backend and Database Setup

The FastAPI backend is running from the `backend` directory with:

``` bash
python3 -m uvicorn app.main:app --reload
```

The application currently runs at:

``` text
http://127.0.0.1:8000
```

The PostgreSQL database runs in Docker.

Current development database configuration:

``` text
Database: secret_signal
User: postgres
Host: localhost
Port: 5432
```

The database connection uses SQLAlchemy's async PostgreSQL driver:

``` text
postgresql+asyncpg://...
```

Database connectivity was tested successfully using an async SQLAlchemy
connection and `SELECT 1`.

The PostgreSQL container can be accessed with:

``` bash
docker exec -it secret_signal_postgres \
  psql -U postgres -d secret_signal
```

Useful PostgreSQL commands:

``` sql
\dt
\d users
\d auth_identities

SELECT id, username, email, is_active, is_verified, created_at
FROM users
ORDER BY id;

SELECT id, user_id, provider, provider_subject, provider_email
FROM auth_identities
ORDER BY id;

\q
```

------------------------------------------------------------------------

## 2. Application Configuration

The project uses a Pydantic `Settings` class in:

``` text
app/core/config.py
```

Configuration currently includes:

-   `DATABASE_URL`
-   `secret_key`
-   `algorithm`
-   `access_token_expire_minutes`
-   `google_client_id`
-   `google_client_secret`
-   `google_redirect_uri`
-   `google_link_redirect_uri`
-   `frontend_url`
-   `redis_url`
-   `debug`

Sensitive values such as the JWT secret, Google client ID, and Google
client secret should be stored in `.env`, not committed in source code.

Example:

``` env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/secret_signal
secret_key=YOUR_SECRET_KEY
google_client_id=YOUR_GOOGLE_CLIENT_ID
google_client_secret=YOUR_GOOGLE_CLIENT_SECRET
google_redirect_uri=http://localhost:8000/api/v1/auth/google/callback
google_link_redirect_uri=http://localhost:8000/api/v1/auth/google/link/callback
redis_url=redis://localhost:6379/0
```

The `.env` file should be included in `.gitignore`.

------------------------------------------------------------------------

## 3. SQLAlchemy Base and Async Session

The shared SQLAlchemy declarative base is defined in:

``` text
app/db/base.py
```

The async engine, session factory, and `get_db` dependency are defined
in:

``` text
app/db/session.py
```

The database session module was imported and tested successfully.

------------------------------------------------------------------------

## 4. User Model

The `users` table is represented by:

``` text
app/users/models.py
```

The model includes fields equivalent to:

-   `id`
-   `username`
-   `email`
-   `password_hash`
-   `is_active`
-   `is_verified`
-   `created_at`
-   `updated_at`

Important design rule:

> Plaintext passwords are never stored. Only password hashes are stored
> in `password_hash`.

Google-only users may have a null `password_hash`.

The User repository was tested successfully for:

-   create user
-   get by ID
-   get by email
-   get by username

The repository test successfully inserted and queried a test user from
PostgreSQL.

------------------------------------------------------------------------

## 5. User and Authentication Schemas

User response schemas were implemented in:

``` text
app/users/schemas.py
```

Password hashes and internal database fields are not returned in API
responses.

Authentication schemas were implemented in:

``` text
app/auth/schemas.py
```

The main request/response contracts include:

### SignupRequest

Contains:

-   `username`
-   `email`
-   `password`

### LoginRequest

Contains:

-   `email`
-   `password`

### TokenResponse

Contains:

-   `access_token`
-   `token_type`
-   `user`

Emails are normalized to lowercase in the authentication service.

------------------------------------------------------------------------

## 6. Password Hashing and JWT Authentication

Security utilities are implemented in:

``` text
app/auth/security.py
```

The module provides:

``` text
hash_password()
verify_password()
create_access_token()
decode_access_token()
```

Password hashing uses bcrypt/passlib.

JWT tokens use the configured secret key and algorithm, currently HS256.

JWT payloads use the `sub` claim for the local user ID and include an
expiration time.

A JWT round-trip test was completed successfully:

``` text
create token → decode token → recover payload
```

Because the local environment uses Python 3.9, type annotations were
adjusted to avoid Python 3.10-only union syntax such as:

``` python
int | None
```

where necessary.

------------------------------------------------------------------------

## 7. Authentication Service

Authentication business logic is implemented in:

``` text
app/auth/service.py
```

### Signup flow

The signup service performs:

``` text
normalize email
    ↓
check email uniqueness
    ↓
check username uniqueness
    ↓
hash password
    ↓
create user
    ↓
create JWT
    ↓
return TokenResponse
```

### Login flow

The login service performs:

``` text
normalize email
    ↓
find user by email
    ↓
verify password
    ↓
create JWT
    ↓
return TokenResponse
```

OAuth-only accounts with no password hash cannot log in using the
password login endpoint.

------------------------------------------------------------------------

## 8. Application Exceptions

Custom application exceptions are defined in:

``` text
app/core/exceptions.py
```

Implemented exception types include:

  Exception               HTTP Status
  --------------------- -------------
  `NotFoundError`                 404
  `ConflictError`                 409
  `UnauthorizedError`             401
  `ForbiddenError`                403
  `ValidationError`               422

A global FastAPI exception handler was added to:

``` text
app/main.py
```

The handler converts `AppException` subclasses into JSON HTTP responses.

------------------------------------------------------------------------

## 9. Authentication Dependencies

Authentication dependencies are implemented in:

``` text
app/auth/dependencies.py
```

The project uses bearer-token authentication.

The main dependency flow is:

``` text
Authorization: Bearer <JWT>
        ↓
OAuth2PasswordBearer
        ↓
decode_access_token()
        ↓
read sub claim
        ↓
load user from database
        ↓
return current User
```

The project also has active-user authorization logic to reject inactive
users.

The `/me` endpoint uses the authenticated user dependency.

------------------------------------------------------------------------

## 10. Authentication Routes

Authentication routes are defined in:

``` text
app/auth/router.py
```

The router prefix is:

``` text
/api/v1/auth
```

Implemented or wired routes include:

``` text
POST /signup
POST /login
POST /logout
GET  /me
GET  /google/login
GET  /google/callback
GET  /google/link
GET  /google/link/callback
```

### Logout behavior

The current system uses short-lived stateless JWTs without a
refresh-token store or access-token blacklist.

Therefore logout currently means:

``` text
frontend deletes access token
    ↓
frontend clears authenticated state
    ↓
frontend redirects user
```

The backend logout route returns a successful response, but an
already-issued JWT remains valid until expiration.

------------------------------------------------------------------------

## 11. Alembic Database Migrations

Alembic was installed and initialized.

Created structure:

``` text
alembic/
├── versions/
├── env.py
├── README
└── script.py.mako

alembic.ini
```

`alembic/env.py` was configured for:

-   async SQLAlchemy
-   the application database URL
-   shared `Base.metadata`
-   User model registration
-   AuthIdentity model registration

An initial baseline migration was created:

``` text
08bd7494cde1
```

Because the `users` table already existed and matched the SQLAlchemy
model, the initial migration was empty and the database was stamped to
the revision.

The workflow from now on is:

``` text
change SQLAlchemy model
        ↓
python3 -m alembic revision --autogenerate -m "description"
        ↓
review migration
        ↓
python3 -m alembic upgrade head
```

------------------------------------------------------------------------

## 12. AuthIdentity Model

The Google OAuth identity model is defined in:

``` text
app/auth/models.py
```

The `auth_identities` table contains:

-   `id`
-   `user_id`
-   `provider`
-   `provider_subject`
-   `provider_email`
-   `created_at`

The table has:

-   foreign key from `user_id` to `users.id`
-   cascade delete behavior
-   index on `user_id`
-   unique constraint on `(provider, provider_subject)`

The `provider_subject` stores the OpenID Connect `sub` claim.

The Google `sub` is used for identity linking instead of relying on
email because it is the stable provider identifier.

The migration for the auth identity table was generated and applied
successfully.

------------------------------------------------------------------------

## 13. Auth Identity Repository

The auth repository is implemented in:

``` text
app/auth/repository.py
```

Implemented operations:

``` text
get_identity()
create_identity()
```

The repository was tested against PostgreSQL successfully.

Tested flow:

``` text
existing local user
        ↓
create Google AuthIdentity
        ↓
commit
        ↓
query by provider + provider_subject
        ↓
retrieve linked user ID
```

The successful test created an identity and retrieved it correctly.

------------------------------------------------------------------------

## 14. Google OAuth Configuration

Google OAuth credentials were created through Google Cloud.

The OAuth client type is:

``` text
Web application
```

Authorized redirect URIs include the login callback and link callback:

``` text
http://localhost:8000/api/v1/auth/google/callback
http://localhost:8000/api/v1/auth/google/link/callback
```

The client ID and client secret are loaded from environment variables.

------------------------------------------------------------------------

## 15. Google OAuth Schemas

OAuth provider schemas are defined in:

``` text
app/auth/oauth/schemas.py
```

`GoogleUserInfo` contains:

-   `sub`
-   `email`
-   `email_verified`
-   `name`
-   `picture`

The schema was implemented and tested.

------------------------------------------------------------------------

## 16. Google Authorization URL

Google OAuth logic is implemented in:

``` text
app/auth/oauth/google.py
```

`build_authorization_url()` builds the Google authorization URL with:

-   client ID
-   redirect URI
-   response type `code`
-   scopes `openid email profile`
-   CSRF state
-   offline access settings
-   consent prompt

The Google login route generates a cryptographically random state and
redirects the browser to Google.

The redirect flow was tested successfully.

------------------------------------------------------------------------

## 17. Google Code Exchange and ID Token Verification

The project uses:

-   `httpx`
-   `google-auth`

The OAuth callback logic:

``` text
authorization code
        ↓
POST to Google token endpoint
        ↓
receive ID token
        ↓
verify signed ID token
        ↓
validate audience and token claims
        ↓
extract verified Google user information
```

The Google verification module imported successfully.

The local environment emitted warnings because:

-   Python 3.9 is end-of-life
-   the system Python SSL module uses an older LibreSSL version

These warnings did not block the current development flow, but upgrading
to a modern Python environment is recommended.

------------------------------------------------------------------------

## 18. Google Login Account Policy

The chosen policy is:

> Do not automatically link a Google account to an existing password
> account merely because the emails match.

Current intended behavior:

``` text
Google identity already linked
        ↓
log in linked user


Google identity not linked
        ↓
email belongs to existing local account?
        ├── yes → reject Google login; user must log in normally first
        └── no  → create OAuth-only user and Google identity
```

This avoids automatic account linking based only on matching email.

------------------------------------------------------------------------

## 19. Unique Username Generation for OAuth Users

A helper was added to generate a unique username from a Google email.

Example:

``` text
kunal@example.com
        ↓
try kunal
        ↓ occupied
try kunal_1
        ↓ occupied
try kunal_2
        ↓ available
```

The helper respects the 30-character username limit.

------------------------------------------------------------------------

## 20. Google Callback Service

The Google callback service handles:

``` text
verify Google authorization code
        ↓
get verified GoogleUserInfo
        ↓
find AuthIdentity by Google sub
        ↓
if identity exists:
    load linked user
    issue application JWT

if identity does not exist:
    check local email collision
    reject if local account already exists
    otherwise generate username
    create OAuth-only user
    create AuthIdentity
    issue application JWT
```

The callback route was wired and the browser OAuth flow was tested.

------------------------------------------------------------------------

## 21. Redis Setup

Redis is running in Docker and was tested with:

``` text
PONG
```

Python Redis support uses the async Redis client.

Redis configuration is located in:

``` text
app/core/redis.py
```

The Redis connection was tested successfully by:

``` text
PING
SET key
GET key
```

------------------------------------------------------------------------

## 22. OAuth State Protection

OAuth login state is stored in Redis with a short expiration time.

Flow:

``` text
/google/login
        ↓
generate random state
        ↓
store oauth_state:<state> in Redis
        ↓
TTL: 5 minutes
        ↓
redirect to Google


/google/callback
        ↓
receive code + state
        ↓
atomically consume Redis state
        ↓
missing → reject with 401
found   → continue OAuth flow
```

The state helper was tested:

``` text
First check: True
Second check: False
```

This proves that the OAuth state is single-use.

The unused `state` parameter was later removed from lower-level Google
token verification because state verification belongs at the callback
boundary before the service processes the code.

------------------------------------------------------------------------

## 23. Explicit Google Account Linking

The chosen account-linking policy requires the user to log in first.

The intended flow is:

``` text
password login
        ↓
authenticated local user
        ↓
GET /api/v1/auth/google/link
        ↓
store user ID with one-time state in Redis
        ↓
Google authorization
        ↓
GET /api/v1/auth/google/link/callback
        ↓
consume link state
        ↓
recover initiating user ID
        ↓
verify Google identity
        ↓
validate linking rules
        ↓
create AuthIdentity
```

Redis link-state storage maps:

``` text
google_link_state:<state> → user_id
```

with a short TTL and single-use consumption.

The link state helpers were tested successfully:

``` text
First: 2
Second: None
```

The Google link-start route requires the authenticated user dependency.

The Google link callback service checks:

-   Google identity is not already linked
-   local user still exists
-   Google email matches the logged-in user's local account email
-   identity is then created

Separate redirect URI handling was added so Google login and Google
account linking can use different callbacks.

------------------------------------------------------------------------

## 24. Current Main Application Structure

Relevant backend structure:

``` text
backend/
├── alembic/
│   ├── versions/
│   └── env.py
├── alembic.ini
├── app/
│   ├── auth/
│   │   ├── oauth/
│   │   │   ├── google.py
│   │   │   └── schemas.py
│   │   ├── dependencies.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   └── service.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── redis.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── users/
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── service.py
│   └── main.py
└── .env
```

------------------------------------------------------------------------

## 25. Current Authentication Status

Completed so far:

-   PostgreSQL Docker setup
-   async SQLAlchemy database connection
-   shared declarative Base
-   async session dependency
-   User model
-   User schemas
-   Auth schemas
-   password hashing
-   password verification
-   JWT creation
-   JWT decoding
-   User repository
-   signup service
-   login service
-   signup route
-   login route
-   logout route behavior
-   authenticated `/me`
-   active-user dependency
-   application exception hierarchy
-   FastAPI exception handler
-   Alembic setup
-   Alembic baseline
-   AuthIdentity model
-   AuthIdentity migration
-   Auth identity repository
-   Google OAuth credentials
-   Google user schema
-   Google authorization URL
-   Google login redirect
-   authorization-code exchange
-   Google ID-token verification
-   Google callback service
-   Google callback route
-   Redis connection
-   OAuth state storage
-   one-time OAuth state consumption
-   explicit Google link-state storage
-   Google link-start route
-   Google link callback service
-   Google link callback route

------------------------------------------------------------------------

## 26. Next Planned Work

The next planned security improvement is a one-time frontend OAuth
handoff flow.

Instead of returning the application JWT directly in the browser or
placing it in a URL, the intended design is:

``` text
Google callback
        ↓
backend creates application JWT
        ↓
backend creates random one-time handoff code
        ↓
Redis stores:
oauth_handoff:<code> → JWT
TTL: about 60 seconds
        ↓
backend redirects frontend to:
http://localhost:5173/auth/callback?code=<one-time-code>
        ↓
frontend exchanges code with backend
        ↓
backend consumes code exactly once
        ↓
backend returns authentication response
```

The Redis handoff helpers were the next planned implementation step:

``` text
create_oauth_handoff()
consume_oauth_handoff()
```

After that, remaining work includes:

-   frontend OAuth callback page
-   one-time code exchange endpoint
-   safer browser token storage decision
-   refresh-token strategy if needed
-   token rotation/revocation if refresh tokens are added
-   OAuth error handling and user-friendly frontend redirects
-   tests for signup, login, `/me`, OAuth login, state replay, and
    account linking
-   Python environment upgrade from Python 3.9
-   production configuration and deployment hardening

------------------------------------------------------------------------

## 27. Useful Development Commands

Start backend:

``` bash
python3 -m uvicorn app.main:app --reload
```

Check Alembic revision:

``` bash
python3 -m alembic current
```

Show migration heads:

``` bash
python3 -m alembic heads
```

Generate migration:

``` bash
python3 -m alembic revision --autogenerate -m "description"
```

Apply migrations:

``` bash
python3 -m alembic upgrade head
```

Open PostgreSQL:

``` bash
docker exec -it secret_signal_postgres \
  psql -U postgres -d secret_signal
```

Check Redis:

``` bash
docker exec -it secret_signal_redis redis-cli ping
```

Start Google login flow:

``` text
http://localhost:8000/api/v1/auth/google/login
```

Health check:

``` text
http://localhost:8000/health
```

------------------------------------------------------------------------

## 28. Important Security Notes

1.  Never store plaintext passwords.
2.  Never commit `.env`.
3.  Keep JWT secrets and OAuth client secrets outside source code.
4.  Do not trust OAuth callback claims without ID-token verification.
5.  Use Google `sub`, not email, as the stable provider identity.
6.  OAuth state must be short-lived and single-use.
7.  Do not automatically link accounts based only on matching email.
8.  Avoid placing long-lived access tokens in URL query parameters.
9.  Review every Alembic migration before applying it.
10. Upgrade the development environment from Python 3.9 before
    production deployment.
