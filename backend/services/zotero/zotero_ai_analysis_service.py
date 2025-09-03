"""
Zotero AI Analysis Service for reference content analysis, topic extraction, and insights
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import requests
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from core.config import settings
from core.database import get_db
from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroConnection
from models.zotero_schemas import ZoteroItemResponse

logger = logging.getLogger(__name__)


class ZoteroAIAnalysisService:
    """Service for AI-enhanced analysis of Zotero references"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.max_tokens = 2048
        self.temperature = 0.3
        
    async def analyze_reference_content(
        self,
        item_id: str,
        user_id: str,
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze reference content using LLMs
        
        Args:
            item_id: Zotero item ID
            user_id: User ID for access control
            analysis_types: Types of analysis to perform (topics, keywords, summary)
            
        Returns:
            Dictionary containing analysis results
        """
        if analysis_types is None:
            analysis_types = ["topics", "keywords", "summary"]
            
        try:
            db = next(get_db())
            
            # Get the reference item with access control
            item = await self._get_user_item(db, item_id, user_id)
            if not item:
                raise ValueError(f"Item {item_id} not found or access denied")
            
            analysis_results = {
                "item_id": item_id,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis_types": analysis_types,
                "results": {}
            }
            
            # Extract content for analysis
            content = self._extract_item_content(item)
            if not content.strip():
                return {
                    **analysis_results,
                    "results": {"error": "No content available for analysis"}
                }
            
            # Perform requested analyses
            if "topics" in analysis_types:
                analysis_results["results"]["topics"] = await self._extract_topics(content, item)
                
            if "keywords" in analysis_types:
                analysis_results["results"]["keywords"] = await self._extract_keywords(content, item)
                
            if "summary" in analysis_types:
                analysis_results["results"]["summary"] = await self._generate_summary(content, item)
                
            # Store analysis results in item metadata
            await self._store_analysis_results(db, item_id, analysis_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing reference content for item {item_id}: {e}")
            raise
    
    async def batch_analyze_references(
        self,
        item_ids: List[str],
        user_id: str,
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze multiple references in batch
        
        Args:
            item_ids: List of Zotero item IDs
            user_id: User ID for access control
            analysis_types: Types of analysis to perform
            
        Returns:
            Dictionary containing batch analysis results
        """
        batch_results = {
            "batch_id": f"batch_{int(time.time())}",
            "timestamp": datetime.utcnow().isoformat(),
            "total_items": len(item_ids),
            "successful": 0,
            "failed": 0,
            "results": {},
            "errors": []
        }
        
        for item_id in item_ids:
            try:
                result = await self.analyze_reference_content(item_id, user_id, analysis_types)
                batch_results["results"][item_id] = result
                batch_results["successful"] += 1
            except Exception as e:
                batch_results["failed"] += 1
                batch_results["errors"].append({
                    "item_id": item_id,
                    "error": str(e)
                })
                logger.error(f"Failed to analyze item {item_id}: {e}")
        
        return batch_results
    
    async def get_analysis_results(
        self,
        item_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get stored analysis results for a reference
        
        Args:
            item_id: Zotero item ID
            user_id: User ID for access control
            
        Returns:
            Stored analysis results or None if not found
        """
        try:
            db = next(get_db())
            
            item = await self._get_user_item(db, item_id, user_id)
            if not item:
                return None
            
            # Extract analysis results from metadata
            metadata = item.item_metadata or {}
            return metadata.get("ai_analysis")
            
        except Exception as e:
            logger.error(f"Error retrieving analysis results for item {item_id}: {e}")
            return None
    
    async def _extract_topics(self, content: str, item: ZoteroItem) -> Dict[str, Any]:
        """Extract topics from reference content using LLM"""
        prompt = f"""
        Analyze the following academic reference and extract the main topics and themes.
        
        Title: {item.title or 'N/A'}
        Abstract: {item.abstract_note or 'N/A'}
        Publication: {item.publication_title or 'N/A'}
        Year: {item.publication_year or 'N/A'}
        
        Content to analyze:
        {content[:2000]}  # Limit content length
        
        Please identify:
        1. Primary research topics (3-5 main topics)
        2. Secondary themes (2-4 supporting themes)
        3. Research domain/field
        4. Methodology type (if applicable)
        
        Respond in JSON format:
        {{
            "primary_topics": ["topic1", "topic2", ...],
            "secondary_themes": ["theme1", "theme2", ...],
            "research_domain": "domain name",
            "methodology": "methodology type or null",
            "confidence_score": 0.0-1.0
        }}
        """
        
        try:
            response = await self._call_llm(prompt)
            result = json.loads(response)
            
            # Validate and clean the response
            return {
                "primary_topics": result.get("primary_topics", [])[:5],
                "secondary_themes": result.get("secondary_themes", [])[:4],
                "research_domain": result.get("research_domain", "Unknown"),
                "methodology": result.get("methodology"),
                "confidence_score": min(max(result.get("confidence_score", 0.5), 0.0), 1.0),
                "extraction_timestamp": datetime.utcnow().isoformat()
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response for topic extraction: {e}")
            return {
                "primary_topics": [],
                "secondary_themes": [],
                "research_domain": "Unknown",
                "methodology": None,
                "confidence_score": 0.0,
                "error": "Failed to parse LLM response"
            }
    
    async def _extract_keywords(self, content: str, item: ZoteroItem) -> Dict[str, Any]:
        """Extract keywords from reference content using LLM"""
        prompt = f"""
        Extract relevant keywords and key phrases from this academic reference.
        
        Title: {item.title or 'N/A'}
        Abstract: {item.abstract_note or 'N/A'}
        Publication: {item.publication_title or 'N/A'}
        
        Content:
        {content[:2000]}
        
        Please identify:
        1. Technical keywords (specific terms, concepts, methods)
        2. General keywords (broader concepts, fields)
        3. Author-provided keywords (if available in the text)
        4. Suggested additional keywords
        
        Respond in JSON format:
        {{
            "technical_keywords": ["keyword1", "keyword2", ...],
            "general_keywords": ["keyword1", "keyword2", ...],
            "author_keywords": ["keyword1", "keyword2", ...],
            "suggested_keywords": ["keyword1", "keyword2", ...],
            "confidence_score": 0.0-1.0
        }}
        """
        
        try:
            response = await self._call_llm(prompt)
            result = json.loads(response)
            
            return {
                "technical_keywords": result.get("technical_keywords", [])[:10],
                "general_keywords": result.get("general_keywords", [])[:8],
                "author_keywords": result.get("author_keywords", [])[:6],
                "suggested_keywords": result.get("suggested_keywords", [])[:5],
                "confidence_score": min(max(result.get("confidence_score", 0.5), 0.0), 1.0),
                "extraction_timestamp": datetime.utcnow().isoformat()
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response for keyword extraction: {e}")
            return {
                "technical_keywords": [],
                "general_keywords": [],
                "author_keywords": [],
                "suggested_keywords": [],
                "confidence_score": 0.0,
                "error": "Failed to parse LLM response"
            }
    
    async def _generate_summary(self, content: str, item: ZoteroItem) -> Dict[str, Any]:
        """Generate AI summary of reference content"""
        prompt = f"""
        Create a comprehensive summary of this academic reference.
        
        Title: {item.title or 'N/A'}
        Authors: {', '.join([f"{c.get('firstName', '')} {c.get('lastName', '')}" for c in (item.creators or [])]) or 'N/A'}
        Publication: {item.publication_title or 'N/A'}
        Year: {item.publication_year or 'N/A'}
        
        Abstract/Content:
        {content[:3000]}
        
        Please provide:
        1. A concise summary (2-3 sentences)
        2. Key findings or contributions (3-5 points)
        3. Research methodology (if identifiable)
        4. Significance and implications
        5. Limitations or future work mentioned
        
        Respond in JSON format:
        {{
            "concise_summary": "2-3 sentence summary",
            "key_findings": ["finding1", "finding2", ...],
            "methodology": "methodology description or null",
            "significance": "significance and implications",
            "limitations": "limitations or future work",
            "confidence_score": 0.0-1.0
        }}
        """
        
        try:
            response = await self._call_llm(prompt)
            result = json.loads(response)
            
            return {
                "concise_summary": result.get("concise_summary", ""),
                "key_findings": result.get("key_findings", [])[:5],
                "methodology": result.get("methodology"),
                "significance": result.get("significance", ""),
                "limitations": result.get("limitations", ""),
                "confidence_score": min(max(result.get("confidence_score", 0.5), 0.0), 1.0),
                "generation_timestamp": datetime.utcnow().isoformat()
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response for summary generation: {e}")
            return {
                "concise_summary": "",
                "key_findings": [],
                "methodology": None,
                "significance": "",
                "limitations": "",
                "confidence_score": 0.0,
                "error": "Failed to parse LLM response"
            }
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM: {e}")
            raise Exception(f"LLM service unavailable: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling LLM: {e}")
            raise
    
    def _extract_item_content(self, item: ZoteroItem) -> str:
        """Extract text content from Zotero item for analysis"""
        content_parts = []
        
        if item.title:
            content_parts.append(f"Title: {item.title}")
        
        if item.abstract_note:
            content_parts.append(f"Abstract: {item.abstract_note}")
        
        if item.creators:
            authors = []
            for creator in item.creators:
                if isinstance(creator, dict):
                    name_parts = []
                    if creator.get("firstName"):
                        name_parts.append(creator["firstName"])
                    if creator.get("lastName"):
                        name_parts.append(creator["lastName"])
                    if creator.get("name"):
                        name_parts.append(creator["name"])
                    if name_parts:
                        authors.append(" ".join(name_parts))
            if authors:
                content_parts.append(f"Authors: {', '.join(authors)}")
        
        if item.publication_title:
            content_parts.append(f"Publication: {item.publication_title}")
        
        if item.publication_year:
            content_parts.append(f"Year: {item.publication_year}")
        
        if item.tags:
            if isinstance(item.tags, list):
                content_parts.append(f"Tags: {', '.join(item.tags)}")
        
        if item.extra_fields and isinstance(item.extra_fields, dict):
            for key, value in item.extra_fields.items():
                if value and isinstance(value, str) and len(value) > 10:
                    content_parts.append(f"{key}: {value}")
        
        return "\n\n".join(content_parts)
    
    async def _get_user_item(self, db: Session, item_id: str, user_id: str) -> Optional[ZoteroItem]:
        """Get Zotero item with user access control"""
        return db.query(ZoteroItem).join(
            ZoteroLibrary, ZoteroItem.library_id == ZoteroLibrary.id
        ).join(
            ZoteroConnection, ZoteroLibrary.connection_id == ZoteroConnection.id
        ).filter(
            and_(
                ZoteroItem.id == item_id,
                ZoteroConnection.user_id == user_id,
                ZoteroItem.is_deleted == False
            )
        ).first()
    
    async def _store_analysis_results(
        self,
        db: Session,
        item_id: str,
        analysis_results: Dict[str, Any]
    ) -> None:
        """Store analysis results in item metadata"""
        try:
            item = db.query(ZoteroItem).filter(ZoteroItem.id == item_id).first()
            if item:
                metadata = item.item_metadata or {}
                metadata["ai_analysis"] = analysis_results
                item.item_metadata = metadata
                db.commit()
        except Exception as e:
            logger.error(f"Error storing analysis results for item {item_id}: {e}")
            db.rollback()
            raise