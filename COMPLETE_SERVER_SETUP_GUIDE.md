# 🚀 Complete Server Setup Guide - AI Scholar Advanced RAG

## 📋 **File Organization Summary**

Your deployment files are organized as follows:

```
📁 Root Level (Documentation)
├── 📄 SERVER_LAUNCH_PLAN.md          # Comprehensive launch plan
├── 📄 DEPLOYMENT_GUIDE.md            # Detailed deployment guide
├── 📄 QUICK_LAUNCH_GUIDE.md          # 30-minute quick start
├── 📄 DEPLOYMENT_CHECKLIST.md        # Pre/post deployment checklist
└── 📄 COMPLETE_SERVER_SETUP_GUIDE.md # This file

📁 scripts/deployment/ (Automation Scripts)
├── 📄 deploy.sh                      # Main deployment script
├── 📄 production-deploy.sh           # Production deployment
├── 📄 backup.sh                      # Backup automation
├── 📄 health-check.sh               # Health monitoring
├── 📄 maintenance.sh                # Maintenance tasks
├── 📄 update.sh                     # Update procedures
└── 📄 validate-deployment.sh        # Deployment validation

📁 Configuration Files
├── 📄 docker-compose.yml            # Development setup
├── 📄 docker-compose.prod.yml       # Production setup
├── 📄 .env.production               # Production environment
├── 📄 nginx.conf                    # Nginx configuration
└── 📄 nginx.prod.conf               # Production Nginx config
```

## 🎯 **Quick Server Setup (Choose Your Path)**

### **Path 1: Quick Launch (30 minutes)**
```bash
# Follow QUICK_LAUNCH_GUIDE.md for rapid deployment
./scripts/deployment/deploy.sh
```

### **Path 2: Production Setup (2-4 hours)**
```bash
# Follow SERVER_LAUNCH_PLAN.md for comprehensive setup
./scripts/deployment/production-deploy.sh
```

### **Path 3: Custom Setup**
```bash
# Follow DEPLOYMENT_GUIDE.md for detailed customization
# Then use individual scripts as needed
```

## 🖥️ **Server Requirements**

### **Minimum (Development/Testing)**
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 50GB SSD
- **Cost**: ~$20/month

### **Recommended (Small Team)**
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 100GB SSD
- **Cost**: ~$40/month

### **Production (Medium Team)**
- **CPU**: 8 cores
- **RAM**: 16GB
- **Storage**: 200GB SSD
- **Cost**: ~$80/month

## 🚀 **Step-by-Step Server Configuration**

### **Step 1: Server Provisioning**

**Recommended Providers:**
- **DigitalOcean**: Easy setup, good documentation
- **Linode**: Great performance/price ratio
- **Vultr**: High-performance SSD
- **AWS EC2**: Enterprise features (more complex)

**Quick Setup Commands:**
```bash
# Connect to your server
ssh root@your-server-ip

# Run the automated setup
curl -fsSL https://raw.githubusercontent.com/yourusername/ai-scholar/main/scripts/deployment/production-deploy.sh | bash
```

### **Step 2: Domain Configuration**

1. **Buy Domain**: Namecheap, GoDaddy, or Cloudflare
2. **DNS Setup**:
   ```
   A Record: yourdomain.com → Your Server IP
   A Record: www.yourdomain.com → Your Server IP
   ```
3. **Wait**: 1-24 hours for DNS propagation

### **Step 3: SSL Certificate**

```bash
# Automatic SSL setup (included in deployment scripts)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### **Step 4: Application Deployment**

```bash
# Clone your repository
git clone https://github.com/yourusername/ai-scholar-advanced-rag.git
cd ai-scholar-advanced-rag

# Configure environment
cp .env.production .env
vim .env  # Edit with your settings

# Deploy
./scripts/deployment/production-deploy.sh
```

### **Step 5: Verification**

```bash
# Check all services
./scripts/deployment/health-check.sh

# Access your application
# Frontend: https://yourdomain.com
# API: https://yourdomain.com/api/docs
# Admin: https://yourdomain.com/admin
```

## 🔧 **Essential Configuration**

### **Environment Variables (.env)**
```bash
# Domain Configuration
DOMAIN=yourdomain.com
ENVIRONMENT=production

# Database Configuration
POSTGRES_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_redis_password_here

# Application Secrets
SECRET_KEY=your_64_character_secret_key
JWT_SECRET=your_jwt_secret_key

# AI API Keys
OPENAI_API_KEY=your_openai_api_key
HUGGINGFACE_API_KEY=your_huggingface_key

# Email Configuration (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### **Security Configuration**
```bash
# Firewall (automatically configured by scripts)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# SSL Auto-renewal (automatically configured)
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## 📊 **Monitoring & Maintenance**

### **Health Monitoring**
```bash
# Check system health
./scripts/deployment/health-check.sh

# View application logs
docker-compose logs -f backend

# Monitor resources
htop
docker stats
```

### **Backup & Recovery**
```bash
# Manual backup
./scripts/deployment/backup.sh

# Automated daily backups (configured automatically)
crontab -l  # View scheduled backups
```

### **Updates & Maintenance**
```bash
# Update application
./scripts/deployment/update.sh

# System maintenance
./scripts/deployment/maintenance.sh
```

## 🎯 **Production Checklist**

### **Before Going Live**
- [ ] Server provisioned and secured
- [ ] Domain configured with SSL
- [ ] Environment variables set
- [ ] Database initialized
- [ ] All services running
- [ ] Health checks passing
- [ ] Backups configured
- [ ] Monitoring enabled

### **After Going Live**
- [ ] User acceptance testing
- [ ] Performance monitoring
- [ ] Security monitoring
- [ ] Backup verification
- [ ] Documentation updated
- [ ] Team access configured

## 🆘 **Troubleshooting**

### **Common Issues**

**Services Won't Start:**
```bash
# Check logs
docker-compose logs [service_name]

# Check resources
free -h && df -h

# Restart services
docker-compose restart
```

**SSL Certificate Issues:**
```bash
# Renew certificate
sudo certbot renew

# Check certificate
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout
```

**Database Connection Issues:**
```bash
# Check database
docker-compose exec postgres pg_isready

# Reset database
docker-compose down
docker volume rm $(docker volume ls -q)
docker-compose up -d
```

## 💰 **Cost Estimation**

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| **VPS (8GB)** | $40-60 | DigitalOcean/Linode |
| **Domain** | $10-15 | .com domain |
| **SSL** | $0 | Let's Encrypt (free) |
| **Backup Storage** | $5-10 | AWS S3 or similar |
| **Total** | **$55-85** | For small-medium team |

## 🎉 **Success Metrics**

After successful deployment:
- ✅ Application accessible at https://yourdomain.com
- ✅ All health checks passing
- ✅ SSL certificate valid
- ✅ Database operational
- ✅ Backups working
- ✅ Monitoring active

## 📞 **Next Steps**

1. **Choose your deployment path** (Quick/Production/Custom)
2. **Provision your server** (DigitalOcean/Linode recommended)
3. **Configure your domain** (DNS setup)
4. **Run deployment script** (automated setup)
5. **Verify deployment** (health checks)
6. **Go live!** 🚀

Your AI Scholar Advanced RAG system will be production-ready and serving users!

## 📚 **Additional Resources**

- **Detailed Setup**: `SERVER_LAUNCH_PLAN.md`
- **Quick Start**: `QUICK_LAUNCH_GUIDE.md`
- **Custom Deployment**: `DEPLOYMENT_GUIDE.md`
- **Maintenance**: `scripts/deployment/` directory
- **Monitoring**: Grafana dashboards in `monitoring/`