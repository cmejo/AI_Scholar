"""
Zotero collection and hierarchy management service
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from core.database import get_db
from models.zotero_models import (
    ZoteroConnection, ZoteroLibrary, ZoteroCollection, ZoteroItem,
    ZoteroItemCollection
)
from models.zotero_schemas import ZoteroCollectionResponse, ZoteroCollectionTree
from services.zotero.zotero_client import ZoteroAPIClient, ZoteroAPIError

logger = logging.getLogger(__name__)


class ZoteroCollectionService:
    """Service for managing Zotero collections and hierarchies"""
    
    def __init__(self):
        self.client = ZoteroAPIClient()
    
    async def get_library_collections(
        self,
        connection_id: str,
        library_id: str,
        include_hierarchy: bool = True,
        include_item_counts: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all collections for a library
        
        Args:
            connection_id: Zotero connection ID
            library_id: Library ID
            include_hierarchy: Whether to include hierarchical structure
            include_item_counts: Whether to include item counts
            
        Returns:
            List of collections with optional hierarchy and counts
        """
        async with get_db() as db:
            # Verify connection and library
            connection = db.query(ZoteroConnection).filter(
                ZoteroConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            library = db.query(ZoteroLibrary).filter(
                and_(
                    ZoteroLibrary.connection_id == connection_id,
                    ZoteroLibrary.id == library_id
                )
            ).first()
            
            if not library:
                raise ValueError(f"Library {library_id} not found")
            
            # Get collections
            collections_query = db.query(ZoteroCollection).filter(
                ZoteroCollection.library_id == library_id
            ).order_by(ZoteroCollection.collection_name)
            
            collections = collections_query.all()
            
            # Convert to response format
            collection_list = []
            for collection in collections:
                collection_data = {
                    "id": collection.id,
                    "library_id": collection.library_id,
                    "zotero_collection_key": collection.zotero_collection_key,
                    "parent_collection_id": collection.parent_collection_id,
                    "collection_name": collection.collection_name,
                    "collection_version": collection.collection_version,
                    "collection_path": collection.collection_path,
                    "item_count": collection.item_count,
                    "created_at": collection.created_at,
                    "updated_at": collection.updated_at
                }
                
                # Add real-time item count if requested
                if include_item_counts:
                    actual_count = db.query(ZoteroItemCollection).filter(
                        ZoteroItemCollection.collection_id == collection.id
                    ).count()
                    collection_data["actual_item_count"] = actual_count
                
                collection_list.append(collection_data)
            
            # Build hierarchy if requested
            if include_hierarchy:
                return self._build_collection_hierarchy(collection_list)
            
            return collection_list
    
    def _build_collection_hierarchy(self, collections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build hierarchical structure from flat collection list"""
        
        # Create lookup maps
        collection_map = {col["id"]: col for col in collections}
        root_collections = []
        
        # Add children list to each collection
        for collection in collections:
            collection["children"] = []
        
        # Build parent-child relationships
        for collection in collections:
            parent_id = collection["parent_collection_id"]
            if parent_id and parent_id in collection_map:
                # Add to parent's children
                parent = collection_map[parent_id]
                parent["children"].append(collection)
            else:
                # Root level collection
                root_collections.append(collection)
        
        return root_collections
    
    async def get_collection_tree(
        self,
        connection_id: str,
        library_id: str,
        collection_id: Optional[str] = None
    ) -> ZoteroCollectionTree:
        """
        Get collection tree structure
        
        Args:
            connection_id: Zotero connection ID
            library_id: Library ID
            collection_id: Specific collection ID (None for all root collections)
            
        Returns:
            Hierarchical collection tree
        """
        async with get_db() as db:
            if collection_id:
                # Get specific collection and its children
                collection = db.query(ZoteroCollection).filter(
                    and_(
                        ZoteroCollection.library_id == library_id,
                        ZoteroCollection.id == collection_id
                    )
                ).first()
                
                if not collection:
                    raise ValueError(f"Collection {collection_id} not found")
                
                return await self._build_collection_tree_node(db, collection)
            else:
                # Get all root collections
                root_collections = db.query(ZoteroCollection).filter(
                    and_(
                        ZoteroCollection.library_id == library_id,
                        ZoteroCollection.parent_collection_id.is_(None)
                    )
                ).order_by(ZoteroCollection.collection_name).all()
                
                # Build tree for each root collection
                trees = []
                for collection in root_collections:
                    tree = await self._build_collection_tree_node(db, collection)
                    trees.append(tree)
                
                return trees
    
    async def _build_collection_tree_node(
        self,
        db: Session,
        collection: ZoteroCollection
    ) -> ZoteroCollectionTree:
        """Build a single collection tree node with its children"""
        
        # Get child collections
        child_collections = db.query(ZoteroCollection).filter(
            ZoteroCollection.parent_collection_id == collection.id
        ).order_by(ZoteroCollection.collection_name).all()
        
        # Recursively build child trees
        children = []
        for child in child_collections:
            child_tree = await self._build_collection_tree_node(db, child)
            children.append(child_tree)
        
        # Get actual item count
        item_count = db.query(ZoteroItemCollection).filter(
            ZoteroItemCollection.collection_id == collection.id
        ).count()
        
        return ZoteroCollectionTree(
            id=collection.id,
            collection_name=collection.collection_name,
            item_count=item_count,
            children=children
        )
    
    async def get_collection_items(
        self,
        connection_id: str,
        library_id: str,
        collection_id: str,
        include_subcollections: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get items in a collection
        
        Args:
            connection_id: Zotero connection ID
            library_id: Library ID
            collection_id: Collection ID
            include_subcollections: Whether to include items from subcollections
            limit: Maximum number of items to return
            offset: Number of items to skip
            
        Returns:
            Dictionary with items and pagination info
        """
        async with get_db() as db:
            # Verify collection exists
            collection = db.query(ZoteroCollection).filter(
                and_(
                    ZoteroCollection.library_id == library_id,
                    ZoteroCollection.id == collection_id
                )
            ).first()
            
            if not collection:
                raise ValueError(f"Collection {collection_id} not found")
            
            # Build collection filter
            collection_ids = [collection_id]
            
            if include_subcollections:
                # Get all descendant collections
                descendant_ids = await self._get_descendant_collection_ids(db, collection_id)
                collection_ids.extend(descendant_ids)
            
            # Get items in collection(s)
            items_query = db.query(ZoteroItem).join(ZoteroItemCollection).filter(
                and_(
                    ZoteroItemCollection.collection_id.in_(collection_ids),
                    ZoteroItem.is_deleted == False
                )
            ).order_by(ZoteroItem.title)
            
            # Get total count
            total_count = items_query.count()
            
            # Apply pagination
            items = items_query.offset(offset).limit(limit).all()
            
            # Convert to response format
            item_list = []
            for item in items:
                item_data = {
                    "id": item.id,
                    "zotero_item_key": item.zotero_item_key,
                    "item_type": item.item_type,
                    "title": item.title,
                    "creators": item.creators,
                    "publication_title": item.publication_title,
                    "publication_year": item.publication_year,
                    "publisher": item.publisher,
                    "doi": item.doi,
                    "url": item.url,
                    "abstract_note": item.abstract_note,
                    "tags": item.tags,
                    "date_added": item.date_added,
                    "date_modified": item.date_modified,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at
                }
                item_list.append(item_data)
            
            return {
                "collection": {
                    "id": collection.id,
                    "name": collection.collection_name,
                    "path": collection.collection_path
                },
                "items": item_list,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + len(items) < total_count
                },
                "included_subcollections": include_subcollections,
                "collection_count": len(collection_ids)
            }
    
    async def _get_descendant_collection_ids(
        self,
        db: Session,
        collection_id: str
    ) -> List[str]:
        """Get all descendant collection IDs recursively"""
        
        descendant_ids = []
        
        # Get direct children
        children = db.query(ZoteroCollection).filter(
            ZoteroCollection.parent_collection_id == collection_id
        ).all()
        
        for child in children:
            descendant_ids.append(child.id)
            # Recursively get grandchildren
            grandchildren_ids = await self._get_descendant_collection_ids(db, child.id)
            descendant_ids.extend(grandchildren_ids)
        
        return descendant_ids
    
    async def search_collections(
        self,
        connection_id: str,
        library_id: str,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search collections by name
        
        Args:
            connection_id: Zotero connection ID
            library_id: Library ID
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching collections
        """
        async with get_db() as db:
            # Search collections by name
            collections = db.query(ZoteroCollection).filter(
                and_(
                    ZoteroCollection.library_id == library_id,
                    ZoteroCollection.collection_name.ilike(f"%{query}%")
                )
            ).order_by(ZoteroCollection.collection_name).limit(limit).all()
            
            # Convert to response format
            results = []
            for collection in collections:
                # Get item count
                item_count = db.query(ZoteroItemCollection).filter(
                    ZoteroItemCollection.collection_id == collection.id
                ).count()
                
                results.append({
                    "id": collection.id,
                    "collection_name": collection.collection_name,
                    "collection_path": collection.collection_path,
                    "item_count": item_count,
                    "parent_collection_id": collection.parent_collection_id,
                    "zotero_collection_key": collection.zotero_collection_key
                })
            
            return results
    
    async def get_collection_statistics(
        self,
        connection_id: str,
        library_id: str
    ) -> Dict[str, Any]:
        """
        Get collection statistics for a library
        
        Args:
            connection_id: Zotero connection ID
            library_id: Library ID
            
        Returns:
            Dictionary with collection statistics
        """
        async with get_db() as db:
            # Get basic counts
            total_collections = db.query(ZoteroCollection).filter(
                ZoteroCollection.library_id == library_id
            ).count()
            
            root_collections = db.query(ZoteroCollection).filter(
                and_(
                    ZoteroCollection.library_id == library_id,
                    ZoteroCollection.parent_collection_id.is_(None)
                )
            ).count()
            
            # Get collection with most items
            collection_with_most_items = db.query(
                ZoteroCollection,
                func.count(ZoteroItemCollection.item_id).label('item_count')
            ).outerjoin(ZoteroItemCollection).filter(
                ZoteroCollection.library_id == library_id
            ).group_by(ZoteroCollection.id).order_by(
                func.count(ZoteroItemCollection.item_id).desc()
            ).first()
            
            # Get average items per collection
            avg_items_per_collection = db.query(
                func.avg(func.count(ZoteroItemCollection.item_id))
            ).select_from(ZoteroCollection).outerjoin(ZoteroItemCollection).filter(
                ZoteroCollection.library_id == library_id
            ).group_by(ZoteroCollection.id).scalar() or 0
            
            # Get depth statistics
            max_depth = 0
            collections_by_depth = {}
            
            collections = db.query(ZoteroCollection).filter(
                ZoteroCollection.library_id == library_id
            ).all()
            
            for collection in collections:
                depth = self._calculate_collection_depth(collection.collection_path)
                max_depth = max(max_depth, depth)
                
                if depth not in collections_by_depth:
                    collections_by_depth[depth] = 0
                collections_by_depth[depth] += 1
            
            return {
                "total_collections": total_collections,
                "root_collections": root_collections,
                "nested_collections": total_collections - root_collections,
                "max_depth": max_depth,
                "collections_by_depth": collections_by_depth,
                "average_items_per_collection": round(float(avg_items_per_collection), 2),
                "largest_collection": {
                    "name": collection_with_most_items[0].collection_name if collection_with_most_items else None,
                    "item_count": collection_with_most_items[1] if collection_with_most_items else 0
                } if collection_with_most_items else None
            }
    
    def _calculate_collection_depth(self, collection_path: Optional[str]) -> int:
        """Calculate the depth of a collection based on its path"""
        if not collection_path:
            return 0
        return collection_path.count('/') + 1
    
    async def update_collection_paths(
        self,
        connection_id: str,
        library_id: str
    ) -> Dict[str, Any]:
        """
        Update collection paths for proper hierarchy
        
        Args:
            connection_id: Zotero connection ID
            library_id: Library ID
            
        Returns:
            Dictionary with update results
        """
        async with get_db() as db:
            # Get all collections for the library
            collections = db.query(ZoteroCollection).filter(
                ZoteroCollection.library_id == library_id
            ).all()
            
            # Create lookup map
            collection_map = {col.id: col for col in collections}
            
            updated_count = 0
            
            # Update paths for all collections
            for collection in collections:
                old_path = collection.collection_path
                new_path = self._build_collection_path(collection, collection_map)
                
                if old_path != new_path:
                    collection.collection_path = new_path
                    collection.updated_at = datetime.now()
                    updated_count += 1
            
            db.commit()
            
            return {
                "total_collections": len(collections),
                "updated_collections": updated_count,
                "message": f"Updated paths for {updated_count} collections"
            }
    
    def _build_collection_path(
        self,
        collection: ZoteroCollection,
        collection_map: Dict[str, ZoteroCollection]
    ) -> str:
        """Build hierarchical path for a collection"""
        
        path_parts = [collection.collection_name]
        current = collection
        
        # Walk up the hierarchy
        while current.parent_collection_id:
            parent = collection_map.get(current.parent_collection_id)
            if not parent:
                break  # Broken hierarchy
            
            path_parts.insert(0, parent.collection_name)
            current = parent
            
            # Prevent infinite loops
            if len(path_parts) > 10:
                logger.warning(f"Collection hierarchy too deep for {collection.collection_name}")
                break
        
        return "/".join(path_parts)
    
    async def get_collection_breadcrumbs(
        self,
        connection_id: str,
        library_id: str,
        collection_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get breadcrumb navigation for a collection
        
        Args:
            connection_id: Zotero connection ID
            library_id: Library ID
            collection_id: Collection ID
            
        Returns:
            List of breadcrumb items from root to current collection
        """
        async with get_db() as db:
            collection = db.query(ZoteroCollection).filter(
                and_(
                    ZoteroCollection.library_id == library_id,
                    ZoteroCollection.id == collection_id
                )
            ).first()
            
            if not collection:
                raise ValueError(f"Collection {collection_id} not found")
            
            breadcrumbs = []
            current = collection
            
            # Build breadcrumbs from current to root
            while current:
                breadcrumbs.insert(0, {
                    "id": current.id,
                    "name": current.collection_name,
                    "zotero_collection_key": current.zotero_collection_key
                })
                
                if current.parent_collection_id:
                    current = db.query(ZoteroCollection).filter(
                        ZoteroCollection.id == current.parent_collection_id
                    ).first()
                else:
                    current = None
            
            return breadcrumbs
    
    async def move_collection(
        self,
        connection_id: str,
        library_id: str,
        collection_id: str,
        new_parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Move a collection to a new parent (local operation only)
        
        Args:
            connection_id: Zotero connection ID
            library_id: Library ID
            collection_id: Collection ID to move
            new_parent_id: New parent collection ID (None for root level)
            
        Returns:
            Dictionary with move results
        """
        async with get_db() as db:
            collection = db.query(ZoteroCollection).filter(
                and_(
                    ZoteroCollection.library_id == library_id,
                    ZoteroCollection.id == collection_id
                )
            ).first()
            
            if not collection:
                raise ValueError(f"Collection {collection_id} not found")
            
            # Verify new parent exists if specified
            if new_parent_id:
                new_parent = db.query(ZoteroCollection).filter(
                    and_(
                        ZoteroCollection.library_id == library_id,
                        ZoteroCollection.id == new_parent_id
                    )
                ).first()
                
                if not new_parent:
                    raise ValueError(f"New parent collection {new_parent_id} not found")
                
                # Check for circular reference
                if await self._would_create_circular_reference(db, collection_id, new_parent_id):
                    raise ValueError("Move would create circular reference")
            
            # Update parent
            old_parent_id = collection.parent_collection_id
            collection.parent_collection_id = new_parent_id
            collection.updated_at = datetime.now()
            
            # Update path
            collection_map = {col.id: col for col in db.query(ZoteroCollection).filter(
                ZoteroCollection.library_id == library_id
            ).all()}
            collection.collection_path = self._build_collection_path(collection, collection_map)
            
            db.commit()
            
            # Update paths for all descendants
            await self._update_descendant_paths(db, collection_id, collection_map)
            
            return {
                "collection_id": collection_id,
                "old_parent_id": old_parent_id,
                "new_parent_id": new_parent_id,
                "new_path": collection.collection_path,
                "message": "Collection moved successfully"
            }
    
    async def _would_create_circular_reference(
        self,
        db: Session,
        collection_id: str,
        new_parent_id: str
    ) -> bool:
        """Check if moving collection would create circular reference"""
        
        current_id = new_parent_id
        visited = set()
        
        while current_id and current_id not in visited:
            if current_id == collection_id:
                return True  # Circular reference detected
            
            visited.add(current_id)
            
            parent = db.query(ZoteroCollection).filter(
                ZoteroCollection.id == current_id
            ).first()
            
            current_id = parent.parent_collection_id if parent else None
        
        return False
    
    async def _update_descendant_paths(
        self,
        db: Session,
        collection_id: str,
        collection_map: Dict[str, ZoteroCollection]
    ):
        """Update paths for all descendant collections"""
        
        descendants = db.query(ZoteroCollection).filter(
            ZoteroCollection.parent_collection_id == collection_id
        ).all()
        
        for descendant in descendants:
            descendant.collection_path = self._build_collection_path(descendant, collection_map)
            descendant.updated_at = datetime.now()
            
            # Recursively update grandchildren
            await self._update_descendant_paths(db, descendant.id, collection_map)
        
        db.commit()