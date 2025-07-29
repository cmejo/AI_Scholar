"""
RAG service for generating responses with context
"""
import json
import time
import logging
from typing import List, Dict, Any, Optional
import requests
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db, Conversation, Message, Document
from services.vector_store import VectorStoreService
from services.knowledge_graph import KnowledgeGraphService
from models.schemas import ChatResponse, Source

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.knowledge_graph = KnowledgeGraphService()
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
    
    async def generate_response(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        use_chain_of_thought: bool = False,
        citation_mode: bool = True
    ) -> ChatResponse:
        """Generate RAG response"""
        start_time = time.time()
        
        try:
            # Get or create conversation
            db = next(get_db())
            
            if conversation_id:
                conversation = db.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                ).first()
            else:
                conversation = Conversation(
                    user_id=user_id,
                    title=query[:50] + "..." if len(query) > 50 else query
                )
                db.add(conversation)
                db.commit()
                conversation_id = conversation.id
            
            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                role="user",
                content=query
            )
            db.add(user_message)
            db.commit()
            
            # Perform semantic search
            search_results = await self.vector_store.semantic_search(
                query=query,
                user_id=user_id,
                limit=5
            )
            
            # Build context from search results
            context = self._build_context(search_results)
            
            # Generate response using Ollama
            if use_chain_of_thought:
                response_text, chain_of_thought = await self._generate_chain_of_thought_response(query, context)
            else:
                response_text = await self._generate_standard_response(query, context, citation_mode)
                chain_of_thought = None
            
            # Format sources
            sources = self._format_sources(search_results)
            
            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=response_text,
                sources=json.dumps([source.dict() for source in sources]),
                metadata=json.dumps({
                    "chain_of_thought": chain_of_thought,
                    "search_results_count": len(search_results)
                })
            )
            db.add(assistant_message)
            db.commit()
            
            processing_time = time.time() - start_time
            
            return ChatResponse(
                response=response_text,
                sources=sources,
                conversation_id=conversation_id,
                model=self.model,
                processing_time=processing_time,
                chain_of_thought=chain_of_thought
            )
            
        except Exception as e:
            logger.error(f"RAG generation error: {str(e)}")
            raise e
        finally:
            if 'db' in locals():
                db.close()
    
    async def _generate_standard_response(self, query: str, context: str, citation_mode: bool) -> str:
        """Generate standard RAG response"""
        if citation_mode:
            prompt = f"""Based on the following context, please answer the question and include citations in the format [Source X] where X is the source number.

Context:
{context}

Question: {query}

Please provide a comprehensive answer with proper citations:"""
        else:
            prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 1024
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "I apologize, but I'm having trouble generating a response right now. Please try again."
                
        except Exception as e:
            logger.error(f"Ollama request error: {str(e)}")
            return "I apologize, but I'm having trouble connecting to the language model. Please try again."
    
    async def _generate_chain_of_thought_response(self, query: str, context: str) -> tuple[str, Dict[str, Any]]:
        """Generate response with chain of thought reasoning"""
        cot_prompt = f"""Let me think through this step by step.

Context: {context}

Question: {query}

Let me break this down:

Step 1: Understanding the question
{query} - This is asking about...

Step 2: Analyzing the available information
From the context, I can see that...

Step 3: Reasoning through the problem
Based on the information, I need to consider...

Step 4: Drawing conclusions
Therefore, the answer is...

Final Answer:"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": cot_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 1500
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                full_response = response.json()["response"]
                
                # Extract final answer and reasoning steps
                if "Final Answer:" in full_response:
                    parts = full_response.split("Final Answer:")
                    reasoning = parts[0].strip()
                    final_answer = parts[1].strip()
                else:
                    reasoning = full_response
                    final_answer = full_response
                
                chain_of_thought = {
                    "reasoning_steps": reasoning,
                    "final_answer": final_answer,
                    "total_steps": reasoning.count("Step"),
                    "confidence": 0.8  # Mock confidence
                }
                
                return final_answer, chain_of_thought
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "I apologize, but I'm having trouble generating a response right now.", None
                
        except Exception as e:
            logger.error(f"Chain of thought generation error: {str(e)}")
            return "I apologize, but I'm having trouble with the reasoning process.", None
    
    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Build context string from search results"""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            metadata = result.get("metadata", {})
            document_name = metadata.get("document_name", "Unknown")
            page_number = metadata.get("page_number", 1)
            
            context_parts.append(
                f"Source {i} ({document_name}, page {page_number}):\n{result['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    def _format_sources(self, search_results: List[Dict[str, Any]]) -> List[Source]:
        """Format search results as sources"""
        sources = []
        
        for result in search_results:
            metadata = result.get("metadata", {})
            
            source = Source(
                document=metadata.get("document_name", "Unknown"),
                page=metadata.get("page_number", 1),
                relevance=result.get("relevance", 0.0),
                snippet=result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
            )
            sources.append(source)
        
        return sources
    
    async def compare_documents(
        self,
        document_ids: List[str],
        query: str,
        comparison_type: str = "general"
    ) -> Dict[str, Any]:
        """Compare multiple documents"""
        try:
            db = next(get_db())
            
            # Get documents
            documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
            
            if len(documents) < 2:
                raise ValueError("At least 2 documents required for comparison")
            
            # Get relevant chunks from each document
            document_contexts = {}
            for doc in documents:
                search_results = await self.vector_store.semantic_search(
                    query=query,
                    user_id="",  # Skip user filter for comparison
                    limit=3,
                    filter_metadata={"document_id": doc.id}
                )
                document_contexts[doc.id] = {
                    "name": doc.name,
                    "content": self._build_context(search_results)
                }
            
            # Generate comparison
            comparison_prompt = f"""Compare the following documents regarding: {query}

Document 1 ({document_contexts[document_ids[0]]['name']}):
{document_contexts[document_ids[0]]['content']}

Document 2 ({document_contexts[document_ids[1]]['name']}):
{document_contexts[document_ids[1]]['content']}

Please provide a detailed comparison focusing on:
1. Key similarities
2. Key differences
3. Overall summary

Comparison:"""
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": comparison_prompt,
                    "stream": False
                },
                timeout=60
            )
            
            comparison_text = response.json()["response"] if response.status_code == 200 else "Comparison failed"
            
            return {
                "documents": document_ids,
                "comparison_type": comparison_type,
                "summary": comparison_text,
                "document_names": [doc.name for doc in documents]
            }
            
        except Exception as e:
            logger.error(f"Document comparison error: {str(e)}")
            raise e
        finally:
            if 'db' in locals():
                db.close()
    
    async def get_analytics_data(self, user_id: str) -> Dict[str, Any]:
        """Get analytics data for user"""
        try:
            db = next(get_db())
            
            # Get user's conversations and messages
            conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
            total_conversations = len(conversations)
            
            messages = db.query(Message).join(Conversation).filter(
                Conversation.user_id == user_id,
                Message.role == "user"
            ).all()
            total_queries = len(messages)
            
            # Get user's documents
            documents = db.query(Document).filter(Document.user_id == user_id).all()
            total_documents = len(documents)
            total_chunks = sum(doc.chunks_count or 0 for doc in documents)
            
            # Vector store stats
            vector_stats = await self.vector_store.get_stats()
            
            return {
                "user_stats": {
                    "total_conversations": total_conversations,
                    "total_queries": total_queries,
                    "total_documents": total_documents,
                    "total_chunks": total_chunks
                },
                "system_stats": vector_stats,
                "recent_activity": [
                    {
                        "type": "conversation",
                        "title": conv.title,
                        "created_at": conv.created_at.isoformat()
                    }
                    for conv in conversations[-5:]  # Last 5 conversations
                ]
            }
            
        except Exception as e:
            logger.error(f"Analytics error: {str(e)}")
            return {"error": str(e)}
        finally:
            if 'db' in locals():
                db.close()