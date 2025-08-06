# AI Scholar Advanced RAG - Deployment Infrastructure

This directory contains the complete deployment infrastructure for the AI Scholar Advanced RAG system, implementing task 10.1 from the missing advanced features specification.

## 🚀 Overview

The deployment infrastructure provides:

- **CI/CD Pipelines**: Automated mobile app and web application deployment
- **Blue-Green Deployment**: Zero-downtime deployments with automatic rollback
- **Database Migrations**: Schema updates with zero-downtime migration support
- **Health Monitoring**: Comprehensive health checks and monitoring
- **Multi-platform Support**: Mobile apps (iOS/Android), PWA, and web application

## 📁 Directory Structure

```
scripts/deployment/
├── README.md                    # This file
├── deploy.sh                    # Main deployment orchestrator
├── blue-green-deployment.sh     # Blue-green deployment implementation
├── database-migration.sh        # Database schema migration
├── switch-traffic.sh           # Traffic switching for blue-green
├── rollback.sh                 # Emergency and graceful rollback
├── health-check.sh             # Comprehensive health monitoring
├── maintenance.sh              # Maintenance mode management
└── incident-response.sh        # Incident response automation

config/
├── docker-compose.blue.yml     # Blue environment configuration
├── docker-compose.green.yml    # Green environment configuration
├── deployment.env.example      # Environment configuration template
└── dockerfiles/
    ├── Dockerfile.frontend      # Frontend container build
    ├── Dockerfile.backend       # Backend container build
    └── Dockerfile.nginx         # Nginx reverse proxy build

.github/workflows/
├── mobile-deployment.yml       # Mobile app CI/CD pipeline
└── web-deployment.yml          # Web application CI/CD pipeline
```

## 🛠️ Setup Instructions

### 1. Environment Configuration

Copy the environment template and configure for your environment:

```bash
cp config/deployment.env.example .env.production
```

Edit `.env.production` with your specific configuration:

- Database credentials
- API keys (OpenAI, Hugging Face)
- AWS credentials for mobile app deployment
- Notification webhooks (Slack, email)
- SSL certificate paths

### 2. Docker Registry Setup

Configure your Docker registry (GitHub Container Registry by default):

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# Or configure for other registries
export REGISTRY=your-registry.com
export IMAGE_NAME=your-org/ai-scholar-rag
```

### 3. Infrastructure Prerequisites

Ensure the following are installed and configured:

- Docker and Docker Compose
- Nginx (for load balancing)
- SSL certificates (Let's Encrypt recommended)
- Database backup storage (AWS S3 or similar)

### 4. Initial Deployment

Run the initial deployment:

```bash
# Make scripts executable
chmod +x scripts/deployment/*.sh

# Run initial deployment
./scripts/deployment/deploy.sh deploy v1.0.0 blue-green
```

## 🔄 Deployment Strategies

### Blue-Green Deployment (Recommended)

Zero-downtime deployment with automatic rollback:

```bash
# Deploy to inactive environment and switch traffic
./scripts/deployment/blue-green-deployment.sh latest

# Manual traffic switch
./scripts/deployment/switch-traffic.sh blue

# Rollback if needed
./scripts/deployment/rollback.sh auto
```

### Rolling Deployment

Update services one by one:

```bash
./scripts/deployment/deploy.sh deploy latest rolling
```

### Recreate Deployment

Full restart (with downtime):

```bash
./scripts/deployment/deploy.sh deploy latest recreate
```

## 📱 Mobile App Deployment

### Prerequisites

1. **Android**: Configure Google Play Console API access
2. **iOS**: Configure App Store Connect API access
3. **PWA**: Configure CDN (AWS CloudFront/S3)

### Configuration

Set up mobile deployment secrets in GitHub:

```bash
# Android
ANDROID_KEYSTORE          # Base64 encoded keystore
KEYSTORE_PASSWORD         # Keystore password
KEY_ALIAS                 # Key alias
KEY_PASSWORD              # Key password
GOOGLE_PLAY_SERVICE_ACCOUNT # Service account JSON

# iOS
APPLE_ID_USERNAME         # Apple ID username
APPLE_ID_PASSWORD         # App-specific password

# PWA
PWA_S3_BUCKET_PROD       # Production S3 bucket
PWA_S3_BUCKET_STAGING    # Staging S3 bucket
CLOUDFRONT_DISTRIBUTION_ID_PROD   # CloudFront distribution ID
CLOUDFRONT_DISTRIBUTION_ID_STAGING # Staging CloudFront ID
```

### Deployment Process

Mobile apps are automatically deployed when changes are pushed to the main branch:

1. **Build**: Apps are built for Android and iOS
2. **Test**: Automated testing on multiple devices
3. **Deploy**: 
   - PWA deployed to CDN
   - Android APK uploaded to Google Play
   - iOS IPA uploaded to App Store Connect

## 🗄️ Database Migrations

### Standard Migration

```bash
./scripts/deployment/database-migration.sh migrate
```

### Zero-Downtime Migration

For production environments:

```bash
./scripts/deployment/database-migration.sh zero-downtime
```

### Rollback Migration

```bash
./scripts/deployment/database-migration.sh rollback
```

### Migration Features

- **Automatic Backups**: Created before each migration
- **Schema Validation**: Ensures migration integrity
- **Batch Processing**: Large data migrations in batches
- **Rollback Support**: Automatic rollback on failure

## 🏥 Health Monitoring

### Comprehensive Health Check

```bash
./scripts/deployment/health-check.sh comprehensive
```

### Quick Health Check

```bash
./scripts/deployment/health-check.sh quick
```

### Service-Specific Checks

```bash
./scripts/deployment/health-check.sh database
./scripts/deployment/health-check.sh redis
./scripts/deployment/health-check.sh backend
./scripts/deployment/health-check.sh frontend
```

### Monitoring Components

- **Database**: Connection, performance, disk usage
- **Redis**: Memory usage, connection count
- **Application**: Response times, error rates
- **Infrastructure**: CPU, memory, disk space
- **SSL**: Certificate expiration
- **Docker**: Container health status

## 🔄 CI/CD Pipeline Features

### Web Application Pipeline

- **Multi-stage builds**: Optimized Docker images
- **Parallel testing**: Frontend and backend tests
- **Security scanning**: Container vulnerability scans
- **Blue-green deployment**: Zero-downtime updates
- **Automatic rollback**: On deployment failure

### Mobile Application Pipeline

- **Cross-platform builds**: iOS and Android
- **Device testing**: Multiple device configurations
- **Store deployment**: Automated app store uploads
- **PWA deployment**: CDN distribution
- **Version management**: Semantic versioning

## 🚨 Incident Response

### Automatic Rollback

The system automatically rolls back on:

- Health check failures
- High error rates
- Performance degradation
- Database connection issues

### Manual Rollback

```bash
# Emergency rollback (immediate)
./scripts/deployment/rollback.sh emergency blue

# Graceful rollback (with health checks)
./scripts/deployment/rollback.sh graceful green
```

### Incident Response Features

- **Automated alerts**: Slack/email notifications
- **Health monitoring**: Continuous service monitoring
- **Log aggregation**: Centralized logging
- **Performance metrics**: Real-time dashboards

## 🔧 Maintenance

### Maintenance Mode

```bash
# Enable maintenance mode
./scripts/deployment/maintenance.sh enable

# Disable maintenance mode
./scripts/deployment/maintenance.sh disable
```

### System Updates

```bash
# Update system packages
./scripts/deployment/maintenance.sh update-system

# Update Docker images
./scripts/deployment/maintenance.sh update-images

# Clean up old resources
./scripts/deployment/maintenance.sh cleanup
```

## 📊 Monitoring and Observability

### Metrics Collection

- **Application metrics**: Response times, throughput
- **Infrastructure metrics**: CPU, memory, disk
- **Business metrics**: User activity, feature usage
- **Error tracking**: Exception monitoring

### Dashboards

- **Grafana**: System and application dashboards
- **Prometheus**: Metrics collection and alerting
- **Log aggregation**: Centralized log analysis

### Alerting

- **Threshold alerts**: CPU, memory, disk usage
- **Error rate alerts**: Application error monitoring
- **Availability alerts**: Service uptime monitoring
- **Performance alerts**: Response time degradation

## 🔐 Security

### Container Security

- **Non-root users**: All containers run as non-root
- **Minimal images**: Alpine-based images
- **Security scanning**: Automated vulnerability scans
- **Secret management**: Encrypted environment variables

### Network Security

- **SSL/TLS**: End-to-end encryption
- **Rate limiting**: API rate limiting
- **CORS**: Cross-origin request protection
- **Security headers**: Comprehensive security headers

### Access Control

- **Role-based access**: Deployment permissions
- **API authentication**: Secure API access
- **Audit logging**: Deployment activity logging

## 🚀 Performance Optimization

### Application Performance

- **Connection pooling**: Database connection optimization
- **Caching**: Redis caching layer
- **CDN**: Static asset distribution
- **Compression**: Gzip compression

### Infrastructure Performance

- **Load balancing**: Nginx load balancing
- **Auto-scaling**: Horizontal scaling (optional)
- **Resource limits**: Container resource constraints
- **Health checks**: Proactive health monitoring

## 📚 Troubleshooting

### Common Issues

1. **Deployment Failures**
   ```bash
   # Check deployment logs
   tail -f logs/deployment/deployment-*.log
   
   # Check service health
   ./scripts/deployment/health-check.sh comprehensive
   ```

2. **Database Migration Issues**
   ```bash
   # Verify migration status
   ./scripts/deployment/database-migration.sh verify
   
   # Rollback if needed
   ./scripts/deployment/database-migration.sh rollback
   ```

3. **Traffic Switching Problems**
   ```bash
   # Check current environment
   ./scripts/deployment/blue-green-deployment.sh status
   
   # Manual traffic switch
   ./scripts/deployment/switch-traffic.sh blue
   ```

### Log Locations

- **Deployment logs**: `logs/deployment/`
- **Application logs**: `logs/app/`
- **Nginx logs**: `logs/nginx/`
- **Database logs**: Container logs via `docker-compose logs postgres`

### Support Commands

```bash
# Show deployment status
./scripts/deployment/deploy.sh status

# Show rollback options
./scripts/deployment/rollback.sh status

# Show health status
./scripts/deployment/health-check.sh comprehensive
```

## 🤝 Contributing

When adding new deployment features:

1. Update the relevant scripts
2. Add comprehensive error handling
3. Include logging and monitoring
4. Update this documentation
5. Test in staging environment first

## 📄 License

This deployment infrastructure is part of the AI Scholar Advanced RAG project and follows the same license terms.