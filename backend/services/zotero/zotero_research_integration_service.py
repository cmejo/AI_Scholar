"""
Zotero Research Integration Service

Handles integration between Zotero references and research/note-taking features.
Provides reference linking in notes, research summaries, and AI research assistance.
"""

import re
import json
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_

from ...models.zotero_models import ZoteroItem, ZoteroConnection
from ...core.database import get_db
from .zotero_search_service import ZoteroSearchService
from .zotero_citation_service import ZoteroCitationService


class ZoteroResearchIntegrationService:
    """Service for integrating Zotero references with research and note-taking features"""
    
    def __init__(self):
        self.search_service = ZoteroSearchService()
        self.citation_service = ZoteroCitationService()
    
    def extract_reference_links(self, content: str) -> Dict[str, List[str]]:
        """
        Extract reference links from note content.
        Supports formats like [[ref:item-id]] or @[Title]
        """
        item_id_pattern = r'\[\[ref:([^\]]+)\]\]'
        mention_pattern = r'@\[([^\]]+)\]'
        
        item_ids = re.findall(item_id_pattern, content)
        mentions = re.findall(mention_pattern, content)
        
        return {
            'itemIds': item_ids,
            'mentions': mentions
        }
    
    async def process_note_content(
        self,
        content: str,
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Process note content to resolve reference links"""
        links = self.extract_reference_links(content)
        references = []
        processed_content = content
        
        # Resolve item IDs to references
        for item_id in links['itemIds']:
            try:
                item = db.query(ZoteroItem).filter(
                    ZoteroItem.id == item_id,
                    ZoteroItem.user_id == user_id
                ).first()
                
                if item:
                    reference = self._convert_item_to_reference(item)
                    references.append(reference)
                    
                    # Replace link with formatted reference
                    link_pattern = rf'\[\[ref:{re.escape(item_id)}\]\]'
                    formatted_ref = f'[{reference["title"]}](zotero:{item_id})'
                    processed_content = re.sub(link_pattern, formatted_ref, processed_content)
                    
            except Exception as e:
                print(f"Warning: Failed to resolve reference {item_id}: {e}")
        
        # Resolve mentions to references
        for mention in links['mentions']:
            try:
                search_results = await self.search_service.search_items(
                    user_id=user_id,
                    query=mention,
                    limit=1,
                    db=db
                )
                
                if search_results.get('items'):
                    item = search_results['items'][0]
                    reference = self._convert_item_to_reference(item)
                    references.append(reference)
                    
                    # Replace mention with formatted reference
                    mention_pattern = rf'@\[{re.escape(mention)}\]'
                    formatted_ref = f'[{reference["title"]}](zotero:{item.id})'
                    processed_content = re.sub(mention_pattern, formatted_ref, processed_content)
                    
            except Exception as e:
                print(f"Warning: Failed to resolve mention '{mention}': {e}")
        
        return {
            'processedContent': processed_content,
            'references': references,
            'originalLinks': links
        }
    
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
            year_match = re.search(r'\b(\d{4})\b', item.date)
            if year_match:
                year = int(year_match.group(1))
        
        first_author = creators[0] if creators else 'Unknown'
        author_name = first_author.split()[-1] if first_author != 'Unknown' else 'Unknown'
        citation_key = f"{author_name}{year or datetime.now().year}"
        
        return {
            'id': item.id,
            'title': item.title,
            'creators': creators,
            'year': year,
            'publicationTitle': item.publication_title,
            'relevance': 1.0,  # Direct reference has high relevance
            'citationKey': citation_key,
            'abstractNote': item.abstract_note
        }
    
    async def create_research_summary(
        self,
        topic: str,
        user_id: str,
        db: Session,
        reference_ids: Optional[List[str]] = None,
        note_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create research summary from references and notes"""
        references = []
        
        # Get references
        if reference_ids:
            for ref_id in reference_ids:
                try:
                    item = db.query(ZoteroItem).filter(
                        ZoteroItem.id == ref_id,
                        ZoteroItem.user_id == user_id
                    ).first()
                    if item:
                        references.append(self._convert_item_to_reference(item))
                except Exception as e:
                    print(f"Warning: Failed to load reference {ref_id}: {e}")
        else:
            # Search for relevant references
            search_results = await self.search_service.search_items(
                user_id=user_id,
                query=topic,
                limit=10,
                db=db
            )
            if search_results.get('items'):
                references = [
                    self._convert_item_to_reference(item) 
                    for item in search_results['items']
                ]
        
        # Generate summary components
        summary_content = self._generate_summary_content(topic, references)
        key_findings = self._extract_key_findings(references)
        research_gaps = self._identify_research_gaps(topic, references)
        recommendations = self._generate_recommendations(topic, references, research_gaps)
        
        return {
            'id': f'summary-{int(datetime.now().timestamp())}',
            'topic': topic,
            'summary': summary_content,
            'keyFindings': key_findings,
            'references': references,
            'gaps': research_gaps,
            'recommendations': recommendations,
            'createdAt': datetime.now().isoformat()
        }
    
    def _generate_summary_content(self, topic: str, references: List[Dict[str, Any]]) -> str:
        """Generate summary content from references"""
        if not references:
            return f"No references found for topic: {topic}"
        
        summary_parts = [
            f"# Research Summary: {topic}",
            "",
            f"This summary is based on {len(references)} references from your Zotero library.",
            "",
            "## Key Papers"
        ]
        
        for i, ref in enumerate(references[:5]):
            authors = ', '.join(ref['creators'][:2]) if ref['creators'] else 'Unknown'
            more_authors = ' et al.' if len(ref['creators']) > 2 else ''
            year = f" ({ref['year']})" if ref['year'] else ''
            
            summary_parts.append(f"{i + 1}. **{ref['title']}** - {authors}{more_authors}{year}")
            
            if ref.get('publicationTitle'):
                summary_parts.append(f"   *Published in: {ref['publicationTitle']}*")
            summary_parts.append("")
        
        if len(references) > 5:
            summary_parts.append(f"*... and {len(references) - 5} more papers*")
        
        return '\n'.join(summary_parts)
    
    def _extract_key_findings(self, references: List[Dict[str, Any]]) -> List[str]:
        """Extract key findings from references"""
        findings = [
            f"Analysis of {len(references)} papers reveals several key themes",
            "Multiple studies confirm the importance of the research area",
            "Recent work shows promising developments in the field"
        ]
        
        if len(references) > 5:
            findings.append("Large body of literature indicates mature research area")
        
        # Analyze publication years
        years = [ref['year'] for ref in references if ref.get('year')]
        if years:
            recent_years = [y for y in years if y >= datetime.now().year - 3]
            if len(recent_years) > len(years) * 0.5:
                findings.append("Active area with significant recent research activity")
        
        return findings
    
    def _identify_research_gaps(self, topic: str, references: List[Dict[str, Any]]) -> List[str]:
        """Identify research gaps from references"""
        gaps = [
            "Limited recent studies in the past 2 years",
            "Lack of comprehensive meta-analysis",
            "Need for more empirical validation"
        ]
        
        # Analyze temporal distribution
        years = [ref['year'] for ref in references if ref.get('year')]
        if years:
            recent_refs = [y for y in years if y >= datetime.now().year - 2]
            if len(recent_refs) < len(references) * 0.3:
                gaps.append("Opportunity for updated research with current methodologies")
        
        # Analyze publication diversity
        publications = set(ref.get('publicationTitle', '') for ref in references)
        if len(publications) < len(references) * 0.5:
            gaps.append("Limited diversity in publication venues")
        
        return gaps
    
    def _generate_recommendations(
        self,
        topic: str,
        references: List[Dict[str, Any]],
        gaps: List[str]
    ) -> List[str]:
        """Generate research recommendations"""
        recommendations = [
            "Conduct systematic literature review of recent developments",
            "Consider interdisciplinary approaches to the research question",
            "Explore novel methodologies not yet applied to this area"
        ]
        
        if gaps:
            recommendations.append("Address identified research gaps in future work")
        
        if len(references) > 10:
            recommendations.append("Consider meta-analysis of existing studies")
        
        # Analyze author diversity
        all_authors = []
        for ref in references:
            all_authors.extend(ref.get('creators', []))
        
        unique_authors = set(all_authors)
        if len(unique_authors) > len(references) * 1.5:
            recommendations.append("Rich author diversity suggests collaborative opportunities")
        
        return recommendations
    
    async def get_research_context(
        self,
        topic: str,
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Get research context for AI assistance"""
        # Get relevant references
        search_results = await self.search_service.search_items(
            user_id=user_id,
            query=topic,
            limit=10,
            db=db
        )
        
        relevant_references = []
        if search_results.get('items'):
            relevant_references = [
                self._convert_item_to_reference(item)
                for item in search_results['items']
            ]
        
        # Generate suggested questions
        suggested_questions = self._generate_suggested_questions(topic, relevant_references)
        
        # Identify research gaps
        research_gaps = self._identify_research_gaps(topic, relevant_references)
        
        return {
            'topic': topic,
            'relevantReferences': relevant_references,
            'relatedNotes': [],  # Would be loaded from note storage
            'suggestedQuestions': suggested_questions,
            'researchGaps': research_gaps
        }
    
    def _generate_suggested_questions(
        self,
        topic: str,
        references: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate suggested research questions"""
        questions = [
            f"What are the current trends in {topic}?",
            f"What methodologies are commonly used in {topic} research?",
            f"What are the main challenges in {topic}?",
            f"How has {topic} evolved over the past decade?"
        ]
        
        if len(references) > 5:
            questions.extend([
                f"What consensus exists among researchers in {topic}?",
                f"What are the most cited works in {topic}?"
            ])
        
        # Analyze temporal patterns
        years = [ref['year'] for ref in references if ref.get('year')]
        if years:
            year_range = max(years) - min(years)
            if year_range > 10:
                questions.append(f"How has the research focus in {topic} shifted over time?")
        
        # Generate domain-specific questions based on reference content
        domain_terms = self._extract_domain_terms(references)
        for term in domain_terms[:3]:  # Add up to 3 domain-specific questions
            questions.append(f"What role does {term} play in {topic}?")
        
        # Add questions based on publication venues
        venues = set(ref.get('publicationTitle', '') for ref in references if ref.get('publicationTitle'))
        if len(venues) > 3:
            questions.append(f"How do different research communities approach {topic}?")
        
        return questions
    
    def _extract_domain_terms(self, references: List[Dict[str, Any]]) -> List[str]:
        """Extract domain-specific terms from reference titles and abstracts"""
        all_text = []
        
        # Collect text from titles and abstracts
        for ref in references:
            if ref.get('title'):
                all_text.append(ref['title'].lower())
            if ref.get('abstractNote'):
                all_text.append(ref['abstractNote'].lower())
        
        combined_text = ' '.join(all_text)
        
        # Extract potential domain terms (simple approach)
        # Look for common domain-specific patterns
        domain_patterns = [
            r'\b(diagnostic|diagnosis|diagnostics)\b',
            r'\b(therapeutic|therapy|treatment)\b',
            r'\b(predictive|prediction|forecasting)\b',
            r'\b(clinical|medical|healthcare)\b',
            r'\b(algorithm|algorithms|computational)\b',
            r'\b(imaging|visualization|analysis)\b',
            r'\b(machine learning|deep learning|artificial intelligence)\b',
            r'\b(neural networks|models|modeling)\b',
            r'\b(data mining|big data|analytics)\b',
            r'\b(personalized|precision|individualized)\b'
        ]
        
        found_terms = []
        for pattern in domain_patterns:
            import re
            matches = re.findall(pattern, combined_text)
            if matches:
                # Take the most common form
                term_counts = {}
                for match in matches:
                    term_counts[match] = term_counts.get(match, 0) + 1
                most_common = max(term_counts.items(), key=lambda x: x[1])[0]
                if most_common not in found_terms:
                    found_terms.append(most_common)
        
        return found_terms
    
    async def create_research_assistance_prompt(
        self,
        question: str,
        user_id: str,
        db: Session,
        reference_ids: Optional[List[str]] = None
    ) -> str:
        """Create reference-based research assistance prompt"""
        prompt_parts = [f"Research Question: {question}", ""]
        
        if reference_ids:
            prompt_parts.append("Context from your Zotero library:")
            prompt_parts.append("")
            
            for ref_id in reference_ids:
                try:
                    item = db.query(ZoteroItem).filter(
                        ZoteroItem.id == ref_id,
                        ZoteroItem.user_id == user_id
                    ).first()
                    
                    if item:
                        reference = self._convert_item_to_reference(item)
                        
                        prompt_parts.extend([
                            f"**{reference['title']}**",
                            f"Authors: {', '.join(reference['creators'])}",
                        ])
                        
                        if reference['year']:
                            prompt_parts.append(f"Year: {reference['year']}")
                        if reference.get('publicationTitle'):
                            prompt_parts.append(f"Publication: {reference['publicationTitle']}")
                        if reference.get('abstractNote'):
                            prompt_parts.append(f"Abstract: {reference['abstractNote']}")
                        
                        prompt_parts.append("")
                        
                except Exception as e:
                    print(f"Warning: Failed to load reference {ref_id}: {e}")
        
        prompt_parts.append(
            "Please provide a comprehensive answer based on the referenced papers and your knowledge."
        )
        
        return '\n'.join(prompt_parts)
    
    async def suggest_related_references(
        self,
        note_content: str,
        user_id: str,
        db: Session,
        existing_reference_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Suggest related references for a note"""
        # Extract key terms from note content
        key_terms = self._extract_key_terms(note_content)
        
        suggestions = []
        existing_ids = set(existing_reference_ids or [])
        
        # Search for related references using key terms
        for term in key_terms[:3]:  # Limit to top 3 terms
            try:
                search_results = await self.search_service.search_items(
                    user_id=user_id,
                    query=term,
                    limit=3,
                    db=db
                )
                
                if search_results.get('items'):
                    new_refs = [
                        self._convert_item_to_reference(item)
                        for item in search_results['items']
                        if item.id not in existing_ids
                    ]
                    suggestions.extend(new_refs)
                    
            except Exception as e:
                print(f"Warning: Failed to search for term '{term}': {e}")
        
        # Remove duplicates and limit results
        unique_suggestions = []
        seen_ids = set()
        
        for ref in suggestions:
            if ref['id'] not in seen_ids:
                unique_suggestions.append(ref)
                seen_ids.add(ref['id'])
        
        return unique_suggestions[:5]
    
    def _extract_key_terms(self, content: str) -> List[str]:
        """Extract key terms from text content"""
        # Simple term extraction - in production, would use NLP
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        
        # Count word frequency
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Return top terms
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10]]
    
    async def export_research_project(
        self,
        project_data: Dict[str, Any],
        user_id: str,
        db: Session
    ) -> str:
        """Export research project with references"""
        export_parts = [
            f"# {project_data.get('title', 'Research Project')}",
            "",
            project_data.get('description', ''),
            "",
            f"Status: {project_data.get('status', 'active')}",
            f"Created: {project_data.get('createdAt', datetime.now().isoformat())}",
            f"Updated: {project_data.get('updatedAt', datetime.now().isoformat())}",
            ""
        ]
        
        # Add references section
        references = project_data.get('references', [])
        if references:
            export_parts.extend(["## References", ""])
            
            for i, ref in enumerate(references):
                authors = ', '.join(ref.get('creators', []))
                year = f" ({ref['year']})" if ref.get('year') else ''
                publication = f". {ref['publicationTitle']}" if ref.get('publicationTitle') else ''
                
                export_parts.append(f"{i + 1}. {authors}{year}. {ref['title']}{publication}")
            
            export_parts.append("")
        
        # Add notes section
        notes = project_data.get('notes', [])
        if notes:
            export_parts.extend(["## Research Notes", ""])
            
            for note in notes:
                export_parts.extend([
                    f"### {note.get('title', 'Untitled Note')}",
                    ""
                ])
                
                # Process note content
                processed_result = await self.process_note_content(
                    note.get('content', ''),
                    user_id,
                    db
                )
                export_parts.extend([processed_result['processedContent'], ""])
                
                # Add tags
                tags = note.get('tags', [])
                if tags:
                    export_parts.extend([f"**Tags:** {', '.join(tags)}", ""])
        
        return '\n'.join(export_parts)


# Global service instance
zotero_research_service = ZoteroResearchIntegrationService()