"""
Zotero Chat Integration Service

Handles integration between Zotero references and chat functionality.
Provides reference context injection, mention linking, and reference-aware responses.
"""

import re
import json
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from ...models.zotero_models import ZoteroItem, ZoteroConnection
from ...core.database import get_db
from .zotero_search_service import ZoteroSearchService
from .zotero_citation_service import ZoteroCitationService


class ZoteroChatIntegrationService:
    """Service for integrating Zotero references with chat functionality"""
    
    def __init__(self):
        self.search_service = ZoteroSearchService()
        self.citation_service = ZoteroCitationService()
    
    def extract_reference_mentions(self, content: str) -> List[str]:
        """
        Extract reference mentions from chat message content.
        Supports formats like @[Title] or @[Author, Year]
        """
        mention_pattern = r'@\[([^\]]+)\]'
        mentions = re.findall(mention_pattern, content)
        return mentions
    
    async def find_referenced_items(
        self, 
        mentions: List[str], 
        user_id: str,
        db: Session
    ) -> List[ZoteroItem]:
        """Find Zotero items that match the mentioned references"""
        items = []
        
        for mention in mentions:
            try:
                # Search for items by title or author
                search_results = await self.search_service.search_items(
                    user_id=user_id,
                    query=mention,
                    limit=5,
                    db=db
                )
                
                # Add the most relevant matches
                if search_results.get('items'):
                    items.extend(search_results['items'][:2])
                    
            except Exception as e:
                print(f"Warning: Failed to find reference for mention '{mention}': {e}")
        
        return items
    
    def convert_to_chat_references(
        self, 
        items: List[ZoteroItem], 
        relevance_scores: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Convert Zotero items to chat reference format"""
        references = []
        
        for i, item in enumerate(items):
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
                # Extract year from date string
                year_match = re.search(r'\b(\d{4})\b', item.date)
                if year_match:
                    year = int(year_match.group(1))
            
            reference = {
                'id': item.id,
                'title': item.title,
                'creators': creators,
                'year': year,
                'publicationTitle': item.publication_title,
                'relevance': relevance_scores[i] if relevance_scores and i < len(relevance_scores) else 0.8,
                'citationKey': self._generate_citation_key(item, creators, year)
            }
            
            references.append(reference)
        
        return references
    
    def _generate_citation_key(
        self, 
        item: ZoteroItem, 
        creators: List[str], 
        year: Optional[int]
    ) -> str:
        """Generate a citation key for an item"""
        if creators:
            # Get first author's last name
            first_author = creators[0]
            # Extract last name (assume format "First Last" or just "Last")
            parts = first_author.split()
            author_name = parts[-1] if parts else 'Unknown'
        else:
            author_name = 'Unknown'
        
        year_str = str(year) if year else str(datetime.now().year)
        
        return f"{author_name}{year_str}"
    
    async def inject_reference_context(
        self,
        content: str,
        user_id: str,
        db: Session,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Inject reference context into chat message"""
        references = []
        enhanced_content = content
        
        # Extract mentions from content
        mentions = self.extract_reference_mentions(content)
        
        if mentions:
            referenced_items = await self.find_referenced_items(mentions, user_id, db)
            references = self.convert_to_chat_references(referenced_items)
        
        # Add specific reference IDs if provided
        if options and options.get('referenceIds'):
            try:
                specific_items = []
                for ref_id in options['referenceIds']:
                    item = db.query(ZoteroItem).filter(
                        ZoteroItem.id == ref_id,
                        ZoteroItem.user_id == user_id
                    ).first()
                    if item:
                        specific_items.append(item)
                
                specific_references = self.convert_to_chat_references(specific_items)
                references.extend(specific_references)
                
            except Exception as e:
                print(f"Warning: Failed to load specific reference items: {e}")
        
        # Add context information for AI
        if references and options and options.get('includeZoteroContext'):
            context_info = self._build_context_info(references, options.get('contextType'))
            enhanced_content = f"{content}\n\n[REFERENCE_CONTEXT]\n{context_info}"
        
        return enhanced_content, references
    
    def _build_context_info(
        self, 
        references: List[Dict[str, Any]], 
        context_type: Optional[str] = None
    ) -> str:
        """Build context information for AI processing"""
        context_lines = []
        
        for ref in references:
            authors = ', '.join(ref['creators']) if ref['creators'] else 'Unknown'
            year = f" ({ref['year']})" if ref['year'] else ''
            publication = f" - {ref['publicationTitle']}" if ref['publicationTitle'] else ''
            
            context_lines.append(f"- {ref['title']} by {authors}{year}{publication}")
        
        context_header = 'Referenced papers:'
        if context_type == 'research':
            context_header = 'Research context from referenced papers:'
        elif context_type == 'citation':
            context_header = 'Papers to cite:'
        elif context_type == 'analysis':
            context_header = 'Papers for analysis:'
        
        return f"{context_header}\n" + '\n'.join(context_lines)
    
    def process_ai_response(
        self, 
        response: str, 
        available_references: List[Dict[str, Any]]
    ) -> str:
        """Process AI response to add reference links"""
        processed_response = response
        
        # Find potential reference mentions in AI response
        for ref in available_references:
            patterns = [
                (ref['citationKey'], f"[@{ref['title']}](zotero:{ref['id']})"),
                (ref['title'][:30], f"[@{ref['title']}](zotero:{ref['id']})")
            ]
            
            # Add creator patterns
            for creator in ref['creators']:
                patterns.append((creator, f"[@{ref['title']}](zotero:{ref['id']})"))
            
            for pattern, replacement in patterns:
                # Use word boundaries to avoid partial matches
                regex_pattern = r'\b' + re.escape(pattern) + r'\b'
                processed_response = re.sub(
                    regex_pattern, 
                    replacement, 
                    processed_response, 
                    flags=re.IGNORECASE
                )
        
        return processed_response
    
    async def get_relevant_references(
        self,
        topic: str,
        user_id: str,
        db: Session,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get relevant references for a chat topic"""
        try:
            search_results = await self.search_service.search_items(
                user_id=user_id,
                query=topic,
                limit=limit,
                db=db
            )
            
            items = search_results.get('items', [])
            return self.convert_to_chat_references(items)
            
        except Exception as e:
            print(f"Warning: Failed to get relevant references: {e}")
            return []
    
    async def generate_citations_for_references(
        self,
        references: List[Dict[str, Any]],
        style: str = 'apa',
        user_id: str,
        db: Session
    ) -> List[str]:
        """Generate citations for referenced items"""
        try:
            item_ids = [ref['id'] for ref in references]
            citation_result = await self.citation_service.generate_citation(
                item_ids=item_ids,
                style=style,
                user_id=user_id,
                db=db
            )
            
            # Split bibliography into individual citations
            if citation_result.get('bibliography'):
                return [line.strip() for line in citation_result['bibliography'].split('\n') if line.strip()]
            
        except Exception as e:
            print(f"Warning: Failed to generate citations: {e}")
        
        # Fallback to simple format
        citations = []
        for ref in references:
            authors = ', '.join(ref['creators']) if ref['creators'] else 'Unknown'
            year = f" ({ref['year']})" if ref['year'] else ''
            citations.append(f"{authors}{year}. {ref['title']}.")
        
        return citations
    
    async def create_research_summary(
        self,
        topic: str,
        user_id: str,
        db: Session,
        reference_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a research summary with references"""
        references = []
        
        if reference_ids:
            try:
                items = []
                for ref_id in reference_ids:
                    item = db.query(ZoteroItem).filter(
                        ZoteroItem.id == ref_id,
                        ZoteroItem.user_id == user_id
                    ).first()
                    if item:
                        items.append(item)
                
                references = self.convert_to_chat_references(items)
                
            except Exception as e:
                print(f"Warning: Failed to load reference items for summary: {e}")
        else:
            references = await self.get_relevant_references(topic, user_id, db, limit=10)
        
        summary = self._build_research_summary(topic, references)
        
        return {
            'summary': summary,
            'references': references
        }
    
    def _build_research_summary(
        self, 
        topic: str, 
        references: List[Dict[str, Any]]
    ) -> str:
        """Build a research summary from references"""
        if not references:
            return f"No references found for topic: {topic}"
        
        summary_parts = [
            f"Research Summary: {topic}",
            f"Based on {len(references)} references from your Zotero library:",
            "",
            "Key Papers:"
        ]
        
        for i, ref in enumerate(references[:5]):
            authors = ', '.join(ref['creators'][:2]) if ref['creators'] else 'Unknown'
            more_authors = ' et al.' if len(ref['creators']) > 2 else ''
            year = f" ({ref['year']})" if ref['year'] else ''
            
            summary_parts.append(
                f"{i + 1}. {ref['title']} - {authors}{more_authors}{year}"
            )
        
        if len(references) > 5:
            summary_parts.append(f"... and {len(references) - 5} more papers")
        
        return '\n'.join(summary_parts)
    
    async def export_conversation_with_citations(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        db: Session,
        citation_style: str = 'apa'
    ) -> str:
        """Export conversation with proper citations"""
        export_parts = []
        all_references = []
        
        # Collect all references from messages
        for message in messages:
            if message.get('references'):
                all_references.extend(message['references'])
        
        # Remove duplicates
        unique_references = []
        seen_ids = set()
        for ref in all_references:
            if ref['id'] not in seen_ids:
                unique_references.append(ref)
                seen_ids.add(ref['id'])
        
        # Export conversation
        export_parts.extend([
            '# AI Scholar Conversation Export',
            f'Exported on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            ''
        ])
        
        for i, message in enumerate(messages):
            role = 'User' if message['role'] == 'user' else 'AI Assistant'
            timestamp = message.get('timestamp', datetime.now().isoformat())
            
            export_parts.extend([
                f"## {role} ({timestamp})",
                message['content']
            ])
            
            if message.get('references'):
                export_parts.extend(['', '**Referenced Papers:**'])
                for ref in message['references']:
                    authors = ', '.join(ref['creators']) if ref['creators'] else 'Unknown'
                    year = f" ({ref['year']})" if ref['year'] else ''
                    export_parts.append(f"- {ref['title']} by {authors}{year}")
            
            export_parts.append('')
        
        # Add bibliography
        if unique_references:
            export_parts.append('## References')
            
            try:
                citations = await self.generate_citations_for_references(
                    unique_references, 
                    citation_style, 
                    user_id, 
                    db
                )
                export_parts.extend(citations)
            except Exception as e:
                print(f"Warning: Failed to generate bibliography: {e}")
                # Fallback format
                for ref in unique_references:
                    authors = ', '.join(ref['creators']) if ref['creators'] else 'Unknown'
                    year = f" ({ref['year']})" if ref['year'] else ''
                    export_parts.append(f"{authors}{year}. {ref['title']}.")
        
        return '\n'.join(export_parts)


# Global service instance
zotero_chat_service = ZoteroChatIntegrationService()