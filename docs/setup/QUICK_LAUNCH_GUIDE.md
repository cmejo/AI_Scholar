# ⚡ Quick Launch Guide - Advanced RAG Research Ecosystem

## 🚀 **30-Minute Launch** (For Experienced Users)

### **Prerequisites**
- VPS with Ubuntu 22.04 (8GB RAM, 4 CPU cores)
- Domain name pointing to your server
- SSH access to server

### **Step 1: Server Setup (5 minutes)**
```bash
# Connect and update
ssh root@your-server-ip
apt update && apt upgrade -y
apt install -y curl git docker.io docker-compose

# Create user
adduser appuser
usermod -aG sudo,docker appuser
su - appuser
```

### **Step 2: Clone & Configure (5 minutes)**
```bash
# Clone repository
git clone https://github.com/yourusername/advanced-rag-research-ecosystem.git
cd advanced-rag-research-ecosystem

# Configure environment
cp .env.production .env
vim .env  # Edit with your values:
# - DOMAIN=yourdomain.com
# - POSTGRES_PASSWORD=secure_password
# - SECRET_KEY=random_64_char_string
# - OPENAI_API_KEY=your_key
```

### **Step 3: SSL Setup (5 minutes)**
```bash
# Install certbot and get certificate
sudo apt install -y certbot
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl/
```

### **Step 4: Deploy (10 minutes)**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Deploy application
./scripts/deploy.sh

# This automatically:
# - Builds all Docker images
# - Starts all services
# - Runs database migrations
# - Verifies deployment
```

### **Step 5: Verify (5 minutes)**
```bash
# Check services
docker-compose ps

# Test application
curl -f https://yourdomain.com/api/health

# Access application
# Frontend: https://yourdomain.com
# API Docs: https://yourdomain.com/api/docs
```

---

## 🔧 **Essential Commands**

```bash
# View logs
docker-compose logs -f [service_name]

# Restart service
docker-compose restart [service_name]

# Update deployment
./scripts/deploy.sh update

# Backup data
./scripts/backup.sh

# Monitor resources
docker stats
```

---

## 🆘 **Quick Troubleshooting**

**Services won't start:**
```bash
docker-compose logs backend
# Check environment variables in .env
```

**SSL issues:**
```bash
sudo certbot renew
docker-compose restart nginx
```

**Database issues:**
```bash
docker-compose restart postgres
docker-compose logs postgres
```

---

## ✅ **Success Indicators**

- [ ] All services show "Up" status
- [ ] https://yourdomain.com loads successfully
- [ ] API documentation accessible
- [ ] Can create user account
- [ ] Can upload and process documents

**Your Advanced RAG Research Ecosystem is now live! 🎉**

For detailed configuration and advanced features, see `SERVER_LAUNCH_PLAN.md`.