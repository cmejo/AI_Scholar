# AI Scholar Chatbot - Docker Deployment Guide

## 🐳 Overview

This guide covers the complete Docker deployment of the AI Scholar Chatbot with enhanced LLM backend, including Ollama for local AI models, PostgreSQL database, Redis caching, and Nginx reverse proxy.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   Backend       │    │     Ollama      │
│ (Reverse Proxy) │◄──►│   (Flask)       │◄──►│  (Local LLMs)   │
│   Port 80/443   │    │   Port 5000     │    │   Port 11434    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │            ┌─────────────────┐                │
         │            │   PostgreSQL    │                │
         │            │   Port 5432     │                │
         │            └─────────────────┘                │
         │                       │                       │
         │                       ▼                       │
         │            ┌─────────────────┐                │
         └───────────►│     Redis       │◄───────────────┘
                      │   Port 6379     │
                      └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM (for running 7B models)
- 20GB+ free disk space

### 1. Automated Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd ai_scholar_chatbot_project

# Run the setup script
./docker-setup.sh
```

### 2. Manual Setup

```bash
# 1. Create environment file
cp .env.docker .env

# 2. Edit environment variables (IMPORTANT!)
nano .env

# 3. Start services
docker-compose -f docker-compose.ollama.yml up -d

# 4. Wait for services to be ready
./test-docker-setup.py
```

## 📋 Available Configurations

### 1. Full Production Setup
```bash
docker-compose -f docker-compose.ollama.yml up -d
```
**Includes:** Nginx, Backend, Ollama, PostgreSQL, Redis, Model Downloader

### 2. Development Setup
```bash
docker-compose -f docker-compose.enhanced-dev.yml up -d
```
**Includes:** Backend (hot reload), Ollama, SQLite database

### 3. Minimal Test Setup
```bash
docker-compose -f docker-compose.enhanced-dev.yml up -d ollama backend-dev
```
**Includes:** Backend + Ollama only

## ⚙️ Configuration

### Environment Variables

Edit `.env.docker` before starting:

```bash
# Security (CHANGE THESE!)
SECRET_KEY=your-production-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# Database
POSTGRES_PASSWORD=your-secure-database-password

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=llama2:7b-chat
```

### Model Configuration

The system automatically downloads recommended models:
- `llama2:7b-chat` - General conversation
- `mistral:7b-instruct` - Instruction following

To add more models:
```bash
# Connect to Ollama container
docker exec -it ai-scholar-ollama ollama pull codellama:7b-instruct

# Or use the API
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "codellama:7b-instruct"}'
```

## 🔧 Management Commands

### Service Management
```bash
# Start all services
docker-compose -f docker-compose.ollama.yml up -d

# Stop all services
docker-compose -f docker-compose.ollama.yml down

# Restart services
docker-compose -f docker-compose.ollama.yml restart

# View logs
docker-compose -f docker-compose.ollama.yml logs -f

# Check status
docker-compose -f docker-compose.ollama.yml ps
```

### Using the Setup Script
```bash
# Start services
./docker-setup.sh start

# Stop services
./docker-setup.sh stop

# View logs
./docker-setup.sh logs

# Check status
./docker-setup.sh status

# List models
./docker-setup.sh models

# Clean up everything
./docker-setup.sh clean
```

### Individual Service Management
```bash
# Backend only
docker-compose -f docker-compose.ollama.yml up -d backend

# Ollama only
docker-compose -f docker-compose.ollama.yml up -d ollama

# Database only
docker-compose -f docker-compose.ollama.yml up -d postgres
```

## 📊 Monitoring and Health Checks

### Health Check Endpoints
```bash
# Backend health
curl http://localhost:5000/api/health

# Ollama health
curl http://localhost:11434/api/tags

# System status
curl http://localhost:5000/api/system/status
```

### Logs and Debugging
```bash
# View all logs
docker-compose -f docker-compose.ollama.yml logs

# View specific service logs
docker-compose -f docker-compose.ollama.yml logs backend
docker-compose -f docker-compose.ollama.yml logs ollama

# Follow logs in real-time
docker-compose -f docker-compose.ollama.yml logs -f backend

# Check container status
docker ps
```

### Resource Monitoring
```bash
# Check resource usage
docker stats

# Check disk usage
docker system df

# Check volumes
docker volume ls
```

## 🔒 Security Configuration

### Production Security Checklist

- [ ] Change default passwords in `.env.docker`
- [ ] Generate secure secret keys
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Enable log monitoring
- [ ] Configure backup strategy

### SSL/HTTPS Setup

1. **Generate SSL certificates:**
```bash
mkdir ssl
# Add your SSL certificates to the ssl/ directory
# - ssl/cert.pem
# - ssl/key.pem
```

2. **Update Nginx configuration:**
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of configuration
}
```

### Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw allow 22    # SSH (if needed)
ufw deny 5000   # Block direct backend access
ufw deny 11434  # Block direct Ollama access
ufw deny 5432   # Block direct database access
```

## 📦 Data Management

### Volumes and Persistence

The setup creates several Docker volumes:
- `ollama_data` - Ollama models and configuration
- `postgres_data` - Database data
- `redis_data` - Redis cache data
- `backend_data` - Application data
- `backend_logs` - Application logs
- `backend_uploads` - Uploaded files

### Backup Strategy

```bash
# Backup database
docker exec ai-scholar-postgres pg_dump -U chatbot_user chatbot_db > backup.sql

# Backup Ollama models
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/ollama_backup.tar.gz /data

# Backup application data
docker run --rm -v backend_data:/data -v $(pwd):/backup alpine tar czf /backup/backend_backup.tar.gz /data
```

### Restore from Backup

```bash
# Restore database
docker exec -i ai-scholar-postgres psql -U chatbot_user chatbot_db < backup.sql

# Restore Ollama models
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar xzf /backup/ollama_backup.tar.gz -C /

# Restore application data
docker run --rm -v backend_data:/data -v $(pwd):/backup alpine tar xzf /backup/backend_backup.tar.gz -C /
```

## 🚀 Scaling and Performance

### Horizontal Scaling

```yaml
# Scale backend instances
services:
  backend:
    deploy:
      replicas: 3
    # ... rest of configuration
```

### Performance Tuning

1. **Ollama Performance:**
```bash
# Set GPU support (if available)
docker-compose -f docker-compose.ollama.yml up -d --build
```

2. **Database Performance:**
```yaml
postgres:
  environment:
    - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
    - POSTGRES_MAX_CONNECTIONS=200
```

3. **Redis Configuration:**
```yaml
redis:
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Ollama Not Starting
```bash
# Check logs
docker-compose -f docker-compose.ollama.yml logs ollama

# Restart Ollama
docker-compose -f docker-compose.ollama.yml restart ollama

# Check if port is available
netstat -tulpn | grep 11434
```

#### 2. Backend Connection Issues
```bash
# Check backend logs
docker-compose -f docker-compose.ollama.yml logs backend

# Test backend directly
curl http://localhost:5000/api/health

# Check environment variables
docker exec ai-scholar-backend env | grep OLLAMA
```

#### 3. Database Connection Issues
```bash
# Check database logs
docker-compose -f docker-compose.ollama.yml logs postgres

# Test database connection
docker exec ai-scholar-postgres psql -U chatbot_user -d chatbot_db -c "SELECT 1;"

# Reset database
docker-compose -f docker-compose.ollama.yml down -v
docker-compose -f docker-compose.ollama.yml up -d postgres
```

#### 4. Model Download Issues
```bash
# Check available space
df -h

# Manually download models
docker exec ai-scholar-ollama ollama pull llama2:7b-chat

# Check model status
curl http://localhost:11434/api/tags
```

### Performance Issues

#### 1. Slow Response Times
- Check system resources: `docker stats`
- Use smaller models for faster responses
- Increase memory allocation
- Consider GPU acceleration

#### 2. High Memory Usage
- Monitor with `docker stats`
- Limit container memory
- Use model quantization
- Clean up unused models

### Log Analysis

```bash
# Search for errors
docker-compose -f docker-compose.ollama.yml logs | grep -i error

# Monitor real-time logs
docker-compose -f docker-compose.ollama.yml logs -f --tail=100

# Export logs for analysis
docker-compose -f docker-compose.ollama.yml logs > system.log
```

## 📈 Monitoring and Alerting

### Basic Monitoring

```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    curl -s http://localhost:5000/api/health | jq .
    docker stats --no-stream
    echo ""
    sleep 60
done
EOF

chmod +x monitor.sh
./monitor.sh
```

### Advanced Monitoring

For production deployments, consider:
- Prometheus + Grafana
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Docker health checks
- External monitoring services

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.ollama.yml down
docker-compose -f docker-compose.ollama.yml build --no-cache
docker-compose -f docker-compose.ollama.yml up -d
```

### Updating Models

```bash
# Update existing models
docker exec ai-scholar-ollama ollama pull llama2:7b-chat

# Add new models
docker exec ai-scholar-ollama ollama pull codellama:7b-instruct
```

### System Maintenance

```bash
# Clean up unused resources
docker system prune -f

# Update base images
docker-compose -f docker-compose.ollama.yml pull

# Restart all services
docker-compose -f docker-compose.ollama.yml restart
```

## 📞 Support

### Getting Help

1. **Check logs first:**
   ```bash
   docker-compose -f docker-compose.ollama.yml logs
   ```

2. **Run diagnostics:**
   ```bash
   ./test-docker-setup.py
   ```

3. **Check system resources:**
   ```bash
   docker stats
   df -h
   free -h
   ```

4. **Verify configuration:**
   ```bash
   docker-compose -f docker-compose.ollama.yml config
   ```

### Common Solutions

- **Port conflicts:** Change ports in docker-compose.yml
- **Permission issues:** Check file ownership and Docker permissions
- **Memory issues:** Increase Docker memory limits
- **Network issues:** Check Docker network configuration

---

## 🎉 Conclusion

Your AI Scholar Chatbot is now fully dockerized and ready for production deployment! The setup provides:

- **Scalability:** Easy to scale individual components
- **Reliability:** Health checks and automatic restarts
- **Security:** Nginx proxy, isolated networks, configurable secrets
- **Maintainability:** Comprehensive logging and monitoring
- **Flexibility:** Multiple deployment configurations

**Next Steps:**
1. Configure your domain and SSL certificates
2. Set up monitoring and alerting
3. Configure automated backups
4. Deploy your React frontend
5. Start building amazing AI applications!

For additional help, refer to the troubleshooting section or check the project documentation.