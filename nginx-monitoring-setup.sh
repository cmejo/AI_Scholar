#!/bin/bash
# Nginx Monitoring and Logging Setup for AI Scholar
# Sets up comprehensive logging, metrics, and monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Configuration
NGINX_CONF_DIR="/etc/nginx"
NGINX_LOG_DIR="/var/log/nginx"
MONITORING_DIR="/opt/nginx-monitoring"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    NGINX_CONF_DIR="/usr/local/etc/nginx"
    NGINX_LOG_DIR="/usr/local/var/log/nginx"
    MONITORING_DIR="/usr/local/opt/nginx-monitoring"
elif [[ -f /etc/debian_version ]]; then
    OS="debian"
elif [[ -f /etc/redhat-release ]]; then
    OS="redhat"
else
    OS="unknown"
fi

echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                 Nginx Monitoring Setup                       ║
║              Logging, Metrics & Alerting                     ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

info "OS: $OS"
info "Nginx config dir: $NGINX_CONF_DIR"
info "Nginx log dir: $NGINX_LOG_DIR"

# Check if running as root (except on macOS)
if [[ "$OS" != "macos" && $EUID -ne 0 ]]; then
    error "This script must be run as root (use sudo)"
fi

# Create monitoring directory
log "Creating monitoring directories..."
mkdir -p "$MONITORING_DIR"/{scripts,configs,logs}
mkdir -p "$NGINX_LOG_DIR"

# 1. Enhanced Logging Configuration
log "Setting up enhanced logging configuration..."
cat > "$NGINX_CONF_DIR/conf.d/logging.conf" << 'EOF'
# Enhanced logging configuration for AI Scholar

# JSON log format for structured logging
log_format json_combined escape=json '{'
    '"timestamp":"$time_iso8601",'
    '"remote_addr":"$remote_addr",'
    '"remote_user":"$remote_user",'
    '"request":"$request",'
    '"status":$status,'
    '"body_bytes_sent":$body_bytes_sent,'
    '"request_time":$request_time,'
    '"upstream_response_time":"$upstream_response_time",'
    '"upstream_addr":"$upstream_addr",'
    '"http_referrer":"$http_referer",'
    '"http_user_agent":"$http_user_agent",'
    '"http_x_forwarded_for":"$http_x_forwarded_for",'
    '"http_host":"$http_host",'
    '"server_name":"$server_name",'
    '"request_uri":"$request_uri",'
    '"args":"$args",'
    '"scheme":"$scheme",'
    '"request_method":"$request_method",'
    '"request_length":$request_length,'
    '"bytes_sent":$bytes_sent,'
    '"gzip_ratio":"$gzip_ratio",'
    '"connection":"$connection",'
    '"connection_requests":$connection_requests'
'}';

# Performance monitoring log format
log_format performance '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent" '
                       'rt=$request_time uct="$upstream_connect_time" '
                       'uht="$upstream_header_time" urt="$upstream_response_time"';

# Security monitoring log format
log_format security '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    '"$http_x_forwarded_for" "$http_x_real_ip" '
                    'country="$geoip2_country_code" city="$geoip2_city"';

# Error log with detailed information
error_log /var/log/nginx/error.log warn;

# Access logs
access_log /var/log/nginx/access.log json_combined;
access_log /var/log/nginx/performance.log performance;

# Separate logs for different endpoints
map $request_uri $api_log {
    ~^/api/ /var/log/nginx/api.log;
    default /dev/null;
}

map $request_uri $static_log {
    ~*\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp)$ /var/log/nginx/static.log;
    default /dev/null;
}

access_log $api_log json_combined;
access_log $static_log json_combined;
EOF

# 2. Nginx Status Module Configuration
log "Setting up nginx status monitoring..."
cat > "$NGINX_CONF_DIR/conf.d/status.conf" << 'EOF'
# Nginx status monitoring configuration

server {
    listen 127.0.0.1:8888;
    server_name localhost;
    
    location /nginx-status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow ::1;
        deny all;
    }
    
    location /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# 3. Log Rotation Configuration
log "Setting up log rotation..."
cat > "/etc/logrotate.d/nginx-ai-scholar" << EOF
$NGINX_LOG_DIR/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 nginx nginx
    sharedscripts
    prerotate
        if [ -d /etc/logrotate.d/httpd-prerotate ]; then \
            run-parts /etc/logrotate.d/httpd-prerotate; \
        fi \
    endscript
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 \`cat /var/run/nginx.pid\`
        fi
    endscript
}
EOF

# 4. Monitoring Scripts
log "Creating monitoring scripts..."

# Real-time log monitoring script
cat > "$MONITORING_DIR/scripts/monitor-logs.sh" << 'EOF'
#!/bin/bash
# Real-time nginx log monitoring for AI Scholar

NGINX_LOG_DIR="/var/log/nginx"
ALERT_EMAIL="admin@yourdomain.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Monitor error log for critical issues
monitor_errors() {
    tail -f "$NGINX_LOG_DIR/error.log" | while read line; do
        if echo "$line" | grep -E "(emerg|alert|crit)"; then
            error "CRITICAL: $line"
            # Send alert (uncomment and configure)
            # echo "$line" | mail -s "Nginx Critical Error" "$ALERT_EMAIL"
        elif echo "$line" | grep -E "(error)"; then
            warn "ERROR: $line"
        fi
    done
}

# Monitor access log for suspicious activity
monitor_access() {
    tail -f "$NGINX_LOG_DIR/access.log" | while read line; do
        # Check for 4xx/5xx errors
        if echo "$line" | grep -E '"status":[45][0-9][0-9]'; then
            warn "HTTP Error: $line"
        fi
        
        # Check for high response times
        if echo "$line" | grep -E '"request_time":[5-9]\.[0-9]+'; then
            warn "Slow Response: $line"
        fi
    done
}

# Main monitoring function
case "${1:-all}" in
    "errors")
        log "Monitoring nginx error log..."
        monitor_errors
        ;;
    "access")
        log "Monitoring nginx access log..."
        monitor_access
        ;;
    "all")
        log "Starting comprehensive log monitoring..."
        monitor_errors &
        monitor_access &
        wait
        ;;
    *)
        echo "Usage: $0 [errors|access|all]"
        exit 1
        ;;
esac
EOF

# Performance monitoring script
cat > "$MONITORING_DIR/scripts/performance-monitor.sh" << 'EOF'
#!/bin/bash
# Nginx performance monitoring script

NGINX_LOG_DIR="/var/log/nginx"
REPORT_FILE="/tmp/nginx-performance-report.txt"

# Generate performance report
generate_report() {
    echo "Nginx Performance Report - $(date)" > "$REPORT_FILE"
    echo "=======================================" >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"
    
    # Request count by status code
    echo "Requests by Status Code (last 1000 entries):" >> "$REPORT_FILE"
    tail -1000 "$NGINX_LOG_DIR/access.log" | \
        grep -o '"status":[0-9]*' | \
        cut -d: -f2 | \
        sort | uniq -c | sort -nr >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"
    
    # Top requested URLs
    echo "Top 10 Requested URLs:" >> "$REPORT_FILE"
    tail -1000 "$NGINX_LOG_DIR/access.log" | \
        grep -o '"request_uri":"[^"]*"' | \
        cut -d'"' -f4 | \
        sort | uniq -c | sort -nr | head -10 >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"
    
    # Response time statistics
    echo "Response Time Statistics:" >> "$REPORT_FILE"
    tail -1000 "$NGINX_LOG_DIR/access.log" | \
        grep -o '"request_time":[0-9.]*' | \
        cut -d: -f2 | \
        awk '{
            sum += $1; 
            count++; 
            if($1 > max) max = $1; 
            if(min == "" || $1 < min) min = $1
        } 
        END {
            print "Average: " sum/count "s"
            print "Min: " min "s"
            print "Max: " max "s"
        }' >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"
    
    # User agents
    echo "Top 5 User Agents:" >> "$REPORT_FILE"
    tail -1000 "$NGINX_LOG_DIR/access.log" | \
        grep -o '"http_user_agent":"[^"]*"' | \
        cut -d'"' -f4 | \
        sort | uniq -c | sort -nr | head -5 >> "$REPORT_FILE"
    
    cat "$REPORT_FILE"
}

# Real-time performance monitoring
monitor_performance() {
    while true; do
        clear
        echo "=== Nginx Real-time Performance Monitor ==="
        echo "Press Ctrl+C to exit"
        echo
        
        # Current connections
        if curl -s http://127.0.0.1:8888/nginx-status > /dev/null 2>&1; then
            echo "Current Status:"
            curl -s http://127.0.0.1:8888/nginx-status
            echo
        fi
        
        # Recent requests (last 10)
        echo "Recent Requests (last 10):"
        tail -10 "$NGINX_LOG_DIR/access.log" | \
            jq -r '"\(.timestamp) \(.status) \(.request_time)s \(.request)"' 2>/dev/null || \
            tail -10 "$NGINX_LOG_DIR/access.log"
        
        sleep 5
    done
}

case "${1:-report}" in
    "report")
        generate_report
        ;;
    "monitor")
        monitor_performance
        ;;
    *)
        echo "Usage: $0 [report|monitor]"
        exit 1
        ;;
esac
EOF

# Security monitoring script
cat > "$MONITORING_DIR/scripts/security-monitor.sh" << 'EOF'
#!/bin/bash
# Nginx security monitoring script

NGINX_LOG_DIR="/var/log/nginx"
ALERT_THRESHOLD=10
BLOCK_LIST="/tmp/nginx-blocked-ips.txt"

# Monitor for suspicious activity
monitor_security() {
    echo "=== Nginx Security Monitor ==="
    echo "Monitoring for suspicious activity..."
    echo
    
    # Check for potential attacks
    echo "Potential Security Issues (last 1000 requests):"
    
    # SQL injection attempts
    SQL_ATTACKS=$(tail -1000 "$NGINX_LOG_DIR/access.log" | grep -i -E "(union|select|insert|delete|drop|script|alert)" | wc -l)
    if [ "$SQL_ATTACKS" -gt 0 ]; then
        echo "⚠️  SQL injection attempts: $SQL_ATTACKS"
    fi
    
    # XSS attempts
    XSS_ATTACKS=$(tail -1000 "$NGINX_LOG_DIR/access.log" | grep -i -E "(<script|javascript:|onload=|onerror=)" | wc -l)
    if [ "$XSS_ATTACKS" -gt 0 ]; then
        echo "⚠️  XSS attempts: $XSS_ATTACKS"
    fi
    
    # Directory traversal
    TRAVERSAL_ATTACKS=$(tail -1000 "$NGINX_LOG_DIR/access.log" | grep -E "\.\./|\.\.\\\\|%2e%2e" | wc -l)
    if [ "$TRAVERSAL_ATTACKS" -gt 0 ]; then
        echo "⚠️  Directory traversal attempts: $TRAVERSAL_ATTACKS"
    fi
    
    # Brute force detection (multiple 401/403 from same IP)
    echo
    echo "IPs with multiple failed requests:"
    tail -1000 "$NGINX_LOG_DIR/access.log" | \
        grep '"status":[43][0-9][0-9]' | \
        grep -o '"remote_addr":"[^"]*"' | \
        cut -d'"' -f4 | \
        sort | uniq -c | \
        awk -v threshold="$ALERT_THRESHOLD" '$1 > threshold {print "🚨 " $2 ": " $1 " failed requests"}'
    
    # Top error-generating IPs
    echo
    echo "Top IPs generating errors:"
    tail -1000 "$NGINX_LOG_DIR/access.log" | \
        grep '"status":[45][0-9][0-9]' | \
        grep -o '"remote_addr":"[^"]*"' | \
        cut -d'"' -f4 | \
        sort | uniq -c | sort -nr | head -5
}

# Generate security report
generate_security_report() {
    echo "Nginx Security Report - $(date)"
    echo "====================================="
    echo
    
    monitor_security
    
    echo
    echo "Recent 4xx/5xx Errors:"
    tail -100 "$NGINX_LOG_DIR/access.log" | \
        grep '"status":[45][0-9][0-9]' | \
        jq -r '"\(.timestamp) \(.remote_addr) \(.status) \(.request)"' 2>/dev/null || \
        tail -100 "$NGINX_LOG_DIR/access.log" | grep -E '"status":[45][0-9][0-9]'
}

case "${1:-monitor}" in
    "monitor")
        monitor_security
        ;;
    "report")
        generate_security_report
        ;;
    *)
        echo "Usage: $0 [monitor|report]"
        exit 1
        ;;
esac
EOF

# Make scripts executable
chmod +x "$MONITORING_DIR/scripts/"*.sh

# 5. Alerting Configuration
log "Setting up alerting configuration..."
cat > "$MONITORING_DIR/configs/alerts.conf" << 'EOF'
# Nginx Alerting Configuration for AI Scholar

# Email settings
ALERT_EMAIL="admin@yourdomain.com"
SMTP_SERVER="localhost"

# Thresholds
ERROR_RATE_THRESHOLD=5          # Errors per minute
RESPONSE_TIME_THRESHOLD=5.0     # Seconds
CONNECTION_THRESHOLD=1000       # Concurrent connections
DISK_USAGE_THRESHOLD=80         # Percentage

# Alert intervals (minutes)
ERROR_ALERT_INTERVAL=5
PERFORMANCE_ALERT_INTERVAL=10
SECURITY_ALERT_INTERVAL=1
EOF

# 6. Systemd service for monitoring (Linux only)
if [[ "$OS" != "macos" ]]; then
    log "Creating systemd service for monitoring..."
    cat > "/etc/systemd/system/nginx-monitor.service" << EOF
[Unit]
Description=Nginx Monitoring Service for AI Scholar
After=nginx.service
Requires=nginx.service

[Service]
Type=simple
User=nginx
Group=nginx
ExecStart=$MONITORING_DIR/scripts/monitor-logs.sh all
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable nginx-monitor.service
fi

# 7. Cron jobs for regular monitoring
log "Setting up cron jobs for monitoring..."
cat > "/tmp/nginx-monitoring-cron" << EOF
# Nginx monitoring cron jobs for AI Scholar

# Generate performance report every hour
0 * * * * $MONITORING_DIR/scripts/performance-monitor.sh report > $MONITORING_DIR/logs/performance-\$(date +\%Y\%m\%d-\%H).log

# Security scan every 15 minutes
*/15 * * * * $MONITORING_DIR/scripts/security-monitor.sh report > $MONITORING_DIR/logs/security-\$(date +\%Y\%m\%d-\%H\%M).log

# Clean old monitoring logs weekly
0 2 * * 0 find $MONITORING_DIR/logs -name "*.log" -mtime +7 -delete
EOF

crontab -l 2>/dev/null | cat - /tmp/nginx-monitoring-cron | crontab -
rm /tmp/nginx-monitoring-cron

# 8. Dashboard script
log "Creating monitoring dashboard..."
cat > "$MONITORING_DIR/scripts/dashboard.sh" << 'EOF'
#!/bin/bash
# Nginx monitoring dashboard

NGINX_LOG_DIR="/var/log/nginx"

show_dashboard() {
    clear
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    AI Scholar Nginx Dashboard                ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo
    
    # System info
    echo "System Information:"
    echo "  Date: $(date)"
    echo "  Uptime: $(uptime | cut -d',' -f1 | cut -d' ' -f4-)"
    echo
    
    # Nginx status
    echo "Nginx Status:"
    if pgrep nginx > /dev/null; then
        echo "  ✅ Nginx is running"
        if curl -s http://127.0.0.1:8888/nginx-status > /dev/null 2>&1; then
            echo "  📊 Status module available"
            curl -s http://127.0.0.1:8888/nginx-status | sed 's/^/    /'
        fi
    else
        echo "  ❌ Nginx is not running"
    fi
    echo
    
    # Recent activity
    echo "Recent Activity (last 10 requests):"
    if [[ -f "$NGINX_LOG_DIR/access.log" ]]; then
        tail -10 "$NGINX_LOG_DIR/access.log" | \
            jq -r '"  \(.timestamp) \(.status) \(.request_time)s \(.remote_addr) \(.request)"' 2>/dev/null || \
            tail -10 "$NGINX_LOG_DIR/access.log" | sed 's/^/  /'
    else
        echo "  No access log found"
    fi
    echo
    
    # Error summary
    echo "Recent Errors:"
    if [[ -f "$NGINX_LOG_DIR/error.log" ]]; then
        tail -5 "$NGINX_LOG_DIR/error.log" | sed 's/^/  /'
    else
        echo "  No error log found"
    fi
    echo
    
    # Quick stats
    echo "Quick Stats (last 1000 requests):"
    if [[ -f "$NGINX_LOG_DIR/access.log" ]]; then
        echo "  Total requests: $(tail -1000 "$NGINX_LOG_DIR/access.log" | wc -l)"
        echo "  2xx responses: $(tail -1000 "$NGINX_LOG_DIR/access.log" | grep '"status":2[0-9][0-9]' | wc -l)"
        echo "  4xx responses: $(tail -1000 "$NGINX_LOG_DIR/access.log" | grep '"status":4[0-9][0-9]' | wc -l)"
        echo "  5xx responses: $(tail -1000 "$NGINX_LOG_DIR/access.log" | grep '"status":5[0-9][0-9]' | wc -l)"
    fi
    echo
    
    echo "Press 'r' to refresh, 'q' to quit, or wait 10 seconds for auto-refresh..."
}

# Interactive dashboard
while true; do
    show_dashboard
    
    read -t 10 -n 1 key
    case $key in
        'q'|'Q')
            echo
            echo "Goodbye!"
            exit 0
            ;;
        'r'|'R')
            continue
            ;;
        *)
            continue
            ;;
    esac
done
EOF

chmod +x "$MONITORING_DIR/scripts/dashboard.sh"

# Test nginx configuration
log "Testing nginx configuration..."
if nginx -t; then
    log "✅ Nginx configuration is valid"
    
    # Reload nginx
    if [[ "$OS" == "macos" ]]; then
        nginx -s reload
    else
        systemctl reload nginx
    fi
else
    error "❌ Nginx configuration test failed"
fi

# Set proper permissions
if [[ "$OS" != "macos" ]]; then
    chown -R nginx:nginx "$MONITORING_DIR"
    chown -R nginx:nginx "$NGINX_LOG_DIR"
fi

echo
echo -e "${GREEN}🎉 Nginx Monitoring Setup Complete! 🎉${NC}"
echo
echo -e "${BLUE}=== Monitoring Tools ===${NC}"
echo -e "Dashboard: ${GREEN}$MONITORING_DIR/scripts/dashboard.sh${NC}"
echo -e "Log monitor: ${GREEN}$MONITORING_DIR/scripts/monitor-logs.sh${NC}"
echo -e "Performance: ${GREEN}$MONITORING_DIR/scripts/performance-monitor.sh${NC}"
echo -e "Security: ${GREEN}$MONITORING_DIR/scripts/security-monitor.sh${NC}"
echo
echo -e "${BLUE}=== Log Files ===${NC}"
echo -e "Access log: ${GREEN}$NGINX_LOG_DIR/access.log${NC}"
echo -e "Error log: ${GREEN}$NGINX_LOG_DIR/error.log${NC}"
echo -e "API log: ${GREEN}$NGINX_LOG_DIR/api.log${NC}"
echo -e "Performance log: ${GREEN}$NGINX_LOG_DIR/performance.log${NC}"
echo
echo -e "${BLUE}=== Quick Commands ===${NC}"
echo "View dashboard: $MONITORING_DIR/scripts/dashboard.sh"
echo "Monitor logs: $MONITORING_DIR/scripts/monitor-logs.sh"
echo "Performance report: $MONITORING_DIR/scripts/performance-monitor.sh report"
echo "Security scan: $MONITORING_DIR/scripts/security-monitor.sh"
echo "Nginx status: curl http://127.0.0.1:8888/nginx-status"
echo
echo -e "${YELLOW}Note: Configure email alerts in $MONITORING_DIR/configs/alerts.conf${NC}"