#!/bin/bash
# =============================================================================
# Secret Signal — Oracle Cloud Deployment Script
# Run this ON the Oracle Cloud ARM instance after SSH access
# =============================================================================
set -euo pipefail

echo "============================================"
echo "  Secret Signal — Oracle Cloud Deployment"
echo "============================================"

# ---------------------------------------------------------------------------
# 1. System update + Docker install
# ---------------------------------------------------------------------------
echo "[1/8] Updating system and installing Docker..."
sudo dnf update -y
sudo dnf install -y docker.io git

sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Docker Compose plugin
echo "[2/8] Installing Docker Compose..."
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-aarch64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

echo "Docker version: $(docker --version)"
echo "Compose version: $(docker compose version)"

# ---------------------------------------------------------------------------
# 3. Clone repo
# ---------------------------------------------------------------------------
echo "[3/8] Cloning repository..."
cd /home/opc
if [ -d "Secret-Signal" ]; then
  cd Secret-Signal && git pull
else
  git clone https://github.com/YOUR_USERNAME/Secret-Signal.git
  cd Secret-Signal
fi

# ---------------------------------------------------------------------------
# 4. Generate secrets
# ---------------------------------------------------------------------------
echo "[4/8] Generating secrets..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || openssl rand -base64 48)
POSTGRES_PASSWORD=$(openssl rand -base64 24)

echo "SECRET_KEY=$SECRET_KEY" > .env.production
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env.production
echo "POSTGRES_USER=postgres" >> .env.production
echo "POSTGRES_DB=secret_signal" >> .env.production
echo "DOMAIN=YOUR_DOMAIN_HERE" >> .env.production

echo ""
echo "  >> .env.production created. Edit it to set your DOMAIN."
echo ""

# ---------------------------------------------------------------------------
# 5. Build and start services
# ---------------------------------------------------------------------------
echo "[5/8] Building and starting services..."
docker compose -f docker-compose.prod.yml --env-file .env.production build
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

echo "Waiting for services to start..."
sleep 15

# ---------------------------------------------------------------------------
# 6. Run migrations
# ---------------------------------------------------------------------------
echo "[6/8] Running database migrations..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# ---------------------------------------------------------------------------
# 7. SSL setup (Let's Encrypt)
# ---------------------------------------------------------------------------
echo "[7/8] Setting up SSL..."
DOMAIN=$(grep DOMAIN .env.production | cut -d= -f2)

if [ "$DOMAIN" = "YOUR_DOMAIN_HERE" ]; then
  echo "  >> SKIPPED: Set DOMAIN in .env.production first, then re-run this script."
else
  # Install certbot
  sudo dnf install -y certbot

  # Get certificate (standalone mode — temporarily stop nginx)
  docker compose -f docker-compose.prod.yml stop nginx
  sudo certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"
  docker compose -f docker-compose.prod.yml start nginx

  # Auto-renew cron
  echo "0 0,12 * * * root certbot renew --quiet" | sudo tee /etc/cron.d/certbot-renew
fi

# ---------------------------------------------------------------------------
# 8. Verify
# ---------------------------------------------------------------------------
echo "[8/8] Verifying deployment..."
echo ""
echo "Backend health:"
curl -s http://localhost/health | python3 -m json.tool 2>/dev/null || echo "  >> Not ready yet"
echo ""
echo "Services:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "============================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================"
echo ""
echo "Backend:  https://YOUR_DOMAIN/api/v1/health/readiness"
echo "Health:   https://YOUR_DOMAIN/health"
echo ""
echo "To view logs:"
echo "  docker compose -f docker-compose.prod.yml logs -f backend"
echo ""
echo "To restart:"
echo "  docker compose -f docker-compose.prod.yml restart backend"
echo ""
