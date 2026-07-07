# Architecture Overview

## System Overview

Secret Signal follows a modular monolith architecture with a clear separation of concerns between frontend, backend, and machine learning components.

## Frontend

- Built with React, TypeScript, and Vite
- Uses Tailwind CSS for styling
- State management with Zustand
- Routing with React Router
- Communicates with backend via WebSocket and REST API

## Backend

- Python 3.12+ with FastAPI
- Modular domain-oriented structure:
  - Core: Shared utilities, configuration, base classes
  - Auth: User authentication and authorization
  - Users: Player profiles and management
  - Rooms: Game room creation and management
  - Matchmaking: Player matching and lobby system
  - Game Engine: State machine, round progression, scoring
  - Chat: Message handling, reactions, replies
  - Voting: Accusation and voting systems
  - Missions: Mission generation, validation, and tracking
  - Events: Domain event publishing and handling
  - Analytics: Event collection and processing
  - DB: Database models and migrations
  - Redis: Caching, pub/sub, temporary state
  - WebSocket: Connection management and event broadcasting

## Data Layer

- PostgreSQL: Persistent storage for users, rooms, games, events, etc.
- Redis: Ephemeral storage for active game states, player connections, pub/sub

## Machine Learning (Future)

- Separated ML pipeline for behavioral analysis
- Feature extraction from game events
- Model training and inference services
- MLflow for experiment tracking

## Communication

- WebSocket for real-time game events
- REST API for initial setup and non-real-time operations
- Event-driven internal communication using domain events

## Infrastructure

- Docker Compose for local development
- Planned migration to Kubernetes for production
- GitHub Actions for CI/CD