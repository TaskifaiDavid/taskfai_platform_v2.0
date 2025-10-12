#!/bin/bash
# ============================================
# TaskifAI Development Environment Testing
# ============================================
# Run backend and/or frontend tests
# Usage: ./scripts/dev-test.sh [backend|frontend|all]
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
    echo ""
}

# Check if script is run from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "This script must be run from the project root directory"
    echo ""
    echo "Current directory: $(pwd)"
    echo ""
    echo "Please run: cd /home/david/TaskifAI_platform_v2.0 && ./scripts/dev-test.sh"
    exit 1
fi

# Run backend tests
run_backend_tests() {
    print_header "Backend Tests (pytest)"

    if docker compose ps backend | grep -q "Up"; then
        print_info "Running tests in backend container..."
        if docker compose exec -T backend pytest tests/ -v --tb=short; then
            print_success "Backend tests passed"
            return 0
        else
            print_error "Backend tests failed"
            return 1
        fi
    else
        print_error "Backend container is not running"
        echo "Start services with: ./scripts/dev-start.sh"
        return 1
    fi
}

# Run frontend tests
run_frontend_tests() {
    print_header "Frontend Tests (Vitest)"

    if docker compose ps frontend | grep -q "Up"; then
        print_info "Running tests in frontend container..."
        if docker compose exec -T frontend npm test -- --run; then
            print_success "Frontend tests passed"
            return 0
        else
            print_error "Frontend tests failed"
            return 1
        fi
    else
        print_error "Frontend container is not running"
        echo "Start services with: ./scripts/dev-start.sh"
        return 1
    fi
}

# Main execution
COMPONENT=${1:-all}
BACKEND_RESULT=0
FRONTEND_RESULT=0

case $COMPONENT in
    backend)
        run_backend_tests
        BACKEND_RESULT=$?
        ;;
    frontend)
        run_frontend_tests
        FRONTEND_RESULT=$?
        ;;
    all)
        run_backend_tests
        BACKEND_RESULT=$?
        echo ""
        run_frontend_tests
        FRONTEND_RESULT=$?
        ;;
    *)
        print_error "Invalid component: $COMPONENT"
        echo ""
        echo -e "${BLUE}Usage:${NC}"
        echo -e "  ${YELLOW}./scripts/dev-test.sh${NC}            # Run all tests"
        echo -e "  ${YELLOW}./scripts/dev-test.sh backend${NC}   # Run backend tests only"
        echo -e "  ${YELLOW}./scripts/dev-test.sh frontend${NC}  # Run frontend tests only"
        exit 1
        ;;
esac

# Summary
echo ""
print_header "Test Summary"

if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "backend" ]; then
    if [ $BACKEND_RESULT -eq 0 ]; then
        echo -e "  Backend:  ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  Backend:  ${RED}✗ FAILED${NC}"
    fi
fi

if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "frontend" ]; then
    if [ $FRONTEND_RESULT -eq 0 ]; then
        echo -e "  Frontend: ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  Frontend: ${RED}✗ FAILED${NC}"
    fi
fi

echo ""

# Exit with failure if any tests failed
if [ $BACKEND_RESULT -ne 0 ] || [ $FRONTEND_RESULT -ne 0 ]; then
    exit 1
fi

exit 0
