#!/bin/bash
# ============================================
# TaskifAI Development Environment Stop
# ============================================
# Stops all Docker Compose services
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if script is run from project root
check_project_root() {
    if [ ! -f "docker-compose.yml" ]; then
        print_error "This script must be run from the project root directory"
        echo ""
        echo "Current directory: $(pwd)"
        echo ""
        echo "Please run: cd /home/david/TaskifAI_platform_v2.0 && ./scripts/dev-stop.sh"
        exit 1
    fi
}

check_project_root

# Parse arguments
REMOVE_VOLUMES=false
if [ "$1" == "--clean" ] || [ "$1" == "-c" ]; then
    REMOVE_VOLUMES=true
    print_warning "Clean mode: Will remove volumes (database data will be lost)"
fi

print_info "Stopping Docker Compose services..."

if [ "$REMOVE_VOLUMES" = true ]; then
    docker compose down -v
    print_success "All services stopped and volumes removed"
    print_warning "Database data has been deleted"
else
    docker compose down
    print_success "All services stopped (data preserved)"
fi

echo ""
echo -e "${BLUE}Services Status:${NC}"
docker compose ps

echo ""
echo -e "${BLUE}To start again:${NC} ${YELLOW}./scripts/dev-start.sh${NC}"
echo -e "${BLUE}To clean volumes:${NC} ${YELLOW}./scripts/dev-stop.sh --clean${NC}"
echo ""
