# Multi-Instance ArXiv System - Configuration Reference

## Overview

This document provides comprehensive reference for all configuration options available in the Multi-Instance ArXiv System. The system uses YAML configuration files for instance-specific settings and environment variables for system-wide configuration.

## Environment Variables

### Core System Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BASE_STORAGE_PATH` | Base directory for all data storage | `./data` | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |
| `LOG_FILE` | Path to main log file | `logs/system.log` | No |
| `CONFIG_DIR` | Directory containing instance configurations | `config` | No |

### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CHROMA_HOST` | ChromaDB server hostname | `localhost` | No |
| `CHROMA_PORT` | ChromaDB server port | `8000` | No |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB persistence directory | `./chroma_db` | No |

### Email Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SMTP_HOST` | SMTP server hostname | - | Yes* |
| `SMTP_PORT` | SMTP server port | `587` | No |
| `SMTP_USERNAME` | SMTP username/email | - | Yes* |
| `SMTP_PASSWORD` | SMTP password/app password | - | Yes* |
| `SMTP_USE_TLS` | Enable TLS encryption | `true` | No |
| `EMAIL_FROM` | Default sender email address | `SMTP_USERNAME` | No |

*Required only if email notifications are enabled

### API Keys

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | - | No** |
| `HUGGINGFACE_API_KEY` | Hugging Face API key | - | No** |

**Required only if using specific embedding models

### Performance Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAX_CONCURRENT_DOWNLOADS` | Maximum concurrent downloads | `4` | No |
| `MAX_CONCURRENT_PROCESSING` | Maximum concurrent processing | `2` | No |
| `MEMORY_LIMIT_GB` | Memory limit in GB | `8` | No |
| `DISK_SPACE_THRESHOLD_GB` | Disk space warning threshold | `10` | No |

## Instance Configuration Files

Instance configurations are stored in YAML files within the `config/` directory. Each instance requires its own configuration file.

### Basic Instance Structure

```yaml
# Instance identification
instance_name: "instance_name"
description: "Human-readable description"

# Storage configuration
storage_path: "path/to/instance/data"
papers_path: "path/to/papers"
logs_path: "path/to/logs"
cache_path: "path/to/cache"
reports_path: "path/to/reports"

# Source configuration
arxiv_categories: []
journal_sources: []

# Processing configuration
processing:
  batch_size: 50
  max_concurrent: 4
  chunk_size: 1000
  chunk_overlap: 200
  
# Vector store configuration
vector_store:
  collection_name: "collection_name"
  embedding_model: "model_name"
  
# Scheduling configuration
schedule:
  monthly_day: 1
  monthly_hour: 2
```

### Storage Configuration

#### storage_path
- **Type**: String
- **Description**: Base directory for all instance data
- **Example**: `"data/ai_scholar"`
- **Required**: Yes

#### papers_path
- **Type**: String
- **Description**: Directory for storing downloaded papers
- **Example**: `"data/ai_scholar/papers"`
- **Default**: `{storage_path}/papers`

#### logs_path
- **Type**: String
- **Description**: Directory for instance-specific logs
- **Example**: `"data/ai_scholar/logs"`
- **Default**: `{storage_path}/logs`

#### cache_path
- **Type**: String
- **Description**: Directory for temporary and cache files
- **Example**: `"data/ai_scholar/cache"`
- **Default**: `{storage_path}/cache`

#### reports_path
- **Type**: String
- **Description**: Directory for generated reports
- **Example**: `"data/ai_scholar/reports"`
- **Default**: `{storage_path}/reports`

### ArXiv Categories Configuration

#### arxiv_categories
- **Type**: List of strings
- **Description**: ArXiv categories to monitor and download
- **Supports**: Exact matches and wildcards (*)
- **Examples**:
  ```yaml
  arxiv_categories:
    - "cs.AI"      # Exact category
    - "cs.LG"      # Machine Learning
    - "q-fin.*"    # All Quantitative Finance
    - "stat.*"     # All Statistics
  ```

#### Common ArXiv Categories

**Computer Science:**
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CV` - Computer Vision and Pattern Recognition
- `cs.CL` - Computation and Language
- `cs.NE` - Neural and Evolutionary Computing
- `cs.IR` - Information Retrieval
- `cs.RO` - Robotics

**Mathematics:**
- `math.ST` - Statistics Theory
- `math.PR` - Probability
- `math.OC` - Optimization and Control

**Statistics:**
- `stat.ML` - Machine Learning
- `stat.AP` - Applications
- `stat.CO` - Computation
- `stat.ME` - Methodology

**Quantitative Finance:**
- `q-fin.CP` - Computational Finance
- `q-fin.MF` - Mathematical Finance
- `q-fin.PM` - Portfolio Management
- `q-fin.RM` - Risk Management
- `q-fin.ST` - Statistical Finance
- `q-fin.TR` - Trading and Market Microstructure

**Economics:**
- `econ.EM` - Econometrics
- `econ.GN` - General Economics
- `econ.TH` - Theoretical Economics

### Journal Sources Configuration

#### journal_sources
- **Type**: List of objects
- **Description**: Configuration for non-ArXiv journal sources
- **Structure**:
  ```yaml
  journal_sources:
    - name: "Journal Name"
      handler: "HandlerClassName"
      base_url: "https://journal.url"
      enabled: true
      settings:
        key: value
  ```

#### Supported Journal Handlers

**JStatSoftwareHandler**
```yaml
- name: "Journal of Statistical Software"
  handler: "JStatSoftwareHandler"
  base_url: "https://www.jstatsoft.org"
  enabled: true
  settings:
    max_papers_per_issue: 50
    include_code: true
```

**RJournalHandler**
```yaml
- name: "R Journal"
  handler: "RJournalHandler"
  base_url: "https://journal.r-project.org"
  enabled: true
  settings:
    max_papers_per_volume: 100
    include_supplements: true
```

### Processing Configuration

#### processing.batch_size
- **Type**: Integer
- **Description**: Number of papers to process in each batch
- **Range**: 1-200
- **Default**: 50
- **Recommendation**: 30-100 depending on system resources

#### processing.max_concurrent
- **Type**: Integer
- **Description**: Maximum concurrent processing threads
- **Range**: 1-16
- **Default**: 4
- **Recommendation**: Number of CPU cores / 2

#### processing.chunk_size
- **Type**: Integer
- **Description**: Size of text chunks for vector storage
- **Range**: 100-2000
- **Default**: 1000
- **Unit**: Characters

#### processing.chunk_overlap
- **Type**: Integer
- **Description**: Overlap between consecutive chunks
- **Range**: 0-500
- **Default**: 200
- **Unit**: Characters

#### processing.skip_existing
- **Type**: Boolean
- **Description**: Skip papers that are already processed
- **Default**: true

#### processing.validate_pdfs
- **Type**: Boolean
- **Description**: Validate PDF files before processing
- **Default**: true

### Vector Store Configuration

#### vector_store.collection_name
- **Type**: String
- **Description**: Name of the ChromaDB collection
- **Pattern**: `{instance_name}_papers`
- **Example**: `"ai_scholar_papers"`
- **Required**: Yes

#### vector_store.embedding_model
- **Type**: String
- **Description**: Embedding model to use
- **Options**:
  - `"sentence-transformers/all-MiniLM-L6-v2"` (Default, fast)
  - `"sentence-transformers/all-mpnet-base-v2"` (Better quality)
  - `"text-embedding-ada-002"` (OpenAI, requires API key)
- **Default**: `"sentence-transformers/all-MiniLM-L6-v2"`

#### vector_store.distance_metric
- **Type**: String
- **Description**: Distance metric for similarity search
- **Options**: `"cosine"`, `"euclidean"`, `"manhattan"`
- **Default**: `"cosine"`

#### vector_store.max_documents
- **Type**: Integer
- **Description**: Maximum documents in collection (0 = unlimited)
- **Default**: 0

### Scheduling Configuration

#### schedule.monthly_day
- **Type**: Integer
- **Description**: Day of month for automated updates
- **Range**: 1-28
- **Default**: 1
- **Note**: Use 1-28 to avoid month-end issues

#### schedule.monthly_hour
- **Type**: Integer
- **Description**: Hour of day for automated updates (24-hour format)
- **Range**: 0-23
- **Default**: 2

#### schedule.enabled
- **Type**: Boolean
- **Description**: Enable automated scheduling
- **Default**: true

#### schedule.timezone
- **Type**: String
- **Description**: Timezone for scheduling
- **Default**: System timezone
- **Example**: `"UTC"`, `"America/New_York"`

### Notification Configuration

#### notifications.email.enabled
- **Type**: Boolean
- **Description**: Enable email notifications
- **Default**: true

#### notifications.email.recipients
- **Type**: List of strings
- **Description**: Email addresses for notifications
- **Example**: `["admin@example.com", "user@example.com"]`

#### notifications.email.on_success
- **Type**: Boolean
- **Description**: Send notifications on successful updates
- **Default**: true

#### notifications.email.on_error
- **Type**: Boolean
- **Description**: Send notifications on errors
- **Default**: true

#### notifications.email.on_warning
- **Type**: Boolean
- **Description**: Send notifications on warnings
- **Default**: false

### Error Handling Configuration

#### error_handling.max_retries
- **Type**: Integer
- **Description**: Maximum retry attempts for failed operations
- **Range**: 0-10
- **Default**: 3

#### error_handling.retry_delay
- **Type**: Integer
- **Description**: Delay between retries in seconds
- **Range**: 1-300
- **Default**: 60

#### error_handling.exponential_backoff
- **Type**: Boolean
- **Description**: Use exponential backoff for retries
- **Default**: true

#### error_handling.skip_on_error
- **Type**: Boolean
- **Description**: Skip problematic papers and continue processing
- **Default**: true

### Storage Management Configuration

#### storage.cleanup.enabled
- **Type**: Boolean
- **Description**: Enable automated storage cleanup
- **Default**: true

#### storage.cleanup.max_age_days
- **Type**: Integer
- **Description**: Maximum age for temporary files
- **Range**: 1-365
- **Default**: 30

#### storage.cleanup.min_free_space_gb
- **Type**: Float
- **Description**: Minimum free space to maintain
- **Range**: 1.0-100.0
- **Default**: 10.0

#### storage.compression.enabled
- **Type**: Boolean
- **Description**: Enable compression for old files
- **Default**: true

#### storage.compression.age_threshold_days
- **Type**: Integer
- **Description**: Age threshold for compression
- **Range**: 1-365
- **Default**: 7

## Configuration Validation

The system automatically validates configuration files on startup. Common validation errors:

### Required Fields Missing
```
Error: Missing required field 'instance_name' in config file
```

### Invalid Values
```
Error: batch_size must be between 1 and 200, got 500
```

### Path Issues
```
Error: storage_path '/invalid/path' does not exist or is not writable
```

### Category Format Issues
```
Error: Invalid arXiv category format 'invalid-category'
```

## Configuration Examples

### Minimal Configuration
```yaml
instance_name: "minimal_instance"
storage_path: "data/minimal"
arxiv_categories:
  - "cs.AI"
```

### Full AI Scholar Configuration
```yaml
instance_name: "ai_scholar"
description: "Comprehensive AI and ML paper collection"

storage_path: "data/ai_scholar"
papers_path: "data/ai_scholar/papers"
logs_path: "data/ai_scholar/logs"
cache_path: "data/ai_scholar/cache"
reports_path: "data/ai_scholar/reports"

arxiv_categories:
  - "cs.AI"
  - "cs.LG"
  - "cs.CV"
  - "cs.CL"
  - "cs.NE"
  - "stat.ML"

processing:
  batch_size: 100
  max_concurrent: 6
  chunk_size: 1200
  chunk_overlap: 240
  skip_existing: true
  validate_pdfs: true

vector_store:
  collection_name: "ai_scholar_papers"
  embedding_model: "sentence-transformers/all-mpnet-base-v2"
  distance_metric: "cosine"
  max_documents: 0

schedule:
  monthly_day: 1
  monthly_hour: 2
  enabled: true
  timezone: "UTC"

notifications:
  email:
    enabled: true
    recipients:
      - "ai-team@company.com"
    on_success: true
    on_error: true
    on_warning: false

error_handling:
  max_retries: 5
  retry_delay: 120
  exponential_backoff: true
  skip_on_error: true

storage:
  cleanup:
    enabled: true
    max_age_days: 60
    min_free_space_gb: 20.0
  compression:
    enabled: true
    age_threshold_days: 14
```

### Full Quant Scholar Configuration
```yaml
instance_name: "quant_scholar"
description: "Quantitative Finance and Statistics papers"

storage_path: "data/quant_scholar"

arxiv_categories:
  - "q-fin.*"
  - "stat.AP"
  - "stat.CO"
  - "stat.ME"
  - "math.ST"
  - "econ.EM"

journal_sources:
  - name: "Journal of Statistical Software"
    handler: "JStatSoftwareHandler"
    base_url: "https://www.jstatsoft.org"
    enabled: true
    settings:
      max_papers_per_issue: 50
      include_code: true
  
  - name: "R Journal"
    handler: "RJournalHandler"
    base_url: "https://journal.r-project.org"
    enabled: true
    settings:
      max_papers_per_volume: 100
      include_supplements: true

processing:
  batch_size: 50
  max_concurrent: 4
  chunk_size: 1000
  chunk_overlap: 200

vector_store:
  collection_name: "quant_scholar_papers"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

schedule:
  monthly_day: 15
  monthly_hour: 3
  enabled: true

notifications:
  email:
    enabled: true
    recipients:
      - "quant-team@company.com"
    on_success: true
    on_error: true

storage:
  cleanup:
    enabled: true
    max_age_days: 90
    min_free_space_gb: 15.0
```

## Configuration Best Practices

### 1. Resource Allocation
- Set `max_concurrent` to half your CPU cores
- Set `batch_size` based on available memory (50-100 for 16GB RAM)
- Monitor disk space and adjust `min_free_space_gb` accordingly

### 2. Scheduling
- Stagger instance schedules to avoid resource conflicts
- Use different days/hours for different instances
- Consider timezone for scheduling

### 3. Storage Management
- Enable cleanup and compression for production systems
- Set appropriate age thresholds based on usage patterns
- Monitor storage usage regularly

### 4. Error Handling
- Enable `skip_on_error` for production systems
- Set reasonable retry limits to avoid infinite loops
- Use exponential backoff for network operations

### 5. Security
- Store sensitive configuration in environment variables
- Use restrictive file permissions for config files
- Regularly rotate API keys and passwords

## Troubleshooting Configuration Issues

### Configuration File Not Found
```bash
# Check file exists and is readable
ls -la config/instance_name.yaml
```

### Invalid YAML Syntax
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/instance_name.yaml'))"
```

### Permission Issues
```bash
# Fix file permissions
chmod 644 config/*.yaml
chmod 755 data/
```

### Path Issues
```bash
# Create missing directories
mkdir -p data/instance_name/{papers,logs,cache,reports}
```

For more troubleshooting information, see the [Troubleshooting Guide](troubleshooting-guide.md).