"""
AI Research Chat Assistant Service
Provides conversational research guidance through an intelligent chat interface.
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_

from core.database import (
    get_db, Document, DocumentChunk, DocumentTag, AnalyticsEvent,
    User, UserProfile, KGEntity, KGRelationship
)
from services.research_assistant import ResearchAssistant
from services.knowledge_graph import KnowledgeGraphService

logger = logging.getLogger(__name__)

class ChatMessageType(str, Enum):
    """Chat message types"""
    USER_QUESTION = "user_question"
    AI_RESPONSE = "ai_response"
    SYSTEM_MESSAGE = "system_message"
    RESEARCH_SUGGESTION = "research_suggestion"

class ResearchContext(str, Enum):
    """Research context types"""
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY_DESIGN = "methodology_design"
    DATA_ANALYSIS = "data_analysis"
    HYPOTHESIS_TESTING = "hypothesis_testing"
    CONCEPT_EXPLORATION = "concept_exploration"
    GENERAL_RESEARCH = "general_research"

@dataclass
class ChatMessage:
    """Chat message structure"""
    id: str
    user_id: str
    session_id: str
    message_type: ChatMessageType
    content: str
    context: Optional[ResearchContext] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    confidence_score: Optional[float] = None
    sources: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None

@dataclass
class ResearchAnswer:
    """Research answer structure"""
    answer: str
    confidence: float
    sources: List[str]
    related_concepts: List[str]
    follow_up_questions: List[str]
    methodology_suggestions: List[str]
    context: ResearchContext

@dataclass
class ChatSession:
    """Chat session management"""
    id: str
    user_id: str
    title: str
    context: ResearchContext
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    is_active: bool

class AIResearchChatService:
    """Main AI Research Chat service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.research_assistant = ResearchAssistant(db)
        self.kg_service = KnowledgeGraphService(db)
        
        # Chat session storage
        self.active_sessions: Dict[str, ChatSession] = {}
        
        # Research knowledge patterns
        self.research_patterns = {
            "methodology_questions": [
                r"what methodology should i use",
                r"which research method",
                r"how to design study"
            ],
            "concept_questions": [
                r"what is",
                r"explain",
                r"define"
            ],
            "literature_questions": [
                r"literature review",
                r"research papers",
                r"previous studies"
            ]
        }

    async def start_chat_session(
        self,
        user_id: str,
        context: ResearchContext = ResearchContext.GENERAL_RESEARCH,
        title: Optional[str] = None
    ) -> ChatSession:
        """Start a new chat session"""
        try:
            session_id = str(uuid.uuid4())
            
            if not title:
                title = f"Research Chat - {context.value.replace('_', ' ').title()}"
            
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                title=title,
                context=context,
                messages=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            
            # Add welcome message
            welcome_msg = await self._generate_welcome_message(user_id, context)
            welcome_msg.session_id = session_id
            session.messages.append(welcome_msg)
            
            # Store session
            self.active_sessions[session_id] = session
            
            # Track analytics
            await self._track_chat_event(user_id, "chat_session_started", {
                "session_id": session_id,
                "context": context.value
            })
            
            return session
            
        except Exception as e:
            logger.error(f"Error starting chat session: {str(e)}")
            raise

    async def ask_research_question(
        self,
        session_id: str,
        question: str,
        context_override: Optional[ResearchContext] = None
    ) -> ResearchAnswer:
        """Process a research question and provide intelligent answer"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                raise ValueError("Chat session not found")
            
            # Determine question context
            question_context = context_override or self._classify_question(question)
            
            # Add user message to session
            user_msg = ChatMessage(
                id=str(uuid.uuid4()),
                user_id=session.user_id,
                session_id=session_id,
                message_type=ChatMessageType.USER_QUESTION,
                content=question,
                context=question_context,
                timestamp=datetime.utcnow()
            )
            session.messages.append(user_msg)
            
            # Generate research answer
            answer = await self._generate_research_answer(
                session.user_id, question, question_context, session
            )
            
            # Add AI response to session
            ai_msg = ChatMessage(
                id=str(uuid.uuid4()),
                user_id=session.user_id,
                session_id=session_id,
                message_type=ChatMessageType.AI_RESPONSE,
                content=answer.answer,
                context=question_context,
                metadata={
                    "confidence": answer.confidence,
                    "sources": answer.sources,
                    "related_concepts": answer.related_concepts
                },
                timestamp=datetime.utcnow(),
                confidence_score=answer.confidence,
                sources=answer.sources,
                suggestions=answer.follow_up_questions
            )
            session.messages.append(ai_msg)
            
            # Update session
            session.updated_at = datetime.utcnow()
            
            return answer
            
        except Exception as e:
            logger.error(f"Error processing research question: {str(e)}")
            raise

    async def get_chat_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> Union[List[ChatMessage], ChatSession]:
        """Get chat history for user or specific session"""
        try:
            if session_id:
                session = self.active_sessions.get(session_id)
                if session and session.user_id == user_id:
                    return session
                else:
                    raise ValueError("Session not found or access denied")
            else:
                # Get recent messages across all sessions for user
                all_messages = []
                for session in self.active_sessions.values():
                    if session.user_id == user_id:
                        all_messages.extend(session.messages)
                
                # Sort by timestamp and limit
                all_messages.sort(key=lambda x: x.timestamp or datetime.min, reverse=True)
                return all_messages[:limit]
                
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            raise

    def _classify_question(self, question: str) -> ResearchContext:
        """Classify question to determine context"""
        question_lower = question.lower()
        
        for context_type, patterns in self.research_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    if context_type == "methodology_questions":
                        return ResearchContext.METHODOLOGY_DESIGN
                    elif context_type == "concept_questions":
                        return ResearchContext.CONCEPT_EXPLORATION
                    elif context_type == "literature_questions":
                        return ResearchContext.LITERATURE_REVIEW
        
        return ResearchContext.GENERAL_RESEARCH

    async def _generate_welcome_message(self, user_id: str, context: ResearchContext) -> ChatMessage:
        """Generate welcome message for new chat session"""
        context_messages = {
            ResearchContext.LITERATURE_REVIEW: "I'm here to help you with literature reviews and finding relevant papers.",
            ResearchContext.METHODOLOGY_DESIGN: "I can assist you with choosing appropriate research methodologies.",
            ResearchContext.CONCEPT_EXPLORATION: "I can explain research concepts and their applications.",
            ResearchContext.GENERAL_RESEARCH: "I'm your AI research assistant, ready to help with any research questions."
        }
        
        welcome_text = f"Hello! {context_messages.get(context, context_messages[ResearchContext.GENERAL_RESEARCH])} What would you like to explore today?"
        
        return ChatMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id="",  # Will be set by caller
            message_type=ChatMessageType.SYSTEM_MESSAGE,
            content=welcome_text,
            context=context,
            timestamp=datetime.utcnow()
        )

    async def _generate_research_answer(
        self,
        user_id: str,
        question: str,
        context: ResearchContext,
        session: ChatSession
    ) -> ResearchAnswer:
        """Generate intelligent research answer"""
        try:
            # Get user's knowledge context
            user_docs = self.db.query(Document).filter(
                Document.user_id == user_id,
                Document.status == "completed"
            ).limit(5).all()
            
            # Extract relevant information
            relevant_content = []
            sources = []
            
            for doc in user_docs:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).limit(2).all()
                
                for chunk in chunks:
                    if any(word in chunk.content.lower() for word in question.lower().split()):
                        relevant_content.append(chunk.content[:300])
                        sources.append(doc.name)
            
            # Generate answer based on context
            if context == ResearchContext.METHODOLOGY_DESIGN:
                answer = await self._generate_methodology_answer(question, relevant_content)
            elif context == ResearchContext.CONCEPT_EXPLORATION:
                answer = await self._generate_concept_answer(question, relevant_content)
            else:
                answer = await self._generate_general_answer(question, relevant_content)
            
            # Get related concepts
            related_concepts = await self._get_related_concepts(user_id, question)
            
            # Generate follow-up questions
            follow_ups = self._generate_follow_up_questions(context)
            
            return ResearchAnswer(
                answer=answer,
                confidence=0.8,
                sources=list(set(sources))[:3],
                related_concepts=related_concepts,
                follow_up_questions=follow_ups,
                methodology_suggestions=[],
                context=context
            )
            
        except Exception as e:
            logger.error(f"Error generating research answer: {str(e)}")
            return ResearchAnswer(
                answer="I'd be happy to help with your research question. Could you provide more details?",
                confidence=0.5,
                sources=[],
                related_concepts=[],
                follow_up_questions=["What specific aspect would you like to explore?"],
                methodology_suggestions=[],
                context=context
            )

    async def _generate_methodology_answer(self, question: str, content: List[str]) -> str:
        """Generate methodology-specific answer"""
        base_answer = "For your research question, I'd recommend considering:\n\n"
        
        if "quantitative" in question.lower():
            base_answer += "• Quantitative approaches for measuring relationships\n"
            base_answer += "• Consider experimental or survey designs\n"
        elif "qualitative" in question.lower():
            base_answer += "• Qualitative approaches for exploring experiences\n"
            base_answer += "• Consider interviews or focus groups\n"
        else:
            base_answer += "• Mixed methods might provide comprehensive insights\n"
            base_answer += "• Consider your research questions and resources\n"
        
        return base_answer

    async def _generate_concept_answer(self, question: str, content: List[str]) -> str:
        """Generate concept explanation answer"""
        concept_patterns = [r"what is (.+?)[\?\.]", r"explain (.+?)[\?\.]", r"define (.+?)[\?\.]"]
        
        concept = "the concept"
        for pattern in concept_patterns:
            match = re.search(pattern, question.lower())
            if match:
                concept = match.group(1).strip()
                break
        
        base_answer = f"Regarding {concept}:\n\n"
        
        if content:
            base_answer += f"Based on your documents, {concept} appears in your research context.\n"
        else:
            base_answer += f"{concept.title()} is an important research concept. "
            base_answer += "I'd be happy to provide more details if you specify the domain.\n"
        
        return base_answer

    async def _generate_general_answer(self, question: str, content: List[str]) -> str:
        """Generate general research answer"""
        base_answer = "That's an interesting research question. "
        
        if content:
            base_answer += "I found relevant information in your documents that might help.\n\n"
            base_answer += "Key considerations:\n"
            for i, text in enumerate(content[:2]):
                summary = text[:150] + "..." if len(text) > 150 else text
                base_answer += f"• {summary}\n"
        else:
            base_answer += "To provide a specific answer, I'd need more context about your research.\n"
        
        return base_answer

    async def _get_related_concepts(self, user_id: str, question: str) -> List[str]:
        """Get related concepts from knowledge graph"""
        try:
            question_words = [word.lower() for word in question.split() if len(word) > 3]
            
            entities = self.db.query(KGEntity).filter(
                KGEntity.user_id == user_id
            ).limit(10).all()
            
            related_concepts = []
            for entity in entities:
                if any(word in entity.name.lower() for word in question_words):
                    related_concepts.append(entity.name)
            
            return related_concepts[:3]
            
        except Exception as e:
            logger.warning(f"Error getting related concepts: {str(e)}")
            return []

    def _generate_follow_up_questions(self, context: ResearchContext) -> List[str]:
        """Generate relevant follow-up questions"""
        follow_ups = {
            ResearchContext.METHODOLOGY_DESIGN: [
                "What are your research objectives?",
                "What resources do you have available?",
                "What is your timeline?"
            ],
            ResearchContext.CONCEPT_EXPLORATION: [
                "How is this concept applied in practice?",
                "What are related theories?",
                "What are common applications?"
            ],
            ResearchContext.GENERAL_RESEARCH: [
                "Could you provide more context?",
                "What specific aspect interests you?",
                "What are you hoping to achieve?"
            ]
        }
        
        return follow_ups.get(context, follow_ups[ResearchContext.GENERAL_RESEARCH])

    async def _track_chat_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]):
        """Track chat analytics events"""
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                event_data={
                    **event_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "ai_research_chat"
                }
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking chat event: {str(e)}")

# Export classes
__all__ = [
    'AIResearchChatService',
    'ChatMessage',
    'ResearchAnswer',
    'ChatSession',
    'ChatMessageType',
    'ResearchContext'
]