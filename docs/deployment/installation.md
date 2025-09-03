# 🚀 AI Scholar Installation & Deployment Guide

## Complete Setup Instructions for Self-Hosted Deployment

This guide will walk you through deploying AI Scholar on your own infrastructure, giving you complete control over your research data and unlimited customization capabilities.

## 📋 **System Requirements**

### **Minimum Requirements**
```
Hardware:
├── CPU: 8 cores (Intel Xeon or AMD EPYC recommended)
├── RAM: 32GB DDR4
├── Storage: 1TB NVMe SSD
├── GPU: NVIDIA RTX 3080 or better (optional but recommended)
└── Network: 1Gbps internet connection

Software:
├── OS: Ubuntu 20.04 LTS or CentOS 8
├── Docker: 20.10+ with Docker Compose
├── Python: 3.9+
├── Node.js: 16+
└── PostgreSQL: 13+
```

### **Recommended Production Setup**
```
Hardware:
├── CPU: 32 cores (Intel Xeon Platinum or AMD EPYC)
├── RAM: 128GB DDR4 ECC
├── Storage: 10TB NVMe SSD RAID 10
├── GPU: Multiple NVIDIA A100 or H100
└── Network: 10Gbps with redundancy

Software:
├── OS: Ubuntu 22.04 LTS
├── Kubernetes: 1.25+
├── Docker: 24.0+
├── PostgreSQL: 15+ with clustering
└── Redis: 7.0+ with clustering
```

### **Enterprise Kubernetes Setup**
```
Cluster Configuration:
├── Master Nodes: 3x (16 cores, 64GB RAM each)
├── Worker Nodes: 6x (32 cores, 128GB RAM each)
├── GPU Nodes: 4x (64 cores, 256GB RAM, 8x A100 each)
├── Storage: Distributed storage with 100TB capacity
└── Network: 25Gbps with load balancing
```

## 🐳 **Quick Start with Docker**

### **1. Clone Repository**
```bash
# Clone the main repository
git clone https://github.com/ai-scholar/platform.git
cd platform

# Verify you have the latest version
git checkout main
git pull origin main
```

### **2. Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (see configuration section below)
nano .env
```

### **3. Docker Compose Deployment**
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Access the application
open http://localhost:3000
```

### **4. Initial Setup**
```bash
# Run database migrations
docker-compose exec backend python manage.py migrate

# Create superuser account
docker-compose exec backend python manage.py createsuperuser

# Load initial data
docker-compose exec backend python manage.py loaddata initial_data.json

# Start AI model downloads (this may take 30-60 minutes)
docker-compose exec backend python manage.py download_models
```

## ⚙️ **Configuration**

### **Environment Variables (.env)**
```bash
# Basic Configuration
APP_NAME=AI Scholar
APP_ENV=production
DEBUG=false
SECRET_KEY=your-super-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://aischolar:password@postgres:5432/aischolar
REDIS_URL=redis://redis:6379/0

# AI Model Configuration
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key

# Blockchain Configuration
BLOCKCHAIN_NETWORK=mainnet
BLOCKCHAIN_RPC_URL=https://your-blockchain-node.com
PRIVATE_KEY=your-blockchain-private-key

# Storage Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket
AWS_S3_REGION_NAME=us-east-1

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=true

# Security Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com

# Feature Flags
ENABLE_VR_FEATURES=true
ENABLE_BLOCKCHAIN=true
ENABLE_MULTILINGUAL=true
ENABLE_AI_ASSISTANT=true

# Performance Configuration
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
CACHE_BACKEND=redis://redis:6379/3

# Monitoring Configuration
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### **Advanced Configuration Files**

**config/ai_models.yaml**
```yaml
models:
  research_assistant:
    model_name: "ai-scholar/research-assistant-v2"
    model_type: "transformer"
    gpu_memory: "16GB"
    batch_size: 32
    
  multilingual_translator:
    model_name: "ai-scholar/multilingual-translator-v1"
    model_type: "seq2seq"
    supported_languages: 17
    gpu_memory: "8GB"
    
  knowledge_graph:
    model_name: "ai-scholar/knowledge-graph-v1"
    model_type: "graph_neural_network"
    embedding_dim: 768
    gpu_memory: "12GB"

inference:
  max_concurrent_requests: 100
  timeout_seconds: 300
  auto_scaling: true
  min_replicas: 2
  max_replicas: 10
```

**config/blockchain.yaml**
```yaml
network:
  name: "ai-scholar-mainnet"
  chain_id: 12345
  consensus: "proof-of-authority"
  block_time: 15
  
validators:
  - name: "MIT"
    address: "0x1234567890123456789012345678901234567890"
    stake: 10000
  - name: "Stanford"
    address: "0x2345678901234567890123456789012345678901"
    stake: 10000
  - name: "Oxford"
    address: "0x3456789012345678901234567890123456789012"
    stake: 10000

smart_contracts:
  research_registry: "0x4567890123456789012345678901234567890123"
  peer_review: "0x5678901234567890123456789012345678901234"
  collaboration: "0x6789012345678901234567890123456789012345"
```

## 🏗️ **Production Deployment**

### **1. Kubernetes Deployment**

**namespace.yaml**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-scholar
  labels:
    name: ai-scholar
```

**configmap.yaml**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-scholar-config
  namespace: ai-scholar
data:
  DATABASE_URL: "postgresql://aischolar:password@postgres:5432/aischolar"
  REDIS_URL: "redis://redis:6379/0"
  APP_ENV: "production"
  DEBUG: "false"
```

**deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-scholar-backend
  namespace: ai-scholar
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-scholar-backend
  template:
    metadata:
      labels:
        app: ai-scholar-backend
    spec:
      containers:
      - name: backend
        image: aischolar/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: ai-scholar-config
        - secretRef:
            name: ai-scholar-secrets
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-scholar-backend-service
  namespace: ai-scholar
spec:
  selector:
    app: ai-scholar-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

**ingress.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-scholar-ingress
  namespace: ai-scholar
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: ai-scholar-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-scholar-backend-service
            port:
              number: 80
```

### **2. Deploy to Kubernetes**
```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check deployment status
kubectl get pods -n ai-scholar
kubectl get services -n ai-scholar
kubectl get ingress -n ai-scholar

# View logs
kubectl logs -f deployment/ai-scholar-backend -n ai-scholar
```

### **3. Database Setup**

**PostgreSQL with High Availability**
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
  namespace: ai-scholar
spec:
  instances: 3
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      maintenance_work_mem: "64MB"
      checkpoint_completion_target: "0.9"
      wal_buffers: "16MB"
      default_statistics_target: "100"
      random_page_cost: "1.1"
      effective_io_concurrency: "200"
      
  bootstrap:
    initdb:
      database: aischolar
      owner: aischolar
      secret:
        name: postgres-credentials
        
  storage:
    size: 1Ti
    storageClass: fast-ssd
    
  monitoring:
    enabled: true
    
  backup:
    retentionPolicy: "30d"
    barmanObjectStore:
      destinationPath: "s3://your-backup-bucket/postgres"
      s3Credentials:
        accessKeyId:
          name: backup-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-credentials
          key: SECRET_ACCESS_KEY
```

### **4. Redis Cluster Setup**
```yaml
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: RedisCluster
metadata:
  name: redis-cluster
  namespace: ai-scholar
spec:
  clusterSize: 6
  kubernetesConfig:
    image: redis:7.0
    imagePullPolicy: IfNotPresent
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 1000m
        memory: 1Gi
  storage:
    volumeClaimTemplate:
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
        storageClassName: fast-ssd
```

## 🤖 **AI Model Setup**

### **1. Model Download and Configuration**
```bash
# Create models directory
mkdir -p /opt/ai-scholar/models

# Download pre-trained models
python scripts/download_models.py --models all --path /opt/ai-scholar/models

# Verify model integrity
python scripts/verify_models.py --path /opt/ai-scholar/models
```

### **2. GPU Configuration**
```yaml
# gpu-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-scholar-gpu-worker
  namespace: ai-scholar
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-scholar-gpu-worker
  template:
    metadata:
      labels:
        app: ai-scholar-gpu-worker
    spec:
      containers:
      - name: gpu-worker
        image: aischolar/gpu-worker:latest
        resources:
          limits:
            nvidia.com/gpu: 1
          requests:
            nvidia.com/gpu: 1
        env:
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        volumeMounts:
        - name: model-storage
          mountPath: /models
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: model-storage-pvc
```

### **3. Model Serving with TensorRT**
```python
# scripts/optimize_models.py
import tensorrt as trt
import torch
from transformers import AutoModel

def optimize_model_for_inference(model_path: str, output_path: str):
    """Optimize model for production inference"""
    
    # Load model
    model = AutoModel.from_pretrained(model_path)
    model.eval()
    
    # Convert to TensorRT
    with torch.no_grad():
        # Create example input
        example_input = torch.randint(0, 1000, (1, 512))
        
        # Trace model
        traced_model = torch.jit.trace(model, example_input)
        
        # Convert to TensorRT
        trt_model = torch.jit.script(traced_model)
        
        # Save optimized model
        trt_model.save(output_path)
    
    print(f"Model optimized and saved to {output_path}")

# Optimize all models
models = [
    "research-assistant",
    "multilingual-translator", 
    "knowledge-graph",
    "peer-review-assistant"
]

for model in models:
    optimize_model_for_inference(
        f"/models/{model}",
        f"/models/{model}-optimized.pt"
    )
```

## 🔒 **Security Configuration**

### **1. SSL/TLS Setup**
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Create cluster issuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@your-domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### **2. Network Security**
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-scholar-network-policy
  namespace: ai-scholar
spec:
  podSelector:
    matchLabels:
      app: ai-scholar-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: ai-scholar
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
```

### **3. Secrets Management**
```bash
# Create secrets
kubectl create secret generic ai-scholar-secrets \
  --from-literal=SECRET_KEY="your-super-secret-key" \
  --from-literal=DATABASE_PASSWORD="your-db-password" \
  --from-literal=OPENAI_API_KEY="your-openai-key" \
  --from-literal=AWS_SECRET_ACCESS_KEY="your-aws-secret" \
  -n ai-scholar

# Create TLS secret for blockchain
kubectl create secret tls blockchain-tls \
  --cert=blockchain.crt \
  --key=blockchain.key \
  -n ai-scholar
```

## 📊 **Monitoring and Observability**

### **1. Prometheus Setup**
```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: ai-scholar
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'ai-scholar-backend'
      static_configs:
      - targets: ['ai-scholar-backend-service:80']
      metrics_path: /metrics
    - job_name: 'ai-scholar-gpu-worker'
      static_configs:
      - targets: ['ai-scholar-gpu-worker-service:80']
      metrics_path: /metrics
    - job_name: 'postgres'
      static_configs:
      - targets: ['postgres-exporter:9187']
    - job_name: 'redis'
      static_configs:
      - targets: ['redis-exporter:9121']
```

### **2. Grafana Dashboards**
```json
{
  "dashboard": {
    "title": "AI Scholar Performance",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "AI Model Inference Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ai_inference_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "type": "graph",
        "targets": [
          {
            "expr": "nvidia_gpu_utilization_gpu",
            "legendFormat": "GPU {{gpu}}"
          }
        ]
      }
    ]
  }
}
```

### **3. Logging Configuration**
```yaml
# fluentd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: ai-scholar
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*ai-scholar*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
      time_format %Y-%m-%dT%H:%M:%S.%NZ
    </source>
    
    <filter kubernetes.**>
      @type kubernetes_metadata
    </filter>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name ai-scholar
      type_name _doc
    </match>
```

## 🔧 **Maintenance and Updates**

### **1. Backup Strategy**
```bash
#!/bin/bash
# backup.sh - Automated backup script

# Database backup
kubectl exec -n ai-scholar postgres-cluster-1 -- pg_dump -U aischolar aischolar > backup-$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).sql s3://your-backup-bucket/database/

# Model backup
kubectl exec -n ai-scholar deployment/ai-scholar-backend -- tar -czf models-backup-$(date +%Y%m%d).tar.gz /models
kubectl cp ai-scholar/ai-scholar-backend-xxx:/models-backup-$(date +%Y%m%d).tar.gz ./
aws s3 cp models-backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/models/

# Configuration backup
kubectl get all -n ai-scholar -o yaml > k8s-config-$(date +%Y%m%d).yaml
aws s3 cp k8s-config-$(date +%Y%m%d).yaml s3://your-backup-bucket/config/

# Cleanup local files older than 7 days
find . -name "backup-*.sql" -mtime +7 -delete
find . -name "models-backup-*.tar.gz" -mtime +7 -delete
find . -name "k8s-config-*.yaml" -mtime +7 -delete
```

### **2. Update Procedure**
```bash
#!/bin/bash
# update.sh - Rolling update script

# Pull latest images
docker pull aischolar/backend:latest
docker pull aischolar/frontend:latest
docker pull aischolar/gpu-worker:latest

# Update deployments with zero downtime
kubectl set image deployment/ai-scholar-backend backend=aischolar/backend:latest -n ai-scholar
kubectl set image deployment/ai-scholar-frontend frontend=aischolar/frontend:latest -n ai-scholar
kubectl set image deployment/ai-scholar-gpu-worker gpu-worker=aischolar/gpu-worker:latest -n ai-scholar

# Wait for rollout to complete
kubectl rollout status deployment/ai-scholar-backend -n ai-scholar
kubectl rollout status deployment/ai-scholar-frontend -n ai-scholar
kubectl rollout status deployment/ai-scholar-gpu-worker -n ai-scholar

# Run database migrations if needed
kubectl exec -n ai-scholar deployment/ai-scholar-backend -- python manage.py migrate

# Verify deployment
kubectl get pods -n ai-scholar
curl -f https://your-domain.com/health || echo "Health check failed!"
```

### **3. Disaster Recovery**
```bash
#!/bin/bash
# disaster-recovery.sh - Complete system recovery

# Restore database
kubectl exec -n ai-scholar postgres-cluster-1 -- psql -U aischolar -d aischolar < backup-latest.sql

# Restore models
kubectl cp models-backup-latest.tar.gz ai-scholar/ai-scholar-backend-xxx:/tmp/
kubectl exec -n ai-scholar deployment/ai-scholar-backend -- tar -xzf /tmp/models-backup-latest.tar.gz -C /

# Restore configuration
kubectl apply -f k8s-config-latest.yaml

# Restart all services
kubectl rollout restart deployment -n ai-scholar

# Verify recovery
./scripts/health-check.sh
```

## 🚀 **Performance Optimization**

### **1. Auto-scaling Configuration**
```yaml
# hpa.yaml - Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-scholar-backend-hpa
  namespace: ai-scholar
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-scholar-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: ai_inference_queue_length
      target:
        type: AverageValue
        averageValue: "10"
```

### **2. Caching Strategy**
```yaml
# redis-cache-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-cache-config
  namespace: ai-scholar
data:
  redis.conf: |
    maxmemory 8gb
    maxmemory-policy allkeys-lru
    save 900 1
    save 300 10
    save 60 10000
    appendonly yes
    appendfsync everysec
    tcp-keepalive 300
    timeout 0
```

### **3. Database Optimization**
```sql
-- database-optimization.sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_papers_topic ON papers USING GIN(to_tsvector('english', title || ' ' || abstract));
CREATE INDEX CONCURRENTLY idx_papers_date ON papers(publication_date DESC);
CREATE INDEX CONCURRENTLY idx_citations_paper_id ON citations(paper_id);
CREATE INDEX CONCURRENTLY idx_authors_name ON authors(name);

-- Optimize PostgreSQL settings
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();
```

## 🎯 **Troubleshooting**

### **Common Issues and Solutions**

**1. Out of Memory Errors**
```bash
# Check memory usage
kubectl top pods -n ai-scholar

# Increase memory limits
kubectl patch deployment ai-scholar-backend -n ai-scholar -p '{"spec":{"template":{"spec":{"containers":[{"name":"backend","resources":{"limits":{"memory":"16Gi"}}}]}}}}'

# Enable memory monitoring
kubectl apply -f monitoring/memory-alerts.yaml
```

**2. GPU Not Detected**
```bash
# Check GPU availability
kubectl describe nodes | grep nvidia.com/gpu

# Install NVIDIA device plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Verify GPU pods
kubectl get pods -n kube-system | grep nvidia
```

**3. Database Connection Issues**
```bash
# Check database status
kubectl get pods -n ai-scholar | grep postgres

# Test connection
kubectl exec -n ai-scholar deployment/ai-scholar-backend -- python -c "
import psycopg2
conn = psycopg2.connect('postgresql://aischolar:password@postgres:5432/aischolar')
print('Database connection successful')
"

# Check database logs
kubectl logs -n ai-scholar postgres-cluster-1
```

**4. Model Loading Failures**
```bash
# Check model files
kubectl exec -n ai-scholar deployment/ai-scholar-backend -- ls -la /models/

# Re-download models
kubectl exec -n ai-scholar deployment/ai-scholar-backend -- python scripts/download_models.py --force

# Check GPU memory
kubectl exec -n ai-scholar deployment/ai-scholar-gpu-worker -- nvidia-smi
```

### **Health Check Scripts**
```bash
#!/bin/bash
# health-check.sh - Comprehensive health check

echo "=== AI Scholar Health Check ==="

# Check pod status
echo "Checking pod status..."
kubectl get pods -n ai-scholar

# Check service endpoints
echo "Checking service endpoints..."
kubectl get endpoints -n ai-scholar

# Test API endpoints
echo "Testing API endpoints..."
curl -f https://your-domain.com/health || echo "❌ Health endpoint failed"
curl -f https://your-domain.com/api/v1/status || echo "❌ API status failed"

# Check database connectivity
echo "Testing database connectivity..."
kubectl exec -n ai-scholar deployment/ai-scholar-backend -- python -c "
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('✅ Database connection successful')
" || echo "❌ Database connection failed"

# Check Redis connectivity
echo "Testing Redis connectivity..."
kubectl exec -n ai-scholar deployment/ai-scholar-backend -- python -c "
import redis
r = redis.Redis(host='redis', port=6379, db=0)
r.ping()
print('✅ Redis connection successful')
" || echo "❌ Redis connection failed"

# Check AI model status
echo "Testing AI model status..."
curl -f https://your-domain.com/api/v1/models/status || echo "❌ AI models not ready"

echo "=== Health Check Complete ==="
```

---

## 🎉 **Conclusion**

You now have a complete AI Scholar installation running on your infrastructure! This setup provides:

- **Complete Data Control**: Your research data never leaves your servers
- **Unlimited Scalability**: Auto-scaling based on demand
- **High Availability**: Redundant systems with automatic failover
- **Enterprise Security**: End-to-end encryption and compliance
- **Custom Integration**: Full API access for custom development

### **Next Steps**

1. **Configure Custom Datasets**: Add your institutional research data
2. **Set Up User Authentication**: Integrate with your SSO system
3. **Customize AI Models**: Train models on your specific research domains
4. **Monitor Performance**: Set up alerts and monitoring dashboards
5. **Plan Backups**: Implement automated backup and disaster recovery

### **Support and Resources**

- **Documentation**: [https://docs.aischolar.com](https://docs.aischolar.com)
- **Community Forum**: [https://community.aischolar.com](https://community.aischolar.com)
- **GitHub Issues**: [https://github.com/ai-scholar/platform/issues](https://github.com/ai-scholar/platform/issues)
- **Enterprise Support**: [enterprise@aischolar.com](mailto:enterprise@aischolar.com)

**Your AI Scholar deployment is ready to revolutionize research at your institution!**