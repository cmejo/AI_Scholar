# Configuration

This directory contains all configuration files for the project.

## Files

- `.env.production` - Production environment variables
- `docker-compose.prod.yml` - Production Docker Compose configuration
- `nginx.conf` - Nginx configuration
- `nginx.prod.conf` - Production Nginx configuration

## Dockerfiles

The `dockerfiles/` directory contains all Docker build files:
- `Dockerfile.backend` - Backend service
- `Dockerfile.frontend` - Frontend service
- `Dockerfile.streamlit` - Streamlit app service
- `Dockerfile.backup` - Backup service

## Usage

Copy example environment file:
```bash
cp .env.example .env
```

For production:
```bash
cp config/.env.production .env
```

Build with specific Dockerfile:
```bash
docker build -f config/dockerfiles/Dockerfile.backend -t backend .
```
