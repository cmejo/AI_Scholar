# AI Scholar Production Deployment Guide

This guide covers deploying AI Scholar with nginx reverse proxy in a production environment with enterprise-grade security, monitoring, and reliability.

## 🏗️ Production Architecture

```
Internet → Firewall → Load Balancer → Nginx Reverse Proxy → AI Scholar Services
                                    ↓
                              SSL Termination
                              Rate Limiting
                              Security Headers
                              Monitoring
```

## 🚀 Quick Production Setup

### One-Command Production Deployment
```bash
# Replace with your actual domain and email
./quick-nginx-setup.sh --production --domain yourdomain.com --email admin@yourdomain.com
```

## 📋 Step-by-Step Production Deployment

### 1. Server Preparation

#### System Requirements
- **OS**: Ubuntu 20.04+ LTS, CentOS 8+, or RHEL 8+
- **RAM**: 8GB minimum, 16GB+ recommended
- **CPU**: 4 cores minimum, 8+ recommended
- **Storage**: 100GB+ SSD
- **Network**: Static IP address, domain name configured

#### Initial Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git unzip htop fail2ban ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Configure fail2ban for SSH protection
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. Domain and DNS Setup

#### DNS Configuration
```bash
# A Records (replace with your server IP)
yourdomain.com.     A    203.0.113.1
www.yourdomain.com. A    203.0.113.1

# Optional: AAAA records for IPv6
yourdomain.com.     AAAA 2001:db8::1
```

#### Verify DNS Propagation
```bash
# Check DNS resolution
dig yourdomain.com
nslookup yourdomain.com

# Test from multiple locations
curl -I http://yourdomain.com
```

### 3. Production Nginx Setup

#### Clone and Setup
```bash
# Clone your AI Scholar repository
git clone https://github.com/yourusername/ai-scholar.git
cd ai-scholar

# Make scripts executable
chmod +x *.sh

# Run production setup
sudo ./quick-nginx-setup.sh --production --domain yourdomain.com --email admin@yourdomain.com
```

#### Manual Production Setup (Alternative)
```bash
# Step 1: Setup nginx with production config
sudo ./setup-nginx-proxy.sh yourdomain.com production

# Step 2: Setup Let's Encrypt SSL
sudo ./nginx-ssl-setup.sh --production --domain yourdomain.com --email admin@yourdomain.com

# Step 3: Setup monitoring
sudo ./nginx-monitoring-setup.sh

# Step 4: Test configuration
./test-nginx-config.sh yourdomain.com
```

### 4. AI Scholar Services Deployment

#### Environment Configuration
```bash
# Copy production environment file
cp .env.production .env

# Edit production settings
nano .env
```

#### Production Environment Variables
```bash
# Database
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=ai_scholar_prod
POSTGRES_USER=ai_scholar_prod

# Redis
REDIS_PASSWORD=your_redis_password_here

# Security
SECRET_KEY=your_very_long_secret_key_here
JWT_SECRET=your_jwt_secret_here

# API Keys
OPENAI_API_KEY=your_openai_key
HUGGINGFACE_API_KEY=your_hf_key
ANTHROPIC_API_KEY=your_anthropic_key

# Production settings
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Domain configuration
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

#### Deploy Services
```bash
# Build and deploy with production compose
docker-compose -f docker-compose.prod.yml up -d

# Or use the deployment script
./deploy-with-ai-services.sh
```

### 5. SSL Certificate Management

#### Let's Encrypt Setup
```bash
# Automatic setup (already done in quick setup)
sudo ./nginx-ssl-setup.sh --production --domain yourdomain.com --email admin@yourdomain.com

# Manual certificate request
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

#### Certificate Verification
```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout

# Test SSL configuration
curl -I https://yourdomain.com

# Online SSL test
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

### 6. Security Hardening

#### Additional Security Measures
```bash
# Install additional security tools
sudo apt install -y aide rkhunter chkrootkit

# Configure automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Setup log monitoring
sudo apt install -y logwatch
```

#### Firewall Configuration
```bash
# Advanced firewall rules
sudo ufw limit ssh
sudo ufw deny from 192.168.0.0/16 to any port 22
sudo ufw allow from trusted.ip.address to any port 22

# Rate limiting for HTTP/HTTPS
sudo ufw limit 80/tcp
sudo ufw limit 443/tcp
```

### 7. Monitoring and Alerting

#### System Monitoring
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Setup system monitoring
sudo ./nginx-monitoring-setup.sh

# Configure email alerts
sudo nano /opt/nginx-monitoring/configs/alerts.conf
```

#### Log Management
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/nginx-ai-scholar

# Setup centralized logging (optional)
# Install ELK stack or similar
```

### 8. Backup Strategy

#### Database Backups
```bash
# Create backup script
cat > /usr/local/bin/backup-ai-scholar.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/ai-scholar"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker exec ai-scholar-postgres pg_dump -U ai_scholar_prod ai_scholar_prod > $BACKUP_DIR/db_$DATE.sql

# Application data backup
tar -czf $BACKUP_DIR/data_$DATE.tar.gz ./data/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-ai-scholar.sh

# Schedule daily backups
echo "0 2 * * * /usr/local/bin/backup-ai-scholar.sh" | sudo crontab -
```

### 9. Performance Optimization

#### System Optimization
```bash
# Optimize system limits
sudo nano /etc/security/limits.conf
# Add:
# nginx soft nofile 65536
# nginx hard nofile 65536

# Optimize kernel parameters
sudo nano /etc/sysctl.conf
# Add:
# net.core.somaxconn = 65536
# net.ipv4.tcp_max_syn_backlog = 65536
# net.core.netdev_max_backlog = 5000

# Apply changes
sudo sysctl -p
```

#### Nginx Optimization
```bash
# The setup scripts already include optimized nginx configuration
# Additional tuning can be done in /etc/nginx/nginx.conf

# Monitor performance
sudo /opt/nginx-monitoring/scripts/performance-monitor.sh monitor
```

### 10. Health Checks and Monitoring

#### Service Health Checks
```bash
# Test all endpoints
./test-nginx-config.sh yourdomain.com

# Monitor services
sudo /opt/nginx-monitoring/scripts/dashboard.sh

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

#### External Monitoring
```bash
# Setup external monitoring (recommended)
# - Pingdom, UptimeRobot, or similar
# - Monitor: https://yourdomain.com/health

# Setup log aggregation
# - ELK Stack, Splunk, or similar
# - Monitor: /var/log/nginx/*.log
```

## 🔧 Production Configuration Files

### Nginx Production Config
The setup scripts create optimized production configurations with:
- HTTP/2 and TLS 1.3 support
- Security headers (HSTS, CSP, etc.)
- Rate limiting and DDoS protection
- Gzip compression
- Static file caching
- WebSocket support

### Docker Compose Production
```yaml
# docker-compose.prod.yml (already exists)
# Includes:
# - Resource limits
# - Health checks
# - Restart policies
# - Production environment variables
```

## 📊 Monitoring and Maintenance

### Daily Monitoring Tasks
```bash
# Check system health
sudo /opt/nginx-monitoring/scripts/dashboard.sh

# Review logs
sudo tail -f /var/log/nginx/error.log
sudo journalctl -u nginx -f

# Check SSL certificate expiry
sudo certbot certificates

# Monitor disk space
df -h
```

### Weekly Maintenance
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Review security logs
sudo fail2ban-client status
sudo grep "Failed password" /var/log/auth.log

# Check backup integrity
ls -la /var/backups/ai-scholar/

# Performance review
sudo /opt/nginx-monitoring/scripts/performance-monitor.sh report
```

## 🚨 Troubleshooting

### Common Production Issues

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates manually
sudo certbot renew --dry-run
sudo certbot renew

# Check nginx SSL config
sudo nginx -t
openssl s_client -connect yourdomain.com:443
```

#### Performance Issues
```bash
# Check resource usage
htop
iotop
nethogs

# Monitor nginx performance
sudo /opt/nginx-monitoring/scripts/performance-monitor.sh monitor

# Check upstream services
curl http://localhost:8001/health
curl http://localhost:3006/health
```

#### Service Connectivity Issues
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs

# Test internal connectivity
docker exec ai-scholar-nginx curl http://backend:8000/health
```

## 🔐 Security Checklist

### Pre-Production Security Audit
- [ ] SSL/TLS configuration (A+ rating on SSL Labs)
- [ ] Security headers implemented
- [ ] Rate limiting configured
- [ ] Firewall rules in place
- [ ] Fail2ban configured
- [ ] Regular security updates enabled
- [ ] Strong passwords and keys
- [ ] Database access restricted
- [ ] Log monitoring active
- [ ] Backup strategy implemented

### Ongoing Security Tasks
- [ ] Weekly security updates
- [ ] Monthly SSL certificate check
- [ ] Quarterly security audit
- [ ] Regular backup testing
- [ ] Log review and analysis
- [ ] Performance monitoring
- [ ] Vulnerability scanning

## 📈 Scaling Considerations

### Horizontal Scaling
```bash
# Load balancer configuration
# Multiple nginx instances
# Database clustering
# Redis clustering
# CDN integration
```

### Vertical Scaling
```bash
# Increase server resources
# Optimize nginx worker processes
# Database performance tuning
# Application optimization
```

## 📞 Support and Maintenance

### Log Locations
- Nginx logs: `/var/log/nginx/`
- Application logs: `./logs/`
- System logs: `/var/log/syslog`
- Security logs: `/var/log/auth.log`

### Key Commands
```bash
# Restart services
sudo systemctl restart nginx
docker-compose -f docker-compose.prod.yml restart

# View logs
sudo tail -f /var/log/nginx/error.log
docker-compose -f docker-compose.prod.yml logs -f

# Test configuration
sudo nginx -t
./test-nginx-config.sh yourdomain.com

# Monitor performance
sudo /opt/nginx-monitoring/scripts/dashboard.sh
```

## 🎯 Production Checklist

### Before Going Live
- [ ] Domain DNS configured
- [ ] SSL certificates installed and tested
- [ ] All services running and healthy
- [ ] Security hardening complete
- [ ] Monitoring and alerting configured
- [ ] Backup strategy implemented
- [ ] Performance testing completed
- [ ] Documentation updated
- [ ] Team trained on operations

### Post-Deployment
- [ ] Monitor for 24-48 hours
- [ ] Verify all functionality
- [ ] Check performance metrics
- [ ] Review security logs
- [ ] Test backup and recovery
- [ ] Update monitoring thresholds
- [ ] Document any issues
- [ ] Plan regular maintenance

This production guide ensures your AI Scholar application runs reliably, securely, and efficiently in a production environment with enterprise-grade nginx reverse proxy configuration.