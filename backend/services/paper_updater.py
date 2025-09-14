"""
Paper Update Service for AI Scholar
Handles automatic checking and processing of new papers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import json
import hashlib

from .scientific_pdf_processor import scientific_pdf_processor
from .vector_store_service import vector_store_service
from .scientific_rag_service import scientific_rag_service

logger = logging.getLogger(__name__)

class PaperUpdateService:
    """Service for automatically updating the paper database"""
    
    def __init__(self, dataset_path: str = "/home/cmejo/arxiv-dataset/pdf"):
        self.dataset_path = Path(dataset_path)
        self.processed_files_cache = Path("processed_files.json")
        self.last_check_file = Path("last_update_check.json")
        self.processed_files: Set[str] = set()
        self.new_papers_count = 0
        
    async def initialize(self):
        """Initialize the update service"""
        try:
            # Load processed files cache
            await self.load_processed_files_cache()
            
            # Initialize vector store
            await vector_store_service.initialize()
            
            logger.info("Paper update service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize paper update service: {e}")
            return False
    
    async def load_processed_files_cache(self):
        """Load the cache of already processed files"""
        try:
            if self.processed_files_cache.exists():
                with open(self.processed_files_cache, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed_files', []))
                    logger.info(f"Loaded {len(self.processed_files)} processed files from cache")
            else:
                logger.info("No processed files cache found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading processed files cache: {e}")
            self.processed_files = set()
    
    async def save_processed_files_cache(self):
        """Save the cache of processed files"""
        try:
            cache_data = {
                'processed_files': list(self.processed_files),
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.processed_files)
            }
            
            with open(self.processed_files_cache, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved {len(self.processed_files)} processed files to cache")
        except Exception as e:
            logger.error(f"Error saving processed files cache: {e}")
    
    async def check_for_new_papers(self) -> Dict[str, any]:
        """Check for new papers in the dataset"""
        try:
            if not self.dataset_path.exists():
                logger.warning(f"Dataset path does not exist: {self.dataset_path}")
                return {'new_papers': [], 'total_papers': 0, 'error': 'Dataset path not found'}
            
            # Get all PDF files
            all_pdf_files = list(self.dataset_path.rglob("*.pdf"))
            
            # Find new files (not in processed cache)
            new_files = []
            for pdf_file in all_pdf_files:
                file_hash = self.get_file_hash(pdf_file)
                if file_hash not in self.processed_files:
                    new_files.append({
                        'path': str(pdf_file),
                        'name': pdf_file.name,
                        'size': pdf_file.stat().st_size,
                        'modified': datetime.fromtimestamp(pdf_file.stat().st_mtime).isoformat(),
                        'hash': file_hash
                    })
            
            logger.info(f"Found {len(new_files)} new papers out of {len(all_pdf_files)} total")
            
            return {
                'new_papers': new_files,
                'new_count': len(new_files),
                'total_papers': len(all_pdf_files),
                'processed_count': len(self.processed_files),
                'check_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking for new papers: {e}")
            return {'error': str(e), 'new_papers': [], 'total_papers': 0}
    
    def get_file_hash(self, file_path: Path) -> str:
        """Generate a hash for a file based on path and modification time"""
        file_info = f"{file_path.name}_{file_path.stat().st_size}_{file_path.stat().st_mtime}"
        return hashlib.md5(file_info.encode()).hexdigest()
    
    async def process_new_papers(self, max_papers: int = 10) -> Dict[str, any]:
        """Process new papers found in the dataset"""
        try:
            # Check for new papers
            check_result = await self.check_for_new_papers()
            
            if check_result.get('error'):
                return check_result
            
            new_papers = check_result['new_papers'][:max_papers]  # Limit processing
            
            if not new_papers:
                logger.info("No new papers to process")
                return {
                    'processed_count': 0,
                    'failed_count': 0,
                    'message': 'No new papers found',
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"Processing {len(new_papers)} new papers...")
            
            processed_count = 0
            failed_count = 0
            
            for paper_info in new_papers:
                try:
                    pdf_path = Path(paper_info['path'])
                    
                    # Extract content from PDF
                    document_data = scientific_pdf_processor.extract_comprehensive_content(str(pdf_path))
                    
                    # Create chunks for vector storage
                    chunks = scientific_rag_service._create_scientific_chunks(document_data)
                    
                    if chunks:
                        # Add to vector store
                        await vector_store_service.add_document_chunks(
                            document_data['document_id'],
                            chunks
                        )
                        
                        # Add to processed files cache
                        self.processed_files.add(paper_info['hash'])
                        processed_count += 1
                        
                        logger.info(f"Successfully processed: {pdf_path.name}")
                    else:
                        logger.warning(f"No chunks created for: {pdf_path.name}")
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process {paper_info['name']}: {e}")
                    failed_count += 1
            
            # Save updated cache
            await self.save_processed_files_cache()
            
            # Update last check time
            await self.save_last_check_time()
            
            result = {
                'processed_count': processed_count,
                'failed_count': failed_count,
                'total_new_papers': len(check_result['new_papers']),
                'message': f'Successfully processed {processed_count} new papers',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Paper processing complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing new papers: {e}")
            return {
                'error': str(e),
                'processed_count': 0,
                'failed_count': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    async def save_last_check_time(self):
        """Save the last check time"""
        try:
            check_data = {
                'last_check': datetime.now().isoformat(),
                'papers_processed': len(self.processed_files)
            }
            
            with open(self.last_check_file, 'w') as f:
                json.dump(check_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving last check time: {e}")
    
    async def get_last_check_time(self) -> Optional[datetime]:
        """Get the last check time"""
        try:
            if self.last_check_file.exists():
                with open(self.last_check_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data['last_check'])
        except Exception as e:
            logger.error(f"Error getting last check time: {e}")
        
        return None
    
    async def should_check_for_updates(self, check_interval_hours: int = 24) -> bool:
        """Check if it's time to look for updates"""
        last_check = await self.get_last_check_time()
        
        if not last_check:
            return True  # Never checked before
        
        time_since_check = datetime.now() - last_check
        return time_since_check >= timedelta(hours=check_interval_hours)
    
    async def get_update_status(self) -> Dict[str, any]:
        """Get current update status"""
        try:
            last_check = await self.get_last_check_time()
            should_check = await self.should_check_for_updates()
            
            # Quick check for new papers count
            check_result = await self.check_for_new_papers()
            
            return {
                'last_check': last_check.isoformat() if last_check else None,
                'should_check': should_check,
                'processed_papers_count': len(self.processed_files),
                'new_papers_available': check_result.get('new_count', 0),
                'total_papers_in_dataset': check_result.get('total_papers', 0),
                'service_status': 'healthy',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting update status: {e}")
            return {
                'error': str(e),
                'service_status': 'error',
                'timestamp': datetime.now().isoformat()
            }

# Global instance
paper_updater = PaperUpdateService()