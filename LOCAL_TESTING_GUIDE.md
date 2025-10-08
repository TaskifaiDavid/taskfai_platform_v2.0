# TaskifAI Local Testing Guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Ports available: 5173 (frontend), 8000 (backend), 5432 (postgres), 6379 (redis)

### Step 1: Environment Setup ✅
Environment files have been created:
- `backend/.env` - Backend configuration
- `frontend/.env` - Frontend configuration

**Optional**: Add your OpenAI API key to `backend/.env` if you want to test AI chat features.

### Step 2: Start All Services

```bash
# From project root
docker-compose up --build
```

This will start:
- **PostgreSQL** (port 5432) - Database
- **Redis** (port 6379) - Cache/Queue
- **Backend API** (port 8000) - FastAPI server
- **Celery Worker** - Background tasks
- **Frontend** (port 5173) - React/Vite app

### Step 3: Verify Services

Wait for all containers to be healthy (~30-60 seconds). You should see:
```
✅ taskifai-postgres - Database ready
✅ taskifai-redis - Cache ready
✅ taskifai-backend - API server running
✅ taskifai-worker - Celery worker running
✅ taskifai-frontend - Frontend dev server ready
```

### Step 4: Access the Application

- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health Check**: http://localhost:8000/api/health

## 🧪 Testing Checklist

### Basic Functionality
- [ ] Frontend loads without errors
- [ ] API health endpoint responds
- [ ] Can create/login user account
- [ ] Can switch tenants (if multi-tenant enabled)

### File Upload
- [ ] Can upload vendor files (Excel/CSV)
- [ ] Background worker processes uploads
- [ ] Data appears in dashboard

### Analytics
- [ ] Dashboard shows data
- [ ] Charts render correctly
- [ ] Filters work

### AI Chat (requires OpenAI key)
- [ ] Chat interface loads
- [ ] Can send messages
- [ ] Receives AI responses

## 🔍 Troubleshooting

### Port Conflicts
If ports are in use:
```bash
# Check what's using the ports
sudo lsof -i :5173  # Frontend
sudo lsof -i :8000  # Backend
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :6379  # Redis
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up --build
```

### Container Status
```bash
# Check running containers
docker-compose ps

# Restart specific service
docker-compose restart backend
```

## 🛑 Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (full reset)
docker-compose down -v
```

## 📊 Development Workflow

### Making Backend Changes
1. Edit files in `backend/` directory
2. Changes auto-reload (uvicorn --reload)
3. Check logs: `docker-compose logs -f backend`

### Making Frontend Changes
1. Edit files in `frontend/src/` directory
2. Vite HMR auto-updates browser
3. Check logs: `docker-compose logs -f frontend`

### Database Migrations
```bash
# Access backend container
docker exec -it taskifai-backend bash

# Run migrations (if needed)
alembic upgrade head
```

## 🔐 Default Test Credentials

The system uses email/password authentication. You'll need to register via the UI or API:

**Register via API**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@taskifai.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'
```

## 📝 Key URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Interactive Swagger UI |
| Health Check | http://localhost:8000/api/health | System status |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |

## 🎯 What to Test Before Deployment

### Critical Features
1. **Authentication**: Register, login, logout
2. **Multi-Tenancy**: Tenant switching (if enabled)
3. **File Upload**: Vendor data ingestion
4. **Data Pipeline**: Background processing
5. **Dashboard**: Analytics display
6. **Error Handling**: Invalid inputs, network errors

### Performance
- File upload speed (test with real vendor files)
- Dashboard load time
- API response times

### Security
- CORS configured correctly
- Authentication required for protected routes
- Tenant isolation working

## 🚀 Ready for DigitalOcean?

Once local testing is complete:
1. All services start without errors ✅
2. Frontend connects to backend ✅
3. File uploads work ✅
4. Dashboard displays data ✅
5. No console errors ✅

Proceed with DigitalOcean deployment using `DIGITALOCEAN_DEPLOYMENT.md`
