"""
Auto-tagging service for LLM-assisted document metadata generation
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
import requests
from sqlalchemy.orm import Session
from datetime import datetime

from core.config import settings
from core.database import get_db, Document, DocumentTag
from models.schemas import (
    DocumentTagCreate, 
    DocumentTagResponse, 
    TagType
)

logger = logging.getLogger(__name__)

class AutoTaggingService:
    """Service for automatic document tagging using LLM assistance"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.confidence_threshold = 0.6
        self.max_tags_per_type = 5
        
    async def generate_document_tags(
        self, 
        document_id: str, 
        content: str,
        db: Session
    ) -> List[DocumentTagResponse]:
        """
        Generate comprehensive tags for a document using LLM assistance
        
        Args:
            document_id: ID of the document to tag
            content: Document content to analyze
            db: Database session
            
        Returns:
            List of generated document tags
        """
        try:
            # Generate different types of tags
            topic_tags = await self._generate_topic_tags(content)
            domain_tags = await self._generate_domain_tags(content)
            complexity_tags = await self._generate_complexity_tags(content)
            sentiment_tags = await self._generate_sentiment_tags(content)
            category_tags = await self._generate_category_tags(content)
            
            all_tags = []
            all_tags.extend(topic_tags)
            all_tags.extend(domain_tags)
            all_tags.extend(complexity_tags)
            all_tags.extend(sentiment_tags)
            all_tags.extend(category_tags)
            
            # Store tags in database
            stored_tags = []
            for tag_data in all_tags:
                if tag_data['confidence'] >= self.confidence_threshold:
                    tag_create = DocumentTagCreate(
                        document_id=document_id,
                        tag_name=tag_data['name'],
                        tag_type=TagType(tag_data['type']),
                        confidence_score=tag_data['confidence'],
                        generated_by="llm"
                    )
                    
                    tag_db = DocumentTag(
                        document_id=tag_create.document_id,
                        tag_name=tag_create.tag_name,
                        tag_type=tag_create.tag_type.value,
                        confidence_score=tag_create.confidence_score,
                        generated_by=tag_create.generated_by
                    )
                    
                    db.add(tag_db)
                    db.commit()
                    db.refresh(tag_db)
                    
                    stored_tags.append(DocumentTagResponse(
                        id=tag_db.id,
                        document_id=tag_db.document_id,
                        tag_name=tag_db.tag_name,
                        tag_type=tag_db.tag_type,
                        confidence_score=tag_db.confidence_score,
                        generated_by=tag_db.generated_by,
                        created_at=tag_db.created_at
                    ))
            
            logger.info(f"Generated {len(stored_tags)} tags for document {document_id}")
            return stored_tags
            
        except Exception as e:
            logger.error(f"Error generating tags for document {document_id}: {str(e)}")
            raise
    
    async def _generate_topic_tags(self, content: str) -> List[Dict[str, Any]]:
        """Generate topic-based tags for the document"""
        prompt = f"""
        Analyze the following document content and identify the main topics discussed.
        Provide up to {self.max_tags_per_type} specific topic tags with confidence scores.
        
        Content: {content[:2000]}...
        
        Respond in JSON format:
        {{
            "topics": [
                {{"name": "topic_name", "confidence": 0.85, "explanation": "brief explanation"}},
                ...
            ]
        }}
        """
        
        try:
            response = await self._call_llm(prompt)
            topics_data = json.loads(response)
            
            tags = []
            for topic in topics_data.get('topics', []):
                tags.append({
                    'name': topic['name'].lower().replace(' ', '_'),
                    'type': 'topic',
                    'confidence': float(topic['confidence']),
                    'explanation': topic.get('explanation', '')
                })
            
            return tags[:self.max_tags_per_type]
            
        except Exception as e:
            logger.error(f"Error generating topic tags: {str(e)}")
            return []
    
    async def _generate_domain_tags(self, content: str) -> List[Dict[str, Any]]:
        """Generate domain/field-specific tags"""
        prompt = f"""
        Analyze the following document content and identify the academic or professional domains it belongs to.
        Consider fields like: technology, medicine, law, business, science, education, etc.
        Provide up to {self.max_tags_per_type} domain tags with confidence scores.
        
        Content: {content[:2000]}...
        
        Respond in JSON format:
        {{
            "domains": [
                {{"name": "domain_name", "confidence": 0.90, "explanation": "brief explanation"}},
                ...
            ]
        }}
        """
        
        try:
            response = await self._call_llm(prompt)
            domains_data = json.loads(response)
            
            tags = []
            for domain in domains_data.get('domains', []):
                tags.append({
                    'name': domain['name'].lower().replace(' ', '_'),
                    'type': 'domain',
                    'confidence': float(domain['confidence']),
                    'explanation': domain.get('explanation', '')
                })
            
            return tags[:self.max_tags_per_type]
            
        except Exception as e:
            logger.error(f"Error generating domain tags: {str(e)}")
            return []
    
    async def _generate_complexity_tags(self, content: str) -> List[Dict[str, Any]]:
        """Generate complexity level tags"""
        prompt = f"""
        Analyze the following document content and determine its complexity level.
        Consider factors like: vocabulary difficulty, concept complexity, technical depth, required background knowledge.
        
        Content: {content[:2000]}...
        
        Classify the complexity as one of: beginner, intermediate, advanced, expert
        Also provide specific complexity aspects.
        
        Respond in JSON format:
        {{
            "complexity": {{
                "overall_level": "intermediate",
                "confidence": 0.85,
                "aspects": [
                    {{"name": "technical_complexity", "level": "advanced", "confidence": 0.80}},
                    {{"name": "vocabulary_difficulty", "level": "intermediate", "confidence": 0.90}}
                ]
            }}
        }}
        """
        
        try:
            response = await self._call_llm(prompt)
            complexity_data = json.loads(response)
            
            tags = []
            complexity = complexity_data.get('complexity', {})
            
            # Overall complexity tag
            if 'overall_level' in complexity:
                tags.append({
                    'name': f"complexity_{complexity['overall_level']}",
                    'type': 'complexity',
                    'confidence': float(complexity.get('confidence', 0.5)),
                    'explanation': f"Overall complexity level: {complexity['overall_level']}"
                })
            
            # Specific aspect tags
            for aspect in complexity.get('aspects', []):
                tags.append({
                    'name': f"{aspect['name']}_{aspect['level']}",
                    'type': 'complexity',
                    'confidence': float(aspect.get('confidence', 0.5)),
                    'explanation': f"{aspect['name']} is at {aspect['level']} level"
                })
            
            return tags[:self.max_tags_per_type]
            
        except Exception as e:
            logger.error(f"Error generating complexity tags: {str(e)}")
            return []
    
    async def _generate_sentiment_tags(self, content: str) -> List[Dict[str, Any]]:
        """Generate sentiment and tone tags"""
        prompt = f"""
        Analyze the following document content and determine its sentiment and tone.
        Consider: emotional tone, formality level, objectivity vs subjectivity, persuasive intent.
        
        Content: {content[:2000]}...
        
        Respond in JSON format:
        {{
            "sentiment": {{
                "emotional_tone": "neutral",
                "formality": "formal",
                "objectivity": "objective",
                "confidence": 0.80
            }}
        }}
        """
        
        try:
            response = await self._call_llm(prompt)
            sentiment_data = json.loads(response)
            
            tags = []
            sentiment = sentiment_data.get('sentiment', {})
            
            for aspect, value in sentiment.items():
                if aspect != 'confidence' and value:
                    tags.append({
                        'name': f"{aspect}_{value}",
                        'type': 'sentiment',
                        'confidence': float(sentiment.get('confidence', 0.5)),
                        'explanation': f"Document has {aspect}: {value}"
                    })
            
            return tags[:self.max_tags_per_type]
            
        except Exception as e:
            logger.error(f"Error generating sentiment tags: {str(e)}")
            return []
    
    async def _generate_category_tags(self, content: str) -> List[Dict[str, Any]]:
        """Generate document category tags"""
        prompt = f"""
        Analyze the following document content and categorize it by document type and purpose.
        Consider categories like: research_paper, tutorial, reference, report, manual, article, etc.
        
        Content: {content[:2000]}...
        
        Respond in JSON format:
        {{
            "categories": [
                {{"name": "document_type", "confidence": 0.90}},
                {{"name": "purpose_category", "confidence": 0.85}}
            ]
        }}
        """
        
        try:
            response = await self._call_llm(prompt)
            categories_data = json.loads(response)
            
            tags = []
            for category in categories_data.get('categories', []):
                tags.append({
                    'name': category['name'].lower().replace(' ', '_'),
                    'type': 'category',
                    'confidence': float(category['confidence']),
                    'explanation': f"Document category: {category['name']}"
                })
            
            return tags[:self.max_tags_per_type]
            
        except Exception as e:
            logger.error(f"Error generating category tags: {str(e)}")
            return []
    
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
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
            
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            raise
    
    async def get_document_tags(
        self, 
        document_id: str, 
        db: Session,
        tag_type: Optional[str] = None
    ) -> List[DocumentTagResponse]:
        """
        Retrieve existing tags for a document
        
        Args:
            document_id: ID of the document
            db: Database session
            tag_type: Optional filter by tag type
            
        Returns:
            List of document tags
        """
        try:
            query = db.query(DocumentTag).filter(DocumentTag.document_id == document_id)
            
            if tag_type:
                query = query.filter(DocumentTag.tag_type == tag_type)
            
            tags = query.all()
            
            return [
                DocumentTagResponse(
                    id=tag.id,
                    document_id=tag.document_id,
                    tag_name=tag.tag_name,
                    tag_type=tag.tag_type,
                    confidence_score=tag.confidence_score,
                    generated_by=tag.generated_by,
                    created_at=tag.created_at
                )
                for tag in tags
            ]
            
        except Exception as e:
            logger.error(f"Error retrieving tags for document {document_id}: {str(e)}")
            raise
    
    async def validate_tag_consistency(
        self, 
        document_id: str, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Validate consistency and quality of generated tags
        
        Args:
            document_id: ID of the document
            db: Database session
            
        Returns:
            Validation results with consistency scores and recommendations
        """
        try:
            tags = await self.get_document_tags(document_id, db)
            
            if not tags:
                return {
                    "consistency_score": 0.0,
                    "issues": ["No tags found for document"],
                    "recommendations": ["Generate tags for this document"],
                    "tag_distribution": {},
                    "average_confidence": 0.0
                }
            
            # Group tags by type
            tags_by_type = {}
            for tag in tags:
                if tag.tag_type not in tags_by_type:
                    tags_by_type[tag.tag_type] = []
                tags_by_type[tag.tag_type].append(tag)
            
            issues = []
            recommendations = []
            
            # Check for minimum confidence scores
            low_confidence_tags = [tag for tag in tags if tag.confidence_score < self.confidence_threshold]
            if low_confidence_tags:
                issues.append(f"Found {len(low_confidence_tags)} tags with low confidence")
                recommendations.append("Review and potentially remove low-confidence tags")
            
            # Check for tag type coverage
            expected_types = ['topic', 'domain', 'complexity']
            missing_types = [t for t in expected_types if t not in tags_by_type]
            if missing_types:
                issues.append(f"Missing tag types: {', '.join(missing_types)}")
                recommendations.append(f"Generate tags for missing types: {', '.join(missing_types)}")
            
            # Calculate overall consistency score
            type_coverage_score = (len(expected_types) - len(missing_types)) / len(expected_types)
            average_confidence = sum(tag.confidence_score for tag in tags) / len(tags) if tags else 0
            consistency_score = (type_coverage_score + average_confidence) / 2
            
            return {
                "consistency_score": consistency_score,
                "issues": issues,
                "recommendations": recommendations,
                "tag_distribution": {tag_type: len(tag_list) for tag_type, tag_list in tags_by_type.items()},
                "average_confidence": average_confidence
            }
            
        except Exception as e:
            logger.error(f"Error validating tag consistency for document {document_id}: {str(e)}")
            raise
    
    async def batch_generate_tags(
        self,
        documents: List[Dict[str, str]],
        db: Session
    ) -> Dict[str, List[DocumentTagResponse]]:
        """
        Generate tags for multiple documents in batch
        
        Args:
            documents: List of documents with 'id' and 'content' keys
            db: Database session
            
        Returns:
            Dictionary mapping document IDs to their generated tags
        """
        results = {}
        
        for doc in documents:
            try:
                document_id = doc['id']
                content = doc['content']
                
                tags = await self.generate_document_tags(document_id, content, db)
                results[document_id] = tags
                
                logger.info(f"Generated {len(tags)} tags for document {document_id}")
                
            except Exception as e:
                logger.error(f"Error generating tags for document {doc.get('id', 'unknown')}: {str(e)}")
                results[doc.get('id', 'unknown')] = []
        
        return results
    
    async def update_tag_confidence(
        self,
        tag_id: str,
        new_confidence: float,
        db: Session
    ) -> bool:
        """
        Update the confidence score of an existing tag
        
        Args:
            tag_id: ID of the tag to update
            new_confidence: New confidence score (0.0 to 1.0)
            db: Database session
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            if not (0.0 <= new_confidence <= 1.0):
                raise ValueError("Confidence score must be between 0.0 and 1.0")
            
            tag = db.query(DocumentTag).filter(DocumentTag.id == tag_id).first()
            
            if not tag:
                logger.warning(f"Tag with ID {tag_id} not found")
                return False
            
            tag.confidence_score = new_confidence
            db.commit()
            
            logger.info(f"Updated confidence score for tag {tag_id} to {new_confidence}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating tag confidence: {str(e)}")
            db.rollback()
            return False
    
    async def delete_low_confidence_tags(
        self,
        document_id: str,
        threshold: Optional[float] = None,
        db: Session = None
    ) -> int:
        """
        Delete tags with confidence scores below the threshold
        
        Args:
            document_id: ID of the document
            threshold: Confidence threshold (uses service default if None)
            db: Database session
            
        Returns:
            Number of tags deleted
        """
        try:
            if threshold is None:
                threshold = self.confidence_threshold
            
            tags_to_delete = db.query(DocumentTag).filter(
                DocumentTag.document_id == document_id,
                DocumentTag.confidence_score < threshold
            ).all()
            
            count = len(tags_to_delete)
            
            for tag in tags_to_delete:
                db.delete(tag)
            
            db.commit()
            
            logger.info(f"Deleted {count} low-confidence tags for document {document_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting low-confidence tags: {str(e)}")
            db.rollback()
            return 0

# Global instance
auto_tagging_service = AutoTaggingService()