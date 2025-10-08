# 🚀 TaskifAI Quick Start Guide

## Option 1: Docker Setup (Recommended)

### Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then verify
docker --version
```

### Start Application
```bash
docker compose up --build
```

**Access**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

---

## Option 2: Native Setup (No Docker)

### 1. Install Prerequisites

**PostgreSQL & Redis**:
```bash
sudo apt update
sudo apt install postgresql redis-server
sudo systemctl start postgresql redis-server
```

**Setup Database**:
```bash
sudo -u postgres psql -c "CREATE DATABASE taskifai;"
sudo -u postgres psql -c "CREATE USER taskifai WITH PASSWORD 'taskifai_dev_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE taskifai TO taskifai;"
```

### 2. Run Setup Script
```bash
./start-local.sh
```

### 3. Start Services (3 Terminals)

**Terminal 1 - Backend**:
```bash
./start-backend.sh
```

**Terminal 2 - Worker**:
```bash
./start-worker.sh
```

**Terminal 3 - Frontend**:
```bash
./start-frontend.sh
```

**Access**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

---

## ✅ Verify Setup

```bash
# Check health
curl http://localhost:8000/api/health

# Should return: {"status":"ok"}
```

---

## 🧪 Test the Application

1. **Open Frontend**: http://localhost:5173
2. **Register Account**: Create test user
3. **Upload File**: Try vendor data upload
4. **View Dashboard**: Check analytics display

---

## 🛑 Stop Services

**Docker**:
```bash
docker compose down
```

**Native**:
Press `Ctrl+C` in each terminal

---

## 📚 Detailed Guides

- **Docker Setup**: See `LOCAL_TESTING_GUIDE.md`
- **Native Setup**: See `LOCAL_TESTING_NATIVE.md`
- **Deployment**: See `DIGITALOCEAN_DEPLOYMENT.md`

---

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Find process
sudo lsof -i :8000  # Backend
sudo lsof -i :5173  # Frontend

# Kill process
kill -9 <PID>
```

### PostgreSQL Connection Error
```bash
# Restart PostgreSQL
sudo systemctl restart postgresql

# Test connection
psql -U taskifai -d taskifai
```

### Redis Connection Error
```bash
# Restart Redis
sudo systemctl restart redis-server

# Test connection
redis-cli ping  # Should return PONG
```

### Backend Import Errors
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Build Errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 🎯 Quick Commands

```bash
# Setup everything
./start-local.sh

# Start services
./start-backend.sh   # Terminal 1
./start-worker.sh    # Terminal 2
./start-frontend.sh  # Terminal 3

# Or with Docker
docker compose up --build

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Reset everything
docker compose down -v  # Docker
# or
dropdb -U taskifai taskifai && createdb -U taskifai taskifai  # Native
```

---

## 📝 Next Steps

1. ✅ Test locally (this guide)
2. 🔑 Add OpenAI API key (optional - for AI chat)
3. 📊 Upload vendor data files
4. 🚀 Deploy to DigitalOcean (see `DIGITALOCEAN_DEPLOYMENT.md`)
