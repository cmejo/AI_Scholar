"""
Vector Store Service for AI Scholar Scientific RAG
Handles document embeddings and semantic search using ChromaDB
"""

import chromadb
from sentence_transformers import SentenceTransformer
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import numpy as np

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Service for managing document embeddings and semantic search"""
    
    def __init__(self, chroma_host: str = "chromadb", chroma_port: int = 8000):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.collection_name = "scientific_papers"
        
        # Embedding model configuration
        self.embedding_model_name = "all-MiniLM-L6-v2"  # Good balance of speed and quality
        # Alternative models:
        # "all-mpnet-base-v2" - Higher quality, slower
        # "multi-qa-MiniLM-L6-cos-v1" - Optimized for Q&A
        
    async def initialize(self):
        """Initialize ChromaDB client and embedding model"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            
            # Test connection
            self.client.heartbeat()
            logger.info(f"Connected to ChromaDB at {self.chroma_host}:{self.chroma_port}")
            
            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "description": "Scientific papers and research documents",
                    "embedding_model": self.embedding_model_name,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Vector store initialized with collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def add_document_chunks(
        self, 
        document_id: str, 
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add document chunks to the vector store"""
        
        if not self.collection or not self.embedding_model:
            raise RuntimeError("Vector store not initialized")
        
        try:
            # Prepare data for ChromaDB
            texts = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_text = chunk.get('text', '')
                
                if not chunk_text.strip():
                    continue  # Skip empty chunks
                
                texts.append(chunk_text)
                ids.append(chunk_id)
                
                # Prepare metadata
                metadata = {
                    'document_id': document_id,
                    'chunk_index': i,
                    'section': chunk.get('section', 'unknown'),
                    'chunk_type': chunk.get('chunk_type', 'standard'),
                    'word_count': len(chunk_text.split()),
                    'character_count': len(chunk_text),
                    'created_at': datetime.now().isoformat()
                }
                
                # Add document metadata if available
                doc_metadata = chunk.get('document_metadata', {})
                if doc_metadata:
                    metadata.update({
                        'title': doc_metadata.get('title', ''),
                        'authors': str(doc_metadata.get('authors', [])),
                        'journal': doc_metadata.get('journal', ''),
                        'publication_year': doc_metadata.get('publication_year'),
                        'doi': doc_metadata.get('doi', ''),
                        'keywords': str(doc_metadata.get('keywords', []))
                    })
                
                metadatas.append(metadata)
            
            if not texts:
                logger.warning(f"No valid chunks found for document {document_id}")
                return {'chunks_added': 0, 'document_id': document_id}
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} chunks")
            embeddings = self.embedding_model.encode(
                texts, 
                convert_to_tensor=False,
                show_progress_bar=True
            ).tolist()
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(texts)} chunks for document {document_id}")
            
            return {
                'chunks_added': len(texts),
                'document_id': document_id,
                'embedding_model': self.embedding_model_name,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error adding document chunks: {e}")
            raise
    
    async def semantic_search(
        self, 
        query: str, 
        n_results: int = 10,
        filters: Optional[Dict] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across the document corpus"""
        
        if not self.collection or not self.embedding_model:
            raise RuntimeError("Vector store not initialized")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Prepare query parameters
            query_params = {
                'query_embeddings': query_embedding,
                'n_results': n_results,
                'include': ['documents', 'distances']
            }
            
            if include_metadata:
                query_params['include'].append('metadatas')
            
            # Add filters if provided
            if filters:
                where_clause = self._build_where_clause(filters)
                if where_clause:
                    query_params['where'] = where_clause
            
            # Perform search
            results = self.collection.query(**query_params)
            
            # Format results
            formatted_results = self._format_search_results(results)
            
            logger.info(f"Semantic search returned {len(formatted_results)} results for query: {query[:100]}...")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            raise
    
    def _build_where_clause(self, filters: Dict) -> Optional[Dict]:
        """Build ChromaDB where clause from filters"""
        where_conditions = []
        
        # Filter by publication year
        if 'year_from' in filters or 'year_to' in filters:
            year_condition = {}
            if 'year_from' in filters:
                year_condition['$gte'] = filters['year_from']
            if 'year_to' in filters:
                year_condition['$lte'] = filters['year_to']
            if year_condition:
                where_conditions.append({'publication_year': year_condition})
        
        # Filter by section
        if 'sections' in filters and filters['sections']:
            where_conditions.append({'section': {'$in': filters['sections']}})
        
        # Filter by journal
        if 'journals' in filters and filters['journals']:
            where_conditions.append({'journal': {'$in': filters['journals']}})
        
        # Filter by minimum relevance (distance)
        if 'min_relevance' in filters:
            # Note: This would need to be handled in post-processing
            # as ChromaDB doesn't support distance filtering in where clause
            pass
        
        # Combine conditions
        if len(where_conditions) == 1:
            return where_conditions[0]
        elif len(where_conditions) > 1:
            return {'$and': where_conditions}
        
        return None
    
    def _format_search_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format ChromaDB results into a standardized format"""
        formatted_results = []
        
        documents = results.get('documents', [[]])[0]
        distances = results.get('distances', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0] if 'metadatas' in results else [{}] * len(documents)
        ids = results.get('ids', [[]])[0]
        
        for i, (doc, distance, metadata, doc_id) in enumerate(zip(documents, distances, metadatas, ids)):
            formatted_result = {
                'id': doc_id,
                'document': doc,
                'distance': distance,
                'relevance_score': 1.0 - distance,  # Convert distance to relevance
                'rank': i + 1
            }
            
            if metadata:
                formatted_result['metadata'] = metadata
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        
        if not self.collection:
            return {}
        
        try:
            # Get basic collection info
            collection_count = self.collection.count()
            
            # Get sample of documents to analyze
            sample_results = self.collection.get(
                limit=min(1000, collection_count),
                include=['metadatas']
            )
            
            metadatas = sample_results.get('metadatas', [])
            
            # Analyze metadata
            stats = {
                'total_chunks': collection_count,
                'sample_size': len(metadatas),
                'document_count': len(set(m.get('document_id', '') for m in metadatas if m.get('document_id'))),
                'sections': {},
                'chunk_types': {},
                'publication_years': {},
                'journals': set(),
                'avg_word_count': 0,
                'quality_distribution': {'high': 0, 'medium': 0, 'low': 0}
            }
            
            total_words = 0
            for metadata in metadatas:
                if not metadata:
                    continue
                
                # Count sections
                section = metadata.get('section', 'unknown')
                stats['sections'][section] = stats['sections'].get(section, 0) + 1
                
                # Count chunk types
                chunk_type = metadata.get('chunk_type', 'unknown')
                stats['chunk_types'][chunk_type] = stats['chunk_types'].get(chunk_type, 0) + 1
                
                # Count publication years
                year = metadata.get('publication_year')
                if year:
                    stats['publication_years'][str(year)] = stats['publication_years'].get(str(year), 0) + 1
                
                # Collect journals
                journal = metadata.get('journal')
                if journal:
                    stats['journals'].add(journal)
                
                # Sum word counts
                word_count = metadata.get('word_count', 0)
                if isinstance(word_count, (int, float)):
                    total_words += word_count
            
            # Calculate averages
            if metadatas:
                stats['avg_word_count'] = total_words / len(metadatas)
            
            # Convert journals set to list
            stats['journals'] = list(stats['journals'])[:20]  # Limit to top 20
            
            # Sort sections and chunk types by frequency
            stats['sections'] = dict(sorted(stats['sections'].items(), key=lambda x: x[1], reverse=True))
            stats['chunk_types'] = dict(sorted(stats['chunk_types'].items(), key=lambda x: x[1], reverse=True))
            
            stats['last_updated'] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a specific document"""
        
        if not self.collection:
            return False
        
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={'document_id': document_id},
                include=['ids']
            )
            
            chunk_ids = results.get('ids', [])
            
            if chunk_ids:
                self.collection.delete(ids=chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for document {document_id}")
                return True
            else:
                logger.warning(f"No chunks found for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def update_document_metadata(
        self, 
        document_id: str, 
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """Update metadata for all chunks of a document"""
        
        if not self.collection:
            return False
        
        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={'document_id': document_id},
                include=['ids', 'metadatas']
            )
            
            chunk_ids = results.get('ids', [])
            current_metadatas = results.get('metadatas', [])
            
            if not chunk_ids:
                logger.warning(f"No chunks found for document {document_id}")
                return False
            
            # Update each chunk's metadata
            updated_metadatas = []
            for metadata in current_metadatas:
                updated_metadata = {**metadata, **metadata_updates}
                updated_metadatas.append(updated_metadata)
            
            # Update in ChromaDB
            self.collection.update(
                ids=chunk_ids,
                metadatas=updated_metadatas
            )
            
            logger.info(f"Updated metadata for {len(chunk_ids)} chunks of document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document metadata: {e}")
            return False
    
    async def get_similar_documents(
        self, 
        document_id: str, 
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Find documents similar to a given document"""
        
        if not self.collection:
            return []
        
        try:
            # Get a representative chunk from the document (e.g., abstract or introduction)
            doc_chunks = self.collection.get(
                where={
                    '$and': [
                        {'document_id': document_id},
                        {'section': {'$in': ['abstract', 'introduction', 'abstract_introduction']}}
                    ]
                },
                limit=1,
                include=['documents']
            )
            
            if not doc_chunks.get('documents'):
                # Fallback to any chunk from the document
                doc_chunks = self.collection.get(
                    where={'document_id': document_id},
                    limit=1,
                    include=['documents']
                )
            
            if not doc_chunks.get('documents'):
                return []
            
            # Use the chunk text as query
            query_text = doc_chunks['documents'][0]
            
            # Perform semantic search
            similar_results = await self.semantic_search(
                query_text,
                n_results=n_results * 3  # Get more results to filter out same document
            )
            
            # Filter out chunks from the same document
            similar_docs = {}
            for result in similar_results:
                result_doc_id = result.get('metadata', {}).get('document_id')
                if result_doc_id and result_doc_id != document_id:
                    if result_doc_id not in similar_docs:
                        similar_docs[result_doc_id] = {
                            'document_id': result_doc_id,
                            'title': result.get('metadata', {}).get('title', 'Unknown'),
                            'relevance_score': result['relevance_score'],
                            'matching_sections': []
                        }
                    
                    similar_docs[result_doc_id]['matching_sections'].append({
                        'section': result.get('metadata', {}).get('section', 'unknown'),
                        'relevance': result['relevance_score']
                    })
            
            # Sort by relevance and return top results
            sorted_docs = sorted(
                similar_docs.values(), 
                key=lambda x: x['relevance_score'], 
                reverse=True
            )[:n_results]
            
            return sorted_docs
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the vector store service"""
        health_status = {
            'status': 'unknown',
            'chromadb_connected': False,
            'embedding_model_loaded': False,
            'collection_available': False,
            'total_documents': 0,
            'last_check': datetime.now().isoformat()
        }
        
        try:
            # Check ChromaDB connection
            if self.client:
                self.client.heartbeat()
                health_status['chromadb_connected'] = True
            
            # Check embedding model
            if self.embedding_model:
                health_status['embedding_model_loaded'] = True
            
            # Check collection
            if self.collection:
                health_status['collection_available'] = True
                health_status['total_documents'] = self.collection.count()
            
            # Overall status
            if all([
                health_status['chromadb_connected'],
                health_status['embedding_model_loaded'],
                health_status['collection_available']
            ]):
                health_status['status'] = 'healthy'
            else:
                health_status['status'] = 'degraded'
                
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            logger.error(f"Vector store health check failed: {e}")
        
        return health_status
    
    async def search_similar(
        self, 
        query: str, 
        limit: int = 10,
        min_relevance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using semantic similarity"""
        
        if not self.collection or not self.embedding_model:
            logger.error("Vector store not properly initialized")
            return []
        
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    # Convert distance to relevance score (lower distance = higher relevance)
                    relevance_score = max(0.0, 1.0 - distance)
                    
                    if relevance_score >= min_relevance:
                        formatted_results.append({
                            'document': doc,
                            'metadata': metadata or {},
                            'relevance_score': relevance_score,
                            'rank': i + 1
                        })
            
            logger.info(f"Found {len(formatted_results)} similar documents for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []

# Global instance
vector_store_service = VectorStoreService() 
