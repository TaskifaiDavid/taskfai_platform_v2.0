#!/bin/bash
# ============================================
# TaskifAI Development Environment Restart
# ============================================
# Restart one or all services
# Usage: ./scripts/dev-restart.sh [service]
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Check if script is run from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "This script must be run from the project root directory"
    echo ""
    echo "Current directory: $(pwd)"
    echo ""
    echo "Please run: cd /home/david/TaskifAI_platform_v2.0 && ./scripts/dev-restart.sh"
    exit 1
fi

SERVICE=$1

if [ -z "$SERVICE" ]; then
    print_info "Restarting all services..."
    docker compose restart
    print_success "All services restarted"
else
    print_info "Restarting ${SERVICE}..."
    docker compose restart "$SERVICE"
    print_success "${SERVICE} restarted"
fi

echo ""
echo -e "${BLUE}Service Status:${NC}"
docker compose ps

echo ""
echo -e "${BLUE}View logs:${NC} ${YELLOW}./scripts/dev-logs.sh${NC}"
echo ""
