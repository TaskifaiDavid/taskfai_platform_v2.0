# TaskifAI DigitalOcean Deployment Guide

## 🎯 Recommended DigitalOcean Setup

### Infrastructure Components

**Option A: Simple Setup (Single Droplet + Managed Services)**
- 1x Droplet (4GB RAM, 2 vCPU) - $24/month
- Managed PostgreSQL Database - $15/month (basic plan)
- Managed Redis - $15/month (basic plan)
- Load Balancer (optional) - $12/month
- **Total: ~$54-66/month**

**Option B: Cost-Optimized (All-in-One Droplet)**
- 1x Droplet (8GB RAM, 4 vCPU) - $48/month
- Docker Compose with PostgreSQL + Redis containers
- **Total: $48/month**

**Recommended: Option A** (better scalability and reliability)

---

## 📋 Step-by-Step Deployment

### 1. Create Droplet

```bash
# Recommended specs:
# - Ubuntu 24.04 LTS
# - 4GB RAM / 2 vCPUs minimum
# - Enable monitoring
# - Add SSH keys
# - Enable backups (optional, +20% cost)
```

**In DigitalOcean Dashboard:**
1. Create Droplets → New Droplet
2. Choose: Ubuntu 24.04 LTS
3. Plan: Basic ($24/mo - 4GB/2vCPU)
4. Datacenter: Choose closest to users
5. Authentication: SSH keys (upload yours)
6. Hostname: `taskifai-production`
7. Enable: Monitoring, IPv6
8. Create Droplet

### 2. Create Managed Databases

**PostgreSQL Database:**
1. Databases → Create Database Cluster
2. Engine: PostgreSQL 17
3. Plan: Basic ($15/mo)
4. Datacenter: Same as droplet
5. Database name: `taskifai`
6. Create cluster
7. **Save connection string** for later

**Redis Database:**
1. Databases → Create Database Cluster
2. Engine: Redis 7
3. Plan: Basic ($15/mo)
4. Datacenter: Same as droplet
5. Create cluster
6. **Save connection string** for later

### 3. Initial Server Setup

SSH into your droplet:

```bash
# SSH into droplet
ssh root@your_droplet_ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Create non-root user
adduser taskifai
usermod -aG sudo taskifai
usermod -aG docker taskifai

# Setup firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Switch to taskifai user
su - taskifai
```

### 4. Install Dependencies

```bash
# Install nginx for reverse proxy
sudo apt install nginx certbot python3-certbot-nginx -y

# Install git
sudo apt install git -y

# Verify installations
docker --version
docker compose version
nginx -v
```

### 5. Clone and Configure Application

```bash
# Create app directory
mkdir -p ~/apps
cd ~/apps

# Clone repository (replace with your repo)
git clone https://github.com/yourusername/TaskifAI_platform_v2.0.git
cd TaskifAI_platform_v2.0

# Create environment file
cp .env.example .env
nano .env
```

**Configure `.env` with DigitalOcean resources:**

```bash
# ============================================
# DATABASE (DigitalOcean Managed PostgreSQL)
# ============================================
DATABASE_URL=postgresql://doadmin:password@db-postgresql-nyc1-12345.db.ondigitalocean.com:25060/taskifai?sslmode=require

# ============================================
# REDIS (DigitalOcean Managed Redis)
# ============================================
REDIS_URL=rediss://default:password@redis-nyc1-12345.db.ondigitalocean.com:25061

# ============================================
# SECURITY
# ============================================
SECRET_KEY=<generate with: openssl rand -hex 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============================================
# ENVIRONMENT
# ============================================
ENVIRONMENT=production
DEBUG=false

# ============================================
# CORS (Your domain)
# ============================================
CORS_ORIGINS=["https://app.taskifai.com", "https://taskifai.com"]

# ============================================
# SUPABASE (if using for auth)
# ============================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# ============================================
# SENDGRID
# ============================================
SENDGRID_API_KEY=SG.xxx
SENDGRID_FROM_EMAIL=noreply@taskifai.com

# ============================================
# OPENAI
# ============================================
OPENAI_API_KEY=sk-xxx

# ============================================
# FRONTEND
# ============================================
VITE_API_URL=https://api.taskifai.com
VITE_ENVIRONMENT=production
```

### 6. Apply Database Migration

```bash
# Get database connection string from DigitalOcean dashboard
# Copy it from: Databases → Your Cluster → Connection Details

# Apply migration
psql "postgresql://doadmin:password@db-host:25060/taskifai?sslmode=require" \
  -f backend/db/migrations/001_multi_tenant_enhancements.sql
```

### 7. Create Production Docker Compose

Create `docker-compose.prod.yml`:

```bash
cat > docker-compose.prod.yml << 'EOF'
version: '3.9'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: taskifai-backend
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - backend_uploads:/app/uploads
      - backend_logs:/app/logs
    networks:
      - taskifai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: taskifai-worker
    restart: unless-stopped
    env_file:
      - .env
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
    volumes:
      - backend_uploads:/app/uploads
      - backend_logs:/app/logs
    networks:
      - taskifai-network
    depends_on:
      backend:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: taskifai-frontend
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:80"
    networks:
      - taskifai-network
    depends_on:
      - backend

volumes:
  backend_uploads:
    driver: local
  backend_logs:
    driver: local

networks:
  taskifai-network:
    driver: bridge
EOF
```

### 8. Configure Nginx Reverse Proxy

```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/taskifai
```

**Nginx Configuration:**

```nginx
# Backend API
server {
    listen 80;
    server_name api.taskifai.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout settings for file uploads
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}

# Frontend Application
server {
    listen 80;
    server_name app.taskifai.com taskifai.com www.taskifai.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Enable site:**

```bash
# Enable configuration
sudo ln -s /etc/nginx/sites-available/taskifai /etc/nginx/sites-enabled/

# Remove default
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 9. Setup SSL with Let's Encrypt

```bash
# Get SSL certificates (replace with your domains)
sudo certbot --nginx -d api.taskifai.com -d app.taskifai.com -d taskifai.com -d www.taskifai.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 10. Deploy Application

```bash
# Build and start containers
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check status
docker compose -f docker-compose.prod.yml ps
```

### 11. Setup Monitoring

```bash
# Install monitoring tools
sudo apt install htop netdata -y

# Enable DigitalOcean monitoring agent (already installed)
sudo systemctl enable do-agent
sudo systemctl start do-agent
```

---

## 🔄 Deployment Script for DigitalOcean

Create `scripts/deploy-digitalocean.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 TaskifAI DigitalOcean Deployment"

# Pull latest changes
git pull origin main

# Build containers
docker compose -f docker-compose.prod.yml build --no-cache

# Stop old containers
docker compose -f docker-compose.prod.yml down

# Start new containers
docker compose -f docker-compose.prod.yml up -d

# Wait for health check
sleep 10

# Verify backend health
curl -f http://localhost:8000/api/health || exit 1

# Cleanup old images
docker image prune -f

echo "✅ Deployment complete!"
```

Make executable:
```bash
chmod +x scripts/deploy-digitalocean.sh
```

---

## 🔧 DNS Configuration

In your DNS provider (Cloudflare, Namecheap, etc.):

```
Type    Name    Value                   TTL
A       @       your_droplet_ip         3600
A       api     your_droplet_ip         3600
A       app     your_droplet_ip         3600
CNAME   www     @                       3600
```

---

## 📊 Post-Deployment Checks

```bash
# 1. Check backend health
curl https://api.taskifai.com/api/health

# 2. Check frontend
curl https://app.taskifai.com

# 3. View backend logs
docker compose -f docker-compose.prod.yml logs backend

# 4. Check container status
docker compose -f docker-compose.prod.yml ps

# 5. Test database connection
docker compose -f docker-compose.prod.yml exec backend python -c "from app.db import get_db; next(get_db())"
```

---

## 🛡️ Security Hardening

```bash
# 1. Setup automatic security updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades

# 2. Configure fail2ban for SSH protection
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 3. Disable root SSH login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd

# 4. Setup logrotate for application logs
sudo nano /etc/logrotate.d/taskifai
```

Add to logrotate config:
```
/home/taskifai/apps/TaskifAI_platform_v2.0/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 taskifai taskifai
    sharedscripts
}
```

---

## 💾 Backup Strategy

### Database Backups (Automatic with DigitalOcean)
- Managed PostgreSQL: Daily automated backups
- Retention: 7 days (basic plan)
- Point-in-time recovery available

### Application Backups

```bash
# Create backup script
cat > ~/backup-taskifai.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/taskifai/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz \
  /var/lib/docker/volumes/taskifai_platform_v20_backend_uploads

# Backup environment
cp /home/taskifai/apps/TaskifAI_platform_v2.0/.env \
  $BACKUP_DIR/env_$DATE.backup

# Keep only last 7 days
find $BACKUP_DIR -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x ~/backup-taskifai.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/taskifai/backup-taskifai.sh
```

---

## 🚨 Troubleshooting

### Container won't start
```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml restart backend
```

### Database connection issues
```bash
# Test from droplet
psql "your_database_url" -c "SELECT version();"

# Check allowed IPs in DigitalOcean dashboard
# Databases → Your Cluster → Settings → Trusted Sources
```

### High memory usage
```bash
# Check resource usage
docker stats

# Restart worker with fewer concurrent tasks
# In docker-compose.prod.yml: --concurrency=1
```

### SSL certificate issues
```bash
sudo certbot renew --force-renewal
sudo systemctl restart nginx
```

---

## 📈 Scaling Options

**Horizontal Scaling:**
1. Add Load Balancer ($12/mo)
2. Deploy multiple droplets
3. Update nginx upstream config

**Vertical Scaling:**
1. Resize droplet (DigitalOcean dashboard)
2. Takes ~1 minute downtime
3. No data loss

**Database Scaling:**
1. Upgrade managed database plan
2. Add read replicas ($15/mo each)
3. Zero downtime

---

## 💰 Cost Breakdown

**Minimal Production Setup:**
- Droplet (4GB): $24/mo
- PostgreSQL: $15/mo
- Redis: $15/mo
- Domain: $12/yr
- **Total: ~$54/mo**

**Recommended Production Setup:**
- Droplet (8GB): $48/mo
- PostgreSQL (managed): $15/mo
- Redis (managed): $15/mo
- Load Balancer: $12/mo
- Backups: $10/mo
- Domain: $12/yr
- **Total: ~$100/mo**

---

## ✅ Quick Start Checklist

- [ ] Create DigitalOcean droplet (Ubuntu 24.04, 4GB RAM)
- [ ] Create managed PostgreSQL database
- [ ] Create managed Redis database
- [ ] SSH into droplet and install Docker
- [ ] Clone repository
- [ ] Configure `.env` with DigitalOcean connection strings
- [ ] Apply database migration
- [ ] Configure nginx reverse proxy
- [ ] Setup SSL with certbot
- [ ] Deploy with `docker-compose.prod.yml`
- [ ] Configure DNS records
- [ ] Test application
- [ ] Setup monitoring and backups
