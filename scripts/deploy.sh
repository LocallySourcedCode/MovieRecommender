#!/usr/bin/env bash
# Manual deployment script for MovieRecommender to EC2
# Usage: ./scripts/deploy.sh

set -euo pipefail

# Configuration
EC2_HOST="ec2-13-59-13-187.us-east-2.compute.amazonaws.com"
EC2_USER="ec2-user"
DEPLOY_DIR="~/MovieRecommender-Henry"
BACKEND_PORT="8001"
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
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "mkdir -p $DEPLOY_DIR"

# Transfer files
echo "📤 Transferring files to EC2..."
rsync -avz --delete -e "ssh -i $SSH_KEY" \
  deploy_package/ \
  "$EC2_USER@$EC2_HOST:$DEPLOY_DIR/"

# Install dependencies and restart services
echo "🔧 Installing dependencies and restarting services..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
  cd $DEPLOY_DIR
  
  # Setup Python virtual environment
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  
  # Stop existing backend
  pkill -f "uvicorn app.main:app.*$BACKEND_PORT" || true
  sleep 2
  
  # Start backend
  nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > backend.log 2>&1 &
  
  echo "✅ Deployment complete!"
  echo "Backend running on port $BACKEND_PORT"
EOF

# Verify deployment
echo "🔍 Verifying deployment..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" << EOF
  cd $DEPLOY_DIR
  
  if pgrep -f "uvicorn app.main:app.*$BACKEND_PORT" > /dev/null; then
    echo "✅ Backend is running on port $BACKEND_PORT"
    ps aux | grep "uvicorn app.main:app" | grep -v grep
  else
    echo "❌ Backend failed to start"
    tail -n 50 backend.log
    exit 1
  fi
EOF

# Cleanup
rm -rf deploy_package

echo "✅ Deployment successful!"
echo "🌐 Backend URL: http://$EC2_HOST:$BACKEND_PORT"
echo "📊 API Docs: http://$EC2_HOST:$BACKEND_PORT/docs"
