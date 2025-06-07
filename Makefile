.PHONY: help up down logs ps restart clean db-shell backend-shell frontend-shell

# Default command: Display help
help:
	@echo "Available commands for StatementSense development:"
	@echo "  make up            Start all services in development mode"
	@echo "  make down          Stop and remove all containers and volumes"
	@echo "  make logs          Show logs from all services"
	@echo "  make ps            List running containers"
	@echo "  make restart       Restart all services"
	@echo "  make clean         Remove all containers, volumes, and temporary files"
	@echo "  make db-shell      Open a PostgreSQL shell"
	@echo "  make backend-shell Open a shell in the backend container"
	@echo "  make frontend-shell Open a shell in the frontend container"

# Start all services in development mode
up:
	@echo "Starting development environment..."
	docker-compose up --build -d

# Stop and remove all containers and volumes
down:
	@echo "Stopping and removing containers..."
	docker-compose down -v

# Show logs from all services
logs:
	docker-compose logs -f

# List running containers
ps:
	docker-compose ps

# Restart all services
restart: down up

# Clean everything
clean: down
	@echo "Removing temporary files and build artifacts..."
	rm -rf .pytest_cache .mypy_cache .ruff_cache build/ dist/ *.egg-info/ venv/ .venv/ uploads/
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	@echo "Clean up complete."

# Database shell
db-shell:
	docker-compose exec postgres psql -U statement_user -d statement_sense

# Backend shell
backend-shell:
	docker-compose exec backend /bin/bash

# Frontend shell
frontend-shell:
	docker-compose exec frontend /bin/sh
