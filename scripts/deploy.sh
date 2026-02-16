#!/bin/bash

################################################################################
# AirportWaze Deployment Script
#
# Automated deployment script with health checks and rollback capability
#
# Usage:
#   ./scripts/deploy.sh [environment]
#
# Arguments:
#   environment - Target environment (staging|production) [default: production]
#
# Examples:
#   ./scripts/deploy.sh production
#   ./scripts/deploy.sh staging
################################################################################

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENVIRONMENT="${1:-production}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$PROJECT_ROOT/backups"
LOG_FILE="$PROJECT_ROOT/deploy_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[✓]${NC} $*" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[⚠]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[✗]${NC} $*" | tee -a "$LOG_FILE"
}

fatal() {
    error "$*"
    exit 1
}

# ============================================================================
# Pre-deployment Checks
# ============================================================================

check_prerequisites() {
    log "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        fatal "Docker is not installed"
    fi
    success "Docker is installed"

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        fatal "Docker Compose is not installed"
    fi
    success "Docker Compose is installed"

    # Check if running as root or in docker group
    if ! docker ps &> /dev/null; then
        fatal "Cannot access Docker. Are you in the docker group?"
    fi
    success "Docker is accessible"

    # Check if git is installed
    if ! command -v git &> /dev/null; then
        fatal "Git is not installed"
    fi
    success "Git is installed"

    # Check if we're in a git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        fatal "Not in a git repository"
    fi
    success "In git repository"

    # Check for required directories
    if [ ! -d "$PROJECT_ROOT/airport-waze-backend" ]; then
        fatal "Backend directory not found"
    fi
    if [ ! -d "$PROJECT_ROOT/airport-waze-frontend" ]; then
        fatal "Frontend directory not found"
    fi
    success "Project structure is valid"

    # Check for environment file
    ENV_FILE="$PROJECT_ROOT/airport-waze-backend/.env"
    if [ ! -f "$ENV_FILE" ]; then
        fatal "Environment file not found: $ENV_FILE"
    fi
    success "Environment file exists"

    # Validate environment file has required variables
    required_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE"; then
            fatal "Required environment variable $var not found in .env"
        fi
    done
    success "Environment variables validated"
}

check_working_directory() {
    log "Checking working directory status..."

    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        warning "There are uncommitted changes in the working directory"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            fatal "Deployment cancelled"
        fi
    fi

    # Get current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    log "Current branch: $CURRENT_BRANCH"

    # Get current commit
    CURRENT_COMMIT=$(git rev-parse --short HEAD)
    log "Current commit: $CURRENT_COMMIT"

    success "Working directory check complete"
}

# ============================================================================
# Backup Functions
# ============================================================================

backup_database() {
    log "Backing up database..."

    mkdir -p "$BACKUP_DIR"

    BACKUP_FILE="$BACKUP_DIR/postgres_backup_${TIMESTAMP}.sql.gz"

    if docker-compose exec -T postgres pg_dump -U airportwaze airportwaze | gzip > "$BACKUP_FILE"; then
        success "Database backed up to: $BACKUP_FILE"
    else
        error "Database backup failed"
        return 1
    fi
}

backup_current_deployment() {
    log "Creating deployment backup..."

    # Tag current Docker images
    docker tag airportwaze/backend:latest "airportwaze/backend:backup_${TIMESTAMP}" || true
    docker tag airportwaze/frontend:latest "airportwaze/frontend:backup_${TIMESTAMP}" || true

    success "Current deployment backed up"
}

# ============================================================================
# Build Functions
# ============================================================================

pull_latest_code() {
    log "Pulling latest code from repository..."

    git fetch origin
    git pull origin "$CURRENT_BRANCH"

    success "Code updated to latest version"
}

build_images() {
    log "Building Docker images..."

    cd "$PROJECT_ROOT"

    if docker-compose build --no-cache; then
        success "Docker images built successfully"
    else
        error "Failed to build Docker images"
        return 1
    fi
}

# ============================================================================
# Deployment Functions
# ============================================================================

run_migrations() {
    log "Running database migrations..."

    if docker-compose exec -T backend alembic upgrade head; then
        success "Database migrations completed"
    else
        error "Database migrations failed"
        return 1
    fi
}

deploy_services() {
    log "Deploying services..."

    cd "$PROJECT_ROOT"

    # Start services with new images
    if docker-compose up -d; then
        success "Services started"
    else
        error "Failed to start services"
        return 1
    fi

    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 10
}

# ============================================================================
# Health Check Functions
# ============================================================================

check_backend_health() {
    log "Checking backend health..."

    MAX_ATTEMPTS=30
    ATTEMPT=0

    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if curl -sf http://localhost:8000/healthz > /dev/null 2>&1; then
            success "Backend is healthy"
            return 0
        fi

        ATTEMPT=$((ATTEMPT + 1))
        log "Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting for backend..."
        sleep 2
    done

    error "Backend health check failed after $MAX_ATTEMPTS attempts"
    return 1
}

check_frontend_health() {
    log "Checking frontend health..."

    MAX_ATTEMPTS=30
    ATTEMPT=0

    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if curl -sf http://localhost:80 > /dev/null 2>&1; then
            success "Frontend is healthy"
            return 0
        fi

        ATTEMPT=$((ATTEMPT + 1))
        log "Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting for frontend..."
        sleep 2
    done

    error "Frontend health check failed after $MAX_ATTEMPTS attempts"
    return 1
}

check_database_health() {
    log "Checking database health..."

    if docker-compose exec -T postgres pg_isready -U airportwaze > /dev/null 2>&1; then
        success "Database is healthy"
        return 0
    else
        error "Database health check failed"
        return 1
    fi
}

check_redis_health() {
    log "Checking Redis health..."

    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        success "Redis is healthy"
        return 0
    else
        error "Redis health check failed"
        return 1
    fi
}

run_health_checks() {
    log "Running comprehensive health checks..."

    HEALTH_CHECK_PASSED=true

    check_database_health || HEALTH_CHECK_PASSED=false
    check_redis_health || HEALTH_CHECK_PASSED=false
    check_backend_health || HEALTH_CHECK_PASSED=false
    check_frontend_health || HEALTH_CHECK_PASSED=false

    if [ "$HEALTH_CHECK_PASSED" = true ]; then
        success "All health checks passed"
        return 0
    else
        error "Health checks failed"
        return 1
    fi
}

# ============================================================================
# Rollback Functions
# ============================================================================

rollback_deployment() {
    error "Deployment failed. Rolling back..."

    # Stop current services
    docker-compose down

    # Restore backup images
    docker tag "airportwaze/backend:backup_${TIMESTAMP}" airportwaze/backend:latest || true
    docker tag "airportwaze/frontend:backup_${TIMESTAMP}" airportwaze/frontend:latest || true

    # Restart with old images
    docker-compose up -d

    # Rollback database migration
    log "Rolling back database migration..."
    docker-compose exec -T backend alembic downgrade -1 || true

    error "Rollback completed"
    fatal "Deployment failed and was rolled back"
}

# ============================================================================
# Cleanup Functions
# ============================================================================

cleanup_old_backups() {
    log "Cleaning up old backups..."

    # Keep only last 7 days of backups
    find "$BACKUP_DIR" -name "postgres_backup_*.sql.gz" -mtime +7 -delete 2>/dev/null || true

    # Remove old backup images (keep last 3)
    OLD_IMAGES=$(docker images airportwaze/backend --format "{{.Tag}}" | grep "backup_" | tail -n +4)
    if [ -n "$OLD_IMAGES" ]; then
        echo "$OLD_IMAGES" | xargs -I {} docker rmi "airportwaze/backend:{}" 2>/dev/null || true
    fi

    success "Old backups cleaned up"
}

# ============================================================================
# Post-deployment Functions
# ============================================================================

show_deployment_info() {
    log "Deployment Summary"
    echo "============================================"
    echo "Environment:     $ENVIRONMENT"
    echo "Branch:          $CURRENT_BRANCH"
    echo "Commit:          $CURRENT_COMMIT"
    echo "Timestamp:       $TIMESTAMP"
    echo "Backup Location: $BACKUP_DIR"
    echo "Log File:        $LOG_FILE"
    echo "============================================"
    echo ""
    echo "Services:"
    echo "  - Frontend:  http://localhost:80"
    echo "  - Backend:   http://localhost:8000"
    echo "  - API Docs:  http://localhost:8000/docs"
    echo "============================================"
}

send_notification() {
    # Placeholder for notification service (Slack, email, etc.)
    # Implement according to your notification preferences
    log "Deployment notification would be sent here"
}

# ============================================================================
# Main Deployment Flow
# ============================================================================

main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║       AirportWaze Deployment Script              ║"
    echo "║       Environment: $ENVIRONMENT                          ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo ""

    log "Starting deployment..."

    # Pre-deployment
    check_prerequisites
    check_working_directory

    # Confirmation for production
    if [ "$ENVIRONMENT" = "production" ]; then
        warning "PRODUCTION DEPLOYMENT"
        read -p "Are you sure you want to deploy to PRODUCTION? (yes/NO): " -r
        echo
        if [[ ! $REPLY = "yes" ]]; then
            fatal "Deployment cancelled"
        fi
    fi

    # Backup
    backup_database || fatal "Database backup failed"
    backup_current_deployment

    # Deploy
    pull_latest_code
    build_images || { rollback_deployment; }
    run_migrations || { rollback_deployment; }
    deploy_services || { rollback_deployment; }

    # Verify
    if ! run_health_checks; then
        rollback_deployment
    fi

    # Cleanup
    cleanup_old_backups

    # Summary
    success "Deployment completed successfully!"
    show_deployment_info
    send_notification

    log "Deployment finished"
}

# ============================================================================
# Script Entry Point
# ============================================================================

# Change to project root
cd "$PROJECT_ROOT"

# Run main deployment
main

exit 0
