"""
Vector store service using ChromaDB
"""
import chromadb
from chromadb.config import Settings
import numpy as np
import logging
from typing import List, Dict, Any, Optional
import requests
import json

from core.config import settings
from core.database import get_db, DocumentChunk, DocumentChunkEnhanced

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.client = None
        self.collection = None
        self.ollama_url = settings.OLLAMA_URL
        self.embedding_model = settings.EMBEDDING_MODEL
    
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False)
            )
            
            self.collection = self.client.get_or_create_collection(
                name="ai_scholar_documents",
                metadata={"description": "AI Scholar document embeddings"}
            )
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Vector store initialization error: {str(e)}")
            raise e
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                logger.error(f"Embedding generation failed: {response.status_code}")
                # Fallback to random embedding for development
                return np.random.rand(384).tolist()
                
        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            # Fallback to random embedding for development
            return np.random.rand(384).tolist()
    
    async def add_document(self, document_data: Dict[str, Any]):
        """Add document chunks to vector store with hierarchical support"""
        try:
            db = next(get_db())
            
            # First try to get enhanced chunks
            enhanced_chunks = db.query(DocumentChunkEnhanced).filter(
                DocumentChunkEnhanced.document_id == document_data["id"]
            ).all()
            
            # If no enhanced chunks, fall back to legacy chunks
            if not enhanced_chunks:
                legacy_chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document_data["id"]
                ).all()
                
                if not legacy_chunks:
                    logger.warning(f"No chunks found for document {document_data['id']}")
                    return
                
                # Process legacy chunks
                await self._add_legacy_chunks(document_data, legacy_chunks)
            else:
                # Process enhanced hierarchical chunks
                await self._add_hierarchical_chunks(document_data, enhanced_chunks)
            
        except Exception as e:
            logger.error(f"Error adding document to vector store: {str(e)}")
            raise e
        finally:
            if 'db' in locals():
                db.close()
    
    async def _add_legacy_chunks(self, document_data: Dict[str, Any], chunks: List[DocumentChunk]):
        """Add legacy chunks to vector store"""
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            # Generate embedding
            embedding = await self.generate_embedding(chunk.content)
            
            ids.append(f"{document_data['id']}_{chunk.chunk_index}")
            embeddings.append(embedding)
            documents.append(chunk.content)
            metadatas.append({
                "document_id": document_data["id"],
                "document_name": document_data["name"],
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number or 1,
                "content_length": len(chunk.content),
                "chunk_type": "legacy"
            })
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(chunks)} legacy chunks to vector store for document {document_data['id']}")
    
    async def _add_hierarchical_chunks(self, document_data: Dict[str, Any], chunks: List[DocumentChunkEnhanced]):
        """Add hierarchical chunks to vector store"""
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            # Generate embedding
            embedding = await self.generate_embedding(chunk.content)
            
            # Create unique ID that includes level information
            chunk_id = f"{document_data['id']}_L{chunk.chunk_level}_{chunk.chunk_index}"
            
            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk.content)
            
            # Enhanced metadata for hierarchical chunks
            metadata = {
                "document_id": document_data["id"],
                "document_name": document_data["name"],
                "chunk_index": chunk.chunk_index,
                "chunk_level": chunk.chunk_level,
                "parent_chunk_id": chunk.parent_chunk_id,
                "content_length": len(chunk.content),
                "chunk_type": "hierarchical",
                "has_overlap": chunk.overlap_start is not None or chunk.overlap_end is not None,
                "sentence_count": len(json.loads(chunk.sentence_boundaries)) if chunk.sentence_boundaries else 0
            }
            
            # Add chunk-specific metadata if available
            if chunk.chunk_metadata:
                if isinstance(chunk.chunk_metadata, dict):
                    metadata.update(chunk.chunk_metadata)
                elif isinstance(chunk.chunk_metadata, str):
                    try:
                        chunk_meta = json.loads(chunk.chunk_metadata)
                        metadata.update(chunk_meta)
                    except json.JSONDecodeError:
                        pass
            
            metadatas.append(metadata)
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(chunks)} hierarchical chunks to vector store for document {document_data['id']}")
    
    async def semantic_search(
        self, 
        query: str, 
        user_id: str, 
        limit: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Prepare where clause for user's documents
            where_clause = {}
            if filter_metadata:
                where_clause.update(filter_metadata)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )
            
            # Format results
            search_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    search_results.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "relevance": 1 - results["distances"][0][i]  # Convert distance to relevance
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            return []
    
    async def delete_document(self, document_id: str):
        """Delete document from vector store"""
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks from vector store for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {str(e)}")
            raise e
    
    async def get_similar_chunks(
        self, 
        chunk_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar chunks to a given chunk"""
        try:
            # Get the chunk
            chunk_result = self.collection.get(ids=[chunk_id])
            
            if not chunk_result["documents"]:
                return []
            
            chunk_content = chunk_result["documents"][0]
            
            # Find similar chunks
            return await self.semantic_search(chunk_content, "", limit)
            
        except Exception as e:
            logger.error(f"Error finding similar chunks: {str(e)}")
            return []
    
    async def hierarchical_search(
        self, 
        query: str, 
        user_id: str, 
        limit: int = 10,
        preferred_level: Optional[int] = None,
        include_context: bool = True
    ) -> List[Dict[str, Any]]:
        """Perform hierarchical semantic search with context awareness"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Prepare where clause
            where_clause = {"chunk_type": "hierarchical"}
            if preferred_level is not None:
                where_clause["chunk_level"] = preferred_level
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit * 2,  # Get more results to filter and rank
                where=where_clause
            )
            
            # Format and enhance results with hierarchical context
            search_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    result = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "relevance": 1 - results["distances"][0][i]
                    }
                    
                    # Add hierarchical context if requested
                    if include_context:
                        result["hierarchical_context"] = await self._get_chunk_context(
                            results["ids"][0][i], 
                            results["metadatas"][0][i]
                        )
                    
                    search_results.append(result)
            
            # Sort by relevance and hierarchical importance
            search_results = self._rank_hierarchical_results(search_results)
            
            return search_results[:limit]
            
        except Exception as e:
            logger.error(f"Hierarchical search error: {str(e)}")
            return []
    
    async def _get_chunk_context(self, chunk_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get hierarchical context for a chunk"""
        context = {
            "level": metadata.get("chunk_level", 0),
            "parent_available": metadata.get("parent_chunk_id") is not None,
            "has_overlap": metadata.get("has_overlap", False),
            "related_chunks": []
        }
        
        try:
            # Get parent chunk if available
            if metadata.get("parent_chunk_id"):
                parent_results = self.collection.get(
                    where={
                        "document_id": metadata["document_id"],
                        "chunk_type": "hierarchical",
                        "chunk_level": metadata.get("chunk_level", 0) + 1
                    }
                )
                
                if parent_results["ids"]:
                    context["parent_chunk"] = {
                        "id": parent_results["ids"][0],
                        "content_preview": parent_results["documents"][0][:200] + "..." if len(parent_results["documents"][0]) > 200 else parent_results["documents"][0]
                    }
            
            # Get sibling chunks (same level, same document)
            sibling_results = self.collection.get(
                where={
                    "document_id": metadata["document_id"],
                    "chunk_type": "hierarchical",
                    "chunk_level": metadata.get("chunk_level", 0)
                }
            )
            
            if sibling_results["ids"]:
                # Filter out the current chunk and limit siblings
                siblings = [
                    {"id": sid, "content_preview": doc[:100] + "..." if len(doc) > 100 else doc}
                    for sid, doc in zip(sibling_results["ids"], sibling_results["documents"])
                    if sid != chunk_id
                ][:3]  # Limit to 3 siblings
                context["related_chunks"] = siblings
                
        except Exception as e:
            logger.error(f"Error getting chunk context: {str(e)}")
        
        return context
    
    def _rank_hierarchical_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank results considering hierarchical factors"""
        def hierarchical_score(result):
            base_relevance = result["relevance"]
            metadata = result["metadata"]
            
            # Boost score based on chunk level (lower levels often more specific)
            level_boost = 1.0 - (metadata.get("chunk_level", 0) * 0.1)
            
            # Boost score if chunk has overlap (indicates important boundaries)
            overlap_boost = 1.1 if metadata.get("has_overlap", False) else 1.0
            
            # Boost score based on content length (moderate length preferred)
            content_length = metadata.get("content_length", 0)
            length_boost = 1.0
            if 200 <= content_length <= 1000:
                length_boost = 1.05
            elif content_length > 1000:
                length_boost = 0.95
            
            return base_relevance * level_boost * overlap_boost * length_boost
        
        # Sort by hierarchical score
        results.sort(key=hierarchical_score, reverse=True)
        return results
    
    async def get_chunk_hierarchy_info(self, chunk_id: str) -> Dict[str, Any]:
        """Get detailed hierarchy information for a specific chunk"""
        try:
            # Get the chunk
            chunk_result = self.collection.get(ids=[chunk_id])
            
            if not chunk_result["documents"]:
                return {}
            
            metadata = chunk_result["metadatas"][0]
            
            hierarchy_info = {
                "chunk_id": chunk_id,
                "level": metadata.get("chunk_level", 0),
                "document_id": metadata["document_id"],
                "parent_chunk_id": metadata.get("parent_chunk_id"),
                "content_length": metadata.get("content_length", 0),
                "has_overlap": metadata.get("has_overlap", False),
                "sentence_count": metadata.get("sentence_count", 0)
            }
            
            # Get all chunks from the same document to build hierarchy
            doc_chunks = self.collection.get(
                where={
                    "document_id": metadata["document_id"],
                    "chunk_type": "hierarchical"
                }
            )
            
            if doc_chunks["ids"]:
                # Group by level
                levels = {}
                for i, (cid, meta) in enumerate(zip(doc_chunks["ids"], doc_chunks["metadatas"])):
                    level = meta.get("chunk_level", 0)
                    if level not in levels:
                        levels[level] = []
                    levels[level].append({
                        "id": cid,
                        "chunk_index": meta.get("chunk_index", 0),
                        "is_current": cid == chunk_id
                    })
                
                hierarchy_info["document_hierarchy"] = levels
            
            return hierarchy_info
            
        except Exception as e:
            logger.error(f"Error getting chunk hierarchy info: {str(e)}")
            return {}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics with hierarchical information"""
        try:
            count = self.collection.count()
            
            # Get hierarchical chunk statistics
            hierarchical_results = self.collection.get(
                where={"chunk_type": "hierarchical"}
            )
            
            legacy_results = self.collection.get(
                where={"chunk_type": "legacy"}
            )
            
            hierarchical_count = len(hierarchical_results["ids"]) if hierarchical_results["ids"] else 0
            legacy_count = len(legacy_results["ids"]) if legacy_results["ids"] else 0
            
            # Analyze hierarchical levels
            level_distribution = {}
            if hierarchical_results["metadatas"]:
                for metadata in hierarchical_results["metadatas"]:
                    level = metadata.get("chunk_level", 0)
                    level_distribution[level] = level_distribution.get(level, 0) + 1
            
            return {
                "total_chunks": count,
                "hierarchical_chunks": hierarchical_count,
                "legacy_chunks": legacy_count,
                "level_distribution": level_distribution,
                "collection_name": self.collection.name,
                "embedding_model": self.embedding_model
            }
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            return {"total_chunks": 0}