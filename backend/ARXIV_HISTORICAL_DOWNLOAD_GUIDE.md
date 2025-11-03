# ArXiv Historical Download Guide

This guide explains how to download papers from the beginning of arXiv (1991) or any historical period.

## ArXiv Timeline & Categories

### ArXiv History
- **1991**: ArXiv begins with `hep-th` (High Energy Physics - Theory)
- **1992**: `gr-qc` (General Relativity), `astro-ph` (Astrophysics) added
- **1993**: `cond-mat` (Condensed Matter) added
- **1994**: `nucl-th` (Nuclear Theory) added
- **1995**: `math` (Mathematics) added
- **1996**: `quant-ph` (Quantum Physics) added ⭐ **Key for AI Scholar**
- **1997**: `physics.*` categories added
- **1998**: `cs.*` (Computer Science) categories added ⭐ **Key for AI Scholar**
- **2007**: `q-bio` (Quantitative Biology) added
- **2008**: `q-fin` (Quantitative Finance), `stat` (Statistics) added
- **2009**: `eess` (Electrical Engineering) added
- **2019**: `econ` (Economics) added

### AI Scholar Relevant Categories by Era

**Early ArXiv (1991-1995)**
- `hep-th`, `hep-ph` - Theoretical physics foundations
- `gr-qc` - General relativity and quantum gravity
- `cond-mat` - Condensed matter physics
- `math` - Mathematical foundations

**Quantum Era (1996-1997)**
- `quant-ph` - Quantum physics and quantum computing ⭐
- `physics.*` - Various physics categories

**Computer Science Era (1998+)**
- `cs.AI` - Artificial Intelligence ⭐
- `cs.LG` - Machine Learning ⭐
- `cs.CL` - Computational Linguistics
- `cs.CV` - Computer Vision

**Modern Era (2007+)**
- `stat.ML` - Statistics and Machine Learning
- `q-fin` - Quantitative Finance
- `eess` - Signal Processing

## Download Methods

### 1. Historical Downloader Script

```bash
# Download from arXiv's beginning (1991) to now
python backend/ai_scholar_historical_downloader.py

# Download specific year range
python backend/ai_scholar_historical_downloader.py --start-year 1991 --end-year 2000

# Download specific date range
python backend/ai_scholar_historical_downloader.py --start-date 1995-01-01 --end-date 1995-12-31

# Download early physics papers (pre-quantum computing)
python backend/ai_scholar_historical_downloader.py --start-year 1991 --end-year 1995 --categories "hep-th,gr-qc,cond-mat"

# Download quantum computing era
python backend/ai_scholar_historical_downloader.py --start-year 1996 --end-year 2005 --categories "quant-ph,cond-mat,math-ph"

# Download AI/ML era
python backend/ai_scholar_historical_downloader.py --start-year 1998 --end-year 2010 --categories "cs.AI,cs.LG,quant-ph,stat.ML"
```

### 2. Regular Downloader with Large Date Ranges

```bash
# Download papers from last 10 years (3650 days)
python backend/ai_scholar_downloader.py --days 3650 --max-papers 50000

# Download papers from last 20 years (7300 days)
python backend/ai_scholar_downloader.py --days 7300 --max-papers 100000
```

### 3. Year-by-Year Approach

```bash
# Process each year individually (recommended for very large datasets)
for year in {1991..2024}; do
    python backend/ai_scholar_downloader.py \
        --start-date ${year}-01-01 \
        --end-date ${year}-12-31 \
        --max-papers 10000 \
        --resume
done
```

## Recommended Strategies

### Strategy 1: Complete Historical Download
```bash
# Phase 1: Early ArXiv (1991-1995) - Physics foundations
python backend/ai_scholar_historical_downloader.py \
    --start-year 1991 --end-year 1995 \
    --categories "hep-th,gr-qc,cond-mat,math" \
    --max-papers 5000

# Phase 2: Quantum Era (1996-1997) - Quantum physics begins
python backend/ai_scholar_historical_downloader.py \
    --start-year 1996 --end-year 1997 \
    --categories "quant-ph,cond-mat,math-ph,physics" \
    --max-papers 10000

# Phase 3: CS Era (1998-2006) - AI and ML papers begin
python backend/ai_scholar_historical_downloader.py \
    --start-year 1998 --end-year 2006 \
    --categories "cs.AI,cs.LG,quant-ph,cond-mat,math" \
    --max-papers 20000

# Phase 4: Modern Era (2007-2015) - ML explosion
python backend/ai_scholar_historical_downloader.py \
    --start-year 2007 --end-year 2015 \
    --categories "cs.AI,cs.LG,stat.ML,quant-ph,math" \
    --max-papers 50000

# Phase 5: Deep Learning Era (2016-now) - Use regular downloader
python backend/ai_scholar_downloader.py --days 2920 --max-papers 100000  # Last 8 years
```

### Strategy 2: Focused Historical Download
```bash
# Focus on quantum computing history
python backend/ai_scholar_historical_downloader.py \
    --start-year 1996 --end-year 2024 \
    --categories "quant-ph" \
    --max-papers 30000

# Focus on AI/ML history
python backend/ai_scholar_historical_downloader.py \
    --start-year 1998 --end-year 2024 \
    --categories "cs.AI,cs.LG,stat.ML" \
    --max-papers 50000
```

### Strategy 3: Decade-by-Decade
```bash
# 1990s: Physics foundations
python backend/ai_scholar_historical_downloader.py --start-year 1991 --end-year 1999

# 2000s: Quantum + early CS
python backend/ai_scholar_historical_downloader.py --start-year 2000 --end-year 2009

# 2010s: ML explosion
python backend/ai_scholar_historical_downloader.py --start-year 2010 --end-year 2019

# 2020s: Modern AI
python backend/ai_scholar_downloader.py --days 1460  # Last 4 years
```

## Important Considerations

### 1. Data Volume Estimates

**Early ArXiv (1991-1995)**
- ~50-200 papers per month total
- AI Scholar categories: ~10-50 papers per month
- **Total estimate**: 1,000-3,000 papers

**Growth Period (1996-2005)**
- ~200-2,000 papers per month total
- AI Scholar categories: ~50-500 papers per month
- **Total estimate**: 10,000-50,000 papers

**Modern ArXiv (2006-2024)**
- ~5,000-15,000 papers per month total
- AI Scholar categories: ~1,000-5,000 papers per month
- **Total estimate**: 200,000-1,000,000 papers

### 2. Storage Requirements

- **PDF files**: ~2-5 MB per paper average
- **Processed data**: ~1-2 MB per paper (embeddings, chunks)
- **Complete historical dataset**: 500GB - 2TB estimated

### 3. Processing Time

- **Download rate**: 10-100 papers per minute (network dependent)
- **Processing rate**: 5-20 papers per minute (CPU dependent)
- **Complete historical processing**: Days to weeks

### 4. Category Availability

**Before 1996**: No `quant-ph` (quantum physics)
**Before 1998**: No `cs.*` (computer science) categories
**Before 2008**: No `stat.ML` (statistics/ML)

Plan your downloads accordingly!

## Practical Examples

### Example 1: Quantum Computing History
```bash
# Get the complete history of quantum computing papers
python backend/ai_scholar_historical_downloader.py \
    --start-year 1996 \
    --categories "quant-ph,cond-mat.mes-hall,physics.atom-ph" \
    --max-papers 25000 \
    --batch-size 50
```

### Example 2: AI/ML Complete History
```bash
# Get complete AI/ML history (will be large!)
python backend/ai_scholar_historical_downloader.py \
    --start-year 1998 \
    --categories "cs.AI,cs.LG,cs.CL,cs.CV,stat.ML" \
    --max-papers 100000 \
    --batch-size 100
```

### Example 3: Physics Foundations
```bash
# Get foundational physics papers from arXiv's early days
python backend/ai_scholar_historical_downloader.py \
    --start-year 1991 --end-year 1997 \
    --categories "hep-th,gr-qc,cond-mat,math-ph" \
    --max-papers 15000
```

### Example 4: Decade Sampling
```bash
# Sample from each decade
python backend/ai_scholar_historical_downloader.py --start-year 1991 --end-year 1999 --max-papers 5000
python backend/ai_scholar_historical_downloader.py --start-year 2000 --end-year 2009 --max-papers 15000
python backend/ai_scholar_historical_downloader.py --start-year 2010 --end-year 2019 --max-papers 30000
python backend/ai_scholar_downloader.py --days 1460 --max-papers 20000  # 2020-2024
```

## Monitoring and Management

### Progress Tracking
```bash
# Use verbose mode to monitor progress
python backend/ai_scholar_historical_downloader.py --verbose

# Check log files
tail -f ai_scholar_historical.log
```

### Resume Interrupted Downloads
```bash
# Always use --resume for large downloads
python backend/ai_scholar_historical_downloader.py --resume
```

### Dry Run First
```bash
# Always test with dry run for large periods
python backend/ai_scholar_historical_downloader.py \
    --start-year 1991 --end-year 2024 \
    --dry-run
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**: ArXiv API has rate limits
   - Solution: Use smaller batch sizes, built-in delays

2. **Storage Space**: Historical downloads are large
   - Solution: Monitor disk space, use cleanup options

3. **Memory Issues**: Processing many papers
   - Solution: Reduce batch size, process in smaller chunks

4. **Network Timeouts**: Long downloads may timeout
   - Solution: Use resume functionality, smaller time periods

### Performance Tips

1. **Start Small**: Test with 1-2 years first
2. **Use Categories**: Filter to relevant categories only
3. **Batch Processing**: Use appropriate batch sizes for your system
4. **Monitor Resources**: Watch CPU, memory, and disk usage
5. **Resume Capability**: Always use --resume for large downloads

## Integration with Existing System

The historical downloader integrates with:
- **AI Scholar Configuration**: Uses same config files
- **Vector Store**: Stores in same ChromaDB collections
- **Error Handling**: Same robust error handling
- **Progress Tracking**: Same monitoring and logging

Historical papers will be seamlessly integrated with your existing AI Scholar system!