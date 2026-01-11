# AirportWaze Makefile
# Common development and deployment tasks

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# Development Setup
# ============================================================================

.PHONY: install
install: install-backend install-frontend ## Install all dependencies

.PHONY: install-backend
install-backend: ## Install backend dependencies
	@echo "Installing backend dependencies..."
	cd airport-waze-backend && poetry install
	@echo "✓ Backend dependencies installed"

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies
	@echo "Installing frontend dependencies..."
	cd airport-waze-frontend && npm install
	@echo "✓ Frontend dependencies installed"

.PHONY: setup
setup: install setup-env setup-db ## Complete development setup
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env files with your configuration"
	@echo "  2. Run 'make dev' to start development servers"

.PHONY: setup-env
setup-env: ## Create environment files from templates
	@echo "Creating environment files..."
	@if [ ! -f airport-waze-backend/.env ]; then \
		cp airport-waze-backend/.env.example airport-waze-backend/.env; \
		echo "✓ Created airport-waze-backend/.env"; \
	else \
		echo "⚠ airport-waze-backend/.env already exists"; \
	fi

.PHONY: setup-db
setup-db: ## Set up database (requires Docker)
	@echo "Setting up database..."
	docker-compose up -d postgres redis
	@echo "Waiting for database to be ready..."
	@sleep 5
	@echo "Running migrations..."
	$(MAKE) migrate
	@echo "✓ Database setup complete"

# ============================================================================
# Development Servers
# ============================================================================

.PHONY: dev
dev: ## Start all development servers
	@echo "Starting development servers..."
	@trap 'kill 0' EXIT; \
	make dev-backend & \
	make dev-frontend & \
	wait

.PHONY: dev-backend
dev-backend: ## Start backend development server
	@echo "Starting backend server on http://localhost:8000..."
	cd airport-waze-backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: dev-frontend
dev-frontend: ## Start frontend development server
	@echo "Starting frontend server on http://localhost:5173..."
	cd airport-waze-frontend && npm run dev

# ============================================================================
# Testing
# ============================================================================

.PHONY: test
test: test-backend ## Run all tests

.PHONY: test-backend
test-backend: ## Run backend tests
	@echo "Running backend tests..."
	cd airport-waze-backend && poetry run pytest

.PHONY: test-backend-cov
test-backend-cov: ## Run backend tests with coverage
	@echo "Running backend tests with coverage..."
	cd airport-waze-backend && poetry run pytest --cov=app --cov-report=html --cov-report=term

.PHONY: test-frontend
test-frontend: ## Run frontend tests (when implemented)
	@echo "Running frontend tests..."
	cd airport-waze-frontend && npm test

.PHONY: test-watch
test-watch: ## Run backend tests in watch mode
	cd airport-waze-backend && poetry run pytest-watch

# ============================================================================
# Code Quality
# ============================================================================

.PHONY: lint
lint: lint-backend lint-frontend ## Run all linters

.PHONY: lint-backend
lint-backend: ## Lint backend code
	@echo "Linting backend..."
	cd airport-waze-backend && poetry run ruff check .
	cd airport-waze-backend && poetry run mypy app/

.PHONY: lint-frontend
lint-frontend: ## Lint frontend code
	@echo "Linting frontend..."
	cd airport-waze-frontend && npm run lint

.PHONY: format
format: format-backend ## Format all code

.PHONY: format-backend
format-backend: ## Format backend code with black
	@echo "Formatting backend code..."
	cd airport-waze-backend && poetry run black .
	cd airport-waze-backend && poetry run ruff check --fix .

.PHONY: format-check
format-check: ## Check code formatting
	@echo "Checking backend formatting..."
	cd airport-waze-backend && poetry run black --check .

.PHONY: quality
quality: format lint test ## Run all quality checks (format, lint, test)
	@echo "✓ All quality checks passed!"

# ============================================================================
# Database
# ============================================================================

.PHONY: migrate
migrate: ## Run database migrations
	@echo "Running database migrations..."
	cd airport-waze-backend && poetry run alembic upgrade head
	@echo "✓ Migrations complete"

.PHONY: migrate-create
migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is required. Usage: make migrate-create MSG='your message'"; \
		exit 1; \
	fi
	@echo "Creating migration: $(MSG)"
	cd airport-waze-backend && poetry run alembic revision --autogenerate -m "$(MSG)"

.PHONY: migrate-down
migrate-down: ## Rollback last migration
	@echo "Rolling back last migration..."
	cd airport-waze-backend && poetry run alembic downgrade -1

.PHONY: migrate-history
migrate-history: ## Show migration history
	cd airport-waze-backend && poetry run alembic history

.PHONY: db-shell
db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U airportwaze -d airportwaze

.PHONY: db-backup
db-backup: ## Backup database
	@echo "Backing up database..."
	@mkdir -p backups
	@BACKUP_FILE=backups/postgres_backup_$$(date +%Y%m%d_%H%M%S).sql.gz && \
	docker-compose exec -T postgres pg_dump -U airportwaze airportwaze | gzip > $$BACKUP_FILE && \
	echo "✓ Backup saved to $$BACKUP_FILE"

.PHONY: db-restore
db-restore: ## Restore database (usage: make db-restore FILE=backups/file.sql.gz)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE is required. Usage: make db-restore FILE=backups/file.sql.gz"; \
		exit 1; \
	fi
	@echo "Restoring database from $(FILE)..."
	gunzip < $(FILE) | docker-compose exec -T postgres psql -U airportwaze airportwaze
	@echo "✓ Database restored"

.PHONY: redis-cli
redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

.PHONY: redis-flush
redis-flush: ## Flush Redis cache
	@echo "Flushing Redis cache..."
	docker-compose exec redis redis-cli FLUSHALL
	@echo "✓ Redis cache flushed"

# ============================================================================
# Docker
# ============================================================================

.PHONY: docker-build
docker-build: ## Build Docker images
	@echo "Building Docker images..."
	docker-compose build

.PHONY: docker-up
docker-up: ## Start all Docker containers
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "✓ Containers started"
	@echo ""
	@echo "Services:"
	@echo "  - Frontend: http://localhost:80"
	@echo "  - Backend:  http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"

.PHONY: docker-down
docker-down: ## Stop all Docker containers
	@echo "Stopping Docker containers..."
	docker-compose down

.PHONY: docker-restart
docker-restart: docker-down docker-up ## Restart all Docker containers

.PHONY: docker-logs
docker-logs: ## View Docker logs
	docker-compose logs -f

.PHONY: docker-ps
docker-ps: ## List running containers
	docker-compose ps

.PHONY: docker-clean
docker-clean: ## Remove all containers and volumes
	@echo "Warning: This will remove all containers and volumes!"
	@read -p "Are you sure? (y/N): " confirm && [ $$confirm = y ] || exit 1
	docker-compose down -v
	docker system prune -f

# ============================================================================
# Build
# ============================================================================

.PHONY: build
build: build-backend build-frontend ## Build all applications

.PHONY: build-backend
build-backend: ## Build backend Docker image
	@echo "Building backend..."
	cd airport-waze-backend && docker build -t airportwaze/backend:latest .

.PHONY: build-frontend
build-frontend: ## Build frontend for production
	@echo "Building frontend..."
	cd airport-waze-frontend && npm run build
	@echo "✓ Frontend built to airport-waze-frontend/dist/"

# ============================================================================
# Deployment
# ============================================================================

.PHONY: deploy
deploy: ## Deploy to production (requires deploy.sh)
	@echo "Deploying to production..."
	./scripts/deploy.sh

.PHONY: deploy-check
deploy-check: quality ## Run pre-deployment checks
	@echo "Running pre-deployment checks..."
	@echo "✓ All checks passed. Ready to deploy!"

# ============================================================================
# Documentation
# ============================================================================

.PHONY: docs
docs: ## Open API documentation in browser
	@echo "Opening API documentation..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:8000/docs; \
	elif command -v open > /dev/null; then \
		open http://localhost:8000/docs; \
	else \
		echo "Please open http://localhost:8000/docs in your browser"; \
	fi

# ============================================================================
# Utilities
# ============================================================================

.PHONY: clean
clean: ## Clean temporary files and caches
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules/.cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -exec rm -f {} + 2>/dev/null || true
	@echo "✓ Cleaned"

.PHONY: generate-secret
generate-secret: ## Generate a secure secret key
	@python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

.PHONY: generate-password
generate-password: ## Generate a secure password
	@python3 -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(24))"

.PHONY: check-ports
check-ports: ## Check if required ports are available
	@echo "Checking ports..."
	@lsof -i :5432 > /dev/null && echo "⚠ Port 5432 (PostgreSQL) is in use" || echo "✓ Port 5432 is available"
	@lsof -i :6379 > /dev/null && echo "⚠ Port 6379 (Redis) is in use" || echo "✓ Port 6379 is available"
	@lsof -i :8000 > /dev/null && echo "⚠ Port 8000 (Backend) is in use" || echo "✓ Port 8000 is available"
	@lsof -i :5173 > /dev/null && echo "⚠ Port 5173 (Frontend) is in use" || echo "✓ Port 5173 is available"
	@lsof -i :80 > /dev/null && echo "⚠ Port 80 (Nginx) is in use" || echo "✓ Port 80 is available"

.PHONY: status
status: ## Show status of all services
	@echo "=== Docker Services ==="
	@docker-compose ps || echo "Docker Compose not running"
	@echo ""
	@echo "=== Health Checks ==="
	@curl -s http://localhost:8000/healthz > /dev/null && echo "✓ Backend is healthy" || echo "✗ Backend is not responding"
	@curl -s http://localhost:5173 > /dev/null && echo "✓ Frontend is responding" || echo "✗ Frontend is not responding"
	@docker-compose exec -T postgres pg_isready -U airportwaze > /dev/null 2>&1 && echo "✓ PostgreSQL is ready" || echo "✗ PostgreSQL is not ready"
	@docker-compose exec -T redis redis-cli ping > /dev/null 2>&1 && echo "✓ Redis is ready" || echo "✗ Redis is not ready"

.PHONY: version
version: ## Show version information
	@echo "AirportWaze v2.0.0"
	@echo ""
	@echo "Backend:"
	@cd airport-waze-backend && poetry --version || echo "Poetry not installed"
	@cd airport-waze-backend && poetry run python --version || echo "Python not available"
	@echo ""
	@echo "Frontend:"
	@cd airport-waze-frontend && node --version || echo "Node.js not installed"
	@cd airport-waze-frontend && npm --version || echo "npm not installed"
	@echo ""
	@echo "Infrastructure:"
	@docker --version || echo "Docker not installed"
	@docker-compose --version || echo "Docker Compose not installed"

# ============================================================================
# CI/CD
# ============================================================================

.PHONY: ci
ci: install quality ## Run CI pipeline locally
	@echo "✓ CI pipeline completed successfully!"

.PHONY: ci-backend
ci-backend: install-backend lint-backend test-backend-cov ## Run backend CI pipeline
	@echo "✓ Backend CI pipeline completed!"

.PHONY: ci-frontend
ci-frontend: install-frontend lint-frontend ## Run frontend CI pipeline
	@echo "✓ Frontend CI pipeline completed!"

# ============================================================================
# Default target
# ============================================================================

.DEFAULT_GOAL := help
