# Turing Vessel

An asynchronous Python platform featuring automation and infrastructure management.

## Project Structure

This project follows a clean architecture pattern:

```text
├── data/                  # Persistent data (e.g. Postgres data)
├── src/
│   ├── domain/            # Domain models and business rules
│   ├── application/       # Application use cases
│   ├── infrastructure/    # Database, external services implementation
│   └── interfaces/        # User interfaces
│       └── cli/           # Command line interface
├── tests/                 # Test suite
│   └── acceptance/        # Acceptance tests (pytest-bdd)
├── Makefile               # Automation tasks
├── docker-compose.yml     # PostgreSQL service definition
└── pyproject.toml         # Python dependencies configuration (Poetry)
```

## Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- Docker and Docker Compose

### Environment Setup

1. Run the setup target to install dependencies and initialize the directories:
   ```bash
   make setup
   ```

2. Start the database infrastructure:
   ```bash
   make up
   ```

3. Run quality assurance tools:
   ```bash
   make lint
   ```

4. Run the test suite:
   ```bash
   make test
   ```

5. Stop infrastructure:
   ```bash
   make down
   ```
