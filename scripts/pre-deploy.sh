#!/bin/bash
# =============================================================================
# Secret Signal — Local Pre-deploy Script
# Run this locally to prepare for Oracle Cloud deployment
# =============================================================================
set -euo pipefail

echo "============================================"
echo "  Secret Signal — Pre-deploy Setup"
echo "============================================"

# ---------------------------------------------------------------------------
# 1. Check prerequisites
# ---------------------------------------------------------------------------
echo "[1/3] Checking prerequisites..."

if ! command -v git &> /dev/null; then
  echo "ERROR: git not found. Install git first."
  exit 1
fi

if ! command -v docker &> /dev/null; then
  echo "WARNING: Docker not found locally. You'll need Docker on the Oracle Cloud instance."
fi

# ---------------------------------------------------------------------------
# 2. Build and test Docker image locally (optional)
# ---------------------------------------------------------------------------
echo "[2/3] Building backend Docker image..."
docker build -f infrastructure/docker/Dockerfile.backend -t secret-signal-backend:latest .

echo "Backend image built successfully."

# ---------------------------------------------------------------------------
# 3. Git push
# ---------------------------------------------------------------------------
echo "[3/3] Pushing to GitHub..."
if git status --porcelain | grep -q .; then
  echo "You have uncommitted changes. Please commit first:"
  echo "  git add ."
  echo "  git commit -m 'Production deployment prep'"
  echo "  git push"
else
  echo "All changes committed. Pushing..."
  git push origin main
fi

echo ""
echo "============================================"
echo "  NEXT STEPS"
echo "============================================"
echo ""
echo "1. Create Oracle Cloud account: https://cloud.oracle.com"
echo "2. Create Always Free ARM instance (4 OCPU, 24GB RAM)"
echo "3. Open port 80 and 443 in security list"
echo "4. SSH into instance and run:"
echo ""
echo "   sudo dnf update -y && sudo dnf install -y docker.io git"
echo "   sudo systemctl enable docker && sudo systemctl start docker"
echo "   git clone https://github.com/YOUR_USERNAME/Secret-Signal.git"
echo "   cd Secret-Signal"
echo "   bash scripts/deploy-oracle.sh"
echo ""
echo "5. Point your domain DNS to the instance public IP"
echo "6. Edit .env.production on the instance with your domain"
echo "7. Re-run deploy script for SSL"
echo ""
