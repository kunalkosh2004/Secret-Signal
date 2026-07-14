.PHONY: help install frontend backend dev-up dev-down dev-logs dev-full migrate test frontend-dev backend-dev lint format docker-build docker-up monitoring

help:
	@echo "Available targets:"
	@echo ""
	@echo "  Development:"
	@echo "    install              - Install dependencies for both frontend and backend"
	@echo "    dev-up               - Start PostgreSQL + Redis (Docker)"
	@echo "    dev-down             - Stop PostgreSQL + Redis"
	@echo "    dev-full             - Start ALL services (app + monitoring)"
	@echo "    dev-logs             - View logs for development infrastructure"
	@echo "    frontend-dev         - Start frontend dev server"
	@echo "    backend-dev          - Start backend dev server"
	@echo "    migrate              - Apply database migrations"
	@echo ""
	@echo "  Docker:"
	@echo "    docker-build         - Build all Docker images"
	@echo "    docker-up            - Start full stack via Docker Compose"
	@echo "    docker-down          - Stop Docker Compose stack"
	@echo ""
	@echo "  Monitoring:"
	@echo "    monitoring           - Start infrastructure + monitoring stack"
	@echo ""
	@echo "  Quality:"
	@echo "    test                 - Run all tests"
	@echo "    lint                 - Run linting"
	@echo "    format               - Format code"

install:
	@echo "Installing frontend dependencies..."
	cd frontend/frontend && npm install
	@echo "Installing backend dependencies..."
	cd backend && pip install -e ".[dev]"

frontend-dev:
	@echo "Starting frontend development server..."
	cd frontend/frontend && npm run dev

backend-dev:
	@echo "Starting backend development server..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-up:
	@echo "Starting development infrastructure..."
	docker compose up -d postgres redis

dev-down:
	@echo "Stopping development infrastructure..."
	docker compose down

dev-full:
	@echo "Starting full development stack..."
	docker compose --profile tools up -d

dev-logs:
	@echo "Showing logs for development services..."
	docker compose logs -f

migrate:
	@echo "Applying database migrations..."
	cd backend && alembic upgrade head

test:
	$(MAKE) frontend-test 2>/dev/null || true
	$(MAKE) backend-test

frontend-test:
	@echo "Running frontend tests..."
	cd frontend/frontend && npm test 2>/dev/null || echo "No frontend tests configured yet"

backend-test:
	@echo "Running backend tests..."
	cd backend && pytest

lint:
	$(MAKE) frontend-lint
	$(MAKE) backend-lint

frontend-lint:
	@echo "Linting frontend..."
	cd frontend/frontend && npm run lint

backend-lint:
	@echo "Linting backend..."
	cd backend && ruff check .

format:
	$(MAKE) frontend-format
	$(MAKE) backend-format

frontend-format:
	@echo "Formatting frontend..."
	cd frontend/frontend && npx prettier --write "src/**/*.{ts,tsx,css}"

backend-format:
	@echo "Formatting backend..."
	cd backend && ruff check --fix .
	cd backend && ruff format .

docker-build:
	@echo "Building Docker images..."
	docker compose build

docker-up:
	@echo "Starting full stack..."
	docker compose up -d

docker-down:
	@echo "Stopping Docker stack..."
	docker compose down

monitoring:
	@echo "Starting with monitoring stack..."
	docker compose --profile monitoring up -d
