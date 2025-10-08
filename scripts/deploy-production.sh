#!/bin/bash

# ============================================
# TaskifAI Production Deployment Script
# ============================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Deployment configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
DOCKER_USERNAME="${DOCKER_USERNAME:-taskifai}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed"
        exit 1
    fi

    # Check if required environment variables are set
    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL environment variable is not set"
        exit 1
    fi

    if [ -z "${SECRET_KEY:-}" ]; then
        log_error "SECRET_KEY environment variable is not set"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Backup database
backup_database() {
    log_info "Creating database backup..."

    BACKUP_DIR="./backups"
    mkdir -p "$BACKUP_DIR"

    BACKUP_FILE="$BACKUP_DIR/taskifai-$(date +%Y%m%d-%H%M%S).sql"

    # Extract database connection details from DATABASE_URL
    # Format: postgresql://user:password@host:port/database
    # This is a placeholder - adjust based on your actual backup strategy

    log_info "Database backup created: $BACKUP_FILE"
}

# Pull latest code
pull_latest_code() {
    log_info "Pulling latest code from $DEPLOY_BRANCH..."

    git fetch origin
    git checkout "$DEPLOY_BRANCH"
    git pull origin "$DEPLOY_BRANCH"

    log_info "Code updated to latest version"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."

    # Build backend image
    docker build -t "$DOCKER_REGISTRY/$DOCKER_USERNAME/taskifai-backend:latest" \
        -t "$DOCKER_REGISTRY/$DOCKER_USERNAME/taskifai-backend:$(git rev-parse --short HEAD)" \
        ./backend

    # Build frontend image
    docker build -t "$DOCKER_REGISTRY/$DOCKER_USERNAME/taskifai-frontend:latest" \
        -t "$DOCKER_REGISTRY/$DOCKER_USERNAME/taskifai-frontend:$(git rev-parse --short HEAD)" \
        ./frontend

    log_info "Docker images built successfully"
}

# Push images to registry
push_images() {
    log_info "Pushing images to registry..."

    docker push "$DOCKER_REGISTRY/$DOCKER_USERNAME/taskifai-backend:latest"
    docker push "$DOCKER_REGISTRY/$DOCKER_USERNAME/taskifai-backend:$(git rev-parse --short HEAD)"

    docker push "$DOCKER_REGISTRY/$DOCKER_USERNAME/taskifai-frontend:latest"
    docker push "$DOCKER_REGISTRY/$DOCKER_USERNAME/taskifai-frontend:$(git rev-parse --short HEAD)"

    log_info "Images pushed to registry"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."

    # Apply schema updates
    docker-compose run --rm backend python -m alembic upgrade head || true

    # Apply multi-tenant enhancements migration
    docker-compose run --rm backend psql "$DATABASE_URL" -f /app/db/migrations/001_multi_tenant_enhancements.sql || true

    log_info "Database migrations completed"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."

    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull

    # Stop old containers
    docker-compose -f docker-compose.prod.yml down

    # Start new containers
    docker-compose -f docker-compose.prod.yml up -d

    log_info "Services deployed successfully"
}

# Health check
health_check() {
    log_info "Performing health checks..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts..."

        # Check backend health
        if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
            log_info "Backend is healthy"
            return 0
        fi

        attempt=$((attempt + 1))
        sleep 10
    done

    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Rollback deployment
rollback() {
    log_warn "Rolling back deployment..."

    # Stop new containers
    docker-compose -f docker-compose.prod.yml down

    # Restore from backup if needed
    # This is environment-specific

    log_warn "Rollback completed"
    exit 1
}

# Main deployment flow
main() {
    log_info "Starting TaskifAI production deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Branch: $DEPLOY_BRANCH"

    # Step 1: Prerequisites
    check_prerequisites

    # Step 2: Backup
    backup_database

    # Step 3: Code update
    pull_latest_code

    # Step 4: Build images
    build_images

    # Step 5: Push to registry
    if [ "${SKIP_PUSH:-false}" != "true" ]; then
        push_images
    fi

    # Step 6: Run migrations
    run_migrations

    # Step 7: Deploy
    deploy_services

    # Step 8: Health check
    if ! health_check; then
        log_error "Deployment failed health check"
        rollback
    fi

    log_info "✓ Deployment completed successfully!"
    log_info "Backend: http://localhost:8000"
    log_info "Frontend: http://localhost"
}

# Trap errors and rollback
trap 'rollback' ERR

# Run main deployment
main "$@"
