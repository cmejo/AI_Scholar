# Zotero Integration Deployment Configuration

This directory contains all deployment-related configuration files and documentation for the Zotero integration feature.

## Directory Structure

```
config/deployment/
├── README.md                    # This file
├── deployment-checklist.md     # Comprehensive deployment checklist
├── production.env              # Production environment variables
├── staging.env                 # Staging environment variables
├── development.env             # Development environment variables
└── templates/                  # Configuration templates
```

## Environment Files

### production.env
Production-ready configuration with:
- High security settings
- Performance optimizations
- Full monitoring and alerting
- SSL/TLS enforcement
- Comprehensive logging
- Backup and recovery settings

### staging.env
Staging environment configuration with:
- Production-like settings
- Enhanced debugging
- Relaxed security for testing
- Comprehensive monitoring
- Test data configurations

### development.env
Development environment configuration with:
- Local development settings
- Debug mode enabled
- Simplified configurations
- Mock services where appropriate
- Hot reload capabilities

## Deployment Scripts

### Core Scripts
- `scripts/deploy-zotero-integration.sh` - Standard deployment script
- `scripts/deploy-zotero-production.sh` - Production deployment with blue-green
- `scripts/database-migration.sh` - Database migration management
- `scripts/health-check.sh` - Comprehensive health checking
- `scripts/validate-deployment-config.sh` - Configuration validation

### Docker Configurations
- `docker-compose.blue.yml` - Blue environment for blue-green deployment
- `docker-compose.green.yml` - Green environment for blue-green deployment
- `docker-compose.monitoring.yml` - Monitoring stack

## Configuration Management

### Environment Variables

#### Database Configuration
```bash
DB_HOST=your-database-host
DB_PORT=5432
DB_NAME=ai_scholar
DB_USER=your-db-user
DB_PASSWORD=your-secure-password
DB_SSL_MODE=require  # production only
```

#### Redis Configuration
```bash
REDIS_URL=redis://your-redis-host:6379
REDIS_PASSWORD=your-redis-password
REDIS_MAX_CONNECTIONS=50
```

#### Zotero API Configuration
```bash
ZOTERO_CLIENT_ID=your-zotero-client-id
ZOTERO_CLIENT_SECRET=your-zotero-client-secret
ZOTERO_REDIRECT_URI=https://your-domain.com/auth/zotero/callback
ZOTERO_ENCRYPTION_KEY=your-32-character-encryption-key
ZOTERO_WEBHOOK_SECRET=your-webhook-secret
```

#### Security Configuration
```bash
SECRET_KEY=your-application-secret-key
JWT_SECRET=your-jwt-secret-key
CORS_ORIGINS=https://your-domain.com
ALLOWED_HOSTS=your-domain.com
```

### Feature Flags
Control feature availability per environment:
```bash
FEATURE_PDF_PROCESSING=true
FEATURE_ANNOTATION_SYNC=true
FEATURE_GROUP_LIBRARIES=true
FEATURE_COLLABORATION=true
FEATURE_AI_ANALYSIS=true
```

## Deployment Process

### 1. Pre-Deployment Validation
```bash
# Validate configuration
./scripts/validate-deployment-config.sh production

# Check system health
./scripts/health-check.sh production all
```

### 2. Database Migration
```bash
# Run migrations
./scripts/database-migration.sh production latest

# Verify migration
./scripts/database-migration.sh production status
```

### 3. Application Deployment
```bash
# Production deployment (blue-green)
./scripts/deploy-zotero-production.sh

# Standard deployment
./scripts/deploy-zotero-integration.sh production
```

### 4. Post-Deployment Verification
```bash
# Comprehensive health check
./scripts/health-check.sh production all

# Verify specific endpoints
curl -f https://your-domain.com/health/zotero
curl -f https://your-domain.com/api/zotero/status
```

## Monitoring and Alerting

### Prometheus Metrics
- Service availability and performance
- API request rates and response times
- Database connection pool status
- Cache hit rates and performance
- Storage usage and capacity
- Sync operation statistics

### Grafana Dashboards
- Zotero Integration Overview
- Sync Operation Monitoring
- Performance Metrics
- Error Tracking and Analysis

### AlertManager Rules
- Critical service failures
- Performance degradation
- Security incidents
- Resource exhaustion
- Sync operation failures

## Security Considerations

### Production Security
- All secrets encrypted at rest
- TLS/SSL enforced for all connections
- Rate limiting and abuse prevention
- Audit logging enabled
- Regular security scans
- Principle of least privilege

### Access Control
- Database connections from private networks only
- API endpoints protected with authentication
- File storage with proper permissions
- Container security best practices

## Backup and Recovery

### Automated Backups
- Daily database backups
- Configuration file backups
- Application state backups
- Retention policies configured

### Recovery Procedures
- Database restoration from backups
- Configuration rollback procedures
- Application state recovery
- Disaster recovery planning

## Troubleshooting

### Common Issues

#### Database Connection Failures
```bash
# Check database connectivity
pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER

# Verify credentials
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;"
```

#### Redis Connection Issues
```bash
# Test Redis connectivity
redis-cli -u $REDIS_URL ping

# Check Redis memory usage
redis-cli -u $REDIS_URL info memory
```

#### SSL Certificate Problems
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.crt -text -noout

# Verify certificate expiry
openssl x509 -in /path/to/cert.crt -enddate -noout
```

### Log Locations
- Application logs: `/app/logs/`
- Database logs: Check PostgreSQL configuration
- Redis logs: Check Redis configuration
- System logs: `/var/log/`

### Health Check Endpoints
- Overall health: `/health`
- Zotero health: `/health/zotero`
- Database health: `/health/zotero/database`
- Sync health: `/health/zotero/sync`

## Performance Optimization

### Database Optimization
- Connection pooling configured
- Indexes on frequently queried columns
- Query optimization and monitoring
- Regular maintenance tasks

### Caching Strategy
- Redis caching for frequently accessed data
- Appropriate TTL values per data type
- Cache invalidation strategies
- Cache hit rate monitoring

### Application Performance
- Async processing for long-running tasks
- Background job queues
- Resource limits and monitoring
- Performance profiling

## Compliance and Auditing

### Audit Logging
- All user actions logged
- System events tracked
- Security events monitored
- Log retention policies

### Compliance Requirements
- Data protection regulations
- Security standards compliance
- Regular security assessments
- Incident response procedures

## Support and Escalation

### Contact Information
- DevOps Team: devops@aischolar.com
- Backend Team: backend-team@aischolar.com
- Security Team: security@aischolar.com
- On-call Engineer: +1-XXX-XXX-XXXX

### Escalation Procedures
1. Check monitoring dashboards
2. Review application logs
3. Run health checks
4. Contact on-call engineer
5. Escalate to engineering manager

## Documentation Links

- [Main Deployment Guide](../../DEPLOYMENT_GUIDE.md)
- [Security Guidelines](../../backend/docs/ZOTERO_SECURITY_GUIDELINES.md)
- [API Documentation](../../docs/API_DOCUMENTATION.md)
- [Troubleshooting Guide](../../docs/zotero/TROUBLESHOOTING_FAQ.md)
- [User Guide](../../docs/zotero/USER_GUIDE.md)

---

For questions or issues with deployment configuration, please contact the DevOps team or refer to the troubleshooting documentation.