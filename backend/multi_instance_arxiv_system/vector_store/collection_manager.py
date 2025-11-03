"""
Collection Manager for Multi-Instance Vector Store.

This module handles collection creation, management, and validation
for different scholar instances with proper naming conventions.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import chromadb
from pathlib import Path

logger = logging.getLogger(__name__)


class CollectionManager:
    """
    Manages ChromaDB collections for different scholar instances
    with standardized naming and metadata conventions.
    """
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8082):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.client = None
        
        # Collection naming conventions
        self.collection_prefix = "scholar_instance"
        self.collection_suffix = "papers"
        self.reserved_names = {"default", "system", "admin", "test"}
        
    async def initialize(self):
        """Initialize ChromaDB client."""
        try:
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            
            # Test connection
            self.client.heartbeat()
            logger.info(f"CollectionManager connected to ChromaDB at {self.chroma_host}:{self.chroma_port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize CollectionManager: {e}")
            raise
    
    def _validate_instance_name(self, instance_name: str) -> bool:
        """Validate instance name for collection creation."""
        if not instance_name:
            return False
        
        # Check for reserved names
        if instance_name.lower() in self.reserved_names:
            return False
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not all(c.isalnum() or c in ['_', '-'] for c in instance_name):
            return False
        
        # Check length
        if len(instance_name) < 2 or len(instance_name) > 50:
            return False
        
        return True
    
    def _get_collection_name(self, instance_name: str) -> str:
        """Generate standardized collection name for an instance."""
        if not self._validate_instance_name(instance_name):
            raise ValueError(f"Invalid instance name: {instance_name}")
        
        # Convert to safe collection name
        safe_name = instance_name.lower().replace('-', '_').replace(' ', '_')
        return f"{self.collection_prefix}_{safe_name}_{self.collection_suffix}"
    
    async def create_instance_collection(
        self, 
        instance_name: str, 
        embedding_model: str = "all-MiniLM-L6-v2",
        description: str = "",
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new collection for a scholar instance."""
        
        if not self.client:
            raise RuntimeError("CollectionManager not initialized")
        
        try:
            collection_name = self._get_collection_name(instance_name)
            
            # Check if collection already exists
            try:
                existing_collection = self.client.get_collection(collection_name)
                logger.warning(f"Collection {collection_name} already exists")
                return {
                    'collection_name': collection_name,
                    'instance_name': instance_name,
                    'status': 'already_exists',
                    'created': False
                }
            except Exception:
                # Collection doesn't exist, proceed with creation
                pass
            
            # Prepare collection metadata
            metadata = {
                "hnsw:space": "cosine",
                "instance_name": instance_name,
                "instance_type": "scholar_instance",
                "description": description or f"Collection for {instance_name} scholar instance",
                "embedding_model": embedding_model,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "document_count": 0,
                "version": "1.0"
            }
            
            # Add additional metadata if provided
            if additional_metadata:
                metadata.update(additional_metadata)
            
            # Create collection
            collection = self.client.create_collection(
                name=collection_name,
                metadata=metadata
            )
            
            logger.info(f"Created collection {collection_name} for instance {instance_name}")
            
            return {
                'collection_name': collection_name,
                'instance_name': instance_name,
                'status': 'created',
                'created': True,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating collection for {instance_name}: {e}")
            raise
    
    async def get_instance_collection(self, instance_name: str) -> Optional[Any]:
        """Get collection for a specific instance."""
        
        if not self.client:
            raise RuntimeError("CollectionManager not initialized")
        
        try:
            collection_name = self._get_collection_name(instance_name)
            collection = self.client.get_collection(collection_name)
            return collection
            
        except Exception as e:
            logger.error(f"Error getting collection for {instance_name}: {e}")
            return None
    
    async def list_instance_collections(self) -> List[Dict[str, Any]]:
        """List all scholar instance collections."""
        
        if not self.client:
            raise RuntimeError("CollectionManager not initialized")
        
        try:
            all_collections = self.client.list_collections()
            instance_collections = []
            
            for collection in all_collections:
                # Check if this is a scholar instance collection
                if collection.name.startswith(self.collection_prefix):
                    metadata = collection.metadata or {}
                    
                    instance_info = {
                        'collection_name': collection.name,
                        'instance_name': metadata.get('instance_name', 'unknown'),
                        'instance_type': metadata.get('instance_type', 'unknown'),
                        'description': metadata.get('description', ''),
                        'embedding_model': metadata.get('embedding_model', ''),
                        'created_at': metadata.get('created_at', ''),
                        'last_updated': metadata.get('last_updated', ''),
                        'document_count': collection.count()
                    }
                    
                    instance_collections.append(instance_info)
            
            return instance_collections
            
        except Exception as e:
            logger.error(f"Error listing instance collections: {e}")
            return []
    
    async def delete_instance_collection(self, instance_name: str) -> bool:
        """Delete collection for a specific instance."""
        
        if not self.client:
            raise RuntimeError("CollectionManager not initialized")
        
        try:
            collection_name = self._get_collection_name(instance_name)
            
            # Check if collection exists
            try:
                self.client.get_collection(collection_name)
            except Exception:
                logger.warning(f"Collection {collection_name} does not exist")
                return False
            
            # Delete collection
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection {collection_name} for instance {instance_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection for {instance_name}: {e}")
            return False
    
    async def update_collection_metadata(
        self, 
        instance_name: str, 
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """Update metadata for an instance collection."""
        
        if not self.client:
            raise RuntimeError("CollectionManager not initialized")
        
        try:
            collection = await self.get_instance_collection(instance_name)
            if not collection:
                return False
            
            # Get current metadata
            current_metadata = collection.metadata or {}
            
            # Update metadata
            updated_metadata = {
                **current_metadata,
                **metadata_updates,
                'last_updated': datetime.now().isoformat()
            }
            
            # Apply updates
            collection.modify(metadata=updated_metadata)
            
            logger.info(f"Updated metadata for collection {collection.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating collection metadata for {instance_name}: {e}")
            return False
    
    async def get_collection_stats(self, instance_name: str) -> Dict[str, Any]:
        """Get detailed statistics for an instance collection."""
        
        try:
            collection = await self.get_instance_collection(instance_name)
            if not collection:
                return {}
            
            # Basic stats
            document_count = collection.count()
            metadata = collection.metadata or {}
            
            stats = {
                'collection_name': collection.name,
                'instance_name': instance_name,
                'document_count': document_count,
                'embedding_model': metadata.get('embedding_model', ''),
                'created_at': metadata.get('created_at', ''),
                'last_updated': metadata.get('last_updated', ''),
                'description': metadata.get('description', '')
            }
            
            # Get sample documents for analysis
            if document_count > 0:
                sample_size = min(100, document_count)
                sample_data = collection.get(
                    limit=sample_size,
                    include=['metadatas']
                )
                
                metadatas = sample_data.get('metadatas', [])
                
                # Analyze metadata
                if metadatas:
                    # Count document types
                    paper_types = {}
                    sections = {}
                    years = {}
                    
                    for metadata in metadatas:
                        if not metadata:
                            continue
                        
                        # Paper types
                        paper_type = metadata.get('paper_type', 'unknown')
                        paper_types[paper_type] = paper_types.get(paper_type, 0) + 1
                        
                        # Sections
                        section = metadata.get('section', 'unknown')
                        sections[section] = sections.get(section, 0) + 1
                        
                        # Publication years
                        pub_date = metadata.get('published_date', '')
                        if pub_date:
                            try:
                                year = pub_date[:4]  # Extract year from ISO date
                                years[year] = years.get(year, 0) + 1
                            except:
                                pass
                    
                    stats.update({
                        'paper_types': dict(sorted(paper_types.items(), key=lambda x: x[1], reverse=True)),
                        'sections': dict(sorted(sections.items(), key=lambda x: x[1], reverse=True)),
                        'publication_years': dict(sorted(years.items(), reverse=True)),
                        'sample_size': len(metadatas)
                    })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats for {instance_name}: {e}")
            return {}
    
    async def validate_collection_integrity(self, instance_name: str) -> Dict[str, Any]:
        """Validate the integrity of an instance collection."""
        
        validation_result = {
            'instance_name': instance_name,
            'valid': True,
            'issues': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            collection = await self.get_instance_collection(instance_name)
            if not collection:
                validation_result['valid'] = False
                validation_result['issues'].append("Collection not found")
                return validation_result
            
            # Check collection metadata
            metadata = collection.metadata or {}
            expected_instance = metadata.get('instance_name')
            
            if expected_instance != instance_name:
                validation_result['issues'].append(
                    f"Instance name mismatch: expected {instance_name}, found {expected_instance}"
                )
                validation_result['valid'] = False
            
            # Check document count
            document_count = collection.count()
            validation_result['stats']['document_count'] = document_count
            
            if document_count == 0:
                validation_result['warnings'].append("Collection is empty")
            
            # Sample documents for validation
            if document_count > 0:
                sample_size = min(50, document_count)
                sample_data = collection.get(
                    limit=sample_size,
                    include=['metadatas', 'documents']
                )
                
                metadatas = sample_data.get('metadatas', [])
                documents = sample_data.get('documents', [])
                
                # Validate metadata consistency
                instance_mismatches = 0
                empty_documents = 0
                missing_metadata = 0
                
                for i, (metadata, document) in enumerate(zip(metadatas, documents)):
                    if not metadata:
                        missing_metadata += 1
                        continue
                    
                    if metadata.get('instance_name') != instance_name:
                        instance_mismatches += 1
                    
                    if not document or not document.strip():
                        empty_documents += 1
                
                validation_result['stats'].update({
                    'sample_size': len(metadatas),
                    'instance_mismatches': instance_mismatches,
                    'empty_documents': empty_documents,
                    'missing_metadata': missing_metadata
                })
                
                # Add issues based on validation
                if instance_mismatches > 0:
                    validation_result['issues'].append(
                        f"{instance_mismatches} documents have incorrect instance metadata"
                    )
                    validation_result['valid'] = False
                
                if empty_documents > 0:
                    validation_result['warnings'].append(
                        f"{empty_documents} documents are empty or contain only whitespace"
                    )
                
                if missing_metadata > 0:
                    validation_result['warnings'].append(
                        f"{missing_metadata} documents have missing metadata"
                    )
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['issues'].append(f"Validation error: {str(e)}")
            logger.error(f"Error validating collection for {instance_name}: {e}")
        
        return validation_result
    
    async def backup_collection(
        self, 
        instance_name: str, 
        backup_path: str,
        include_embeddings: bool = False
    ) -> bool:
        """Backup an instance collection to a file."""
        
        try:
            collection = await self.get_instance_collection(instance_name)
            if not collection:
                return False
            
            # Determine what to include in backup
            include_fields = ['documents', 'metadatas']
            if include_embeddings:
                include_fields.append('embeddings')
            
            # Get all data
            all_data = collection.get(include=include_fields)
            
            # Prepare backup data
            backup_data = {
                'instance_name': instance_name,
                'collection_name': collection.name,
                'collection_metadata': collection.metadata,
                'backup_timestamp': datetime.now().isoformat(),
                'document_count': collection.count(),
                'includes_embeddings': include_embeddings,
                'data': all_data
            }
            
            # Save to file
            import json
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Backed up collection for {instance_name} to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up collection for {instance_name}: {e}")
            return False
    
    async def restore_collection(
        self, 
        backup_path: str, 
        new_instance_name: Optional[str] = None
    ) -> bool:
        """Restore a collection from a backup file."""
        
        try:
            # Load backup data
            import json
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            instance_name = new_instance_name or backup_data['instance_name']
            
            # Create collection
            result = await self.create_instance_collection(
                instance_name=instance_name,
                embedding_model=backup_data.get('collection_metadata', {}).get('embedding_model', 'all-MiniLM-L6-v2'),
                description=f"Restored from backup on {datetime.now().isoformat()}"
            )
            
            if not result['created'] and result['status'] != 'already_exists':
                return False
            
            # Get the collection
            collection = await self.get_instance_collection(instance_name)
            if not collection:
                return False
            
            # Restore data
            data = backup_data['data']
            if data.get('documents'):
                # Add documents back to collection
                add_params = {
                    'documents': data['documents'],
                    'metadatas': data.get('metadatas', []),
                    'ids': [f"restored_{i}" for i in range(len(data['documents']))]
                }
                
                if backup_data.get('includes_embeddings') and data.get('embeddings'):
                    add_params['embeddings'] = data['embeddings']
                
                collection.add(**add_params)
            
            logger.info(f"Restored collection for {instance_name} from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring collection from {backup_path}: {e}")
            return False