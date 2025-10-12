# TaskifAI Demo Server Configuration

**App Name:** taskifai-demo
**Region:** Amsterdam (ams)
**App ID:** ef090864-9e06-4a9a-96fb-276a047cf479
**Repository:** TaskifaiDavid/taskfai_platform_v2.0
**Branch:** master
**Auto-deploy:** Enabled

---

## Components

### 1. API Service (demo-api)

**Service Type:** FastAPI Web Service
**Instance Size:** professional-xs
**Instance Count:** 1
**HTTP Port:** 8000
**Dockerfile:** `backend/Dockerfile`

#### Health Check Configuration
- **Path:** `/health`
- **Initial Delay:** 30 seconds
- **Period:** 10 seconds
- **Timeout:** 5 seconds
- **Success Threshold:** 1
- **Failure Threshold:** 3

#### Environment Variables
```bash
APP_NAME="TaskifAI Analytics Platform - Demo"
DEBUG=false
SECRET_KEY=<encrypted>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Supabase Main Database
SUPABASE_URL=https://afualzsndhnbsuruwese.supabase.co
SUPABASE_ANON_KEY=<encrypted>
SUPABASE_SERVICE_KEY=<encrypted>

# Redis (Upstash)
REDIS_URL=redis://default:AVUsAAIncDJiNGM0NTc5ZGM3NDQ0MTgzOGJmNmVhZDFiNjFlMWIxNXAyMjE4MDQ@real-imp-21804.upstash.io:6379

# OpenAI
OPENAI_API_KEY=<encrypted>

# Upload Configuration
MAX_UPLOAD_SIZE=104857600  # 100MB
UPLOAD_DIR=/tmp/uploads

# CORS
ALLOWED_ORIGINS=https://demo.taskifai.com
```

---

### 2. Celery Worker (demo-worker)

**Service Type:** Background Worker
**Instance Size:** basic-xxs
**Instance Count:** 1
**Run Command:** `celery -A app.workers.celery_app worker --loglevel=info --concurrency=4`
**Dockerfile:** `backend/Dockerfile`

#### Environment Variables
```bash
APP_NAME="TaskifAI Analytics Platform - Demo"
DEBUG=false
SECRET_KEY=<encrypted>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Supabase Main Database
SUPABASE_URL=https://afualzsndhnbsuruwese.supabase.co
SUPABASE_ANON_KEY=<encrypted>
SUPABASE_SERVICE_KEY=<encrypted>

# Redis (Upstash)
REDIS_URL=redis://default:AVUsAAIncDJiNGM0NTc5ZGM3NDQ0MTgzOGJmNmVhZDFiNjFlMWIxNXAyMjE4MDQ@real-imp-21804.upstash.io:6379

# OpenAI
OPENAI_API_KEY=<encrypted>

# Upload Configuration
MAX_UPLOAD_SIZE=104857600  # 100MB
UPLOAD_DIR=/tmp/uploads

# CORS
ALLOWED_ORIGINS=https://demo.taskifai.com
```

---

## Global Environment Variables

These variables are set at the app level:

```bash
SUPABASE_URL=https://afualzsndhnbsuruwese.supabase.co
SUPABASE_ANON_KEY=<encrypted>
SUPABASE_SERVICE_KEY=<encrypted>
ENVIRONMENT=development
ALLOWED_ORIGINS_STR=http://localhost:3000,http://localhost:5173
OPEN_API_KEY=<encrypted>
DEBUG=false
REDIS_URL=<encrypted>

# Tenant Registry Database (Supabase)
TENANT_REGISTRY_URL=https://jzyvvmzkhprmqrqmxzdv.supabase.co
TENANT_REGISTRY_ANON_KEY=<encrypted>
TENANT_REGISTRY_SERVICE_KEY=<encrypted>
```

---

## Ingress Configuration

**Routing Rule:**
- Path prefix: `/`
- Target component: `demo-api`

All incoming requests are routed to the demo-api service.

---

## Features

- **Build Stack:** Ubuntu 22.04 (`buildpack-stack=ubuntu-22`)
- **Auto Deploy:** Enabled on push to master branch
- **Multi-tenant:** Tenant registry database for subdomain routing

---

## Dependencies

### Critical Version Constraints

From `backend/requirements.txt`:

```python
# Authentication & Security
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=3.2.0,<4.0.0  # CRITICAL: Must be 3.x for passlib 1.7.4 compatibility
python-dotenv>=1.0.0
```

**Important:** bcrypt must be pinned to version 3.x range because:
- passlib 1.7.4 is the latest stable version (1.7.5 doesn't exist)
- bcrypt 4.x removed the `__about__` attribute that passlib 1.7.4 expects
- This constraint resolves password verification errors

---

## Deployment Notes

### Current Status
- **Deployment ID:** d13619dd-328a-4512-99e5-2fe7f9a6800d
- **Commit:** 2719eca9e1fa65ec6165f6e076fb0b9f04406b17
- **Status:** ACTIVE and HEALTHY
- **Build Time:** ~4.9 minutes
  - demo-api: 116 seconds
  - demo-worker: 134 seconds

### Health Status
- **demo-api:**
  - CPU: 2.45%
  - Memory: 18.55%
  - State: HEALTHY
  - Replicas: 1/1 ready

- **demo-worker:**
  - CPU: 4.35%
  - Memory: 91.38%
  - State: HEALTHY
  - Replicas: 1/1 ready

### Access URLs
- **Backend API:** https://taskifai-demo-ak4kq.ondigitalocean.app
- **Frontend:** https://demo.taskifai.com (hosted separately on DigitalOcean Spaces)

---

## Replication Guide

To replicate this configuration for a new environment:

### 1. Create App Spec JSON

```json
{
  "name": "taskifai-[environment]",
  "region": "ams",
  "services": [
    {
      "name": "[environment]-api",
      "github": {
        "repo": "TaskifaiDavid/taskfai_platform_v2.0",
        "branch": "master",
        "deploy_on_push": true
      },
      "dockerfile_path": "backend/Dockerfile",
      "instance_size_slug": "professional-xs",
      "instance_count": 1,
      "http_port": 8000,
      "health_check": {
        "http_path": "/health",
        "initial_delay_seconds": 30,
        "period_seconds": 10,
        "timeout_seconds": 5,
        "success_threshold": 1,
        "failure_threshold": 3
      },
      "envs": [
        // Copy environment variables from demo-api section
      ]
    }
  ],
  "workers": [
    {
      "name": "[environment]-worker",
      "github": {
        "repo": "TaskifaiDavid/taskfai_platform_v2.0",
        "branch": "master",
        "deploy_on_push": true
      },
      "dockerfile_path": "backend/Dockerfile",
      "run_command": "celery -A app.workers.celery_app worker --loglevel=info --concurrency=4",
      "instance_size_slug": "basic-xxs",
      "instance_count": 1,
      "envs": [
        // Copy environment variables from demo-worker section
      ]
    }
  ],
  "features": ["buildpack-stack=ubuntu-22"]
}
```

### 2. Set Environment Variables

Replace `<encrypted>` values with actual credentials:
- Generate new SECRET_KEY: `openssl rand -hex 32`
- Get Supabase keys from Supabase dashboard
- Create Redis instance on Upstash
- Get OpenAI API key from OpenAI dashboard
- Update ALLOWED_ORIGINS with your frontend domain

### 3. Deploy

```bash
# Using DigitalOcean CLI
doctl apps create --spec app-spec.json

# Or via DigitalOcean Control Panel
# Apps → Create App → Import from spec
```

### 4. Configure DNS

Point your custom domain to the app URL:
- CNAME record: `[subdomain]` → `[app-name]-[id].ondigitalocean.app`

---

## Monitoring

### Health Check Endpoint
```bash
curl https://taskifai-demo-ak4kq.ondigitalocean.app/health
```

Expected response:
```json
{"status": "healthy", "version": "2.0.0"}
```

### View Logs
```bash
# API logs
doctl apps logs ef090864-9e06-4a9a-96fb-276a047cf479 --component demo-api

# Worker logs
doctl apps logs ef090864-9e06-4a9a-96fb-276a047cf479 --component demo-worker
```

---

## Security Notes

1. **Encrypted Secrets:** All sensitive values are encrypted by DigitalOcean (marked as `<encrypted>`)
2. **CORS:** Restricted to `https://demo.taskifai.com`
3. **JWT Expiry:** 24 hours (1440 minutes)
4. **RLS:** Supabase Row-Level Security policies enforce data isolation (bypassed by service_key)
5. **Service Key Usage:** Backend uses Supabase service_key which bypasses RLS - manual user_id filtering required

---

## Troubleshooting

### Build Failures
- Check Python dependencies in `requirements.txt`
- Verify bcrypt is pinned to 3.x range
- Review build logs in DigitalOcean dashboard

### Password Verification Errors
- Ensure bcrypt version is `>=3.2.0,<4.0.0`
- passlib must be `>=1.7.4` (1.7.5 doesn't exist)

### Worker Not Processing Tasks
- Verify Redis URL is correct
- Check worker logs for connection errors
- Ensure celery concurrency matches workload

### CORS Issues
- Verify ALLOWED_ORIGINS matches frontend domain
- Check frontend is sending correct Origin header
- Ensure no trailing slashes in domain URLs
