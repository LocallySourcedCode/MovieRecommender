# GitHub Actions Workflows

## Deploy to EC2 (`deploy.yml`)

Automatically deploys the MovieRecommender app to EC2 on every push to `master`.

### Required GitHub Secret

- **`AWS_PRIVATE_KEY`**: Your EC2 `.pem` private key contents

### What it does

1. ✅ Checks out code
2. 📦 Builds React frontend (`npm run build`)
3. 🚀 Transfers files to EC2 via SSH/rsync
4. 🐍 Installs Python dependencies in a virtual environment in the service directory
5. 🔄 Restarts the systemd service `movierec` (Uvicorn on 127.0.0.1:8000 behind Nginx)
6. ✔️ Verifies health via HTTP GET to `http://$DEPLOY_HOST/config` (Nginx → Uvicorn)

### Deployment Target

- **Host:** `ec2-13-59-13-187.us-east-2.compute.amazonaws.com`
- **User:** `ec2-user`
- **Directory:** `/home/ec2-user/movierec/movierec` (matches systemd WorkingDirectory)
- **Backend:** Uvicorn on 8000 (behind Nginx on port 80)

### Files Deployed

- `app/` - FastAPI backend
- `frontend/dist/` - Built React frontend (renamed to `frontend-dist/`)
- `requirements.txt` - Python dependencies

### Trigger

```bash
git add .
git commit -m "Your changes"
git push origin master  # This triggers the deployment
```

### Monitoring

View deployment progress:
- Go to your GitHub repo → **Actions** tab
- Click on the latest workflow run

### Manual Deployment

If you need to deploy without pushing to GitHub:

```bash
./scripts/deploy.sh
```

See [DEPLOYMENT.md](../../DEPLOYMENT.md) for full documentation.
