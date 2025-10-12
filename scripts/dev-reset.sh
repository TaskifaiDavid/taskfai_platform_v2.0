#!/bin/bash
# ============================================
# TaskifAI Development Database Reset
# ============================================
# Drops and recreates database with fresh schema
# WARNING: This will DELETE ALL DATA
# Usage: ./scripts/dev-reset.sh [--force]
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

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if script is run from project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "This script must be run from the project root directory"
    echo ""
    echo "Current directory: $(pwd)"
    echo ""
    echo "Please run: cd /home/david/TaskifAI_platform_v2.0 && ./scripts/dev-reset.sh"
    exit 1
fi

# Check if database is running
check_database() {
    if ! docker compose ps db | grep -q "Up"; then
        print_error "Database container is not running"
        echo "Start services with: ./scripts/dev-start.sh"
        exit 1
    fi
    print_success "Database container is running"
}

# Confirm action
confirm_reset() {
    if [ "$1" != "--force" ]; then
        echo ""
        print_warning "THIS WILL DELETE ALL DATABASE DATA"
        echo ""
        read -p "Are you sure you want to continue? (type 'yes' to confirm): " response
        if [ "$response" != "yes" ]; then
            print_info "Reset cancelled"
            exit 0
        fi
    fi
}

# Reset database
reset_database() {
    print_info "Dropping and recreating database..."

    # Drop all connections and recreate database
    docker compose exec -T db psql -U taskifai -d postgres << 'EOF'
-- Terminate existing connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'taskifai' AND pid <> pg_backend_pid();

-- Drop and recreate database
DROP DATABASE IF EXISTS taskifai;
CREATE DATABASE taskifai OWNER taskifai;
EOF

    print_success "Database recreated"
}

# Apply schema
apply_schema() {
    print_info "Applying database schema..."

    if [ ! -f "backend/db/schema.sql" ]; then
        print_error "Schema file not found: backend/db/schema.sql"
        exit 1
    fi

    docker compose exec -T db psql -U taskifai -d taskifai < backend/db/schema.sql

    print_success "Schema applied"
}

# Apply seed data
apply_seed_data() {
    print_info "Applying seed data..."

    if [ -f "backend/db/seed_vendor_configs.sql" ]; then
        docker compose exec -T db psql -U taskifai -d taskifai < backend/db/seed_vendor_configs.sql
        print_success "Vendor configurations seeded"
    else
        print_warning "Seed file not found: backend/db/seed_vendor_configs.sql (skipping)"
    fi
}

# Main execution
print_warning "Database Reset Tool"
echo ""

check_database
confirm_reset "$1"

echo ""
reset_database
apply_schema
apply_seed_data

echo ""
print_success "Database reset complete"
echo ""
print_info "You may need to restart the backend service:"
echo "  ./scripts/dev-restart.sh backend"
echo ""
