#!/bin/bash

# BIBBI v2 - Development Setup Script
# This script sets up the development environment

set -e

echo "🚀 BIBBI v2 Development Setup"
echo "================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env files exist
echo ""
echo "📝 Checking environment files..."

if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  backend/.env not found. Copying from .env.example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}⚠️  Please edit backend/.env with your actual credentials!${NC}"
else
    echo -e "${GREEN}✅ backend/.env exists${NC}"
fi

if [ ! -f "frontend/.env" ]; then
    echo -e "${YELLOW}⚠️  frontend/.env not found. Copying from .env.example...${NC}"
    cp frontend/.env.example frontend/.env
else
    echo -e "${GREEN}✅ frontend/.env exists${NC}"
fi

# Start Docker Compose
echo ""
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API is running${NC}"
else
    echo -e "${YELLOW}⚠️  Backend API not responding yet. Check logs with: docker-compose logs backend${NC}"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend not responding yet. Check logs with: docker-compose logs frontend${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}✨ Setup Complete!${NC}"
echo ""
echo "Access the application:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API Docs: http://localhost:8000/api/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart services: docker-compose restart"
echo ""
