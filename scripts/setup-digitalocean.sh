#!/bin/bash
# ============================================
# TaskifAI DigitalOcean Initial Setup Script
# Run this on your fresh DigitalOcean droplet
# ============================================

set -e

echo "🚀 TaskifAI DigitalOcean Setup"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}[1/8] Updating system...${NC}"
apt update && apt upgrade -y

echo -e "${GREEN}[2/8] Installing Docker...${NC}"
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

echo -e "${GREEN}[3/8] Installing Docker Compose...${NC}"
apt install docker-compose-plugin -y

echo -e "${GREEN}[4/8] Installing nginx and certbot...${NC}"
apt install nginx certbot python3-certbot-nginx git htop -y

echo -e "${GREEN}[5/8] Creating taskifai user...${NC}"
if ! id -u taskifai > /dev/null 2>&1; then
    adduser --gecos "" --disabled-password taskifai
    echo "taskifai:$(openssl rand -base64 32)" | chpasswd
fi

usermod -aG sudo taskifai
usermod -aG docker taskifai

echo -e "${GREEN}[6/8] Configuring firewall...${NC}"
ufw --force enable
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw allow 80/tcp
ufw allow 443/tcp

echo -e "${GREEN}[7/8] Setting up directories...${NC}"
mkdir -p /home/taskifai/apps
mkdir -p /home/taskifai/backups
chown -R taskifai:taskifai /home/taskifai

echo -e "${GREEN}[8/8] Installing security tools...${NC}"
apt install unattended-upgrades fail2ban -y
dpkg-reconfigure -plow unattended-upgrades
systemctl enable fail2ban
systemctl start fail2ban

# Generate SSH key for deployments
if [ ! -f /home/taskifai/.ssh/id_rsa ]; then
    su - taskifai -c "ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ''"
fi

echo ""
echo -e "${GREEN}✅ Initial setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Switch to taskifai user: su - taskifai"
echo "2. Clone repository: cd ~/apps && git clone YOUR_REPO"
echo "3. Configure .env file"
echo "4. Apply database migration"
echo "5. Run deployment script"
echo ""
echo -e "${YELLOW}SSH Key for Git:${NC}"
cat /home/taskifai/.ssh/id_rsa.pub
echo ""
