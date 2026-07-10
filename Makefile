.PHONY: help install frontend backend dev-up dev-down dev-logs migrate test frontend-dev backend-dev lint format

help:
	@echo "Available targets:"
	@echo "  install              - Install dependencies for both frontend and backend"
	@echo "  frontend-dev         - Start frontend development server"
	@echo "  backend-dev          - Start backend development server"
	@echo "  dev-up               - Start development infrastructure (PostgreSQL, Redis)"
	@echo "  dev-down             - Stop development infrastructure"
	@echo "  dev-logs             - View logs for development infrastructure"
	@echo "  migrate              - Apply backend database migrations"
	@echo "  test                 - Run tests for both frontend and backend"
	@echo "  frontend-test        - Run frontend tests"
	@echo "  backend-test         - Run backend tests"
	@echo "  lint                 - Run linting for both frontend and backend"
	@echo "  format               - Format code for both frontend and backend"

install:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing backend dependencies..."
	cd backend && pip install -e ".[dev]"

frontend-dev:
	@echo "Starting frontend development server..."
	cd frontend && npm run dev

backend-dev:
	@echo "Starting backend development server..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-up:
	@echo "Starting development services..."
	docker-compose up -d

dev-down:
	@echo "Stopping development services..."
	docker-compose down

dev-logs:
	@echo "Showing logs for development services..."
	docker-compose logs -f

migrate:
	@echo "Applying backend database migrations..."
	cd backend && uv run alembic upgrade head

test:
	@echo "Running all tests..."
	$(MAKE) frontend-test
	$(MAKE) backend-test

frontend-test:
	@echo "Running frontend tests..."
	cd frontend && npm test

backend-test:
	@echo "Running backend tests..."
	cd backend && pytest

lint:
	@echo "Running linting..."
	$(MAKE) frontend-lint
	$(MAKE) backend-lint

frontend-lint:
	@echo "Linting frontend..."
	cd frontend && npm run lint

backend-lint:
	@echo "Linting backend..."
	cd backend && ruff check .

format:
	@echo "Formatting code..."
	$(MAKE) frontend-format
	$(MAKE) backend-format

frontend-format:
	@echo "Formatting frontend..."
	cd frontend && npm run format

backend-format:
	@echo "Formatting backend..."
	cd backend && ruff check --fix .
	cd backend && black .
