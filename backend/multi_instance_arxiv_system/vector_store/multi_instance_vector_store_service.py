"""
Multi-Instance Vector Store Service for ArXiv System.

This service extends the existing VectorStoreService to support multiple scholar instances
with complete separation, instance-specific metadata, and unified search capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import asyncio
import uuid

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from services.vector_store_service import VectorStoreService
    from multi_instance_arxiv_system.shared.multi_instance_data_models import (
        BasePaper, ArxivPaper, JournalPaper, InstanceConfig, VectorStoreConfig
    )
except ImportError as e:
    print(f"Import error: {e}")
    raise

logger = logging.getLogger(__name__)


class MultiInstanceVectorStoreService:
    """
    Multi-instance vector store service that manages separate collections
    for different scholar instances while providing unified search capabilities.
    """
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8082):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.instance_services: Dict[str, VectorStoreService] = {}
        self.instance_configs: Dict[str, VectorStoreConfig] = {}
        self.initialized_instances: set = set()
        
        # Collection naming conventions
        self.collection_prefix = "scholar_instance"
        self.collection_suffix = "papers"
        
        logger.info(f"Initialized MultiInstanceVectorStoreService for {chroma_host}:{chroma_port}")
    
    def _get_collection_name(self, instance_name: str) -> str:
        """Generate standardized collection name for an instance."""
        # Convert instance name to safe collection name
        safe_name = instance_name.lower().replace('-', '_').replace(' ', '_')
        return f"{self.collection_prefix}_{safe_name}_{self.collection_suffix}"
    
    async def initialize_instance(
        self, 
        instance_name: str, 
        config: VectorStoreConfig
    ) -> bool:
        """Initialize vector store service for a specific instance."""
        
        try:
            logger.info(f"Initializing vector store for instance: {instance_name}")
            
            # Create instance-specific vector store service
            service = VectorStoreService(
                chroma_host=config.host or self.chroma_host,
                chroma_port=config.port or self.chroma_port
            )
            
            # Set instance-specific configuration
            service.collection_name = self._get_collection_name(instance_name)
            service.embedding_model_name = config.embedding_model
            
            # Initialize the service
            await service.initialize()
            
            # Store service and config
            self.instance_services[instance_name] = service
            self.instance_configs[instance_name] = config
            self.initialized_instances.add(instance_name)
            
            # Update collection metadata with instance information
            if service.collection:
                current_metadata = service.collection.metadata or {}
                instance_metadata = {
                    **current_metadata,
                    "instance_name": instance_name,
                    "instance_type": "scholar_instance",
                    "embedding_model": config.embedding_model,
                    "chunk_size": config.chunk_size,
                    "chunk_overlap": config.chunk_overlap,
                    "last_initialized": datetime.now().isoformat()
                }
                
                # Update collection metadata
                service.collection.modify(metadata=instance_metadata)
            
            logger.info(f"Successfully initialized vector store for {instance_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store for {instance_name}: {e}")
            return False
    
    async def add_instance_document(
        self, 
        instance_name: str, 
        paper: BasePaper, 
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add a document to a specific instance's vector store."""
        
        if instance_name not in self.instance_services:
            raise ValueError(f"Instance {instance_name} not initialized")
        
        service = self.instance_services[instance_name]
        
        try:
            # Enhance chunks with instance-specific metadata
            enhanced_chunks = []
            for chunk in chunks:
                enhanced_chunk = {**chunk}
                
                # Add instance-specific metadata
                if 'document_metadata' not in enhanced_chunk:
                    enhanced_chunk['document_metadata'] = {}
                
                enhanced_chunk['document_metadata'].update({
                    'instance_name': instance_name,
                    'paper_type': paper.source_type,
                    'document_id': paper.get_document_id(),
                    'paper_id': paper.paper_id,
                    'title': paper.title,
                    'authors': paper.authors,
                    'published_date': paper.published_date.isoformat(),
                    'abstract': paper.abstract[:500] + "..." if len(paper.abstract) > 500 else paper.abstract
                })
                
                # Add paper-specific metadata
                if isinstance(paper, ArxivPaper):
                    enhanced_chunk['document_metadata'].update({
                        'arxiv_id': paper.arxiv_id,
                        'categories': paper.categories,
                        'doi': paper.doi,
                        'pdf_url': paper.pdf_url
                    })
                elif isinstance(paper, JournalPaper):
                    enhanced_chunk['document_metadata'].update({
                        'journal_name': paper.journal_name,
                        'volume': paper.volume,
                        'issue': paper.issue,
                        'pages': paper.pages,
                        'doi': paper.doi,
                        'journal_url': paper.journal_url
                    })
                
                enhanced_chunks.append(enhanced_chunk)
            
            # Add document to instance collection
            result = await service.add_document_chunks(
                document_id=paper.get_document_id(),
                chunks=enhanced_chunks
            )
            
            # Add instance information to result
            result['instance_name'] = instance_name
            result['collection_name'] = service.collection_name
            
            logger.info(f"Added document {paper.get_document_id()} to {instance_name} collection")
            return result
            
        except Exception as e:
            logger.error(f"Error adding document to {instance_name}: {e}")
            raise
    
    async def search_instance_papers(
        self, 
        instance_name: str, 
        query: str, 
        n_results: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search papers within a specific instance."""
        
        if instance_name not in self.instance_services:
            raise ValueError(f"Instance {instance_name} not initialized")
        
        service = self.instance_services[instance_name]
        
        try:
            # Add instance filter to ensure we only get results from this instance
            instance_filters = filters or {}
            instance_filters['instance_name'] = instance_name
            
            results = await service.semantic_search(
                query=query,
                n_results=n_results,
                filters=instance_filters,
                include_metadata=True
            )
            
            # Enhance results with instance information
            for result in results:
                result['instance_name'] = instance_name
                result['collection_name'] = service.collection_name
            
            logger.info(f"Found {len(results)} results in {instance_name} for query: {query[:100]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching {instance_name}: {e}")
            raise
    
    async def search_all_instances(
        self, 
        query: str, 
        n_results: int = 10,
        instance_weights: Optional[Dict[str, float]] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search across all initialized instances with optional weighting."""
        
        if not self.initialized_instances:
            logger.warning("No instances initialized for search")
            return []
        
        try:
            # Default equal weighting
            weights = instance_weights or {name: 1.0 for name in self.initialized_instances}
            
            # Search each instance
            all_results = []
            search_tasks = []
            
            for instance_name in self.initialized_instances:
                # Calculate results per instance based on weight
                instance_weight = weights.get(instance_name, 1.0)
                instance_results = max(1, int(n_results * instance_weight))
                
                task = self.search_instance_papers(
                    instance_name=instance_name,
                    query=query,
                    n_results=instance_results,
                    filters=filters
                )
                search_tasks.append((instance_name, task))
            
            # Execute searches concurrently
            for instance_name, task in search_tasks:
                try:
                    results = await task
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Search failed for instance {instance_name}: {e}")
                    continue
            
            # Sort by relevance score and limit results
            all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            final_results = all_results[:n_results]
            
            # Re-rank results
            for i, result in enumerate(final_results):
                result['global_rank'] = i + 1
            
            logger.info(f"Found {len(final_results)} total results across {len(self.initialized_instances)} instances")
            return final_results
            
        except Exception as e:
            logger.error(f"Error searching all instances: {e}")
            return []
    
    async def get_instance_stats(self, instance_name: str) -> Dict[str, Any]:
        """Get statistics for a specific instance."""
        
        if instance_name not in self.instance_services:
            return {}
        
        service = self.instance_services[instance_name]
        
        try:
            stats = await service.get_collection_stats()
            
            # Add instance-specific information
            stats.update({
                'instance_name': instance_name,
                'collection_name': service.collection_name,
                'embedding_model': service.embedding_model_name,
                'initialized': instance_name in self.initialized_instances,
                'config': self.instance_configs.get(instance_name, {}).to_dict() if instance_name in self.instance_configs else {}
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats for {instance_name}: {e}")
            return {}
    
    async def get_all_instance_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all initialized instances."""
        
        stats = {}
        
        for instance_name in self.initialized_instances:
            stats[instance_name] = await self.get_instance_stats(instance_name)
        
        return stats
    
    async def delete_instance_document(
        self, 
        instance_name: str, 
        document_id: str
    ) -> bool:
        """Delete a document from a specific instance."""
        
        if instance_name not in self.instance_services:
            return False
        
        service = self.instance_services[instance_name]
        
        try:
            result = await service.delete_document(document_id)
            logger.info(f"Deleted document {document_id} from {instance_name}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting document from {instance_name}: {e}")
            return False
    
    async def update_instance_document_metadata(
        self, 
        instance_name: str, 
        document_id: str, 
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """Update document metadata in a specific instance."""
        
        if instance_name not in self.instance_services:
            return False
        
        service = self.instance_services[instance_name]
        
        try:
            # Ensure instance name is preserved in metadata
            metadata_updates['instance_name'] = instance_name
            
            result = await service.update_document_metadata(document_id, metadata_updates)
            logger.info(f"Updated metadata for {document_id} in {instance_name}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating document metadata in {instance_name}: {e}")
            return False
    
    async def find_similar_papers_across_instances(
        self, 
        reference_paper: BasePaper, 
        n_results: int = 10,
        exclude_same_instance: bool = False
    ) -> List[Dict[str, Any]]:
        """Find papers similar to a reference paper across all instances."""
        
        try:
            # Use paper abstract and title as query
            query = f"{reference_paper.title} {reference_paper.abstract}"
            
            # Search all instances
            all_results = await self.search_all_instances(
                query=query,
                n_results=n_results * 2  # Get more results to filter
            )
            
            # Filter results
            filtered_results = []
            for result in all_results:
                metadata = result.get('metadata', {})
                result_paper_id = metadata.get('paper_id')
                result_instance = metadata.get('instance_name')
                
                # Skip the reference paper itself
                if result_paper_id == reference_paper.paper_id:
                    continue
                
                # Skip same instance if requested
                if exclude_same_instance and result_instance == reference_paper.instance_name:
                    continue
                
                filtered_results.append(result)
            
            # Return top results
            return filtered_results[:n_results]
            
        except Exception as e:
            logger.error(f"Error finding similar papers: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all instance vector stores."""
        
        health_status = {
            'overall_status': 'unknown',
            'total_instances': len(self.initialized_instances),
            'healthy_instances': 0,
            'instance_health': {},
            'last_check': datetime.now().isoformat()
        }
        
        try:
            for instance_name in self.initialized_instances:
                service = self.instance_services.get(instance_name)
                if service:
                    instance_health = await service.health_check()
                    health_status['instance_health'][instance_name] = instance_health
                    
                    if instance_health.get('status') == 'healthy':
                        health_status['healthy_instances'] += 1
                else:
                    health_status['instance_health'][instance_name] = {
                        'status': 'not_initialized',
                        'error': 'Service not found'
                    }
            
            # Determine overall status
            if health_status['healthy_instances'] == health_status['total_instances']:
                health_status['overall_status'] = 'healthy'
            elif health_status['healthy_instances'] > 0:
                health_status['overall_status'] = 'degraded'
            else:
                health_status['overall_status'] = 'unhealthy'
            
        except Exception as e:
            health_status['overall_status'] = 'error'
            health_status['error'] = str(e)
            logger.error(f"Health check failed: {e}")
        
        return health_status
    
    async def backup_instance_collection(
        self, 
        instance_name: str, 
        backup_path: str
    ) -> bool:
        """Backup a specific instance's collection."""
        
        if instance_name not in self.instance_services:
            return False
        
        service = self.instance_services[instance_name]
        
        try:
            # Get all documents from the collection
            if not service.collection:
                return False
            
            # Get all data from collection
            all_data = service.collection.get(
                include=['documents', 'metadatas', 'embeddings']
            )
            
            # Save to backup file
            backup_data = {
                'instance_name': instance_name,
                'collection_name': service.collection_name,
                'embedding_model': service.embedding_model_name,
                'backup_timestamp': datetime.now().isoformat(),
                'data': all_data
            }
            
            import json
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Backed up {instance_name} collection to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up {instance_name}: {e}")
            return False
    
    async def get_collection_names(self) -> Dict[str, str]:
        """Get mapping of instance names to collection names."""
        return {
            instance_name: self._get_collection_name(instance_name)
            for instance_name in self.initialized_instances
        }
    
    async def validate_instance_separation(self) -> Dict[str, Any]:
        """Validate that instances are properly separated."""
        
        validation_results = {
            'separation_valid': True,
            'issues': [],
            'instance_collections': {},
            'cross_contamination': []
        }
        
        try:
            for instance_name in self.initialized_instances:
                service = self.instance_services[instance_name]
                if not service.collection:
                    continue
                
                # Get sample documents from this instance
                sample_data = service.collection.get(
                    limit=100,
                    include=['metadatas']
                )
                
                metadatas = sample_data.get('metadatas', [])
                validation_results['instance_collections'][instance_name] = {
                    'collection_name': service.collection_name,
                    'document_count': len(metadatas),
                    'proper_instance_metadata': 0,
                    'missing_instance_metadata': 0
                }
                
                # Check metadata for proper instance tagging
                for metadata in metadatas:
                    if metadata and metadata.get('instance_name') == instance_name:
                        validation_results['instance_collections'][instance_name]['proper_instance_metadata'] += 1
                    else:
                        validation_results['instance_collections'][instance_name]['missing_instance_metadata'] += 1
                        validation_results['cross_contamination'].append({
                            'expected_instance': instance_name,
                            'actual_instance': metadata.get('instance_name') if metadata else None,
                            'document_id': metadata.get('document_id') if metadata else None
                        })
            
            # Check for issues
            if validation_results['cross_contamination']:
                validation_results['separation_valid'] = False
                validation_results['issues'].append("Cross-contamination detected between instances")
            
            for instance_name, data in validation_results['instance_collections'].items():
                if data['missing_instance_metadata'] > 0:
                    validation_results['issues'].append(
                        f"Instance {instance_name} has {data['missing_instance_metadata']} documents with missing/incorrect instance metadata"
                    )
            
        except Exception as e:
            validation_results['separation_valid'] = False
            validation_results['issues'].append(f"Validation error: {str(e)}")
            logger.error(f"Error validating instance separation: {e}")
        
        return validation_results