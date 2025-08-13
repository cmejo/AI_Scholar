# AI Scholar Deployment Guide for Ubuntu 24.04.2 LTS

This guide provides step-by-step instructions for deploying the AI Scholar RAG chatbot application on Ubuntu 24.04.2 LTS with Docker.

## Prerequisites

- Ubuntu 24.04.2 LTS server
- At least 8GB RAM (16GB recommended)
- At least 50GB free disk space (100GB recommended for Ollama models)
- Domain name pointing to your server (for SSL)
- Root or sudo access

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd ai-scholar-chatbot
   ```

2. **Run the deployment script:**
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```

3. **Configure environment:**
   ```bash
   cp .env.production .env
   nano .env  # Update with your actual values
   ```

4. **Set up SSL (optional but recommended):**
   ```bash
   ./scripts/setup-ssl.sh yourdomain.com your-email@domain.com
   ```

## Detailed Deployment Steps

### 1. System Preparation

Update your Ubuntu system:
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Docker and Docker Compose

The deployment script will install Docker automatically, but you can also install manually:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Configure Environment Variables

Copy the production environment template:
```bash
cp .env.production .env
```

Edit the `.env` file with your actual values:
```bash
nano .env
```

**Critical settings to update:**
- `DOMAIN_NAME`: Your domain name
- `SSL_EMAIL`: Your email for SSL certificates
- `POSTGRES_PASSWORD`: Secure PostgreSQL password
- `REDIS_PASSWORD`: Secure Redis password
- `SECRET_KEY`: Long random string (64+ characters)
- `JWT_SECRET`: Different long random string
- `OPENAI_API_KEY`: Your OpenAI API key
- `HUGGINGFACE_API_KEY`: Your Hugging Face API key

### 4. Deploy Services

#### Basic Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### Full Deployment with All Services
```bash
# Start core services
docker-compose -f docker-compose.prod.yml up -d postgres redis chromadb ollama backend frontend nginx

# Start monitoring (optional)
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Start workers (optional)
docker-compose -f docker-compose.prod.yml --profile workers up -d

# Start backup service (optional)
docker-compose -f docker-compose.prod.yml --profile backup up -d
```

### 5. Initialize Ollama Models

Wait for Ollama to start, then initialize models:
```bash
# Check if Ollama is ready
docker-compose -f docker-compose.prod.yml logs ollama

# Initialize models (this may take 30+ minutes)
docker-compose -f docker-compose.prod.yml exec ollama /ollama-init.sh
```

### 6. Set Up SSL Certificates

For production deployment with HTTPS:
```bash
./scripts/setup-ssl.sh yourdomain.com your-email@domain.com
```

### 7. Verify Deployment

Check service status:
```bash
docker-compose -f docker-compose.prod.yml ps
```

Test endpoints:
```bash
# Health check
curl http://localhost:8000/health

# Frontend
curl http://localhost:3005/health

# With SSL
curl https://yourdomain.com/health
```

## Service Configuration

### Available Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3005 | React application |
| Backend | 8000 | FastAPI backend |
| PostgreSQL | 5432 | Main database |
| Redis | 6379 | Cache and sessions |
| ChromaDB | 8080 | Vector database |
| Ollama | 11434 | Local LLM inference |
| Nginx | 80/443 | Reverse proxy |
| Elasticsearch | 9200 | Search engine (optional) |
| Prometheus | 9090 | Metrics (optional) |
| Grafana | 3001 | Monitoring dashboard (optional) |

### Service Profiles

Use Docker Compose profiles to control which services run:

- **Default**: Core services (postgres, redis, chromadb, ollama, backend, frontend, nginx)
- **monitoring**: Adds Prometheus and Grafana
- **workers**: Adds Celery workers and scheduler
- **backup**: Adds automated backup service
- **full-stack**: Adds Elasticsearch
- **ssl**: SSL certificate management

Example:
```bash
# Start with monitoring
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Start everything
docker-compose -f docker-compose.prod.yml --profile monitoring --profile workers --profile backup up -d
```

## Configuration Files

### Environment Variables

Key environment variables in `.env`:

```bash
# Domain and SSL
DOMAIN_NAME=yourdomain.com
SSL_EMAIL=admin@yourdomain.com

# Database
POSTGRES_DB=ai_scholar_db
POSTGRES_USER=ai_scholar_user
POSTGRES_PASSWORD=secure_password_here

# Application
SECRET_KEY=your_64_char_secret_key
JWT_SECRET=your_64_char_jwt_secret

# AI Services
OPENAI_API_KEY=your_openai_key
HUGGINGFACE_API_KEY=your_hf_key

# Ollama Models
OLLAMA_ADDITIONAL_MODELS=llama2:7b,phi:latest
```

### Resource Limits

Services have resource limits configured in `docker-compose.prod.yml`:

- **Backend**: 4GB RAM limit, 2GB reserved
- **Ollama**: 8GB RAM limit, 4GB reserved
- **PostgreSQL**: 1GB RAM limit, 512MB reserved
- **Elasticsearch**: 4GB RAM limit, 2GB reserved

Adjust based on your server specifications.

## Monitoring and Maintenance

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Service Management
```bash
# Restart a service
docker-compose -f docker-compose.prod.yml restart backend

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Update and restart
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Database Backup
```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U ai_scholar_user ai_scholar_db > backup.sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U ai_scholar_user ai_scholar_db < backup.sql
```

### SSL Certificate Renewal
```bash
# Manual renewal
./scripts/renew-ssl.sh

# Check certificate expiry
openssl x509 -in ssl/fullchain.pem -text -noout | grep "Not After"
```

## Troubleshooting

### Common Issues

1. **Services won't start**
   ```bash
   # Check logs
   docker-compose -f docker-compose.prod.yml logs
   
   # Check system resources
   docker system df
   free -h
   ```

2. **Ollama models not loading**
   ```bash
   # Check Ollama logs
   docker-compose -f docker-compose.prod.yml logs ollama
   
   # Manually pull models
   docker-compose -f docker-compose.prod.yml exec ollama ollama pull mistral
   ```

3. **SSL certificate issues**
   ```bash
   # Check certificate
   openssl x509 -in ssl/fullchain.pem -text -noout
   
   # Test SSL
   curl -I https://yourdomain.com
   ```

4. **Database connection issues**
   ```bash
   # Check PostgreSQL logs
   docker-compose -f docker-compose.prod.yml logs postgres
   
   # Test connection
   docker-compose -f docker-compose.prod.yml exec postgres psql -U ai_scholar_user -d ai_scholar_db -c "SELECT 1;"
   ```

### Performance Optimization

1. **Increase resource limits** in `docker-compose.prod.yml`
2. **Enable swap** if running low on memory:
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. **Optimize PostgreSQL** settings in `config/postgres.conf`
4. **Configure Redis** memory limits in `config/redis.conf`

## Security Considerations

1. **Change all default passwords** in `.env`
2. **Use strong SSL certificates** (Let's Encrypt recommended)
3. **Configure firewall** (UFW recommended)
4. **Enable fail2ban** for SSH protection
5. **Regular security updates**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   docker-compose -f docker-compose.prod.yml pull
   ```

6. **Monitor logs** for suspicious activity
7. **Backup regularly** and test restore procedures

## Scaling and High Availability

For production environments with high traffic:

1. **Use external databases** (managed PostgreSQL, Redis)
2. **Load balancer** in front of multiple app instances
3. **Separate Ollama** to dedicated GPU servers
4. **CDN** for static assets
5. **Container orchestration** (Kubernetes, Docker Swarm)

## Support

For issues and questions:
1. Check the logs first
2. Review this documentation
3. Check GitHub issues
4. Create a new issue with logs and configuration details

## Updates

To update the application:
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
```

Always backup your data before updating!