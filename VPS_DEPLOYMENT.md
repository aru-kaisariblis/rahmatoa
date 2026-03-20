# VPS Deployment Guide - Azure VM

## Prerequisites
- Azure VM with Linux (Ubuntu 20.04+)
- SSH key access ke VM
- Git installed

## Step 1: Reset SSH Key di Azure Portal

1. Open https://portal.azure.com
2. Find VM: `aru-kaisariblis`
3. Left sidebar → **"Operations"** → **"Reset password"** atau **"Reset SSH public key"**
4. Select: **"Reset SSH public key"**
5. Username: `aru-rajaiblis`
6. Select: **"Generate new key pair"**
7. Click **"Reset"**
8. Download file `.pem` yang baru

## Step 2: Setup SSH Key Locally

```bash
# Move key ke .ssh folder
mv ~/Downloads/aru-rajaiblis.pem ~/.ssh/
chmod 600 ~/.ssh/aru-rajaiblis.pem

# Test SSH connection
ssh -i ~/.ssh/aru-rajaiblis.pem aru-rajaiblis@20.249.210.165

# Jika berhasil, kamu akan di shell VM
```

## Step 3: Deploy Bot ke VPS

```bash
# Dari VM SSH session:

# Download deployment script
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/wa-bot-reminder/main/deploy.sh
chmod +x deploy.sh

# Run deployment (takes 5-10 minutes)
./deploy.sh

# Wait for completion...
```

Or manual setup:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install -y docker-compose

# Clone project
git clone https://github.com/YOUR_USERNAME/wa-bot-reminder.git
cd wa-bot-reminder

# Setup .env
cp .env.deploy .env

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

## Step 4: Get Your VPS IP & Configure WAHA

```bash
# From VM:
hostname -I
# Get result like: 20.249.210.165
```

1. WAHA Dashboard: `http://20.249.210.165:3000`
2. Login dengan credentials dari `.env`
3. Sessions → default → Scan QR code
4. Webhooks → Edit URL ke: `http://20.249.210.165:8001/webhook`

## Step 5: Test Bot

Send message to WhatsApp:
```
/help
```

Bot should respond with help message!

## Troubleshooting

### Services tidak start
```bash
docker-compose logs -f
```

### Firewall/Port blocked
```bash
# Check if ports open
sudo netstat -tlnp | grep 3000
sudo netstat -tlnp | grep 8001

# Allow ports
sudo ufw allow 3000/tcp
sudo ufw allow 8001/tcp
```

### Database issue
```bash
# Recreate database
docker-compose exec bot rm /tmp/tasks.db
docker-compose restart bot
```

## SSH Shortcut (Optional)

Add to `~/.ssh/config`:
```
Host wa-bot-vps
    HostName 20.249.210.165
    User aru-rajaiblis
    IdentityFile ~/.ssh/aru-rajaiblis.pem
```

Then connect with:
```bash
ssh wa-bot-vps
```

## Useful Commands

```bash
# SSH ke VPS
ssh -i ~/.ssh/aru-rajaiblis.pem aru-rajaiblis@20.249.210.165

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# View running containers
docker-compose ps

# Execute command di container
docker-compose exec bot python -m pytest

# Update code (pull latest)
git pull
docker-compose restart
```

## Cost Optimization

- Use Azure Spot Instances (70% cheaper)
- Set auto-shutdown di non-working hours
- Monitor resource usage via Azure Monitor

Done! 🎉
