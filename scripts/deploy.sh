#!/usr/bin/env bash
# Manual deployment script for MovieRecommender to EC2
# Usage: ./scripts/deploy.sh

set -euo pipefail

# Configuration
EC2_HOST="ec2-13-59-13-187.us-east-2.compute.amazonaws.com"
EC2_USER="ec2-user"
# Must match systemd WorkingDirectory on EC2
DEPLOY_DIR="/home/ec2-user/movierec/movierec"
# Uvicorn listens on 8000 behind Nginx; public health check is on port 80
BACKEND_PORT="8000"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/movie-recommender-ec2.pem}"

echo "🚀 Starting deployment to EC2..."

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
  echo "❌ SSH key not found at: $SSH_KEY"
  echo "Set SSH_KEY environment variable or place key at default location"
  exit 1
fi

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm ci
npm run build
cd ..

# Prepare deployment package
echo "📦 Preparing deployment files..."
rm -rf deploy_package
mkdir -p deploy_package
cp -r app deploy_package/
cp -r frontend/dist deploy_package/frontend-dist
cp requirements.txt deploy_package/

# Create deployment directory on EC2
echo "📁 Creating deployment directory on EC2..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "sudo mkdir -p $DEPLOY_DIR && sudo chown -R ec2-user:ec2-user /home/ec2-user/movierec"

# Transfer files
echo "📤 Transferring files to EC2..."
rsync -avz --delete -e "ssh -i $SSH_KEY" \
  deploy_package/ \
  "$EC2_USER@$EC2_HOST:$DEPLOY_DIR/"

# Install dependencies and restart services
echo "🔧 Installing dependencies and restarting services..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "bash -lc 'set -e; cd $DEPLOY_DIR; if [ ! -d .venv ]; then python3 -m venv .venv; fi; source .venv/bin/activate; pip install --upgrade pip; pip install -r requirements.txt; sudo systemctl restart movierec; sudo systemctl status --no-pager movierec || true'"

# Verify deployment
echo "🔍 Verifying deployment..."
if curl -fsS "http://$EC2_HOST/config" > /dev/null; then
  echo "✅ Health check passed via Nginx (port 80)"
else
  echo "❌ Health check failed; recent logs:"
  ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "sudo journalctl -u movierec --since '5 minutes ago' --no-pager || true"
  exit 1
fi

# Cleanup
rm -rf deploy_package

echo "✅ Deployment successful!"
echo "🌐 API Base: http://$EC2_HOST"
echo "📊 API Docs: http://$EC2_HOST/docs"
