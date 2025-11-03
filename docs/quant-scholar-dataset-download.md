# Quant Scholar Dataset Download Guide

## Overview

This guide provides step-by-step instructions for downloading and setting up the Quant Scholar dataset, which includes papers from quantitative finance, statistics, econometrics, and related mathematical fields.

## Quick Start Commands

### 1. Download Recent Papers (Last 30 Days)
```bash
# Activate virtual environment
source venv/bin/activate

# Download recent Quant Scholar papers
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --days 30 --limit 200 --verbose

# Process downloaded papers
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_processor \
  --batch-size 50 --verbose
```

### 2. Download Specific Date Range
```bash
# Download papers from specific date range
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --start-date 2024-01-01 --end-date 2024-01-31 --limit 500
```

### 3. Download by Category
```bash
# Download only quantitative finance papers
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --categories "q-fin.*" --days 60 --limit 300

# Download only statistics papers
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --categories "stat.AP,stat.CO,stat.ME" --days 30 --limit 150
```

## Detailed Download Options

### Command Line Arguments

| Argument | Description | Example | Default |
|----------|-------------|---------|---------|
| `--days` | Download papers from last N days | `--days 30` | 7 |
| `--limit` | Maximum number of papers to download | `--limit 500` | 100 |
| `--start-date` | Start date (YYYY-MM-DD) | `--start-date 2024-01-01` | - |
| `--end-date` | End date (YYYY-MM-DD) | `--end-date 2024-01-31` | - |
| `--categories` | Specific arXiv categories | `--categories "q-fin.*,stat.AP"` | All configured |
| `--journals` | Include journal sources | `--journals` | False |
| `--dry-run` | Test without downloading | `--dry-run` | False |
| `--verbose` | Detailed output | `--verbose` | False |
| `--resume` | Resume interrupted download | `--resume` | False |

### ArXiv Categories for Quant Scholar

#### Quantitative Finance (q-fin)
- `q-fin.CP` - Computational Finance
- `q-fin.EC` - Economics  
- `q-fin.GN` - General Finance
- `q-fin.MF` - Mathematical Finance
- `q-fin.PM` - Portfolio Management
- `q-fin.PR` - Pricing of Securities
- `q-fin.RM` - Risk Management
- `q-fin.ST` - Statistical Finance
- `q-fin.TR` - Trading and Market Microstructure

#### Statistics (stat)
- `stat.AP` - Applications
- `stat.CO` - Computation
- `stat.ME` - Methodology
- `stat.ML` - Machine Learning
- `stat.OT` - Other Statistics
- `stat.TH` - Statistics Theory

#### Mathematics (math)
- `math.ST` - Statistics Theory
- `math.PR` - Probability
- `math.OC` - Optimization and Control

#### Economics (econ)
- `econ.EM` - Econometrics
- `econ.GN` - General Economics
- `econ.TH` - Theoretical Economics

## Journal Sources

### Supported Journals

#### Journal of Statistical Software (JSS)
```bash
# Download from JSS specifically
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --journals --journal-name "Journal of Statistical Software" --limit 100
```

#### R Journal
```bash
# Download from R Journal specifically  
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --journals --journal-name "R Journal" --limit 50
```

#### All Journal Sources
```bash
# Download from all configured journal sources
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --journals --days 90 --limit 200
```

## Download Strategies

### 1. Initial Dataset Setup (Comprehensive)
```bash
# Download comprehensive dataset (last 2 years)
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --days 730 --limit 5000 --journals --verbose

# This will take several hours - run in background
nohup python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --days 730 --limit 5000 --journals --verbose > quant_download.log 2>&1 &
```

### 2. Regular Updates (Monthly)
```bash
# Monthly update (automated via cron)
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_monthly_update
```

### 3. Targeted Collection
```bash
# Focus on specific research areas
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --categories "q-fin.MF,q-fin.RM,q-fin.PM" --days 180 --limit 1000

# Focus on computational methods
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --categories "q-fin.CP,stat.CO" --days 365 --limit 800
```

## Processing Downloaded Papers

### 1. Basic Processing
```bash
# Process all downloaded papers
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_processor
```

### 2. Batch Processing
```bash
# Process in smaller batches (recommended for large datasets)
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_processor \
  --batch-size 25 --max-concurrent 2
```

### 3. Resume Processing
```bash
# Resume interrupted processing
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_processor \
  --resume --skip-existing
```

## Monitoring Download Progress

### 1. Real-time Monitoring
```bash
# Monitor download progress
tail -f data/quant_scholar/logs/downloader.log
```

### 2. Check Download Statistics
```bash
# Check current dataset size
python -c "
from pathlib import Path
papers_dir = Path('data/quant_scholar/papers')
pdf_count = len(list(papers_dir.glob('*.pdf')))
print(f'Downloaded papers: {pdf_count}')
"
```

### 3. Verify Data Integrity
```bash
# Run data integrity check
python -m backend.multi_instance_arxiv_system.scripts.verify_dataset \
  --instance quant_scholar --check-pdfs --check-metadata
```

## Storage Management

### 1. Check Storage Usage
```bash
# Check storage usage by category
python -m backend.multi_instance_arxiv_system.scripts.storage_manager \
  analyze --instance quant_scholar
```

### 2. Cleanup Old Files
```bash
# Clean up cache and temporary files
python -m backend.multi_instance_arxiv_system.scripts.storage_manager \
  cleanup --instance quant_scholar --max-age-days 30
```

### 3. Compress Old Papers
```bash
# Compress papers older than 90 days
python -m backend.multi_instance_arxiv_system.scripts.storage_manager \
  compress --instance quant_scholar --age-threshold 90
```

## Troubleshooting

### 1. Download Failures
```bash
# Check network connectivity
curl -I https://arxiv.org/

# Check arXiv API status
curl "http://export.arxiv.org/api/query?search_query=cat:q-fin.ST&max_results=1"

# Resume failed downloads
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --resume --verbose
```

### 2. Processing Errors
```bash
# Check processing logs
tail -n 100 data/quant_scholar/logs/processor.log

# Skip problematic papers and continue
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_processor \
  --skip-errors --verbose
```

### 3. Storage Issues
```bash
# Check available disk space
df -h data/quant_scholar/

# Clean up if space is low
python -m backend.multi_instance_arxiv_system.scripts.storage_manager \
  emergency-cleanup --instance quant_scholar
```

## Performance Optimization

### 1. Parallel Downloads
```bash
# Increase concurrent downloads (if bandwidth allows)
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --max-concurrent 6 --days 30 --limit 500
```

### 2. Batch Size Tuning
```bash
# Adjust batch size based on available memory
# For 16GB RAM: batch_size = 50
# For 32GB RAM: batch_size = 100
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_processor \
  --batch-size 50
```

### 3. Rate Limiting
```bash
# Respect arXiv rate limits (3 seconds between requests)
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --rate-limit 3 --days 7 --limit 100
```

## Dataset Statistics

After downloading, you can generate statistics:

```bash
# Generate dataset report
python -c "
from backend.multi_instance_arxiv_system.scripts.generate_dataset_report import generate_report
report = generate_report('quant_scholar')
print(report)
"
```

Expected dataset sizes:
- **30 days**: ~200-400 papers (~2-4 GB)
- **1 year**: ~2,000-4,000 papers (~20-40 GB)  
- **2 years**: ~4,000-8,000 papers (~40-80 GB)

## Automated Setup Script

For convenience, here's a complete setup script:

```bash
#!/bin/bash
# quant_scholar_setup.sh

echo "Setting up Quant Scholar dataset..."

# Activate environment
source venv/bin/activate

# Create directories
mkdir -p data/quant_scholar/{papers,logs,cache,reports}

# Download recent papers (last 60 days)
echo "Downloading recent papers..."
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_downloader \
  --days 60 --limit 1000 --journals --verbose

# Process downloaded papers
echo "Processing papers..."
python -m backend.multi_instance_arxiv_system.scripts.quant_scholar_processor \
  --batch-size 50 --verbose

# Generate initial report
echo "Generating report..."
python -m backend.multi_instance_arxiv_system.scripts.generate_dataset_report \
  --instance quant_scholar --output reports/quant_scholar_initial_report.html

echo "Quant Scholar dataset setup complete!"
echo "Check reports/quant_scholar_initial_report.html for details."
```

Make it executable and run:
```bash
chmod +x quant_scholar_setup.sh
./quant_scholar_setup.sh
```

## Next Steps

After downloading the dataset:

1. **Verify Data Quality**: Run integrity checks
2. **Set Up Monitoring**: Configure automated monitoring
3. **Schedule Updates**: Set up monthly automated updates
4. **Backup Data**: Implement backup procedures
5. **Explore Data**: Use the search and analysis tools

For more information, see:
- [Configuration Reference](configuration-reference.md)
- [Troubleshooting Guide](troubleshooting-guide.md)
- [User Guide](USER_GUIDE.md)