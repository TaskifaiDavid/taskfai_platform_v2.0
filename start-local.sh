#!/bin/bash
# ============================================
# TaskifAI Local Development Startup Script
# ============================================

set -e

echo "🚀 TaskifAI Local Development Startup"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version | cut -d' ' -f2)${NC}"

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js $(node --version)${NC}"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠ PostgreSQL not found. Install with: sudo apt install postgresql${NC}"
    echo "Do you want to continue without PostgreSQL? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ PostgreSQL installed${NC}"

    # Check if PostgreSQL is running
    if ! systemctl is-active --quiet postgresql 2>/dev/null; then
        echo -e "${YELLOW}⚠ PostgreSQL not running. Starting...${NC}"
        sudo systemctl start postgresql || echo -e "${RED}Failed to start PostgreSQL${NC}"
    else
        echo -e "${GREEN}✓ PostgreSQL running${NC}"
    fi
fi

# Check Redis
if ! command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}⚠ Redis not found. Install with: sudo apt install redis-server${NC}"
    echo "Do you want to continue without Redis? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Redis installed${NC}"

    # Check if Redis is running
    if ! redis-cli ping &> /dev/null; then
        echo -e "${YELLOW}⚠ Redis not running. Starting...${NC}"
        sudo systemctl start redis-server || echo -e "${RED}Failed to start Redis${NC}"
    else
        echo -e "${GREEN}✓ Redis running${NC}"
    fi
fi

echo ""
echo "======================================"
echo "📦 Setting up services..."
echo "======================================"
echo ""

# Setup Backend
echo "🔧 Backend Setup"
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ backend/.env not found, using example${NC}"
    cp ../.env.example .env 2>/dev/null || true
fi

echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

cd ..

# Setup Frontend
echo ""
echo "🎨 Frontend Setup"
cd frontend

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ frontend/.env not found, creating...${NC}"
    echo "VITE_API_URL=http://localhost:8000" > .env
    echo "VITE_ENVIRONMENT=development" >> .env
fi

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
else
    echo "Node modules already installed"
fi

cd ..

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Start Backend API (Terminal 1):"
echo "   cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "2. Start Celery Worker (Terminal 2):"
echo "   cd backend && source venv/bin/activate && celery -A app.workers.celery_app worker --loglevel=info"
echo ""
echo "3. Start Frontend (Terminal 3):"
echo "   cd frontend && npm run dev"
echo ""
echo "Or use the helper scripts:"
echo "   ./start-backend.sh"
echo "   ./start-worker.sh"
echo "   ./start-frontend.sh"
echo ""
echo "🌐 Access Points:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/api/health"
echo ""
