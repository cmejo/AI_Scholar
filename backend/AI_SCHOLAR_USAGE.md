# AI Scholar Usage Guide

This guide explains how to use the AI Scholar bulk download and processing scripts.

## Prerequisites

1. **ChromaDB Service**: Make sure ChromaDB is running on localhost:8082
2. **Python Dependencies**: Install required packages (see requirements.txt)
3. **Configuration**: Ensure AI Scholar config file exists

## Available Scripts

### 1. AI Scholar Downloader (`ai_scholar_downloader.py`)

Downloads and processes papers from arXiv for AI Scholar categories.

**Basic Usage:**
```bash
# Download papers from last 7 days
python ai_scholar_downloader.py

# Download papers from last 30 days, max 500 papers
python ai_scholar_downloader.py --days 30 --max-papers 500

# Dry run to see what would be downloaded
python ai_scholar_downloader.py --days 7 --dry-run

# Resume interrupted download
python ai_scholar_downloader.py --resume
```

**Options:**
- `--days DAYS`: Number of days back to search (default: 7)
- `--max-papers NUM`: Maximum number of papers to process (default: 100)
- `--config PATH`: Path to AI Scholar config file
- `--dry-run`: Show what would be downloaded without downloading
- `--resume`: Resume from previous interrupted run
- `--verbose`: Enable verbose logging

### 2. AI Scholar Processor (`ai_scholar_processor.py`)

Processes existing PDF files into the AI Scholar vector store.

**Basic Usage:**
```bash
# Process all PDFs in a directory
python ai_scholar_processor.py /path/to/pdfs

# Process PDFs recursively with custom batch size
python ai_scholar_processor.py --recursive --batch-size 20 /path/to/pdfs

# Process specific pattern of files
python ai_scholar_processor.py --pattern "arxiv_*.pdf" /path/to/pdfs

# Resume interrupted processing
python ai_scholar_processor.py --resume /path/to/pdfs
```

**Options:**
- `--config PATH`: Path to AI Scholar config file
- `--batch-size NUM`: Number of PDFs to process in each batch (default: 10)
- `--recursive`: Recursively search subdirectories for PDFs
- `--pattern PATTERN`: File pattern to match (default: *.pdf)
- `--resume`: Resume from previous interrupted run
- `--force`: Reprocess files even if already processed

### 3. AI Scholar Monthly Update (`ai_scholar_monthly_update.py`)

Runs automated monthly updates for AI Scholar.

### 4. AI Scholar Historical Downloader (`ai_scholar_historical_downloader.py`)

Downloads papers from the beginning of arXiv (1991) or any historical period.

**Basic Usage:**
```bash
# Process previous month
python ai_scholar_monthly_update.py

# Process specific month
python ai_scholar_monthly_update.py --month 2024-10

# Process with email report and cleanup
python ai_scholar_monthly_update.py --email --cleanup
```

**Options:**
- `--month YYYY-MM`: Specific month to process (default: previous month)
- `--config PATH`: Path to AI Scholar config file
- `--max-papers NUM`: Maximum number of papers to process (default: 1000)
- `--email`: Send email report after completion
- `--cleanup`: Run cleanup of old files after processing

**Basic Usage:**
```bash
# Download from arXiv's beginning (1991) to now
python ai_scholar_historical_downloader.py

# Download from specific year range  
python ai_scholar_historical_downloader.py --start-year 1996 --end-year 2005

# Download quantum computing history
python ai_scholar_historical_downloader.py --start-year 1996 --categories "quant-ph,cond-mat"

# Download early AI papers
python ai_scholar_historical_downloader.py --start-year 1998 --categories "cs.AI,cs.LG"
```

**Options:**
- `--start-year YEAR`: Starting year (default: 1991)
- `--end-year YEAR`: Ending year (default: current year)
- `--start-date YYYY-MM-DD`: Specific start date
- `--end-date YYYY-MM-DD`: Specific end date
- `--categories CAT1,CAT2`: Specific categories
- `--max-papers NUM`: Maximum papers per period (default: 10000)
- `--dry-run`: Show what would be downloaded

## Configuration

The scripts will automatically look for the AI Scholar configuration file in these locations:
1. `multi_instance_arxiv_system/configs/ai_scholar.yaml`
2. `configs/ai_scholar.yaml`
3. `../configs/ai_scholar.yaml`

You can also specify a custom config file with the `--config` option.

## Example Workflows

### Quick Start - Download Recent Papers
```bash
# Download and process papers from last 3 days (small test)
python ai_scholar_downloader.py --days 3 --max-papers 10 --verbose
```

### Process Local PDF Collection
```bash
# Process all PDFs in your downloads folder
python ai_scholar_processor.py --recursive ~/Downloads/arxiv_papers/
```

### Monthly Batch Processing
```bash
# Process all papers from October 2024
python ai_scholar_monthly_update.py --month 2024-10 --cleanup
```

### Large Scale Processing
```bash
# Download papers from last 30 days, up to 1000 papers
python ai_scholar_downloader.py --days 30 --max-papers 1000
```

## Monitoring and Logs

All scripts create log files:
- `ai_scholar_downloader.log`
- `ai_scholar_processor.log`
- `ai_scholar_monthly_update.log`

Use `--verbose` flag for detailed logging to console.

## Error Handling

The scripts include comprehensive error handling:
- **Retry Logic**: Automatic retries with exponential backoff
- **Circuit Breakers**: Prevent cascading failures
- **Resume Capability**: Continue from where you left off
- **Error Reports**: Detailed error logging and categorization

## Storage Locations

By default, files are stored in:
- **PDFs**: `/datapool/aischolar/ai-scholar-arxiv-dataset/pdf`
- **Processed Data**: `/datapool/aischolar/ai-scholar-arxiv-dataset/processed`
- **State Files**: `/datapool/aischolar/ai-scholar-arxiv-dataset/state`
- **Error Logs**: `/datapool/aischolar/ai-scholar-arxiv-dataset/errors`

These paths can be configured in the AI Scholar config file.

## Troubleshooting

### Common Issues

1. **ChromaDB Connection Error**
   ```
   Solution: Make sure ChromaDB is running on localhost:8082
   ```

2. **Config File Not Found**
   ```
   Solution: Specify config file with --config option or ensure it exists in expected locations
   ```

3. **Permission Errors**
   ```
   Solution: Check file permissions for storage directories
   ```

4. **Memory Issues**
   ```
   Solution: Reduce batch size with --batch-size option
   ```

### Getting Help

Run any script with `--help` to see detailed usage information:
```bash
python ai_scholar_downloader.py --help
python ai_scholar_processor.py --help
python ai_scholar_monthly_update.py --help
```

## Performance Tips

1. **Batch Size**: Adjust `--batch-size` based on available memory
2. **Concurrent Processing**: Configure in the AI Scholar config file
3. **Storage**: Use fast storage (SSD) for better performance
4. **Network**: Ensure stable internet connection for downloads
5. **Resources**: Monitor CPU and memory usage during processing

## Integration with Existing System

The AI Scholar system integrates with:
- **ChromaDB**: For vector storage and semantic search
- **Existing PDF Processor**: For scientific document processing
- **Vector Store Service**: For embedding generation and storage
- **Error Handling**: Comprehensive logging and recovery