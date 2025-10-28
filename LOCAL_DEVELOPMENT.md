# Local Development Environment Setup

This guide explains how to set up and use the local Docker-based development environment for TaskifAI.

## Overview

Your project now supports **two separate environments**:

1. **Local Development** (`.env.local` files) - For testing before pushing to git
2. **Production** (`.env` files) - For deployed environments (DigitalOcean, etc.)

## Quick Start

### 1. Start Docker Desktop

Make sure Docker Desktop is running on your machine.

### 2. Start Local Environment

```bash
# Start all services (PostgreSQL, Redis, Backend, Worker, Frontend)
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Stop Local Environment

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Environment Files Explained

### Backend Environment Files

- **`backend/.env.local`** - Local development (Docker)
  - Uses local PostgreSQL: `postgresql://taskifai:taskifai_dev_password@db:5432/taskifai`
  - Uses local Redis: `redis://redis:6379/0`
  - Still uses Supabase for data storage (or configure local DB)
  - **GIT**: ✅ Ignored (safe to modify)

- **`backend/.env`** - Production environment
  - Uses production Supabase database
  - Uses production Redis (DigitalOcean)
  - **GIT**: ✅ Ignored (never commit!)

- **`backend/.env.example`** - Template for reference
  - **GIT**: ✅ Committed (no secrets)

### Frontend Environment Files

- **`frontend/.env.local`** - Local development
  - Points to local backend: `VITE_API_URL=http://localhost:8000`
  - **GIT**: ✅ Ignored (safe to modify)

- **`frontend/.env`** - Production environment
  - Points to production backend
  - **GIT**: ✅ Ignored (never commit!)

- **`frontend/.env.example`** - Template for reference
  - **GIT**: ✅ Committed (no secrets)

## Common Tasks

### View Running Services

```bash
docker-compose ps
```

### Rebuild Services After Code Changes

```bash
# Rebuild and restart all services
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend
```

### Access Service Shells

```bash
# Backend shell
docker exec -it taskifai-backend bash

# PostgreSQL shell
docker exec -it taskifai-postgres psql -U taskifai -d taskifai

# Redis CLI
docker exec -it taskifai-redis redis-cli
```

### Run Backend Tests

```bash
# From host machine
docker exec -it taskifai-backend pytest

# Or enter container and run
docker exec -it taskifai-backend bash
pytest
pytest tests/test_file.py  # Specific test
```

### Check Celery Worker

```bash
# View worker logs
docker-compose logs -f worker

# Check active tasks
docker exec -it taskifai-worker celery -A app.workers.celery_app inspect active
```

### Database Operations

```bash
# Access PostgreSQL
docker exec -it taskifai-postgres psql -U taskifai -d taskifai

# Run SQL file
docker exec -i taskifai-postgres psql -U taskifai -d taskifai < backend/db/schema.sql

# Backup database
docker exec taskifai-postgres pg_dump -U taskifai taskifai > backup.sql

# Restore database
docker exec -i taskifai-postgres psql -U taskifai -d taskifai < backup.sql
```

## Switching Between Environments

### Local Development Workflow

1. Make code changes in your editor
2. Test locally with `docker-compose up -d`
3. Verify everything works at http://localhost:5173
4. Commit and push to git
5. Deploy to production (DigitalOcean uses `.env` files)

### Using Production Data Locally (Optional)

If you want to test with production data locally:

1. Keep the Supabase URLs in `backend/.env.local`
2. Copy your OpenAI API key to `backend/.env.local`
3. Copy SendGrid API key if testing emails

**Warning**: Changes made locally will affect production data!

### Using Fully Local Database (Advanced)

To use a completely local PostgreSQL database:

1. Edit `backend/.env.local`:
   ```bash
   # Comment out or remove Supabase URLs
   # SUPABASE_URL=...
   # SUPABASE_SERVICE_KEY=...
   ```

2. Run database migrations:
   ```bash
   docker exec -i taskifai-postgres psql -U taskifai -d taskifai < backend/db/schema.sql
   docker exec -i taskifai-postgres psql -U taskifai -d taskifai < backend/db/seed_vendor_configs.sql
   ```

3. Update backend code to use PostgreSQL directly instead of Supabase client

## Troubleshooting

### Docker Not Starting

```bash
# Check Docker is running
docker ps

# Restart Docker Desktop
# Then try: docker-compose up -d
```

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :8000  # Backend
sudo lsof -i :5173  # Frontend
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :6379  # Redis

# Kill the process or change port in docker-compose.yml
```

### Backend Health Check Failing

```bash
# Check backend logs
docker-compose logs backend

# Common issues:
# - Missing environment variables in .env.local
# - Database connection failed
# - Redis connection failed

# Verify services are healthy
docker-compose ps
```

### Database Connection Error

```bash
# Ensure PostgreSQL is healthy
docker-compose ps db

# Check PostgreSQL logs
docker-compose logs db

# Restart PostgreSQL
docker-compose restart db
```

### Clean Slate (Reset Everything)

```bash
# Stop and remove all containers, volumes, and networks
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Frontend Not Connecting to Backend

1. Check `frontend/.env.local` has `VITE_API_URL=http://localhost:8000`
2. Check backend is running: http://localhost:8000/health
3. Check browser console for CORS errors
4. Verify `backend/.env.local` has `CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]`

## Service Ports

| Service    | Port | URL                       |
|------------|------|---------------------------|
| Frontend   | 5173 | http://localhost:5173     |
| Backend    | 8000 | http://localhost:8000     |
| PostgreSQL | 5432 | localhost:5432            |
| Redis      | 6379 | localhost:6379            |

## Git Workflow

### ✅ Safe Operations

```bash
# Your production .env files are ignored by git
git status  # .env.local files won't appear

# Commit your code changes
git add backend/app/
git commit -m "Add new feature"
git push
```

### ⚠️ Never Commit

- `backend/.env` (production secrets)
- `frontend/.env` (production config)
- `backend/.env.local` (local config - already ignored)
- `frontend/.env.local` (local config - already ignored)

### ✅ Safe to Commit

- `backend/.env.example` (template)
- `frontend/.env.example` (template)
- All source code
- `docker-compose.yml`
- This `LOCAL_DEVELOPMENT.md` file

## Testing Before Production

### Recommended Workflow

1. **Local Development**
   ```bash
   # Make changes
   docker-compose up -d
   # Test at http://localhost:5173
   ```

2. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature-branch
   ```

3. **Create Pull Request**
   - Review changes on GitHub
   - Run automated tests (if configured)

4. **Merge to Main**
   - DigitalOcean automatically deploys
   - Uses production `.env` files (not in git)

## Optional: OpenAI & SendGrid for Local Testing

If you want to test AI chat or email features locally:

1. Edit `backend/.env.local`:
   ```bash
   # Add your API keys
   OPENAI_API_KEY=sk-your-key-here
   SENDGRID_API_KEY=SG.your-key-here
   SENDGRID_FROM_EMAIL=dev@yourdomain.com
   ```

2. Restart backend:
   ```bash
   docker-compose restart backend worker
   ```

If you leave these empty, those features just won't work locally (no errors).

## Summary

**Local Development** = Docker containers + `.env.local` files
**Production** = DigitalOcean deployment + `.env` files (not in git)
**Git** = Source code only (no `.env` files committed)

Your production environment is completely isolated from local testing! 🎉
