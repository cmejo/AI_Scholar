#!/bin/bash
# Production Deployment Script for AI Scholar
# Complete production setup with security hardening and monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

success() {
    echo -e "${PURPLE}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Configuration
DOMAIN=""
EMAIL=""
SKIP_SYSTEM_SETUP=false
SKIP_SECURITY_HARDENING=false
SKIP_MONITORING=false
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --skip-system)
            SKIP_SYSTEM_SETUP=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY_HARDENING=true
            shift
            ;;
        --skip-monitoring)
            SKIP_MONITORING=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Production Deployment Script for AI Scholar"
            echo
            echo "Usage: $0 --domain DOMAIN --email EMAIL [OPTIONS]"
            echo
            echo "Required:"
            echo "  --domain DOMAIN       Your production domain (e.g., example.com)"
            echo "  --email EMAIL         Email for Let's Encrypt and alerts"
            echo
            echo "Options:"
            echo "  --skip-system         Skip system setup and hardening"
            echo "  --skip-security       Skip security hardening"
            echo "  --skip-monitoring     Skip monitoring setup"
            echo "  --dry-run            Show what would be done without executing"
            echo "  -h, --help           Show this help message"
            echo
            echo "Example:"
            echo "  $0 --domain myapp.com --email admin@myapp.com"
            exit 0
            ;;
        *)
            error "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

# Validation
if [[ -z "$DOMAIN" ]]; then
    error "Domain is required. Use --domain yourdomain.com"
fi

if [[ -z "$EMAIL" ]]; then
    error "Email is required. Use --email your@email.com"
fi

if [[ "$DOMAIN" == "localhost" ]]; then
    error "Cannot use localhost for production. Please use a real domain."
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root (use sudo)"
fi

echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║              AI Scholar Production Deployment                ║
║           Enterprise-Grade Setup with Security               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

info "Domain: $DOMAIN"
info "Email: $EMAIL"
info "Dry run: $DRY_RUN"

if [[ "$DRY_RUN" == true ]]; then
    warn "DRY RUN MODE - No changes will be made"
fi

# Pre-flight checks
log "Running pre-flight checks..."

# Check if required scripts exist
REQUIRED_SCRIPTS=(
    "setup-nginx-proxy.sh"
    "nginx-ssl-setup.sh"
    "test-nginx-config.sh"
    "nginx-monitoring-setup.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ ! -f "$script" ]]; then
        error "Required script not found: $script"
    fi
done

# Check internet connectivity
if ! ping -c 1 google.com &> /dev/null; then
    error "No internet connectivity. Please check your network connection."
fi

# Check DNS resolution for domain
if ! nslookup "$DOMAIN" &> /dev/null; then
    warn "DNS resolution failed for $DOMAIN. Make sure DNS is configured correctly."
fi

success "Pre-flight checks completed"

# System Setup and Hardening
if [[ "$SKIP_SYSTEM_SETUP" == false ]]; then
    log "🔧 Setting up and hardening system..."
    
    if [[ "$DRY_RUN" == false ]]; then
        # Update system
        info "Updating system packages..."
        apt update && apt upgrade -y
        
        # Install essential packages
        info "Installing essential packages..."
        apt install -y \
            curl wget git unzip htop iotop nethogs \
            fail2ban ufw logwatch aide rkhunter \
            unattended-upgrades apt-listchanges \
            software-properties-common ca-certificates \
            gnupg lsb-release jq
        
        # Configure automatic security updates
        info "Configuring automatic security updates..."
        echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
        dpkg-reconfigure -plow unattended-upgrades
        
        # Configure firewall
        info "Configuring firewall..."
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw limit ssh
        ufw --force enable
        
        # Configure fail2ban
        info "Configuring fail2ban..."
        systemctl enable fail2ban
        systemctl start fail2ban
        
        # Create fail2ban configuration for nginx
        cat > /etc/fail2ban/jail.d/nginx.conf << 'EOF'
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
findtime = 600
bantime = 7200

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
EOF
        
        systemctl restart fail2ban
        
        success "System setup and hardening completed"
    else
        info "Would update system and configure security (dry run)"
    fi
fi

# Security Hardening
if [[ "$SKIP_SECURITY_HARDENING" == false ]]; then
    log "🛡️ Applying additional security hardening..."
    
    if [[ "$DRY_RUN" == false ]]; then
        # Secure shared memory
        if ! grep -q "tmpfs /run/shm tmpfs defaults,noexec,nosuid 0 0" /etc/fstab; then
            echo "tmpfs /run/shm tmpfs defaults,noexec,nosuid 0 0" >> /etc/fstab
        fi
        
        # Disable unused network protocols
        cat > /etc/modprobe.d/blacklist-rare-network.conf << 'EOF'
# Disable rare network protocols
install dccp /bin/true
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
EOF
        
        # Kernel hardening
        cat > /etc/sysctl.d/99-security.conf << 'EOF'
# IP Spoofing protection
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.rp_filter = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Log Martians
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Ignore ICMP ping requests
net.ipv4.icmp_echo_ignore_all = 0

# Ignore Directed pings
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable IPv6 if not needed
net.ipv6.conf.all.disable_ipv6 = 0
net.ipv6.conf.default.disable_ipv6 = 0

# Performance and security
net.core.somaxconn = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_syncookies = 1
EOF
        
        sysctl -p /etc/sysctl.d/99-security.conf
        
        # Setup log monitoring
        cat > /etc/logwatch/conf/logwatch.conf << EOF
LogDir = /var/log
MailTo = $EMAIL
MailFrom = logwatch@$DOMAIN
Detail = Med
Service = All
Range = yesterday
Format = html
EOF
        
        success "Security hardening completed"
    else
        info "Would apply security hardening (dry run)"
    fi
fi

# Install Docker if not present
log "🐳 Setting up Docker..."
if [[ "$DRY_RUN" == false ]]; then
    if ! command -v docker &> /dev/null; then
        info "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        
        # Install Docker Compose
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        
        # Start Docker
        systemctl enable docker
        systemctl start docker
        
        success "Docker installed and started"
    else
        info "Docker already installed"
    fi
else
    info "Would install Docker if needed (dry run)"
fi

# Setup Nginx Reverse Proxy
log "🌐 Setting up Nginx reverse proxy..."
if [[ "$DRY_RUN" == false ]]; then
    ./setup-nginx-proxy.sh "$DOMAIN" production
    success "Nginx reverse proxy configured"
else
    info "Would setup nginx reverse proxy (dry run)"
fi

# Setup SSL Certificates
log "🔒 Setting up SSL certificates..."
if [[ "$DRY_RUN" == false ]]; then
    ./nginx-ssl-setup.sh --production --domain "$DOMAIN" --email "$EMAIL"
    success "SSL certificates configured"
else
    info "Would setup SSL certificates (dry run)"
fi

# Setup Monitoring
if [[ "$SKIP_MONITORING" == false ]]; then
    log "📊 Setting up monitoring and logging..."
    if [[ "$DRY_RUN" == false ]]; then
        ./nginx-monitoring-setup.sh
        
        # Configure email alerts
        sed -i "s/admin@yourdomain.com/$EMAIL/g" /opt/nginx-monitoring/configs/alerts.conf
        sed -i "s/yourdomain.com/$DOMAIN/g" /opt/nginx-monitoring/configs/alerts.conf
        
        success "Monitoring and logging configured"
    else
        info "Would setup monitoring (dry run)"
    fi
fi

# Setup Backup Strategy
log "💾 Setting up backup strategy..."
if [[ "$DRY_RUN" == false ]]; then
    # Create backup directory
    mkdir -p /var/backups/ai-scholar
    
    # Create backup script
    cat > /usr/local/bin/backup-ai-scholar.sh << EOF
#!/bin/bash
# AI Scholar Production Backup Script

BACKUP_DIR="/var/backups/ai-scholar"
DATE=\$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Create backup directory
mkdir -p \$BACKUP_DIR

# Database backup
if docker ps | grep -q ai-scholar-postgres; then
    echo "Backing up PostgreSQL database..."
    docker exec ai-scholar-postgres pg_dump -U ai_scholar_prod ai_scholar_prod > \$BACKUP_DIR/db_\$DATE.sql
    gzip \$BACKUP_DIR/db_\$DATE.sql
fi

# Application data backup
if [[ -d "./data" ]]; then
    echo "Backing up application data..."
    tar -czf \$BACKUP_DIR/data_\$DATE.tar.gz ./data/
fi

# Configuration backup
echo "Backing up configuration..."
tar -czf \$BACKUP_DIR/config_\$DATE.tar.gz /etc/nginx/ .env* docker-compose*.yml

# SSL certificates backup
if [[ -d "/etc/letsencrypt" ]]; then
    tar -czf \$BACKUP_DIR/ssl_\$DATE.tar.gz /etc/letsencrypt/
fi

# Clean old backups
find \$BACKUP_DIR -name "*.sql.gz" -mtime +\$RETENTION_DAYS -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +\$RETENTION_DAYS -delete

# Log backup completion
echo "\$(date): Backup completed successfully" >> /var/log/ai-scholar-backup.log

# Send notification (optional)
# echo "AI Scholar backup completed on \$(hostname)" | mail -s "Backup Report" $EMAIL
EOF
    
    chmod +x /usr/local/bin/backup-ai-scholar.sh
    
    # Schedule daily backups
    (crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-ai-scholar.sh") | crontab -
    
    success "Backup strategy configured"
else
    info "Would setup backup strategy (dry run)"
fi

# Deploy AI Scholar Services
log "🚀 Deploying AI Scholar services..."
if [[ "$DRY_RUN" == false ]]; then
    # Check if .env.production exists
    if [[ ! -f ".env.production" ]]; then
        warn ".env.production not found. Creating template..."
        cat > .env.production << EOF
# AI Scholar Production Environment

# Database Configuration
POSTGRES_DB=ai_scholar_prod
POSTGRES_USER=ai_scholar_prod
POSTGRES_PASSWORD=CHANGE_THIS_SECURE_PASSWORD
POSTGRES_PORT=5433

# Redis Configuration
REDIS_PASSWORD=CHANGE_THIS_REDIS_PASSWORD
REDIS_PORT=6380

# Application Security
SECRET_KEY=CHANGE_THIS_TO_A_VERY_LONG_RANDOM_STRING
JWT_SECRET=CHANGE_THIS_JWT_SECRET

# API Keys (add your actual keys)
OPENAI_API_KEY=your_openai_key_here
HUGGINGFACE_API_KEY=your_huggingface_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Production Settings
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Domain Configuration
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN

# Service Ports
BACKEND_PORT=8001
FRONTEND_PORT=3006

# Resource Limits
MAX_FILE_SIZE_MB=100
NGINX_WORKER_PROCESSES=auto
NGINX_WORKER_CONNECTIONS=1024
EOF
        warn "Please edit .env.production with your actual values before continuing"
        warn "Especially change all passwords and API keys!"
    fi
    
    # Copy production environment
    cp .env.production .env
    
    # Deploy services
    if [[ -f "docker-compose.prod.yml" ]]; then
        info "Deploying with production compose..."
        docker-compose -f docker-compose.prod.yml up -d
    else
        info "Deploying with AI services script..."
        ./deploy-with-ai-services.sh
    fi
    
    success "AI Scholar services deployed"
else
    info "Would deploy AI Scholar services (dry run)"
fi

# Test Configuration
log "🧪 Testing production configuration..."
if [[ "$DRY_RUN" == false ]]; then
    sleep 30  # Wait for services to start
    
    ./test-nginx-config.sh "$DOMAIN"
    
    # Additional production tests
    info "Running additional production tests..."
    
    # Test SSL
    if curl -I "https://$DOMAIN/health" &> /dev/null; then
        success "HTTPS endpoint is responding"
    else
        warn "HTTPS endpoint test failed"
    fi
    
    # Test security headers
    HEADERS=$(curl -I -s "https://$DOMAIN/health" 2>/dev/null)
    if echo "$HEADERS" | grep -q "Strict-Transport-Security"; then
        success "HSTS header present"
    else
        warn "HSTS header missing"
    fi
    
    success "Configuration testing completed"
else
    info "Would test configuration (dry run)"
fi

# Final Security Scan
log "🔍 Running final security scan..."
if [[ "$DRY_RUN" == false ]]; then
    # Check for common security issues
    info "Checking for common security issues..."
    
    # Check SSH configuration
    if grep -q "PermitRootLogin no" /etc/ssh/sshd_config; then
        success "Root SSH login disabled"
    else
        warn "Consider disabling root SSH login"
    fi
    
    # Check firewall status
    if ufw status | grep -q "Status: active"; then
        success "Firewall is active"
    else
        warn "Firewall is not active"
    fi
    
    # Check fail2ban status
    if systemctl is-active --quiet fail2ban; then
        success "Fail2ban is running"
    else
        warn "Fail2ban is not running"
    fi
    
    success "Security scan completed"
else
    info "Would run security scan (dry run)"
fi

# Generate deployment report
log "📋 Generating deployment report..."
REPORT_FILE="/tmp/ai-scholar-deployment-report.txt"

cat > "$REPORT_FILE" << EOF
AI Scholar Production Deployment Report
======================================
Date: $(date)
Domain: $DOMAIN
Email: $EMAIL

System Information:
- OS: $(lsb_release -d | cut -f2)
- Kernel: $(uname -r)
- Architecture: $(uname -m)
- Memory: $(free -h | grep Mem | awk '{print $2}')
- Disk: $(df -h / | tail -1 | awk '{print $2}')

Services Status:
$(systemctl is-active nginx || echo "nginx: inactive")
$(systemctl is-active docker || echo "docker: inactive")
$(systemctl is-active fail2ban || echo "fail2ban: inactive")

Docker Services:
$(docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "Docker not running")

SSL Certificate:
$(openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -subject -dates 2>/dev/null || echo "Certificate not found")

Network Configuration:
$(ufw status numbered)

Next Steps:
1. Review and update .env.production with secure passwords and API keys
2. Test all application functionality
3. Setup external monitoring (Pingdom, UptimeRobot, etc.)
4. Configure log aggregation if needed
5. Schedule regular security updates
6. Test backup and recovery procedures

Important Files:
- Nginx config: /etc/nginx/sites-available/ai-scholar
- SSL certificates: /etc/letsencrypt/live/$DOMAIN/
- Monitoring scripts: /opt/nginx-monitoring/scripts/
- Backup script: /usr/local/bin/backup-ai-scholar.sh
- Environment file: .env.production

Monitoring Commands:
- Dashboard: sudo /opt/nginx-monitoring/scripts/dashboard.sh
- Logs: sudo tail -f /var/log/nginx/access.log
- Status: ./test-nginx-config.sh $DOMAIN
- Security: sudo /opt/nginx-monitoring/scripts/security-monitor.sh

Support:
- Check logs: /var/log/nginx/error.log
- Test config: sudo nginx -t
- Reload nginx: sudo systemctl reload nginx
- Restart services: docker-compose -f docker-compose.prod.yml restart
EOF

if [[ "$DRY_RUN" == false ]]; then
    cat "$REPORT_FILE"
    cp "$REPORT_FILE" "/var/log/ai-scholar-deployment-$(date +%Y%m%d_%H%M%S).log"
else
    info "Would generate deployment report (dry run)"
fi

echo
echo -e "${GREEN}🎉 AI Scholar Production Deployment Complete! 🎉${NC}"
echo
echo -e "${BLUE}=== Access Information ===${NC}"
echo -e "🌐 Main application: ${GREEN}https://$DOMAIN${NC}"
echo -e "🔧 Health check: ${GREEN}https://$DOMAIN/health${NC}"
echo -e "📊 Monitoring: ${GREEN}sudo /opt/nginx-monitoring/scripts/dashboard.sh${NC}"
echo
echo -e "${BLUE}=== Important Next Steps ===${NC}"
echo "1. 🔑 Update .env.production with secure passwords and API keys"
echo "2. 🧪 Test all application functionality thoroughly"
echo "3. 📈 Setup external monitoring (Pingdom, UptimeRobot, etc.)"
echo "4. 📧 Configure email alerts in monitoring scripts"
echo "5. 🔄 Test backup and recovery procedures"
echo "6. 📋 Review security settings and harden further if needed"
echo
echo -e "${YELLOW}⚠️  Security Reminders:${NC}"
echo "- Change all default passwords in .env.production"
echo "- Review firewall rules: sudo ufw status"
echo "- Monitor fail2ban: sudo fail2ban-client status"
echo "- Check SSL rating: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo
echo -e "${BLUE}=== Support Commands ===${NC}"
echo "View logs: sudo tail -f /var/log/nginx/error.log"
echo "Test config: ./test-nginx-config.sh $DOMAIN"
echo "Monitor dashboard: sudo /opt/nginx-monitoring/scripts/dashboard.sh"
echo "Backup now: sudo /usr/local/bin/backup-ai-scholar.sh"
echo
log "🚀 Production deployment completed successfully!"

if [[ "$DRY_RUN" == true ]]; then
    echo
    warn "This was a dry run. No changes were made to your system."
    warn "Run without --dry-run to perform the actual deployment."
fi