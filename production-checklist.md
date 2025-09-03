# AI Scholar Production Deployment Checklist

Use this checklist to ensure a complete and secure production deployment.

## 📋 Pre-Deployment Checklist

### Server Requirements
- [ ] Server meets minimum requirements (8GB RAM, 4 CPU cores, 100GB SSD)
- [ ] Static IP address assigned
- [ ] Domain name purchased and configured
- [ ] DNS A records pointing to server IP
- [ ] SSH access configured with key-based authentication
- [ ] Server accessible from your location

### Domain and DNS
- [ ] Domain purchased from registrar
- [ ] DNS A record: `yourdomain.com` → `your.server.ip`
- [ ] DNS A record: `www.yourdomain.com` → `your.server.ip`
- [ ] DNS propagation verified (`dig yourdomain.com`)
- [ ] Domain resolves correctly from multiple locations

### Security Preparation
- [ ] Strong passwords generated for all services
- [ ] API keys obtained (OpenAI, Hugging Face, etc.)
- [ ] Email account configured for alerts and certificates
- [ ] Backup strategy planned
- [ ] Security monitoring plan in place

## 🚀 Deployment Steps

### 1. Server Setup
```bash
# Run the complete production deployment
sudo ./production-deploy.sh --domain yourdomain.com --email admin@yourdomain.com
```

**Manual Steps:**
- [ ] System updated and hardened
- [ ] Firewall configured (UFW)
- [ ] Fail2ban installed and configured
- [ ] Docker and Docker Compose installed
- [ ] Security updates automated

### 2. Nginx Reverse Proxy
- [ ] Nginx installed and configured
- [ ] Production configuration applied
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Gzip compression enabled

### 3. SSL Certificates
- [ ] Let's Encrypt certificates obtained
- [ ] SSL configuration tested (A+ rating)
- [ ] Auto-renewal configured
- [ ] Certificate monitoring setup

### 4. Application Deployment
- [ ] Environment variables configured in `.env.production`
- [ ] All passwords changed from defaults
- [ ] API keys added
- [ ] Docker services deployed
- [ ] Health checks passing

### 5. Monitoring and Logging
- [ ] Nginx monitoring configured
- [ ] Log rotation setup
- [ ] Performance monitoring active
- [ ] Security monitoring enabled
- [ ] Email alerts configured

### 6. Backup Strategy
- [ ] Backup script created and tested
- [ ] Daily backups scheduled
- [ ] Backup retention policy set
- [ ] Recovery procedure documented

## ✅ Post-Deployment Verification

### Functionality Tests
- [ ] Main application loads: `https://yourdomain.com`
- [ ] Health endpoint responds: `https://yourdomain.com/health`
- [ ] API endpoints working: `https://yourdomain.com/api/health`
- [ ] WebSocket connections functional
- [ ] File uploads working
- [ ] Database connectivity verified
- [ ] Redis caching operational
- [ ] ChromaDB accessible (if enabled)
- [ ] Ollama responding (if enabled)

### Security Tests
- [ ] SSL Labs test: A+ rating
- [ ] Security headers present
- [ ] Rate limiting functional
- [ ] Firewall rules active
- [ ] Fail2ban monitoring SSH
- [ ] No unnecessary ports open
- [ ] Strong cipher suites only

### Performance Tests
- [ ] Page load times acceptable (<3 seconds)
- [ ] API response times good (<500ms)
- [ ] Concurrent user handling tested
- [ ] Resource usage monitored
- [ ] Caching working effectively

### Monitoring Tests
- [ ] Log files being written
- [ ] Monitoring dashboard accessible
- [ ] Alerts configured and tested
- [ ] Performance metrics collected
- [ ] Security events logged

## 🔧 Configuration Files to Review

### Environment Configuration
```bash
# Edit production environment
nano .env.production

# Required changes:
# - POSTGRES_PASSWORD (strong password)
# - REDIS_PASSWORD (strong password)
# - SECRET_KEY (long random string)
# - JWT_SECRET (long random string)
# - API keys (OpenAI, Hugging Face, etc.)
# - CORS_ORIGINS (your domain)
# - ALLOWED_HOSTS (your domain)
```

### Nginx Configuration
```bash
# Main nginx config
/etc/nginx/sites-available/ai-scholar

# SSL configuration
/etc/nginx/ssl/

# Monitoring config
/opt/nginx-monitoring/configs/alerts.conf
```

### Security Configuration
```bash
# Firewall rules
sudo ufw status numbered

# Fail2ban status
sudo fail2ban-client status

# SSL certificate
sudo certbot certificates
```

## 📊 Monitoring Commands

### Daily Monitoring
```bash
# Interactive dashboard
sudo /opt/nginx-monitoring/scripts/dashboard.sh

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View recent logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check SSL certificate expiry
sudo certbot certificates
```

### Weekly Maintenance
```bash
# System updates
sudo apt update && sudo apt upgrade

# Security scan
sudo /opt/nginx-monitoring/scripts/security-monitor.sh

# Performance report
sudo /opt/nginx-monitoring/scripts/performance-monitor.sh report

# Backup verification
ls -la /var/backups/ai-scholar/
```

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew --dry-run
sudo certbot renew

# Test SSL configuration
openssl s_client -connect yourdomain.com:443
```

#### Service Not Starting
```bash
# Check Docker services
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs

# Check nginx
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

#### Performance Issues
```bash
# Check resource usage
htop
iotop
df -h

# Monitor nginx performance
sudo /opt/nginx-monitoring/scripts/performance-monitor.sh monitor

# Check upstream services
curl http://localhost:8001/health
curl http://localhost:3006/health
```

#### Security Alerts
```bash
# Check fail2ban status
sudo fail2ban-client status
sudo fail2ban-client status nginx-limit-req

# Review security logs
sudo grep "Failed password" /var/log/auth.log
sudo tail -f /var/log/nginx/error.log
```

## 📈 Scaling Considerations

### When to Scale
- [ ] CPU usage consistently >80%
- [ ] Memory usage consistently >80%
- [ ] Response times >2 seconds
- [ ] Error rates >1%
- [ ] Concurrent users approaching limits

### Scaling Options
- [ ] Vertical scaling (larger server)
- [ ] Horizontal scaling (multiple servers)
- [ ] Database optimization
- [ ] CDN implementation
- [ ] Load balancer setup

## 🔐 Security Maintenance

### Monthly Security Tasks
- [ ] Review access logs for suspicious activity
- [ ] Update all system packages
- [ ] Check SSL certificate expiry
- [ ] Review firewall rules
- [ ] Audit user accounts and permissions
- [ ] Test backup and recovery procedures

### Quarterly Security Audit
- [ ] Full security scan
- [ ] Penetration testing
- [ ] SSL configuration review
- [ ] Access control audit
- [ ] Incident response plan review
- [ ] Security training update

## 📞 Emergency Procedures

### Service Down
1. Check service status: `docker-compose ps`
2. Check logs: `docker-compose logs`
3. Restart services: `docker-compose restart`
4. Check nginx: `sudo systemctl status nginx`
5. Review error logs: `sudo tail -f /var/log/nginx/error.log`

### Security Incident
1. Isolate affected systems
2. Review security logs
3. Block malicious IPs: `sudo ufw deny from IP_ADDRESS`
4. Check fail2ban: `sudo fail2ban-client status`
5. Document incident
6. Update security measures

### SSL Certificate Expiry
1. Check certificate: `sudo certbot certificates`
2. Renew certificate: `sudo certbot renew`
3. Test renewal: `sudo certbot renew --dry-run`
4. Restart nginx: `sudo systemctl restart nginx`
5. Verify SSL: Test at ssllabs.com

## 📋 Final Production Checklist

### Before Going Live
- [ ] All tests passing
- [ ] Security hardening complete
- [ ] Monitoring configured
- [ ] Backups tested
- [ ] Documentation updated
- [ ] Team trained
- [ ] Emergency procedures documented
- [ ] Performance benchmarks established

### Go-Live Day
- [ ] Final deployment executed
- [ ] All services verified
- [ ] Monitoring active
- [ ] Team on standby
- [ ] Rollback plan ready
- [ ] Communication plan executed

### Post Go-Live (First 48 Hours)
- [ ] Continuous monitoring
- [ ] Performance metrics reviewed
- [ ] Error logs monitored
- [ ] User feedback collected
- [ ] Issues documented and resolved
- [ ] Success metrics measured

## 📚 Documentation Links

- [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Nginx Reverse Proxy Guide](NGINX_REVERSE_PROXY_GUIDE.md)
- [Security Best Practices](docs/SECURITY_BEST_PRACTICES.md)
- [Monitoring Guide](docs/MONITORING_GUIDE.md)
- [Backup and Recovery](docs/BACKUP_RECOVERY.md)

---

**Remember**: Production deployment is a critical process. Take your time, follow each step carefully, and don't hesitate to test thoroughly before going live.