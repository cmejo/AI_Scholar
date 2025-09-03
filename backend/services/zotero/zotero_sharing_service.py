"""
Zotero Sharing and Export Service

Handles export and sharing capabilities for Zotero-integrated content.
Provides conversation export with citations, reference sharing, and project collections.
"""

import json
import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_

from ...models.zotero_models import ZoteroItem, ZoteroConnection
from ...core.database import get_db
from .zotero_citation_service import ZoteroCitationService


class ZoteroSharingService:
    """Service for handling Zotero sharing and export functionality"""
    
    def __init__(self):
        self.citation_service = ZoteroCitationService()
    
    def get_export_formats(self) -> List[Dict[str, str]]:
        """Get available export formats"""
        return [
            {
                'id': 'markdown',
                'name': 'Markdown',
                'extension': 'md',
                'mimeType': 'text/markdown',
                'description': 'Markdown format with reference links'
            },
            {
                'id': 'html',
                'name': 'HTML',
                'extension': 'html',
                'mimeType': 'text/html',
                'description': 'HTML document with interactive references'
            },
            {
                'id': 'pdf',
                'name': 'PDF',
                'extension': 'pdf',
                'mimeType': 'application/pdf',
                'description': 'PDF document with formatted citations'
            },
            {
                'id': 'docx',
                'name': 'Word Document',
                'extension': 'docx',
                'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'description': 'Microsoft Word document'
            },
            {
                'id': 'bibtex',
                'name': 'BibTeX',
                'extension': 'bib',
                'mimeType': 'application/x-bibtex',
                'description': 'BibTeX bibliography format'
            },
            {
                'id': 'ris',
                'name': 'RIS',
                'extension': 'ris',
                'mimeType': 'application/x-research-info-systems',
                'description': 'Research Information Systems format'
            }
        ]
    
    async def export_conversation(
        self,
        messages: List[Dict[str, Any]],
        options: Dict[str, Any],
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Export conversation with proper citations"""
        format_type = options.get('format', 'markdown')
        timestamp = datetime.now().strftime('%Y-%m-%d')
        filename = f"ai-scholar-conversation-{timestamp}.{self._get_format_extension(format_type)}"
        
        if format_type == 'markdown':
            content = await self._export_conversation_as_markdown(messages, options, user_id, db)
        elif format_type == 'html':
            content = await self._export_conversation_as_html(messages, options, user_id, db)
        else:
            # For other formats, use markdown as base
            content = await self._export_conversation_as_markdown(messages, options, user_id, db)
        
        format_info = next((f for f in self.get_export_formats() if f['id'] == format_type), None)
        mime_type = format_info['mimeType'] if format_info else 'text/plain'
        
        return {
            'content': content,
            'filename': filename,
            'mimeType': mime_type
        }
    
    async def _export_conversation_as_markdown(
        self,
        messages: List[Dict[str, Any]],
        options: Dict[str, Any],
        user_id: str,
        db: Session
    ) -> str:
        """Export conversation as Markdown"""
        export_parts = []
        all_references = []
        
        # Header
        export_parts.append('# AI Scholar Conversation Export')
        
        if options.get('includeMetadata', True):
            export_parts.extend([
                f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Format:** {options.get('format', 'markdown').upper()}",
            ])
            
            if options.get('includeCitations', True):
                export_parts.append(f"**Citation Style:** {options.get('citationStyle', 'apa')}")
            
            export_parts.append('')
        
        # Messages
        for message in messages:
            role = 'User' if message['role'] == 'user' else 'AI Assistant'
            export_parts.append(f"## {role}")
            
            if options.get('includeTimestamps', True):
                timestamp = message.get('timestamp', datetime.now().isoformat())
                export_parts.extend([f"*{timestamp}*", ''])
            
            export_parts.extend([message['content'], ''])
            
            # Add references if present
            references = message.get('references', [])
            if references and options.get('includeReferences', True):
                export_parts.append('**Referenced Papers:**')
                
                for ref in references:
                    authors = ', '.join(ref.get('creators', []))
                    year = f" ({ref['year']})" if ref.get('year') else ''
                    publication = f" - {ref['publicationTitle']}" if ref.get('publicationTitle') else ''
                    
                    export_parts.append(f"- {ref['title']} by {authors}{year}{publication}")
                
                export_parts.append('')
                all_references.extend(references)
        
        # Bibliography
        if options.get('includeCitations', True) and all_references:
            export_parts.extend(['## References', ''])
            
            try:
                unique_references = self._remove_duplicate_references(all_references)
                citations = await self._generate_citations(
                    unique_references, 
                    options.get('citationStyle', 'apa'),
                    user_id,
                    db
                )
                export_parts.extend(citations)
            except Exception as e:
                print(f"Warning: Failed to generate citations: {e}")
                # Fallback format
                unique_references = self._remove_duplicate_references(all_references)
                for ref in unique_references:
                    authors = ', '.join(ref.get('creators', []))
                    year = f" ({ref['year']})" if ref.get('year') else ''
                    export_parts.append(f"{authors}{year}. {ref['title']}.")
        
        return '\n'.join(export_parts)
    
    async def _export_conversation_as_html(
        self,
        messages: List[Dict[str, Any]],
        options: Dict[str, Any],
        user_id: str,
        db: Session
    ) -> str:
        """Export conversation as HTML"""
        markdown_content = await self._export_conversation_as_markdown(messages, options, user_id, db)
        
        # Simple Markdown to HTML conversion
        html_content = (markdown_content
                       .replace('# ', '<h1>')
                       .replace('\n## ', '</h1>\n<h2>')
                       .replace('\n### ', '</h2>\n<h3>')
                       .replace('**', '<strong>', 1)
                       .replace('**', '</strong>', 1)
                       .replace('*', '<em>', 1)
                       .replace('*', '</em>', 1)
                       .replace('\n- ', '\n<li>')
                       .replace('\n\n', '</p>\n<p>')
                       .replace('\n', '<br>\n'))
        
        # Wrap in HTML structure
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Scholar Conversation Export</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            line-height: 1.6; 
        }}
        h1, h2, h3 {{ color: #333; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
        .references {{ 
            background: #f5f5f5; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 10px 0; 
        }}
        .reference-link {{ 
            color: #0066cc; 
            text-decoration: none; 
        }}
        .reference-link:hover {{ 
            text-decoration: underline; 
        }}
    </style>
</head>
<body>
    <div class="content">
        <p>{html_content}</p>
    </div>
</body>
</html>"""
    
    async def share_reference(
        self,
        reference_id: str,
        shared_with: List[str],
        permissions: Dict[str, bool],
        user_id: str,
        db: Session,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Share reference with other users"""
        shared_reference = {
            'id': str(uuid.uuid4()),
            'referenceId': reference_id,
            'sharedBy': user_id,
            'sharedWith': shared_with,
            'sharedAt': datetime.now().isoformat(),
            'permissions': permissions,
            'note': note
        }
        
        # In a real implementation, this would be stored in the database
        # For now, we'll just return the sharing information
        print(f"Sharing reference {reference_id} with users: {shared_with}")
        
        return shared_reference
    
    async def create_reference_collection(
        self,
        name: str,
        description: str,
        reference_ids: List[str],
        user_id: str,
        db: Session,
        is_public: bool = False,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a reference collection"""
        # Get reference details
        references = []
        for ref_id in reference_ids:
            try:
                item = db.query(ZoteroItem).filter(
                    ZoteroItem.id == ref_id,
                    ZoteroItem.user_id == user_id
                ).first()
                
                if item:
                    reference = self._convert_item_to_reference(item)
                    references.append(reference)
            except Exception as e:
                print(f"Warning: Failed to load reference {ref_id}: {e}")
        
        collection = {
            'id': str(uuid.uuid4()),
            'name': name,
            'description': description,
            'references': references,
            'collaborators': [],
            'isPublic': is_public,
            'createdBy': user_id,
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat(),
            'tags': tags or []
        }
        
        # In a real implementation, this would be stored in the database
        print(f"Created collection: {name} with {len(references)} references")
        
        return collection
    
    async def export_project(
        self,
        project_data: Dict[str, Any],
        options: Dict[str, Any],
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Export research project"""
        format_type = options.get('format', 'markdown')
        timestamp = datetime.now().strftime('%Y-%m-%d')
        filename = f"research-project-{timestamp}.{self._get_format_extension(format_type)}"
        
        if format_type == 'markdown':
            content = await self._export_project_as_markdown(project_data, options, user_id, db)
        elif format_type == 'zip':
            content = await self._export_project_as_zip(project_data, options, user_id, db)
        else:
            content = await self._export_project_as_markdown(project_data, options, user_id, db)
        
        format_info = next((f for f in self.get_export_formats() if f['id'] == format_type), None)
        mime_type = format_info['mimeType'] if format_info else 'text/plain'
        
        return {
            'content': content,
            'filename': filename,
            'mimeType': mime_type
        }
    
    async def _export_project_as_markdown(
        self,
        project_data: Dict[str, Any],
        options: Dict[str, Any],
        user_id: str,
        db: Session
    ) -> str:
        """Export project as Markdown"""
        export_parts = []
        
        # Project header
        export_parts.extend([
            f"# {project_data.get('title', 'Research Project')}",
            '',
            project_data.get('description', ''),
            '',
            f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ''
        ])
        
        # References section
        references = project_data.get('references', [])
        if options.get('includeReferences', True) and references:
            export_parts.extend(['## References', ''])
            
            for i, ref in enumerate(references):
                authors = ', '.join(ref.get('creators', []))
                year = f" ({ref['year']})" if ref.get('year') else ''
                publication = f" - {ref['publicationTitle']}" if ref.get('publicationTitle') else ''
                
                export_parts.append(f"{i + 1}. **{ref['title']}** by {authors}{year}{publication}")
            
            export_parts.append('')
        
        # Notes section
        notes = project_data.get('notes', [])
        if options.get('includeNotes', True) and notes:
            export_parts.extend(['## Research Notes', ''])
            
            for note in notes:
                export_parts.extend([
                    f"### {note.get('title', 'Untitled Note')}",
                    '',
                    note.get('content', ''),
                    ''
                ])
                
                tags = note.get('tags', [])
                if tags:
                    export_parts.extend([f"**Tags:** {', '.join(tags)}", ''])
        
        # Bibliography
        if options.get('includeBibliography', True) and references:
            export_parts.extend(['## Bibliography', ''])
            
            try:
                citations = await self._generate_citations(
                    references,
                    options.get('citationStyle', 'apa'),
                    user_id,
                    db
                )
                export_parts.extend(citations)
            except Exception as e:
                print(f"Warning: Failed to generate bibliography: {e}")
                # Fallback format
                for ref in references:
                    authors = ', '.join(ref.get('creators', []))
                    year = f" ({ref['year']})" if ref.get('year') else ''
                    export_parts.append(f"{authors}{year}. {ref['title']}.")
        
        return '\n'.join(export_parts)
    
    async def _export_project_as_zip(
        self,
        project_data: Dict[str, Any],
        options: Dict[str, Any],
        user_id: str,
        db: Session
    ) -> str:
        """Export project as ZIP (placeholder)"""
        # In a real implementation, this would create a ZIP file with multiple documents
        markdown_content = await self._export_project_as_markdown(project_data, options, user_id, db)
        
        # For now, return the markdown content
        # In production, would use a library to create actual ZIP files
        return markdown_content
    
    def generate_shareable_link(
        self,
        collection_id: str,
        is_public: bool,
        base_url: str = "https://ai-scholar.com"
    ) -> str:
        """Generate shareable link for collection"""
        if is_public:
            return f"{base_url}/shared/collection/{collection_id}"
        else:
            # Generate a secure token for private sharing
            token = self._generate_secure_token()
            return f"{base_url}/shared/collection/{collection_id}?token={token}"
    
    def _generate_secure_token(self) -> str:
        """Generate secure token for private sharing"""
        return str(uuid.uuid4()).replace('-', '')
    
    def _convert_item_to_reference(self, item: ZoteroItem) -> Dict[str, Any]:
        """Convert Zotero item to reference format"""
        creators = []
        if item.creators:
            for creator in item.creators:
                if isinstance(creator, dict):
                    if creator.get('name'):
                        creators.append(creator['name'])
                    elif creator.get('firstName') and creator.get('lastName'):
                        creators.append(f"{creator['firstName']} {creator['lastName']}")
        
        year = None
        if item.date:
            import re
            year_match = re.search(r'\b(\d{4})\b', item.date)
            if year_match:
                year = int(year_match.group(1))
        
        return {
            'id': item.id,
            'title': item.title,
            'creators': creators,
            'year': year,
            'publicationTitle': item.publication_title,
            'relevance': 1.0,
            'citationKey': self._generate_citation_key(creators, year),
            'abstractNote': item.abstract_note
        }
    
    def _generate_citation_key(self, creators: List[str], year: Optional[int]) -> str:
        """Generate citation key"""
        if creators:
            first_author = creators[0]
            author_name = first_author.split()[-1] if first_author else 'Unknown'
        else:
            author_name = 'Unknown'
        
        year_str = str(year) if year else str(datetime.now().year)
        return f"{author_name}{year_str}"
    
    async def _generate_citations(
        self,
        references: List[Dict[str, Any]],
        style: str,
        user_id: str,
        db: Session
    ) -> List[str]:
        """Generate citations for references"""
        try:
            item_ids = [ref['id'] for ref in references]
            citation_result = await self.citation_service.generate_citation(
                item_ids=item_ids,
                style=style,
                user_id=user_id,
                db=db
            )
            
            if citation_result.get('bibliography'):
                return [line.strip() for line in citation_result['bibliography'].split('\n') if line.strip()]
        except Exception as e:
            print(f"Warning: Failed to generate citations via service: {e}")
        
        # Fallback to simple format
        citations = []
        for ref in references:
            authors = ', '.join(ref.get('creators', []))
            year = f" ({ref['year']})" if ref.get('year') else ''
            citations.append(f"{authors}{year}. {ref['title']}.")
        
        return citations
    
    def _remove_duplicate_references(self, references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate references"""
        seen = set()
        unique_refs = []
        
        for ref in references:
            ref_id = ref.get('id')
            if ref_id and ref_id not in seen:
                seen.add(ref_id)
                unique_refs.append(ref)
        
        return unique_refs
    
    def _get_format_extension(self, format_type: str) -> str:
        """Get file extension for format"""
        format_map = {
            'markdown': 'md',
            'html': 'html',
            'pdf': 'pdf',
            'docx': 'docx',
            'zip': 'zip',
            'bibtex': 'bib',
            'ris': 'ris'
        }
        
        return format_map.get(format_type, 'txt')


# Global service instance
zotero_sharing_service = ZoteroSharingService()