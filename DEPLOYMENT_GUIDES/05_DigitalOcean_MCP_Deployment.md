# DigitalOcean App Platform Deployment via MCP

## Table of Contents
1. [What is MCP](#what-is-mcp)
2. [Prerequisites](#prerequisites)
3. [MCP Setup with Claude](#mcp-setup-with-claude)
4. [Deploying Central Login](#deploying-central-login)
5. [Deploying Tenant Applications](#deploying-tenant-applications)
6. [Managing Deployments](#managing-deployments)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Cost Optimization](#cost-optimization)

---

## What is MCP?

**MCP (Model Context Protocol)** enables you to deploy and manage DigitalOcean App Platform using **natural language commands** through Claude.

### Traditional Deployment vs MCP

**Traditional (Manual):**
```bash
# 1. Create app spec YAML file
# 2. Use doctl CLI or web UI
# 3. Configure services manually
# 4. Set environment variables
# 5. Deploy and monitor

Total time: 30-60 minutes per app
```

**With MCP (Automated):**
```
You: "Deploy demo tenant from my GitHub repo with 1GB container"
Claude: ✅ Creates app spec
        ✅ Deploys from repository
        ✅ Configures environment
        ✅ Sets up SSL
        ✅ Reports status

Total time: 2-5 minutes
```

---

## Prerequisites

### 1. DigitalOcean Account
- Sign up at https://www.digitalocean.com
- Verify email and payment method

### 2. DigitalOcean API Token

**Create Personal Access Token:**

1. Log in to DigitalOcean
2. Navigate to: **API** → **Tokens/Keys**
3. Click **Generate New Token**
4. Name: `TaskifAI-MCP`
5. Scopes: **Read** and **Write**
6. Click **Generate Token**
7. **IMPORTANT:** Copy token immediately (shown only once)

Save token somewhere safe:
```
dop_v1_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. GitHub Repository

Your TaskifAI code should be pushed to GitHub:
```bash
# If not already done
git remote add origin https://github.com/yourusername/taskifai-platform.git
git push -u origin main
```

### 4. Claude Desktop with MCP

**Install Claude Desktop:**
- Download from: https://claude.ai/download
- Install for your OS (macOS, Windows, Linux)

**Configure MCP Server:**

Edit Claude configuration file:

**macOS/Linux:**
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
notepad %APPDATA%\Claude\claude_desktop_config.json
```

**Add DigitalOcean MCP:**
```json
{
  "mcpServers": {
    "digitalocean": {
      "command": "npx",
      "args": [
        "-y",
        "@digitalocean/mcp-server-digitalocean"
      ],
      "env": {
        "DIGITALOCEAN_API_TOKEN": "dop_v1_your_actual_token_here"
      }
    }
  }
}
```

**Restart Claude Desktop**

### 5. Supabase Projects

Create 3 Supabase projects:

1. **Tenant Registry** (for central login)
   - Name: `TaskifAI-Registry`
   - Save: URL, anon key, service key

2. **Demo Tenant**
   - Name: `TaskifAI-Demo`
   - Save: URL, anon key, service key

3. **BIBBI Tenant** (when needed)
   - Name: `TaskifAI-BIBBI`
   - Save: URL, anon key, service key

### 6. Redis (Upstash Free)

1. Sign up at https://upstash.com
2. Create Redis database: `taskifai-redis`
3. Choose: **Global** region
4. Copy connection string: `redis://default:xxxxx@xxxxx.upstash.io:6379`

---

## MCP Setup with Claude

### Test MCP Connection

Open Claude Desktop and ask:

```
"List my DigitalOcean apps"
```

**Expected Response:**
```
I can see you have X apps currently deployed:
- [List of apps or empty if none]

MCP Connection: ✅ Working
```

**If error:**
- Check API token is correct
- Restart Claude Desktop
- Verify `claude_desktop_config.json` syntax

---

## Deploying Central Login

### Step 1: Prepare Environment Variables

Create a file: `env-central-login.txt`

```env
# Security
SECRET_KEY=your-secret-key-min-32-chars-generate-with-openssl
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Tenant Registry (Supabase)
SUPABASE_URL=https://your-registry-project.supabase.co
SUPABASE_ANON_KEY=your-registry-anon-key
SUPABASE_SERVICE_KEY=your-registry-service-key

# Redis
REDIS_URL=redis://default:xxxxx@xxxxx.upstash.io:6379

# CORS (allow all tenant subdomains)
ALLOWED_ORIGINS=https://demo.taskifai.com,https://bibbi.taskifai.com,https://*.taskifai.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

### Step 2: Deploy via MCP

**In Claude Desktop, use this prompt:**

```
Create a new DigitalOcean app for TaskifAI Central Login with the following configuration:

Name: taskifai-central
Region: nyc (or your preferred region)
Repository: https://github.com/yourusername/taskifai-platform
Branch: main

Components:
1. Static Site for frontend:
   - Name: central-frontend
   - Build command: cd frontend && npm install && npm run build
   - Output directory: frontend/dist
   - Environment variables:
     VITE_API_URL=https://app.taskifai.com/api

2. API Service (Basic container, 512MB):
   - Name: central-api
   - Dockerfile path: backend/Dockerfile
   - HTTP port: 8000
   - Health check path: /api/health
   - Environment variables: [paste content from env-central-login.txt]

Domain: app.taskifai.com

Deploy now.
```

**MCP will:**
1. Create app specification
2. Deploy from GitHub
3. Build frontend and backend
4. Configure SSL for app.taskifai.com
5. Report deployment status

**Wait 5-10 minutes for deployment**

### Step 3: Configure DNS

While deployment runs, configure DNS:

1. Go to your domain registrar (Namecheap, Cloudflare, etc.)
2. Add CNAME record:
   ```
   Type: CNAME
   Name: app
   Value: [provided by DigitalOcean, e.g., app.ondigitalocean.app]
   TTL: 300 (5 minutes)
   ```

3. Wait for DNS propagation (5-30 minutes)

### Step 4: Register Tenant in Registry

Once deployed, add demo tenant to registry:

**Execute in Supabase SQL Editor (Registry project):**

```sql
-- Insert demo tenant
INSERT INTO tenants (subdomain, display_name, database_url, database_anon_key, is_active)
VALUES (
    'demo',
    'Demo Account',
    'https://your-demo-project.supabase.co',
    'demo-anon-key-here',
    true
);
```

### Step 5: Test Central Login

```
Visit: https://app.taskifai.com

Expected:
- Login page loads
- No errors in console
- API health check: https://app.taskifai.com/api/health returns {"status": "healthy"}
```

---

## Deploying Tenant Applications

### Deploy Demo Tenant

**Prepare environment file:** `env-demo-tenant.txt`

```env
# App Info
APP_NAME=TaskifAI Analytics Platform - Demo
DEBUG=false

# Security
SECRET_KEY=your-secret-key-different-from-central
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Supabase (Demo tenant database)
SUPABASE_URL=https://demo-project.supabase.co
SUPABASE_ANON_KEY=demo-anon-key
SUPABASE_SERVICE_KEY=demo-service-key

# Redis
REDIS_URL=redis://default:xxxxx@xxxxx.upstash.io:6379

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# SendGrid
SENDGRID_API_KEY=SG.your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@taskifai.com
SENDGRID_FROM_NAME=TaskifAI Demo

# File Upload
MAX_UPLOAD_SIZE=104857600
UPLOAD_DIR=/tmp/uploads

# CORS
ALLOWED_ORIGINS=https://demo.taskifai.com
```

**Deploy via MCP:**

```
Create a new DigitalOcean app for TaskifAI Demo Tenant:

Name: taskifai-demo
Region: nyc
Repository: https://github.com/yourusername/taskifai-platform
Branch: main

Components:
1. Static Site for frontend:
   - Name: demo-frontend
   - Build command: cd frontend && npm install && npm run build
   - Output directory: frontend/dist
   - Environment:
     VITE_API_URL=https://demo.taskifai.com/api

2. API Service (Professional container, 1GB):
   - Name: demo-api
   - Dockerfile path: backend/Dockerfile
   - HTTP port: 8000
   - Health check path: /api/health
   - Instance count: 1
   - Instance size: professional-xs (1GB RAM, $12/mo)
   - Environment: [paste env-demo-tenant.txt]

3. Worker Service (Basic container, 512MB):
   - Name: demo-worker
   - Dockerfile path: backend/Dockerfile
   - Run command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
   - Instance count: 1
   - Instance size: basic-xxs (512MB RAM, $5/mo)
   - Environment: [same as demo-api]

Domain: demo.taskifai.com

Deploy now.
```

**Configure DNS for demo subdomain:**

```
Type: CNAME
Name: demo
Value: [DigitalOcean app URL]
TTL: 300
```

**Test Demo Tenant:**

1. Visit: https://demo.taskifai.com
2. Register user via API or frontend
3. Test file upload
4. Verify analytics dashboard

---

### Deploy BIBBI Tenant

**Same process as demo, but change:**

```
Name: taskifai-bibbi
Domain: bibbi.taskifai.com
Environment: Use BIBBI Supabase credentials
DNS: CNAME bibbi → [app URL]
```

**MCP Command:**

```
Create DigitalOcean app for BIBBI tenant, identical to demo tenant configuration but:
- Name: taskifai-bibbi
- Domain: bibbi.taskifai.com
- Use BIBBI Supabase credentials
- [paste env-bibbi-tenant.txt]

Deploy now.
```

---

## Managing Deployments

### Common MCP Commands

#### View All Apps
```
"List all my DigitalOcean apps"
```

#### Get App Details
```
"Show details for taskifai-demo app"
```

#### View Deployment Logs
```
"Show deployment logs for taskifai-demo"
```

#### View Application Logs
```
"Show active logs for taskifai-demo demo-api component"
```

#### Update App
```
"Deploy latest code from main branch to taskifai-demo"
```

#### Restart App
```
"Restart taskifai-demo app"
```

#### Scale App
```
"Scale taskifai-demo demo-api component to 2 instances"
```

#### Rollback Deployment
```
"Validate rollback for taskifai-demo to previous deployment"
"Rollback taskifai-demo to previous version"
```

#### Check Metrics
```
"Show bandwidth metrics for taskifai-demo"
```

#### Delete App
```
"Delete taskifai-demo app"
```

---

## Monitoring & Troubleshooting

### Health Checks

**Check app status:**
```
"Show app status for taskifai-demo"
```

**Check all deployments:**
```
"List all deployments for taskifai-demo"
```

**Check specific deployment:**
```
"Show deployment [deployment-id] for taskifai-demo"
```

### Common Issues

#### Issue 1: Deployment Fails

**Diagnosis:**
```
"Show deployment logs for taskifai-demo"
```

**Common causes:**
- Build errors (check Dockerfile)
- Missing environment variables
- Port conflicts
- Out of memory

**Solution:**
```
"Show build logs for latest deployment of taskifai-demo"
```

Review errors, fix code/config, then:
```
"Redeploy taskifai-demo from main branch"
```

#### Issue 2: App Not Accessible

**Check:**
1. DNS propagation: `dig demo.taskifai.com`
2. SSL certificate: Visit https://demo.taskifai.com
3. App status: Ask MCP "Show taskifai-demo status"

**Fix DNS:**
- Update CNAME record
- Wait 5-30 minutes for propagation

#### Issue 3: Worker Not Processing Files

**Check worker logs:**
```
"Show logs for taskifai-demo demo-worker component"
```

**Common issues:**
- Redis connection failed (check REDIS_URL)
- Celery not starting (check run command)
- Out of memory (upgrade to 1GB container)

**Restart worker:**
```
"Restart taskifai-demo demo-worker component"
```

#### Issue 4: High Costs

**Check metrics:**
```
"Show bandwidth metrics for all apps"
```

**Optimize:**
- Reduce instance sizes (2GB → 1GB)
- Reduce instance counts
- Add CDN for static files
- Compress images/files

---

## Cost Optimization

### Current Setup Cost Breakdown

**3 Tenants (Central + Demo + BIBBI):**

```
Central Login:
  - Static site (3 free): $0
  - API (512MB): $5/mo

Demo Tenant:
  - Frontend (static, free): $0
  - API (1GB): $12/mo
  - Worker (512MB): $5/mo

BIBBI Tenant:
  - Frontend (static, free): $0
  - API (1GB): $12/mo
  - Worker (512MB): $5/mo

External Services:
  - Redis (Upstash free): $0
  - Supabase (3 × free): $0
  - Domain: $1/mo

TOTAL: $40/month
```

### Optimization Strategies

#### Strategy 1: Reduce Container Sizes (Save $10-14/mo)

**For low-traffic tenants:**

```
"Update taskifai-demo demo-api to use basic-xs instance (512MB)"
"Update taskifai-demo demo-worker to use basic-xxs instance (256MB)"
```

**New cost:**
- Demo API: $12 → $5 (save $7)
- Demo Worker: $5 → $3 (save $2)

**Total savings: $9/month per tenant**

#### Strategy 2: Share Workers (Save $5-10/mo)

**Combine workers if traffic is low:**

```
"Delete taskifai-demo demo-worker component"
"Update taskifai-demo demo-api run command to include:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 &
  celery -A app.workers.celery_app worker --loglevel=info --concurrency=2"
```

**Savings: $5/month per tenant**

⚠️ **Trade-off:** API and worker compete for resources

#### Strategy 3: Use Spaces for Uploads (Better Performance)

**Current:** Files stored in container (lost on restart)

**Better:** Use DigitalOcean Spaces (S3-compatible)

**Cost:** $5/month for 250GB storage + transfer

**Benefits:**
- Persistent file storage
- Faster file access
- Scales automatically
- Backup included

**Setup:**
```
1. Create Space: "Create DigitalOcean Space named taskifai-uploads in nyc3"
2. Update code to use Spaces SDK
3. Redeploy apps
```

#### Strategy 4: Monitor and Auto-Scale

**Check resource usage:**
```
"Show resource usage for taskifai-demo"
```

**If CPU/RAM consistently low (<50%):**
- Downgrade instance sizes

**If CPU/RAM consistently high (>80%):**
- Upgrade instance sizes
- Or add more instances

---

## Upgrading Components

### Upgrade Instance Size

```
"Update taskifai-demo demo-api to professional-s instance (2GB RAM)"
```

**Cost change:** $12/mo → $24/mo

### Add More Instances (Horizontal Scaling)

```
"Scale taskifai-demo demo-api to 2 instances"
```

**Cost change:** $12/mo → $24/mo (doubles cost)

**Benefits:**
- Zero-downtime deployments
- Higher availability
- Auto load balancing

### Upgrade Supabase (When >500MB)

**When demo data grows >450MB:**

1. Upgrade in Supabase dashboard
2. Plan: Free → Pro ($25/month)
3. Features: 8GB storage, better performance

**No app changes needed** (same connection string)

### Upgrade Redis (Unlimited)

**When >10K commands/day:**

1. Upgrade Upstash plan: Free → Pay-as-you-go ($10/mo)
2. Update REDIS_URL if needed
3. Redeploy apps:
```
"Redeploy taskifai-demo with updated environment"
```

---

## Adding New Tenants

### Quick Tenant Deployment

**Template MCP Command:**

```
Create DigitalOcean app for [CUSTOMER_NAME] tenant:

Name: taskifai-[customer]
Region: nyc
Repository: https://github.com/yourusername/taskifai-platform
Branch: main

Components:
1. Static frontend (free)
2. API (Professional 1GB, $12/mo)
3. Worker (Basic 512MB, $5/mo)

Domain: [customer].taskifai.com
Environment: [paste env file]

Deploy now.
```

**Estimated time:** 5 minutes + DNS propagation

**Cost:** +$17/month per tenant

---

## CI/CD Integration (Optional)

### Auto-Deploy on Git Push

**DigitalOcean App Platform automatically deploys when you push to GitHub!**

**How it works:**
1. You push code: `git push origin main`
2. App Platform detects change
3. Automatically builds and deploys
4. Zero-downtime rolling update

**Configure auto-deploy:**
```
"Enable auto-deploy for taskifai-demo from main branch"
```

**Disable auto-deploy:**
```
"Disable auto-deploy for taskifai-demo"
```

**Manual deploy only:**
```
"Deploy taskifai-demo from latest commit on main"
```

---

## Security Best Practices

### Environment Variables

**Never commit secrets to Git!**

✅ **Correct:** Store in App Platform environment variables
❌ **Wrong:** Hardcode in code or .env files in Git

**Update environment variable:**
```
"Update taskifai-demo environment variable SECRET_KEY to [new value]"
```

### API Tokens

**Rotate DigitalOcean token quarterly:**

1. Create new token in DO dashboard
2. Update `claude_desktop_config.json`
3. Restart Claude Desktop
4. Revoke old token

### HTTPS Only

**App Platform enforces HTTPS automatically**

- HTTP requests → redirect to HTTPS
- SSL certificates auto-renewed
- Grade A SSL by default

### Firewall

**App Platform includes DDoS protection and firewall**

- No additional configuration needed
- Rate limiting at edge
- Auto-blocking suspicious traffic

---

## Cost Monitoring

### Monthly Cost Check

```
"Show me all DigitalOcean apps and their costs"
```

### Bandwidth Monitoring

```
"Show bandwidth usage for all apps this month"
```

### Set Budget Alerts

**In DigitalOcean Dashboard:**
1. Billing → Alerts
2. Set threshold (e.g., $50/month)
3. Get email when exceeded

---

## Quick Reference

### Essential MCP Commands

```bash
# List all apps
"List my DigitalOcean apps"

# Deploy new app
"Create app [name] from [repo]"

# Update app
"Deploy latest code to [app-name]"

# View logs
"Show logs for [app-name]"

# Restart app
"Restart [app-name]"

# Scale app
"Scale [app-name] [component] to [N] instances"

# Rollback
"Rollback [app-name] to previous version"

# Delete app
"Delete [app-name] app"

# Check status
"Show status for [app-name]"

# View metrics
"Show bandwidth for [app-name]"
```

---

## Summary

You now have:

✅ **MCP configured** with Claude Desktop
✅ **Deployment process** for central login + tenants
✅ **Management commands** for monitoring and updates
✅ **Cost optimization** strategies
✅ **Troubleshooting** guides

**Total deployment time:** 30 minutes for complete setup

**Cost:** $40/month for 3 tenants (central + demo + BIBBI)

**Next steps:**
1. Deploy central login (10 minutes)
2. Deploy demo tenant (10 minutes)
3. Test complete user flow (10 minutes)
4. Deploy BIBBI when ready (10 minutes)

**Good luck with your deployment! 🚀**
