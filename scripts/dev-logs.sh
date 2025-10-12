#!/bin/bash
# ============================================
# TaskifAI Development Environment Logs
# ============================================
# View logs from Docker Compose services
# Usage: ./scripts/dev-logs.sh [service]
# ============================================

set -e

# Colors
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if script is run from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "This script must be run from the project root directory"
    echo ""
    echo "Current directory: $(pwd)"
    echo ""
    echo "Please run: cd /home/david/TaskifAI_platform_v2.0 && ./scripts/dev-logs.sh"
    exit 1
fi

SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo -e "${BLUE}Available services:${NC}"
    echo "  - backend   (FastAPI API server)"
    echo "  - frontend  (React development server)"
    echo "  - db        (PostgreSQL database)"
    echo "  - redis     (Redis cache)"
    echo "  - worker    (Celery background worker)"
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo "  ${YELLOW}./scripts/dev-logs.sh [service]${NC}  # View specific service"
    echo "  ${YELLOW}./scripts/dev-logs.sh${NC}            # View all services"
    echo ""
    echo -e "${BLUE}Showing logs for all services...${NC}"
    echo ""
    docker compose logs -f --tail=100
else
    echo -e "${BLUE}Showing logs for: ${YELLOW}${SERVICE}${NC}"
    echo ""
    docker compose logs -f --tail=100 "$SERVICE"
fi
