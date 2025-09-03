"""
Zotero Export Service

This service handles exporting Zotero references to various formats including
BibTeX, RIS, EndNote, and other academic reference formats.
"""
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.zotero_models import ZoteroItem
from models.zotero_schemas import ZoteroExportRequest, ZoteroExportResponse
from core.database import get_db
from core.logging_config import get_logger

logger = get_logger(__name__)


class ExportFormatError(Exception):
    """Exception raised for export format related errors"""
    pass


class ExportValidationError(Exception):
    """Exception raised for export validation errors"""
    pass


class ZoteroExportService:
    """Service for handling reference export functionality"""
    
    def __init__(self, db: Session):
        self.db = db
        self.supported_formats = {
            'bibtex': 'BibTeX format (.bib)',
            'ris': 'Research Information Systems format (.ris)',
            'endnote': 'EndNote format (.enw)',
            'json': 'JSON format (.json)',
            'csv': 'Comma-separated values (.csv)',
            'tsv': 'Tab-separated values (.tsv)'
        }
    
    async def export_references(
        self,
        item_ids: List[str],
        export_format: str,
        include_attachments: bool = False,
        include_notes: bool = True,
        user_id: Optional[str] = None
    ) -> ZoteroExportResponse:
        """
        Export references to specified format with enhanced batch processing
        
        Args:
            item_ids: List of Zotero item IDs to export
            export_format: Export format (bibtex, ris, endnote, etc.)
            include_attachments: Whether to include attachment information
            include_notes: Whether to include notes and abstracts
            user_id: User ID for access control
            
        Returns:
            ZoteroExportResponse with exported data
        """
        start_time = datetime.now()
        
        try:
            # Validate inputs
            self._validate_export_request(item_ids, export_format)
            
            # Fetch items from database
            items = await self._get_items_by_ids(item_ids)
            if not items:
                raise ExportValidationError("No valid items found for export")
            
            # Use batch processing for large exports
            if len(items) > 100:
                export_data = await self._batch_export_references(
                    items, export_format, include_attachments, include_notes
                )
            else:
                # Export based on format
                if export_format == 'bibtex':
                    export_data = await self._export_bibtex(items, include_notes)
                elif export_format == 'ris':
                    export_data = await self._export_ris(items, include_notes)
                elif export_format == 'endnote':
                    export_data = await self._export_endnote(items, include_notes)
                elif export_format == 'json':
                    export_data = await self._export_json(items, include_attachments, include_notes)
                elif export_format == 'csv':
                    export_data = await self._export_csv(items, include_notes)
                elif export_format == 'tsv':
                    export_data = await self._export_tsv(items, include_notes)
                else:
                    raise ExportFormatError(f"Unsupported export format: {export_format}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ZoteroExportResponse(
                export_data=export_data,
                export_format=export_format,
                item_count=len(items),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise ExportFormatError(f"Failed to export references: {str(e)}")

    async def batch_export_by_collection(
        self,
        collection_id: str,
        export_format: str,
        include_attachments: bool = False,
        include_notes: bool = True,
        user_id: Optional[str] = None
    ) -> ZoteroExportResponse:
        """
        Export all references from a collection in batches
        
        Args:
            collection_id: Collection ID to export
            export_format: Export format
            include_attachments: Whether to include attachment info
            include_notes: Whether to include notes
            user_id: User ID for access control
            
        Returns:
            ZoteroExportResponse with exported collection data
        """
        try:
            # Get all items in the collection
            from models.zotero_models import ZoteroItemCollection
            
            item_ids = self.db.query(ZoteroItemCollection.item_id).filter(
                ZoteroItemCollection.collection_id == collection_id
            ).all()
            
            if not item_ids:
                raise ExportValidationError("Collection not found or empty")
            
            item_ids = [item_id[0] for item_id in item_ids]
            
            # Use the regular export method which now handles batching
            return await self.export_references(
                item_ids=item_ids,
                export_format=export_format,
                include_attachments=include_attachments,
                include_notes=include_notes,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Batch collection export failed: {str(e)}")
            raise ExportFormatError(f"Failed to export collection: {str(e)}")
    
    async def get_supported_formats(self) -> Dict[str, str]:
        """Get list of supported export formats"""
        return self.supported_formats.copy()
    
    # Private methods
    
    def _validate_export_request(self, item_ids: List[str], export_format: str) -> None:
        """Validate export request parameters"""
        if not item_ids:
            raise ExportValidationError("No item IDs provided")
        
        if len(item_ids) > 1000:
            raise ExportValidationError("Too many items requested (max 1000)")
        
        if export_format not in self.supported_formats:
            raise ExportValidationError(f"Unsupported export format: {export_format}")
    
    async def _get_items_by_ids(self, item_ids: List[str]) -> List[ZoteroItem]:
        """Fetch items from database by IDs"""
        items = self.db.query(ZoteroItem).filter(
            and_(
                ZoteroItem.id.in_(item_ids),
                ZoteroItem.is_deleted == False
            )
        ).all()
        
        return items
    
    async def _export_bibtex(self, items: List[ZoteroItem], include_notes: bool) -> str:
        """Export items to BibTeX format"""
        bibtex_entries = []
        
        for item in items:
            try:
                entry = await self._format_bibtex_entry(item, include_notes)
                bibtex_entries.append(entry)
            except Exception as e:
                logger.warning(f"Failed to format BibTeX entry for item {item.id}: {str(e)}")
                # Continue with other items
        
        return '\n\n'.join(bibtex_entries)
    
    async def _format_bibtex_entry(self, item: ZoteroItem, include_notes: bool) -> str:
        """Format a single BibTeX entry"""
        # Map Zotero item types to BibTeX entry types
        type_mapping = {
            'article': 'article',
            'book': 'book',
            'bookSection': 'inbook',
            'conferencePaper': 'inproceedings',
            'thesis': 'phdthesis',
            'report': 'techreport',
            'webpage': 'misc',
            'journalArticle': 'article'
        }
        
        bibtex_type = type_mapping.get(item.item_type, 'misc')
        
        # Generate citation key
        citation_key = self._generate_citation_key(item)
        
        # Start entry
        entry_lines = [f"@{bibtex_type}{{{citation_key},"]
        
        # Add fields
        if item.title:
            entry_lines.append(f"  title = {{{item.title}}},")
        
        # Authors
        if item.creators:
            authors = self._format_bibtex_authors(item.creators)
            if authors:
                entry_lines.append(f"  author = {{{authors}}},")
        
        # Journal/Publication
        if item.publication_title:
            if item.item_type in ['article', 'journalArticle']:
                entry_lines.append(f"  journal = {{{item.publication_title}}},")
            elif item.item_type == 'conferencePaper':
                entry_lines.append(f"  booktitle = {{{item.publication_title}}},")
            else:
                entry_lines.append(f"  publisher = {{{item.publication_title}}},")
        
        # Publisher
        if item.publisher and item.item_type in ['book', 'bookSection', 'report']:
            entry_lines.append(f"  publisher = {{{item.publisher}}},")
        
        # Year
        if item.publication_year:
            entry_lines.append(f"  year = {{{item.publication_year}}},")
        
        # DOI
        if item.doi:
            entry_lines.append(f"  doi = {{{item.doi}}},")
        
        # ISBN
        if item.isbn:
            entry_lines.append(f"  isbn = {{{item.isbn}}},")
        
        # ISSN
        if item.issn:
            entry_lines.append(f"  issn = {{{item.issn}}},")
        
        # URL
        if item.url:
            entry_lines.append(f"  url = {{{item.url}}},")
        
        # Abstract/Note
        if include_notes and item.abstract_note:
            # Clean abstract for BibTeX
            clean_abstract = self._clean_text_for_bibtex(item.abstract_note)
            entry_lines.append(f"  abstract = {{{clean_abstract}}},")
        
        # Keywords/Tags
        if item.tags:
            keywords = ', '.join(item.tags)
            entry_lines.append(f"  keywords = {{{keywords}}},")
        
        # Remove trailing comma from last field
        if entry_lines[-1].endswith(','):
            entry_lines[-1] = entry_lines[-1][:-1]
        
        # Close entry
        entry_lines.append("}")
        
        return '\n'.join(entry_lines)
    
    async def _export_ris(self, items: List[ZoteroItem], include_notes: bool) -> str:
        """Export items to RIS format"""
        ris_entries = []
        
        for item in items:
            try:
                entry = await self._format_ris_entry(item, include_notes)
                ris_entries.append(entry)
            except Exception as e:
                logger.warning(f"Failed to format RIS entry for item {item.id}: {str(e)}")
        
        return '\n\n'.join(ris_entries)
    
    async def _format_ris_entry(self, item: ZoteroItem, include_notes: bool) -> str:
        """Format a single RIS entry"""
        # Map Zotero item types to RIS types
        type_mapping = {
            'article': 'JOUR',
            'journalArticle': 'JOUR',
            'book': 'BOOK',
            'bookSection': 'CHAP',
            'conferencePaper': 'CONF',
            'thesis': 'THES',
            'report': 'RPRT',
            'webpage': 'ELEC'
        }
        
        ris_type = type_mapping.get(item.item_type, 'GEN')
        
        # Start entry
        entry_lines = [f"TY  - {ris_type}"]
        
        # Title
        if item.title:
            entry_lines.append(f"TI  - {item.title}")
        
        # Authors
        if item.creators:
            for creator in item.creators:
                if creator.get('creator_type') == 'author':
                    if creator.get('name'):  # Organization
                        entry_lines.append(f"AU  - {creator['name']}")
                    else:
                        last = creator.get('last_name', '')
                        first = creator.get('first_name', '')
                        if last and first:
                            entry_lines.append(f"AU  - {last}, {first}")
                        elif last:
                            entry_lines.append(f"AU  - {last}")
        
        # Journal/Publication
        if item.publication_title:
            if item.item_type in ['article', 'journalArticle']:
                entry_lines.append(f"JO  - {item.publication_title}")
            else:
                entry_lines.append(f"T2  - {item.publication_title}")
        
        # Publisher
        if item.publisher:
            entry_lines.append(f"PB  - {item.publisher}")
        
        # Year
        if item.publication_year:
            entry_lines.append(f"PY  - {item.publication_year}")
        
        # DOI
        if item.doi:
            entry_lines.append(f"DO  - {item.doi}")
        
        # ISBN
        if item.isbn:
            entry_lines.append(f"SN  - {item.isbn}")
        
        # URL
        if item.url:
            entry_lines.append(f"UR  - {item.url}")
        
        # Abstract
        if include_notes and item.abstract_note:
            entry_lines.append(f"AB  - {item.abstract_note}")
        
        # Keywords
        if item.tags:
            for tag in item.tags:
                entry_lines.append(f"KW  - {tag}")
        
        # End entry
        entry_lines.append("ER  - ")
        
        return '\n'.join(entry_lines)
    
    async def _export_endnote(self, items: List[ZoteroItem], include_notes: bool) -> str:
        """Export items to EndNote format"""
        endnote_entries = []
        
        for item in items:
            try:
                entry = await self._format_endnote_entry(item, include_notes)
                endnote_entries.append(entry)
            except Exception as e:
                logger.warning(f"Failed to format EndNote entry for item {item.id}: {str(e)}")
        
        return '\n\n'.join(endnote_entries)
    
    async def _format_endnote_entry(self, item: ZoteroItem, include_notes: bool) -> str:
        """Format a single EndNote entry"""
        # Map Zotero item types to EndNote reference types
        type_mapping = {
            'article': '0',
            'journalArticle': '0',
            'book': '6',
            'bookSection': '5',
            'conferencePaper': '10',
            'thesis': '32',
            'report': '27',
            'webpage': '12'
        }
        
        endnote_type = type_mapping.get(item.item_type, '13')  # Generic
        
        entry_lines = [f"%0 Journal Article" if item.item_type in ['article', 'journalArticle'] else f"%0 {item.item_type.title()}"]
        
        # Title
        if item.title:
            entry_lines.append(f"%T {item.title}")
        
        # Authors
        if item.creators:
            for creator in item.creators:
                if creator.get('creator_type') == 'author':
                    if creator.get('name'):  # Organization
                        entry_lines.append(f"%A {creator['name']}")
                    else:
                        last = creator.get('last_name', '')
                        first = creator.get('first_name', '')
                        if last and first:
                            entry_lines.append(f"%A {last}, {first}")
                        elif last:
                            entry_lines.append(f"%A {last}")
        
        # Journal/Publication
        if item.publication_title:
            if item.item_type in ['article', 'journalArticle']:
                entry_lines.append(f"%J {item.publication_title}")
            else:
                entry_lines.append(f"%B {item.publication_title}")
        
        # Publisher
        if item.publisher:
            entry_lines.append(f"%I {item.publisher}")
        
        # Year
        if item.publication_year:
            entry_lines.append(f"%D {item.publication_year}")
        
        # DOI
        if item.doi:
            entry_lines.append(f"%R {item.doi}")
        
        # ISBN
        if item.isbn:
            entry_lines.append(f"%@ {item.isbn}")
        
        # URL
        if item.url:
            entry_lines.append(f"%U {item.url}")
        
        # Abstract
        if include_notes and item.abstract_note:
            entry_lines.append(f"%X {item.abstract_note}")
        
        # Keywords
        if item.tags:
            keywords = '; '.join(item.tags)
            entry_lines.append(f"%K {keywords}")
        
        return '\n'.join(entry_lines)
    
    async def _export_json(self, items: List[ZoteroItem], include_attachments: bool, include_notes: bool) -> str:
        """Export items to JSON format"""
        export_data = []
        
        for item in items:
            item_data = {
                'id': item.id,
                'zotero_item_key': item.zotero_item_key,
                'item_type': item.item_type,
                'title': item.title,
                'creators': item.creators,
                'publication_title': item.publication_title,
                'publication_year': item.publication_year,
                'publisher': item.publisher,
                'doi': item.doi,
                'isbn': item.isbn,
                'issn': item.issn,
                'url': item.url,
                'tags': item.tags,
                'date_added': item.date_added.isoformat() if item.date_added else None,
                'date_modified': item.date_modified.isoformat() if item.date_modified else None
            }
            
            if include_notes and item.abstract_note:
                item_data['abstract_note'] = item.abstract_note
            
            if item.extra_fields:
                item_data['extra_fields'] = item.extra_fields
            
            export_data.append(item_data)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    async def _export_csv(self, items: List[ZoteroItem], include_notes: bool) -> str:
        """Export items to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        
        # Define CSV headers
        headers = [
            'ID', 'Item Type', 'Title', 'Authors', 'Publication Title',
            'Publication Year', 'Publisher', 'DOI', 'ISBN', 'ISSN', 'URL', 'Tags'
        ]
        
        if include_notes:
            headers.append('Abstract')
        
        writer = csv.writer(output)
        writer.writerow(headers)
        
        for item in items:
            # Format authors
            authors = []
            if item.creators:
                for creator in item.creators:
                    if creator.get('creator_type') == 'author':
                        if creator.get('name'):
                            authors.append(creator['name'])
                        else:
                            last = creator.get('last_name', '')
                            first = creator.get('first_name', '')
                            if last and first:
                                authors.append(f"{first} {last}")
                            elif last:
                                authors.append(last)
            
            row = [
                item.id,
                item.item_type,
                item.title or '',
                '; '.join(authors),
                item.publication_title or '',
                item.publication_year or '',
                item.publisher or '',
                item.doi or '',
                item.isbn or '',
                item.issn or '',
                item.url or '',
                '; '.join(item.tags) if item.tags else ''
            ]
            
            if include_notes:
                row.append(item.abstract_note or '')
            
            writer.writerow(row)
        
        return output.getvalue()
    
    async def _export_tsv(self, items: List[ZoteroItem], include_notes: bool) -> str:
        """Export items to TSV format"""
        import csv
        import io
        
        output = io.StringIO()
        
        # Define TSV headers
        headers = [
            'ID', 'Item Type', 'Title', 'Authors', 'Publication Title',
            'Publication Year', 'Publisher', 'DOI', 'ISBN', 'ISSN', 'URL', 'Tags'
        ]
        
        if include_notes:
            headers.append('Abstract')
        
        writer = csv.writer(output, delimiter='\t')
        writer.writerow(headers)
        
        for item in items:
            # Format authors
            authors = []
            if item.creators:
                for creator in item.creators:
                    if creator.get('creator_type') == 'author':
                        if creator.get('name'):
                            authors.append(creator['name'])
                        else:
                            last = creator.get('last_name', '')
                            first = creator.get('first_name', '')
                            if last and first:
                                authors.append(f"{first} {last}")
                            elif last:
                                authors.append(last)
            
            row = [
                item.id,
                item.item_type,
                item.title or '',
                '; '.join(authors),
                item.publication_title or '',
                item.publication_year or '',
                item.publisher or '',
                item.doi or '',
                item.isbn or '',
                item.issn or '',
                item.url or '',
                '; '.join(item.tags) if item.tags else ''
            ]
            
            if include_notes:
                row.append(item.abstract_note or '')
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _generate_citation_key(self, item: ZoteroItem) -> str:
        """Generate a citation key for BibTeX"""
        # Get first author's last name
        author_key = "unknown"
        if item.creators:
            for creator in item.creators:
                if creator.get('creator_type') == 'author':
                    if creator.get('last_name'):
                        author_key = creator['last_name'].lower()
                        break
                    elif creator.get('name'):
                        # Use first word of organization name
                        author_key = creator['name'].split()[0].lower()
                        break
        
        # Clean author key
        author_key = re.sub(r'[^a-zA-Z0-9]', '', author_key)
        
        # Add year
        year_key = str(item.publication_year) if item.publication_year else "nodate"
        
        # Add title word if needed for uniqueness
        title_key = ""
        if item.title:
            # Get first significant word from title
            title_words = re.findall(r'\b[a-zA-Z]{3,}\b', item.title.lower())
            if title_words:
                title_key = title_words[0][:8]  # First 8 characters
        
        # Combine parts
        if title_key:
            citation_key = f"{author_key}{year_key}{title_key}"
        else:
            citation_key = f"{author_key}{year_key}"
        
        return citation_key
    
    def _format_bibtex_authors(self, creators: List[Dict[str, Any]]) -> str:
        """Format authors for BibTeX"""
        authors = []
        
        for creator in creators:
            if creator.get('creator_type') == 'author':
                if creator.get('name'):  # Organization
                    authors.append(creator['name'])
                else:
                    last = creator.get('last_name', '')
                    first = creator.get('first_name', '')
                    if last and first:
                        authors.append(f"{last}, {first}")
                    elif last:
                        authors.append(last)
        
        return ' and '.join(authors)
    
    def _clean_text_for_bibtex(self, text: str) -> str:
        """Clean text for BibTeX format"""
        if not text:
            return ""
        
        # Remove or escape special characters
        text = text.replace('{', '\\{').replace('}', '\\}')
        text = text.replace('%', '\\%')
        text = text.replace('&', '\\&')
        text = text.replace('$', '\\$')
        text = text.replace('#', '\\#')
        text = text.replace('_', '\\_')
        text = text.replace('^', '\\^')
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    asy
nc def _batch_export_references(
        self,
        items: List[ZoteroItem],
        export_format: str,
        include_attachments: bool,
        include_notes: bool,
        batch_size: int = 100
    ) -> str:
        """
        Export references in batches for better performance with large datasets
        
        Args:
            items: List of ZoteroItem objects
            export_format: Export format
            include_attachments: Whether to include attachment info
            include_notes: Whether to include notes
            batch_size: Number of items to process per batch
            
        Returns:
            Combined export data
        """
        all_entries = []
        
        # Process items in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Export batch based on format
            if export_format == 'bibtex':
                batch_entries = await self._batch_export_bibtex(batch, include_notes)
            elif export_format == 'ris':
                batch_entries = await self._batch_export_ris(batch, include_notes)
            elif export_format == 'endnote':
                batch_entries = await self._batch_export_endnote(batch, include_notes)
            elif export_format == 'json':
                batch_entries = await self._batch_export_json(batch, include_attachments, include_notes)
            elif export_format == 'csv':
                # For CSV, we need to handle headers specially
                if i == 0:
                    batch_entries = await self._export_csv(batch, include_notes)
                else:
                    # Skip header for subsequent batches
                    batch_csv = await self._export_csv(batch, include_notes)
                    batch_entries = '\n'.join(batch_csv.split('\n')[1:])  # Skip header line
            elif export_format == 'tsv':
                # Similar handling for TSV
                if i == 0:
                    batch_entries = await self._export_tsv(batch, include_notes)
                else:
                    batch_tsv = await self._export_tsv(batch, include_notes)
                    batch_entries = '\n'.join(batch_tsv.split('\n')[1:])  # Skip header line
            else:
                raise ExportFormatError(f"Unsupported export format for batch processing: {export_format}")
            
            all_entries.append(batch_entries)
            
            # Log progress for large exports
            logger.info(f"Processed {min(i + batch_size, len(items))}/{len(items)} items for {export_format} export")
        
        # Combine all entries
        if export_format in ['csv', 'tsv']:
            return '\n'.join(all_entries)
        elif export_format == 'json':
            # For JSON, we need to merge arrays
            import json
            combined_data = []
            for entry in all_entries:
                batch_data = json.loads(entry)
                combined_data.extend(batch_data)
            return json.dumps(combined_data, indent=2, ensure_ascii=False)
        else:
            # For BibTeX, RIS, EndNote - simple concatenation with separators
            separator = '\n\n' if export_format in ['bibtex', 'ris', 'endnote'] else '\n'
            return separator.join(all_entries)

    async def _batch_export_bibtex(self, items: List[ZoteroItem], include_notes: bool) -> str:
        """Export batch of items to BibTeX format"""
        entries = []
        for item in items:
            try:
                entry = await self._format_bibtex_entry(item, include_notes)
                entries.append(entry)
            except Exception as e:
                logger.warning(f"Failed to format BibTeX entry for item {item.id}: {str(e)}")
        return '\n\n'.join(entries)

    async def _batch_export_ris(self, items: List[ZoteroItem], include_notes: bool) -> str:
        """Export batch of items to RIS format"""
        entries = []
        for item in items:
            try:
                entry = await self._format_ris_entry(item, include_notes)
                entries.append(entry)
            except Exception as e:
                logger.warning(f"Failed to format RIS entry for item {item.id}: {str(e)}")
        return '\n\n'.join(entries)

    async def _batch_export_endnote(self, items: List[ZoteroItem], include_notes: bool) -> str:
        """Export batch of items to EndNote format"""
        entries = []
        for item in items:
            try:
                entry = await self._format_endnote_entry(item, include_notes)
                entries.append(entry)
            except Exception as e:
                logger.warning(f"Failed to format EndNote entry for item {item.id}: {str(e)}")
        return '\n\n'.join(entries)

    async def _batch_export_json(self, items: List[ZoteroItem], include_attachments: bool, include_notes: bool) -> str:
        """Export batch of items to JSON format"""
        export_data = []
        
        for item in items:
            try:
                item_data = {
                    'id': item.id,
                    'zotero_item_key': item.zotero_item_key,
                    'item_type': item.item_type,
                    'title': item.title,
                    'creators': item.creators,
                    'publication_title': item.publication_title,
                    'publication_year': item.publication_year,
                    'publisher': item.publisher,
                    'doi': item.doi,
                    'isbn': item.isbn,
                    'issn': item.issn,
                    'url': item.url,
                    'tags': item.tags,
                    'date_added': item.date_added.isoformat() if item.date_added else None,
                    'date_modified': item.date_modified.isoformat() if item.date_modified else None
                }
                
                if include_notes and item.abstract_note:
                    item_data['abstract_note'] = item.abstract_note
                
                if item.extra_fields:
                    item_data['extra_fields'] = item.extra_fields
                
                export_data.append(item_data)
                
            except Exception as e:
                logger.warning(f"Failed to format JSON entry for item {item.id}: {str(e)}")
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)