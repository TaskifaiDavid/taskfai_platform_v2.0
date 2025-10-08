# TaskifAI Local Testing - Native Setup (No Docker)

## 🚀 Quick Start Without Docker

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

## Step-by-Step Setup

### 1. Install PostgreSQL & Redis

**Ubuntu/Debian**:
```bash
# PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Redis
sudo apt install redis-server

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
```

**macOS**:
```bash
# Using Homebrew
brew install postgresql@15
brew install redis

# Start services
brew services start postgresql@15
brew services start redis
```

### 2. Setup Database

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE taskifai;
CREATE USER taskifai WITH PASSWORD 'taskifai_dev_password';
GRANT ALL PRIVILEGES ON DATABASE taskifai TO taskifai;
\q
```

Load schema:
```bash
psql -U taskifai -d taskifai -f backend/db/schema.sql
psql -U taskifai -d taskifai -f backend/db/seed_vendor_configs.sql
```

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Update .env for local services
# Edit backend/.env and change:
# DATABASE_URL=postgresql://taskifai:taskifai_dev_password@localhost:5432/taskifai
# REDIS_URL=redis://localhost:6379/0
```

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Verify .env is configured
# VITE_API_URL=http://localhost:8000
```

### 5. Start Services

**Terminal 1 - Backend API**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Celery Worker**:
```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

**Terminal 3 - Frontend**:
```bash
cd frontend
npm run dev
```

### 6. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🔍 Verify Services

```bash
# PostgreSQL
psql -U taskifai -d taskifai -c "SELECT version();"

# Redis
redis-cli ping  # Should return PONG

# Backend
curl http://localhost:8000/api/health

# Frontend
curl http://localhost:5173
```

## 🛑 Stopping Services

- Press `Ctrl+C` in each terminal
- Or use `pkill -f uvicorn` and `pkill -f celery`

## 📝 Environment Variables

**backend/.env**:
```bash
DATABASE_URL=postgresql://taskifai:taskifai_dev_password@localhost:5432/taskifai
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
ENVIRONMENT=development
DEBUG=true
```

**frontend/.env**:
```bash
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development
```

## 🧪 Testing

Same testing checklist as Docker setup - see LOCAL_TESTING_GUIDE.md

## 🚨 Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U taskifai -d taskifai
```

### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping

# Restart Redis
sudo systemctl restart redis-server
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000  # Backend
sudo lsof -i :5173  # Frontend

# Kill process
kill -9 <PID>
```

### Python Dependencies
```bash
# If pip install fails
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```
