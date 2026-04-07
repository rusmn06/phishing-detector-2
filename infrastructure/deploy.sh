#!/bin/bash
# ===========================================
# Deployment Script untuk Azure Ubuntu 24
# ===========================================

set -e  # Exit on error

echo "🚀 Starting deployment for Email Phishing Scanner..."

# Config
PROJECT_DIR="/opt/phishing-detector"
BACKUP_DIR="/opt/backups/phishing-detector-$(date +%Y%m%d-%H%M%S)"

# 1. Pull latest code (jika pakai git)
echo "📦 Pulling latest code..."
cd $PROJECT_DIR
git pull origin main

# 2. Backup current deployment (opsional tapi direkomendasikan)
echo "💾 Creating backup..."
mkdir -p $BACKUP_DIR
docker-compose ps -q | xargs -r docker inspect --format='{{.Config.Image}}' > $BACKUP_DIR/images.txt
docker-compose down --volumes 2>/dev/null || true

# 3. Pull/update .env.production (manual step - jangan automate secrets!)
echo "🔐 Pastikan file .env.production sudah terisi dengan benar!"
echo "   Location: $PROJECT_DIR/infrastructure/.env.production"
read -p "Tekan Enter setelah .env.production siap..."

# 4. Build dan start containers
echo "🔨 Building Docker images..."
docker-compose build --no-cache

echo "🏗️ Starting services..."
docker-compose up -d

# 5. Wait for health checks
echo "⏳ Waiting for services to be healthy..."
sleep 30

# 6. Verify deployment
echo "🔍 Verifying deployment..."
if curl -f http://localhost/api/v1/health > /dev/null 2>&1; then
    echo "✅ Backend healthy"
else
    echo "❌ Backend health check failed!"
    docker-compose logs backend --tail=50
    exit 1
fi

if curl -f http://localhost/ > /dev/null 2>&1; then
    echo "✅ Frontend healthy"
else
    echo "❌ Frontend health check failed!"
    docker-compose logs frontend --tail=50
    exit 1
fi

# 7. Setup log rotation (jika belum)
echo "📋 Setting up log rotation..."
if [ ! -f /etc/logrotate.d/phishing-detector ]; then
    cat > /etc/logrotate.d/phishing-detector << 'EOF'
/opt/phishing-detector/infrastructure/logs/nginx/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 nginx nginx
}
EOF
fi

echo "🎉 Deployment completed successfully!"
echo "🌐 Akses aplikasi di: https://<your-azure-ip-or-domain>"
echo "📊 Monitor logs: docker-compose logs -f"
echo "🔄 Update: jalankan script ini lagi setelah git pull"