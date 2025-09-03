# Nginx Reverse Proxy Setup Guide for AI Scholar

This guide provides comprehensive instructions for setting up nginx as a reverse proxy for your AI Scholar application, including both Docker-based and standalone configurations.

## 🏗️ Architecture Overview

Your AI Scholar app consists of:
- **Frontend**: React app (port 3005/3006)
- **Backend**: FastAPI/Python (port 8000/8001)
- **ChromaDB**: Vector database (port 8081)
- **Ollama**: LLM service (port 11435)
- **PostgreSQL**: Database (port 5433)
- **Redis**: Cache (port 6380)

Nginx will act as a single entry point routing traffic to these services.

## 🐳 Docker-Based Setup (Recommended)

### Current Configuration
You already have a solid Docker-based nginx setup with:
- SSL/TLS termination
- Security headers
- Rate limiting
- WebSocket support
- Health checks

### Quick Start
```bash
# Your existing setup works with:
docker-compose -f docker-compose.minimal.yml up -d

# Access your app at:
# HTTP: http://localhost:8080
# HTTPS: https://localhost:8443
```

## 🔧 Standalone Nginx Setup

For production deployments or when you prefer system nginx:

### 1. Install Nginx
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install nginx

# macOS
brew install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 2. Configuration Files
The setup scripts will create:
- `/etc/nginx/sites-available/ai-scholar`
- `/etc/nginx/nginx.conf` (optimized)
- SSL certificates
- Security configurations

## 📋 Available Scripts

### setup-nginx-proxy.sh
Complete nginx setup with SSL and security hardening.

### nginx-ssl-setup.sh  
SSL certificate generation and configuration.

### nginx-security-hardening.sh
Security headers, rate limiting, and DDoS protection.

### test-nginx-config.sh
Configuration validation and testing.

### nginx-monitoring-setup.sh
Logging, metrics, and monitoring configuration.

## 🚀 Quick Setup Commands

### For Docker (Current Setup)
```bash
# Start with AI services
./deploy-with-ai-services.sh

# Or start minimal setup
./quick-start-minimal.sh
```

### For Standalone Nginx
```bash
# Complete setup
./setup-nginx-proxy.sh

# Test configuration
./test-nginx-config.sh

# Enable and start
sudo systemctl enable nginx
sudo systemctl start nginx
```

## 🔒 SSL/TLS Configuration

### Development (Self-Signed)
```bash
./nginx-ssl-setup.sh --dev
```

### Production (Let's Encrypt)
```bash
./nginx-ssl-setup.sh --production --domain yourdomain.com
```

## 📊 Monitoring & Logging

### Access Logs
- Location: `/var/log/nginx/access.log`
- Format: JSON with request details

### Error Logs  
- Location: `/var/log/nginx/error.log`
- Level: Configurable (error, warn, info, debug)

### Metrics
- Nginx status module
- Prometheus metrics (optional)
- Custom health checks

## 🛡️ Security Features

### Headers
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection

### Rate Limiting
- API endpoints: 10 req/sec
- Login endpoints: 1 req/sec
- Static files: No limit

### DDoS Protection
- Connection limiting
- Request size limits
- Timeout configurations

## 🔧 Configuration Customization

### Environment Variables
```bash
# Set in .env file
NGINX_WORKER_PROCESSES=auto
NGINX_WORKER_CONNECTIONS=1024
NGINX_CLIENT_MAX_BODY_SIZE=100M
NGINX_RATE_LIMIT_API=10r/s
NGINX_RATE_LIMIT_LOGIN=1r/s
```

### Custom Locations
Add custom proxy rules in `/etc/nginx/conf.d/custom.conf`:

```nginx
# Example: Proxy to additional service
location /custom-service/ {
    proxy_pass http://localhost:9000/;
    include /etc/nginx/proxy_params;
}
```

## 🧪 Testing & Validation

### Configuration Test
```bash
sudo nginx -t
```

### Reload Configuration
```bash
sudo nginx -s reload
```

### Performance Test
```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost/

# Using curl
curl -I http://localhost/health
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   sudo netstat -tlnp | grep :80
   sudo netstat -tlnp | grep :443
   ```

2. **Permission Issues**
   ```bash
   sudo chown -R nginx:nginx /var/log/nginx
   sudo chmod 644 /etc/nginx/sites-available/*
   ```

3. **SSL Certificate Issues**
   ```bash
   openssl x509 -in /etc/nginx/ssl/fullchain.pem -text -noout
   ```

4. **Upstream Connection Issues**
   ```bash
   # Check if backend services are running
   curl http://localhost:8001/health  # Backend
   curl http://localhost:3006/health  # Frontend
   ```

### Log Analysis
```bash
# Real-time error monitoring
sudo tail -f /var/log/nginx/error.log

# Access log analysis
sudo tail -f /var/log/nginx/access.log | grep -E "(4[0-9]{2}|5[0-9]{2})"
```

## 📈 Performance Optimization

### Caching
- Static file caching (1 year)
- Browser caching headers
- Gzip compression

### Connection Optimization
- Keep-alive connections
- HTTP/2 support
- Connection pooling

### Resource Limits
- Worker processes: Auto-detected
- Worker connections: 1024
- Client body size: 100MB

## 🔄 Maintenance

### Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/nginx
```

### Certificate Renewal
```bash
# For Let's Encrypt
sudo certbot renew --dry-run
```

### Configuration Backup
```bash
# Backup current config
sudo cp -r /etc/nginx /etc/nginx.backup.$(date +%Y%m%d)
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review nginx error logs
3. Test configuration with `nginx -t`
4. Verify upstream services are running

## 🔗 Useful Links

- [Nginx Documentation](https://nginx.org/en/docs/)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)
- [Security Headers Test](https://securityheaders.com/)