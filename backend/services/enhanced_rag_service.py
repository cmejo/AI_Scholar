"""
Enhanced RAG service with memory integration for context-aware responses
"""
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import requests
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from core.config import settings
from core.database import get_db, Conversation, Message, Document
from services.vector_store import VectorStoreService
from services.knowledge_graph import KnowledgeGraphService
from services.memory_service import (
    conversation_memory_manager,
    context_compressor,
    user_memory_store,
    MemoryItem,
    ConversationContext,
    MemoryType
)
from models.schemas import (
    ChatResponse, 
    Source, 
    EnhancedChatResponse,
    ReasoningResult,
    UncertaintyScore
)
from services.reasoning_engine import ReasoningEngine
from services.citation_service import CitationGenerator, RAGCitationIntegrator, CitationFormat

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    """Enhanced RAG service with memory, personalization, and reasoning capabilities"""
    
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.knowledge_graph = KnowledgeGraphService()
        self.memory_manager = conversation_memory_manager
        self.context_compressor = context_compressor
        self.user_memory = user_memory_store
        self.reasoning_engine = ReasoningEngine()
        self.citation_generator = CitationGenerator()
        self.citation_integrator = RAGCitationIntegrator(self.citation_generator)
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.max_context_length = 4000
        
    async def generate_enhanced_response(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        use_chain_of_thought: bool = False,
        citation_mode: bool = True,
        enable_reasoning: bool = True,
        enable_memory: bool = True,
        personalization_level: float = 1.0,
        max_sources: int = 5
    ) -> EnhancedChatResponse:
        """Generate enhanced RAG response with memory and personalization"""
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
            
            # Store user query in memory
            if enable_memory:
                await self._store_query_in_memory(conversation_id, query, user_id)
            
            # Get conversation context from memory
            memory_context = {}
            if enable_memory:
                memory_context = await self._get_memory_context(conversation_id, user_id, query)
            
            # Get personalized context
            personalized_context = {}
            if personalization_level > 0:
                personalized_context = await self.user_memory.get_personalized_context(
                    user_id, query
                )
            
            # Perform enhanced semantic search with personalization
            search_results = await self._enhanced_semantic_search(
                query, user_id, personalized_context, max_sources
            )
            
            # Build enhanced context
            enhanced_context = await self._build_enhanced_context(
                search_results, memory_context, personalized_context, query
            )
            
            # Generate response with reasoning
            response_data = await self._generate_response_with_reasoning(
                query, enhanced_context, use_chain_of_thought, citation_mode, 
                enable_reasoning, personalized_context
            )
            
            # Store response in memory
            if enable_memory:
                await self._store_response_in_memory(
                    conversation_id, response_data["response"], user_id
                )
            
            # Learn from interaction
            if personalization_level > 0:
                await self._learn_from_interaction(
                    user_id, query, response_data, search_results
                )
            
            # Save messages to database
            await self._save_messages_to_db(
                db, conversation_id, query, response_data, search_results
            )
            
            processing_time = time.time() - start_time
            
            # Format sources with knowledge graph information
            sources = self._format_sources(search_results)
            
            # Collect knowledge graph statistics
            kg_stats = self._collect_knowledge_graph_stats(search_results)
            
            # Enhance response with reasoning insights
            enhanced_response = await self._enhance_response_with_reasoning(
                response_data["response"], response_data.get("reasoning_results", [])
            )
            
            # Add citations to response if citation mode is enabled
            citation_data = {}
            if citation_mode:
                citation_data = await self._add_citations_to_response(
                    enhanced_response, search_results, user_id, personalized_context
                )
                enhanced_response = citation_data.get("response", enhanced_response)
            
            return EnhancedChatResponse(
                response=enhanced_response,
                sources=sources,
                conversation_id=conversation_id,
                model=self.model,
                processing_time=processing_time,
                chain_of_thought=response_data.get("chain_of_thought"),
                reasoning_results=response_data.get("reasoning_results", []),
                uncertainty_score=response_data.get("uncertainty_score"),
                memory_context=memory_context,
                personalization_applied=personalization_level > 0,
                knowledge_graph_used=kg_stats["relationships_found"] > 0,
                metadata={
                    "knowledge_graph_stats": kg_stats,
                    "entities_extracted": kg_stats["total_entities"],
                    "relationships_found": kg_stats["relationships_found"],
                    "reasoning_applied": len(response_data.get("reasoning_results", [])) > 0,
                    "reasoning_types": [r.reasoning_type for r in response_data.get("reasoning_results", [])],
                    "average_reasoning_confidence": (
                        sum(r.confidence for r in response_data.get("reasoning_results", [])) / 
                        len(response_data.get("reasoning_results", [])) 
                        if response_data.get("reasoning_results") else 0
                    ),
                    "citations": citation_data.get("citations", []),
                    "bibliography": citation_data.get("bibliography", ""),
                    "citation_format": citation_data.get("citation_format", ""),
                    "citation_style": citation_data.get("citation_style", "")
                }
            )
            
        except Exception as e:
            logger.error(f"Enhanced RAG generation error: {str(e)}")
            raise e
        finally:
            if 'db' in locals():
                db.close()
    
    async def _store_query_in_memory(
        self, 
        conversation_id: str, 
        query: str, 
        user_id: str
    ) -> None:
        """Store user query in conversation memory"""
        try:
            # Calculate importance score for the query
            importance_score = await self.memory_manager.calculate_importance_score(
                query, MemoryType.SHORT_TERM
            )
            
            # Create memory item
            memory_item = MemoryItem(
                content=f"User query: {query}",
                memory_type=MemoryType.SHORT_TERM,
                importance_score=importance_score,
                timestamp=datetime.now(),
                metadata={
                    "type": "user_query",
                    "user_id": user_id,
                    "query_length": len(query),
                    "entities": await self._extract_entities_from_text(query)
                }
            )
            
            await self.memory_manager.store_memory_item(conversation_id, memory_item)
            
        except Exception as e:
            logger.error(f"Error storing query in memory: {e}")
    
    async def _store_response_in_memory(
        self, 
        conversation_id: str, 
        response: str, 
        user_id: str
    ) -> None:
        """Store assistant response in conversation memory"""
        try:
            # Calculate importance score for the response
            importance_score = await self.memory_manager.calculate_importance_score(
                response, MemoryType.CONTEXT
            )
            
            # Create memory item
            memory_item = MemoryItem(
                content=f"Assistant response: {response[:200]}...",  # Truncate for memory
                memory_type=MemoryType.CONTEXT,
                importance_score=importance_score,
                timestamp=datetime.now(),
                metadata={
                    "type": "assistant_response",
                    "user_id": user_id,
                    "response_length": len(response),
                    "entities": await self._extract_entities_from_text(response)
                }
            )
            
            await self.memory_manager.store_memory_item(conversation_id, memory_item)
            
        except Exception as e:
            logger.error(f"Error storing response in memory: {e}")
    
    async def _get_memory_context(
        self, 
        conversation_id: str, 
        user_id: str, 
        current_query: str
    ) -> Dict[str, Any]:
        """Get relevant memory context for the current query"""
        try:
            # Get conversation context
            conversation_context = await self.memory_manager.get_conversation_context(conversation_id)
            
            if not conversation_context:
                return {}
            
            # Compress context if needed
            if conversation_context.total_tokens > self.max_context_length:
                conversation_context = await self.context_compressor.compress_conversation_context(
                    conversation_context
                )
            
            # Get relevant memories based on current query
            relevant_memories = await self.context_compressor.prune_context_by_relevance(
                conversation_context.short_term_memory,
                current_query,
                max_items=10
            )
            
            return {
                "conversation_summary": conversation_context.context_summary,
                "relevant_memories": [
                    {
                        "content": memory.content,
                        "importance": memory.importance_score,
                        "timestamp": memory.timestamp.isoformat(),
                        "type": memory.memory_type.value
                    }
                    for memory in relevant_memories
                ],
                "active_entities": conversation_context.active_entities,
                "memory_count": len(relevant_memories)
            }
            
        except Exception as e:
            logger.error(f"Error getting memory context: {e}")
            return {}
    
    async def _enhanced_semantic_search(
        self,
        query: str,
        user_id: str,
        personalized_context: Dict[str, Any],
        max_sources: int
    ) -> List[Dict[str, Any]]:
        """Perform enhanced semantic search with personalization"""
        try:
            # Get user preferences for search customization
            user_preferences = personalized_context.get("user_preferences", {})
            
            # Adjust search parameters based on preferences
            search_limit = max_sources
            if user_preferences.get("response_style", {}).get("value") == "detailed":
                search_limit = min(max_sources + 2, 10)  # More sources for detailed responses
            
            # Perform semantic search
            search_results = await self.vector_store.semantic_search(
                query=query,
                user_id=user_id,
                limit=search_limit
            )
            
            # Enhance results with knowledge graph information
            enhanced_results = await self._enhance_with_knowledge_graph(search_results, query)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in enhanced semantic search: {e}")
            # Fallback to basic search
            return await self.vector_store.semantic_search(query=query, user_id=user_id, limit=max_sources)
    
    async def _enhance_with_knowledge_graph(
        self,
        search_results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """Enhance search results with knowledge graph relationships"""
        try:
            # Extract entities from query using the knowledge graph service
            query_entities = await self.knowledge_graph.entity_extractor.extract_entities(query)
            query_entity_names = [entity["text"] for entity in query_entities if entity["confidence"] > 0.5]
            
            if not query_entity_names:
                logger.debug("No high-confidence entities found in query")
                return search_results
            
            # For each search result, enhance with knowledge graph information
            enhanced_results = []
            for result in search_results:
                enhanced_result = result.copy()
                
                try:
                    # Extract entities from the search result content
                    content_entities = await self.knowledge_graph.entity_extractor.extract_entities(
                        result["content"]
                    )
                    content_entity_names = [
                        entity["text"] for entity in content_entities 
                        if entity["confidence"] > 0.5
                    ]
                    
                    # Find relationships between query entities and content entities
                    relationship_context = await self._build_relationship_context(
                        query_entity_names, content_entity_names
                    )
                    
                    if relationship_context:
                        enhanced_result["metadata"]["knowledge_graph"] = relationship_context
                        
                        # Calculate knowledge graph boost based on relationship strength
                        kg_boost = self._calculate_knowledge_graph_boost(relationship_context)
                        enhanced_result["relevance"] = min(1.0, result.get("relevance", 0) + kg_boost)
                        
                        # Add relationship summary to metadata
                        enhanced_result["metadata"]["relationship_summary"] = self._summarize_relationships(
                            relationship_context
                        )
                    
                    # Store extracted entities for potential use in response generation
                    enhanced_result["metadata"]["extracted_entities"] = {
                        "query_entities": query_entity_names,
                        "content_entities": content_entity_names
                    }
                        
                except Exception as kg_error:
                    logger.debug(f"Knowledge graph enhancement failed for result: {kg_error}")
                
                enhanced_results.append(enhanced_result)
            
            # Re-rank results based on knowledge graph relationships
            enhanced_results = await self._rerank_with_knowledge_graph(enhanced_results, query_entity_names)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error enhancing with knowledge graph: {e}")
            return search_results
    
    async def _build_enhanced_context(
        self,
        search_results: List[Dict[str, Any]],
        memory_context: Dict[str, Any],
        personalized_context: Dict[str, Any],
        query: str
    ) -> str:
        """Build enhanced context with memory, personalization, and knowledge graph relationships"""
        context_parts = []
        
        # Add personalization context
        if personalized_context.get("user_preferences"):
            user_prefs = personalized_context["user_preferences"]
            context_parts.append("User Preferences:")
            for pref_key, pref_data in user_prefs.items():
                if isinstance(pref_data, dict) and "value" in pref_data:
                    context_parts.append(f"- {pref_key}: {pref_data['value']}")
            context_parts.append("")
        
        # Add memory context
        if memory_context.get("conversation_summary"):
            context_parts.append(f"Conversation Context: {memory_context['conversation_summary']}")
            context_parts.append("")
        
        if memory_context.get("relevant_memories"):
            context_parts.append("Relevant Previous Discussion:")
            for memory in memory_context["relevant_memories"][:3]:  # Top 3 memories
                context_parts.append(f"- {memory['content']}")
            context_parts.append("")
        
        # Add knowledge graph context if available
        kg_context = await self._build_knowledge_graph_context(search_results, query)
        if kg_context:
            context_parts.append("Knowledge Graph Relationships:")
            context_parts.append(kg_context)
            context_parts.append("")
        
        # Add search results with relationship context
        context_parts.append("Relevant Documents:")
        for i, result in enumerate(search_results, 1):
            metadata = result.get("metadata", {})
            document_name = metadata.get("document_name", "Unknown")
            page_number = metadata.get("page_number", 1)
            
            # Add basic source information
            source_info = f"Source {i} ({document_name}, page {page_number})"
            
            # Add knowledge graph relationship info if available
            kg_info = metadata.get("knowledge_graph", {})
            if kg_info.get("relationship_strength", 0) > 0.1:
                relationship_summary = metadata.get("relationship_summary", "")
                source_info += f" [Relationships: {relationship_summary}]"
            
            context_parts.append(f"{source_info}:\n{result['content']}\n")
        
        return "\n".join(context_parts)
    
    async def _build_knowledge_graph_context(
        self, 
        search_results: List[Dict[str, Any]], 
        query: str
    ) -> str:
        """Build knowledge graph context summary"""
        try:
            # Collect all relationships from search results
            all_relationships = []
            entity_mentions = set()
            
            for result in search_results:
                kg_metadata = result.get("metadata", {}).get("knowledge_graph", {})
                
                # Collect direct relationships
                direct_rels = kg_metadata.get("direct_relationships", [])
                all_relationships.extend(direct_rels)
                
                # Collect entity mentions
                extracted_entities = result.get("metadata", {}).get("extracted_entities", {})
                entity_mentions.update(extracted_entities.get("query_entities", []))
                entity_mentions.update(extracted_entities.get("content_entities", []))
            
            if not all_relationships and not entity_mentions:
                return ""
            
            context_parts = []
            
            # Summarize key relationships
            if all_relationships:
                # Group relationships by type
                rel_by_type = {}
                for rel in all_relationships:
                    rel_type = rel["relationship_type"]
                    if rel_type not in rel_by_type:
                        rel_by_type[rel_type] = []
                    rel_by_type[rel_type].append(rel)
                
                context_parts.append("Key entity relationships found:")
                for rel_type, rels in rel_by_type.items():
                    if len(rels) <= 2:
                        for rel in rels:
                            context_parts.append(
                                f"- {rel['source']} {rel_type} {rel['target']} "
                                f"(confidence: {rel['confidence']:.2f})"
                            )
                    else:
                        context_parts.append(f"- Multiple {rel_type} relationships ({len(rels)} found)")
            
            # Mention key entities
            if entity_mentions:
                key_entities = list(entity_mentions)[:5]  # Limit to top 5
                context_parts.append(f"Key entities: {', '.join(key_entities)}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building knowledge graph context: {e}")
            return ""
    
    async def _generate_response_with_reasoning(
        self,
        query: str,
        context: str,
        use_chain_of_thought: bool,
        citation_mode: bool,
        enable_reasoning: bool,
        personalized_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate response with optional reasoning capabilities"""
        
        # Get user preferences for response customization
        user_prefs = personalized_context.get("user_preferences", {})
        response_style = user_prefs.get("response_style", {}).get("value", "balanced")
        technical_level = user_prefs.get("technical_level", {}).get("value", "intermediate")
        
        # Build personalized prompt
        prompt = await self._build_personalized_prompt(
            query, context, citation_mode, response_style, technical_level
        )
        
        response_data = {}
        
        if use_chain_of_thought:
            response_text, chain_of_thought = await self._generate_chain_of_thought_response(
                prompt, query
            )
            response_data["response"] = response_text
            response_data["chain_of_thought"] = chain_of_thought
        else:
            response_text = await self._generate_standard_response(prompt)
            response_data["response"] = response_text
        
        # Add reasoning results if enabled with selective application
        reasoning_results = []
        if enable_reasoning:
            reasoning_results = await self._apply_selective_reasoning(
                query, context, response_text, personalized_context
            )
            response_data["reasoning_results"] = reasoning_results
        
        # Store reasoning results for uncertainty calculation
        self._last_reasoning_results = reasoning_results
        
        # Calculate uncertainty score
        uncertainty_score = await self._calculate_uncertainty_score(
            response_text, context, query
        )
        response_data["uncertainty_score"] = uncertainty_score
        
        return response_data
    
    async def _build_personalized_prompt(
        self,
        query: str,
        context: str,
        citation_mode: bool,
        response_style: str,
        technical_level: str
    ) -> str:
        """Build personalized prompt based on user preferences"""
        
        # Style instructions
        style_instructions = {
            "concise": "Provide a brief, to-the-point answer.",
            "detailed": "Provide a comprehensive, detailed explanation.",
            "balanced": "Provide a well-balanced answer with appropriate detail."
        }
        
        # Technical level instructions
        technical_instructions = {
            "beginner": "Use simple language and explain technical terms.",
            "intermediate": "Use moderate technical language with some explanations.",
            "advanced": "Use technical language appropriate for experts."
        }
        
        style_instruction = style_instructions.get(response_style, style_instructions["balanced"])
        technical_instruction = technical_instructions.get(technical_level, technical_instructions["intermediate"])
        
        citation_instruction = ""
        if citation_mode:
            citation_instruction = "Include citations in the format [Source X] where X is the source number."
        
        prompt = f"""Based on the following context, please answer the question.

{style_instruction} {technical_instruction} {citation_instruction}

Context:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    async def _generate_standard_response(self, prompt: str) -> str:
        """Generate standard response using LLM"""
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
                return "I apologize, but I'm having trouble generating a response right now."
                
        except Exception as e:
            logger.error(f"Response generation error: {str(e)}")
            return "I apologize, but I'm having trouble connecting to the language model."
    
    async def _generate_chain_of_thought_response(
        self, 
        prompt: str, 
        query: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate response with chain of thought reasoning"""
        cot_prompt = f"""Let me think through this step by step.

{prompt}

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
                    "confidence": 0.8
                }
                
                return final_answer, chain_of_thought
            else:
                logger.error(f"Chain of thought generation error: {response.status_code}")
                return "I apologize, but I'm having trouble with the reasoning process.", None
                
        except Exception as e:
            logger.error(f"Chain of thought generation error: {str(e)}")
            return "I apologize, but I'm having trouble with the reasoning process.", None
    
    async def _apply_selective_reasoning(
        self,
        query: str,
        context: str,
        response: str,
        personalized_context: Dict[str, Any]
    ) -> List[ReasoningResult]:
        """Apply reasoning selectively based on query complexity and user preferences"""
        try:
            # Check user preferences for reasoning
            user_prefs = personalized_context.get("user_preferences", {})
            reasoning_preference = user_prefs.get("reasoning_level", {}).get("value", "adaptive")
            
            # Determine if reasoning should be applied
            should_apply = self._should_apply_reasoning_selective(
                query, response, reasoning_preference
            )
            
            if not should_apply:
                logger.debug("Selective reasoning: skipping based on complexity/preferences")
                return []
            
            # Apply reasoning with appropriate intensity
            reasoning_intensity = self._determine_reasoning_intensity(
                query, reasoning_preference
            )
            
            return await self._apply_reasoning_with_intensity(
                query, context, response, reasoning_intensity
            )
            
        except Exception as e:
            logger.error(f"Error in selective reasoning: {e}")
            return []
    
    def _should_apply_reasoning_selective(
        self, 
        query: str, 
        response: str, 
        reasoning_preference: str
    ) -> bool:
        """Determine if reasoning should be applied based on selective criteria"""
        
        # Always apply if user explicitly wants it
        if reasoning_preference == "always":
            return True
        
        # Never apply if user disabled it
        if reasoning_preference == "never":
            return False
        
        # For adaptive mode, use complexity analysis
        if reasoning_preference == "adaptive":
            # Use reasoning engine's complexity check with adjusted threshold
            base_complexity = self.reasoning_engine.should_apply_reasoning(query, 0.05)
            
            # Additional complexity indicators
            complex_patterns = [
                len(query.split()) > 15,  # Long queries
                "?" in query and len(query.split("?")) > 2,  # Multiple questions
                any(word in response.lower() for word in [
                    "complex", "complicated", "multiple", "various", "several"
                ]),
                len(response.split()) > 100  # Long responses
            ]
            
            additional_complexity = sum(complex_patterns) >= 2
            
            return base_complexity or additional_complexity
        
        # Default to basic complexity check
        return self.reasoning_engine.should_apply_reasoning(query)
    
    def _determine_reasoning_intensity(self, query: str, reasoning_preference: str) -> str:
        """Determine the intensity of reasoning to apply"""
        
        if reasoning_preference == "always":
            return "comprehensive"
        
        # Analyze query for intensity indicators
        high_intensity_indicators = [
            "analyze", "explain in detail", "comprehensive", "thorough",
            "why exactly", "how specifically", "what are all"
        ]
        
        medium_intensity_indicators = [
            "explain", "describe", "compare"
        ]
        
        query_lower = query.lower()
        
        if any(indicator in query_lower for indicator in high_intensity_indicators):
            return "comprehensive"
        elif any(indicator in query_lower for indicator in medium_intensity_indicators):
            return "moderate"
        elif any(word in query_lower for word in ["what", "how", "why"]) and len(query.split()) > 5:
            return "moderate"  # Only moderate for longer questions
        else:
            return "basic"
    
    async def _apply_reasoning_with_intensity(
        self,
        query: str,
        context: str,
        response: str,
        intensity: str
    ) -> List[ReasoningResult]:
        """Apply reasoning with specified intensity level"""
        
        if intensity == "basic":
            # Apply only core reasoning types
            return await self._apply_reasoning(query, context, response)
        
        elif intensity == "moderate":
            # Apply core reasoning plus one specialized agent
            reasoning_results = await self._apply_reasoning(query, context, response)
            
            # Add most relevant specialized agent
            specialized_agents = self._determine_specialized_agents(query, response, context)
            if specialized_agents:
                # Pick the most relevant agent
                primary_agent = specialized_agents[0]
                specialized_result = await self.reasoning_engine.apply_specialized_agents(
                    query, context, [primary_agent]
                )
                reasoning_results.extend(specialized_result)
            
            return reasoning_results
        
        elif intensity == "comprehensive":
            # Apply all relevant reasoning types and agents
            reasoning_results = await self._apply_reasoning(query, context, response)
            
            # Apply all relevant specialized agents
            specialized_agents = self._determine_specialized_agents(query, response, context)
            if specialized_agents:
                specialized_results = await self.reasoning_engine.apply_specialized_agents(
                    query, context, specialized_agents
                )
                reasoning_results.extend(specialized_results)
            
            return reasoning_results
        
        else:
            # Fallback to basic reasoning
            return await self._apply_reasoning(query, context, response)

    async def _apply_reasoning(
        self, 
        query: str, 
        context: str, 
        response: str
    ) -> List[ReasoningResult]:
        """Apply reasoning capabilities using the reasoning engine"""
        reasoning_results = []
        
        try:
            # Check if reasoning should be applied based on query complexity
            if not self.reasoning_engine.should_apply_reasoning(query):
                logger.debug("Query complexity below threshold, skipping reasoning")
                return reasoning_results
            
            # Determine which reasoning types to apply based on query patterns
            reasoning_types = self._determine_reasoning_types(query, response)
            
            if reasoning_types:
                # Apply core reasoning (causal and analogical)
                core_reasoning = await self.reasoning_engine.apply_reasoning(
                    query, context, reasoning_types
                )
                reasoning_results.extend(core_reasoning)
            
            # Apply specialized agents based on content analysis
            specialized_agents = self._determine_specialized_agents(query, response, context)
            
            if specialized_agents:
                specialized_results = await self.reasoning_engine.apply_specialized_agents(
                    query, context, specialized_agents
                )
                reasoning_results.extend(specialized_results)
            
            # Log reasoning application for debugging
            logger.info(f"Applied reasoning: {len(reasoning_results)} results generated")
            for result in reasoning_results:
                logger.debug(f"Reasoning type: {result.reasoning_type}, confidence: {result.confidence}")
            
        except Exception as e:
            logger.error(f"Error applying reasoning: {e}")
            # Fallback to basic reasoning indicators
            reasoning_results = await self._apply_basic_reasoning_fallback(query, context, response)
        
        return reasoning_results
    
    def _determine_reasoning_types(self, query: str, response: str) -> List[str]:
        """Determine which reasoning types to apply based on query and response patterns"""
        reasoning_types = []
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Causal reasoning indicators
        causal_indicators = [
            "why", "because", "cause", "reason", "due to", "leads to", 
            "results in", "consequence", "effect", "impact", "influence"
        ]
        if any(indicator in query_lower for indicator in causal_indicators):
            reasoning_types.append("causal")
        
        # Analogical reasoning indicators
        analogical_indicators = [
            "like", "similar", "compare", "analogy", "resembles", "parallel",
            "equivalent", "corresponds", "matches", "relates to"
        ]
        if any(indicator in query_lower for indicator in analogical_indicators):
            reasoning_types.append("analogical")
        
        return reasoning_types
    
    def _determine_specialized_agents(self, query: str, response: str, context: str) -> List[str]:
        """Determine which specialized agents to apply"""
        agents = []
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Fact-checking indicators
        fact_check_indicators = [
            "fact", "proven", "research shows", "studies indicate", "evidence",
            "verified", "confirmed", "documented", "established", "true", "false"
        ]
        if (any(indicator in response_lower for indicator in fact_check_indicators) or
            any(word in query_lower for word in ["verify", "check", "confirm", "validate"])):
            agents.append("fact_checking")
        
        # Summarization indicators
        summary_indicators = [
            "summarize", "summary", "overview", "brief", "main points",
            "key points", "outline", "digest", "abstract"
        ]
        if (any(indicator in query_lower for indicator in summary_indicators) or
            len(context) > 2000):  # Long context benefits from summarization
            agents.append("summarization")
        
        # Research indicators
        research_indicators = [
            "research", "investigate", "explore", "analyze", "examine",
            "study", "comprehensive", "detailed analysis", "in-depth"
        ]
        if any(indicator in query_lower for indicator in research_indicators):
            agents.append("research")
        
        return agents
    
    async def _apply_basic_reasoning_fallback(
        self, 
        query: str, 
        context: str, 
        response: str
    ) -> List[ReasoningResult]:
        """Fallback to basic reasoning when full reasoning engine fails"""
        reasoning_results = []
        
        try:
            # Basic causal reasoning check
            if any(word in query.lower() for word in ["why", "because", "cause", "reason"]):
                reasoning_results.append(ReasoningResult(
                    reasoning_type="causal",
                    confidence=0.6,
                    explanation="Basic causal reasoning pattern detected in query",
                    supporting_evidence=[context[:100] + "..."],
                    metadata={"fallback": True, "pattern": "causal_question"}
                ))
            
            # Basic analogical reasoning check
            if any(word in query.lower() for word in ["like", "similar", "compare"]):
                reasoning_results.append(ReasoningResult(
                    reasoning_type="analogical",
                    confidence=0.5,
                    explanation="Basic analogical reasoning pattern detected",
                    supporting_evidence=[response[:100] + "..."],
                    metadata={"fallback": True, "pattern": "comparison_request"}
                ))
            
        except Exception as e:
            logger.error(f"Error in basic reasoning fallback: {e}")
        
        return reasoning_results
    
    async def _enhance_response_with_reasoning(
        self,
        response: str,
        reasoning_results: List[ReasoningResult]
    ) -> str:
        """Enhance the response with reasoning insights"""
        
        if not reasoning_results:
            return response
        
        try:
            # Group reasoning results by type
            reasoning_by_type = {}
            for result in reasoning_results:
                if result.reasoning_type not in reasoning_by_type:
                    reasoning_by_type[result.reasoning_type] = []
                reasoning_by_type[result.reasoning_type].append(result)
            
            # Build reasoning insights
            reasoning_insights = []
            
            # Add causal reasoning insights
            if "causal" in reasoning_by_type:
                causal_results = reasoning_by_type["causal"]
                high_confidence_causal = [r for r in causal_results if r.confidence > 0.7]
                if high_confidence_causal:
                    causal_relations = []
                    for result in high_confidence_causal:
                        relations = result.metadata.get("causal_relations", [])
                        for rel in relations[:2]:  # Limit to top 2 relations
                            causal_relations.append(f"{rel['cause']} → {rel['effect']}")
                    
                    if causal_relations:
                        reasoning_insights.append(
                            f"**Causal Analysis:** {'; '.join(causal_relations)}"
                        )
            
            # Add analogical reasoning insights
            if "analogical" in reasoning_by_type:
                analogical_results = reasoning_by_type["analogical"]
                high_confidence_analogical = [r for r in analogical_results if r.confidence > 0.6]
                if high_confidence_analogical:
                    analogies = []
                    for result in high_confidence_analogical:
                        analogy_data = result.metadata.get("analogies", [])
                        for analogy in analogy_data[:1]:  # Limit to top analogy
                            analogies.append(
                                f"{analogy['source_domain']} ↔ {analogy['target_domain']}"
                            )
                    
                    if analogies:
                        reasoning_insights.append(
                            f"**Analogical Insights:** {'; '.join(analogies)}"
                        )
            
            # Add fact-checking insights
            if "fact_checking" in reasoning_by_type:
                fact_check_results = reasoning_by_type["fact_checking"]
                for result in fact_check_results:
                    fact_checks = result.metadata.get("fact_check_results", [])
                    verified_count = len([fc for fc in fact_checks if fc.get("status") == "VERIFIED"])
                    total_count = len(fact_checks)
                    
                    if total_count > 0:
                        reasoning_insights.append(
                            f"**Fact Verification:** {verified_count}/{total_count} claims verified"
                        )
            
            # Add summarization insights
            if "summarization" in reasoning_by_type:
                summary_results = reasoning_by_type["summarization"]
                for result in summary_results:
                    key_insights = result.metadata.get("key_insights", [])
                    if key_insights:
                        reasoning_insights.append(
                            f"**Key Insights:** {'; '.join(key_insights[:2])}"
                        )
            
            # Append reasoning insights to response if any were generated
            if reasoning_insights:
                enhanced_response = response + "\n\n---\n\n" + "\n\n".join(reasoning_insights)
                return enhanced_response
            
            return response
            
        except Exception as e:
            logger.error(f"Error enhancing response with reasoning: {e}")
            return response
    
    async def _calculate_uncertainty_score(
        self, 
        response: str, 
        context: str, 
        query: str
    ) -> UncertaintyScore:
        """Calculate uncertainty score for the response using the reasoning engine"""
        try:
            # Prepare sources from context for uncertainty quantification
            sources = []
            if context:
                # Split context into chunks and treat as sources
                context_chunks = context.split('\n\n')  # Simple splitting
                for i, chunk in enumerate(context_chunks):
                    if chunk.strip():
                        sources.append({
                            "content": chunk.strip(),
                            "relevance": 0.8,  # Default relevance
                            "document_id": f"context_chunk_{i}"
                        })
            
            # Get reasoning results if available (from previous processing)
            reasoning_results = getattr(self, '_last_reasoning_results', [])
            
            # Use the reasoning engine's uncertainty quantifier
            uncertainty_score = await self.reasoning_engine.quantify_uncertainty(
                response=response,
                sources=sources,
                reasoning_results=reasoning_results
            )
            
            return uncertainty_score
            
        except Exception as e:
            logger.error(f"Error calculating uncertainty score: {e}")
            # Fallback to simple calculation
            return UncertaintyScore(
                confidence=0.5,
                uncertainty_factors=["Error in uncertainty calculation"],
                reliability_score=0.5,
                source_quality=0.5
            )
    
    async def _learn_from_interaction(
        self,
        user_id: str,
        query: str,
        response_data: Dict[str, Any],
        search_results: List[Dict[str, Any]]
    ) -> None:
        """Learn from user interaction to improve personalization"""
        try:
            interaction_data = {
                "query": query,
                "response_length": len(response_data["response"]),
                "sources_count": len(search_results),
                "reasoning_applied": len(response_data.get("reasoning_results", [])) > 0,
                "uncertainty_score": response_data.get("uncertainty_score", {}).get("confidence", 0.5),
                "timestamp": datetime.now().isoformat()
            }
            
            # Extract domain from query (simplified)
            domains = ["machine_learning", "python", "data_science", "web_development", "ai"]
            query_lower = query.lower()
            for domain in domains:
                if domain.replace("_", " ") in query_lower or domain in query_lower:
                    interaction_data["query_domain"] = domain
                    break
            
            # Learn preferences from interaction
            learned_preferences = await self.user_memory.learn_preference_from_interaction(
                user_id, interaction_data
            )
            
            if learned_preferences:
                logger.info(f"Learned preferences for user {user_id}: {learned_preferences}")
            
        except Exception as e:
            logger.error(f"Error learning from interaction: {e}")
    
    async def _save_messages_to_db(
        self,
        db: Session,
        conversation_id: str,
        query: str,
        response_data: Dict[str, Any],
        search_results: List[Dict[str, Any]]
    ) -> None:
        """Save messages to database"""
        try:
            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                role="user",
                content=query
            )
            db.add(user_message)
            
            # Save assistant message
            sources_data = [self._format_source_for_db(result) for result in search_results]
            
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=response_data["response"],
                sources=json.dumps(sources_data),
                message_metadata=json.dumps({
                    "chain_of_thought": response_data.get("chain_of_thought"),
                    "reasoning_results": [r.dict() if hasattr(r, 'dict') else r for r in response_data.get("reasoning_results", [])],
                    "uncertainty_score": response_data.get("uncertainty_score", {}).dict() if hasattr(response_data.get("uncertainty_score", {}), 'dict') else response_data.get("uncertainty_score", {}),
                    "search_results_count": len(search_results),
                    "enhanced_features_used": True
                })
            )
            db.add(assistant_message)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error saving messages to database: {e}")
            db.rollback()
    
    def _format_source_for_db(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format search result for database storage"""
        metadata = result.get("metadata", {})
        return {
            "document": metadata.get("document_name", "Unknown"),
            "page": metadata.get("page_number", 1),
            "relevance": result.get("relevance", 0.0),
            "snippet": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
        }
    
    def _collect_knowledge_graph_stats(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect knowledge graph statistics from search results"""
        stats = {
            "total_entities": 0,
            "relationships_found": 0,
            "direct_relationships": 0,
            "indirect_relationships": 0,
            "avg_relationship_confidence": 0.0,
            "top_relationship_types": []
        }
        
        try:
            all_relationships = []
            relationship_types = []
            
            for result in search_results:
                kg_metadata = result.get("metadata", {}).get("knowledge_graph", {})
                extracted_entities = result.get("metadata", {}).get("extracted_entities", {})
                
                # Count entities
                query_entities = len(extracted_entities.get("query_entities", []))
                content_entities = len(extracted_entities.get("content_entities", []))
                stats["total_entities"] += query_entities + content_entities
                
                # Count relationships
                direct_rels = kg_metadata.get("direct_relationships", [])
                indirect_rels = kg_metadata.get("indirect_relationships", [])
                
                stats["direct_relationships"] += len(direct_rels)
                stats["indirect_relationships"] += len(indirect_rels)
                
                all_relationships.extend(direct_rels + indirect_rels)
                relationship_types.extend([rel["relationship_type"] for rel in direct_rels + indirect_rels])
            
            stats["relationships_found"] = len(all_relationships)
            
            # Calculate average confidence
            if all_relationships:
                total_confidence = sum(rel["confidence"] for rel in all_relationships)
                stats["avg_relationship_confidence"] = total_confidence / len(all_relationships)
            
            # Get top relationship types
            if relationship_types:
                from collections import Counter
                type_counts = Counter(relationship_types)
                stats["top_relationship_types"] = [
                    {"type": rel_type, "count": count} 
                    for rel_type, count in type_counts.most_common(3)
                ]
            
        except Exception as e:
            logger.error(f"Error collecting knowledge graph stats: {e}")
        
        return stats
    
    def _format_sources(self, search_results: List[Dict[str, Any]]) -> List[Source]:
        """Format search results as sources with knowledge graph information"""
        sources = []
        
        for result in search_results:
            metadata = result.get("metadata", {})
            
            # Create base source
            relevance = result.get("combined_relevance", result.get("relevance", 0.0))
            snippet = result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
            
            # Add knowledge graph information to snippet if available
            kg_metadata = metadata.get("knowledge_graph", {})
            if kg_metadata.get("relationship_strength", 0) > 0.1:
                relationship_summary = metadata.get("relationship_summary", "")
                snippet += f"\n[Knowledge Graph: {relationship_summary}]"
            
            source = Source(
                document=metadata.get("document_name", "Unknown"),
                page=metadata.get("page_number", 1),
                relevance=relevance,
                snippet=snippet
            )
            sources.append(source)
        
        return sources
        
        return sources
    
    async def _build_relationship_context(
        self, 
        query_entities: List[str], 
        content_entities: List[str]
    ) -> Dict[str, Any]:
        """Build relationship context between query and content entities"""
        relationship_context = {
            "direct_relationships": [],
            "indirect_relationships": [],
            "entity_connections": {},
            "relationship_strength": 0.0
        }
        
        try:
            # Find direct relationships between query and content entities
            for query_entity in query_entities:
                for content_entity in content_entities:
                    # Check if entities are related
                    related_entities = await self.knowledge_graph.find_related_entities(
                        query_entity, max_depth=2
                    )
                    
                    for related in related_entities:
                        if related["entity"].lower() == content_entity.lower():
                            relationship_info = {
                                "source": query_entity,
                                "target": content_entity,
                                "relationship_type": related["relationship"],
                                "confidence": related["confidence"],
                                "depth": related["depth"],
                                "context": related.get("context", "")
                            }
                            
                            if related["depth"] == 1:
                                relationship_context["direct_relationships"].append(relationship_info)
                            else:
                                relationship_context["indirect_relationships"].append(relationship_info)
            
            # Build entity connection map
            for query_entity in query_entities:
                connections = await self.knowledge_graph.find_related_entities(query_entity, max_depth=1)
                if connections:
                    relationship_context["entity_connections"][query_entity] = [
                        {
                            "entity": conn["entity"],
                            "relationship": conn["relationship"],
                            "confidence": conn["confidence"]
                        }
                        for conn in connections[:5]  # Limit to top 5 connections
                    ]
            
            # Calculate overall relationship strength
            direct_strength = sum(rel["confidence"] for rel in relationship_context["direct_relationships"])
            indirect_strength = sum(rel["confidence"] * 0.5 for rel in relationship_context["indirect_relationships"])
            relationship_context["relationship_strength"] = min(1.0, direct_strength + indirect_strength)
            
        except Exception as e:
            logger.error(f"Error building relationship context: {e}")
        
        return relationship_context
    
    def _calculate_knowledge_graph_boost(self, relationship_context: Dict[str, Any]) -> float:
        """Calculate relevance boost based on knowledge graph relationships"""
        base_boost = 0.0
        
        # Boost for direct relationships
        direct_count = len(relationship_context.get("direct_relationships", []))
        if direct_count > 0:
            base_boost += min(0.3, direct_count * 0.1)
        
        # Smaller boost for indirect relationships
        indirect_count = len(relationship_context.get("indirect_relationships", []))
        if indirect_count > 0:
            base_boost += min(0.15, indirect_count * 0.05)
        
        # Boost based on relationship strength
        strength_boost = relationship_context.get("relationship_strength", 0.0) * 0.2
        base_boost += strength_boost
        
        return min(0.4, base_boost)  # Cap the boost at 0.4
    
    def _summarize_relationships(self, relationship_context: Dict[str, Any]) -> str:
        """Create a human-readable summary of relationships"""
        summary_parts = []
        
        direct_rels = relationship_context.get("direct_relationships", [])
        if direct_rels:
            summary_parts.append(f"Direct relationships: {len(direct_rels)}")
            for rel in direct_rels[:2]:  # Show top 2
                summary_parts.append(
                    f"  • {rel['source']} {rel['relationship_type']} {rel['target']} "
                    f"(confidence: {rel['confidence']:.2f})"
                )
        
        indirect_rels = relationship_context.get("indirect_relationships", [])
        if indirect_rels:
            summary_parts.append(f"Indirect relationships: {len(indirect_rels)}")
        
        entity_connections = relationship_context.get("entity_connections", {})
        if entity_connections:
            summary_parts.append(f"Connected entities: {len(entity_connections)}")
        
        return "; ".join(summary_parts) if summary_parts else "No significant relationships found"
    
    async def _rerank_with_knowledge_graph(
        self, 
        results: List[Dict[str, Any]], 
        query_entities: List[str]
    ) -> List[Dict[str, Any]]:
        """Re-rank search results considering knowledge graph relationships"""
        try:
            # Calculate combined score for each result
            for result in results:
                base_relevance = result.get("relevance", 0.0)
                kg_metadata = result.get("metadata", {}).get("knowledge_graph", {})
                
                # Knowledge graph factors
                relationship_strength = kg_metadata.get("relationship_strength", 0.0)
                direct_rel_count = len(kg_metadata.get("direct_relationships", []))
                indirect_rel_count = len(kg_metadata.get("indirect_relationships", []))
                
                # Calculate knowledge graph score
                kg_score = (
                    relationship_strength * 0.4 +
                    min(1.0, direct_rel_count * 0.3) +
                    min(0.5, indirect_rel_count * 0.1)
                )
                
                # Combine scores (70% base relevance, 30% knowledge graph)
                combined_score = (base_relevance * 0.7) + (kg_score * 0.3)
                result["combined_relevance"] = combined_score
                result["kg_score"] = kg_score
            
            # Sort by combined relevance
            results.sort(key=lambda x: x.get("combined_relevance", x.get("relevance", 0)), reverse=True)
            
        except Exception as e:
            logger.error(f"Error re-ranking with knowledge graph: {e}")
        
        return results
    
    async def _extract_entities_from_text(self, text: str) -> List[str]:
        """Extract entities from text using knowledge graph service"""
        try:
            entities = await self.knowledge_graph.entity_extractor.extract_entities(text)
            return [entity["text"] for entity in entities if entity["confidence"] > 0.5]
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            # Fallback to simple extraction
            import re
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            common_words = {"The", "This", "That", "And", "But", "For", "With", "From", "To", "In", "On", "At"}
            return [word for word in words if word not in common_words][:5]
    
    async def _add_citations_to_response(
        self,
        response: str,
        search_results: List[Dict[str, Any]],
        user_id: str,
        personalized_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add citations to the response based on user preferences and search results"""
        try:
            # Get user citation preferences
            user_prefs = personalized_context.get("user_preferences", {})
            citation_format = user_prefs.get("citation_preference", {}).get("value", "inline")
            
            # Map citation preference to format and style
            format_mapping = {
                "inline": (CitationFormat.APA, "inline"),
                "footnote": (CitationFormat.APA, "footnote"),
                "bibliography": (CitationFormat.APA, "bibliography"),
                "apa": (CitationFormat.APA, "inline"),
                "mla": (CitationFormat.MLA, "inline"),
                "chicago": (CitationFormat.CHICAGO, "inline"),
                "ieee": (CitationFormat.IEEE, "inline"),
                "harvard": (CitationFormat.HARVARD, "inline")
            }
            
            citation_format_enum, citation_style = format_mapping.get(
                citation_format, (CitationFormat.APA, "inline")
            )
            
            # Convert search results to citation sources
            sources = []
            for i, result in enumerate(search_results, 1):
                source = {
                    "document": result.get("document", f"Document {i}"),
                    "page": result.get("page", 1),
                    "relevance": result.get("score", 0.0),
                    "snippet": result.get("content", "")[:200] + "...",
                    "metadata": self._extract_citation_metadata(result)
                }
                sources.append(source)
            
            # Generate citations using the citation integrator
            citation_result = self.citation_integrator.add_citations_to_response(
                response,
                sources,
                citation_format_enum,
                citation_style
            )
            
            return citation_result
            
        except Exception as e:
            logger.error(f"Error adding citations to response: {e}")
            return {
                "response": response,
                "citations": [],
                "bibliography": "",
                "citation_format": "apa",
                "citation_style": "inline",
                "error": str(e)
            }
    
    def _extract_citation_metadata(self, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract citation metadata from search result"""
        metadata = search_result.get("metadata", {})
        
        # Extract document information
        document_name = search_result.get("document", "Unknown Document")
        
        # Try to extract metadata from various sources
        citation_metadata = {
            "title": document_name,
            "document_type": self._determine_document_type_from_name(document_name)
        }
        
        # Extract authors if available
        if "authors" in metadata:
            citation_metadata["authors"] = metadata["authors"]
        elif "author" in metadata:
            citation_metadata["authors"] = [metadata["author"]]
        
        # Extract publication information
        if "publication_date" in metadata:
            citation_metadata["publication_date"] = metadata["publication_date"]
        elif "date" in metadata:
            citation_metadata["publication_date"] = metadata["date"]
        
        # Extract journal/publisher information
        for field in ["journal", "publisher", "volume", "issue", "pages", "doi", "isbn", "url"]:
            if field in metadata:
                citation_metadata[field] = metadata[field]
        
        return citation_metadata
    
    def _determine_document_type_from_name(self, document_name: str) -> str:
        """Determine document type from document name"""
        name_lower = document_name.lower()
        
        if any(keyword in name_lower for keyword in ["journal", "article"]):
            return "journal_article"
        elif any(keyword in name_lower for keyword in ["book", "manual", "guide"]):
            return "book"
        elif any(keyword in name_lower for keyword in ["thesis", "dissertation"]):
            return "thesis"
        elif any(keyword in name_lower for keyword in ["conference", "proceedings"]):
            return "conference_paper"
        elif any(keyword in name_lower for keyword in ["report", "white paper"]):
            return "report"
        elif name_lower.endswith(".pdf"):
            return "pdf"
        else:
            return "unknown"


# Global instance
enhanced_rag_service = EnhancedRAGService()