# Deployment Checklist

## Pre-Deployment Setup (One-Time)

### 1. GitHub Repository Setup
- [ ] Add `AWS_PRIVATE_KEY` secret to GitHub
  - Go to: Settings → Secrets and variables → Actions → New repository secret
  - Name: `AWS_PRIVATE_KEY`
  - Value: Paste entire contents of your `.pem` file

### 2. EC2 Instance Setup
- [ ] SSH into EC2 and verify Python 3.11+ is installed
  ```bash
  ssh -i your-key.pem ec2-user@ec2-13-59-13-187.us-east-2.compute.amazonaws.com
  python3.11 --version
  ```

- [ ] Verify security group allows HTTP (80) and SSH (22)
  - AWS Console → EC2 → Security Groups
  - Add inbound rule: TCP port 80 from 0.0.0.0/0 (or specific IPs)
  - Ensure SSH port 22 is allowed from your IP

- [ ] (Optional) Set up environment variables on EC2
  ```bash
  cd ~/MovieRecommender-Henry
  nano .env
  # Add: TMDB_READ_TOKEN=your_token_here
  ```

### 3. Local Development Setup
- [ ] Ensure `.gitignore` is committed
- [ ] Test frontend build locally
  ```bash
  cd frontend
  npm run build
  ```

## Deployment Methods

### Method 1: Automatic (GitHub Actions)
- [ ] Commit your changes
  ```bash
  git add .
  git commit -m "Your commit message"
  ```

- [ ] Push to master branch
  ```bash
  git push origin master
  ```

- [ ] Monitor deployment in GitHub Actions tab
  - Go to: Repository → Actions
  - Watch the "Deploy to EC2" workflow

- [ ] Verify deployment succeeded
  - Check workflow status (green checkmark)
  - Visit: http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com/docs

### Method 2: Manual (Local Script)
- [ ] Ensure SSH key is in place
  ```bash
  # Default location: ~/.ssh/movie-recommender-ec2.pem
  chmod 600 ~/.ssh/movie-recommender-ec2.pem
  ```

- [ ] Run deploy script
  ```bash
  ./scripts/deploy.sh
  ```

- [ ] Verify deployment
  - Script will show status at the end
  - Visit: http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com/docs

## Post-Deployment Verification

- [ ] API is accessible
  ```bash
  curl http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com/config
  ```

- [ ] Backend service is running (systemd)
  ```bash
  ssh -i your-key.pem ec2-user@ec2-13-59-13-187.us-east-2.compute.amazonaws.com
  sudo systemctl status --no-pager movierec
  ```

- [ ] Check backend logs for errors
  ```bash
  ssh -i your-key.pem ec2-user@ec2-13-59-13-187.us-east-2.compute.amazonaws.com
  sudo journalctl -u movierec --since '10 minutes ago' --no-pager
  ```

- [ ] Test API endpoints
  - Visit: http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com/docs
  - Try: `/config`, `/auth/register`, etc.

## Troubleshooting

### Deployment fails in GitHub Actions
- [ ] Check Actions tab for error logs
- [ ] Verify `AWS_PRIVATE_KEY` secret is set correctly
- [ ] Ensure EC2 security group allows SSH (port 22) from GitHub IPs

### Backend not starting
- [ ] SSH into EC2 and check logs
  ```bash
  sudo journalctl -u movierec --since '10 minutes ago' --no-pager
  ```
- [ ] Verify Python dependencies installed
  ```bash
  source /home/ec2-user/MovieRecommender-Henry/.venv/bin/activate
  pip list
  ```
- [ ] Check if port 8000 is listening (optional)
  ```bash
  sudo lsof -i :8000 || ss -tlnp | grep 8000 || true
  ```

### Cannot access API from browser
- [ ] Verify security group allows inbound HTTP 80
- [ ] Check if service is running: `sudo systemctl status movierec`
- [ ] Test locally on EC2: `curl localhost/config`

## Files Created

- `.github/workflows/deploy.yml` - GitHub Actions workflow
- `scripts/deploy.sh` - Manual deployment script
- `DEPLOYMENT.md` - Full deployment documentation
- `.github/workflows/README.md` - Workflow documentation
- `DEPLOYMENT_CHECKLIST.md` - This file

## Quick Commands Reference

```bash
# View deployment status on EC2
ssh -i ~/.ssh/movie-recommender-ec2.pem ec2-user@ec2-13-59-13-187.us-east-2.compute.amazonaws.com \
  "ps aux | grep uvicorn"

# View backend logs
ssh -i ~/.ssh/movie-recommender-ec2.pem ec2-user@ec2-13-59-13-187.us-east-2.compute.amazonaws.com \
  "sudo journalctl -u movierec -f --no-pager"

# Restart backend manually
ssh -i ~/.ssh/movie-recommender-ec2.pem ec2-user@ec2-13-59-13-187.us-east-2.compute.amazonaws.com \
  "sudo systemctl restart movierec && sudo systemctl status --no-pager movierec"

# Test API
curl http://ec2-13-59-13-187.us-east-2.compute.amazonaws.com/config
```

## Next Steps After First Deployment

- [ ] Set up systemd service for auto-restart (see DEPLOYMENT.md)
- [ ] Configure Nginx reverse proxy (optional)
- [ ] Set up CloudWatch monitoring
- [ ] Configure custom domain with Route 53
- [ ] Add SSL/TLS certificate
