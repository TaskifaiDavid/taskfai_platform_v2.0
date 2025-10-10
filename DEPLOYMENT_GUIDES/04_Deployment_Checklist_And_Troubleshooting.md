# App Platform Deployment Checklist & Troubleshooting

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Central Login Deployment](#central-login-deployment)
3. [Tenant Deployment](#tenant-deployment)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Common Issues & Solutions](#common-issues--solutions)
6. [Monitoring & Health](#monitoring--health)
7. [Emergency Procedures](#emergency-procedures)

---

## Pre-Deployment Checklist

### Accounts & Services

- [ ] **DigitalOcean Account**
  - [ ] Account created and verified
  - [ ] Payment method configured
  - [ ] API token generated (read + write permissions)
  - [ ] Token saved securely

- [ ] **GitHub Repository**
  - [ ] Code pushed to repository
  - [ ] Repository accessible (public or private)
  - [ ] `.env.example` files documented
  - [ ] Dockerfile tested locally

- [ ] **Supabase Projects Created**
  - [ ] Tenant registry project
  - [ ] Demo tenant project
  - [ ] BIBBI tenant project (when needed)
  - [ ] API keys copied (URL, anon key, service key)

- [ ] **Redis (Upstash)**
  - [ ] Account created
  - [ ] Database created (Global region)
  - [ ] Connection string copied

- [ ] **Domain Name**
  - [ ] Domain purchased
  - [ ] Access to DNS management
  - [ ] DNS provider supports CNAME records

- [ ] **Claude Desktop**
  - [ ] Downloaded and installed
  - [ ] MCP configured with DO API token
  - [ ] MCP connection tested

### Optional Services

- [ ] **OpenAI API**
  - [ ] Account created
  - [ ] API key generated
  - [ ] Billing configured

- [ ] **SendGrid**
  - [ ] Account created
  - [ ] API key generated
  - [ ] Sender email verified

---

## Central Login Deployment

### Step 1: Prepare Environment Variables

Create file: `env-central-login.txt`

```env
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SUPABASE_URL=https://registry-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...
REDIS_URL=redis://default:xxx@xxx.upstash.io:6379
ALLOWED_ORIGINS=https://demo.taskifai.com,https://bibbi.taskifai.com
RATE_LIMIT_ENABLED=true
```

**Validation:**
- [ ] SECRET_KEY ≥32 characters
- [ ] All Supabase keys from registry project
- [ ] Redis URL from Upstash dashboard
- [ ] ALLOWED_ORIGINS includes all tenant subdomains

### Step 2: Setup Tenant Registry Database

**Execute in Supabase SQL Editor (Registry Project):**

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

**Verification:**
- [ ] Tables created successfully
- [ ] No errors in SQL Editor
- [ ] Indexes created

### Step 3: Deploy via MCP

**Ask Claude:**

```
Create a new DigitalOcean app for TaskifAI Central Login:

Name: taskifai-central
Region: nyc
Repository: https://github.com/[your-username]/taskifai-platform
Branch: main

Components:
1. Static Site (Frontend):
   - Name: central-frontend
   - Build command: cd frontend && npm install && npm run build
   - Output directory: frontend/dist
   - Environment: VITE_API_URL=https://app.taskifai.com/api

2. Web Service (API, Basic 512MB):
   - Name: central-api
   - Dockerfile: backend/Dockerfile
   - Port: 8000
   - Health check: /api/health
   - Environment: [paste env-central-login.txt]

Deploy now and show me the deployment status.
```

**Wait 5-10 minutes for deployment**

- [ ] Build completed successfully
- [ ] Frontend deployed
- [ ] API service running
- [ ] Health check passing

### Step 4: Configure DNS

**Get App URL from MCP:**
```
"What is the default URL for taskifai-central app?"
```

**Add DNS Records:**

```dns
Type: CNAME
Name: app
Value: [app-url-from-mcp].ondigitalocean.app
TTL: 300
```

**Verification:**
- [ ] DNS record added
- [ ] Wait 5-30 minutes for propagation
- [ ] Test: `dig app.taskifai.com` shows CNAME

### Step 5: Verify Deployment

```bash
# Test health endpoint
curl https://app.taskifai.com/api/health

# Expected response:
{"status":"healthy"}

# Test tenant discovery (should fail - no tenants yet)
curl -X POST https://app.taskifai.com/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Expected: 404 (tenant not found)
```

**Checklist:**
- [ ] Health endpoint returns 200
- [ ] HTTPS working (not HTTP)
- [ ] Discovery endpoint returns 404 (expected)
- [ ] No errors in App Platform logs

---

## Tenant Deployment

### Demo Tenant Example

Follow for each tenant: demo, bibbi, customer3, etc.

### Step 1: Create Supabase Project

**In Supabase Dashboard:**
- [ ] Create new project: "TaskifAI-Demo"
- [ ] Choose region (closest to users)
- [ ] Generate strong database password
- [ ] Wait for provisioning (~2 minutes)

**Copy Credentials:**
```
Project URL: https://xxxxx.supabase.co
Anon Key: eyJhbGc...
Service Role Key: eyJhbGc...
```

### Step 2: Setup Database Schema

**Execute in SQL Editor (Demo Project):**

- [ ] Copy content from `backend/db/schema.sql`
- [ ] Paste into SQL Editor
- [ ] Run
- [ ] Copy content from `backend/db/seed_vendor_configs.sql`
- [ ] Paste into SQL Editor
- [ ] Run

**Verify Tables:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Expected tables:
- [ ] ecommerce_orders
- [ ] sellout_entries2
- [ ] products
- [ ] users
- [ ] upload_batches
- [ ] conversation_history
- [ ] vendor_configs

### Step 3: Register Tenant in Registry

**Execute in Registry Supabase Project:**

```sql
INSERT INTO tenants (subdomain, display_name, database_url, database_anon_key, is_active)
VALUES (
    'demo',
    'Demo Account',
    'https://xxxxx.supabase.co',
    'eyJhbGc...anon-key...',
    true
);

-- Verify
SELECT tenant_id, subdomain, display_name, is_active
FROM tenants
WHERE subdomain = 'demo';
```

- [ ] Tenant registered successfully
- [ ] tenant_id returned
- [ ] is_active = true

### Step 4: Prepare Environment

Create file: `env-demo-tenant.txt`

```env
APP_NAME=TaskifAI Analytics Platform - Demo
DEBUG=false
SECRET_KEY=demo-specific-secret-key-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SUPABASE_URL=https://demo-xxxxx.supabase.co
SUPABASE_ANON_KEY=demo-anon-key
SUPABASE_SERVICE_KEY=demo-service-key
REDIS_URL=redis://default:xxx@xxx.upstash.io:6379
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
SENDGRID_API_KEY=SG.your-key
SENDGRID_FROM_EMAIL=noreply@taskifai.com
SENDGRID_FROM_NAME=TaskifAI Demo
MAX_UPLOAD_SIZE=104857600
UPLOAD_DIR=/tmp/uploads
ALLOWED_ORIGINS=https://demo.taskifai.com
```

**Validation:**
- [ ] Different SECRET_KEY from central login
- [ ] Supabase credentials from demo project
- [ ] All API keys valid

### Step 5: Deploy via MCP

**Ask Claude:**

```
Create DigitalOcean app for TaskifAI Demo Tenant:

Name: taskifai-demo
Region: nyc
Repository: https://github.com/[your-username]/taskifai-platform
Branch: main

Components:
1. Static Site (Frontend):
   - Name: demo-frontend
   - Build command: cd frontend && npm install && npm run build
   - Output directory: frontend/dist
   - Environment: VITE_API_URL=https://demo.taskifai.com/api

2. Web Service (API, Professional 1GB):
   - Name: demo-api
   - Dockerfile: backend/Dockerfile
   - Port: 8000
   - Health check: /api/health
   - Instance size: professional-xs
   - Environment: [paste env-demo-tenant.txt]

3. Worker Service (Basic 512MB):
   - Name: demo-worker
   - Dockerfile: backend/Dockerfile
   - Instance size: basic-xxs
   - Run command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
   - Environment: [same as demo-api]

Deploy now.
```

**Wait 10-15 minutes for deployment**

- [ ] Frontend build completed
- [ ] API service running
- [ ] Worker service running
- [ ] All health checks passing

### Step 6: Configure DNS

```dns
Type: CNAME
Name: demo
Value: [app-url-from-mcp].ondigitalocean.app
TTL: 300
```

- [ ] DNS record added
- [ ] Propagation wait (5-30 min)
- [ ] Test: `dig demo.taskifai.com`

### Step 7: Create Admin User

**Via API:**
```bash
curl -X POST https://demo.taskifai.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.com",
    "password": "SecurePassword123!",
    "full_name": "Demo Admin",
    "role": "admin"
  }'
```

- [ ] Registration successful
- [ ] Token received
- [ ] user_id saved

### Step 8: Register User in Tenant Registry

**Execute in Registry Supabase:**

```sql
-- Get tenant_id
SELECT tenant_id FROM tenants WHERE subdomain = 'demo';

-- Register user
INSERT INTO user_tenants (tenant_id, email)
VALUES ('[tenant-id-from-above]', 'admin@demo.com');
```

- [ ] User registered in registry
- [ ] No errors

### Step 9: Verify Complete Flow

**1. Tenant Discovery:**
```bash
curl -X POST https://app.taskifai.com/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com"}'
```

Expected:
```json
{
  "tenant": "demo",
  "redirect_url": "https://demo.taskifai.com/login"
}
```

**2. Login:**
```bash
curl -X POST https://demo.taskifai.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","password":"SecurePassword123!"}'
```

Expected: Access token + user data

**3. Test Upload:**
```bash
curl -X POST https://demo.taskifai.com/api/uploads \
  -H "Authorization: Bearer [token]" \
  -F "file=@/path/to/test-file.xlsx" \
  -F "upload_mode=append"
```

Expected: Upload ID + processing status

**4. Check Worker Processing:**

Ask Claude:
```
"Show logs for taskifai-demo demo-worker component"
```

- [ ] Worker processing file
- [ ] No errors in logs
- [ ] Task completing

**5. Verify Data in Supabase:**

```sql
-- Check ecommerce_orders
SELECT COUNT(*) FROM ecommerce_orders;

-- Check upload status
SELECT processing_status, rows_processed
FROM upload_batches
ORDER BY upload_timestamp DESC
LIMIT 1;
```

- [ ] Data inserted
- [ ] Upload marked as completed
- [ ] Row count matches file

---

## Post-Deployment Verification

### System Health

**App Platform Dashboard:**

Ask Claude:
```
"Show status for all TaskifAI apps"
```

- [ ] taskifai-central: Running
- [ ] taskifai-demo: Running
- [ ] All components healthy
- [ ] No failed deployments

### Application Health

**Central Login:**
```bash
curl -I https://app.taskifai.com
# Expected: HTTP/2 200

curl https://app.taskifai.com/api/health
# Expected: {"status":"healthy"}
```

**Demo Tenant:**
```bash
curl -I https://demo.taskifai.com
# Expected: HTTP/2 200

curl https://demo.taskifai.com/api/health
# Expected: {"status":"healthy"}
```

### Security Verification

**SSL/TLS:**
```bash
# Check HTTPS redirect
curl -I http://demo.taskifai.com
# Expected: 301 → https://demo.taskifai.com

# Check SSL grade (manual)
# Visit: https://www.ssllabs.com/ssltest/
# Enter: demo.taskifai.com
# Expected: A or A+ grade
```

**Rate Limiting:**
```bash
# Send 15 requests quickly
for i in {1..15}; do
  curl -X POST https://app.taskifai.com/api/auth/discover-tenant \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com"}'
done
```

- [ ] First 10 requests: 404 (tenant not found)
- [ ] Next 5 requests: 429 (rate limited)

---

## Common Issues & Solutions

### Issue 1: Deployment Failed

**Symptoms:**
- Build fails
- App won't start
- Health checks failing

**Diagnosis via MCP:**
```
"Show deployment logs for taskifai-demo"
"Show build logs for latest deployment"
```

**Common Causes:**

**A. Missing Environment Variables**

Solution:
```
"Show environment variables for taskifai-demo demo-api"
"Update taskifai-demo demo-api environment variable SECRET_KEY to [new-value]"
```

**B. Dockerfile Error**

Check backend/Dockerfile locally:
```bash
cd backend
docker build -t test-build .
docker run -p 8000:8000 test-build
```

**C. Port Mismatch**

Ensure Dockerfile exposes port 8000:
```dockerfile
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**D. Out of Memory**

Solution via MCP:
```
"Update taskifai-demo demo-api to professional-xs instance (1GB)"
```

---

### Issue 2: App Not Accessible

**Symptoms:**
- Domain doesn't load
- SSL errors
- 404 errors

**Diagnosis:**

**Check DNS:**
```bash
dig demo.taskifai.com

# Expected:
# demo.taskifai.com. 300 IN CNAME app-xxxxx.ondigitalocean.app.
```

**Check App URL:**

Ask Claude:
```
"What is the default URL for taskifai-demo?"
```

**Solutions:**

**A. DNS Not Propagated**
- Wait 5-30 more minutes
- Check propagation: https://dnschecker.org

**B. Wrong CNAME Target**
- Update DNS record with correct App Platform URL
- Wait for propagation

**C. SSL Pending**
- App Platform provisioning SSL (takes 2-5 min)
- Check in DO dashboard: Apps → taskifai-demo → Settings → Domains

---

### Issue 3: Worker Not Processing Files

**Symptoms:**
- Upload stuck at "processing"
- No data in database
- Worker logs show errors

**Diagnosis via MCP:**
```
"Show logs for taskifai-demo demo-worker"
```

**Common Causes:**

**A. Redis Connection Failed**

Check REDIS_URL in environment:
```
"Show environment variables for taskifai-demo demo-worker"
```

Test Redis:
```bash
# Using redis-cli (if you have it)
redis-cli -u redis://default:xxx@xxx.upstash.io:6379 ping
```

**B. Worker Not Running**

Check status via MCP:
```
"Show status for taskifai-demo demo-worker component"
"Restart taskifai-demo demo-worker"
```

**C. Out of Memory**

Upgrade worker instance:
```
"Update taskifai-demo demo-worker to basic-xs instance (1GB)"
```

**D. Vendor Detection Failed**

Check logs for vendor detection errors:
```
"Show logs for taskifai-demo demo-worker" (look for "vendor_detector" errors)
```

---

### Issue 4: Tenant Discovery Fails

**Symptoms:**
- User can't login from central portal
- Discovery returns 404 for existing user

**Diagnosis:**

**Check Registry Data:**

Execute in Registry Supabase:
```sql
SELECT t.subdomain, ut.email
FROM tenants t
JOIN user_tenants ut ON t.tenant_id = ut.tenant_id
WHERE ut.email = 'admin@demo.com';
```

**Solutions:**

**A. User Not Registered**

Register in registry:
```sql
-- Get tenant_id
SELECT tenant_id FROM tenants WHERE subdomain = 'demo';

-- Register user
INSERT INTO user_tenants (tenant_id, email)
VALUES ('[tenant-id]', 'admin@demo.com')
ON CONFLICT (tenant_id, email) DO NOTHING;
```

**B. Tenant Not Active**

Activate tenant:
```sql
UPDATE tenants SET is_active = true WHERE subdomain = 'demo';
```

**C. Central API Can't Reach Registry**

Check central login environment:
```
"Show environment variables for taskifai-central central-api"
```

Verify SUPABASE_URL points to registry project.

---

### Issue 5: High Costs

**Symptoms:**
- Monthly bill higher than expected
- Bandwidth overages
- Unexpected resource usage

**Diagnosis via MCP:**
```
"Show bandwidth usage for all apps this month"
"Show resource usage for taskifai-demo"
```

**Solutions:**

**A. Over-Sized Instances**

Check if resources underutilized:
```
"Show CPU and memory usage for taskifai-demo demo-api"
```

If CPU <30% and Memory <50%:
```
"Update taskifai-demo demo-api to basic-xs instance"
```

**Savings: $12/mo → $5/mo**

**B. Too Many Instances**

If traffic is low:
```
"Scale taskifai-demo demo-api to 1 instance"
```

**C. Bandwidth Overages**

Optimize:
- Compress images/files
- Use CDN for static assets
- Enable gzip compression

---

## Monitoring & Health

### Daily Health Checks

**Automated via MCP:**

Ask Claude daily:
```
"Show status for all TaskifAI apps"
"Show any failed deployments in last 24 hours"
"Show error rate for taskifai-demo"
```

### Weekly Reviews

**Performance:**
```
"Show CPU and memory usage for all apps this week"
"Show response times for taskifai-demo"
"Show bandwidth usage this week"
```

**Costs:**
```
"Show current month costs for all apps"
"Compare to last month"
```

### Monthly Audits

- [ ] Review and rotate API keys
- [ ] Check Supabase database sizes
- [ ] Review Redis usage
- [ ] Audit user access logs
- [ ] Check backup status
- [ ] Review error logs

### External Monitoring (Recommended)

**Setup Uptime Robot:**

1. Sign up: https://uptimerobot.com
2. Add monitors:
   - https://app.taskifai.com/api/health (5 min interval)
   - https://demo.taskifai.com/api/health (5 min interval)
3. Configure email alerts

---

## Emergency Procedures

### Service Down

**1. Identify Issue via MCP:**
```
"Show status for taskifai-demo"
"Show latest logs for taskifai-demo demo-api"
```

**2. Quick Restart:**
```
"Restart taskifai-demo"
```

**3. If Restart Fails:**
```
"Rollback taskifai-demo to previous deployment"
```

**4. Verify Recovery:**
```bash
curl https://demo.taskifai.com/api/health
```

### Database Issues

**1. Check Supabase Status:**
- Visit: https://status.supabase.com
- Check for outages

**2. Verify Connection:**

Test from local machine:
```bash
psql "postgresql://postgres:[password]@db.xxxxx.supabase.co:5432/postgres"
```

**3. Restore from Backup:**
- Supabase Dashboard → Database → Backups
- Select backup point
- Restore

### Security Breach

**1. Rotate All Secrets Immediately:**

Generate new keys:
```bash
openssl rand -hex 32
```

Update via MCP:
```
"Update taskifai-demo environment variable SECRET_KEY to [new-value]"
"Restart taskifai-demo"
```

**2. Revoke API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- SendGrid: https://app.sendgrid.com/settings/api_keys
- Supabase: Project settings → API → Revoke service key
- DigitalOcean: API → Tokens → Revoke

**3. Review Access Logs:**

Check Supabase logs and upload history for unauthorized activity.

**4. Force User Logout:**

Changing SECRET_KEY invalidates all JWT tokens.

---

## Quick Reference

### Essential MCP Commands

```bash
# List all apps
"List my DigitalOcean apps"

# Show app status
"Show status for taskifai-demo"

# View logs
"Show logs for taskifai-demo demo-api"

# Restart app
"Restart taskifai-demo"

# Deploy latest code
"Deploy latest code from main to taskifai-demo"

# Rollback
"Rollback taskifai-demo to previous deployment"

# Scale resources
"Update taskifai-demo demo-api to professional-s instance"
"Scale taskifai-demo demo-api to 2 instances"

# Check metrics
"Show CPU usage for taskifai-demo"
"Show bandwidth for taskifai-demo this month"
```

### Health Check URLs

```
Central Login: https://app.taskifai.com/api/health
Demo Tenant: https://demo.taskifai.com/api/health
BIBBI Tenant: https://bibbi.taskifai.com/api/health
```

### Support Resources

- **DigitalOcean Support:** https://www.digitalocean.com/support
- **Supabase Support:** https://supabase.com/support
- **App Platform Docs:** https://docs.digitalocean.com/products/app-platform/

---

## Summary

You now have:

✅ **Complete deployment checklist** for central login + tenants
✅ **Step-by-step verification** procedures
✅ **Common issue troubleshooting** guides
✅ **Monitoring strategies** for daily/weekly/monthly
✅ **Emergency procedures** for critical situations

**Next Steps:**
1. Execute deployment checklist
2. Setup monitoring (Uptime Robot)
3. Schedule weekly health reviews
4. Document any custom procedures

**Good luck with your deployment! 🚀**
