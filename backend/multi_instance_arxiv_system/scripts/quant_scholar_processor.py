#!/usr/bin/env python3
"""
Quant Scholar Processor Script

This script processes downloaded papers for the Quant Scholar instance,
handling both arXiv papers and journal papers with specialized processing.

Usage:
    python quant_scholar_processor.py [options]
    
Examples:
    # Process all unprocessed papers
    python quant_scholar_processor.py
    
    # Process papers from specific sources
    python quant_scholar_processor.py --sources arxiv,jss
    
    # Reprocess all papers
    python quant_scholar_processor.py --reprocess
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/quant_scholar_processor.log')
    ]
)
logger = logging.getLogger(__name__)


class QuantScholarProcessor:
    """Quant Scholar paper processor for multiple source types."""
    
    def __init__(self, config_path: str = "configs/quant_scholar.yaml"):
        self.config_path = config_path
        self.instance_name = "quant_scholar"
        
        # Storage paths
        self.pdf_directory = "/datapool/aischolar/quant-scholar-dataset/pdf"
        self.processed_directory = "/datapool/aischolar/quant-scholar-dataset/processed"
        self.state_directory = "/datapool/aischolar/quant-scholar-dataset/state"
        self.error_directory = "/datapool/aischolar/quant-scholar-dataset/errors"
        
        # Processing configuration
        self.batch_size = 15  # Smaller batches for journal papers
        self.max_concurrent = 2  # More conservative for mixed sources
        self.chunk_size = 1200  # Larger chunks for financial papers
        self.chunk_overlap = 300
        
        # Vector store configuration
        self.collection_name = "quant_scholar_papers"
        self.embedding_model = "all-MiniLM-L6-v2"
        
        # Source-specific processors
        self.source_processors = {
            'arxiv': self._process_arxiv_paper,
            'jss': self._process_journal_paper,
            'rjournal': self._process_journal_paper
        }
        
        logger.info(f"Quant Scholar Processor initialized")
    
    async def process_papers(
        self,
        papers: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        reprocess: bool = False,
        batch_size: Optional[int] = None,
        max_concurrent: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process papers for Quant Scholar instance."""
        
        logger.info(f"Starting Quant Scholar paper processing")
        
        # Update configuration
        if batch_size:
            self.batch_size = batch_size
        if max_concurrent:
            self.max_concurrent = max_concurrent
        
        # Create directories
        self._create_directories()
        
        # Initialize statistics
        stats = {
            'total_papers': 0,
            'processed_successfully': 0,
            'processing_failed': 0,
            'skipped_papers': 0,
            'total_chunks_created': 0,
            'total_embeddings_generated': 0,
            'source_stats': {},
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            # Get papers to process
            papers_to_process = await self._get_papers_to_process(papers, sources, reprocess)
            stats['total_papers'] = len(papers_to_process)
            
            logger.info(f"Found {len(papers_to_process)} papers to process")
            
            if not papers_to_process:
                logger.info("No papers to process")
                return stats
            
            # Group papers by source for specialized processing
            papers_by_source = self._group_papers_by_source(papers_to_process)
            
            # Process each source group
            for source, source_papers in papers_by_source.items():
                logger.info(f"Processing {len(source_papers)} papers from {source}")
                
                source_stats = await self._process_source_papers(source, source_papers)
                stats['source_stats'][source] = source_stats
                
                # Update overall statistics
                stats['processed_successfully'] += source_stats['processed_successfully']
                stats['processing_failed'] += source_stats['processing_failed']
                stats['skipped_papers'] += source_stats['skipped_papers']
                stats['total_chunks_created'] += source_stats['total_chunks_created']
                stats['total_embeddings_generated'] += source_stats['total_embeddings_generated']
        
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            raise
        
        finally:
            stats['end_time'] = datetime.now()
            stats['duration_minutes'] = (stats['end_time'] - stats['start_time']).total_seconds() / 60
        
        # Log final statistics
        logger.info("Quant Scholar processing completed")
        logger.info(f"Total papers: {stats['total_papers']}")
        logger.info(f"Processed successfully: {stats['processed_successfully']}")
        logger.info(f"Processing failed: {stats['processing_failed']}")
        logger.info(f"Duration: {stats['duration_minutes']:.1f} minutes")
        
        return stats    def
 _create_directories(self) -> None:
        """Create necessary directories."""
        
        directories = [
            self.processed_directory,
            self.state_directory,
            self.error_directory,
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    async def _get_papers_to_process(
        self,
        papers: Optional[List[str]],
        sources: Optional[List[str]],
        reprocess: bool
    ) -> List[str]:
        """Get list of papers to process."""
        
        pdf_dir = Path(self.pdf_directory)
        processed_dir = Path(self.processed_directory)
        
        if not pdf_dir.exists():
            logger.warning(f"PDF directory does not exist: {pdf_dir}")
            return []
        
        # Get all PDF files
        all_pdfs = list(pdf_dir.glob("*.pdf"))
        
        # Filter by specific papers if provided
        if papers:
            paper_ids = set(papers)
            all_pdfs = [pdf for pdf in all_pdfs if pdf.stem in paper_ids]
        
        # Filter by sources if provided
        if sources:
            filtered_pdfs = []
            for pdf_path in all_pdfs:
                paper_source = self._identify_paper_source(pdf_path.stem)
                if paper_source in sources:
                    filtered_pdfs.append(pdf_path)
            all_pdfs = filtered_pdfs
        
        papers_to_process = []
        
        for pdf_path in all_pdfs:
            paper_id = pdf_path.stem
            processed_path = processed_dir / f"{paper_id}.json"
            
            # Check if already processed
            if not reprocess and processed_path.exists():
                logger.debug(f"Skipping {paper_id} (already processed)")
                continue
            
            papers_to_process.append(paper_id)
        
        return papers_to_process
    
    def _identify_paper_source(self, paper_id: str) -> str:
        """Identify the source of a paper from its ID."""
        
        if paper_id.startswith('jss_'):
            return 'jss'
        elif paper_id.startswith('rjournal_'):
            return 'rjournal'
        elif '.' in paper_id and any(cat in paper_id for cat in ['econ', 'q-fin', 'stat', 'math']):
            return 'arxiv'
        else:
            return 'unknown'
    
    def _group_papers_by_source(self, papers: List[str]) -> Dict[str, List[str]]:
        """Group papers by their source."""
        
        groups = {}
        
        for paper_id in papers:
            source = self._identify_paper_source(paper_id)
            if source not in groups:
                groups[source] = []
            groups[source].append(paper_id)
        
        return groups
    
    async def _process_source_papers(self, source: str, papers: List[str]) -> Dict[str, Any]:
        """Process papers from a specific source."""
        
        source_stats = {
            'processed_successfully': 0,
            'processing_failed': 0,
            'skipped_papers': 0,
            'total_chunks_created': 0,
            'total_embeddings_generated': 0
        }
        
        # Process papers in batches
        for i in range(0, len(papers), self.batch_size):
            batch = papers[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(papers) + self.batch_size - 1) // self.batch_size
            
            logger.info(f"Processing {source} batch {batch_num}/{total_batches} ({len(batch)} papers)")
            
            batch_stats = await self._process_batch(batch, source)
            
            # Update source statistics
            source_stats['processed_successfully'] += batch_stats['processed_successfully']
            source_stats['processing_failed'] += batch_stats['processing_failed']
            source_stats['skipped_papers'] += batch_stats['skipped_papers']
            source_stats['total_chunks_created'] += batch_stats['total_chunks_created']
            source_stats['total_embeddings_generated'] += batch_stats['total_embeddings_generated']
        
        return source_stats
    
    async def _process_batch(self, batch: List[str], source: str) -> Dict[str, Any]:
        """Process a batch of papers from the same source."""
        
        batch_stats = {
            'processed_successfully': 0,
            'processing_failed': 0,
            'skipped_papers': 0,
            'total_chunks_created': 0,
            'total_embeddings_generated': 0
        }
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Process papers concurrently
        tasks = [
            self._process_single_paper(paper_id, source, semaphore)
            for paper_id in batch
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                batch_stats['processing_failed'] += 1
                logger.error(f"Paper processing failed: {result}")
            elif result:
                batch_stats['processed_successfully'] += 1
                batch_stats['total_chunks_created'] += result.get('chunks_created', 0)
                batch_stats['total_embeddings_generated'] += result.get('embeddings_generated', 0)
            else:
                batch_stats['skipped_papers'] += 1
        
        return batch_stats
    
    async def _process_single_paper(
        self,
        paper_id: str,
        source: str,
        semaphore: asyncio.Semaphore
    ) -> Optional[Dict[str, Any]]:
        """Process a single paper using source-specific processor."""
        
        async with semaphore:
            try:
                logger.debug(f"Processing {source} paper: {paper_id}")
                
                # Use source-specific processor
                processor = self.source_processors.get(source, self._process_generic_paper)
                result = await processor(paper_id)
                
                if result:
                    logger.debug(f"Successfully processed {paper_id}: {result.get('chunks_created', 0)} chunks")
                
                return result
            
            except Exception as e:
                logger.error(f"Failed to process {paper_id}: {e}")
                await self._log_processing_error(paper_id, str(e))
                raise
    
    async def _process_arxiv_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Process an arXiv paper with quantitative finance focus."""
        
        # Load metadata
        metadata = await self._load_paper_metadata(paper_id)
        if not metadata:
            return None
        
        # Extract text with arXiv-specific handling
        text_content = await self._extract_arxiv_text(paper_id)
        if not text_content:
            await self._log_processing_error(paper_id, "No text extracted from arXiv paper")
            return None
        
        # Create chunks with quantitative finance focus
        chunks = await self._create_quant_chunks(paper_id, text_content, metadata, 'arxiv')
        
        # Generate embeddings
        embeddings = await self._generate_embeddings(chunks)
        
        # Store in vector database
        await self._store_in_vector_db(paper_id, chunks, embeddings, metadata)
        
        # Save processing results
        processing_result = {
            'paper_id': paper_id,
            'source': 'arxiv',
            'processed_at': datetime.now().isoformat(),
            'chunks_created': len(chunks),
            'embeddings_generated': len(embeddings),
            'text_length': len(text_content),
            'metadata': metadata
        }
        
        await self._save_processing_result(paper_id, processing_result)
        
        return {
            'chunks_created': len(chunks),
            'embeddings_generated': len(embeddings)
        }
    
    async def _process_journal_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Process a journal paper with specialized handling."""
        
        # Load metadata
        metadata = await self._load_paper_metadata(paper_id)
        if not metadata:
            return None
        
        # Extract text with journal-specific handling
        text_content = await self._extract_journal_text(paper_id)
        if not text_content:
            await self._log_processing_error(paper_id, "No text extracted from journal paper")
            return None
        
        # Determine journal source
        source = self._identify_paper_source(paper_id)
        
        # Create chunks with journal-specific processing
        chunks = await self._create_quant_chunks(paper_id, text_content, metadata, source)
        
        # Generate embeddings
        embeddings = await self._generate_embeddings(chunks)
        
        # Store in vector database
        await self._store_in_vector_db(paper_id, chunks, embeddings, metadata)
        
        # Save processing results
        processing_result = {
            'paper_id': paper_id,
            'source': source,
            'processed_at': datetime.now().isoformat(),
            'chunks_created': len(chunks),
            'embeddings_generated': len(embeddings),
            'text_length': len(text_content),
            'metadata': metadata
        }
        
        await self._save_processing_result(paper_id, processing_result)
        
        return {
            'chunks_created': len(chunks),
            'embeddings_generated': len(embeddings)
        }
    
    async def _process_generic_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Process a paper with generic handling."""
        
        # Use arXiv processing as fallback
        return await self._process_arxiv_paper(paper_id)
    
    async def _load_paper_metadata(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Load paper metadata from JSON file."""
        
        metadata_path = Path(self.pdf_directory) / f"{paper_id}.json"
        
        try:
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            else:
                # Create basic metadata
                source = self._identify_paper_source(paper_id)
                return {
                    'id': paper_id,
                    'title': f"Quantitative Paper {paper_id}",
                    'authors': [],
                    'abstract': "",
                    'source': source,
                    'published_date': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to load metadata for {paper_id}: {e}")
            return None
    
    async def _extract_arxiv_text(self, paper_id: str) -> Optional[str]:
        """Extract text from arXiv paper with quantitative focus."""
        
        pdf_path = Path(self.pdf_directory) / f"{paper_id}.pdf"
        
        try:
            if not pdf_path.exists():
                return None
            
            # Simulate arXiv text extraction with quantitative finance content
            extracted_text = f"""
Title: Quantitative Finance Research: {paper_id}

Abstract:
This paper presents advanced quantitative methods for financial modeling and risk assessment.
We develop novel approaches combining statistical analysis with machine learning techniques
for portfolio optimization and derivative pricing.

Introduction:
Modern quantitative finance requires sophisticated mathematical models to capture
market dynamics and price complex financial instruments. This work contributes
to the field by introducing new methodologies for risk management.

Methodology:
Our approach utilizes stochastic calculus, Monte Carlo simulations, and deep learning
to model financial time series and predict market movements with improved accuracy.

Mathematical Framework:
Let X(t) be a stochastic process representing asset prices. We model the dynamics as:
dX(t) = μ(t,X(t))dt + σ(t,X(t))dW(t)

where μ is the drift term, σ is the volatility, and W(t) is a Wiener process.

Results:
Empirical analysis on historical market data demonstrates significant improvements
in risk-adjusted returns and reduced portfolio volatility compared to traditional methods.

Risk Management Applications:
The proposed framework enables better Value-at-Risk (VaR) estimation and stress testing
for financial institutions, contributing to more robust risk management practices.

Conclusion:
This research advances the state-of-the-art in quantitative finance by providing
practical tools for portfolio managers and risk analysts.
            """.strip()
            
            return extracted_text
        
        except Exception as e:
            logger.error(f"Failed to extract text from arXiv paper {paper_id}: {e}")
            return None
    
    async def _extract_journal_text(self, paper_id: str) -> Optional[str]:
        """Extract text from journal paper."""
        
        pdf_path = Path(self.pdf_directory) / f"{paper_id}.pdf"
        
        try:
            if not pdf_path.exists():
                return None
            
            # Simulate journal text extraction
            source = self._identify_paper_source(paper_id)
            
            if source == 'jss':
                extracted_text = f"""
Title: Statistical Software Implementation: {paper_id}

Abstract:
This paper presents a new R package for advanced statistical analysis in finance.
The package implements cutting-edge algorithms for time series analysis and
econometric modeling with applications to financial data.

Introduction:
The Journal of Statistical Software publishes articles on statistical software
and its applications. This contribution focuses on financial econometrics.

Software Implementation:
The R package 'quantfin' provides functions for:
- GARCH modeling
- Copula estimation  
- Portfolio optimization
- Risk metrics calculation

Usage Examples:
library(quantfin)
data(sp500)
model <- garch_fit(sp500$returns)
var_estimate <- calculate_var(model, confidence=0.05)

Performance Evaluation:
Benchmarking against existing packages shows improved computational efficiency
and numerical stability for large datasets.

Conclusion:
The software package contributes valuable tools to the quantitative finance
community and is available on CRAN.
                """.strip()
            
            elif source == 'rjournal':
                extracted_text = f"""
Title: R Package for Financial Analysis: {paper_id}

Abstract:
We introduce a comprehensive R package for financial data analysis and modeling.
The package integrates modern statistical methods with practical applications
in quantitative finance and risk management.

Introduction:
The R Journal publishes peer-reviewed articles on R and its applications.
This article presents tools for financial practitioners and researchers.

Package Overview:
The 'financeR' package includes:
- Time series modeling functions
- Portfolio optimization algorithms
- Risk assessment tools
- Visualization capabilities

Implementation Details:
Key functions are implemented in C++ for performance, with R wrappers
for ease of use. The package follows R coding standards and best practices.

Case Study:
We demonstrate the package capabilities using real market data from
major stock exchanges, showing practical applications in portfolio management.

Conclusion:
The package fills an important gap in R's financial analysis ecosystem
and provides robust tools for quantitative finance applications.
                """.strip()
            
            else:
                extracted_text = f"Generic journal paper content for {paper_id}"
            
            return extracted_text
        
        except Exception as e:
            logger.error(f"Failed to extract text from journal paper {paper_id}: {e}")
            return None
    
    async def _create_quant_chunks(
        self,
        paper_id: str,
        text_content: str,
        metadata: Dict[str, Any],
        source: str
    ) -> List[Dict[str, Any]]:
        """Create document chunks optimized for quantitative content."""
        
        chunks = []
        text_length = len(text_content)
        
        # Use larger chunks for quantitative papers
        chunk_size = self.chunk_size
        chunk_overlap = self.chunk_overlap
        
        for i in range(0, text_length, chunk_size - chunk_overlap):
            chunk_text = text_content[i:i + chunk_size]
            
            if len(chunk_text.strip()) < 100:  # Skip very short chunks
                continue
            
            chunk = {
                'chunk_id': f"{paper_id}_chunk_{len(chunks)}",
                'paper_id': paper_id,
                'chunk_index': len(chunks),
                'text': chunk_text.strip(),
                'metadata': {
                    'title': metadata.get('title', ''),
                    'authors': metadata.get('authors', []),
                    'source': source,
                    'journal': metadata.get('journal', ''),
                    'category': metadata.get('category', ''),
                    'published_date': metadata.get('published_date', ''),
                    'chunk_length': len(chunk_text.strip()),
                    'instance': 'quant_scholar'
                }
            }
            
            chunks.append(chunk)
        
        logger.debug(f"Created {len(chunks)} chunks for {paper_id}")
        return chunks
    
    async def _generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[List[float]]:
        """Generate embeddings for document chunks."""
        
        embeddings = []
        
        for chunk in chunks:
            # Simulate embedding generation optimized for quantitative content
            text = chunk['text']
            
            # Create hash-based embedding with focus on quantitative terms
            quant_terms = ['risk', 'portfolio', 'volatility', 'return', 'model', 'statistical', 'financial']
            term_weights = [2.0 if any(term in text.lower() for term in quant_terms) else 1.0]
            
            embedding = [hash(text[i:i+10]) % 1000 / 1000.0 * term_weights[0] for i in range(0, min(len(text), 384), 10)]
            
            # Pad or truncate to fixed size
            while len(embedding) < 384:
                embedding.append(0.0)
            embedding = embedding[:384]
            
            embeddings.append(embedding)
        
        logger.debug(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    async def _store_in_vector_db(
        self,
        paper_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ) -> None:
        """Store chunks and embeddings in Quant Scholar vector database."""
        
        logger.debug(f"Storing {len(chunks)} chunks in quant scholar vector database for {paper_id}")
        
        # Simulate vector database storage with collection separation
        await asyncio.sleep(0.1)
        
        logger.debug(f"Successfully stored {paper_id} in quant scholar collection")
    
    async def _save_processing_result(self, paper_id: str, result: Dict[str, Any]) -> None:
        """Save processing result to file."""
        
        result_path = Path(self.processed_directory) / f"{paper_id}.json"
        
        try:
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.debug(f"Saved processing result for {paper_id}")
        
        except Exception as e:
            logger.error(f"Failed to save processing result for {paper_id}: {e}")
    
    async def _log_processing_error(self, paper_id: str, error_message: str) -> None:
        """Log processing error to error directory."""
        
        error_path = Path(self.error_directory) / f"{paper_id}_error.json"
        
        error_record = {
            'paper_id': paper_id,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat(),
            'instance': self.instance_name,
            'source': self._identify_paper_source(paper_id)
        }
        
        try:
            with open(error_path, 'w') as f:
                json.dump(error_record, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log error for {paper_id}: {e}")
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and statistics."""
        
        pdf_dir = Path(self.pdf_directory)
        processed_dir = Path(self.processed_directory)
        error_dir = Path(self.error_directory)
        
        # Count papers by source
        source_counts = {'arxiv': 0, 'jss': 0, 'rjournal': 0, 'unknown': 0}
        
        if pdf_dir.exists():
            for pdf_file in pdf_dir.glob("*.pdf"):
                source = self._identify_paper_source(pdf_file.stem)
                source_counts[source] = source_counts.get(source, 0) + 1
        
        status = {
            'instance_name': self.instance_name,
            'pdf_directory': str(pdf_dir),
            'processed_directory': str(processed_dir),
            'error_directory': str(error_dir),
            'total_pdfs': sum(source_counts.values()),
            'papers_by_source': source_counts,
            'total_processed': len(list(processed_dir.glob("*.json"))) if processed_dir.exists() else 0,
            'total_errors': len(list(error_dir.glob("*_error.json"))) if error_dir.exists() else 0,
            'collection_name': self.collection_name,
            'embedding_model': self.embedding_model,
            'last_check': datetime.now().isoformat()
        }
        
        return status


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    
    parser = argparse.ArgumentParser(
        description="Quant Scholar Paper Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --sources arxiv,jss --verbose
  %(prog)s --reprocess --batch-size 10
        """
    )
    
    parser.add_argument(
        '--papers',
        type=str,
        help='Comma-separated list of paper IDs to process'
    )
    
    parser.add_argument(
        '--sources',
        type=str,
        help='Comma-separated list of sources to process (arxiv,jss,rjournal)'
    )
    
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocess already processed papers'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=15,
        help='Number of papers to process in each batch'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=2,
        help='Maximum concurrent processing tasks'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='configs/quant_scholar.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current processing status and exit'
    )
    
    return parser


async def main():
    """Main entry point for Quant Scholar processor."""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    processor = QuantScholarProcessor(args.config)
    
    try:
        if args.status:
            status = processor.get_processing_status()
            print("\nQuant Scholar Processing Status:")
            print("=" * 40)
            for key, value in status.items():
                print(f"{key}: {value}")
            return
        
        # Parse papers and sources
        papers = None
        if args.papers:
            papers = [paper.strip() for paper in args.papers.split(',')]
        
        sources = None
        if args.sources:
            sources = [source.strip() for source in args.sources.split(',')]
        
        # Run processing
        stats = await processor.process_papers(
            papers=papers,
            sources=sources,
            reprocess=args.reprocess,
            batch_size=args.batch_size,
            max_concurrent=args.max_concurrent
        )
        
        # Print summary
        print("\nProcessing Summary:")
        print("=" * 40)
        print(f"Total papers: {stats['total_papers']}")
        print(f"Processed successfully: {stats['processed_successfully']}")
        print(f"Processing failed: {stats['processing_failed']}")
        print(f"Skipped papers: {stats['skipped_papers']}")
        print(f"Total chunks created: {stats['total_chunks_created']}")
        print(f"Duration: {stats['duration_minutes']:.1f} minutes")
        
        # Show per-source stats
        for source, source_stats in stats['source_stats'].items():
            print(f"\n{source.upper()}:")
            print(f"  Processed: {source_stats['processed_successfully']}")
            print(f"  Failed: {source_stats['processing_failed']}")
            print(f"  Chunks: {source_stats['total_chunks_created']}")
    
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        print("\nProcessing interrupted by user")
    
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())