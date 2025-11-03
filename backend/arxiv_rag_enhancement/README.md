# arXiv RAG Enhancement System

A comprehensive system for enhancing the AI Scholar RAG (Retrieval-Augmented Generation) chatbot with arXiv scientific papers. This system provides three powerful scripts for processing, downloading, and automatically updating your knowledge base with the latest research.

## 🚀 Features

### Three Processing Scripts

1. **Local Dataset Processor** (`process_local_arxiv_dataset.py`)
   - Process existing PDFs from local directories
   - Resume interrupted processing
   - Real-time progress tracking
   - Comprehensive error handling

2. **Bulk arXiv Downloader** (`download_bulk_arxiv_papers.py`)
   - Download papers from arXiv's bulk data repository
   - Filter by categories and date ranges
   - Duplicate detection
   - Concurrent downloads with rate limiting

3. **Monthly Auto-Updater** (`run_monthly_update.py`)
   - Automated monthly updates via cron
   - Email notifications
   - Comprehensive reporting
   - Storage cleanup and monitoring

### Key Capabilities

- **Resume Functionality**: Never lose progress on interrupted processing
- **Progress Tracking**: Real-time progress with ETA calculations
- **Error Handling**: Comprehensive error logging and recovery
- **RAG Integration**: Seamless integration with existing ChromaDB vector store
- **Configuration Management**: YAML/JSON config files with environment variable support
- **Monitoring**: Built-in health checks and performance monitoring

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- 50GB+ free disk space (recommended)
- 4GB+ RAM (recommended)
- ChromaDB running on localhost:8082

### Supported arXiv Categories
- `cond-mat` - Condensed Matter
- `gr-qc` - General Relativity and Quantum Cosmology
- `hep-ph` - High Energy Physics - Phenomenology
- `hep-th` - High Energy Physics - Theory
- `math` - Mathematics
- `math-ph` - Mathematical Physics
- `physics` - Physics
- `q-alg` - Quantum Algebra
- `quant-ph` - Quantum Physics

## 🛠️ Installation

### Quick Setup

1. **Run the setup script:**
   ```bash
   cd backend
   python setup_arxiv_rag_enhancement.py
   ```

2. **Verify installation:**
   ```bash
   python process_local_arxiv_dataset.py --help
   ```

### Manual Installation

1. **Install dependencies:**
   ```bash
   pip install -r arxiv_rag_enhancement/requirements.txt
   ```

2. **Create directory structure:**
   ```bash
   mkdir -p /datapool/aischolar/arxiv-dataset-2024/{pdfs,processed,metadata,config}
   ```

3. **Ensure ChromaDB is running:**
   ```bash
   # Check if ChromaDB is accessible
   curl http://localhost:8082/api/v1/heartbeat
   ```

## 📖 Usage

### Script 1: Local Dataset Processor

Process existing PDFs from your local dataset:

```bash
# Process all PDFs in default directory
python process_local_arxiv_dataset.py

# Process specific number of files with verbose output
python process_local_arxiv_dataset.py --max-files 100 --verbose

# Resume previous processing
python process_local_arxiv_dataset.py --resume

# Dry run to see what would be processed
python process_local_arxiv_dataset.py --dry-run

# Use custom directories
python process_local_arxiv_dataset.py \
  --source-dir /path/to/pdfs \
  --output-dir /path/to/output
```

### Script 2: Bulk arXiv Downloader

Download and process papers from arXiv:

```bash
# Download all supported categories since July 2024
python download_bulk_arxiv_papers.py

# Download specific categories
python download_bulk_arxiv_papers.py --categories cond-mat gr-qc hep-ph

# Download papers from specific date range
python download_bulk_arxiv_papers.py \
  --start-date 2024-08-01 \
  --end-date 2024-09-01

# Limit number of papers
python download_bulk_arxiv_papers.py --max-papers 500

# Discovery only (no download)
python download_bulk_arxiv_papers.py --discovery-only

# Download only (no processing)
python download_bulk_arxiv_papers.py --download-only
```

### Script 3: Monthly Auto-Updater

Automated monthly updates:

```bash
# Run monthly update
python run_monthly_update.py

# Setup cron scheduling
python run_monthly_update.py --setup-cron

# Dry run to see what would be updated
python run_monthly_update.py --dry-run

# Force update (ignore schedule)
python run_monthly_update.py --force

# Cleanup old data only
python run_monthly_update.py --cleanup-only
```

## ⚙️ Configuration

### Configuration Files

The system supports multiple configuration formats:

1. **YAML Configuration** (`config/arxiv_rag_config.yaml`):
   ```yaml
   global:
     output_dir: /datapool/aischolar/arxiv-dataset-2024
     categories: [cond-mat, gr-qc, hep-ph, hep-th, math]
     batch_size: 10
   
   local_processor:
     source_dir: ~/arxiv-dataset/pdf
     max_files: null
   
   monthly_updater:
     enabled: true
     email_notifications:
       enabled: false
       smtp_server: smtp.gmail.com
   ```

2. **Environment Variables** (`.env`):
   ```bash
   ARXIV_RAG_OUTPUT_DIR=/datapool/aischolar/arxiv-dataset-2024
   ARXIV_RAG_BATCH_SIZE=10
   CHROMADB_HOST=localhost
   CHROMADB_PORT=8082
   ```

### Email Notifications

Configure email notifications for monthly updates:

```yaml
monthly_updater:
  email_notifications:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    username: your-email@gmail.com
    password: your-app-password
    from_email: arxiv-updater@yourdomain.com
    to_emails:
      - admin@yourdomain.com
```

### Cron Scheduling

Set up automated monthly updates:

1. **Generate cron configuration:**
   ```bash
   python run_monthly_update.py --setup-cron
   ```

2. **Add to crontab:**
   ```bash
   crontab -e
   # Add the generated cron line, for example:
   0 2 1 * * /usr/bin/python /path/to/run_monthly_update.py
   ```

## 📊 Monitoring and Logging

### Log Files

- **Processing Logs**: `/datapool/aischolar/arxiv-dataset-2024/processed/error_logs/`
- **State Files**: `/datapool/aischolar/arxiv-dataset-2024/processed/state_files/`
- **Reports**: `/datapool/aischolar/arxiv-dataset-2024/processed/reports/`

### Progress Tracking

All scripts provide real-time progress tracking:

```
[████████████████████████████████████████] 100.00% (1000/1000) 2.50 items/sec ETA: 00:00
Processing: paper_title_here.pdf
```

### Error Handling

- **Automatic Recovery**: Scripts continue processing after errors
- **Detailed Logging**: All errors logged with context and stack traces
- **Error Reports**: Comprehensive error summaries generated
- **Resume Support**: Interrupted processing can be resumed

## 🔧 Troubleshooting

### Common Issues

1. **ChromaDB Connection Failed**
   ```bash
   # Check if ChromaDB is running
   curl http://localhost:8082/api/v1/heartbeat
   
   # Start ChromaDB if needed
   chroma run --host localhost --port 8082
   ```

2. **Permission Denied Errors**
   ```bash
   # Fix directory permissions
   sudo chown -R $USER:$USER /datapool/aischolar/
   chmod -R 755 /datapool/aischolar/
   ```

3. **Out of Disk Space**
   ```bash
   # Check disk usage
   df -h /datapool/aischolar/
   
   # Clean up old files
   python run_monthly_update.py --cleanup-only
   ```

4. **PDF Processing Errors**
   - Check PDF file integrity
   - Ensure sufficient memory available
   - Review error logs for specific issues

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
python process_local_arxiv_dataset.py --verbose
python download_bulk_arxiv_papers.py --verbose
python run_monthly_update.py --verbose
```

### Health Checks

Check system status:

```bash
# Run status check script
./scripts/check_status.sh

# Manual health check
python -c "
from arxiv_rag_enhancement.processors.local_processor import ArxivLocalProcessor
processor = ArxivLocalProcessor()
print('System OK')
"
```

## 📈 Performance Optimization

### Batch Processing

Adjust batch sizes based on your system:

```yaml
global:
  batch_size: 20  # Increase for more powerful systems
  max_concurrent: 5  # Adjust based on CPU cores
```

### Memory Management

For large datasets:

```yaml
performance:
  memory_limit_mb: 8192  # Increase memory limit
  processing_timeout: 7200  # 2 hours
```

### Network Optimization

For bulk downloads:

```yaml
bulk_downloader:
  max_concurrent_downloads: 10  # Increase for faster downloads
  download_timeout: 600  # 10 minutes
```

## 🔒 Security Considerations

### File Permissions

The system sets appropriate file permissions:
- Directories: 755
- Files: 644
- Executables: 755

### Network Security

- All downloads use HTTPS
- Rate limiting prevents server overload
- No sensitive data transmitted

### Data Privacy

- All processing occurs locally
- No data sent to external services
- Audit trail maintained for compliance

## 🤝 Integration with AI Scholar

The system seamlessly integrates with your existing AI Scholar RAG infrastructure:

- **ChromaDB**: Uses existing vector store configuration
- **Embeddings**: Compatible with existing embedding models
- **Metadata**: Maintains consistent metadata schema
- **Collections**: Integrates with existing document collections

## 📚 API Reference

### Core Classes

#### ArxivLocalProcessor
```python
from arxiv_rag_enhancement.processors.local_processor import ArxivLocalProcessor

processor = ArxivLocalProcessor(
    source_dir="~/arxiv-dataset/pdf",
    output_dir="/datapool/aischolar/arxiv-dataset-2024",
    batch_size=10
)

# Initialize services
await processor.initialize_services()

# Process dataset
success = await processor.process_dataset(max_files=100)
```

#### ArxivBulkDownloader
```python
from arxiv_rag_enhancement.processors.bulk_downloader import ArxivBulkDownloader
from datetime import datetime

downloader = ArxivBulkDownloader(
    categories=['cond-mat', 'gr-qc'],
    start_date=datetime(2024, 7, 1),
    output_dir="/datapool/aischolar/arxiv-dataset-2024"
)

# Discover papers
papers = await downloader.discover_papers()

# Download papers
downloaded_files = await downloader.download_papers(papers)
```

#### ArxivMonthlyUpdater
```python
from arxiv_rag_enhancement.processors.monthly_updater import ArxivMonthlyUpdater

updater = ArxivMonthlyUpdater(
    categories=['cond-mat', 'gr-qc'],
    output_dir="/datapool/aischolar/arxiv-dataset-2024"
)

# Run monthly update
report = await updater.run_monthly_update()
```

## 📄 License

This project is part of the AI Scholar system. Please refer to the main project license.

## 🆘 Support

For support and questions:

1. Check the troubleshooting section above
2. Review log files for error details
3. Ensure all system requirements are met
4. Verify ChromaDB connectivity

## 🔄 Updates

The system includes automatic update capabilities:

- **Monthly Updates**: Automatically download new papers
- **Configuration Updates**: Hot-reload configuration changes
- **Service Updates**: Integrate with AI Scholar system updates

---

**Happy researching! 🎓✨**