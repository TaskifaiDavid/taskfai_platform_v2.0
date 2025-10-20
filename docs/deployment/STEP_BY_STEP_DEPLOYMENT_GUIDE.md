# TaskifAI Platform - Complete Step-by-Step Deployment Guide

## 🎯 Overview

This guide walks you through deploying TaskifAI Platform from scratch to production using DigitalOcean App Platform + MCP in **approximately 60 minutes**.

**What You'll Deploy:**
- Central login portal (app.taskifai.com)
- Demo tenant application (demo.taskifai.com)
- All supporting infrastructure (databases, Redis, monitoring)

**Prerequisites Time:** ~25 minutes
**Deployment Time:** ~30 minutes
**DNS Propagation Wait:** 5-30 minutes

---

## 📋 Master Progress Checklist

**Track your overall deployment progress here. Check off each phase as you complete it.**

### Phase 1: Prerequisites (25 min)
- [ ] DigitalOcean account created and verified
- [ ] DigitalOcean API token generated and saved
- [ ] GitHub repository setup with code pushed
- [ ] Tenant Registry Supabase project created
- [ ] Tenant Registry database schema deployed
- [ ] Demo Tenant Supabase project created
- [ ] Demo Tenant database schema deployed
- [ ] Redis (Upstash) database created
- [ ] Claude Desktop installed
- [ ] MCP configured and tested

### Phase 2: Central Login (10 min)
- [ ] Central Login environment file created
- [ ] Central Login app deployed via Claude MCP
- [ ] DNS CNAME record added for app.taskifai.com
- [ ] Central Login health check passing

### Phase 3: Demo Tenant (15 min)
- [ ] Tenant registered in Registry database
- [ ] Demo Tenant environment file created
- [ ] Demo Tenant app deployed via Claude MCP
- [ ] DNS CNAME record added for demo.taskifai.com
- [ ] Admin user created in Demo Tenant
- [ ] User registered in Tenant Registry

### Phase 4: Testing (10 min)
- [ ] Tenant discovery API test passed
- [ ] Login API test passed
- [ ] File upload test passed
- [ ] Worker processing verified
- [ ] Database data verified
- [ ] Frontend login flow tested

### Phase 5: Production Ready
- [ ] Monitoring setup (Uptime Robot)
- [ ] Documentation reviewed
- [ ] Backup plan documented
- [ ] Ready to add more tenants

---

## Table of Contents

1. [Prerequisites Setup](#prerequisites-setup-25-minutes)
2. [Central Login Deployment](#central-login-deployment-10-minutes)
3. [Demo Tenant Deployment](#demo-tenant-deployment-15-minutes)
4. [Testing & Verification](#testing--verification-10-minutes)
5. [Next Steps](#next-steps)
6. [Credentials Tracking Template](#credentials-tracking-template)

---

## 📝 Credentials Tracking Template

**Use this template to track all credentials during deployment. Save as `deployment-credentials.txt` and store securely.**

```
=================================================================
TaskifAI Platform Deployment Credentials
Deployment Date: _______________
=================================================================

DIGITALOCEAN
-------------------
API Token: dop_v1_________________________________________
Central App URL: app-_________-_________.ondigitalocean.app
Demo App URL: app-_________-_________.ondigitalocean.app
BIBBI App URL: app-_________-_________.ondigitalocean.app

GITHUB
-------------------
Repository: https://github.com/___________/taskifai-platform
Branch: main

SUPABASE - TENANT REGISTRY
-------------------
Project Name: TaskifAI-Registry
URL: https://____________.supabase.co
Anon Key: eyJhbGc___________________________________________
Service Key: eyJhbGc___________________________________________
Database Password: ___________________________________________

SUPABASE - DEMO TENANT
-------------------
Project Name: TaskifAI-Demo
URL: https://____________.supabase.co
Anon Key: eyJhbGc___________________________________________
Service Key: eyJhbGc___________________________________________
Database Password: ___________________________________________
Tenant ID (from registry): ___________________________________________

SUPABASE - BIBBI TENANT
-------------------
Project Name: TaskifAI-BIBBI
URL: https://____________.supabase.co
Anon Key: eyJhbGc___________________________________________
Service Key: eyJhbGc___________________________________________
Database Password: ___________________________________________
Tenant ID (from registry): ___________________________________________

REDIS (UPSTASH)
-------------------
Database Name: taskifai-redis
Connection URL: redis://default:_____@_____.upstash.io:6379

SECRET KEYS
-------------------
Central Login SECRET_KEY: ___________________________________________
Demo Tenant SECRET_KEY: ___________________________________________
BIBBI Tenant SECRET_KEY: ___________________________________________

OPTIONAL SERVICES
-------------------
OpenAI API Key: sk-___________________________________________
SendGrid API Key: SG.___________________________________________
SendGrid From Email: noreply@taskifai.com

DNS CONFIGURATION
-------------------
Domain: taskifai.com
Registrar: ___________________________________________
Central Login CNAME: app → ___________________________________________
Demo Tenant CNAME: demo → ___________________________________________
BIBBI Tenant CNAME: bibbi → ___________________________________________

USER ACCOUNTS
-------------------
Demo Admin:
  Email: admin@demo.com
  Password: ___________________________________________
  User ID: ___________________________________________
  Access Token: ___________________________________________

BIBBI Admin:
  Email: admin@bibbi.com
  Password: ___________________________________________
  User ID: ___________________________________________
  Access Token: ___________________________________________

MONITORING
-------------------
UptimeRobot Account: ___________________________________________
Central Monitor URL: https://app.taskifai.com/api/health
Demo Monitor URL: https://demo.taskifai.com/api/health
BIBBI Monitor URL: https://bibbi.taskifai.com/api/health

DEPLOYMENT TIMELINE
-------------------
Prerequisites Started: ___________________________________________
Prerequisites Completed: ___________________________________________
Central Login Deployed: ___________________________________________
Demo Tenant Deployed: ___________________________________________
Testing Completed: ___________________________________________
Production Ready: ___________________________________________

NOTES
-------------------
___________________________________________________________________
___________________________________________________________________
___________________________________________________________________
```

---

## Prerequisites Setup (25 minutes)

### ✅ Prerequisites Detailed Checklist

#### Step 1: DigitalOcean Account
- [ ] Visit DigitalOcean website
- [ ] Complete registration
- [ ] Add payment method
- [ ] Verify email address
- [ ] Navigate to API settings
- [ ] Generate new API token named "TaskifAI-MCP"
- [ ] Enable both Read and Write scopes
- [ ] Copy and save token securely
- [ ] Verify token starts with `dop_v1_`

#### Step 2: GitHub Repository
- [ ] Code is ready in local directory
- [ ] Git repository initialized
- [ ] Remote repository created on GitHub
- [ ] Remote added to local repository
- [ ] Code committed with meaningful message
- [ ] Code pushed to main branch
- [ ] Verify code visible on GitHub

#### Step 3: Supabase - Registry Project
- [ ] Navigate to Supabase dashboard
- [ ] Create new project "TaskifAI-Registry"
- [ ] Choose appropriate region
- [ ] Generate and save database password
- [ ] Wait for project provisioning (2 min)
- [ ] Copy SUPABASE_URL
- [ ] Copy SUPABASE_ANON_KEY
- [ ] Copy SUPABASE_SERVICE_KEY
- [ ] Navigate to SQL Editor
- [ ] Paste tenants table schema
- [ ] Execute tenants table creation
- [ ] Paste user_tenants table schema
- [ ] Execute user_tenants table creation
- [ ] Verify both indexes created
- [ ] Confirm "Success. No rows returned"

#### Step 4: Supabase - Demo Tenant Project
- [ ] Create new project "TaskifAI-Demo"
- [ ] Use same region as Registry
- [ ] Generate and save database password
- [ ] Wait for project provisioning (2 min)
- [ ] Copy DEMO_SUPABASE_URL
- [ ] Copy DEMO_ANON_KEY
- [ ] Copy DEMO_SERVICE_KEY
- [ ] Open local file: `backend/db/schema.sql`
- [ ] Copy entire schema content
- [ ] Paste in SQL Editor
- [ ] Execute schema
- [ ] Wait 30 seconds for completion
- [ ] Open `backend/db/seed_vendor_configs.sql`
- [ ] Copy seed data
- [ ] Paste in new SQL query
- [ ] Execute seed data
- [ ] Verify vendor configs inserted

#### Step 5: Redis (Upstash)
- [ ] Visit Upstash website
- [ ] Sign up using GitHub/Google
- [ ] Click "Create Database"
- [ ] Name database "taskifai-redis"
- [ ] Select Redis type
- [ ] Choose Global region
- [ ] Create database
- [ ] Navigate to database details
- [ ] Locate REST API section
- [ ] Copy Redis URL
- [ ] Verify URL format: `redis://default:...@...upstash.io:6379`
- [ ] Save Redis URL securely

#### Step 6: Claude Desktop + MCP
- [ ] Download Claude Desktop from claude.ai/download
- [ ] Install Claude Desktop for your OS
- [ ] Launch Claude Desktop
- [ ] Close Claude Desktop
- [ ] Locate config directory for your OS
- [ ] Create `claude_desktop_config.json` file
- [ ] Paste MCP configuration JSON
- [ ] Replace `YOUR_DO_TOKEN_HERE` with actual token
- [ ] Save configuration file
- [ ] Reopen Claude Desktop
- [ ] Type "List my DigitalOcean apps"
- [ ] Verify response shows MCP working
- [ ] Confirm "0 apps deployed" message

---

### Step 1: DigitalOcean Account (5 minutes)

1. Visit https://www.digitalocean.com
2. Click "Sign Up"
3. Complete registration
4. Add payment method
5. Verify email

**Generate API Token:**

1. Click your profile → "API"
2. Click "Generate New Token"
3. Name: `TaskifAI-MCP`
4. Scopes: Check both "Read" and "Write"
5. Click "Generate Token"
6. **IMPORTANT:** Copy token immediately and save it:

```
YOUR_DO_TOKEN=dop_v1_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

✅ **Checkpoint:** Token saved securely

---

### Step 2: GitHub Repository (3 minutes)

**If not already done:**

```bash
# Clone your local code
cd ~/projects
git init taskifai-platform
cd taskifai-platform

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/taskifai-platform.git

# Push code
git add .
git commit -m "Initial commit"
git push -u origin main
```

✅ **Checkpoint:** Code pushed to GitHub

---

### Step 3: Supabase Projects (10 minutes)

**Create 3 projects:**

#### A. Tenant Registry Project

1. Visit https://supabase.com
2. Click "New Project"
3. Organization: Your organization
4. Name: `TaskifAI-Registry`
5. Database Password: Generate strong password
6. Region: Choose closest to you
7. Click "Create new project"
8. Wait 2 minutes for provisioning

**Copy credentials:**

```
REGISTRY_SUPABASE_URL=https://xxxxx.supabase.co
REGISTRY_ANON_KEY=eyJhbGc...
REGISTRY_SERVICE_KEY=eyJhbGc...
```

**Setup schema:**

1. Click "SQL Editor" in left sidebar
2. Click "New query"
3. Copy and paste:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

4. Click "Run" (or press Cmd/Ctrl + Enter)
5. Verify: "Success. No rows returned"

✅ **Checkpoint:** Registry database created

#### B. Demo Tenant Project

1. Click "New Project" again
2. Name: `TaskifAI-Demo`
3. Database Password: Generate strong password
4. Region: Same as registry
5. Click "Create new project"
6. Wait 2 minutes

**Copy credentials:**

```
DEMO_SUPABASE_URL=https://yyyyy.supabase.co
DEMO_ANON_KEY=eyJhbGc...
DEMO_SERVICE_KEY=eyJhbGc...
```

**Setup schema:**

1. In your local project: `backend/db/schema.sql`
2. Copy entire file content
3. Supabase → SQL Editor → New query
4. Paste schema
5. Click "Run"
6. Wait 30 seconds
7. Copy `backend/db/seed_vendor_configs.sql`
8. SQL Editor → New query
9. Paste
10. Click "Run"

✅ **Checkpoint:** Demo database created

---

### Step 4: Redis (Upstash) (3 minutes)

1. Visit https://upstash.com
2. Click "Sign Up" (use GitHub/Google)
3. Click "Create Database"
4. Name: `taskifai-redis`
5. Type: **Redis**
6. Region: **Global** (important!)
7. Click "Create"

**Copy connection string:**

1. Click your database
2. Scroll to "REST API" section
3. Copy "Redis URL":

```
REDIS_URL=redis://default:xxxxx@xxxxx.upstash.io:6379
```

✅ **Checkpoint:** Redis created

---

### Step 5: Claude Desktop + MCP (4 minutes)

1. Download Claude Desktop: https://claude.ai/download
2. Install for your OS
3. Launch Claude Desktop

**Configure MCP:**

**On macOS/Linux:**
```bash
mkdir -p ~/Library/Application\ Support/Claude
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**On Windows:**
```powershell
mkdir "$env:APPDATA\Claude"
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

**Paste this configuration:**

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
        "DIGITALOCEAN_API_TOKEN": "YOUR_DO_TOKEN_HERE"
      }
    }
  }
}
```

**Replace** `YOUR_DO_TOKEN_HERE` with your actual token from Step 1.

**Save and close Claude Desktop, then reopen.**

**Test MCP:**

Open Claude Desktop and type:

```
List my DigitalOcean apps
```

**Expected response:**
```
You currently have 0 apps deployed.
MCP Connection: ✅ Working
```

✅ **Checkpoint:** MCP configured and working

---

## Central Login Deployment (10 minutes)

### ✅ Central Login Detailed Checklist

#### Step 1: Environment File Preparation
- [ ] Create file `env-central-login.txt` on desktop
- [ ] Run `openssl rand -hex 32` command
- [ ] Copy generated SECRET_KEY
- [ ] Paste SECRET_KEY into environment file
- [ ] Add ALGORITHM=HS256
- [ ] Add ACCESS_TOKEN_EXPIRE_MINUTES=1440
- [ ] Paste REGISTRY_SUPABASE_URL
- [ ] Paste REGISTRY_ANON_KEY
- [ ] Paste REGISTRY_SERVICE_KEY
- [ ] Paste REDIS_URL
- [ ] Set ALLOWED_ORIGINS with demo subdomain
- [ ] Set RATE_LIMIT_ENABLED=true
- [ ] Set DEBUG=false
- [ ] Save environment file
- [ ] Verify all values filled in

#### Step 2: Deploy via Claude MCP
- [ ] Open Claude Desktop
- [ ] Prepare deployment command
- [ ] Replace YOUR_USERNAME with actual GitHub username
- [ ] Copy environment variables from env-central-login.txt
- [ ] Paste complete deployment command
- [ ] Send command to Claude
- [ ] Monitor build progress
- [ ] Wait for "Deployment successful" message
- [ ] Copy default DigitalOcean app URL
- [ ] Save app URL for DNS configuration
- [ ] Verify deployment shows in Claude response

#### Step 3: DNS Configuration
- [ ] Ask Claude for default app URL
- [ ] Copy app URL (format: app-xxxxx.ondigitalocean.app)
- [ ] Log in to DNS provider (Cloudflare/Namecheap)
- [ ] Navigate to DNS settings
- [ ] Add new CNAME record
- [ ] Set Name: `app`
- [ ] Set Value: [app URL from Claude]
- [ ] Set TTL: 300 (5 minutes)
- [ ] Save DNS record
- [ ] Note time for DNS propagation tracking

#### Step 4: Deployment Verification
- [ ] Copy DigitalOcean app URL
- [ ] Run curl command to `/api/health` endpoint
- [ ] Verify response: `{"status":"healthy"}`
- [ ] Wait 5-30 min for DNS propagation
- [ ] Test `https://app.taskifai.com/api/health`
- [ ] Verify custom domain health check passes
- [ ] Document deployment completion time

---

### Step 1: Prepare Environment File (2 minutes)

Create file on your desktop: `env-central-login.txt`

**Generate SECRET_KEY:**
```bash
openssl rand -hex 32
```

**Fill in template:**

```env
SECRET_KEY=paste-generated-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

SUPABASE_URL=paste-REGISTRY_SUPABASE_URL-here
SUPABASE_ANON_KEY=paste-REGISTRY_ANON_KEY-here
SUPABASE_SERVICE_KEY=paste-REGISTRY_SERVICE_KEY-here

REDIS_URL=paste-REDIS_URL-here

ALLOWED_ORIGINS=https://demo.taskifai.com,https://bibbi.taskifai.com,https://*.taskifai.com

RATE_LIMIT_ENABLED=true
DEBUG=false
```

**Save the file.**

✅ **Checkpoint:** Environment file ready

---

### Step 2: Deploy via Claude (5 minutes)

**In Claude Desktop, paste this command:**

```
Create a new DigitalOcean app for TaskifAI Central Login with the following configuration:

Name: taskifai-central
Region: nyc
Repository: https://github.com/YOUR_USERNAME/taskifai-platform
Branch: main

Components:

1. Static Site (Frontend):
   - Name: central-frontend
   - Build command: cd frontend && npm install && npm run build
   - Output directory: frontend/dist
   - Environment variables:
     VITE_API_URL=https://app.taskifai.com/api

2. Web Service (API - Basic 512MB):
   - Name: central-api
   - Dockerfile path: backend/Dockerfile
   - HTTP port: 8000
   - Instance size: basic-xxs
   - Health check path: /api/health
   - Environment variables:
     [Copy/paste entire content of env-central-login.txt here]

Deploy now and show me the deployment URL.
```

**Wait 5-10 minutes for deployment.**

Claude will show you:
- Build progress
- Deployment status
- Default app URL (e.g., `app-xxxxx-xxxxx.ondigitalocean.app`)

✅ **Checkpoint:** Central login deployed

---

### Step 3: Configure DNS (2 minutes)

**Get App URL from Claude:**

```
What is the default URL for taskifai-central app?
```

**In your DNS provider (Cloudflare, Namecheap, etc.):**

Add CNAME record:
```
Type: CNAME
Name: app
Value: [paste-app-url-from-claude]
TTL: 300 (5 minutes)
```

**Save DNS record.**

**Wait 5-30 minutes for propagation** (continue to next steps, check back later).

✅ **Checkpoint:** DNS configured

---

### Step 4: Verify Deployment (1 minute)

**Test health endpoint:**

```bash
# Using the DigitalOcean URL first (while DNS propagates)
curl https://app-xxxxx-xxxxx.ondigitalocean.app/api/health
```

**Expected:**
```json
{"status":"healthy"}
```

**Once DNS propagates:**
```bash
curl https://app.taskifai.com/api/health
```

✅ **Checkpoint:** Central login healthy

---

## Demo Tenant Deployment (15 minutes)

### ✅ Demo Tenant Detailed Checklist

#### Step 1: Register Tenant in Registry
- [ ] Open Supabase Registry Project
- [ ] Navigate to SQL Editor
- [ ] Click "New query"
- [ ] Copy INSERT INTO tenants SQL statement
- [ ] Replace placeholders with DEMO_SUPABASE_URL
- [ ] Replace placeholder with DEMO_ANON_KEY
- [ ] Execute SQL query
- [ ] Verify successful insertion
- [ ] Copy returned `tenant_id` UUID
- [ ] Save tenant_id for later use
- [ ] Run SELECT query to verify tenant exists
- [ ] Confirm subdomain='demo' in results

#### Step 2: Environment File Preparation
- [ ] Create file `env-demo-tenant.txt`
- [ ] Run `openssl rand -hex 32` for new SECRET_KEY
- [ ] Copy generated key (different from central)
- [ ] Set APP_NAME=TaskifAI Analytics Platform - Demo
- [ ] Set DEBUG=false
- [ ] Paste new SECRET_KEY
- [ ] Add ALGORITHM=HS256
- [ ] Add ACCESS_TOKEN_EXPIRE_MINUTES=1440
- [ ] Paste DEMO_SUPABASE_URL
- [ ] Paste DEMO_ANON_KEY
- [ ] Paste DEMO_SERVICE_KEY
- [ ] Paste REDIS_URL (same as central)
- [ ] Add OPENAI_API_KEY (if available)
- [ ] Add SENDGRID_API_KEY (if available)
- [ ] Set MAX_UPLOAD_SIZE=104857600
- [ ] Set UPLOAD_DIR=/tmp/uploads
- [ ] Set ALLOWED_ORIGINS=https://demo.taskifai.com
- [ ] Save environment file
- [ ] Verify all required values filled

#### Step 3: Deploy via Claude MCP
- [ ] Open Claude Desktop
- [ ] Prepare demo tenant deployment command
- [ ] Replace YOUR_USERNAME with GitHub username
- [ ] Copy environment from env-demo-tenant.txt
- [ ] Paste complete deployment command
- [ ] Include all 3 components (frontend, api, worker)
- [ ] Send command to Claude
- [ ] Monitor build progress (10-15 min)
- [ ] Wait for deployment completion
- [ ] Copy default DigitalOcean app URL
- [ ] Save demo app URL
- [ ] Verify all 3 components deployed

#### Step 4: DNS Configuration
- [ ] Ask Claude for demo app default URL
- [ ] Copy app URL from Claude response
- [ ] Log in to DNS provider
- [ ] Navigate to DNS settings
- [ ] Add new CNAME record
- [ ] Set Name: `demo`
- [ ] Set Value: [demo app URL]
- [ ] Set TTL: 300
- [ ] Save DNS record
- [ ] Note time for DNS propagation

#### Step 5: Create Admin User
- [ ] Copy DigitalOcean demo app URL
- [ ] Prepare curl POST request to /api/auth/register
- [ ] Set email: admin@demo.com
- [ ] Set password: SecurePassword123!
- [ ] Set full_name: Demo Admin
- [ ] Set role: admin
- [ ] Execute curl command
- [ ] Verify successful registration
- [ ] Copy `access_token` from response
- [ ] Copy `user_id` from response
- [ ] Save both values securely

#### Step 6: Register User in Tenant Registry
- [ ] Open Supabase Registry Project
- [ ] Navigate to SQL Editor
- [ ] Prepare INSERT INTO user_tenants SQL
- [ ] Paste saved tenant_id from Step 1
- [ ] Set email: admin@demo.com
- [ ] Execute SQL query
- [ ] Verify successful insertion
- [ ] Confirm user-tenant association created

---

### Step 1: Register Tenant in Registry (2 minutes)

**In Supabase (Registry Project):**

1. SQL Editor → New query
2. Paste:

```sql
INSERT INTO tenants (subdomain, display_name, database_url, database_anon_key, is_active)
VALUES (
    'demo',
    'Demo Account',
    'paste-DEMO_SUPABASE_URL-here',
    'paste-DEMO_ANON_KEY-here',
    true
);

-- Verify insertion
SELECT tenant_id, subdomain, display_name, is_active
FROM tenants
WHERE subdomain = 'demo';
```

3. Click "Run"
4. Copy the returned `tenant_id` (you'll need it later)

✅ **Checkpoint:** Tenant registered

---

### Step 2: Prepare Environment File (3 minutes)

Create file: `env-demo-tenant.txt`

**Generate SECRET_KEY (different from central):**
```bash
openssl rand -hex 32
```

**Fill in template:**

```env
APP_NAME=TaskifAI Analytics Platform - Demo
DEBUG=false

SECRET_KEY=paste-new-generated-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

SUPABASE_URL=paste-DEMO_SUPABASE_URL-here
SUPABASE_ANON_KEY=paste-DEMO_ANON_KEY-here
SUPABASE_SERVICE_KEY=paste-DEMO_SERVICE_KEY-here

REDIS_URL=paste-REDIS_URL-here

OPENAI_API_KEY=sk-your-openai-key-if-you-have-one
OPENAI_MODEL=gpt-4o-mini

SENDGRID_API_KEY=SG.your-sendgrid-key-if-you-have-one
SENDGRID_FROM_EMAIL=noreply@taskifai.com
SENDGRID_FROM_NAME=TaskifAI Demo

MAX_UPLOAD_SIZE=104857600
UPLOAD_DIR=/tmp/uploads

ALLOWED_ORIGINS=https://demo.taskifai.com
```

**Save the file.**

✅ **Checkpoint:** Demo environment ready

---

### Step 3: Deploy via Claude (7 minutes)

**In Claude Desktop:**

```
Create a DigitalOcean app for TaskifAI Demo Tenant:

Name: taskifai-demo
Region: nyc
Repository: https://github.com/YOUR_USERNAME/taskifai-platform
Branch: main

Components:

1. Static Site (Frontend):
   - Name: demo-frontend
   - Build command: cd frontend && npm install && npm run build
   - Output directory: frontend/dist
   - Environment variables:
     VITE_API_URL=https://demo.taskifai.com/api

2. Web Service (API - Professional 1GB):
   - Name: demo-api
   - Dockerfile path: backend/Dockerfile
   - HTTP port: 8000
   - Instance size: professional-xs
   - Health check path: /api/health
   - Environment variables:
     [Copy/paste entire content of env-demo-tenant.txt here]

3. Worker Service (Basic 512MB):
   - Name: demo-worker
   - Dockerfile path: backend/Dockerfile
   - Instance size: basic-xxs
   - Run command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
   - Environment variables:
     [Same as demo-api]

Deploy now and show me the deployment URL.
```

**Wait 10-15 minutes for deployment.**

✅ **Checkpoint:** Demo tenant deployed

---

### Step 4: Configure DNS (2 minutes)

**Get App URL from Claude:**

```
What is the default URL for taskifai-demo app?
```

**In your DNS provider:**

Add CNAME record:
```
Type: CNAME
Name: demo
Value: [paste-app-url-from-claude]
TTL: 300
```

**Save DNS record.**

✅ **Checkpoint:** Demo DNS configured

---

### Step 5: Create Admin User (1 minute)

**Using the DigitalOcean URL (while DNS propagates):**

```bash
curl -X POST https://app-demo-xxxxx.ondigitalocean.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.com",
    "password": "SecurePassword123!",
    "full_name": "Demo Admin",
    "role": "admin"
  }'
```

**Save the response:**
- Copy the `access_token`
- Copy the `user_id`

✅ **Checkpoint:** Admin user created

---

### Step 6: Register User in Tenant Registry (1 minute)

**In Supabase (Registry Project):**

SQL Editor → New query:

```sql
-- Use the tenant_id from Step 1
INSERT INTO user_tenants (tenant_id, email)
VALUES (
    'paste-tenant_id-from-step-1-here',
    'admin@demo.com'
);
```

Click "Run"

✅ **Checkpoint:** User registered in registry

---

## Testing & Verification (10 minutes)

### ✅ Testing Detailed Checklist

#### Test 1: Tenant Discovery API
- [ ] Prepare curl POST command
- [ ] Target: `https://app.taskifai.com/api/auth/discover-tenant`
- [ ] Set email: admin@demo.com
- [ ] Execute curl command
- [ ] Verify response contains "tenant": "demo"
- [ ] Verify redirect_url: "https://demo.taskifai.com/login"
- [ ] Confirm status code 200
- [ ] Mark test as PASSED

#### Test 2: Login API
- [ ] Prepare curl POST to login endpoint
- [ ] Target: `https://demo.taskifai.com/api/auth/login`
- [ ] Set email: admin@demo.com
- [ ] Set password: SecurePassword123!
- [ ] Execute curl command
- [ ] Verify access_token returned
- [ ] Verify user data in response
- [ ] Copy access_token
- [ ] Save token in environment: `export TOKEN="..."`
- [ ] Mark test as PASSED

#### Test 3: File Upload
- [ ] Create test CSV file `test-upload.csv`
- [ ] Add sample order data (2 rows minimum)
- [ ] Include required columns (Order ID, Functional Name, etc.)
- [ ] Save test file
- [ ] Prepare curl POST with file upload
- [ ] Target: `https://demo.taskifai.com/api/uploads`
- [ ] Include Authorization header with token
- [ ] Attach test file
- [ ] Set upload_mode=append
- [ ] Execute curl command
- [ ] Verify upload_id returned
- [ ] Verify processing_status in response
- [ ] Save upload_id for verification
- [ ] Mark test as PASSED

#### Test 4: Worker Processing Verification
- [ ] Open Claude Desktop
- [ ] Request logs: "Show logs for taskifai-demo demo-worker"
- [ ] Wait for log output
- [ ] Look for "Processing file..." message
- [ ] Verify "Vendor detected: ..." appears
- [ ] Check for "Inserted X rows" message
- [ ] Verify no error messages in logs
- [ ] Confirm processing completed successfully
- [ ] Mark test as PASSED

#### Test 5: Database Data Verification
- [ ] Open Supabase Demo Project
- [ ] Navigate to SQL Editor
- [ ] Run: `SELECT COUNT(*) FROM ecommerce_orders`
- [ ] Verify count matches uploaded rows (2)
- [ ] Run: `SELECT * FROM ecommerce_orders LIMIT 5`
- [ ] Verify data appears correctly
- [ ] Run: `SELECT * FROM upload_batches ORDER BY upload_timestamp DESC LIMIT 1`
- [ ] Verify processing_status = 'completed'
- [ ] Verify rows_processed = 2
- [ ] Confirm upload_timestamp is recent
- [ ] Mark test as PASSED

#### Test 6: Frontend Login Flow
- [ ] Open web browser
- [ ] Navigate to: `https://app.taskifai.com`
- [ ] Verify central login page loads
- [ ] Enter email: admin@demo.com
- [ ] Click "Continue" button
- [ ] Verify redirect to: `https://demo.taskifai.com/login`
- [ ] Enter password: SecurePassword123!
- [ ] Click "Login" button
- [ ] Verify successful login
- [ ] Confirm dashboard loads
- [ ] Check uploaded data visible in dashboard
- [ ] Test navigation between pages
- [ ] Mark test as PASSED

#### Final Verification Checklist
- [ ] All 6 tests passed
- [ ] Central login portal functional
- [ ] Demo tenant fully operational
- [ ] Worker processing files correctly
- [ ] Data flowing into database
- [ ] Frontend accessible and working
- [ ] Ready for production use

---

### Test 1: Tenant Discovery (1 minute)

```bash
curl -X POST https://app.taskifai.com/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com"}'
```

**Expected:**
```json
{
  "tenant": "demo",
  "redirect_url": "https://demo.taskifai.com/login"
}
```

✅ **Pass:** Tenant discovery working

---

### Test 2: Login (1 minute)

```bash
curl -X POST https://demo.taskifai.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.com",
    "password": "SecurePassword123!"
  }'
```

**Expected:** Access token + user data

**Save the token:**
```bash
export TOKEN="paste-access-token-here"
```

✅ **Pass:** Login working

---

### Test 3: Test File Upload (2 minutes)

**Create a test CSV file:**

```bash
cat > test-upload.csv << 'EOF'
Order ID,Functional Name,Product Name,Order Date,Quantity,Price
ORD001,Skin Care,Anti-Aging Serum,2025-01-01,2,49.99
ORD002,Hair Care,Shampoo,2025-01-02,1,15.99
EOF
```

**Upload file:**

```bash
curl -X POST https://demo.taskifai.com/api/uploads \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test-upload.csv" \
  -F "upload_mode=append"
```

**Expected:** Upload ID + processing status

✅ **Pass:** Upload working

---

### Test 4: Check Worker Processing (2 minutes)

**In Claude Desktop:**

```
Show logs for taskifai-demo demo-worker component
```

Look for:
- "Processing file..."
- "Vendor detected: ..."
- "Inserted X rows"
- No errors

✅ **Pass:** Worker processing files

---

### Test 5: Verify Data in Database (2 minutes)

**In Supabase (Demo Project):**

SQL Editor:

```sql
-- Check ecommerce_orders
SELECT COUNT(*) as total_orders FROM ecommerce_orders;

-- View sample data
SELECT * FROM ecommerce_orders LIMIT 5;

-- Check upload status
SELECT
    processing_status,
    rows_processed,
    upload_timestamp
FROM upload_batches
ORDER BY upload_timestamp DESC
LIMIT 1;
```

**Expected:**
- total_orders: 2
- processing_status: 'completed'
- rows_processed: 2

✅ **Pass:** Data in database

---

### Test 6: Test Frontend (2 minutes)

**Open browser:**

1. Visit: `https://app.taskifai.com`
2. Enter email: `admin@demo.com`
3. Click "Continue"
4. Should redirect to: `https://demo.taskifai.com/login`
5. Enter password: `SecurePassword123!`
6. Click "Login"
7. Should see dashboard with uploaded data

✅ **Pass:** Frontend working

---

## Next Steps

### ✅ Post-Deployment Checklist

#### Monitoring Setup (5 min)
- [ ] Visit https://uptimerobot.com
- [ ] Create free account
- [ ] Click "Add New Monitor"
- [ ] Add monitor for Central Login
  - [ ] Type: HTTP(s)
  - [ ] URL: `https://app.taskifai.com/api/health`
  - [ ] Monitoring Interval: 5 minutes
  - [ ] Name: TaskifAI Central Login
- [ ] Add monitor for Demo Tenant
  - [ ] Type: HTTP(s)
  - [ ] URL: `https://demo.taskifai.com/api/health`
  - [ ] Monitoring Interval: 5 minutes
  - [ ] Name: TaskifAI Demo Tenant
- [ ] Configure email alerts
  - [ ] Add notification email
  - [ ] Test notification
  - [ ] Verify alert settings
- [ ] Verify monitors show "Up" status

#### Documentation & Backup (10 min)
- [ ] Document all credentials in secure location
  - [ ] DigitalOcean API token
  - [ ] Supabase URLs and keys (Registry + Demo)
  - [ ] Redis connection string
  - [ ] SECRET_KEY values
  - [ ] Admin user credentials
- [ ] Create backup of environment files
  - [ ] env-central-login.txt
  - [ ] env-demo-tenant.txt
- [ ] Save tenant_id for demo tenant
- [ ] Document DNS configuration
- [ ] Save DigitalOcean app URLs
- [ ] Create deployment completion report
- [ ] Store all documentation securely

#### Adding BIBBI Tenant (15 min)
- [ ] Create Supabase project: "TaskifAI-BIBBI"
  - [ ] Choose same region
  - [ ] Generate strong password
  - [ ] Wait for provisioning
- [ ] Setup BIBBI database schema
  - [ ] Copy backend/db/schema.sql
  - [ ] Execute in SQL Editor
  - [ ] Copy backend/db/seed_vendor_configs.sql
  - [ ] Execute seed data
- [ ] Register BIBBI tenant in Registry
  - [ ] INSERT INTO tenants
  - [ ] subdomain: 'bibbi'
  - [ ] display_name: 'BIBBI Account'
  - [ ] Save tenant_id
- [ ] Create env-bibbi-tenant.txt
  - [ ] Generate new SECRET_KEY
  - [ ] Add BIBBI Supabase credentials
  - [ ] Configure all environment variables
- [ ] Deploy via Claude MCP
  - [ ] Create taskifai-bibbi app
  - [ ] Deploy frontend, api, worker
  - [ ] Wait for deployment completion
- [ ] Configure DNS
  - [ ] Add CNAME: bibbi → app URL
  - [ ] Wait for propagation
- [ ] Test BIBBI tenant
  - [ ] Health check
  - [ ] Create admin user
  - [ ] Register in tenant registry
  - [ ] Test login flow
- [ ] Add monitoring for BIBBI
  - [ ] UptimeRobot monitor
  - [ ] Email alerts configured

#### Weekly Maintenance Tasks (10 min/week)
- [ ] Check all app statuses in Claude
  - [ ] "Show status for all TaskifAI apps"
- [ ] Review resource usage
  - [ ] "Show CPU and memory usage for all apps this week"
  - [ ] "Show bandwidth usage this week"
- [ ] Check costs
  - [ ] "Show current month costs for all apps"
  - [ ] Compare against budget
- [ ] Review monitoring alerts
  - [ ] Check UptimeRobot dashboard
  - [ ] Investigate any downtime incidents
- [ ] Check worker logs for errors
  - [ ] Review each tenant's worker logs
  - [ ] Address any processing failures
- [ ] Verify database backups
  - [ ] Check Supabase automatic backups
  - [ ] Confirm backup retention settings
- [ ] Review DNS health
  - [ ] Test all subdomains resolving
  - [ ] Check TTL settings

#### Optional Enhancements Checklist
- [ ] **Email Notifications**
  - [ ] Sign up for SendGrid
  - [ ] Get API key
  - [ ] Configure sender email
  - [ ] Update environment variables
  - [ ] Redeploy apps
  - [ ] Test email sending
- [ ] **AI Chat Feature**
  - [ ] Get OpenAI API key
  - [ ] Update environment variables
  - [ ] Redeploy apps
  - [ ] Test chat functionality
- [ ] **Custom Vendor Processors**
  - [ ] Identify new vendor format
  - [ ] Create vendor processor
  - [ ] Add to detector patterns
  - [ ] Test with sample file
  - [ ] Deploy updated code
- [ ] **File Storage Upgrade**
  - [ ] Create DigitalOcean Space
  - [ ] Configure access keys
  - [ ] Update upload service
  - [ ] Test file uploads
- [ ] **Additional Domains**
  - [ ] Purchase new domains
  - [ ] Configure DNS
  - [ ] Add to allowed origins
  - [ ] Test accessibility

#### New Customer Onboarding Template (12 min)
- [ ] **Step 1: Gather Requirements (2 min)**
  - [ ] Customer subdomain name
  - [ ] Customer display name
  - [ ] Required vendor processors
  - [ ] User email addresses
- [ ] **Step 2: Infrastructure (3 min)**
  - [ ] Create Supabase project
  - [ ] Setup database schema
  - [ ] Save credentials securely
- [ ] **Step 3: Registry (1 min)**
  - [ ] Register tenant in database
  - [ ] Save tenant_id
- [ ] **Step 4: Environment (1 min)**
  - [ ] Create environment file
  - [ ] Generate SECRET_KEY
  - [ ] Configure all variables
- [ ] **Step 5: Deployment (5 min)**
  - [ ] Deploy via Claude MCP
  - [ ] Configure DNS
  - [ ] Wait for propagation
  - [ ] Verify health check
- [ ] **Step 6: Testing (2 min)**
  - [ ] Create admin user
  - [ ] Register in tenant registry
  - [ ] Test complete login flow
  - [ ] Verify upload functionality
- [ ] **Step 7: Documentation**
  - [ ] Document credentials
  - [ ] Provide customer with login URL
  - [ ] Send welcome email
  - [ ] Add to monitoring

---

### You Now Have:

✅ **Central login portal** at app.taskifai.com
✅ **Demo tenant** at demo.taskifai.com
✅ **Complete user flow** from discovery → login → upload → analytics
✅ **Production infrastructure** with auto-scaling and monitoring

### Recommended Actions:

#### 1. Setup Monitoring (5 minutes)

**Add Uptime Robot:**
1. Visit https://uptimerobot.com
2. Sign up (free)
3. Add monitors:
   - `https://app.taskifai.com/api/health` (5 min interval)
   - `https://demo.taskifai.com/api/health` (5 min interval)
4. Configure email alerts

#### 2. Add BIBBI Tenant (15 minutes)

Follow the same process as Demo Tenant:
1. Create Supabase project: "TaskifAI-BIBBI"
2. Setup schema
3. Register tenant in registry
4. Create environment file
5. Deploy via Claude
6. Configure DNS

#### 3. Customize for Your Customers

**For each new customer:**
1. Create Supabase project (3 min)
2. Register in registry (1 min)
3. Deploy via Claude (5 min)
4. Configure DNS (1 min)
5. Test deployment (2 min)

**Total per customer: ~12 minutes**

#### 4. Weekly Maintenance (10 minutes/week)

**Ask Claude:**
```
Show status for all TaskifAI apps
Show CPU and memory usage for all apps this week
Show bandwidth usage this week
Show current month costs for all apps
```

#### 5. Optional Enhancements

- **Add more vendors:** Customize `backend/app/services/vendors/`
- **Email notifications:** Configure SendGrid
- **AI chat:** Add OpenAI API key
- **File storage:** Upgrade to DigitalOcean Spaces
- **Custom domain:** Add additional domains

---

## Cost Summary

**Current Monthly Cost:**

| Item | Cost |
|------|------|
| Central Login API | $5 |
| Demo Tenant API | $12 |
| Demo Tenant Worker | $5 |
| Redis (Upstash Free) | $0 |
| Supabase (2 free projects) | $0 |
| Domain | $1 |
| **Total** | **$23/month** |

**When adding BIBBI tenant:** +$17/month = **$40/month total**

---

## Troubleshooting

### Issue: MCP not connecting

**Solution:**
1. Verify API token is correct
2. Restart Claude Desktop
3. Check config file syntax

### Issue: Deployment failed

**In Claude:**
```
Show deployment logs for taskifai-demo
Show build logs for latest deployment
```

Look for errors in output.

### Issue: DNS not propagating

**Check:**
```bash
dig demo.taskifai.com
```

**Wait 5-30 minutes.** DNS propagation varies by provider.

### Issue: Worker not processing files

**In Claude:**
```
Show logs for taskifai-demo demo-worker
Restart taskifai-demo demo-worker
```

---

## Support Resources

- **DigitalOcean Docs:** https://docs.digitalocean.com/products/app-platform/
- **Supabase Docs:** https://supabase.com/docs
- **MCP Docs:** https://modelcontextprotocol.io/

---

## Congratulations! 🎉

You've successfully deployed TaskifAI Platform on DigitalOcean App Platform with MCP!

**What you accomplished:**
- ✅ Central login with tenant discovery
- ✅ Isolated tenant deployments
- ✅ Automated background processing
- ✅ Secure multi-tenant architecture
- ✅ Production-ready infrastructure

**Next customer onboarding:** 12 minutes
**Monthly maintenance:** 10 minutes
**Cost per tenant:** $17/month

**You're ready to scale! 🚀**
