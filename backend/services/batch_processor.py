"""
Batch Processing Service for AI Scholar
Optimizes AI operations by processing multiple items in batches
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    batch_size: int = 10
    max_wait_time: float = 2.0  # seconds
    max_concurrent_batches: int = 3
    retry_attempts: int = 2
    retry_delay: float = 1.0

@dataclass
class BatchResult:
    """Result of batch processing"""
    success_count: int
    error_count: int
    total_time: float
    results: List[Any]
    errors: List[Exception]

class BatchProcessor(Generic[T, R]):
    """Generic batch processor for AI operations"""
    
    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        self.pending_items: List[T] = []
        self.pending_callbacks: List[Callable] = []
        self.processing_lock = asyncio.Lock()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_batches)
    
    async def add_to_batch(self, item: T, processor: Callable[[List[T]], List[R]]) -> R:
        """Add item to batch and return result when batch is processed"""
        future = asyncio.Future()
        
        async with self.processing_lock:
            self.pending_items.append(item)
            self.pending_callbacks.append((future, processor))
            
            # Process batch if it's full or after timeout
            if len(self.pending_items) >= self.config.batch_size:
                await self._process_batch()
        
        # Set up timeout for batch processing
        try:
            return await asyncio.wait_for(future, timeout=self.config.max_wait_time + 5.0)
        except asyncio.TimeoutError:
            # Force process batch if timeout reached
            async with self.processing_lock:
                if self.pending_items:
                    await self._process_batch()
            return await future
    
    async def _process_batch(self):
        """Process current batch of items"""
        if not self.pending_items:
            return
        
        items = self.pending_items.copy()
        callbacks = self.pending_callbacks.copy()
        
        # Clear pending items
        self.pending_items.clear()
        self.pending_callbacks.clear()
        
        start_time = time.time()
        
        try:
            # Group items by processor type
            processor_groups = {}
            for i, (future, processor) in enumerate(callbacks):
                processor_key = id(processor)
                if processor_key not in processor_groups:
                    processor_groups[processor_key] = {
                        'processor': processor,
                        'items': [],
                        'futures': []
                    }
                processor_groups[processor_key]['items'].append(items[i])
                processor_groups[processor_key]['futures'].append(future)
            
            # Process each group
            for group_data in processor_groups.values():
                try:
                    results = await self._execute_processor(
                        group_data['processor'], 
                        group_data['items']
                    )
                    
                    # Set results for futures
                    for future, result in zip(group_data['futures'], results):
                        if not future.done():
                            future.set_result(result)
                            
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
                    # Set exception for all futures in this group
                    for future in group_data['futures']:
                        if not future.done():
                            future.set_exception(e)
        
        except Exception as e:
            logger.error(f"Critical batch processing error: {e}")
            # Set exception for all remaining futures
            for future, _ in callbacks:
                if not future.done():
                    future.set_exception(e)
        
        processing_time = time.time() - start_time
        logger.info(f"Processed batch of {len(items)} items in {processing_time:.3f}s")
    
    async def _execute_processor(self, processor: Callable, items: List[T]) -> List[R]:
        """Execute processor with retry logic"""
        for attempt in range(self.config.retry_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(processor):
                    return await processor(items)
                else:
                    # Run synchronous processor in thread pool
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(self.executor, processor, items)
            
            except Exception as e:
                if attempt < self.config.retry_attempts:
                    logger.warning(f"Batch processor attempt {attempt + 1} failed: {e}, retrying...")
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    logger.error(f"Batch processor failed after {attempt + 1} attempts: {e}")
                    raise
    
    async def force_process_pending(self):
        """Force process any pending items"""
        async with self.processing_lock:
            if self.pending_items:
                await self._process_batch()

class DocumentBatchProcessor:
    """Specialized batch processor for document operations"""
    
    def __init__(self):
        self.embedding_processor = BatchProcessor[str, List[float]](
            BatchConfig(batch_size=20, max_wait_time=3.0)
        )
        self.summary_processor = BatchProcessor[Dict, Dict](
            BatchConfig(batch_size=10, max_wait_time=5.0)
        )
        self.analysis_processor = BatchProcessor[Dict, Dict](
            BatchConfig(batch_size=15, max_wait_time=4.0)
        )
    
    async def process_documents_batch(self, documents: List[Dict], operations: List[str]) -> List[Dict]:
        """Process multiple documents with specified operations"""
        results = []
        
        for doc in documents:
            doc_results = {"document_id": doc.get("id"), "operations": {}}
            
            # Process each requested operation
            tasks = []
            
            if "embeddings" in operations:
                task = self._process_document_embeddings(doc)
                tasks.append(("embeddings", task))
            
            if "summary" in operations:
                task = self._process_document_summary(doc)
                tasks.append(("summary", task))
            
            if "analysis" in operations:
                task = self._process_document_analysis(doc)
                tasks.append(("analysis", task))
            
            # Wait for all operations to complete
            for operation, task in tasks:
                try:
                    result = await task
                    doc_results["operations"][operation] = result
                except Exception as e:
                    logger.error(f"Error in {operation} for document {doc.get('id')}: {e}")
                    doc_results["operations"][operation] = {"error": str(e)}
            
            results.append(doc_results)
        
        return results
    
    async def _process_document_embeddings(self, document: Dict) -> List[float]:
        """Process document embeddings using batch processor"""
        text = document.get("content", "")
        
        async def embedding_batch_processor(texts: List[str]) -> List[List[float]]:
            """Batch process embeddings"""
            # This would integrate with your actual embedding service
            results = []
            for text in texts:
                # Mock embedding generation - replace with actual service
                embedding = [0.1 * i * len(text) for i in range(384)]
                results.append(embedding)
            return results
        
        return await self.embedding_processor.add_to_batch(text, embedding_batch_processor)
    
    async def _process_document_summary(self, document: Dict) -> Dict:
        """Process document summary using batch processor"""
        doc_data = {
            "id": document.get("id"),
            "content": document.get("content", ""),
            "title": document.get("title", "")
        }
        
        async def summary_batch_processor(docs: List[Dict]) -> List[Dict]:
            """Batch process summaries"""
            results = []
            for doc in docs:
                # Mock summary generation - replace with actual service
                summary = {
                    "summary": f"Summary of document {doc['id']}: {doc['content'][:100]}...",
                    "key_points": ["Point 1", "Point 2", "Point 3"],
                    "word_count": len(doc['content'].split()),
                    "confidence": 0.85
                }
                results.append(summary)
            return results
        
        return await self.summary_processor.add_to_batch(doc_data, summary_batch_processor)
    
    async def _process_document_analysis(self, document: Dict) -> Dict:
        """Process document analysis using batch processor"""
        doc_data = {
            "id": document.get("id"),
            "content": document.get("content", ""),
            "metadata": document.get("metadata", {})
        }
        
        async def analysis_batch_processor(docs: List[Dict]) -> List[Dict]:
            """Batch process document analysis"""
            results = []
            for doc in docs:
                # Mock analysis - replace with actual service
                analysis = {
                    "topics": ["AI", "Machine Learning", "Research"],
                    "sentiment": "neutral",
                    "complexity_score": 0.7,
                    "readability_score": 0.8,
                    "entities": ["Entity1", "Entity2"],
                    "keywords": ["keyword1", "keyword2", "keyword3"]
                }
                results.append(analysis)
            return results
        
        return await self.analysis_processor.add_to_batch(doc_data, analysis_batch_processor)
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        tasks = []
        
        for text in texts:
            task = self._process_document_embeddings({"content": text})
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def cleanup(self):
        """Clean up batch processors"""
        await self.embedding_processor.force_process_pending()
        await self.summary_processor.force_process_pending()
        await self.analysis_processor.force_process_pending()

class QueryBatchProcessor:
    """Specialized batch processor for query operations"""
    
    def __init__(self):
        self.rag_processor = BatchProcessor[Dict, Dict](
            BatchConfig(batch_size=8, max_wait_time=4.0)
        )
        self.search_processor = BatchProcessor[str, List[Dict]](
            BatchConfig(batch_size=15, max_wait_time=2.0)
        )
    
    async def process_rag_queries_batch(self, queries: List[Dict]) -> List[Dict]:
        """Process multiple RAG queries efficiently"""
        tasks = []
        
        for query_data in queries:
            task = self._process_single_rag_query(query_data)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_rag_query(self, query_data: Dict) -> Dict:
        """Process single RAG query using batch processor"""
        
        async def rag_batch_processor(queries: List[Dict]) -> List[Dict]:
            """Batch process RAG queries"""
            results = []
            for q in queries:
                # Mock RAG processing - replace with actual service
                result = {
                    "query": q["query"],
                    "answer": f"Answer to: {q['query']}",
                    "confidence": 0.85,
                    "sources": ["doc1.pdf", "doc2.pdf"],
                    "processing_time": 0.5
                }
                results.append(result)
            return results
        
        return await self.rag_processor.add_to_batch(query_data, rag_batch_processor)
    
    async def process_search_queries_batch(self, queries: List[str]) -> List[List[Dict]]:
        """Process multiple search queries efficiently"""
        tasks = []
        
        for query in queries:
            task = self._process_single_search_query(query)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def _process_single_search_query(self, query: str) -> List[Dict]:
        """Process single search query using batch processor"""
        
        async def search_batch_processor(queries: List[str]) -> List[List[Dict]]:
            """Batch process search queries"""
            results = []
            for q in queries:
                # Mock search results - replace with actual service
                search_results = [
                    {"id": "doc1", "title": f"Result 1 for {q}", "score": 0.9},
                    {"id": "doc2", "title": f"Result 2 for {q}", "score": 0.8},
                    {"id": "doc3", "title": f"Result 3 for {q}", "score": 0.7}
                ]
                results.append(search_results)
            return results
        
        return await self.search_processor.add_to_batch(query, search_batch_processor)

# Global batch processors
document_batch_processor = DocumentBatchProcessor()
query_batch_processor = QueryBatchProcessor()

# Convenience functions
async def batch_process_documents(documents: List[Dict], operations: List[str] = None) -> List[Dict]:
    """Batch process documents with specified operations"""
    operations = operations or ["embeddings", "summary"]
    return await document_batch_processor.process_documents_batch(documents, operations)

async def batch_generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Batch generate embeddings for texts"""
    return await document_batch_processor.generate_embeddings_batch(texts)

async def batch_process_rag_queries(queries: List[Dict]) -> List[Dict]:
    """Batch process RAG queries"""
    return await query_batch_processor.process_rag_queries_batch(queries)

# Usage example
if __name__ == "__main__":
    async def test_batch_processing():
        # Test document batch processing
        documents = [
            {"id": "doc1", "content": "This is document 1 content", "title": "Document 1"},
            {"id": "doc2", "content": "This is document 2 content", "title": "Document 2"},
            {"id": "doc3", "content": "This is document 3 content", "title": "Document 3"}
        ]
        
        results = await batch_process_documents(documents, ["embeddings", "summary", "analysis"])
        print(f"Batch processing results: {len(results)} documents processed")
        
        # Test embedding batch processing
        texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
        embeddings = await batch_generate_embeddings(texts)
        print(f"Generated {len(embeddings)} embeddings")
        
        # Test RAG query batch processing
        queries = [
            {"query": "What is AI?", "context": "context1"},
            {"query": "How does ML work?", "context": "context2"},
            {"query": "What is deep learning?", "context": "context3"}
        ]
        
        rag_results = await batch_process_rag_queries(queries)
        print(f"Processed {len(rag_results)} RAG queries")
    
    # Run test
    asyncio.run(test_batch_processing())