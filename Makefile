.PHONY: help up down logs ps restart clean db-shell backend-shell frontend-shell migrate-create migrate-apply

# Default command: Display help
help:
	@echo "Available commands for SentidoFinanciero development:"
	@echo "  make up            Start all services in development mode"
	@echo "  make down          Stop and remove all containers and volumes"
	@echo "  make logs          Show logs from all services"
	@echo "  make ps            List running containers"
	@echo "  make restart       Restart all services"
	@echo "  make clean         Remove all containers, volumes, and temporary files"
	@echo "  make db-shell      Open a PostgreSQL shell"
	@echo "  make backend-shell Open a shell in the backend container"
	@echo "  make frontend-shell Open a shell in the frontend container"
	@echo "  make migrate-create MSG=\"your_migration_message\"  Create a new database migration"
	@echo "  make migrate-apply   Apply pending database migrations"

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

# Clean everything - file system only (no Docker)
clean:
	@echo "Removing temporary files and build artifacts..."
	# Python
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ .coverage htmlcov/

# Database Migrations (Alembic)
# Example: make migrate-create MSG="add user table"
migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Migration message is required. Usage: make migrate-create MSG=\"your_migration_message\""; \
		exit 1; \
	fi
	@echo "Creating migration: $(MSG)..."
	.venv/bin/alembic revision -m "$(MSG)"

migrate-apply:
	@echo "Applying database migrations..."
	.venv/bin/alembic upgrade head
	rm -rf build/ dist/ *.egg-info/
	rm -rf venv/ .venv/ .eggs/
	# Node/JS
	rm -rf frontend/node_modules/ frontend/.next/ frontend/.turbo/ frontend/.cache/
	# Python cache and temp files
	find . -type f -name '*.py[co]' -delete -o -name '*.so' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	# IDE and editor files
	rm -rf .idea/ .vscode/ *.swp *.swo *~
	# Logs and local files
	rm -rf logs/ uploads/ .mypy_cache/ .pytest_cache/
	@echo "Filesystem clean up complete."

# Database shell
db-shell:
	docker-compose exec postgres psql -U statement_user -d statement_sense

# Backend shell
backend-shell:
	docker-compose exec backend /bin/bash

# Frontend shell
frontend-shell:
	docker-compose exec frontend /bin/sh
