#!/bin/bash
# VPS Deployment Script untuk WA Bot Reminder
# Run this after SSH ke VPS: bash deploy.sh

set -e

echo "🚀 Starting WA Bot Reminder deployment..."

# 1. Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# 3. Install Docker Compose
echo "🐳 Installing Docker Compose..."
sudo apt install -y docker-compose

# 4. Add user to docker group
echo "👤 Adding user to docker group..."
sudo usermod -aG docker $USER
newgrp docker

# 5. Clone project
echo "📥 Cloning project repository..."
cd /home/$(whoami)
git clone https://github.com/YOUR_USERNAME/wa-bot-reminder.git
cd wa-bot-reminder

# 6. Copy deployment .env
echo "⚙️  Setting up environment variables..."
cp .env.deploy .env

# 7. Create directories
mkdir -p sessions media

# 8. Start Docker services
echo "🚀 Starting Docker services..."
docker-compose up -d

# 9. Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# 10. Show status
echo "✅ Deployment complete!"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🌐 Access points:"
echo "  - WAHA Dashboard: http://YOUR_VPS_IP:3000"
echo "  - AI Agent API: http://YOUR_VPS_IP:8001"
echo "  - API Health: http://YOUR_VPS_IP:8001/health"
echo ""
echo "📝 Next steps:"
echo "  1. Change YOUR_USERNAME in WAHA_DASHBOARD_USERNAME"
echo "  2. Open WAHA Dashboard and scan QR code for WhatsApp"
echo "  3. Update webhook in WAHA to: http://YOUR_VPS_IP:8001/webhook"
echo "  4. Send /help to bot to test!"
echo ""
echo "📋 Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Restart: docker-compose restart"
echo "  - Stop: docker-compose down"

