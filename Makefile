.PHONY: setup up down test lint format clean help

# Configuration variables
ENV_FILE ?= .env
SHELL := /bin/bash

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup   - Initialize directory structure and install dependencies"
	@echo "  make up      - Start the PostgreSQL database service in Docker"
	@echo "  make down    - Stop the PostgreSQL database service"
	@echo "  make test    - Run test suite"
	@echo "  make lint    - Run code linters (Ruff and Black check)"
	@echo "  make format  - Auto-format code using Black and Ruff"

setup:
	@echo "==> Constructing directory tree..."
	@./init_dirs.sh
	@echo "==> Installing Python dependencies..."
	@poetry install
	@echo "==> Configuring environment variables..."
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "POSTGRES_USER=postgres" > $(ENV_FILE); \
		echo "POSTGRES_PASSWORD=postgres" >> $(ENV_FILE); \
		echo "POSTGRES_DB=turing_vessel" >> $(ENV_FILE); \
		echo "POSTGRES_PORT=5432" >> $(ENV_FILE); \
		echo "Created default $(ENV_FILE) file."; \
	else \
		echo "$(ENV_FILE) file already exists."; \
	fi
	@echo "==> Initializing Alembic migrations..."
	@if [ ! -d "alembic" ]; then \
		poetry run alembic init alembic; \
	else \
		echo "Alembic directory already exists."; \
	fi
	@echo "==> Setup completed successfully."

up:
	@echo "==> Starting PostgreSQL..."
	@docker compose up -d
	@echo "==> Database service is running."

down:
	@echo "==> Stopping PostgreSQL..."
	@docker compose down
	@echo "==> Database service stopped."

test:
	@echo "==> Running test suite..."
	@poetry run pytest

lint:
	@echo "==> Checking code quality (ruff)..."
	@poetry run ruff check src tests
	@echo "==> Checking code formatting (black)..."
	@poetry run black --check src tests
	@echo "==> Code check passed."

format:
	@echo "==> Formatting code..."
	@poetry run ruff check --fix src tests || true
	@poetry run black src tests

clean:
	@echo "==> Cleaning cache and temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "==> Clean completed."
