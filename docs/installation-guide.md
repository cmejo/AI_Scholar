# Multi-Instance ArXiv System - Installation Guide

## Overview

The Multi-Instance ArXiv System is a comprehensive solution for automated paper collection, processing, and analysis from multiple academic sources. This guide will walk you through the complete installation and setup process.

## System Requirements

### Hardware Requirements
- **CPU**: Minimum 4 cores, recommended 8+ cores
- **RAM**: Minimum 16GB, recommended 32GB+
- **Storage**: Minimum 100GB free space, recommended 500GB+
- **Network**: Stable internet connection with good bandwidth

### Software Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Python**: Version 3.9 or higher
- **Docker**: Version 20.10+ (for ChromaDB)
- **Git**: For cloning the repository

## Pre-Installation Setup

### 1. System Updates
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# macOS
brew update && brew upgrade

# Install essential packages
sudo apt install -y python3-pip python3-venv git curl wget
```

### 2. Docker Installation
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
```

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/multi-instance-arxiv-system.git
cd multi-instance-arxiv-system
```

### 2. Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Additional System Dependencies
```bash
# For PDF processing
sudo apt install -y poppler-utils tesseract-ocr

# For scientific computing
sudo apt install -y libopenblas-dev liblapack-dev

# For ChromaDB dependencies
sudo apt install -y build-essential
```

## Configuration Setup

### 1. Create Configuration Directory
```bash
mkdir -p config
mkdir -p logs
mkdir -p data/{ai_scholar,quant_scholar}
mkdir -p reports
```

### 2. Environment Variables
Create a `.env` file in the project root:
```bash
# Database Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Storage Configuration
BASE_STORAGE_PATH=/path/to/your/data/directory

# API Keys (if needed)
OPENAI_API_KEY=your-openai-key
HUGGINGFACE_API_KEY=your-hf-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/system.log
```

### 3. Instance Configuration Files

#### AI Scholar Configuration
Create `config/ai_scholar.yaml`:
```yaml
instance_name: "ai_scholar"
description: "AI and Machine Learning Papers"

# Storage paths
storage_path: "data/ai_scholar"
papers_path: "data/ai_scholar/papers"
logs_path: "data/ai_scholar/logs"
cache_path: "data/ai_scholar/cache"

# ArXiv categories for AI Scholar
arxiv_categories:
  - "cs.AI"    # Artificial Intelligence
  - "cs.LG"    # Machine Learning
  - "cs.CV"    # Computer Vision
  - "cs.CL"    # Computation and Language
  - "cs.NE"    # Neural and Evolutionary Computing
  - "stat.ML"  # Machine Learning (Statistics)

# Processing settings
processing:
  batch_size: 50
  max_concurrent: 4
  chunk_size: 1000
  chunk_overlap: 200

# Vector store settings
vector_store:
  collection_name: "ai_scholar_papers"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

# Update schedule
schedule:
  monthly_day: 1  # First day of month
  monthly_hour: 2  # 2 AM
```

#### Quant Scholar Configuration
Create `config/quant_scholar.yaml`:
```yaml
instance_name: "quant_scholar"
description: "Quantitative Finance and Statistics Papers"

# Storage paths
storage_path: "data/quant_scholar"
papers_path: "data/quant_scholar/papers"
logs_path: "data/quant_scholar/logs"
cache_path: "data/quant_scholar/cache"

# ArXiv categories for Quant Scholar
arxiv_categories:
  - "q-fin.*"   # All Quantitative Finance
  - "stat.AP"   # Applications (Statistics)
  - "stat.CO"   # Computation (Statistics)
  - "stat.ME"   # Methodology (Statistics)
  - "math.ST"   # Statistics Theory
  - "econ.EM"   # Econometrics

# Journal sources
journal_sources:
  - name: "Journal of Statistical Software"
    handler: "JStatSoftwareHandler"
    base_url: "https://www.jstatsoft.org"
    enabled: true
  
  - name: "R Journal"
    handler: "RJournalHandler"
    base_url: "https://journal.r-project.org"
    enabled: true

# Processing settings
processing:
  batch_size: 30
  max_concurrent: 3
  chunk_size: 1000
  chunk_overlap: 200

# Vector store settings
vector_store:
  collection_name: "quant_scholar_papers"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

# Update schedule
schedule:
  monthly_day: 15  # 15th day of month
  monthly_hour: 3   # 3 AM
```

## Database Setup

### 1. Start ChromaDB
```bash
# Using Docker
docker run -d --name chromadb -p 8000:8000 chromadb/chroma:latest

# Verify ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat
```

### 2. Initialize Collections
```bash
# Initialize vector store collections
python -m backend.multi_instance_arxiv_system.scripts.initialize_collections
```

## Verification and Testing

### 1. Run System Health Check
```bash
python -m backend.multi_instance_arxiv_system.scripts.system_health_check --verbose
```

### 2. Test Instance Configurations
```bash
# Test AI Scholar configuration
python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_downloader --dry-run --limit 5

# Test Quant Scholar configuration
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader --dry-run --limit 5
```

### 3. Run Unit Tests
```bash
# Run all tests
python -m pytest backend/tests/ -v

# Run specific test categories
python -m pytest backend/tests/unit/ -v
python -m pytest backend/tests/integration/ -v
```

## Initial Data Population

### 1. Download Sample Papers
```bash
# Download recent AI papers (last 7 days)
python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_downloader \
  --days 7 --limit 100

# Download recent Quant papers (last 7 days)
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --days 7 --limit 50
```

### 2. Process Downloaded Papers
```bash
# Process AI Scholar papers
python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_processor

# Process Quant Scholar papers
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_processor
```

## Automated Scheduling Setup

### 1. Install Cron Jobs
```bash
# Run the cron setup script
python -m backend.multi_instance_arxiv_system.scripts.cron_setup --install

# Verify cron jobs
crontab -l
```

### 2. Manual Cron Configuration (Alternative)
Add to crontab (`crontab -e`):
```bash
# AI Scholar monthly update (1st of month at 2 AM)
0 2 1 * * /path/to/venv/bin/python -m backend.multi_instance_arxiv_system.scripts.ai_scholar_monthly_update

# Quant Scholar monthly update (15th of month at 3 AM)
0 3 15 * * /path/to/venv/bin/python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_monthly_update

# Daily system monitoring (every day at 6 AM)
0 6 * * * /path/to/venv/bin/python -m backend.multi_instance_arxiv_system.scripts.multi_instance_monitor --send-alerts

# Weekly storage cleanup (Sundays at 1 AM)
0 1 * * 0 /path/to/venv/bin/python -m backend.multi_instance_arxiv_system.scripts.storage_manager cleanup --max-age-days 90
```

## Post-Installation Configuration

### 1. Email Notifications Setup
Test email configuration:
```bash
python -c "
from backend.multi_instance_arxiv_system.reporting.email_notification_service import EmailNotificationService
service = EmailNotificationService()
service.send_test_email('your-email@example.com')
"
```

### 2. Monitoring Setup
```bash
# Start continuous monitoring (optional)
python -m backend.multi_instance_arxiv_system.scripts.multi_instance_monitor \
  --continuous 60 --send-alerts
```

### 3. Storage Management
```bash
# Analyze current storage usage
python -m backend.multi_instance_arxiv_system.scripts.storage_manager analyze

# Set up automated cleanup
python -m backend.multi_instance_arxiv_system.scripts.storage_manager cleanup --dry-run
```

## Troubleshooting Common Issues

### 1. ChromaDB Connection Issues
```bash
# Check if ChromaDB is running
docker ps | grep chromadb

# Restart ChromaDB
docker restart chromadb

# Check logs
docker logs chromadb
```

### 2. Permission Issues
```bash
# Fix file permissions
chmod +x backend/multi_instance_arxiv_system/scripts/*.py
chown -R $USER:$USER data/ logs/ reports/
```

### 3. Python Import Issues
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### 4. PDF Processing Issues
```bash
# Install additional PDF tools
sudo apt install -y ghostscript poppler-utils

# Test PDF processing
python -c "
import fitz  # PyMuPDF
print('PDF processing available')
"
```

## Security Considerations

### 1. File Permissions
```bash
# Secure configuration files
chmod 600 .env config/*.yaml

# Secure log directories
chmod 755 logs/
chmod 644 logs/*.log
```

### 2. Network Security
- Use firewall rules to restrict access to ChromaDB port (8000)
- Use HTTPS for external API calls
- Regularly update dependencies

### 3. API Key Management
- Store API keys in environment variables, not in code
- Use application-specific passwords for email
- Rotate API keys regularly

## Performance Optimization

### 1. System Tuning
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
```

### 2. Database Optimization
```bash
# Configure ChromaDB for better performance
# Add to docker run command: -e CHROMA_SERVER_CORS_ALLOW_ORIGINS="*"
```

### 3. Storage Optimization
```bash
# Set up log rotation
sudo tee /etc/logrotate.d/arxiv-system << EOF
/path/to/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF
```

## Next Steps

After successful installation:

1. **Review Configuration**: Double-check all configuration files
2. **Run Initial Tests**: Execute the test suite to ensure everything works
3. **Monitor System**: Set up monitoring and alerting
4. **Schedule Updates**: Configure automated monthly updates
5. **Backup Setup**: Implement backup procedures for data and configurations

For detailed operational procedures, see the [Configuration Reference](configuration-reference.md) and [Troubleshooting Guide](troubleshooting-guide.md).