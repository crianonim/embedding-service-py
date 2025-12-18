.PHONY: install dev run test lint format db-up db-down docker-up docker-down clean

# Install dependencies (creates .venv in project directory)
install:
	poetry config virtualenvs.in-project true
	@if [ ! -d ".venv" ]; then poetry env remove --all 2>/dev/null || true; fi
	poetry install
	@echo ""
	@echo "Virtual environment created at .venv/"
	@echo "Activate with: source .venv/bin/activate"

# Setup local development (install + start db)
dev: install db-up
	@echo "Ready for local development!"
	@echo "Run 'make run' to start the server"

# Run locally
run:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	poetry run pytest

# Run linter
lint:
	poetry run ruff check .
	poetry run mypy app

# Format code
format:
	poetry run ruff format .
	poetry run ruff check --fix .

# Start database only (for local development)
db-up:
	docker-compose up -d db
	@echo "Waiting for database to be ready..."
	@sleep 3
	@echo "Database is running on localhost:5432"

# Stop database
db-down:
	docker-compose down db

# Start all services in Docker
docker-up:
	docker-compose up --build

# Stop all Docker services
docker-down:
	docker-compose down

# Clean up
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
