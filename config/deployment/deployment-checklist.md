# Zotero Integration Deployment Checklist

## Pre-Deployment Checklist

### Environment Preparation
- [ ] Verify environment variables are set in `.env.{environment}`
- [ ] Confirm database credentials and connectivity
- [ ] Validate Redis connection and configuration
- [ ] Check SSL certificates (production only)
- [ ] Verify external API keys (Zotero, OpenAI)
- [ ] Confirm backup storage is available
- [ ] Test monitoring and alerting systems

### Code and Configuration
- [ ] Code review completed and approved
- [ ] All tests passing (unit, integration, e2e)
- [ ] Security audit completed
- [ ] Performance benchmarks validated
- [ ] Configuration files reviewed for environment
- [ ] Database migration scripts tested
- [ ] Docker images built and tested
- [ ] Documentation updated

### Infrastructure
- [ ] Server resources adequate (CPU, memory, disk)
- [ ] Network connectivity verified
- [ ] Load balancer configuration updated
- [ ] Firewall rules configured
- [ ] Monitoring dashboards configured
- [ ] Log aggregation setup verified
- [ ] Backup procedures tested

## Deployment Process

### 1. Pre-Deployment Safety Checks
```bash
# Run comprehensive health check
./scripts/health-check.sh production all

# Verify database connectivity
./scripts/database-migration.sh production status

# Check system resources
df -h
free -m
```

### 2. Create Backup
```bash
# Automated backup creation
./scripts/deploy-zotero-production.sh
# OR manual backup
./scripts/database-migration.sh production backup
```

### 3. Database Migration
```bash
# Run database migrations
./scripts/database-migration.sh production latest

# Verify migration success
./scripts/database-migration.sh production status
```

### 4. Application Deployment
```bash
# Production deployment with blue-green
./scripts/deploy-zotero-production.sh

# OR standard deployment
./scripts/deploy-zotero-integration.sh production
```

### 5. Post-Deployment Verification
```bash
# Health check all components
./scripts/health-check.sh production all

# Verify API endpoints
curl -f https://aischolar.com/health/zotero
curl -f https://aischolar.com/api/zotero/status

# Check monitoring dashboards
# - Grafana: http://monitoring.aischolar.com:3000
# - Prometheus: http://monitoring.aischolar.com:9090
```

## Post-Deployment Checklist

### Immediate Verification (0-15 minutes)
- [ ] All services started successfully
- [ ] Health checks passing
- [ ] API endpoints responding
- [ ] Database connections established
- [ ] Redis cache operational
- [ ] SSL certificates valid
- [ ] Monitoring metrics flowing

### Short-term Monitoring (15 minutes - 2 hours)
- [ ] No error spikes in logs
- [ ] Response times within acceptable limits
- [ ] Memory usage stable
- [ ] CPU usage normal
- [ ] No authentication failures
- [ ] Sync operations working
- [ ] File uploads/downloads functional

### Extended Monitoring (2-24 hours)
- [ ] No memory leaks detected
- [ ] Background jobs processing
- [ ] Scheduled tasks executing
- [ ] Cache hit rates optimal
- [ ] Database performance stable
- [ ] External API integrations working
- [ ] User workflows functional

## Rollback Procedures

### Automatic Rollback Triggers
- Health check failures > 50%
- Error rate > 10%
- Response time > 5 seconds
- Database connection failures
- Critical security alerts

### Manual Rollback Process
```bash
# Stop current deployment
docker-compose down

# Restore from backup
./scripts/database-migration.sh production rollback

# Start previous version
docker-compose -f docker-compose.previous.yml up -d

# Verify rollback success
./scripts/health-check.sh production basic
```

## Environment-Specific Notes

### Production
- Use blue-green deployment
- Require manual approval for database migrations
- Enable all monitoring and alerting
- Perform extended health checks
- Notify stakeholders of deployment

### Staging
- Test all deployment procedures
- Validate migration scripts
- Verify monitoring configuration
- Test rollback procedures
- Performance testing

### Development
- Simplified deployment process
- Automated testing integration
- Development-specific configurations
- Local monitoring setup

## Emergency Contacts

### Technical Team
- DevOps Lead: devops@aischolar.com
- Backend Team: backend-team@aischolar.com
- Database Admin: dba@aischolar.com
- Security Team: security@aischolar.com

### Escalation
- On-call Engineer: +1-XXX-XXX-XXXX
- Engineering Manager: manager@aischolar.com
- CTO: cto@aischolar.com

## Monitoring and Alerting

### Key Metrics to Monitor
- Service uptime and availability
- API response times and error rates
- Database connection pool status
- Memory and CPU utilization
- Disk space and I/O performance
- Cache hit rates and performance
- External API response times
- User authentication success rates

### Alert Thresholds
- Critical: Service down, database unavailable
- Warning: High response times, elevated error rates
- Info: Deployment notifications, scheduled maintenance

### Dashboards
- Zotero Integration Overview: `/d/zotero-overview`
- System Metrics: `/d/system-metrics`
- Database Performance: `/d/database-performance`
- API Performance: `/d/api-performance`

## Documentation Links

- [Deployment Guide](../DEPLOYMENT_GUIDE.md)
- [Monitoring Setup](../monitoring/README.md)
- [Security Guidelines](../backend/docs/ZOTERO_SECURITY_GUIDELINES.md)
- [Troubleshooting Guide](../docs/zotero/TROUBLESHOOTING_FAQ.md)
- [API Documentation](../docs/API_DOCUMENTATION.md)

## Sign-off

### Pre-Deployment Approval
- [ ] Technical Lead: _________________ Date: _______
- [ ] Security Review: ________________ Date: _______
- [ ] QA Approval: ___________________ Date: _______

### Post-Deployment Verification
- [ ] Deployment Engineer: ____________ Date: _______
- [ ] Monitoring Verified: _____________ Date: _______
- [ ] Stakeholder Notification: ________ Date: _______

---

**Deployment Date:** _______________
**Deployment Version:** _______________
**Deployed By:** _______________
**Environment:** _______________