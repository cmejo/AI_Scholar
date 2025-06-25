#!/bin/bash

# AI Scholar Production Deployment Script
# This script sets up and deploys AI Scholar with production-grade features

set -e

echo "🚀 AI Scholar Production Deployment"
echo "=================================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs uploads monitoring/grafana/dashboards monitoring/grafana/datasources nginx/ssl

# Generate secure secrets if not provided
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(openssl rand -hex 32)
    echo "🔑 Generated SECRET_KEY"
fi

if [ -z "$JWT_SECRET_KEY" ]; then
    export JWT_SECRET_KEY=$(openssl rand -hex 32)
    echo "🔑 Generated JWT_SECRET_KEY"
fi

if [ -z "$GRAFANA_PASSWORD" ]; then
    export GRAFANA_PASSWORD=$(openssl rand -base64 12)
    echo "🔑 Generated Grafana password: $GRAFANA_PASSWORD"
fi

# Create environment file
echo "⚙️ Creating environment configuration..."
cat > .env.production << EOF
# Production Environment Configuration
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY
GRAFANA_PASSWORD=$GRAFANA_PASSWORD

# Database Configuration
POSTGRES_DB=ai_scholar_prod
POSTGRES_USER=ai_scholar
POSTGRES_PASSWORD=$(openssl rand -base64 16)

# Application Configuration
ENVIRONMENT=production
RATE_LIMITING_ENABLED=true
MONITORING_ENABLED=true
LOG_LEVEL=INFO
EOF

echo "✅ Environment configuration created"

# Pull required Docker images
echo "📦 Pulling Docker images..."
docker-compose -f docker-compose.production.yml pull

# Build the application
echo "🔨 Building AI Scholar application..."
docker-compose -f docker-compose.production.yml build ai-scholar

# Start the services
echo "🚀 Starting production services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# Check AI Scholar health
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ AI Scholar is healthy"
else
    echo "❌ AI Scholar health check failed"
fi

# Check Prometheus
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus health check failed"
fi

# Check Grafana
if curl -f http://localhost:3001/api/health > /dev/null 2>&1; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana health check failed"
fi

# Setup Ollama models
echo "🤖 Setting up AI models..."
docker-compose -f docker-compose.production.yml exec -T ollama ollama pull llama2:7b-chat
docker-compose -f docker-compose.production.yml exec -T ollama ollama pull codellama:7b-instruct

# Run production feature tests
echo "🧪 Running production feature tests..."
if python test_production_features.py; then
    echo "✅ Production features test passed"
else
    echo "⚠️ Some production features tests failed"
fi

# Display deployment information
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "📊 Service URLs:"
echo "  AI Scholar:    http://localhost:5000"
echo "  Prometheus:    http://localhost:9090"
echo "  Grafana:       http://localhost:3001 (admin/$GRAFANA_PASSWORD)"
echo "  Metrics:       http://localhost:5000/metrics"
echo ""
echo "🔧 Management Commands:"
echo "  View logs:     docker-compose -f docker-compose.production.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.production.yml down"
echo "  Restart:       docker-compose -f docker-compose.production.yml restart"
echo ""
echo "📈 Monitoring:"
echo "  Health Check:  curl http://localhost:5000/api/health"
echo "  Metrics:       curl http://localhost:5000/metrics"
echo "  Status:        curl -H 'Authorization: Bearer <token>' http://localhost:5000/api/monitoring/status"
echo ""
echo "🔒 Security Features Enabled:"
echo "  ✅ Rate Limiting"
echo "  ✅ Structured Logging"
echo "  ✅ Security Headers"
echo "  ✅ Prometheus Monitoring"
echo "  ✅ Health Checks"
echo ""

# Save deployment info
cat > deployment_info.txt << EOF
AI Scholar Production Deployment
Deployed: $(date)
Grafana Password: $GRAFANA_PASSWORD
Services: AI Scholar, PostgreSQL, Redis, Ollama, Prometheus, Grafana
URLs:
  - AI Scholar: http://localhost:5000
  - Prometheus: http://localhost:9090
  - Grafana: http://localhost:3001
EOF

echo "💾 Deployment information saved to deployment_info.txt"
echo ""
echo "🚀 AI Scholar is now running in production mode with enterprise-grade features!"