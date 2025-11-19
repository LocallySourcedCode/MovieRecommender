# Deployment Guide

## EC2 Deployment Setup

### Prerequisites

1. **EC2 Instance Requirements**
   - Python 3.11+ installed
   - Node.js 22+ installed (if serving frontend from EC2)
   - Security group allows inbound HTTP (80) and SSH (22). HTTPS (443) optional.
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
4. Restarts the systemd service `movierec` (Uvicorn on 127.0.0.1:8000 behind Nginx)

**Deployment location on EC2 (canonical):**
```
/home/ec2-user/MovieRecommender-Henry
├── app/                    # FastAPI backend
├── frontend-dist/          # Built React frontend
├── requirements.txt
├── version.txt             # Deployed commit SHA (written by workflow)
└── .venv/                  # Python virtual environment (managed by workflow)
```

**Backend runs on:** `http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com/` (via Nginx → Uvicorn:8000)

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
sudo systemctl status --no-pager movierec
```

**View backend logs:**
```bash
sudo journalctl -u movierec -f --no-pager
```

**Restart backend manually:**
```bash
sudo systemctl restart movierec
```

**Check if Uvicorn port 8000 is listening (optional):**
```bash
sudo lsof -i :8000 || ss -tlnp | grep 8000 || true
```

### Security Group Configuration

Ensure your EC2 security group allows:

| Type | Protocol | Port | Source |
|------|----------|------|--------|
| SSH | TCP | 22 | Your IP |
| HTTP | TCP | 80 | 0.0.0.0/0 (or specific IPs) |
| HTTPS (optional) | TCP | 443 | 0.0.0.0/0 (or specific IPs) |

### Environment Variables

If your app needs environment variables (e.g., `TMDB_API_KEY`), add them to the EC2 instance:

```bash
# SSH into EC2
ssh -i ~/.ssh/movie-recommender-ec2.pem ec2-user@ec2-13-59-13-187.us-east-2.compute.amazonaws.com

# Create .env file in the service directory
cd /home/ec2-user/MovieRecommender-Henry
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

### Example systemd Service (for reference)

Create `/etc/systemd/system/movierec.service`:

```ini
[Unit]
Description=MovieRecommender FastAPI (Uvicorn)
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/MovieRecommender-Henry
Environment="PATH=/home/ec2-user/MovieRecommender-Henry/.venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/home/ec2-user/MovieRecommender-Henry/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=2
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable movierec --now
sudo systemctl status movierec
```

### URLs

- **API Base:** http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com
- **API Docs:** http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com/docs
- **Health Check:** http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com/config

### Support

For issues:
1. Check GitHub Actions logs in the `Actions` tab
2. SSH into EC2 and check `sudo journalctl -u movierec --since '10 minutes ago'`
3. Verify security group rules
4. Ensure `.pem` key is added to GitHub Secrets correctly
