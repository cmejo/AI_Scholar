"""
Zotero Citation Service

This service handles citation generation, formatting, and bibliography creation
for Zotero references. It supports multiple citation styles and output formats.
"""
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.zotero_models import ZoteroItem, ZoteroCitationStyle, ZoteroUserPreferences
from models.zotero_schemas import (
    CitationRequest, CitationResponse, BibliographyRequest, BibliographyResponse,
    ZoteroCreator
)
from services.zotero.citation_formatter import (
    CoreCitationEngine, CitationStyle, OutputFormat,
    CitationFormattingError, CitationValidationError as FormatterValidationError
)
from core.database import get_db
from core.logging_config import get_logger

logger = get_logger(__name__)


class CitationStyleError(Exception):
    """Exception raised for citation style related errors"""
    pass


class CitationValidationError(Exception):
    """Exception raised for citation validation errors"""
    pass


class ZoteroCitationService:
    """Service for handling citation generation and formatting"""
    
    def __init__(self, db: Session):
        self.db = db
        self.citation_engine = CoreCitationEngine()
        self.supported_styles = {
            'apa': 'American Psychological Association 7th edition',
            'mla': 'Modern Language Association 9th edition',
            'chicago': 'Chicago Manual of Style 17th edition (author-date)',
            'chicago-note': 'Chicago Manual of Style 17th edition (notes-bibliography)',
            'ieee': 'Institute of Electrical and Electronics Engineers'
        }
        self.supported_formats = ['text', 'html', 'rtf']
    
    async def generate_citations(
        self,
        item_ids: List[str],
        citation_style: str = 'apa',
        format_type: str = 'text',
        locale: str = 'en-US',
        user_id: Optional[str] = None
    ) -> CitationResponse:
        """
        Generate citations for specified items
        
        Args:
            item_ids: List of Zotero item IDs
            citation_style: Citation style to use
            format_type: Output format (text, html, rtf)
            locale: Locale for formatting
            user_id: User ID for preferences
            
        Returns:
            CitationResponse with generated citations
        """
        start_time = datetime.now()
        
        try:
            # Validate inputs
            self._validate_citation_request(item_ids, citation_style, format_type)
            
            # Get user preferences if available
            if user_id:
                preferences = await self._get_user_preferences(user_id)
                if preferences and preferences.default_citation_style_id:
                    style_info = await self._get_citation_style(preferences.default_citation_style_id)
                    if style_info:
                        citation_style = style_info.style_name
            
            # Fetch items from database
            items = await self._get_items_by_ids(item_ids)
            if not items:
                raise CitationValidationError("No valid items found for citation")
            
            # Generate citations for each item
            citations = []
            for item in items:
                try:
                    citation = await self._format_citation(item, citation_style, format_type, locale)
                    citations.append(citation)
                except Exception as e:
                    logger.warning(f"Failed to generate citation for item {item.id}: {str(e)}")
                    # Add placeholder citation for failed items
                    citations.append(f"[Citation error for item {item.id}]")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Add to citation history
            try:
                from services.zotero.zotero_citation_management_service import ZoteroCitationManagementService
                management_service = ZoteroCitationManagementService(self.db)
                await management_service.add_to_citation_history(
                    user_id=user_id,
                    item_ids=item_ids,
                    citation_style=citation_style,
                    format_type=format_type,
                    citations=citations
                )
            except Exception as e:
                logger.warning(f"Failed to add citations to history: {str(e)}")
            
            return CitationResponse(
                citations=citations,
                style_used=citation_style,
                format=format_type,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Citation generation failed: {str(e)}")
            raise CitationStyleError(f"Failed to generate citations: {str(e)}")
    
    async def generate_bibliography(
        self,
        item_ids: List[str],
        citation_style: str = 'apa',
        format_type: str = 'text',
        sort_by: str = 'author',
        user_id: Optional[str] = None
    ) -> BibliographyResponse:
        """
        Generate bibliography for specified items
        
        Args:
            item_ids: List of Zotero item IDs
            citation_style: Citation style to use
            format_type: Output format
            sort_by: Sort order for bibliography
            user_id: User ID for preferences
            
        Returns:
            BibliographyResponse with generated bibliography
        """
        start_time = datetime.now()
        
        try:
            # Validate inputs
            self._validate_citation_request(item_ids, citation_style, format_type)
            
            # Get user preferences if available
            if user_id:
                preferences = await self._get_user_preferences(user_id)
                if preferences and preferences.default_citation_style_id:
                    style_info = await self._get_citation_style(preferences.default_citation_style_id)
                    if style_info:
                        citation_style = style_info.style_name
            
            # Fetch and sort items
            items = await self._get_items_by_ids(item_ids)
            if not items:
                raise CitationValidationError("No valid items found for bibliography")
            
            # Sort items according to specified order
            sorted_items = await self._sort_items_for_bibliography(items, sort_by)
            
            # Generate bibliography entries using batch processing
            bibliography_entries = await self._batch_generate_bibliography_entries(
                sorted_items, citation_style, format_type
            )
            
            # Combine entries into final bibliography
            bibliography = await self._combine_bibliography_entries(
                bibliography_entries, format_type, citation_style
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return BibliographyResponse(
                bibliography=bibliography,
                item_count=len(items),
                style_used=citation_style,
                format=format_type,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Bibliography generation failed: {str(e)}")
            raise CitationStyleError(f"Failed to generate bibliography: {str(e)}")
    
    async def validate_citation_data(self, item: ZoteroItem) -> Dict[str, Any]:
        """
        Validate citation data for an item and identify missing fields
        
        Args:
            item: ZoteroItem to validate
            
        Returns:
            Dictionary with validation results and missing fields
        """
        try:
            # Use the core citation engine for validation
            return self.citation_engine.validate_item_for_citation(item)
        except Exception as e:
            logger.error(f"Validation failed for item {item.id}: {str(e)}")
            return {
                'is_valid': False,
                'missing_fields': [],
                'warnings': [f"Validation error: {str(e)}"],
                'item_type': item.item_type
            }
    
    async def get_supported_styles(self) -> Dict[str, str]:
        """Get list of supported citation styles"""
        return self.supported_styles.copy()
    
    async def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats"""
        return self.supported_formats.copy()
    
    # Private methods
    
    def _validate_citation_request(
        self,
        item_ids: List[str],
        citation_style: str,
        format_type: str
    ) -> None:
        """Validate citation request parameters"""
        if not item_ids:
            raise CitationValidationError("No item IDs provided")
        
        if len(item_ids) > 100:
            raise CitationValidationError("Too many items requested (max 100)")
        
        if citation_style not in self.supported_styles:
            raise CitationValidationError(f"Unsupported citation style: {citation_style}")
        
        if format_type not in self.supported_formats:
            raise CitationValidationError(f"Unsupported format: {format_type}")
    
    async def _get_items_by_ids(self, item_ids: List[str]) -> List[ZoteroItem]:
        """Fetch items from database by IDs"""
        items = self.db.query(ZoteroItem).filter(
            and_(
                ZoteroItem.id.in_(item_ids),
                ZoteroItem.is_deleted == False
            )
        ).all()
        
        return items
    
    async def _get_user_preferences(self, user_id: str) -> Optional[ZoteroUserPreferences]:
        """Get user preferences"""
        return self.db.query(ZoteroUserPreferences).filter(
            ZoteroUserPreferences.user_id == user_id
        ).first()
    
    async def _get_citation_style(self, style_id: str) -> Optional[ZoteroCitationStyle]:
        """Get citation style by ID"""
        return self.db.query(ZoteroCitationStyle).filter(
            and_(
                ZoteroCitationStyle.id == style_id,
                ZoteroCitationStyle.is_active == True
            )
        ).first()
    
    async def _format_citation(
        self,
        item: ZoteroItem,
        style: str,
        format_type: str,
        locale: str
    ) -> str:
        """Format a single citation using the core citation engine"""
        try:
            # Convert string style to enum
            citation_style = CitationStyle(style)
            output_format = OutputFormat(format_type)
            
            # Use the core citation engine
            return self.citation_engine.format_citation(item, citation_style, output_format)
            
        except ValueError as e:
            # Handle invalid style or format
            raise CitationStyleError(f"Invalid citation style or format: {str(e)}")
        except CitationFormattingError as e:
            # Re-raise formatting errors
            raise CitationStyleError(str(e))
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error formatting citation: {str(e)}")
            raise CitationStyleError(f"Citation formatting failed: {str(e)}")
    
    async def _format_bibliography_entry(
        self,
        item: ZoteroItem,
        style: str,
        format_type: str
    ) -> str:
        """Format a bibliography entry using the core citation engine"""
        try:
            # Convert string style to enum
            citation_style = CitationStyle(style)
            output_format = OutputFormat(format_type)
            
            # Use the core citation engine
            return self.citation_engine.format_bibliography_entry(item, citation_style, output_format)
            
        except ValueError as e:
            # Handle invalid style or format
            raise CitationStyleError(f"Invalid citation style or format: {str(e)}")
        except CitationFormattingError as e:
            # Re-raise formatting errors
            raise CitationStyleError(str(e))
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error formatting bibliography entry: {str(e)}")
            raise CitationStyleError(f"Bibliography formatting failed: {str(e)}")
    
    # Legacy formatting methods removed - now using CoreCitationEngine
    
    async def _sort_items_for_bibliography(
        self,
        items: List[ZoteroItem],
        sort_by: str
    ) -> List[ZoteroItem]:
        """Sort items for bibliography"""
        if sort_by == 'author':
            return sorted(items, key=lambda x: self._get_sort_key_author(x))
        elif sort_by == 'title':
            return sorted(items, key=lambda x: x.title or '')
        elif sort_by == 'year':
            return sorted(items, key=lambda x: x.publication_year or 0, reverse=True)
        else:
            return items
    
    def _get_sort_key_author(self, item: ZoteroItem) -> str:
        """Get sort key for author sorting"""
        if not item.creators:
            return 'zzz'  # Put items without authors at the end
        
        for creator in item.creators:
            if creator.get('creator_type') == 'author':
                if creator.get('name'):
                    return creator['name'].lower()
                elif creator.get('last_name'):
                    return creator['last_name'].lower()
        
        return 'zzz'
    
    async def _batch_generate_bibliography_entries(
        self,
        items: List[ZoteroItem],
        citation_style: str,
        format_type: str,
        batch_size: int = 50
    ) -> List[str]:
        """
        Generate bibliography entries in batches for better performance
        
        Args:
            items: List of ZoteroItem objects
            citation_style: Citation style to use
            format_type: Output format
            batch_size: Number of items to process per batch
            
        Returns:
            List of formatted bibliography entries
        """
        bibliography_entries = []
        
        # Process items in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_entries = []
            
            for item in batch:
                try:
                    entry = await self._format_bibliography_entry(item, citation_style, format_type)
                    batch_entries.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to generate bibliography entry for item {item.id}: {str(e)}")
                    # Add placeholder entry for failed items
                    batch_entries.append(f"[Bibliography error for item {item.id}]")
            
            bibliography_entries.extend(batch_entries)
            
            # Log progress for large bibliographies
            if len(items) > 100:
                logger.info(f"Processed {min(i + batch_size, len(items))}/{len(items)} bibliography entries")
        
        return bibliography_entries

    async def generate_batch_citations(
        self,
        item_ids: List[str],
        citation_style: str = 'apa',
        format_type: str = 'text',
        batch_size: int = 100,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate citations for large batches of items with progress tracking
        
        Args:
            item_ids: List of Zotero item IDs
            citation_style: Citation style to use
            format_type: Output format
            batch_size: Number of items to process per batch
            user_id: User ID for preferences
            
        Returns:
            Dictionary with citations and processing metadata
        """
        start_time = datetime.now()
        
        try:
            # Validate inputs
            if len(item_ids) > 1000:
                raise CitationValidationError("Too many items for batch processing (max 1000)")
            
            # Get user preferences if available
            if user_id:
                preferences = await self._get_user_preferences(user_id)
                if preferences and preferences.default_citation_style_id:
                    style_info = await self._get_citation_style(preferences.default_citation_style_id)
                    if style_info:
                        citation_style = style_info.style_name
            
            # Fetch items
            items = await self._get_items_by_ids(item_ids)
            if not items:
                raise CitationValidationError("No valid items found for batch citation")
            
            # Process in batches
            all_citations = []
            failed_items = []
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_citations = []
                
                for item in batch:
                    try:
                        citation = await self._format_citation(item, citation_style, format_type, 'en-US')
                        batch_citations.append({
                            'item_id': item.id,
                            'citation': citation,
                            'status': 'success'
                        })
                    except Exception as e:
                        logger.warning(f"Failed to generate citation for item {item.id}: {str(e)}")
                        batch_citations.append({
                            'item_id': item.id,
                            'citation': f"[Citation error for item {item.id}]",
                            'status': 'error',
                            'error': str(e)
                        })
                        failed_items.append(item.id)
                
                all_citations.extend(batch_citations)
                
                # Log progress
                logger.info(f"Processed {min(i + batch_size, len(items))}/{len(items)} citations")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'citations': all_citations,
                'total_items': len(items),
                'successful_items': len(items) - len(failed_items),
                'failed_items': failed_items,
                'style_used': citation_style,
                'format': format_type,
                'processing_time': processing_time,
                'batch_size': batch_size
            }
            
        except Exception as e:
            logger.error(f"Batch citation generation failed: {str(e)}")
            raise CitationStyleError(f"Failed to generate batch citations: {str(e)}")

    async def _combine_bibliography_entries(
        self,
        entries: List[str],
        format_type: str,
        style: str
    ) -> str:
        """Combine bibliography entries into final bibliography with enhanced formatting"""
        if not entries:
            return ""
        
        if format_type == 'html':
            # Enhanced HTML formatting with proper bibliography structure
            header = f'<div class="bibliography" data-style="{style}">\n'
            header += f'<h3 class="bibliography-title">References</h3>\n'
            body = '\n'.join(
                f'<div class="bibliography-entry" data-index="{i+1}">{entry}</div>' 
                for i, entry in enumerate(entries)
            )
            footer = '\n</div>'
            return header + body + footer
            
        elif format_type == 'rtf':
            # RTF formatting with proper paragraph breaks
            rtf_header = '{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}\\f0\\fs24 '
            rtf_body = '\\par\\b References\\b0\\par\\par ' + '\\par\\par '.join(entries)
            rtf_footer = '}'
            return rtf_header + rtf_body + rtf_footer
            
        else:
            # Plain text with proper spacing and header
            return 'References\n\n' + '\n\n'.join(entries)
    
    # Legacy validation methods removed - now using CoreCitationEngine