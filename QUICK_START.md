# Quick Start Guide

## Start Local Development Environment

```bash
# 1. Start Docker Desktop (ensure it's running)

# 2. Start all services
docker compose up -d

# 3. View logs (optional)
docker compose logs -f

# 4. Access application
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs

# 5. Stop when done
docker compose down
```

## Verify Everything is Running

```bash
# Check service status
docker compose ps

# Should show all services as "healthy" or "running":
# - taskifai-postgres (healthy)
# - taskifai-redis (healthy)
# - taskifai-backend (healthy)
# - taskifai-worker (running)
# - taskifai-frontend (running)
```

## Common Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Restart a specific service
docker compose restart backend

# View logs
docker compose logs -f backend

# Rebuild after code changes
docker compose up -d --build

# Clean slate (remove all data)
docker compose down -v
```

## First Time Setup

### Backend Configuration

The `backend/.env.local` file is already configured for local development:
- Local PostgreSQL database
- Local Redis
- Supabase connection (for data storage)

**Optional**: Add API keys if testing AI or email features:
```bash
# Edit backend/.env.local
OPENAI_API_KEY=sk-your-key-here
SENDGRID_API_KEY=SG.your-key-here
```

### Frontend Configuration

The `frontend/.env.local` file is already configured:
- Points to local backend: `http://localhost:8000`

## Troubleshooting

### Services won't start?

```bash
# Check Docker is running
docker ps

# Check logs for errors
docker compose logs
```

### Port conflicts?

If port 8000, 5173, 5432, or 6379 is already in use:
```bash
# Find what's using the port
sudo lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

### Need a clean slate?

```bash
# Stop and remove everything
docker compose down -v

# Start fresh
docker compose up -d
```

## Development Workflow

1. **Start Environment**: `docker compose up -d`
2. **Make Code Changes**: Edit files in your IDE
3. **Test**: http://localhost:5173
4. **Commit**: `git add . && git commit -m "description"`
5. **Push**: `git push`
6. **Deploy**: DigitalOcean auto-deploys production

## What's Different from Production?

| Aspect | Local Development | Production |
|--------|-------------------|------------|
| Database | Local PostgreSQL (Docker) | Supabase Cloud |
| Redis | Local Redis (Docker) | DigitalOcean Managed Redis |
| Config | `.env.local` files | `.env` files |
| URL | http://localhost:5173 | https://demo.taskifai.com |
| Git | `.env.local` ignored ✅ | `.env` ignored ✅ |

## Need More Help?

See `LOCAL_DEVELOPMENT.md` for comprehensive documentation.
