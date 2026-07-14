# Secret Signal — Deployment Guide (Zero to Deployed)

This guide assumes you know **nothing** about deployment. Every term is explained.
Every step is numbered. Every click is described.

By the end, your game will be live on the internet.

---

## Table of Contents

1. [What "Deploy" Means](#1-what-deploy-means)
2. [What We're Building](#2-what-were-building)
3. [Accounts You Need](#3-accounts-you-need)
4. [Prerequisites](#4-prerequisites)
5. [Step 1: Push Code to GitHub](#5-step-1-push-code-to-github)
6. [Step 2: Set Up the Database (Neon)](#6-step-2-set-up-the-database-neon)
7. [Step 3: Set Up Redis (Upstash)](#7-step-3-set-up-redis-upstash)
8. [Step 4: Deploy the Backend (Railway)](#8-step-4-deploy-the-backend-railway)
9. [Step 5: Run Database Migrations](#9-step-5-run-database-migrations)
10. [Step 6: Deploy the Frontend (Vercel)](#10-step-6-deploy-the-frontend-vercel)
11. [Step 7: Connect Everything](#11-step-7-connect-everything)
12. [Step 8: Test Your Deployment](#12-step-8-test-your-deployment)
13. [Step 9: Set Up Google OAuth (Optional)](#13-step-9-set-up-google-oauth-optional)
14. [Understanding What Happened](#14-understanding-what-happened)
15. [How to Make Changes After Deploying](#15-how-to-make-changes-after-deploying)
16. [Troubleshooting](#16-troubleshooting)
17. [Cost Summary](#17-cost-summary)
18. [What Each Service Does](#18-what-each-service-does)

---

## 1. What "Deploy" Means

When you run the game on your laptop:
- **You** are the server
- **Your** PostgreSQL database lives in your `docker` container
- **Only you** can access it at `localhost:5173`

When you **deploy**:
- The code lives on **someone else's computer** (a "server") on the internet
- **Anyone in the world** can visit your URL and play
- Your database lives in **the cloud** (not on your laptop)
- You don't have to keep your laptop open for it to work

Think of it like this:
```
LOCAL (your laptop)          DEPLOYED (the internet)
┌──────────────┐              ┌──────────────┐
│ You run it   │     →→→      │ Cloud runs it │
│ localhost    │              │ yourgame.com  │
│ Only you     │              │ Everyone      │
│ Stops when   │              │ Runs 24/7     │
│ you close it │              │ Never stops   │
└──────────────┘              └──────────────┘
```

---

## 2. What We're Building

Secret Signal has **4 parts** that need to be deployed separately:

```
┌─────────────────────────────────────────────────────┐
│                    INTERNET                           │
│                                                       │
│   ③ Frontend          ④ Backend                       │
│   (React app)         (FastAPI + WebSocket)           │
│   lives on Vercel     lives on Railway                │
│   yourgame.vercel.app api.up.railway.app              │
│                                                       │
│         ① Database                ② Redis             │
│         (PostgreSQL)              (Cache/State)       │
│         lives on Neon             lives on Upstash    │
│         stores users, games       stores sessions,    │
│         messages, events          presence, timers    │
└─────────────────────────────────────────────────────┘
```

| Part | What It Does | Where It Lives | Free? |
|------|-------------|----------------|-------|
| Frontend | The website players see | Vercel | Yes (Hobby plan) |
| Backend | The brain (game logic, API) | Railway | $5/month |
| Database | Stores all data permanently | Neon | Yes (free tier) |
| Redis | Fast temporary storage | Upstash | Yes (~$0/month) |

**Total cost: $5/month** (only Railway charges anything)

---

## 3. Accounts You Need

Create accounts at these 4 websites. Use your GitHub account to sign up for all of them:

| Website | URL | Why |
|---------|-----|-----|
| **GitHub** | github.com | Hosts your code |
| **Vercel** | vercel.com | Hosts the frontend |
| **Railway** | railway.app | Hosts the backend |
| **Neon** | neon.tech | PostgreSQL database |
| **Upstash** | upstash.com | Redis cache |

**How to sign up:**
1. Go to each website
2. Click "Sign Up" or "Get Started"
3. Click "Continue with GitHub" (easiest option — links to your GitHub account)
4. Authorize the connection
5. You're in

---

## 4. Prerequisites

Make sure you have these installed on your computer:

```bash
# Check if you have Git
git --version
# Should print something like: git version 2.x.x

# Check if you have Node.js
node --version
# Should print something like: v18.x.x or v20.x.x

# Check if you have Python
python3 --version
# Should print something like: Python 3.12.x
```

If any of these are missing:
- **Git**: Download from https://git-scm.com
- **Node.js**: Download from https://nodejs.org (LTS version)
- **Python**: Download from https://python.org

---

## 5. Step 1: Push Code to GitHub

Your code needs to be on GitHub so Vercel and Railway can access it.

### 5a. Create a GitHub Repository

1. Go to https://github.com
2. Click the **+** icon in the top right → **New repository**
3. Name it: `secret-signal`
4. Make it **Public** (Vercel free tier requires public repos)
5. **DO NOT** check "Add a README" (you already have one)
6. Click **Create repository**

### 5b. Push Your Code

Open a terminal in the project folder and run these commands **one at a time**:

```bash
# Go to the project folder (if not already there)
cd /Users/kunalkoshta/Desktop/Secret-Signal

# Tell Git about the new remote repository
git remote add origin https://github.com/YOUR_USERNAME/secret-signal.git

# Push all code to GitHub
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

**If you get an error** about the remote already existing, run:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/secret-signal.git
```

### 5c. Verify

Go to `https://github.com/YOUR_USERNAME/secret-signal` — you should see all your files there.

---

## 6. Step 2: Set Up the Database (Neon)

Neon gives you a PostgreSQL database in the cloud for free.

### Step by Step:

1. Go to https://neon.tech and sign in with GitHub

2. Click **Create a project**

3. Settings:
   - **Project name**: `secret-signal`
   - **Database name**: `secret_signal` (keep the default)
   - **Region**: Choose the one closest to you (e.g., `US East`)
   - Click **Create project**

4. You'll see a **Connection string** that looks like:
   ```
   postgresql://neondb_owner:abc123xyz@ep-cool-bird-123456.us-east-1.aws.neon.tech/secret_signal?sslmode=require
   ```

5. **Copy this entire string** and save it somewhere safe (like a text file). You'll need it soon.

6. Click **Pools** in the left sidebar → Make sure **Connection pooling** is **enabled** (it should be by default)

7. Go back to the **Dashboard** → Your database is now running

### What Just Happened?

Neon created a PostgreSQL database for you:
- It lives in the cloud (AWS servers)
- It stores all your game data permanently
- It has a URL you can connect to from anywhere
- The `?sslmode=require` at the end means the connection is encrypted (secure)
- It has 512MB of free storage (plenty for an MVP)

---

## 7. Step 3: Set Up Redis (Upstash)

Upstash gives you Redis in the cloud, pay-per-request (very cheap).

### Step by Step:

1. Go to https://upstash.com and sign in with GitHub

2. Click **Create Database**

3. Settings:
   - **Name**: `secret-signal`
   - **Region**: Same region you chose for Neon (important for speed)
   - **Type**: Select **Regional**
   - Click **Create**

4. You'll see a page with connection details. Find:
   - **Redis URL** (looks like: `rediss://default:abc123@apn1-xxxx.upstash.io:6379`)
   
5. **Copy the Redis URL** and save it with the Neon connection string.

6. Scroll down and note:
   - **REST URL**: You'll see something like `https://xxxx.upstash.io`
   - **REST Token**: A long random string

### What Just Happened?

Upstash created a Redis instance:
- It's serverless (no server to manage)
- It runs 24/7 in the cloud
- You pay only for what you use (~$0-5/month)
- It stores temporary data: sessions, rate limits, WebSocket presence

---

## 8. Step 4: Deploy the Backend (Railway)

Railway hosts your FastAPI backend and keeps it running 24/7.

### Step by Step:

1. Go to https://railway.app and sign in with GitHub

2. Click **New Project**

3. Select **Deploy from GitHub Repo**

4. Find and click on your `secret-signal` repository

5. Railway will detect it's a monorepo. You'll see a question about which service to deploy. **Don't select anything yet** — we need to tell Railway to use the Dockerfile.

6. In your project dashboard, click **+ New** → **Service** → **GitHub Repo** → select `secret-signal` again

7. Now click on this new service → **Settings** tab

8. Under **Build**:
   - **Builder**: Select **Dockerfile**
   - **Dockerfile Path**: `infrastructure/docker/Dockerfile.backend`
   - Click **Save**

9. Under **Deploy**:
   - Click **Deploy** — this builds and starts your backend

10. While it builds, set up environment variables (next step)

### Setting Environment Variables

Still in Railway, click on your backend service → **Variables** tab:

Add each of these variables one by one (click **New Variable** for each):

```
DATABASE_URL = postgresql+asyncpg://neondb_owner:YOUR_PASSWORD@ep-xxx.us-east-1.aws.neon.tech/secret_signal?sslmode=require
```

**Wait!** You need to change the connection string format:
- Neon gives you: `postgresql://...` (standard format)
- Our app needs: `postgresql+asyncpg://...` (async format)
- Just add `+asyncpg` after `postgresql`

So change:
```
postgresql://neondb_owner:abc123@ep-cool-bird.us-east-1.aws.neon.tech/secret_signal?sslmode=require
```
To:
```
postgresql+asyncpg://neondb_owner:abc123@ep-cool-bird.us-east-1.aws.neon.tech/secret_signal?sslmode=require
```

Add these variables:

| Variable | Value | Where to get it |
|----------|-------|----------------|
| `DATABASE_URL` | `postgresql+asyncpg://...?sslmode=require` | Neon (with `+asyncpg` added) |
| `REDIS_URL` | `rediss://default:...@...upstash.io:6379` | Upstash |
| `SECRET_KEY` | Run this in your terminal: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` | Generated locally |
| `ENVIRONMENT` | `production` | Type it in |
| `LOG_LEVEL` | `info` | Type it in |
| `FRONTEND_URL` | Leave blank for now (we'll fill this in Step 7) | — |
| `DEBUG` | `false` | Type it in |

11. After adding all variables, Railway will automatically **redeploy** your backend.

12. Wait for the deploy to finish (green checkmark). Click **Logs** to see if it started successfully.

13. Click **Settings** → **Networking** → **Generate Domain**

14. Railway gives you a URL like: `secret-signal-backend-production.up.railway.app`

15. **Copy this URL** — you'll need it for the frontend.

### What Just Happened?

Railway:
1. Downloaded your code from GitHub
2. Built the Docker image (installed Python, dependencies)
3. Started your FastAPI backend
4. Gave it a public URL anyone can visit
5. Your backend is now running 24/7 in the cloud

---

## 9. Step 5: Run Database Migrations

Your database is empty. We need to create all the tables (users, rooms, games, etc.).

### Option A: From Railway (Recommended)

1. In Railway, click on your backend service
2. Click the **Shell** tab (or **Run** → **Shell**)
3. Type this command and press Enter:

```bash
alembic upgrade head
```

4. You should see output like:
   ```
   INFO  [alembic] Running upgrade ... -> 08bd7494cde1, initial users table
   INFO  [alembic] Running upgrade 08bd7494cde1 -> ...
   ...
   ```

5. If you see no errors, the tables are created!

### Option B: From Your Computer

If the shell doesn't work, run this from your computer:

```bash
# Set the DATABASE_URL to your Neon connection string
export DATABASE_URL="postgresql+asyncpg://neondb_owner:abc123@ep-xxx.us-east-1.aws.neon.tech/secret_signal?sslmode=require"

# Run migrations
cd backend
alembic upgrade head
```

### What Just Happened?

Alembic read all 20 migration files and created every database table:
- `users` — stores user accounts
- `rooms` — stores game rooms
- `games` — stores game state
- `messages` — stores chat messages
- `votes` — stores player votes
- `missions` — stores missions
- `game_events` — stores all game events (for replay)
- ...and more

---

## 10. Step 6: Deploy the Frontend (Vercel)

Vercel hosts your React frontend and serves it to players.

### Step by Step:

1. Go to https://vercel.com and sign in with GitHub

2. Click **Add New...** → **Project**

3. Find and click on your `secret-signal` repository

4. Vercel will detect the project. **Important settings:**
   - **Framework Preset**: Vite
   - **Root Directory**: Click **Edit** and change to: `frontend/frontend`
   - **Build Command**: Should auto-detect as `npm run build`
   - **Output Directory**: Should auto-detect as `dist`

5. **Environment Variables** — Add these before clicking Deploy:

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://YOUR_RAILWAY_URL` (the Railway URL from Step 4, without trailing `/`) |
| `VITE_WS_URL` | `wss://YOUR_RAILWAY_URL/ws` (same URL but with `wss://` and `/ws` at the end) |

**Important:**
- If Railway URL is `secret-signal-backend-production.up.railway.app`
- Then `VITE_API_URL` = `https://secret-signal-backend-production.up.railway.app`
- And `VITE_WS_URL` = `wss://secret-signal-backend-production.up.railway.app/ws`
- Notice: `http` becomes `https`, `ws` becomes `wss`

6. Click **Deploy**

7. Wait for the build to finish (usually 1-2 minutes)

8. Vercel gives you a URL like: `secret-signal-xxx.vercel.app`

9. **Visit this URL** — your game should load!

### What Just Happened?

Vercel:
1. Downloaded your code from GitHub
2. Installed Node.js dependencies
3. Ran `vite build` to create optimized static files
4. Uploaded them to their global CDN (Content Delivery Network)
5. Your website is now accessible to anyone in the world
6. Every time you push to GitHub, Vercel auto-deploys

---

## 11. Step 7: Connect Everything

The frontend needs to know the backend URL. The backend needs to know the frontend URL. Let's connect them.

### Update Backend CORS

1. In Railway, go to your backend service → **Variables**

2. Update `FRONTEND_URL`:
   ```
   FRONTEND_URL = https://secret-signal-xxx.vercel.app
   ```
   (Use your actual Vercel URL)

3. Railway will auto-redeploy with the new setting

### Update Frontend API URL (if needed)

If you need to change the Vercel environment variables:

1. In Vercel, go to your project → **Settings** → **Environment Variables**
2. Update `VITE_API_URL` and `VITE_WS_URL` if your Railway URL changed
3. Click **Redeploy** to apply changes

### What Connected?

```
Player visits: https://secret-signal-xxx.vercel.app
                    │
                    ▼
        Vercel serves the React app
                    │
        Player clicks "Login"
                    │
                    ▼
        React sends POST to:
        https://api.up.railway.app/api/v1/auth/login
                    │
                    ▼
        Railway backend processes the request
                    │
            ┌───────┴───────┐
            ▼               ▼
        Neon Database    Upstash Redis
        (stores user)   (caches session)
```

---

## 12. Step 8: Test Your Deployment

Visit your Vercel URL and test everything:

### Test 1: Page Loads
- Visit `https://secret-signal-xxx.vercel.app`
- You should see the landing page
- No console errors (press F12 → Console tab)

### Test 2: Sign Up
- Click "Sign Up"
- Enter a username, email, and password
- Click submit
- You should be logged in

### Test 3: Create Room
- Click "Create Room"
- You should see a room with a 6-character code
- Copy the code

### Test 4: Open Another Browser Tab
- Open a new incognito/private window
- Visit the Vercel URL
- Sign up with a different email
- Enter the room code
- Both players should appear in the room

### Test 5: Play a Game
- Ready up both players
- Host starts the game
- You should see role assignments
- Chat messages should appear in real-time
- Complete a full game

### If Something Fails

Open browser console (F12 → Console) and look for red error messages. See [Troubleshooting](#16-troubleshooting) below.

---

## 13. Step 9: Set Up Google OAuth (Optional)

This lets users sign in with their Google account.

### Step by Step:

1. Go to https://console.cloud.google.com

2. Create a new project:
   - Click the project dropdown at the top
   - Click **New Project**
   - Name: `secret-signal`
   - Click **Create**

3. Enable the Google+ API:
   - Go to **APIs & Services** → **Library**
   - Search for "Google+ API" or "People API"
   - Click it → Click **Enable**

4. Create OAuth credentials:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth client ID**
   - If prompted, configure the OAuth consent screen first:
     - User type: **External**
     - App name: `Secret Signal`
     - Add your email as contact
     - Save and continue through the screens
   - Back to creating credentials:
     - Application type: **Web application**
     - Name: `Secret Signal`
     - Authorized redirect URIs: Add:
       ```
       https://YOUR_RAILWAY_URL/api/v1/auth/google/callback
       ```
     - Click **Create**

5. Copy the **Client ID** and **Client Secret**

6. In Railway → Backend service → Variables, add:
   ```
   GOOGLE_CLIENT_ID = your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET = your-secret
   GOOGLE_REDIRECT_URI = https://YOUR_RAILWAY_URL/api/v1/auth/google/callback
   ```

7. Railway auto-redeploys. Google sign-in should now work.

---

## 14. Understanding What Happened

### The Complete Flow

When a player visits your game and plays a full match:

```
1. Player opens https://secret-signal-xxx.vercel.app
   └─► Vercel serves the React app (static HTML/CSS/JS)

2. Player clicks "Sign Up"
   └─► React sends POST to https://api.up.railway.app/api/v1/auth/signup
   └─► Railway backend creates user in Neon database
   └─► Returns a JWT token

3. Player creates a room
   └─► Backend creates room in Neon, generates 6-char code
   └─► Returns room code

4. Player 2 joins the room via WebSocket
   └─► WebSocket connects to wss://api.up.railway.app/ws
   └─► Backend authenticates via JWT
   └─► Backend stores presence in Upstash Redis
   └─► Broadcasts room state to both players

5. Game starts
   └─► Backend assigns roles, stores in Neon
   └─► Backend starts Redis timer for phase duration
   └─► WebSocket broadcasts role assignments

6. Players chat during Interaction phase
   └─► Each message: WebSocket → Backend → Neon DB → broadcast to all
   └─► Backend evaluates missions, stores events for replay

7. Voting phase
   └─► Backend tallies votes, checks win condition
   └─► Stores result in Neon

8. Game over
   └─► Backend calculates scores, runs analytics
   └─► Generates replay timeline from event log
   └─► Frontend shows AI analysis page
```

### Where Everything Lives

| Data | Where | Why |
|------|-------|-----|
| User accounts | Neon (PostgreSQL) | Permanent, relational |
| Game state | Neon (PostgreSQL) | Permanent, queryable |
| Chat messages | Neon (PostgreSQL) | Permanent, searchable |
| Game events | Neon (PostgreSQL) | Permanent, for replay |
| JWT blacklist | Upstash (Redis) | Temporary, fast lookup |
| Rate limits | Upstash (Redis) | Temporary, fast |
| WebSocket presence | Upstash (Redis) | Temporary, fast |
| Game timers | Upstash (Redis) | TTL-based auto-expire |
| Frontend HTML/JS/CSS | Vercel (CDN) | Static, globally cached |
| Backend API | Railway (container) | Dynamic, compute |

---

## 15. How to Make Changes After Deploying

### Making Code Changes

```bash
# 1. Make changes to your code locally
# 2. Test locally first
cd backend && uvicorn app.main:app --reload
cd frontend/frontend && npm run dev

# 3. Commit and push
git add .
git commit -m "Description of what changed"
git push

# 4. Automatic deployment happens!
#    - Vercel auto-deploys the frontend (1-2 minutes)
#    - Railway auto-deploys the backend (2-3 minutes)
```

### Adding Database Migrations

If you changed a database model:

```bash
# 1. Create migration locally
cd backend
alembic revision --autogenerate -m "description of change"

# 2. Push the migration file
git add alembic/versions/
git commit -m "Add migration: description"
git push

# 3. Railway redeploys with new code
# 4. Run migration on Railway:
#    - Go to Railway → your service → Shell
#    - Run: alembic upgrade head
```

### Checking Logs

**Railway logs:**
1. Go to railway.app → your project → your service
2. Click **Logs** tab
3. See real-time output from your backend

**Vercel logs:**
1. Go to vercel.com → your project
2. Click **Logs** tab
3. See function invocations and errors

---

## 16. Troubleshooting

### "Application failed to start" on Railway

**Check logs.** Most common causes:
1. Missing environment variable — check all variables are set
2. DATABASE_URL format wrong — must be `postgresql+asyncpg://...`
3. SECRET_KEY missing — must be set

### "Connection refused" for database

- Make sure `DATABASE_URL` starts with `postgresql+asyncpg://` (not `postgresql://`)
- Make sure the Neon database is running (check Neon dashboard)
- Make sure `?sslmode=require` is at the end of the URL

### Frontend shows blank page

- Open browser console (F12)
- Look for errors — usually a wrong `VITE_API_URL`
- Make sure `VITE_API_URL` starts with `https://` (not `http://`)
- Make sure there's no trailing `/` at the end of `VITE_API_URL`

### "CORS error" in browser console

- The backend doesn't know about your frontend URL
- In Railway, set `FRONTEND_URL` to your exact Vercel URL
- Make sure it includes `https://` and has no trailing `/`

### WebSocket not connecting

- Make sure `VITE_WS_URL` uses `wss://` (not `ws://`)
- URL should be: `wss://YOUR_RAILWAY_URL/ws`
- Check Railway logs for authentication errors

### "alembic: command not found" in Railway shell

Run with Python:
```bash
python -m alembic upgrade head
```

---

## 17. Cost Summary

| Service | Plan | Monthly Cost | What You Get |
|---------|------|-------------|--------------|
| Vercel | Hobby | **$0** | Frontend hosting, CDN, SSL, preview deploys |
| Railway | Starter | **$5** | Backend hosting, Docker, auto-deploy |
| Neon | Free | **$0** | PostgreSQL (512MB storage, 24/7 compute) |
| Upstash | Pay-as-you-go | **~$0-5** | Redis (pay per request) |
| **TOTAL** | | **$5-10/month** | Full production stack |

### When You'll Start Paying More

- **Neon**: After 512MB storage or if you need always-on compute ($19/month)
- **Upstash**: After ~1M requests/day (unlikely for MVP)
- **Railway**: After 512MB RAM usage (upgrade to $20/month plan)
- **Vercel**: After 100GB bandwidth (unlikely for MVP)

---

## 18. What Each Service Does

### Why Vercel for the Frontend?

Vercel is built by the creators of Next.js (but works with any framework, including Vite/React). It:
- Serves your frontend from **edge servers** worldwide (fast for everyone)
- Automatically gives you **SSL certificates** (https://)
- Creates **preview deployments** for every pull request
- **Auto-deploys** when you push to GitHub
- Has a generous **free tier** for hobby projects

### Why Railway for the Backend?

Railway supports **WebSockets** natively (critical for our real-time game). It:
- Builds **Docker images** from your Dockerfile
- Provides a **public URL** with SSL
- Has **shell access** for running migrations
- **Auto-deploys** on every push to GitHub
- Costs only **$5/month** for the starter plan

### Why Neon for the Database?

Neon is **serverless PostgreSQL** — it scales to zero when idle (free!). It:
- Runs PostgreSQL 15 (same as your local Docker)
- Has **connection pooling** built in (prevents connection exhaustion)
- Supports **branching** (create database copies for testing)
- Has a **generous free tier** (512MB)
- Supports **point-in-time recovery** (restore to any moment)

### Why Upstash for Redis?

Upstash is **serverless Redis** — pay per request, not per hour. It:
- Runs Redis 7 with **append-only persistence**
- Has **no server to manage**
- Provides both **Redis protocol** and **REST API**
- Costs **$0-5/month** for typical MVP usage
- Supports **global replication** for worldwide low latency

### Why Not Use One Service for Everything?

Each service does one thing well:
- **Vercel** excels at static sites and serverless functions (frontend)
- **Railway** excels at long-running servers with WebSockets (backend)
- **Neon** excels at PostgreSQL (our database)
- **Upstash** excels at Redis (our cache)

Trying to run all of one service means vendor lock-in. This setup uses **no vendor lock-in** — you can move any part to a different provider independently.

---

## Quick Reference — All Your URLs

After deployment, fill these in:

| Service | URL | Where |
|---------|-----|-------|
| **Frontend** | `https://____.vercel.app` | Vercel dashboard |
| **Backend API** | `https://____.up.railway.app` | Railway dashboard |
| **Backend Swagger** | `https://____.up.railway.app/docs` | Same as above + /docs |
| **Database** | `postgresql+asyncpg://...@ep-____.neon.tech/...` | Neon dashboard |
| **Redis** | `rediss://...@____.upstash.io:6379` | Upstash dashboard |
| **Database URL** | `https://____.vercel.app` → `https://____.up.railway.app` | Set in Vercel env vars |
| **WebSocket URL** | `wss://____.up.railway.app/ws` | Set in Vercel env vars |

---

*If you get stuck, check the Troubleshooting section or open the browser console (F12) to see error messages.*
