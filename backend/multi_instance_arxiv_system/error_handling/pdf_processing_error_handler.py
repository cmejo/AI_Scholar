"""
PDF Processing Error Handler for Multi-Instance ArXiv System.

This module provides specialized handling for PDF processing errors including
corrupt files, encrypted PDFs, parsing failures, and extraction issues.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import logging
import asyncio
import hashlib
import json
from dataclasses import dataclass
from enum import Enum

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.error_handling.error_models import ProcessingError, ErrorType
except ImportError as e:
    print(f"Import error: {e}")
    # Create minimal fallback classes for testing
    class ProcessingError:
        def __init__(self, *args, **kwargs): pass
    class ErrorType:
        PDF_CORRUPT = "pdf_corrupt"
        PDF_ENCRYPTED = "pdf_encrypted"

logger = logging.getLogger(__name__)


class PDFProcessingError(Exception):
    """Custom PDF processing error exception."""
    
    def __init__(self, message: str, error_type: ErrorType, file_path: Optional[str] = None):
        super().__init__(message)
        self.error_type = error_type
        self.file_path = file_path


@dataclass
class PDFValidationResult:
    """Result of PDF validation."""
    
    is_valid: bool
    file_size: int
    is_encrypted: bool
    page_count: Optional[int] = None
    has_text: bool = False
    error_message: Optional[str] = None
    validation_time: float = 0.0


class PDFProcessingErrorHandler:
    """
    Specialized handler for PDF processing errors.
    
    Provides validation, corruption detection, encryption handling,
    and intelligent skip/retry strategies for PDF files.
    """
    
    def __init__(self, instance_name: str, quarantine_dir: Optional[str] = None):
        self.instance_name = instance_name
        self.quarantine_dir = quarantine_dir or f"quarantine/{instance_name}"
        
        # Tracking problematic files
        self.corrupted_files: Set[str] = set()
        self.encrypted_files: Set[str] = set()
        self.failed_extractions: Set[str] = set()
        
        # Statistics
        self.total_pdfs_processed = 0
        self.corrupted_pdfs = 0
        self.encrypted_pdfs = 0
        self.extraction_failures = 0
        self.successful_recoveries = 0
        
        # File hash cache for duplicate detection
        self.file_hashes: Dict[str, str] = {}
        
        # Ensure quarantine directory exists
        Path(self.quarantine_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"PDFProcessingErrorHandler initialized for {instance_name}")
    
    async def handle_error(self, error: ProcessingError) -> bool:
        """
        Handle a PDF processing error with appropriate recovery strategy.
        
        Args:
            error: The PDF processing error to handle
            
        Returns:
            True if recovery was successful, False otherwise
        """
        
        logger.info(f"Handling PDF processing error: {error.error_type.value}")
        
        file_path = error.context.file_path
        if not file_path:
            logger.warning("No file path in context for PDF processing error")
            return False
        
        # Determine recovery strategy based on error type
        if error.error_type == ErrorType.PDF_CORRUPT:
            return await self._handle_corrupt_pdf(error, file_path)
        elif error.error_type == ErrorType.PDF_ENCRYPTED:
            return await self._handle_encrypted_pdf(error, file_path)
        elif error.error_type == ErrorType.PDF_PARSING_FAILED:
            return await self._handle_parsing_failure(error, file_path)
        elif error.error_type == ErrorType.PDF_EXTRACTION_FAILED:
            return await self._handle_extraction_failure(error, file_path)
        else:
            return await self._handle_generic_pdf_error(error, file_path)
    
    async def _handle_corrupt_pdf(self, error: ProcessingError, file_path: str) -> bool:
        """Handle corrupt PDF files."""
        
        logger.info(f"Handling corrupt PDF: {file_path}")
        
        # Add to corrupted files set
        self.corrupted_files.add(file_path)
        self.corrupted_pdfs += 1
        
        # Validate the file to confirm corruption
        validation_result = await self._validate_pdf_file(file_path)
        
        if not validation_result.is_valid:
            # File is indeed corrupt, quarantine it
            await self._quarantine_file(file_path, "corrupt")
            
            # Log detailed information
            logger.warning(f"Confirmed corrupt PDF quarantined: {file_path}")
            logger.warning(f"File size: {validation_result.file_size} bytes")
            logger.warning(f"Error: {validation_result.error_message}")
            
            return True  # Successfully handled by quarantining
        else:
            # File might not be corrupt, try alternative processing
            logger.info(f"PDF validation passed, attempting alternative processing: {file_path}")
            return await self._attempt_alternative_processing(file_path)
    
    async def _handle_encrypted_pdf(self, error: ProcessingError, file_path: str) -> bool:
        """Handle encrypted PDF files."""
        
        logger.info(f"Handling encrypted PDF: {file_path}")
        
        # Add to encrypted files set
        self.encrypted_files.add(file_path)
        self.encrypted_pdfs += 1
        
        # Validate encryption status
        validation_result = await self._validate_pdf_file(file_path)
        
        if validation_result.is_encrypted:
            # Try common passwords first
            if await self._try_decrypt_pdf(file_path):
                logger.info(f"Successfully decrypted PDF: {file_path}")
                self.successful_recoveries += 1
                return True
            else:
                # Cannot decrypt, quarantine
                await self._quarantine_file(file_path, "encrypted")
                logger.warning(f"Encrypted PDF quarantined (cannot decrypt): {file_path}")
                return True  # Successfully handled by quarantining
        else:
            # Might be a false positive, try processing again
            logger.info(f"PDF not actually encrypted, retrying: {file_path}")
            return True  # Allow retry
    
    async def _handle_parsing_failure(self, error: ProcessingError, file_path: str) -> bool:
        """Handle PDF parsing failures."""
        
        logger.info(f"Handling PDF parsing failure: {file_path}")
        
        # First, validate the file
        validation_result = await self._validate_pdf_file(file_path)
        
        if not validation_result.is_valid:
            # File is corrupt
            return await self._handle_corrupt_pdf(error, file_path)
        
        # Try alternative parsing methods
        if error.recovery_attempts <= 2:
            logger.info(f"Attempting alternative parsing for: {file_path}")
            return await self._attempt_alternative_parsing(file_path)
        else:
            # Max attempts reached, quarantine
            await self._quarantine_file(file_path, "parsing_failed")
            logger.warning(f"PDF parsing failed after retries, quarantined: {file_path}")
            return True
    
    async def _handle_extraction_failure(self, error: ProcessingError, file_path: str) -> bool:
        """Handle text extraction failures."""
        
        logger.info(f"Handling text extraction failure: {file_path}")
        
        # Add to failed extractions
        self.failed_extractions.add(file_path)
        self.extraction_failures += 1
        
        # Validate the file first
        validation_result = await self._validate_pdf_file(file_path)
        
        if not validation_result.is_valid:
            return await self._handle_corrupt_pdf(error, file_path)
        
        if validation_result.is_encrypted:
            return await self._handle_encrypted_pdf(error, file_path)
        
        # Try alternative extraction methods
        if error.recovery_attempts <= 2:
            logger.info(f"Attempting alternative text extraction for: {file_path}")
            return await self._attempt_alternative_extraction(file_path)
        else:
            # Check if file has any extractable text
            if not validation_result.has_text:
                logger.info(f"PDF has no extractable text, skipping: {file_path}")
                await self._quarantine_file(file_path, "no_text")
                return True
            else:
                # Has text but extraction failed, quarantine
                await self._quarantine_file(file_path, "extraction_failed")
                logger.warning(f"Text extraction failed after retries, quarantined: {file_path}")
                return True
    
    async def _handle_generic_pdf_error(self, error: ProcessingError, file_path: str) -> bool:
        """Handle generic PDF processing errors."""
        
        logger.info(f"Handling generic PDF error: {file_path}")
        
        # Validate the file to determine the actual issue
        validation_result = await self._validate_pdf_file(file_path)
        
        if not validation_result.is_valid:
            return await self._handle_corrupt_pdf(error, file_path)
        elif validation_result.is_encrypted:
            return await self._handle_encrypted_pdf(error, file_path)
        else:
            # Unknown issue, try once more if first attempt
            if error.recovery_attempts == 1:
                logger.info(f"Retrying generic PDF processing: {file_path}")
                return True
            else:
                await self._quarantine_file(file_path, "unknown_error")
                return True
    
    async def _validate_pdf_file(self, file_path: str) -> PDFValidationResult:
        """Validate a PDF file and return detailed information."""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return PDFValidationResult(
                    is_valid=False,
                    file_size=0,
                    is_encrypted=False,
                    error_message="File does not exist",
                    validation_time=asyncio.get_event_loop().time() - start_time
                )
            
            file_size = file_path_obj.stat().st_size
            
            if file_size == 0:
                return PDFValidationResult(
                    is_valid=False,
                    file_size=0,
                    is_encrypted=False,
                    error_message="File is empty",
                    validation_time=asyncio.get_event_loop().time() - start_time
                )
            
            # Try to validate with PyPDF2 or similar library
            # For now, we'll do basic validation
            try:
                # Check if file starts with PDF header
                with open(file_path, 'rb') as f:
                    header = f.read(8)
                    if not header.startswith(b'%PDF-'):
                        return PDFValidationResult(
                            is_valid=False,
                            file_size=file_size,
                            is_encrypted=False,
                            error_message="Invalid PDF header",
                            validation_time=asyncio.get_event_loop().time() - start_time
                        )
                
                # Basic validation passed
                return PDFValidationResult(
                    is_valid=True,
                    file_size=file_size,
                    is_encrypted=False,  # Would need actual PDF library to detect
                    page_count=1,  # Placeholder
                    has_text=True,  # Placeholder
                    validation_time=asyncio.get_event_loop().time() - start_time
                )
            
            except Exception as e:
                return PDFValidationResult(
                    is_valid=False,
                    file_size=file_size,
                    is_encrypted=False,
                    error_message=str(e),
                    validation_time=asyncio.get_event_loop().time() - start_time
                )
        
        except Exception as e:
            return PDFValidationResult(
                is_valid=False,
                file_size=0,
                is_encrypted=False,
                error_message=f"Validation error: {e}",
                validation_time=asyncio.get_event_loop().time() - start_time
            )
    
    async def _quarantine_file(self, file_path: str, reason: str) -> None:
        """Move a problematic file to quarantine directory."""
        
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                logger.warning(f"Cannot quarantine non-existent file: {file_path}")
                return
            
            # Create quarantine subdirectory for the reason
            quarantine_subdir = Path(self.quarantine_dir) / reason
            quarantine_subdir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_filename = f"{timestamp}_{source_path.name}"
            quarantine_path = quarantine_subdir / quarantine_filename
            
            # Move file to quarantine
            source_path.rename(quarantine_path)
            
            # Create metadata file
            metadata = {
                'original_path': str(source_path),
                'quarantine_reason': reason,
                'quarantine_time': datetime.now().isoformat(),
                'file_size': quarantine_path.stat().st_size,
                'instance_name': self.instance_name
            }
            
            metadata_path = quarantine_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"File quarantined: {file_path} -> {quarantine_path}")
        
        except Exception as e:
            logger.error(f"Failed to quarantine file {file_path}: {e}")
    
    async def _try_decrypt_pdf(self, file_path: str) -> bool:
        """Try to decrypt PDF with common passwords."""
        
        # Common passwords to try
        common_passwords = [
            "",  # Empty password
            "password",
            "123456",
            "admin",
            "user",
            "pdf",
            "document"
        ]
        
        # This would require a PDF library like PyPDF2
        # For now, return False (cannot decrypt)
        logger.info(f"Attempting to decrypt PDF: {file_path}")
        
        # Placeholder - would implement actual decryption logic
        return False
    
    async def _attempt_alternative_processing(self, file_path: str) -> bool:
        """Attempt alternative PDF processing methods."""
        
        logger.info(f"Attempting alternative processing for: {file_path}")
        
        # This would try different PDF libraries or processing methods
        # For now, return True to allow retry
        return True
    
    async def _attempt_alternative_parsing(self, file_path: str) -> bool:
        """Attempt alternative PDF parsing methods."""
        
        logger.info(f"Attempting alternative parsing for: {file_path}")
        
        # This would try different parsing libraries
        # For now, return True to allow retry
        return True
    
    async def _attempt_alternative_extraction(self, file_path: str) -> bool:
        """Attempt alternative text extraction methods."""
        
        logger.info(f"Attempting alternative text extraction for: {file_path}")
        
        # This would try different extraction methods (OCR, etc.)
        # For now, return True to allow retry
        return True
    
    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Get SHA-256 hash of a file for duplicate detection."""
        
        try:
            if file_path in self.file_hashes:
                return self.file_hashes[file_path]
            
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            
            file_hash = hash_sha256.hexdigest()
            self.file_hashes[file_path] = file_hash
            return file_hash
        
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    def is_problematic_file(self, file_path: str) -> bool:
        """Check if a file is known to be problematic."""
        
        return (file_path in self.corrupted_files or
                file_path in self.encrypted_files or
                file_path in self.failed_extractions)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get PDF processing error handler statistics."""
        
        success_rate = 0.0
        if self.total_pdfs_processed > 0:
            failed_pdfs = self.corrupted_pdfs + self.encrypted_pdfs + self.extraction_failures
            success_rate = ((self.total_pdfs_processed - failed_pdfs) / self.total_pdfs_processed) * 100
        
        return {
            'instance_name': self.instance_name,
            'total_pdfs_processed': self.total_pdfs_processed,
            'corrupted_pdfs': self.corrupted_pdfs,
            'encrypted_pdfs': self.encrypted_pdfs,
            'extraction_failures': self.extraction_failures,
            'successful_recoveries': self.successful_recoveries,
            'success_rate': success_rate,
            'quarantine_directory': self.quarantine_dir,
            'problematic_files_count': len(self.corrupted_files) + len(self.encrypted_files) + len(self.failed_extractions)
        }
    
    def clear_problematic_files_cache(self) -> None:
        """Clear the cache of problematic files."""
        
        self.corrupted_files.clear()
        self.encrypted_files.clear()
        self.failed_extractions.clear()
        self.file_hashes.clear()
        
        logger.info(f"Cleared problematic files cache for {self.instance_name}")
    
    async def cleanup_quarantine(self, older_than: timedelta = timedelta(days=30)) -> int:
        """Clean up old quarantined files."""
        
        cleaned_count = 0
        cutoff_time = datetime.now() - older_than
        
        try:
            quarantine_path = Path(self.quarantine_dir)
            if not quarantine_path.exists():
                return 0
            
            for file_path in quarantine_path.rglob("*"):
                if file_path.is_file():
                    # Check file modification time
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old quarantined files")
        
        except Exception as e:
            logger.error(f"Error cleaning up quarantine: {e}")
        
        return cleaned_count
    
    def get_quarantine_summary(self) -> Dict[str, Any]:
        """Get summary of quarantined files."""
        
        summary = {
            'quarantine_directory': self.quarantine_dir,
            'categories': {},
            'total_files': 0,
            'total_size_mb': 0.0
        }
        
        try:
            quarantine_path = Path(self.quarantine_dir)
            if not quarantine_path.exists():
                return summary
            
            for category_dir in quarantine_path.iterdir():
                if category_dir.is_dir():
                    category_files = list(category_dir.glob("*.pdf"))
                    category_size = sum(f.stat().st_size for f in category_files if f.exists())
                    
                    summary['categories'][category_dir.name] = {
                        'file_count': len(category_files),
                        'size_mb': category_size / (1024 * 1024)
                    }
                    
                    summary['total_files'] += len(category_files)
                    summary['total_size_mb'] += category_size / (1024 * 1024)
        
        except Exception as e:
            logger.error(f"Error getting quarantine summary: {e}")
        
        return summary