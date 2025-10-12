#!/bin/bash
# ============================================
# TaskifAI Development Environment Startup
# ============================================
# Starts all services via Docker Compose
# Creates missing .env files automatically
# ============================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  TaskifAI Development Environment${NC}"
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
    echo ""
}

# Check if script is run from project root
check_project_root() {
    if [ ! -f "docker-compose.yml" ]; then
        print_error "This script must be run from the project root directory"
        echo ""
        echo "Current directory: $(pwd)"
        echo ""
        echo "Please run from project root:"
        echo -e "  ${YELLOW}cd /home/david/TaskifAI_platform_v2.0${NC}"
        echo -e "  ${YELLOW}./scripts/dev-start.sh${NC}"
        exit 1
    fi
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed"
}

# Check if Docker is running
check_docker_running() {
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        echo "Please start Docker Desktop"
        exit 1
    fi
    print_success "Docker is running"
}

# Check if docker-compose is available
check_docker_compose() {
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Create backend .env if missing
create_backend_env() {
    if [ ! -f "backend/.env" ]; then
        if [ -f "backend/.env.example" ]; then
            print_info "Creating backend/.env from .env.example"
            cp backend/.env.example backend/.env
            print_warning "Please update backend/.env with your credentials"
        else
            print_warning "backend/.env.example not found, creating minimal .env"
            cat > backend/.env << EOF
# ============================================
# TaskifAI Backend Environment (Local Dev)
# ============================================

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database (Docker Compose default)
SUPABASE_URL=postgresql://taskifai:taskifai_dev_password@db:5432/taskifai
DATABASE_URL=postgresql://taskifai:taskifai_dev_password@db:5432/taskifai

# Redis (Docker Compose default)
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=development
DEBUG=true

# Optional: Add your API keys here
# OPENAI_API_KEY=your_key_here
# SENDGRID_API_KEY=your_key_here
EOF
        fi
        print_success "Created backend/.env"
    else
        print_success "backend/.env exists"
    fi
}

# Create frontend .env if missing
create_frontend_env() {
    if [ ! -f "frontend/.env" ]; then
        print_info "Creating frontend/.env"
        cat > frontend/.env << EOF
# ============================================
# TaskifAI Frontend Environment (Local Dev)
# ============================================

# API Configuration
VITE_API_URL=http://localhost:8000

# Environment
VITE_ENVIRONMENT=development
EOF
        print_success "Created frontend/.env"
    else
        print_success "frontend/.env exists"
    fi
}

# Start Docker Compose
start_services() {
    print_info "Starting Docker Compose services..."
    docker compose up -d
    print_success "Services started"
}

# Wait for services to be healthy
wait_for_health() {
    print_info "Waiting for services to be healthy..."

    # Wait for database
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker compose exec -T db pg_isready -U taskifai &> /dev/null; then
            print_success "Database is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    if [ $attempt -eq $max_attempts ]; then
        print_warning "Database health check timed out (but may still be starting)"
    fi

    # Give backend a moment to start
    sleep 2

    # Check backend health
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        print_success "Backend is ready"
    else
        print_warning "Backend is starting (may take a moment)"
    fi
}

# Show access information
show_info() {
    echo ""
    echo -e "${GREEN}🚀 TaskifAI Development Environment is Ready!${NC}"
    echo ""
    echo -e "${BLUE}Access URLs:${NC}"
    echo -e "  Frontend:  ${GREEN}http://localhost:5173${NC}"
    echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
    echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  Database:  ${GREEN}localhost:5432${NC} (user: taskifai, password: taskifai_dev_password)"
    echo -e "  Redis:     ${GREEN}localhost:6379${NC}"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "  View logs:     ${YELLOW}./scripts/dev-logs.sh${NC}"
    echo -e "  Stop services: ${YELLOW}./scripts/dev-stop.sh${NC}"
    echo -e "  Restart:       ${YELLOW}./scripts/dev-restart.sh${NC}"
    echo -e "  Run tests:     ${YELLOW}./scripts/dev-test.sh${NC}"
    echo ""
    echo -e "${BLUE}Or use Docker Compose directly:${NC}"
    echo -e "  ${YELLOW}docker compose logs -f backend${NC}  # View backend logs"
    echo -e "  ${YELLOW}docker compose ps${NC}                # Show running services"
    echo -e "  ${YELLOW}docker compose down${NC}              # Stop all services"
    echo ""
}

# Main execution
main() {
    print_header

    check_project_root
    check_docker
    check_docker_running
    check_docker_compose

    echo ""
    print_info "Setting up environment files..."
    create_backend_env
    create_frontend_env

    echo ""
    start_services

    echo ""
    wait_for_health

    show_info
}

main
