# Deployment Guide

This guide explains how to set up automatic deployment for the Backtester application.

## Architecture

The production deployment includes:
- **backtester-web** - Flask web application (port 8000)
- **market-analytics** - FastAPI service for market data
- **telegram-bot** - Telegram bot for notifications
- **postgres** - PostgreSQL database
- **redis** - Redis cache

## GitHub Actions Auto-Deploy

The CI/CD pipeline automatically:
1. Runs tests on push to `main` or `develop`
2. Builds 4 Docker images and pushes to GitHub Container Registry (ghcr.io)
3. Deploys to production server on push to `main`

## Required GitHub Secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions** and add:

### Server Access
- `HOST` - Server IP address or hostname
- `USER` - SSH username (e.g., `root`)
- `SSH_KEY` - Private SSH key for server access

### Application Configuration
- `DOMAIN` - Your domain name (e.g., `backtester.hub-cargo.ru`)
- `LETSENCRYPT_EMAIL` - Email for SSL certificate notifications
- `WEB_PORT` - Web application port (usually `8000`)

### Authentication
- `GHCR_TOKEN` - GitHub Personal Access Token with `read:packages` permission
  - Create at: GitHub → Settings → Developer settings → Personal access tokens
  - Required scopes: `read:packages` (for pulling Docker images on server)

### Database
- `DB_USER` - PostgreSQL username (default: `backtester`)
- `DB_PASSWORD` - PostgreSQL password (generate strong password)

### Services
- `REDIS_PASSWORD` - Redis password (generate strong password)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from @BotFather

## Server Requirements

### 1. Install Docker & Docker Compose
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

### 2. Install Nginx
```bash
sudo apt update
sudo apt install nginx
```

### 3. Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### 4. Create deployment directory
```bash
sudo mkdir -p /opt/backtester
sudo chown $USER:$USER /opt/backtester
```

### 5. Configure DNS
Point your domain A record to your server IP address.

## Manual Deployment

If you need to deploy manually:

```bash
cd /opt/backtester

# Login to GitHub Container Registry
echo $GHCR_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Pull and start services
export GITHUB_REPOSITORY=amraul/backtester
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## Monitoring

### Check service status
```bash
docker compose -f docker-compose.prod.yml ps
```

### View logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backtester-web
docker compose -f docker-compose.prod.yml logs -f market-analytics
docker compose -f docker-compose.prod.yml logs -f telegram-bot
```

### Check container health
```bash
docker inspect backtester_web_prod | grep -A 5 Health
docker inspect market_analytics_prod | grep -A 5 Health
```

## Troubleshooting

### Images not updating
1. Check GitHub Actions logs
2. Verify GHCR_TOKEN has correct permissions
3. Manually pull: `docker compose -f docker-compose.prod.yml pull`

### Container not starting
1. Check logs: `docker compose -f docker-compose.prod.yml logs SERVICE_NAME`
2. Verify environment variables in `.env` file
3. Check database connection

### SSL certificate issues
```bash
# Test Nginx config
sudo nginx -t

# Renew certificate manually
sudo certbot renew --nginx

# Check certificate expiry
sudo certbot certificates
```

## Security Notes

- All database passwords should be strong and unique
- SSH key should have proper permissions (600)
- Never commit secrets to git
- Regularly update dependencies and base images
- Monitor logs for suspicious activity

## Rollback

To rollback to a previous version:

```bash
cd /opt/backtester

# Find previous image
docker images | grep backtester

# Tag specific version
docker tag ghcr.io/amraul/backtester-web:SHA old-version

# Update docker-compose to use specific SHA instead of :latest
# Then restart services
docker compose -f docker-compose.prod.yml up -d
```
