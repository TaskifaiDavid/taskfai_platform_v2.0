# TaskifAI Platform - Infrastructure Deployment Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Server Requirements](#server-requirements)
3. [Domain & DNS Configuration](#domain--dns-configuration)
4. [Server Setup by Component](#server-setup-by-component)
5. [Environment Configuration](#environment-configuration)
6. [Deployment Steps](#deployment-steps)
7. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Architecture Overview

### Multi-Tenant Architecture

TaskifAI uses a **centralized login + isolated tenant architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                  app.taskifai.com                           │
│         (Central Login & Routing Server)                    │
│  - Tenant discovery                                         │
│  - Authentication initiation                                │
│  - Tenant routing                                           │
└─────────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ demo.        │ │ bibbi.       │ │ customer3.   │
│ taskifai.com │ │ taskifai.com │ │ taskifai.com │
│              │ │              │ │              │
│ Tenant App   │ │ Tenant App   │ │ Tenant App   │
│ Instance     │ │ Instance     │ │ Instance     │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Supabase     │ │ Supabase     │ │ Supabase     │
│ Project #1   │ │ Project #2   │ │ Project #3   │
│ (demo data)  │ │ (bibbi data) │ │ (cust3 data) │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Key Infrastructure Components

1. **Central Login Server** (`app.taskifai.com`)
   - Frontend: Static React app
   - Backend API: FastAPI for tenant discovery
   - Database: Tenant registry (Supabase)

2. **Tenant Application Servers** (`{subdomain}.taskifai.com`)
   - Frontend: React app
   - Backend API: FastAPI with full features
   - Worker: Celery for background tasks
   - Redis: Task queue & caching
   - Database: Isolated Supabase project per tenant

---

## Server Requirements

### Option A: Dedicated Servers (Recommended for Production)

| Component | Server Type | Specs | Quantity |
|-----------|-------------|-------|----------|
| **Central Login** | Small VPS | 1 vCPU, 1GB RAM | 1 |
| **Tenant App** | Medium VPS | 2 vCPU, 4GB RAM | 1 per tenant |
| **Redis** | Small VPS | 1 vCPU, 1GB RAM | 1 per tenant |
| **Database** | Supabase (managed) | Varies | 1 per tenant + 1 registry |

### Option B: Single Server (Development/Small Scale)

| Component | Server Type | Specs | Quantity |
|-----------|-------------|-------|----------|
| **All-in-One** | Large VPS | 4 vCPU, 8GB RAM | 1 |
| **Database** | Supabase (managed) | Varies | 2 (registry + demo) |

### Option C: Cloud Orchestration (Scalable)

| Component | Service Type | Provider Options |
|-----------|--------------|------------------|
| **Frontend** | Static Hosting | Vercel / Netlify / Cloudflare Pages |
| **Backend API** | Container Service | AWS ECS / Google Cloud Run / DigitalOcean App Platform |
| **Worker** | Container Service | Same as backend |
| **Redis** | Managed Redis | Upstash / Redis Cloud / AWS ElastiCache |
| **Database** | Supabase (managed) | Supabase Cloud |

---

## Domain & DNS Configuration

### DNS Records Required

```dns
# Central Login Portal
app.taskifai.com          A       <central-login-server-ip>
app.taskifai.com          AAAA    <ipv6-optional>

# Wildcard for Tenant Subdomains
*.taskifai.com            A       <tenant-server-ip>
*.taskifai.com            AAAA    <ipv6-optional>

# Or individual tenant subdomains
demo.taskifai.com         A       <demo-tenant-server-ip>
bibbi.taskifai.com        A       <bibbi-tenant-server-ip>
```

### SSL/TLS Certificates

**Option 1: Wildcard Certificate (Recommended)**
```bash
# Using Let's Encrypt with Certbot
certbot certonly --dns-cloudflare \
  -d taskifai.com -d *.taskifai.com \
  --email admin@taskifai.com
```

**Option 2: Individual Certificates**
```bash
# Central login
certbot certonly --nginx -d app.taskifai.com

# Each tenant
certbot certonly --nginx -d demo.taskifai.com
certbot certonly --nginx -d bibbi.taskifai.com
```

---

## Server Setup by Component

### 1. Central Login Server (`app.taskifai.com`)

#### Purpose
- Handles tenant discovery
- Initial authentication
- Routes users to correct tenant subdomain
- Does NOT store customer data

#### Server Setup (Ubuntu 22.04 LTS)

```bash
# 1. Initial server setup
apt update && apt upgrade -y
apt install -y nginx certbot python3-certbot-nginx nodejs npm git

# 2. Create application directory
mkdir -p /var/www/taskifai-central
cd /var/www/taskifai-central

# 3. Clone repository
git clone https://github.com/yourusername/taskifai-platform.git .

# 4. Setup frontend (central login portal)
cd frontend
npm install
npm run build

# Frontend build output will be in frontend/dist

# 5. Setup backend API (tenant discovery only)
cd ../backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Configure environment variables
cat > .env << EOF
APP_NAME="TaskifAI Central Login"
DEBUG=false

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Tenant Registry Database (Supabase)
SUPABASE_URL=https://your-registry-project.supabase.co
SUPABASE_ANON_KEY=your-registry-anon-key
SUPABASE_SERVICE_KEY=your-registry-service-key

# Redis (shared or local)
REDIS_URL=redis://localhost:6379/0

# CORS - Allow all tenant subdomains
ALLOWED_ORIGINS=https://demo.taskifai.com,https://bibbi.taskifai.com,https://*.taskifai.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
EOF

# 7. Setup systemd service for backend
cat > /etc/systemd/system/taskifai-central-api.service << EOF
[Unit]
Description=TaskifAI Central Login API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/taskifai-central/backend
Environment="PATH=/var/www/taskifai-central/backend/venv/bin"
ExecStart=/var/www/taskifai-central/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable taskifai-central-api
systemctl start taskifai-central-api

# 8. Configure Nginx
cat > /etc/nginx/sites-available/app.taskifai.com << 'EOF'
server {
    listen 80;
    server_name app.taskifai.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.taskifai.com;

    # SSL Configuration
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

ln -s /etc/nginx/sites-available/app.taskifai.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 9. Setup SSL
certbot --nginx -d app.taskifai.com --non-interactive --agree-tos -m admin@taskifai.com

# 10. Setup firewall
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
ufw enable
```

---

### 2. Tenant Application Server (e.g., `demo.taskifai.com`)

#### Purpose
- Full application functionality
- File processing
- Analytics
- AI chat
- Data storage (isolated per tenant)

#### Server Setup (Ubuntu 22.04 LTS)

```bash
# 1. Initial server setup
apt update && apt upgrade -y
apt install -y nginx certbot python3-certbot-nginx nodejs npm git redis-server

# 2. Create application directory
mkdir -p /var/www/taskifai-demo
cd /var/www/taskifai-demo

# 3. Clone repository
git clone https://github.com/yourusername/taskifai-platform.git .

# 4. Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure environment variables
cat > .env << EOF
APP_NAME="TaskifAI Analytics Platform - Demo"
DEBUG=false

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Supabase (Demo tenant database)
SUPABASE_URL=https://demo-tenant-project.supabase.co
SUPABASE_ANON_KEY=demo-tenant-anon-key
SUPABASE_SERVICE_KEY=demo-tenant-service-key

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

# 6. Create uploads directory
mkdir -p /var/www/taskifai-demo/uploads
chown www-data:www-data /var/www/taskifai-demo/uploads

# 7. Setup backend API service
cat > /etc/systemd/system/taskifai-demo-api.service << EOF
[Unit]
Description=TaskifAI Demo API
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/taskifai-demo/backend
Environment="PATH=/var/www/taskifai-demo/backend/venv/bin"
ExecStart=/var/www/taskifai-demo/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 8. Setup Celery worker service
cat > /etc/systemd/system/taskifai-demo-worker.service << EOF
[Unit]
Description=TaskifAI Demo Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/taskifai-demo/backend
Environment="PATH=/var/www/taskifai-demo/backend/venv/bin"
ExecStart=/var/www/taskifai-demo/backend/venv/bin/celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable taskifai-demo-api taskifai-demo-worker
systemctl start taskifai-demo-api taskifai-demo-worker

# 9. Setup frontend
cd ../frontend
npm install

# Configure environment
cat > .env << EOF
VITE_API_URL=https://demo.taskifai.com/api
VITE_ENVIRONMENT=production
EOF

npm run build

# 10. Configure Nginx
cat > /etc/nginx/sites-available/demo.taskifai.com << 'EOF'
server {
    listen 80;
    server_name demo.taskifai.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name demo.taskifai.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/demo.taskifai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/demo.taskifai.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend (React SPA)
    location / {
        root /var/www/taskifai-demo/frontend/dist;
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

        # File upload support
        client_max_body_size 100M;

        # Timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

ln -s /etc/nginx/sites-available/demo.taskifai.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 11. Setup SSL
certbot --nginx -d demo.taskifai.com --non-interactive --agree-tos -m admin@taskifai.com

# 12. Setup firewall
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
ufw enable
```

---

## Environment Configuration

### Tenant Registry Database (Supabase)

Create a **dedicated Supabase project** for the tenant registry:

```sql
-- Create tenant registry tables
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

-- Insert demo tenant
INSERT INTO tenants (subdomain, display_name, database_url, database_anon_key)
VALUES (
    'demo',
    'Demo Account',
    'https://demo-tenant-project.supabase.co',
    'demo-tenant-anon-key-here'
);
```

### Per-Tenant Database (Supabase)

Each tenant gets a **dedicated Supabase project**. Run the schema:

```bash
# Copy schema to Supabase SQL Editor
cat backend/db/schema.sql | pbcopy  # or xclip on Linux

# Then execute in Supabase SQL Editor:
# 1. Navigate to project > SQL Editor
# 2. Paste schema
# 3. Run
```

---

## Deployment Steps

### Step-by-Step Deployment Checklist

#### Phase 1: Central Login Server

- [ ] Provision server (VPS or cloud)
- [ ] Configure DNS: `app.taskifai.com` → server IP
- [ ] Setup SSL certificate
- [ ] Create tenant registry Supabase project
- [ ] Run tenant registry schema
- [ ] Deploy central login backend
- [ ] Deploy central login frontend
- [ ] Test tenant discovery endpoint
- [ ] Verify rate limiting

#### Phase 2: Demo Tenant (First Tenant)

- [ ] Provision server (or use same server)
- [ ] Configure DNS: `demo.taskifai.com` → server IP
- [ ] Setup SSL certificate
- [ ] Create demo tenant Supabase project
- [ ] Run application schema in demo project
- [ ] Register demo tenant in registry
- [ ] Deploy demo backend API
- [ ] Deploy demo Celery worker
- [ ] Deploy demo frontend
- [ ] Test full user flow (login → upload → analytics)

#### Phase 3: Additional Tenants (BIBBI, etc.)

- [ ] Repeat Phase 2 for each new tenant
- [ ] Update tenant registry with new entry
- [ ] Configure tenant-specific vendor processors
- [ ] Migrate/import customer data if needed

---

## Monitoring & Maintenance

### Health Checks

```bash
# Central Login API
curl https://app.taskifai.com/api/health

# Tenant API
curl https://demo.taskifai.com/api/health

# Redis
redis-cli ping

# Celery Worker
celery -A app.workers.celery_app inspect active
```

### Log Locations

```bash
# API logs
journalctl -u taskifai-demo-api -f

# Worker logs
journalctl -u taskifai-demo-worker -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Redis logs
tail -f /var/log/redis/redis-server.log
```

### Backup Strategy

1. **Database**: Supabase automatic backups (daily)
2. **Uploads**: Backup `/var/www/taskifai-{tenant}/uploads` daily
3. **Configuration**: Version control `.env` files (encrypted)

```bash
# Daily backup script
cat > /usr/local/bin/backup-taskifai.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backups/taskifai/$(date +%Y-%m-%d)
mkdir -p $BACKUP_DIR

# Backup uploads
tar -czf $BACKUP_DIR/uploads.tar.gz /var/www/taskifai-demo/uploads

# Backup configs (encrypted)
tar -czf - /var/www/taskifai-demo/backend/.env | \
  openssl enc -aes-256-cbc -salt -out $BACKUP_DIR/config.tar.gz.enc

# Cleanup old backups (keep 30 days)
find /backups/taskifai -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-taskifai.sh

# Add to crontab
echo "0 2 * * * /usr/local/bin/backup-taskifai.sh" | crontab -
```

### Update Procedure

```bash
# 1. Backup current state
/usr/local/bin/backup-taskifai.sh

# 2. Pull latest code
cd /var/www/taskifai-demo
git pull origin main

# 3. Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
systemctl restart taskifai-demo-api taskifai-demo-worker

# 4. Update frontend
cd ../frontend
npm install
npm run build

# 5. Reload Nginx
systemctl reload nginx

# 6. Verify health
curl https://demo.taskifai.com/api/health
```

---

## Security Checklist

- [ ] SSL/TLS enabled for all domains
- [ ] Firewall configured (only 22, 80, 443 open)
- [ ] Environment variables secured (not in git)
- [ ] Rate limiting enabled on auth endpoints
- [ ] CORS properly configured
- [ ] Supabase RLS policies active
- [ ] Regular security updates (`apt update && apt upgrade`)
- [ ] Log monitoring enabled
- [ ] Backup strategy implemented

---

## Cost Estimation (Monthly)

### Small Setup (1-3 tenants)

| Component | Provider | Cost |
|-----------|----------|------|
| Central Login VPS | DigitalOcean | $6 |
| Tenant VPS x2 | DigitalOcean | $24 |
| Supabase (3 projects) | Supabase | $75 |
| Redis Cloud | Upstash | $10 |
| Domain | Namecheap | $1 |
| **Total** | | **~$116/mo** |

### Medium Setup (5-10 tenants)

| Component | Provider | Cost |
|-----------|----------|------|
| Load Balancer | DigitalOcean | $12 |
| Tenant VPS x5 | DigitalOcean | $60 |
| Supabase (6 projects) | Supabase | $150 |
| Redis Cloud | Upstash | $20 |
| **Total** | | **~$242/mo** |

### Large Setup (10+ tenants)

Use cloud orchestration (ECS, Cloud Run) with auto-scaling for cost optimization.

---

## Next Steps

1. Review [Customer Onboarding Guide](./02_Customer_Onboarding_BIBBI_Example.md)
2. Read [Vendor Processor Customization Guide](./03_Vendor_Processor_Customization.md)
3. Check [Deployment Checklist](./04_Deployment_Checklist.md)
