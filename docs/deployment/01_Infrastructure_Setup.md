# TaskifAI Platform - App Platform Infrastructure Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [App Platform Components](#app-platform-components)
3. [Environment Configuration](#environment-configuration)
4. [DNS & Domain Setup](#dns--domain-setup)
5. [Database Configuration](#database-configuration)
6. [Monitoring & Scaling](#monitoring--scaling)

---

## Architecture Overview

### Multi-Tenant App Platform Architecture

TaskifAI uses **DigitalOcean App Platform** with a centralized login + isolated tenant model:

```
┌─────────────────────────────────────────────────────────────┐
│                  app.taskifai.com                           │
│         (Central Login App)                                 │
│  Components:                                                │
│   - Static Site (Frontend) - FREE                           │
│   - Web Service (API) - $5/mo                               │
│  Features:                                                  │
│   - Tenant discovery                                        │
│   - Authentication routing                                  │
│   - Rate limiting                                           │
└─────────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ demo.        │ │ bibbi.       │ │ customer3.   │
│ taskifai.com │ │ taskifai.com │ │ taskifai.com │
│              │ │              │ │              │
│ App Platform │ │ App Platform │ │ App Platform │
│ Instance     │ │ Instance     │ │ Instance     │
│              │ │              │ │              │
│ - Frontend   │ │ - Frontend   │ │ - Frontend   │
│   (Free)     │ │   (Free)     │ │   (Free)     │
│ - API        │ │ - API        │ │ - API        │
│   ($12/mo)   │ │   ($12/mo)   │ │   ($12/mo)   │
│ - Worker     │ │ - Worker     │ │ - Worker     │
│   ($5/mo)    │ │   ($5/mo)    │ │   ($5/mo)    │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Supabase     │ │ Supabase     │ │ Supabase     │
│ Project #1   │ │ Project #2   │ │ Project #3   │
│ (demo data)  │ │ (bibbi data) │ │ (cust3 data) │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Key Infrastructure Benefits

✅ **No Server Management** - App Platform handles all infrastructure
✅ **Auto-Scaling** - Automatically handles traffic spikes
✅ **Zero-Downtime Deploys** - Rolling updates with health checks
✅ **Built-in SSL/TLS** - Automatic HTTPS with Let's Encrypt
✅ **Git Integration** - Deploy on push to GitHub
✅ **Monitoring Included** - Metrics, logs, alerts built-in
✅ **DDoS Protection** - Edge protection included
✅ **Load Balancing** - Automatic for multi-instance apps

---

## App Platform Components

### 1. Central Login App (`taskifai-central`)

**Purpose:** Tenant discovery and routing

#### Components

**A. Static Site (Frontend)**
```yaml
name: central-frontend
type: static_site
source_dir: frontend
build_command: npm install && npm run build
output_dir: dist
env:
  - VITE_API_URL: https://app.taskifai.com/api
routes:
  - path: /
```

**Specs:**
- Build time: 2-3 minutes
- Deploy time: 1 minute
- Cost: **FREE** (3 static sites included)

**B. Web Service (API)**
```yaml
name: central-api
type: web
dockerfile_path: backend/Dockerfile
http_port: 8000
instance_size: basic-xxs (512MB RAM)
instance_count: 1
health_check:
  path: /api/health
env:
  - SECRET_KEY: [generated]
  - SUPABASE_URL: [registry project]
  - SUPABASE_ANON_KEY: [registry anon key]
  - SUPABASE_SERVICE_KEY: [registry service key]
  - REDIS_URL: [upstash redis]
  - RATE_LIMIT_ENABLED: true
```

**Specs:**
- Memory: 512MB RAM
- vCPUs: 1
- Cost: **$5/month**
- Auto-restart on crash
- Health check every 30s

**Total Central Login Cost:** $5/month

---

### 2. Tenant App (`taskifai-demo`, `taskifai-bibbi`, etc.)

**Purpose:** Full application functionality per customer

#### Components

**A. Static Site (Frontend)**
```yaml
name: demo-frontend
type: static_site
source_dir: frontend
build_command: npm install && npm run build
output_dir: dist
env:
  - VITE_API_URL: https://demo.taskifai.com/api
routes:
  - path: /
```

**Specs:**
- Build time: 2-3 minutes
- Cost: **FREE**

**B. Web Service (API)**
```yaml
name: demo-api
type: web
dockerfile_path: backend/Dockerfile
http_port: 8000
instance_size: professional-xs (1GB RAM)
instance_count: 1
health_check:
  path: /api/health
  timeout: 5s
  initial_delay: 10s
env:
  - APP_NAME: TaskifAI Analytics Platform - Demo
  - SECRET_KEY: [unique per tenant]
  - SUPABASE_URL: [tenant-specific]
  - SUPABASE_ANON_KEY: [tenant-specific]
  - SUPABASE_SERVICE_KEY: [tenant-specific]
  - REDIS_URL: [shared upstash]
  - OPENAI_API_KEY: [shared]
  - SENDGRID_API_KEY: [shared]
  - MAX_UPLOAD_SIZE: 104857600
  - ALLOWED_ORIGINS: https://demo.taskifai.com
```

**Specs:**
- Memory: 1GB RAM
- vCPUs: 1
- Cost: **$12/month**
- Handles 100-500 req/min

**C. Worker Service (Celery)**
```yaml
name: demo-worker
type: worker
dockerfile_path: backend/Dockerfile
instance_size: basic-xxs (512MB RAM)
instance_count: 1
run_command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
env:
  [same as demo-api]
```

**Specs:**
- Memory: 512MB RAM
- vCPUs: 1
- Cost: **$5/month**
- Processes background tasks
- Auto-restart on failure

**Total Per Tenant Cost:** $17/month (API + Worker)

---

## Environment Configuration

### Central Login Environment Variables

**Required:**
```env
# Security
SECRET_KEY=generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Tenant Registry Database
SUPABASE_URL=https://your-registry-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...

# Redis (shared)
REDIS_URL=redis://default:password@hostname.upstash.io:6379

# CORS - Allow all tenant subdomains
ALLOWED_ORIGINS=https://demo.taskifai.com,https://bibbi.taskifai.com,https://*.taskifai.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

**Optional:**
```env
DEBUG=false
LOG_LEVEL=info
```

---

### Tenant Environment Variables

**Required:**
```env
# App Identity
APP_NAME=TaskifAI Analytics Platform - Demo
DEBUG=false

# Security (unique per tenant)
SECRET_KEY=tenant-specific-secret-key-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Tenant Database (isolated per tenant)
SUPABASE_URL=https://demo-project.supabase.co
SUPABASE_ANON_KEY=demo-anon-key
SUPABASE_SERVICE_KEY=demo-service-key

# Redis (shared across tenants)
REDIS_URL=redis://default:password@hostname.upstash.io:6379

# AI Chat
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Email (shared)
SENDGRID_API_KEY=SG.your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@taskifai.com
SENDGRID_FROM_NAME=TaskifAI Demo

# File Uploads
MAX_UPLOAD_SIZE=104857600
UPLOAD_DIR=/tmp/uploads

# CORS (tenant-specific)
ALLOWED_ORIGINS=https://demo.taskifai.com
```

**Celery Worker (same as API):**
- Worker uses same environment variables as API
- Shares Redis connection for task queue

---

## DNS & Domain Setup

### DNS Records Required

#### Option 1: Wildcard CNAME (Recommended)

```dns
# Root domain
@                A       <your-server-if-needed>

# Central login
app              CNAME   app-xxxxx.ondigitalocean.app.

# Wildcard for all tenants
*.taskifai.com   CNAME   app-xxxxx.ondigitalocean.app.
```

**Pros:**
- One DNS entry for all future tenants
- No DNS updates when adding tenants
- Simpler management

**Cons:**
- Not all DNS providers support wildcard CNAME

#### Option 2: Individual CNAMEs

```dns
# Central login
app              CNAME   app-central-xxxxx.ondigitalocean.app.

# Each tenant
demo             CNAME   app-demo-xxxxx.ondigitalocean.app.
bibbi            CNAME   app-bibbi-xxxxx.ondigitalocean.app.
customer3        CNAME   app-customer3-xxxxx.ondigitalocean.app.
```

**Pros:**
- Works with all DNS providers
- More granular control

**Cons:**
- Need to add DNS entry for each new tenant

---

### SSL/TLS Configuration

**Automatic SSL:**
- App Platform automatically provisions Let's Encrypt certificates
- Certificates auto-renew before expiration
- HTTPS enforced by default
- HTTP → HTTPS redirect automatic

**Custom Domain Setup:**

1. Deploy app via MCP
2. Get App Platform URL (e.g., `app-demo-xxxxx.ondigitalocean.app`)
3. Add CNAME in DNS provider
4. Wait 5-30 minutes for DNS propagation
5. App Platform automatically detects domain
6. SSL certificate provisioned automatically (2-5 minutes)

**Verification:**
```bash
# Check DNS propagation
dig demo.taskifai.com

# Check HTTPS
curl -I https://demo.taskifai.com

# Expected:
HTTP/2 200
strict-transport-security: max-age=31536000
```

---

## Database Configuration

### Supabase Projects Required

**1. Tenant Registry (Central Login)**

Purpose: Store tenant metadata and user-tenant mappings

```sql
-- Create tables
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subdomain VARCHAR(63) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    database_url TEXT NOT NULL,
    database_anon_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_tenants (
    user_tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_user_tenants_email ON user_tenants(email);
CREATE INDEX idx_user_tenants_tenant ON user_tenants(tenant_id);
```

**2. Tenant Databases (Per Customer)**

Each tenant gets isolated Supabase project:

- **Demo Tenant:** `TaskifAI-Demo` project
- **BIBBI Tenant:** `TaskifAI-BIBBI` project
- **Customer3 Tenant:** `TaskifAI-Customer3` project

**Schema:** Use `backend/db/schema.sql` for each tenant project

**RLS Policies:** Automatically applied from schema.sql

**Backup:**
- Free tier: Daily automatic backups (7 days retention)
- Pro tier: Point-in-time recovery

---

### Redis Configuration (Upstash)

**Setup:**

1. Create account: https://upstash.com
2. Create Redis database: `taskifai-redis`
3. Region: **Global** (multi-region)
4. Copy connection string

**Free Tier Limits:**
- 10,000 commands/day
- 256MB storage
- Multi-region replication

**Shared Usage:**
- All tenants share one Redis instance
- Separate key namespaces per tenant
- Pattern: `tenant:{subdomain}:*`

**Upgrade When:**
- >10K commands/day: $10/month for unlimited
- Need more storage: $10/month for 1GB

---

## Monitoring & Scaling

### Built-in Monitoring

**App Platform Dashboard:**

Access: DigitalOcean Dashboard → Apps → [app-name]

**Metrics Available:**
- CPU usage (%)
- Memory usage (MB)
- Request rate (req/min)
- Response time (ms)
- Error rate (%)
- Bandwidth usage (GB)

**Logs:**
- Real-time build logs
- Application logs (stdout/stderr)
- Deployment logs
- Error tracking

**Alerts:**
- CPU >80% for 5 minutes
- Memory >90% for 5 minutes
- Health check failures
- Deployment failures

---

### Scaling Strategies

#### Vertical Scaling (Increase Resources)

**When to scale up:**
- CPU consistently >70%
- Memory consistently >80%
- Response time degradation

**Instance Sizes:**
```
basic-xxs:  512MB RAM, 1 vCPU  → $5/mo
basic-xs:   1GB RAM,   1 vCPU  → $12/mo
professional-xs: 1GB RAM, 1 vCPU → $12/mo
professional-s:  2GB RAM, 2 vCPU → $24/mo
professional-m:  4GB RAM, 2 vCPU → $48/mo
```

**Scale via MCP:**
```
"Update taskifai-demo demo-api to professional-s instance"
```

#### Horizontal Scaling (Add Instances)

**When to scale out:**
- Traffic spikes expected
- Need high availability
- CPU/RAM at limits with one instance

**Scale via MCP:**
```
"Scale taskifai-demo demo-api to 2 instances"
```

**Cost Impact:**
- 2 instances = 2× cost
- Load balancer included (no extra cost)
- Auto-distribution of traffic

**Benefits:**
- Zero-downtime deployments
- Rolling updates
- Fault tolerance

---

### Cost Optimization

#### Strategy 1: Right-Size Instances

Monitor resource usage and downsize if underutilized:

```
"Show resource usage for taskifai-demo"
```

If CPU <30% and Memory <50% consistently:
```
"Update taskifai-demo demo-api to basic-xs instance"
```

**Savings:** $12/mo → $5/mo (save $7/mo)

#### Strategy 2: Combine Worker with API (Low Traffic)

For tenants with <100 uploads/day:

```
"Delete taskifai-demo demo-worker component"
"Update taskifai-demo demo-api run command to:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 &
  celery -A app.workers.celery_app worker --loglevel=info --concurrency=2"
```

**Savings:** $5/mo (eliminate dedicated worker)

**Trade-off:** Shared resources may impact performance

#### Strategy 3: Use Spaces for File Storage

**Current:** Files in `/tmp` (lost on restart)

**Better:** DigitalOcean Spaces (S3-compatible)

**Cost:** $5/mo for 250GB + bandwidth

**Benefits:**
- Persistent storage
- Better performance
- CDN integration
- Automatic backups

---

### Health Monitoring

#### Application Health Checks

**Configured in App Spec:**
```yaml
health_check:
  path: /api/health
  timeout: 5s
  initial_delay: 10s
  period: 30s
  success_threshold: 1
  failure_threshold: 3
```

**How it works:**
1. App Platform hits `/api/health` every 30s
2. Expects HTTP 200 response
3. After 3 failures → restart instance
4. After 5 failures → alert + rollback

**Health Endpoint Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-01-09T12:00:00Z"
}
```

#### External Monitoring (Optional)

**Uptime Robot (Free):**
- Monitor: https://demo.taskifai.com/api/health
- Interval: 5 minutes
- Alert: Email/SMS on downtime

**Better Uptime ($10/mo):**
- Multi-region monitoring
- SSL certificate expiry alerts
- API endpoint monitoring
- Slack/PagerDuty integration

---

## Deployment Workflow

### Git-Based Deployment

**Automatic Deploy on Push:**

1. Push code to GitHub: `git push origin main`
2. App Platform detects change
3. Automatic build triggered
4. Tests run (if configured)
5. Deploy with zero downtime
6. Health checks validate
7. Old version kept for rollback

**Manual Deploy via MCP:**
```
"Deploy latest code from main branch to taskifai-demo"
```

**Rollback if needed:**
```
"Rollback taskifai-demo to previous deployment"
```

---

## Security Features

### Built-in Security

✅ **DDoS Protection** - Edge network filtering
✅ **Auto SSL/TLS** - Let's Encrypt certificates
✅ **HTTPS Enforcement** - HTTP → HTTPS redirect
✅ **Security Headers** - HSTS, X-Frame-Options auto-added
✅ **Private Networking** - Components can communicate privately
✅ **Secrets Management** - Environment variables encrypted

### Best Practices

**Environment Variables:**
- Never commit secrets to Git
- Use App Platform environment variable encryption
- Rotate API keys quarterly

**Access Control:**
- Limit DigitalOcean API token scope
- Use separate tokens for different environments
- Audit token usage regularly

**Network Security:**
- CORS properly configured per tenant
- Rate limiting on auth endpoints
- Supabase RLS policies active

---

## Summary

### Infrastructure Stack

| Layer | Technology | Management |
|-------|------------|------------|
| **Compute** | App Platform Containers | DigitalOcean Managed |
| **Frontend** | Static Sites (React) | App Platform CDN |
| **Database** | Supabase (PostgreSQL) | Supabase Managed |
| **Cache/Queue** | Redis (Upstash) | Upstash Managed |
| **Storage** | Container /tmp or Spaces | Optional upgrade |
| **Monitoring** | App Platform Dashboard | Built-in |
| **SSL/TLS** | Let's Encrypt | Auto-managed |
| **DNS** | Domain Registrar | Self-managed |

### Key Advantages

✅ **Zero Server Management** - No SSH, no updates, no patches
✅ **Auto-Scaling** - Handle traffic automatically
✅ **Fast Deployment** - 5-10 minute deploys
✅ **Built-in Monitoring** - Logs, metrics, alerts included
✅ **High Availability** - Multi-instance with load balancing
✅ **Cost Effective** - $40/month for 3 tenants

### Next Steps

1. Review [MCP Deployment Guide](05_DigitalOcean_MCP_Deployment.md)
2. Setup prerequisites (accounts, keys, projects)
3. Deploy central login
4. Deploy demo tenant
5. Test complete flow
6. Deploy additional tenants as needed

---

**Ready to deploy?** → Proceed to `05_DigitalOcean_MCP_Deployment.md`
