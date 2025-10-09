# Deployment Checklist & Troubleshooting Guide

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Central Login Deployment](#central-login-deployment)
3. [Tenant Deployment](#tenant-deployment)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Common Issues & Solutions](#common-issues--solutions)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Emergency Procedures](#emergency-procedures)

---

## Pre-Deployment Checklist

### Infrastructure Requirements

- [ ] **Domain purchased and DNS configured**
  - [ ] `taskifai.com` registered
  - [ ] Nameservers pointing to DNS provider
  - [ ] DNS propagation verified (`dig taskifai.com`)

- [ ] **SSL Certificates ready**
  - [ ] Wildcard cert (`*.taskifai.com`) OR
  - [ ] Individual certs per subdomain
  - [ ] Certbot installed on servers

- [ ] **Servers provisioned**
  - [ ] Central login server (1 vCPU, 1GB RAM minimum)
  - [ ] Tenant server(s) (2 vCPU, 4GB RAM minimum per tenant)
  - [ ] SSH access configured
  - [ ] Firewalls configured (ports 22, 80, 443)

- [ ] **Supabase projects created**
  - [ ] Tenant registry project
  - [ ] Demo tenant project
  - [ ] Future tenant projects (as needed)
  - [ ] Billing configured
  - [ ] Backups enabled

- [ ] **Third-party services configured**
  - [ ] OpenAI API key obtained
  - [ ] SendGrid account setup
  - [ ] Redis hosting (Upstash/Redis Cloud) OR local Redis

- [ ] **Repository & CI/CD**
  - [ ] Code pushed to Git repository
  - [ ] .env.example files documented
  - [ ] Deployment scripts tested locally
  - [ ] CI/CD pipeline configured (optional)

---

## Central Login Deployment

### Step 1: Server Setup

```bash
# ✓ SSH into central login server
ssh root@app.taskifai.com

# ✓ Update system
apt update && apt upgrade -y

# ✓ Install dependencies
apt install -y nginx certbot python3-certbot-nginx nodejs npm git redis-server

# ✓ Create deployment user
useradd -m -s /bin/bash deploy
usermod -aG sudo deploy
```

### Step 2: Application Deployment

```bash
# ✓ Clone repository
su - deploy
mkdir -p /var/www/taskifai-central
cd /var/www/taskifai-central
git clone https://github.com/yourusername/taskifai-platform.git .

# ✓ Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ✓ Configure environment
cp .env.example .env
nano .env  # Edit with actual credentials

# Required variables:
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - SUPABASE_URL (tenant registry)
# - SUPABASE_ANON_KEY (tenant registry)
# - SUPABASE_SERVICE_KEY (tenant registry)
# - REDIS_URL
# - ALLOWED_ORIGINS (add all tenant subdomains)
```

**Environment Validation:**

```bash
# ✓ Test environment configuration
python << EOF
from app.core.config import settings
print(f"App Name: {settings.app_name}")
print(f"Supabase URL: {settings.supabase_url}")
print(f"Secret Key Length: {len(settings.secret_key)}")
assert len(settings.secret_key) >= 32, "Secret key too short!"
print("✓ Environment configuration valid")
EOF
```

### Step 3: Database Setup

```bash
# ✓ Setup tenant registry schema
# Copy schema SQL
cat > /tmp/tenant_registry_schema.sql << 'EOF'
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
EOF

# ✓ Execute in Supabase (manual step)
# Navigate to: Supabase Dashboard → SQL Editor → Paste schema → Run
```

### Step 4: Systemd Services

```bash
# ✓ Create API service
sudo tee /etc/systemd/system/taskifai-central-api.service << EOF
[Unit]
Description=TaskifAI Central Login API
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/var/www/taskifai-central/backend
Environment="PATH=/var/www/taskifai-central/backend/venv/bin"
ExecStart=/var/www/taskifai-central/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ✓ Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable taskifai-central-api
sudo systemctl start taskifai-central-api

# ✓ Check status
sudo systemctl status taskifai-central-api
```

### Step 5: Frontend Build

```bash
# ✓ Build frontend
cd /var/www/taskifai-central/frontend
npm install

# ✓ Configure environment
cp .env.example .env
nano .env  # Set VITE_API_URL=https://app.taskifai.com/api

# ✓ Build for production
npm run build

# Verify dist/ directory created
ls -lh dist/
```

### Step 6: Nginx Configuration

```bash
# ✓ Create Nginx config
sudo tee /etc/nginx/sites-available/app.taskifai.com << 'EOF'
server {
    listen 80;
    server_name app.taskifai.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.taskifai.com;

    # SSL (will be configured by Certbot)
    ssl_certificate /etc/letsencrypt/live/app.taskifai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.taskifai.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Frontend (React SPA)
    location / {
        root /var/www/taskifai-central/frontend/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# ✓ Enable site
sudo ln -s /etc/nginx/sites-available/app.taskifai.com /etc/nginx/sites-enabled/

# ✓ Test Nginx config
sudo nginx -t

# ✓ Reload Nginx
sudo systemctl reload nginx
```

### Step 7: SSL Setup

```bash
# ✓ Get SSL certificate
sudo certbot --nginx -d app.taskifai.com --non-interactive --agree-tos -m admin@taskifai.com

# ✓ Test auto-renewal
sudo certbot renew --dry-run

# ✓ Verify HTTPS
curl -I https://app.taskifai.com
```

### Step 8: Verification

```bash
# ✓ Test health endpoint
curl https://app.taskifai.com/api/health
# Expected: {"status": "healthy"}

# ✓ Test tenant discovery
curl -X POST https://app.taskifai.com/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email": "nonexistent@example.com"}'
# Expected: 404 (no tenants registered yet)

# ✓ Check logs
sudo journalctl -u taskifai-central-api -n 50

# ✓ Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Tenant Deployment

### Demo Tenant Example

Follow these steps for each tenant (demo, bibbi, customer3, etc.):

### Step 1: Create Supabase Project

- [ ] **Login to Supabase Dashboard**
- [ ] **Create new project**
  - [ ] Name: "TaskifAI Demo Tenant"
  - [ ] Region: Choose closest to users
  - [ ] Generate strong database password
  - [ ] Wait for project provisioning (~2 minutes)

- [ ] **Copy credentials**
  ```
  Project URL: https://xxxxx.supabase.co
  Anon Key: eyJhbGc...
  Service Role Key: eyJhbGc...
  ```

- [ ] **Execute schema**
  - [ ] Navigate to SQL Editor
  - [ ] Paste content from `backend/db/schema.sql`
  - [ ] Run
  - [ ] Paste content from `backend/db/seed_vendor_configs.sql`
  - [ ] Run

- [ ] **Verify tables created**
  ```sql
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'public'
  ORDER BY table_name;
  ```

### Step 2: Register Tenant in Registry

```sql
-- Execute in Tenant Registry Supabase project
INSERT INTO tenants (subdomain, display_name, database_url, database_anon_key)
VALUES (
    'demo',
    'Demo Account',
    'https://xxxxx.supabase.co',
    'eyJhbGc...anon-key...'
);

-- Verify insertion
SELECT tenant_id, subdomain, display_name, is_active
FROM tenants
WHERE subdomain = 'demo';
```

### Step 3: Server Setup

```bash
# ✓ SSH into tenant server
ssh root@demo.taskifai.com

# ✓ Update system
apt update && apt upgrade -y

# ✓ Install dependencies
apt install -y nginx certbot python3-certbot-nginx nodejs npm git redis-server

# ✓ Create application directory
mkdir -p /var/www/taskifai-demo
cd /var/www/taskifai-demo

# ✓ Clone repository
git clone https://github.com/yourusername/taskifai-platform.git .
```

### Step 4: Backend Configuration

```bash
# ✓ Setup Python environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ✓ Configure environment
cat > .env << EOF
APP_NAME="TaskifAI Analytics Platform - Demo"
DEBUG=false

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Supabase (Demo tenant database)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...demo-anon-key...
SUPABASE_SERVICE_KEY=eyJhbGc...demo-service-key...

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# SendGrid
SENDGRID_API_KEY=SG.your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@taskifai.com
SENDGRID_FROM_NAME=TaskifAI Demo

# File Upload
MAX_UPLOAD_SIZE=104857600
UPLOAD_DIR=/var/www/taskifai-demo/uploads

# CORS
ALLOWED_ORIGINS=https://demo.taskifai.com
EOF

# ✓ Create uploads directory
mkdir -p /var/www/taskifai-demo/uploads
sudo chown www-data:www-data /var/www/taskifai-demo/uploads
```

### Step 5: Systemd Services

```bash
# ✓ Backend API service
sudo tee /etc/systemd/system/taskifai-demo-api.service << EOF
[Unit]
Description=TaskifAI Demo API
After=network.target redis.service

[Service]
Type=simple
User=deploy
WorkingDirectory=/var/www/taskifai-demo/backend
Environment="PATH=/var/www/taskifai-demo/backend/venv/bin"
ExecStart=/var/www/taskifai-demo/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ✓ Celery worker service
sudo tee /etc/systemd/system/taskifai-demo-worker.service << EOF
[Unit]
Description=TaskifAI Demo Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=deploy
WorkingDirectory=/var/www/taskifai-demo/backend
Environment="PATH=/var/www/taskifai-demo/backend/venv/bin"
ExecStart=/var/www/taskifai-demo/backend/venv/bin/celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ✓ Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable taskifai-demo-api taskifai-demo-worker
sudo systemctl start taskifai-demo-api taskifai-demo-worker

# ✓ Check status
sudo systemctl status taskifai-demo-api
sudo systemctl status taskifai-demo-worker
```

### Step 6: Frontend Build

```bash
# ✓ Build frontend
cd /var/www/taskifai-demo/frontend
npm install

# ✓ Configure environment
cat > .env << EOF
VITE_API_URL=https://demo.taskifai.com/api
VITE_ENVIRONMENT=production
EOF

# ✓ Build
npm run build

# ✓ Verify dist/ created
ls -lh dist/
```

### Step 7: Nginx & SSL

```bash
# ✓ Create Nginx config (same as central login, but with demo subdomain)
sudo tee /etc/nginx/sites-available/demo.taskifai.com << 'EOF'
# [Similar to central login config, replace app.taskifai.com with demo.taskifai.com]
# [Add client_max_body_size 100M; for file uploads]
EOF

# ✓ Enable site
sudo ln -s /etc/nginx/sites-available/demo.taskifai.com /etc/nginx/sites-enabled/

# ✓ Test and reload
sudo nginx -t
sudo systemctl reload nginx

# ✓ Get SSL certificate
sudo certbot --nginx -d demo.taskifai.com --non-interactive --agree-tos -m admin@taskifai.com
```

### Step 8: Create Admin User

```bash
# ✓ Create first admin user via API
curl -X POST https://demo.taskifai.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.com",
    "password": "SecurePassword123!",
    "full_name": "Demo Admin",
    "role": "admin"
  }'

# Save the returned token and user_id
```

### Step 9: Register User in Tenant Registry

```sql
-- Execute in Tenant Registry Supabase
-- Get tenant_id first
SELECT tenant_id FROM tenants WHERE subdomain = 'demo';

-- Register admin user
INSERT INTO user_tenants (tenant_id, email)
VALUES ('tenant-id-from-above', 'admin@demo.com');
```

### Step 10: Verification

```bash
# ✓ Test full user flow
# 1. Discover tenant
curl -X POST https://app.taskifai.com/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@demo.com"}'
# Expected: {"tenant": "demo", "redirect_url": "https://demo.taskifai.com/login"}

# 2. Login
curl -X POST https://demo.taskifai.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@demo.com", "password": "SecurePassword123!"}'
# Expected: {"access_token": "...", "user": {...}}

# 3. Test authenticated endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://demo.taskifai.com/api/uploads

# 4. Test file upload (use demo file)
curl -X POST https://demo.taskifai.com/api/uploads \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/demo_file.xlsx" \
  -F "upload_mode=append"

# 5. Check Celery processing
sudo journalctl -u taskifai-demo-worker -n 50

# 6. Verify data in Supabase
# Query ecommerce_orders or sellout_entries2 tables
```

---

## Post-Deployment Verification

### System Health Checklist

```bash
# ✓ All services running
sudo systemctl status taskifai-central-api
sudo systemctl status taskifai-demo-api
sudo systemctl status taskifai-demo-worker
sudo systemctl status redis-server
sudo systemctl status nginx

# ✓ Ports listening
sudo netstat -tlnp | grep -E ':(80|443|6379|8000)'

# ✓ Disk space
df -h

# ✓ Memory usage
free -h

# ✓ CPU load
uptime
```

### Application Health

```bash
# ✓ Central login portal
curl -I https://app.taskifai.com
curl https://app.taskifai.com/api/health

# ✓ Demo tenant
curl -I https://demo.taskifai.com
curl https://demo.taskifai.com/api/health

# ✓ Redis
redis-cli ping

# ✓ Celery worker
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://demo.taskifai.com/api/admin/worker-status
```

### Security Verification

```bash
# ✓ SSL/TLS grade
# Visit: https://www.ssllabs.com/ssltest/
# Enter: app.taskifai.com and demo.taskifai.com
# Expected: A or A+ grade

# ✓ HTTPS enforcement
curl -I http://app.taskifai.com
# Expected: 301 redirect to HTTPS

# ✓ Security headers
curl -I https://demo.taskifai.com | grep -E '(Strict-Transport|X-Frame|X-Content)'

# ✓ Rate limiting
for i in {1..15}; do
  curl -X POST https://app.taskifai.com/api/auth/discover-tenant \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}'
done
# Expected: 429 Too Many Requests after 10 requests
```

---

## Common Issues & Solutions

### Issue 1: Service Won't Start

**Symptoms:**
```bash
sudo systemctl status taskifai-demo-api
● taskifai-demo-api.service - TaskifAI Demo API
   Loaded: loaded
   Active: failed
```

**Diagnosis:**
```bash
# Check detailed logs
sudo journalctl -u taskifai-demo-api -n 100 --no-pager

# Common errors:
# - Port already in use
# - Missing environment variables
# - Import errors
# - Permission errors
```

**Solutions:**

**A. Port already in use**
```bash
# Find process using port 8000
sudo lsof -i :8000
# Kill process
sudo kill -9 <PID>
# Restart service
sudo systemctl restart taskifai-demo-api
```

**B. Missing environment variables**
```bash
# Verify .env file exists and has correct values
cat /var/www/taskifai-demo/backend/.env | grep -E '(SUPABASE_URL|SECRET_KEY)'

# Test environment loading
cd /var/www/taskifai-demo/backend
source venv/bin/activate
python << EOF
from app.core.config import settings
print(settings.supabase_url)
EOF
```

**C. Import errors**
```bash
# Reinstall dependencies
cd /var/www/taskifai-demo/backend
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Check for missing packages
python -c "import fastapi; import supabase; import celery"
```

**D. Permission errors**
```bash
# Fix ownership
sudo chown -R deploy:deploy /var/www/taskifai-demo

# Fix uploads directory
sudo chown www-data:www-data /var/www/taskifai-demo/uploads
sudo chmod 755 /var/www/taskifai-demo/uploads
```

---

### Issue 2: File Upload Fails

**Symptoms:**
- Upload stuck at "processing"
- Status shows "failed" immediately
- No data in database

**Diagnosis:**
```bash
# Check Celery worker logs
sudo journalctl -u taskifai-demo-worker -n 100 --no-pager

# Check Redis connection
redis-cli ping

# Check upload directory permissions
ls -la /var/www/taskifai-demo/uploads

# Check Celery active tasks
cd /var/www/taskifai-demo/backend
source venv/bin/activate
celery -A app.workers.celery_app inspect active
```

**Solutions:**

**A. Celery worker not running**
```bash
sudo systemctl restart taskifai-demo-worker
sudo systemctl status taskifai-demo-worker
```

**B. Redis connection failed**
```bash
# Check Redis status
sudo systemctl status redis-server

# Test connection
redis-cli ping

# Check Redis URL in .env
grep REDIS_URL /var/www/taskifai-demo/backend/.env
```

**C. Vendor detection failed**
```bash
# Test vendor detection manually
cd /var/www/taskifai-demo/backend
source venv/bin/activate
python << EOF
from app.services.vendors.detector import vendor_detector
vendor, confidence = vendor_detector.detect_vendor(
    "/path/to/upload.xlsx",
    "filename.xlsx"
)
print(f"Detected: {vendor} (confidence: {confidence})")
EOF
```

**D. Processor error**
```bash
# Test processor directly
cd /var/www/taskifai-demo/backend
source venv/bin/activate
python scripts/test_processor_integration.py /path/to/upload.xlsx
```

---

### Issue 3: Tenant Discovery Fails

**Symptoms:**
- User can't login from central portal
- Discovery returns 404 for existing user

**Diagnosis:**
```bash
# Check tenant registry data
# Query in Supabase SQL Editor:
SELECT t.subdomain, ut.email
FROM tenants t
JOIN user_tenants ut ON t.tenant_id = ut.tenant_id
WHERE ut.email = 'user@example.com';

# Test discovery endpoint
curl -X POST https://app.taskifai.com/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@demo.com"}' -v
```

**Solutions:**

**A. User not registered in tenant registry**
```sql
-- Register user in tenant registry
-- Get tenant_id
SELECT tenant_id FROM tenants WHERE subdomain = 'demo';

-- Insert user
INSERT INTO user_tenants (tenant_id, email)
VALUES ('tenant-id-here', 'admin@demo.com')
ON CONFLICT (tenant_id, email) DO NOTHING;
```

**B. Tenant not active**
```sql
-- Check tenant status
SELECT subdomain, is_active FROM tenants WHERE subdomain = 'demo';

-- Activate tenant
UPDATE tenants SET is_active = true WHERE subdomain = 'demo';
```

**C. Central login API can't reach registry**
```bash
# Check registry credentials in central login .env
cat /var/www/taskifai-central/backend/.env | grep SUPABASE

# Test connection
cd /var/www/taskifai-central/backend
source venv/bin/activate
python << EOF
from app.core.config import settings
from supabase import create_client

client = create_client(settings.supabase_url, settings.supabase_anon_key)
result = client.table("tenants").select("*").execute()
print(f"Found {len(result.data)} tenants")
EOF
```

---

### Issue 4: AI Chat Not Working

**Symptoms:**
- Chat returns errors
- No SQL generated
- Timeout errors

**Diagnosis:**
```bash
# Check OpenAI API key
grep OPENAI_API_KEY /var/www/taskifai-demo/backend/.env

# Test OpenAI connection
cd /var/www/taskifai-demo/backend
source venv/bin/activate
python << EOF
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say hello"}]
)
print(response.choices[0].message.content)
EOF
```

**Solutions:**

**A. Invalid OpenAI API key**
```bash
# Get new API key from https://platform.openai.com/api-keys
# Update .env
nano /var/www/taskifai-demo/backend/.env
# Update OPENAI_API_KEY=sk-...

# Restart API
sudo systemctl restart taskifai-demo-api
```

**B. Insufficient OpenAI credits**
- Check billing at: https://platform.openai.com/account/billing
- Add credits if balance is low

**C. Timeout errors**
```python
# Increase timeout in app/services/ai_chat/agent.py
# (if you've customized the agent)
```

---

### Issue 5: Data Not Appearing in Dashboard

**Symptoms:**
- Upload succeeds
- No data in analytics
- Empty charts

**Diagnosis:**
```bash
# Check if data was inserted
# Query in tenant's Supabase SQL Editor:
SELECT COUNT(*) FROM ecommerce_orders;
SELECT COUNT(*) FROM sellout_entries2;

# Check specific user's data
SELECT COUNT(*) FROM ecommerce_orders WHERE user_id = 'user-id-here';

# Check upload batch status
SELECT processing_status, rows_processed, error_summary
FROM upload_batches
WHERE uploader_user_id = 'user-id-here'
ORDER BY upload_timestamp DESC
LIMIT 5;
```

**Solutions:**

**A. Data in wrong table**
```sql
-- Check both tables
SELECT 'ecommerce_orders' as table_name, COUNT(*) as row_count
FROM ecommerce_orders WHERE user_id = 'user-id'
UNION ALL
SELECT 'sellout_entries2', COUNT(*)
FROM sellout_entries2 WHERE user_id = 'user-id';
```

**B. RLS blocking access**
```sql
-- Verify user_id matches
SELECT user_id FROM users WHERE email = 'admin@demo.com';

-- Check if data exists with that user_id
SELECT COUNT(*) FROM ecommerce_orders WHERE user_id = 'correct-user-id';
```

**C. Frontend filtering issue**
```bash
# Check browser console for API errors
# Test API directly
curl -H "Authorization: Bearer $TOKEN" \
  "https://demo.taskifai.com/api/analytics/summary"
```

---

## Monitoring & Alerts

### Setup Uptime Monitoring

**Using Uptime Robot (Free):**

1. Sign up at https://uptimerobot.com
2. Add monitors:
   - `https://app.taskifai.com` (HTTP, 5 min interval)
   - `https://demo.taskifai.com` (HTTP, 5 min interval)
   - `https://app.taskifai.com/api/health` (Keyword: "healthy")
3. Configure alerts (email/SMS)

**Using cURL + Cron (Self-hosted):**

```bash
# Create monitoring script
sudo tee /usr/local/bin/monitor-taskifai.sh << 'EOF'
#!/bin/bash

# Check central login
if ! curl -sf https://app.taskifai.com/api/health > /dev/null; then
    echo "ALERT: Central login down!" | mail -s "TaskifAI Alert" admin@taskifai.com
fi

# Check demo tenant
if ! curl -sf https://demo.taskifai.com/api/health > /dev/null; then
    echo "ALERT: Demo tenant down!" | mail -s "TaskifAI Alert" admin@taskifai.com
fi
EOF

sudo chmod +x /usr/local/bin/monitor-taskifai.sh

# Add to crontab (run every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor-taskifai.sh") | crontab -
```

### Setup Log Monitoring

```bash
# Create log rotation
sudo tee /etc/logrotate.d/taskifai << EOF
/var/www/taskifai-*/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
}
EOF

# Test log rotation
sudo logrotate -f /etc/logrotate.d/taskifai
```

### Performance Metrics

**Track these metrics:**

1. **API Response Time**
   ```bash
   curl -w "@-" -o /dev/null -s https://demo.taskifai.com/api/health << 'EOF'
   time_total: %{time_total}s
   EOF
   ```

2. **Upload Success Rate**
   ```sql
   SELECT
       DATE(upload_timestamp) as date,
       COUNT(*) as total_uploads,
       SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) as successful,
       ROUND(100.0 * SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
   FROM upload_batches
   WHERE upload_timestamp >= NOW() - INTERVAL '7 days'
   GROUP BY DATE(upload_timestamp)
   ORDER BY date DESC;
   ```

3. **Active Users**
   ```sql
   SELECT COUNT(DISTINCT user_id) as active_users_last_24h
   FROM conversation_history
   WHERE timestamp >= NOW() - INTERVAL '24 hours';
   ```

---

## Emergency Procedures

### Service Down

```bash
# 1. Identify which service is down
sudo systemctl status taskifai-demo-api
sudo systemctl status taskifai-demo-worker

# 2. Check logs for errors
sudo journalctl -u taskifai-demo-api -n 100 --no-pager

# 3. Restart service
sudo systemctl restart taskifai-demo-api

# 4. If restart fails, check dependencies
sudo systemctl status redis-server
sudo systemctl status nginx

# 5. Verify recovery
curl https://demo.taskifai.com/api/health
```

### Data Loss

```bash
# 1. Check Supabase backups
# Navigate to: Supabase Dashboard → Database → Backups
# Restore from latest backup if needed

# 2. Check local backups
ls -lh /backups/taskifai/

# 3. Restore uploads directory
tar -xzf /backups/taskifai/latest/uploads.tar.gz -C /var/www/taskifai-demo/
```

### Security Breach

```bash
# 1. Rotate all secrets immediately
# Generate new SECRET_KEY
openssl rand -hex 32

# Update .env on all servers
nano /var/www/taskifai-demo/backend/.env

# Restart services
sudo systemctl restart taskifai-demo-api

# 2. Revoke and regenerate API keys
# - OpenAI API key
# - SendGrid API key
# - Supabase service keys (if compromised)

# 3. Force logout all users
# (Invalidate all JWT tokens by changing SECRET_KEY)

# 4. Review access logs
sudo tail -f /var/log/nginx/access.log | grep -E '(POST|DELETE)'

# 5. Check for unauthorized uploads
SELECT * FROM upload_batches
WHERE upload_timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY upload_timestamp DESC;
```

---

## Quick Reference

### Essential Commands

```bash
# Service management
sudo systemctl restart taskifai-demo-api
sudo systemctl restart taskifai-demo-worker
sudo systemctl reload nginx

# Logs
sudo journalctl -u taskifai-demo-api -f
sudo journalctl -u taskifai-demo-worker -f
sudo tail -f /var/log/nginx/error.log

# Health checks
curl https://demo.taskifai.com/api/health
redis-cli ping
celery -A app.workers.celery_app inspect active

# Deployments
cd /var/www/taskifai-demo
git pull origin main
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
sudo systemctl restart taskifai-demo-api taskifai-demo-worker
sudo systemctl reload nginx
```

### Support Contacts

- Infrastructure Issues: devops@taskifai.com
- Application Issues: support@taskifai.com
- Security Issues: security@taskifai.com
- Emergency: [Phone number]

---

## Summary

You now have:

✅ **Infrastructure Deployment Guide** - Server setup, DNS, SSL
✅ **Customer Onboarding Guide** - BIBBI example walkthrough
✅ **Vendor Processor Guide** - Customization patterns
✅ **Deployment Checklist** - Step-by-step verification
✅ **Troubleshooting Guide** - Common issues & solutions

**Next Steps:**
1. Deploy central login server
2. Deploy demo tenant
3. Test complete user flow
4. Setup monitoring
5. Plan next customer onboarding (BIBBI)

**Good luck with your deployment! 🚀**
