# Secret Signal 🎭

Secret Signal is a real-time multiplayer social deduction game where players complete hidden objectives, manipulate conversations, detect suspicious behavior, and uncover the secret Coordinator.

Unlike traditional social deduction games based on elimination, Secret Signal focuses on **social influence and behavioral manipulation**.

One player secretly becomes the **Coordinator**, whose goal is to influence other players into completing hidden actions without being detected. Meanwhile, the **Detective** and **Citizens** observe conversations, complete their own objectives, analyze suspicious behavior, and try to identify the Coordinator.

The project combines real-time multiplayer engineering, backend system design, event-driven architecture, and machine learning-based behavioral analysis.

---

## 🎮 Game Concept

A game consists of 4–8 players and multiple timed rounds.

Each player receives a hidden role:

### 🎭 Coordinator

The Coordinator receives secret missions and must manipulate conversations to complete them without revealing their identity.

Example missions:

* Make three different players mention a city.
* Get two players to react to the same message.
* Make another player change their opinion.
* Get two players to ask you a question.
* Make multiple players use a target word naturally.

The Coordinator earns points by completing missions and surviving incorrect accusations.

### 🕵️ Detective

The Detective observes player behavior and tries to identify the Coordinator.

The Detective may have limited investigation abilities, such as:

* Checking whether the Coordinator is among a selected group of players.
* Viewing behavioral hints.
* Investigating suspicious interaction patterns.

These abilities are intentionally limited and must be used strategically.

### 👥 Citizens

Citizens help identify the Coordinator while completing their own smaller private objectives.

Example Citizen objectives:

* Make another player disagree with you.
* Get someone to ask you a question.
* Receive reactions from multiple players.
* Convince another player to change their opinion.

Giving Citizens their own objectives ensures that every player behaves somewhat suspiciously, making it harder to identify the real Coordinator.

---

## 🔄 Game Flow

```text
Landing Page
      ↓
Create / Join Room
      ↓
Waiting Lobby
      ↓
Players Ready
      ↓
Game Start
      ↓
Secret Role Assignment
      ↓
┌─────────────────────────┐
│       ROUND START       │
│                         │
│  Public Prompt          │
│         ↓               │
│  Private Objectives     │
│         ↓               │
│  Interaction Phase      │
│         ↓               │
│  Mission Evaluation     │
│         ↓               │
│  Discussion Phase       │
│         ↓               │
│  Accuse or Skip         │
│         ↓               │
│  Score Update           │
└─────────────────────────┘
      ↓
Next Round
      ↓
Final Role Reveal
      ↓
Winner Announcement
      ↓
AI Behavior Analysis
```

A typical game contains four rounds and lasts approximately 15–20 minutes.

---

## 💬 Interaction Phase

Each round begins with a public conversation prompt.

Example:

> You receive ₹10 crore, but you must live in one city for the rest of your life. Which city would you choose?

At the same time, players receive private objectives.

The Coordinator may receive:

> Get three different players to mention a country.

A Citizen may receive:

> Make someone disagree with you.

Another Citizen may receive:

> Get two different players to react to your messages.

Players then interact through real-time chat, replies, and reactions while secretly trying to complete their objectives.

The Coordinator must influence the conversation naturally without making their mission obvious.

---

## 🗳️ Discussion and Accusation

After the interaction phase, players enter a discussion period.

Players analyze:

* Who changed the topic?
* Who repeatedly asked leading questions?
* Who benefited from certain conversations?
* Who appeared to influence multiple players?
* Who behaved unusually?

Players then vote for a suspect or choose to skip the accusation.

A wrong accusation rewards the Coordinator side.

A correct accusation rewards the Investigator side.

Players are not eliminated after accusations, allowing everyone to participate throughout the entire match.

---

## 🏆 Winning the Game

Secret Signal uses a team-based scoring system.

The **Coordinator Side** earns points for:

* Completing secret missions.
* Causing incorrect accusations.
* Surviving rounds without being identified.

The **Investigator Side** earns points for:

* Preventing mission completion.
* Correctly identifying the Coordinator.
* Successfully using investigation abilities.

After all rounds are completed, the team with the highest score wins.

The game then reveals:

* All hidden roles.
* The Coordinator.
* Secret missions from every round.
* Mission success and failure history.
* Voting history.
* Player statistics.

---

## 🤖 AI and Machine Learning

Secret Signal includes an experimental behavioral intelligence system designed to analyze multiplayer interactions.

The goal of the ML system is to answer:

> Can a machine learning model identify the hidden Coordinator from behavioral patterns better or faster than human players?

The system can analyze features such as:

* Message frequency.
* Response timing.
* Conversation initiation.
* Topic changes.
* Semantic similarity between messages.
* Reaction patterns.
* Voting alignment.
* Interaction frequency.
* Mission success correlation.
* Player-to-player influence patterns.

Possible ML approaches include:

* Isolation Forest for anomalous behavior detection.
* Gradient boosting models for Coordinator probability prediction.
* Sentence embeddings for semantic analysis.
* Graph-based models for interaction and alliance analysis.
* Neural networks for sequential behavioral modeling.

The AI system is intended primarily for post-game analysis rather than directly deciding game outcomes.

---

## 📊 AI Suspicion Analysis

After the match, players can view how the AI model's suspicion changed throughout the game.

Example:

```text
Round 1

Kunal      22%
Aman       18%
Rahul      31%
Priya      14%

Round 2

Kunal      47%
Aman       20%
Rahul      25%
Priya      16%

Round 3

Kunal      71%
Aman       14%
Rahul      19%
Priya      12%

Round 4

Kunal      84%
Aman       11%
Rahul      16%
Priya       9%
```

Future versions may also include:

* Suspicion timelines.
* Player behavior embeddings.
* Interaction graphs.
* Alliance detection.
* Conversation influence analysis.
* AI-generated post-game summaries.

---

## 🏗️ System Architecture

The initial version follows a modular monolith architecture.

```text
                       React + TypeScript
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

The backend acts as the authoritative source of game state.

Clients send player intentions through WebSocket events. The backend validates actions, updates the game state, stores relevant events, and broadcasts accepted state changes to connected players.

---

## 🛠️ Tech Stack

### Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* React Router
* Zustand
* Native WebSocket API

### Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
* Pytest

### Data Layer

* PostgreSQL
* Redis

### Machine Learning

* scikit-learn
* PyTorch
* Sentence Transformers
* MLflow

### Infrastructure

* Docker
* Docker Compose
* GitHub Actions
* AWS
* Kubernetes in later scaling phases
* Prometheus
* Grafana
* OpenTelemetry

---

## 📁 Planned Repository Structure

```text
secret-signal/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── lobby/
│   │   │   ├── room/
│   │   │   ├── game/
│   │   │   ├── chat/
│   │   │   └── voting/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── types/
│   │   └── utils/
│   │
│   └── tests/
│
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── rooms/
│   │   ├── matchmaking/
│   │   ├── game_engine/
│   │   ├── chat/
│   │   ├── voting/
│   │   ├── missions/
│   │   ├── events/
│   │   └── analytics/
│   │
│   └── tests/
│
├── ml/
│   ├── data/
│   ├── features/
│   ├── training/
│   ├── models/
│   ├── evaluation/
│   └── inference/
│
├── infrastructure/
│   ├── docker/
│   ├── monitoring/
│   └── kubernetes/
│
├── docs/
│   ├── architecture/
│   ├── game-design/
│   └── websocket-protocol/
│
├── scripts/
│
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## 📡 Real-Time Event System

The game uses WebSockets for real-time communication.

Example event structure:

```json
{
  "event": "MESSAGE_SENT",
  "request_id": "uuid",
  "room_id": "uuid",
  "timestamp": "2026-07-08T10:30:00Z",
  "payload": {}
}
```

Example client events:

* `JOIN_ROOM`
* `LEAVE_ROOM`
* `PLAYER_READY`
* `SEND_MESSAGE`
* `ADD_REACTION`
* `CAST_VOTE`
* `SUBMIT_ACCUSATION`

Example server events:

* `ROOM_STATE`
* `PLAYER_JOINED`
* `PLAYER_LEFT`
* `PLAYER_READY_CHANGED`
* `MESSAGE_SENT`
* `REACTION_ADDED`
* `ROUND_STARTED`
* `TIMER_UPDATED`
* `MISSION_ASSIGNED`
* `VOTE_UPDATED`
* `ACCUSATION_RESULT`
* `ROUND_ENDED`
* `GAME_ENDED`
* `ERROR`

---

## 🧠 Game State Machine

```text
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

State transitions are controlled by the backend game engine.

---

## 🚀 Development Roadmap

### Phase 1 — Multiplayer MVP

* User authentication.
* Create and join private rooms.
* Waiting lobby.
* Player ready system.
* Role assignment.
* Real-time chat.
* Basic mission system.
* Game timer.
* Round state machine.
* Voting and accusation system.
* Score calculation.
* Final role reveal.

### Phase 2 — Production Multiplayer Features

* Redis-backed room state.
* Player presence tracking.
* Reconnection support.
* Game event logging.
* Spectator support.
* Rate limiting.
* Improved matchmaking.

### Phase 3 — AI/ML System

* Behavioral feature extraction.
* Player interaction datasets.
* Baseline anomaly detection.
* Coordinator classification model.
* Message embedding pipeline.
* Suspicion scoring.
* Post-game AI dashboard.

### Phase 4 — Distributed Architecture

* Event streaming.
* Independent analytics consumers.
* ML inference service.
* Model monitoring.
* Horizontal WebSocket scaling.
* Kubernetes deployment.
* Distributed tracing and observability.

---

## 🎯 Project Goals

This project is designed to explore and demonstrate:

* Real-time multiplayer systems.
* WebSocket communication.
* Authoritative server architecture.
* Game state machines.
* Distributed state management.
* Event-driven system design.
* Backend engineering with Python.
* Modern frontend development.
* Machine learning pipelines.
* Behavioral analytics.
* MLOps.
* Containerization and deployment.
* Observability and distributed tracing.

---

## ⚠️ Project Status

🚧 Secret Signal is currently under active development.

The first milestone is a playable text-based multiplayer MVP with:

* Private rooms.
* Hidden roles.
* Real-time chat.
* Secret missions.
* Timed rounds.
* Voting.
* Score calculation.
* Final role reveal.

AI behavior analysis and distributed infrastructure will be introduced after the core multiplayer gameplay is stable.

---

## 🤝 Contributing

The project is currently being developed as a personal engineering project.

Suggestions, game mechanic ideas, architecture discussions, and technical feedback are welcome through issues and discussions.

---

## 📄 License

This project is licensed under the MIT License.

---

# Secret Signal

**Influence the conversation. Hide your intent. Find the signal.**
