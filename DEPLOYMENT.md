# Deployment Guide

## EC2 Deployment Setup

### Prerequisites

1. **EC2 Instance Requirements**
   - Python 3.11+ installed
   - Node.js 22+ installed (if serving frontend from EC2)
   - Security group allows inbound traffic on port 8001
   - SSH access configured

2. **GitHub Secrets Configuration**
   
   Add the following secret to your GitHub repository:
   
   - Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
   - Name: `AWS_PRIVATE_KEY`
   - Value: Contents of your `.pem` private key file

### GitHub Actions Deployment

The workflow automatically deploys on every push to `master` branch.

**What it does:**
1. Builds the React frontend (`frontend/dist`)
2. Transfers files to EC2 via SSH/rsync
3. Installs Python dependencies in a virtual environment
4. Restarts the FastAPI backend on port 8001

**Deployment location on EC2:**
```
~/MovieRecommender-Henry/
├── app/                    # FastAPI backend
├── frontend-dist/          # Built React frontend
├── requirements.txt
├── .venv/                  # Python virtual environment
└── backend.log             # Backend logs
```

**Backend runs on:** `http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com:8001`

### Manual Deployment

If you need to deploy manually without GitHub Actions:

```bash
# 1. Place your .pem key at ~/.ssh/movie-recommender-ec2.pem
# 2. Run the deploy script
./scripts/deploy.sh
```

Or specify a custom SSH key location:
```bash
SSH_KEY=/path/to/your/key.pem ./scripts/deploy.sh
```

### EC2 Instance Setup (First Time)

SSH into your EC2 instance and run these commands:

```bash
# Update system packages
sudo yum update -y

# Install Python 3.11 (if not already installed)
sudo yum install python3.11 -y

# Install Node.js 22 (optional, only if serving frontend from EC2)
curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
sudo yum install nodejs -y

# Verify installations
python3.11 --version
node --version
npm --version
```

### Monitoring & Troubleshooting

**Check backend status:**
```bash
ssh -i ~/.ssh/movie-recommender-ec2.pem ec2-user@ec2-13-59-13-187.us-east-2.compute.amazonaws.com
cd ~/MovieRecommender-Henry
ps aux | grep uvicorn
```

**View backend logs:**
```bash
tail -f ~/MovieRecommender-Henry/backend.log
```

**Restart backend manually:**
```bash
cd ~/MovieRecommender-Henry
pkill -f "uvicorn app.main:app.*8001"
source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 > backend.log 2>&1 &
```

**Check if port 8001 is listening:**
```bash
sudo netstat -tlnp | grep 8001
# or
sudo lsof -i :8001
```

### Security Group Configuration

Ensure your EC2 security group allows:

| Type | Protocol | Port | Source |
|------|----------|------|--------|
| SSH | TCP | 22 | Your IP |
| Custom TCP | TCP | 8001 | 0.0.0.0/0 (or specific IPs) |

### Environment Variables

If your app needs environment variables (e.g., `TMDB_API_KEY`), add them to the EC2 instance:

```bash
# SSH into EC2
ssh -i ~/.ssh/movie-recommender-ec2.pem ec2-user@ec2-13-59-13-187.us-east-2.compute.amazonaws.com

# Create .env file
cd ~/MovieRecommender-Henry
cat > .env << 'EOF'
TMDB_READ_TOKEN=your_token_here
TMDB_REGION=US
EOF

# Update deploy workflow to load .env
# (FastAPI will auto-load .env if python-dotenv is installed)
```

### Production Improvements

For a production setup, consider:

1. **Process Manager (PM2 or systemd)**
   - Keeps backend running after SSH disconnect
   - Auto-restart on crashes
   - Log rotation

2. **Reverse Proxy (Nginx)**
   - Serve frontend static files
   - Proxy `/api` requests to backend
   - SSL/TLS termination

3. **Database**
   - Use PostgreSQL/MySQL instead of SQLite
   - Store `app.db` in persistent location

4. **Monitoring**
   - CloudWatch logs
   - Health check endpoints
   - Uptime monitoring

### Example systemd Service (Optional)

Create `/etc/systemd/system/movie-recommender.service`:

```ini
[Unit]
Description=MovieRecommender FastAPI Backend
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/MovieRecommender-Henry
Environment="PATH=/home/ec2-user/MovieRecommender-Henry/.venv/bin"
ExecStart=/home/ec2-user/MovieRecommender-Henry/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable movie-recommender
sudo systemctl start movie-recommender
sudo systemctl status movie-recommender
```

### URLs

- **API Base:** http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com:8001
- **API Docs:** http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com:8001/docs
- **Health Check:** http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com:8001/config

### Support

For issues:
1. Check GitHub Actions logs in the `Actions` tab
2. SSH into EC2 and check `backend.log`
3. Verify security group rules
4. Ensure `.pem` key is added to GitHub Secrets correctly
