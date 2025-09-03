"""
Zotero library synchronization service for importing and syncing library data
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.database import get_db
from models.zotero_models import (
    ZoteroConnection, ZoteroLibrary, ZoteroCollection, ZoteroItem,
    ZoteroItemCollection, ZoteroAttachment, ZoteroSyncLog
)
from models.zotero_schemas import SyncType, SyncStatus
from services.zotero.zotero_client import ZoteroAPIClient, ZoteroAPIError

logger = logging.getLogger(__name__)


class ZoteroSyncProgress:
    """Class to track synchronization progress"""
    
    def __init__(self, sync_id: str, sync_type: SyncType):
        self.sync_id = sync_id
        self.sync_type = sync_type
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.status = SyncStatus.STARTED
        
        # Progress counters
        self.libraries_processed = 0
        self.collections_processed = 0
        self.items_processed = 0
        self.items_added = 0
        self.items_updated = 0
        self.items_deleted = 0
        self.attachments_processed = 0
        self.errors_count = 0
        self.error_details: List[Dict[str, Any]] = []
        
        # Current operation info
        self.current_library: Optional[str] = None
        self.current_operation: Optional[str] = None
        self.estimated_total_items: Optional[int] = None
        
    def update_progress(self, **kwargs):
        """Update progress counters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def add_error(self, error: str, details: Optional[Dict[str, Any]] = None):
        """Add an error to the sync log"""
        self.errors_count += 1
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "library": self.current_library,
            "operation": self.current_operation
        }
        if details:
            error_entry["details"] = details
        self.error_details.append(error_entry)
        logger.error(f"Sync error in {self.sync_id}: {error}")
    
    def complete(self, status: SyncStatus = SyncStatus.COMPLETED):
        """Mark sync as completed"""
        self.status = status
        self.completed_at = datetime.now()
    
    def get_progress_dict(self) -> Dict[str, Any]:
        """Get progress as dictionary"""
        duration = None
        if self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            duration = (datetime.now() - self.started_at).total_seconds()
        
        return {
            "sync_id": self.sync_id,
            "sync_type": self.sync_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": duration,
            "progress": {
                "libraries_processed": self.libraries_processed,
                "collections_processed": self.collections_processed,
                "items_processed": self.items_processed,
                "items_added": self.items_added,
                "items_updated": self.items_updated,
                "items_deleted": self.items_deleted,
                "attachments_processed": self.attachments_processed,
                "estimated_total_items": self.estimated_total_items
            },
            "errors": {
                "count": self.errors_count,
                "details": self.error_details[-10:]  # Last 10 errors
            },
            "current_operation": {
                "library": self.current_library,
                "operation": self.current_operation
            }
        }


class ZoteroLibrarySyncService:
    """Service for synchronizing Zotero libraries"""
    
    def __init__(self):
        self.client = ZoteroAPIClient()
        self._active_syncs: Dict[str, ZoteroSyncProgress] = {}
        
    async def import_library(
        self,
        connection_id: str,
        library_ids: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None
    ) -> ZoteroSyncProgress:
        """
        Import library data from Zotero
        
        Args:
            connection_id: Zotero connection ID
            library_ids: Specific library IDs to import (None for all)
            progress_callback: Optional callback for progress updates
            
        Returns:
            ZoteroSyncProgress object with import results
        """
        # Create sync progress tracker
        sync_id = f"import_{connection_id}_{int(datetime.now().timestamp())}"
        progress = ZoteroSyncProgress(sync_id, SyncType.FULL)
        self._active_syncs[sync_id] = progress
        
        try:
            async with get_db() as db:
                # Get connection details
                connection = db.query(ZoteroConnection).filter(
                    ZoteroConnection.id == connection_id
                ).first()
                
                if not connection:
                    raise ValueError(f"Connection {connection_id} not found")
                
                if connection.connection_status != "active":
                    raise ValueError(f"Connection {connection_id} is not active")
                
                # Create sync log entry
                sync_log = ZoteroSyncLog(
                    connection_id=connection_id,
                    sync_type=SyncType.FULL.value,
                    sync_status=SyncStatus.IN_PROGRESS.value,
                    started_at=progress.started_at
                )
                db.add(sync_log)
                db.commit()
                
                progress.update_progress(status=SyncStatus.IN_PROGRESS)
                
                # Get available libraries
                async with self.client as api_client:
                    libraries = await api_client.get_libraries(
                        connection.access_token,
                        connection.zotero_user_id
                    )
                    
                    # Filter libraries if specific IDs provided
                    if library_ids:
                        libraries = [lib for lib in libraries if lib["id"] in library_ids]
                    
                    logger.info(f"Found {len(libraries)} libraries to import")
                    
                    # Import each library
                    for library_data in libraries:
                        try:
                            progress.current_library = library_data["name"]
                            progress.current_operation = "importing_library"
                            
                            if progress_callback:
                                await progress_callback(progress.get_progress_dict())
                            
                            await self._import_single_library(
                                db, api_client, connection, library_data, progress
                            )
                            
                            progress.libraries_processed += 1
                            
                        except Exception as e:
                            progress.add_error(
                                f"Failed to import library {library_data['name']}: {str(e)}",
                                {"library_id": library_data["id"], "library_type": library_data["type"]}
                            )
                            continue
                
                # Update sync log
                progress.complete()
                sync_log.sync_status = progress.status.value
                sync_log.completed_at = progress.completed_at
                sync_log.items_processed = progress.items_processed
                sync_log.items_added = progress.items_added
                sync_log.items_updated = progress.items_updated
                sync_log.items_deleted = progress.items_deleted
                sync_log.errors_count = progress.errors_count
                sync_log.error_details = progress.error_details
                
                db.commit()
                
                # Update connection last sync time
                connection.last_sync_at = progress.completed_at
                db.commit()
                
                logger.info(f"Library import completed: {progress.get_progress_dict()}")
                
        except Exception as e:
            progress.add_error(f"Library import failed: {str(e)}")
            progress.complete(SyncStatus.FAILED)
            logger.error(f"Library import failed for connection {connection_id}: {e}")
            
        finally:
            # Clean up active sync tracking
            if sync_id in self._active_syncs:
                del self._active_syncs[sync_id]
        
        return progress
    
    async def _import_single_library(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library_data: Dict[str, Any],
        progress: ZoteroSyncProgress
    ):
        """Import a single library with all its collections and items"""
        
        # Create or update library record
        library = db.query(ZoteroLibrary).filter(
            and_(
                ZoteroLibrary.connection_id == connection.id,
                ZoteroLibrary.zotero_library_id == library_data["id"]
            )
        ).first()
        
        if not library:
            library = ZoteroLibrary(
                connection_id=connection.id,
                zotero_library_id=library_data["id"],
                library_type=library_data["type"],
                library_name=library_data["name"],
                owner_id=library_data.get("owner"),
                group_id=library_data.get("id") if library_data["type"] == "group" else None
            )
            db.add(library)
            db.flush()  # Get the ID
        else:
            # Update existing library
            library.library_name = library_data["name"]
            library.is_active = True
        
        # Import collections
        progress.current_operation = "importing_collections"
        await self._import_library_collections(
            db, api_client, connection, library, progress
        )
        
        # Import items
        progress.current_operation = "importing_items"
        await self._import_library_items(
            db, api_client, connection, library, progress
        )
        
        # Update library sync timestamp
        library.last_sync_at = datetime.now()
        db.commit()
    
    async def _import_library_collections(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        progress: ZoteroSyncProgress
    ):
        """Import collections for a library"""
        
        try:
            collections_data = await api_client.get_collections(
                connection.access_token,
                library.library_type,
                library.zotero_library_id
            )
            
            logger.info(f"Importing {len(collections_data)} collections for library {library.library_name}")
            
            # Create a mapping of collection keys to process hierarchy
            collection_map = {}
            
            for collection_data in collections_data:
                try:
                    collection_key = collection_data["key"]
                    collection_version = collection_data["version"]
                    data = collection_data["data"]
                    
                    # Check if collection already exists
                    existing_collection = db.query(ZoteroCollection).filter(
                        and_(
                            ZoteroCollection.library_id == library.id,
                            ZoteroCollection.zotero_collection_key == collection_key
                        )
                    ).first()
                    
                    if existing_collection:
                        # Update existing collection
                        existing_collection.collection_name = data["name"]
                        existing_collection.collection_version = collection_version
                        collection_map[collection_key] = existing_collection
                    else:
                        # Create new collection
                        new_collection = ZoteroCollection(
                            library_id=library.id,
                            zotero_collection_key=collection_key,
                            collection_name=data["name"],
                            collection_version=collection_version,
                            collection_metadata=data
                        )
                        db.add(new_collection)
                        db.flush()  # Get the ID
                        collection_map[collection_key] = new_collection
                    
                    progress.collections_processed += 1
                    
                except Exception as e:
                    progress.add_error(
                        f"Failed to import collection: {str(e)}",
                        {"collection_key": collection_data.get("key")}
                    )
                    continue
            
            # Process parent-child relationships
            for collection_data in collections_data:
                try:
                    collection_key = collection_data["key"]
                    data = collection_data["data"]
                    parent_collection_key = data.get("parentCollection")
                    
                    if parent_collection_key and parent_collection_key in collection_map:
                        child_collection = collection_map[collection_key]
                        parent_collection = collection_map[parent_collection_key]
                        child_collection.parent_collection_id = parent_collection.id
                        
                        # Update collection path for efficient queries
                        if parent_collection.collection_path:
                            child_collection.collection_path = f"{parent_collection.collection_path}/{child_collection.collection_name}"
                        else:
                            child_collection.collection_path = f"{parent_collection.collection_name}/{child_collection.collection_name}"
                
                except Exception as e:
                    progress.add_error(
                        f"Failed to set collection hierarchy: {str(e)}",
                        {"collection_key": collection_data.get("key")}
                    )
                    continue
            
            db.commit()
            
        except Exception as e:
            progress.add_error(f"Failed to import collections: {str(e)}")
            raise
    
    async def _import_library_items(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        progress: ZoteroSyncProgress
    ):
        """Import items for a library with pagination"""
        
        try:
            # Get items in batches
            batch_size = 100
            start = 0
            total_items = 0
            
            while True:
                items_data = await api_client.get_items(
                    connection.access_token,
                    library.library_type,
                    library.zotero_library_id,
                    limit=batch_size,
                    start=start
                )
                
                if not items_data:
                    break
                
                logger.info(f"Processing batch of {len(items_data)} items (start: {start})")
                
                for item_data in items_data:
                    try:
                        await self._import_single_item(
                            db, api_client, connection, library, item_data, progress
                        )
                        progress.items_processed += 1
                        total_items += 1
                        
                    except Exception as e:
                        progress.add_error(
                            f"Failed to import item: {str(e)}",
                            {"item_key": item_data.get("key")}
                        )
                        continue
                
                # Check if we got fewer items than requested (end of results)
                if len(items_data) < batch_size:
                    break
                
                start += batch_size
                
                # Commit periodically to avoid large transactions
                if total_items % 500 == 0:
                    db.commit()
                    logger.info(f"Committed {total_items} items so far")
            
            db.commit()
            logger.info(f"Imported {total_items} items for library {library.library_name}")
            
        except Exception as e:
            progress.add_error(f"Failed to import items: {str(e)}")
            raise
    
    async def _import_single_item(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        item_data: Dict[str, Any],
        progress: ZoteroSyncProgress
    ):
        """Import a single item with its metadata"""
        
        item_key = item_data["key"]
        item_version = item_data["version"]
        data = item_data["data"]
        
        # Check if item already exists
        existing_item = db.query(ZoteroItem).filter(
            and_(
                ZoteroItem.library_id == library.id,
                ZoteroItem.zotero_item_key == item_key
            )
        ).first()
        
        # Transform Zotero data to our format
        transformed_data = self._transform_item_data(data)
        
        if existing_item:
            # Update existing item
            if existing_item.item_version < item_version:
                self._update_item_from_data(existing_item, transformed_data, item_version)
                progress.items_updated += 1
        else:
            # Create new item
            new_item = ZoteroItem(
                library_id=library.id,
                zotero_item_key=item_key,
                item_version=item_version,
                **transformed_data
            )
            db.add(new_item)
            db.flush()  # Get the ID
            progress.items_added += 1
            
            # Handle collections
            collections = item_data.get("data", {}).get("collections", [])
            if collections:
                await self._link_item_to_collections(db, new_item, collections, library)
    
    def _transform_item_data(self, zotero_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Zotero item data to our internal format"""
        
        # Extract creators (authors, editors, etc.)
        creators = []
        for creator in zotero_data.get("creators", []):
            creator_data = {
                "creator_type": creator.get("creatorType", "author"),
                "first_name": creator.get("firstName"),
                "last_name": creator.get("lastName"),
                "name": creator.get("name")  # For organizations
            }
            creators.append(creator_data)
        
        # Extract publication year from date
        publication_year = None
        date_str = zotero_data.get("date", "")
        if date_str:
            # Try to extract year from various date formats
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
            if year_match:
                publication_year = int(year_match.group())
        
        # Map Zotero fields to our schema
        transformed = {
            "item_type": zotero_data.get("itemType", "unknown"),
            "title": zotero_data.get("title"),
            "creators": creators,
            "publication_title": zotero_data.get("publicationTitle") or zotero_data.get("bookTitle"),
            "publication_year": publication_year,
            "publisher": zotero_data.get("publisher"),
            "doi": zotero_data.get("DOI"),
            "isbn": zotero_data.get("ISBN"),
            "issn": zotero_data.get("ISSN"),
            "url": zotero_data.get("url"),
            "abstract_note": zotero_data.get("abstractNote"),
            "date_added": self._parse_zotero_date(zotero_data.get("dateAdded")),
            "date_modified": self._parse_zotero_date(zotero_data.get("dateModified")),
            "tags": [tag["tag"] for tag in zotero_data.get("tags", [])],
            "extra_fields": {
                k: v for k, v in zotero_data.items()
                if k not in [
                    "itemType", "title", "creators", "publicationTitle", "bookTitle",
                    "publisher", "DOI", "ISBN", "ISSN", "url", "abstractNote",
                    "dateAdded", "dateModified", "tags", "collections", "relations"
                ]
            },
            "item_metadata": zotero_data
        }
        
        return transformed
    
    def _update_item_from_data(
        self,
        item: ZoteroItem,
        transformed_data: Dict[str, Any],
        version: int
    ):
        """Update existing item with new data"""
        
        for field, value in transformed_data.items():
            if hasattr(item, field):
                setattr(item, field, value)
        
        item.item_version = version
        item.updated_at = datetime.now()
    
    async def _link_item_to_collections(
        self,
        db: Session,
        item: ZoteroItem,
        collection_keys: List[str],
        library: ZoteroLibrary
    ):
        """Link an item to its collections"""
        
        for collection_key in collection_keys:
            # Find the collection
            collection = db.query(ZoteroCollection).filter(
                and_(
                    ZoteroCollection.library_id == library.id,
                    ZoteroCollection.zotero_collection_key == collection_key
                )
            ).first()
            
            if collection:
                # Check if link already exists
                existing_link = db.query(ZoteroItemCollection).filter(
                    and_(
                        ZoteroItemCollection.item_id == item.id,
                        ZoteroItemCollection.collection_id == collection.id
                    )
                ).first()
                
                if not existing_link:
                    link = ZoteroItemCollection(
                        item_id=item.id,
                        collection_id=collection.id
                    )
                    db.add(link)
    
    def _parse_zotero_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Zotero date string to datetime"""
        if not date_str:
            return None
        
        try:
            # Zotero uses ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def get_sync_progress(self, sync_id: str) -> Optional[Dict[str, Any]]:
        """Get progress for an active sync"""
        if sync_id in self._active_syncs:
            return self._active_syncs[sync_id].get_progress_dict()
        return None
    
    def get_active_syncs(self) -> List[Dict[str, Any]]:
        """Get all active syncs"""
        return [progress.get_progress_dict() for progress in self._active_syncs.values()]
    
    async def incremental_sync(
        self,
        connection_id: str,
        library_ids: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None
    ) -> ZoteroSyncProgress:
        """
        Perform incremental synchronization with Zotero
        
        Args:
            connection_id: Zotero connection ID
            library_ids: Specific library IDs to sync (None for all)
            progress_callback: Optional callback for progress updates
            
        Returns:
            ZoteroSyncProgress object with sync results
        """
        # Create sync progress tracker
        sync_id = f"incremental_{connection_id}_{int(datetime.now().timestamp())}"
        progress = ZoteroSyncProgress(sync_id, SyncType.INCREMENTAL)
        self._active_syncs[sync_id] = progress
        
        try:
            async with get_db() as db:
                # Get connection details
                connection = db.query(ZoteroConnection).filter(
                    ZoteroConnection.id == connection_id
                ).first()
                
                if not connection:
                    raise ValueError(f"Connection {connection_id} not found")
                
                if connection.connection_status != "active":
                    raise ValueError(f"Connection {connection_id} is not active")
                
                # Create sync log entry
                sync_log = ZoteroSyncLog(
                    connection_id=connection_id,
                    sync_type=SyncType.INCREMENTAL.value,
                    sync_status=SyncStatus.IN_PROGRESS.value,
                    started_at=progress.started_at
                )
                db.add(sync_log)
                db.commit()
                
                progress.update_progress(status=SyncStatus.IN_PROGRESS)
                
                # Get libraries to sync
                libraries_query = db.query(ZoteroLibrary).filter(
                    ZoteroLibrary.connection_id == connection_id,
                    ZoteroLibrary.is_active == True
                )
                
                if library_ids:
                    libraries_query = libraries_query.filter(
                        ZoteroLibrary.zotero_library_id.in_(library_ids)
                    )
                
                libraries = libraries_query.all()
                
                if not libraries:
                    logger.warning(f"No libraries found for incremental sync: {connection_id}")
                    progress.complete()
                    return progress
                
                logger.info(f"Starting incremental sync for {len(libraries)} libraries")
                
                # Sync each library incrementally
                async with self.client as api_client:
                    for library in libraries:
                        try:
                            progress.current_library = library.library_name
                            progress.current_operation = "incremental_sync"
                            
                            if progress_callback:
                                await progress_callback(progress.get_progress_dict())
                            
                            await self._incremental_sync_library(
                                db, api_client, connection, library, progress
                            )
                            
                            progress.libraries_processed += 1
                            
                        except Exception as e:
                            progress.add_error(
                                f"Failed to sync library {library.library_name}: {str(e)}",
                                {"library_id": library.zotero_library_id}
                            )
                            continue
                
                # Update sync log
                progress.complete()
                sync_log.sync_status = progress.status.value
                sync_log.completed_at = progress.completed_at
                sync_log.items_processed = progress.items_processed
                sync_log.items_added = progress.items_added
                sync_log.items_updated = progress.items_updated
                sync_log.items_deleted = progress.items_deleted
                sync_log.errors_count = progress.errors_count
                sync_log.error_details = progress.error_details
                
                db.commit()
                
                # Update connection last sync time
                connection.last_sync_at = progress.completed_at
                db.commit()
                
                logger.info(f"Incremental sync completed: {progress.get_progress_dict()}")
                
        except Exception as e:
            progress.add_error(f"Incremental sync failed: {str(e)}")
            progress.complete(SyncStatus.FAILED)
            logger.error(f"Incremental sync failed for connection {connection_id}: {e}")
            
        finally:
            # Clean up active sync tracking
            if sync_id in self._active_syncs:
                del self._active_syncs[sync_id]
        
        return progress
    
    async def _incremental_sync_library(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        progress: ZoteroSyncProgress
    ):
        """Perform incremental sync for a single library"""
        
        # Get current library version from Zotero
        try:
            current_version = await api_client.get_library_version(
                connection.access_token,
                library.library_type,
                library.zotero_library_id
            )
        except Exception as e:
            logger.warning(f"Could not get library version, falling back to full sync: {e}")
            # Fall back to full sync for this library
            await self._import_single_library(db, api_client, connection, {"id": library.zotero_library_id, "type": library.library_type, "name": library.library_name}, progress)
            return
        
        # Check if library needs sync
        if current_version <= library.library_version:
            logger.info(f"Library {library.library_name} is up to date (version {library.library_version})")
            return
        
        logger.info(f"Syncing library {library.library_name} from version {library.library_version} to {current_version}")
        
        # Get items modified since last sync
        since_version = library.library_version
        
        try:
            # Sync collections first
            await self._incremental_sync_collections(
                db, api_client, connection, library, since_version, progress
            )
            
            # Sync items
            await self._incremental_sync_items(
                db, api_client, connection, library, since_version, progress
            )
            
            # Update library version
            library.library_version = current_version
            library.last_sync_at = datetime.now()
            db.commit()
            
        except Exception as e:
            progress.add_error(f"Failed to sync library {library.library_name}: {str(e)}")
            raise
    
    async def _incremental_sync_collections(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        since_version: int,
        progress: ZoteroSyncProgress
    ):
        """Sync collections modified since last sync"""
        
        try:
            # Get collections modified since last sync
            collections_data = await api_client.get_collections(
                connection.access_token,
                library.library_type,
                library.zotero_library_id,
                since=since_version
            )
            
            if not collections_data:
                logger.info(f"No collection changes for library {library.library_name}")
                return
            
            logger.info(f"Syncing {len(collections_data)} modified collections for library {library.library_name}")
            
            # Process each collection
            collection_map = {}
            for collection_data in collections_data:
                try:
                    collection_key = collection_data["key"]
                    collection_version = collection_data["version"]
                    data = collection_data["data"]
                    
                    # Check if collection is deleted
                    if data.get("deleted", False):
                        await self._handle_deleted_collection(db, library, collection_key, progress)
                        continue
                    
                    # Find existing collection
                    existing_collection = db.query(ZoteroCollection).filter(
                        and_(
                            ZoteroCollection.library_id == library.id,
                            ZoteroCollection.zotero_collection_key == collection_key
                        )
                    ).first()
                    
                    if existing_collection:
                        # Update existing collection
                        if existing_collection.collection_version < collection_version:
                            existing_collection.collection_name = data["name"]
                            existing_collection.collection_version = collection_version
                            existing_collection.collection_metadata = data
                            existing_collection.updated_at = datetime.now()
                            collection_map[collection_key] = existing_collection
                    else:
                        # Create new collection
                        new_collection = ZoteroCollection(
                            library_id=library.id,
                            zotero_collection_key=collection_key,
                            collection_name=data["name"],
                            collection_version=collection_version,
                            collection_metadata=data
                        )
                        db.add(new_collection)
                        db.flush()  # Get the ID
                        collection_map[collection_key] = new_collection
                    
                    progress.collections_processed += 1
                    
                except Exception as e:
                    progress.add_error(
                        f"Failed to sync collection: {str(e)}",
                        {"collection_key": collection_data.get("key")}
                    )
                    continue
            
            # Update collection hierarchy
            await self._update_collection_hierarchy(db, collection_map, collections_data)
            
            db.commit()
            
        except Exception as e:
            progress.add_error(f"Failed to sync collections: {str(e)}")
            raise
    
    async def _incremental_sync_items(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        since_version: int,
        progress: ZoteroSyncProgress
    ):
        """Sync items modified since last sync"""
        
        try:
            # Get items modified since last sync in batches
            batch_size = 100
            start = 0
            
            while True:
                items_data = await api_client.get_items(
                    connection.access_token,
                    library.library_type,
                    library.zotero_library_id,
                    limit=batch_size,
                    start=start,
                    since=since_version
                )
                
                if not items_data:
                    break
                
                logger.info(f"Processing batch of {len(items_data)} modified items (start: {start})")
                
                for item_data in items_data:
                    try:
                        await self._sync_single_item(
                            db, api_client, connection, library, item_data, progress
                        )
                        progress.items_processed += 1
                        
                    except Exception as e:
                        progress.add_error(
                            f"Failed to sync item: {str(e)}",
                            {"item_key": item_data.get("key")}
                        )
                        continue
                
                # Check if we got fewer items than requested (end of results)
                if len(items_data) < batch_size:
                    break
                
                start += batch_size
                
                # Commit periodically to avoid large transactions
                if start % 500 == 0:
                    db.commit()
                    logger.info(f"Committed {start} items so far")
            
            db.commit()
            
        except Exception as e:
            progress.add_error(f"Failed to sync items: {str(e)}")
            raise
    
    async def _sync_single_item(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        item_data: Dict[str, Any],
        progress: ZoteroSyncProgress
    ):
        """Sync a single item with conflict resolution"""
        
        item_key = item_data["key"]
        item_version = item_data["version"]
        data = item_data["data"]
        
        # Find existing item
        existing_item = db.query(ZoteroItem).filter(
            and_(
                ZoteroItem.library_id == library.id,
                ZoteroItem.zotero_item_key == item_key
            )
        ).first()
        
        # Check if item is deleted
        if data.get("deleted", False):
            if existing_item:
                existing_item.is_deleted = True
                existing_item.item_version = item_version
                existing_item.updated_at = datetime.now()
                progress.items_deleted += 1
            return
        
        # Transform Zotero data to our format
        transformed_data = self._transform_item_data(data)
        
        if existing_item:
            # Update existing item (Zotero wins conflict resolution)
            if existing_item.item_version < item_version:
                self._update_item_from_data(existing_item, transformed_data, item_version)
                
                # Update item collections
                collections = data.get("collections", [])
                await self._update_item_collections(db, existing_item, collections, library)
                
                progress.items_updated += 1
            # If versions are equal or local is newer, skip (shouldn't happen in normal sync)
        else:
            # Create new item
            new_item = ZoteroItem(
                library_id=library.id,
                zotero_item_key=item_key,
                item_version=item_version,
                **transformed_data
            )
            db.add(new_item)
            db.flush()  # Get the ID
            
            # Link to collections
            collections = data.get("collections", [])
            if collections:
                await self._link_item_to_collections(db, new_item, collections, library)
            
            progress.items_added += 1
    
    async def _handle_deleted_collection(
        self,
        db: Session,
        library: ZoteroLibrary,
        collection_key: str,
        progress: ZoteroSyncProgress
    ):
        """Handle deletion of a collection"""
        
        collection = db.query(ZoteroCollection).filter(
            and_(
                ZoteroCollection.library_id == library.id,
                ZoteroCollection.zotero_collection_key == collection_key
            )
        ).first()
        
        if collection:
            # Remove item-collection associations
            db.query(ZoteroItemCollection).filter(
                ZoteroItemCollection.collection_id == collection.id
            ).delete()
            
            # Delete the collection
            db.delete(collection)
            logger.info(f"Deleted collection {collection.collection_name}")
    
    async def _update_collection_hierarchy(
        self,
        db: Session,
        collection_map: Dict[str, ZoteroCollection],
        collections_data: List[Dict[str, Any]]
    ):
        """Update collection parent-child relationships"""
        
        for collection_data in collections_data:
            try:
                collection_key = collection_data["key"]
                data = collection_data["data"]
                parent_collection_key = data.get("parentCollection")
                
                if collection_key in collection_map:
                    collection = collection_map[collection_key]
                    
                    if parent_collection_key and parent_collection_key in collection_map:
                        parent_collection = collection_map[parent_collection_key]
                        collection.parent_collection_id = parent_collection.id
                        
                        # Update collection path
                        if parent_collection.collection_path:
                            collection.collection_path = f"{parent_collection.collection_path}/{collection.collection_name}"
                        else:
                            collection.collection_path = f"{parent_collection.collection_name}/{collection.collection_name}"
                    else:
                        # Root collection
                        collection.parent_collection_id = None
                        collection.collection_path = collection.collection_name
                        
            except Exception as e:
                logger.error(f"Failed to update collection hierarchy for {collection_key}: {e}")
                continue
    
    async def _update_item_collections(
        self,
        db: Session,
        item: ZoteroItem,
        collection_keys: List[str],
        library: ZoteroLibrary
    ):
        """Update item collection associations"""
        
        # Remove existing associations
        db.query(ZoteroItemCollection).filter(
            ZoteroItemCollection.item_id == item.id
        ).delete()
        
        # Add new associations
        for collection_key in collection_keys:
            collection = db.query(ZoteroCollection).filter(
                and_(
                    ZoteroCollection.library_id == library.id,
                    ZoteroCollection.zotero_collection_key == collection_key
                )
            ).first()
            
            if collection:
                link = ZoteroItemCollection(
                    item_id=item.id,
                    collection_id=collection.id
                )
                db.add(link)
    
    async def detect_sync_conflicts(
        self,
        connection_id: str,
        library_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect potential sync conflicts before performing sync
        
        Args:
            connection_id: Zotero connection ID
            library_ids: Specific library IDs to check (None for all)
            
        Returns:
            Dictionary with conflict information
        """
        conflicts = {
            "has_conflicts": False,
            "total_conflicts": 0,
            "conflict_types": {
                "version_mismatch": 0,
                "deleted_items": 0,
                "modified_items": 0
            },
            "libraries": []
        }
        
        try:
            async with get_db() as db:
                # Get connection
                connection = db.query(ZoteroConnection).filter(
                    ZoteroConnection.id == connection_id
                ).first()
                
                if not connection:
                    raise ValueError(f"Connection {connection_id} not found")
                
                # Get libraries to check
                libraries_query = db.query(ZoteroLibrary).filter(
                    ZoteroLibrary.connection_id == connection_id,
                    ZoteroLibrary.is_active == True
                )
                
                if library_ids:
                    libraries_query = libraries_query.filter(
                        ZoteroLibrary.zotero_library_id.in_(library_ids)
                    )
                
                libraries = libraries_query.all()
                
                async with self.client as api_client:
                    for library in libraries:
                        library_conflicts = await self._detect_library_conflicts(
                            api_client, connection, library
                        )
                        
                        if library_conflicts["conflict_count"] > 0:
                            conflicts["has_conflicts"] = True
                            conflicts["total_conflicts"] += library_conflicts["conflict_count"]
                            
                            # Update conflict type counts
                            for conflict_type, count in library_conflicts["conflict_types"].items():
                                conflicts["conflict_types"][conflict_type] += count
                            
                            conflicts["libraries"].append(library_conflicts)
                
        except Exception as e:
            logger.error(f"Failed to detect sync conflicts: {e}")
            conflicts["error"] = str(e)
        
        return conflicts
    
    async def _detect_library_conflicts(
        self,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary
    ) -> Dict[str, Any]:
        """Detect conflicts for a single library"""
        
        library_conflicts = {
            "library_id": library.id,
            "library_name": library.library_name,
            "conflict_count": 0,
            "conflict_types": {
                "version_mismatch": 0,
                "deleted_items": 0,
                "modified_items": 0
            },
            "conflicts": []
        }
        
        try:
            # Get current library version
            current_version = await api_client.get_library_version(
                connection.access_token,
                library.library_type,
                library.zotero_library_id
            )
            
            # Check version mismatch
            if current_version > library.library_version:
                library_conflicts["conflict_count"] += 1
                library_conflicts["conflict_types"]["version_mismatch"] = 1
                library_conflicts["conflicts"].append({
                    "type": "version_mismatch",
                    "description": f"Library version mismatch: local {library.library_version}, remote {current_version}",
                    "local_version": library.library_version,
                    "remote_version": current_version
                })
                
                # Get modified items since last sync
                modified_items = await api_client.get_items(
                    connection.access_token,
                    library.library_type,
                    library.zotero_library_id,
                    since=library.library_version,
                    limit=100  # Limit for conflict detection
                )
                
                for item_data in modified_items:
                    data = item_data["data"]
                    if data.get("deleted", False):
                        library_conflicts["conflict_count"] += 1
                        library_conflicts["conflict_types"]["deleted_items"] += 1
                        library_conflicts["conflicts"].append({
                            "type": "deleted_item",
                            "description": f"Item deleted in Zotero: {data.get('title', 'Untitled')}",
                            "item_key": item_data["key"],
                            "item_title": data.get("title", "Untitled")
                        })
                    else:
                        library_conflicts["conflict_count"] += 1
                        library_conflicts["conflict_types"]["modified_items"] += 1
                        library_conflicts["conflicts"].append({
                            "type": "modified_item",
                            "description": f"Item modified in Zotero: {data.get('title', 'Untitled')}",
                            "item_key": item_data["key"],
                            "item_title": data.get("title", "Untitled"),
                            "item_version": item_data["version"]
                        })
                
        except Exception as e:
            logger.error(f"Failed to detect conflicts for library {library.library_name}: {e}")
            library_conflicts["error"] = str(e)
        
        return library_conflicts
    
    async def resolve_sync_conflicts(
        self,
        connection_id: str,
        resolution_strategy: str = "zotero_wins",
        library_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Resolve sync conflicts using specified strategy
        
        Args:
            connection_id: Zotero connection ID
            resolution_strategy: Strategy for conflict resolution
            library_ids: Specific library IDs to resolve (None for all)
            
        Returns:
            Dictionary with resolution results
        """
        result = {
            "strategy": resolution_strategy,
            "resolved": False,
            "message": "",
            "sync_result": None
        }
        
        try:
            if resolution_strategy == "zotero_wins":
                # Zotero wins: perform incremental sync (overwrites local changes)
                sync_progress = await self.incremental_sync(
                    connection_id, library_ids
                )
                result["resolved"] = True
                result["message"] = "Conflicts resolved by accepting Zotero changes"
                result["sync_result"] = sync_progress.get_progress_dict()
                
            elif resolution_strategy == "local_wins":
                # Local wins: not yet implemented
                result["message"] = "Local wins strategy not yet implemented"
                
            elif resolution_strategy == "merge":
                # Merge strategy: not yet implemented
                result["message"] = "Merge strategy not yet implemented"
                
            else:
                result["message"] = f"Unknown resolution strategy: {resolution_strategy}"
                
        except Exception as e:
            result["message"] = f"Failed to resolve conflicts: {str(e)}"
            logger.error(f"Failed to resolve sync conflicts: {e}")
        
        return resultsion = 0
        
        # Check if sync is needed
        if current_version <= library.library_version:
            logger.info(f"Library {library.library_name} is up to date (version {library.library_version})")
            return
        
        logger.info(f"Syncing library {library.library_name} from version {library.library_version} to {current_version}")
        
        # Sync collections incrementally
        progress.current_operation = "syncing_collections"
        await self._incremental_sync_collections(
            db, api_client, connection, library, progress
        )
        
        # Sync items incrementally
        progress.current_operation = "syncing_items"
        await self._incremental_sync_items(
            db, api_client, connection, library, progress
        )
        
        # Update library version
        library.library_version = current_version
        library.last_sync_at = datetime.now()
        db.commit()
    
    async def _incremental_sync_collections(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        progress: ZoteroSyncProgress
    ):
        """Incrementally sync collections"""
        
        try:
            # Get collections modified since last sync
            collections_data = await api_client.get_collections(
                connection.access_token,
                library.library_type,
                library.zotero_library_id,
                since_version=library.library_version
            )
            
            logger.info(f"Found {len(collections_data)} modified collections")
            
            for collection_data in collections_data:
                try:
                    await self._sync_single_collection(
                        db, collection_data, library, progress
                    )
                    progress.collections_processed += 1
                    
                except Exception as e:
                    progress.add_error(
                        f"Failed to sync collection: {str(e)}",
                        {"collection_key": collection_data.get("key")}
                    )
                    continue
            
            db.commit()
            
        except Exception as e:
            progress.add_error(f"Failed to sync collections: {str(e)}")
            raise
    
    async def _sync_single_collection(
        self,
        db: Session,
        collection_data: Dict[str, Any],
        library: ZoteroLibrary,
        progress: ZoteroSyncProgress
    ):
        """Sync a single collection with conflict resolution"""
        
        collection_key = collection_data["key"]
        collection_version = collection_data["version"]
        data = collection_data["data"]
        
        # Check if collection exists
        existing_collection = db.query(ZoteroCollection).filter(
            and_(
                ZoteroCollection.library_id == library.id,
                ZoteroCollection.zotero_collection_key == collection_key
            )
        ).first()
        
        if existing_collection:
            # Handle conflict resolution - Zotero is source of truth
            if collection_version > existing_collection.collection_version:
                # Update existing collection
                existing_collection.collection_name = data["name"]
                existing_collection.collection_version = collection_version
                existing_collection.collection_metadata = data
                existing_collection.updated_at = datetime.now()
                
                logger.debug(f"Updated collection {collection_key} to version {collection_version}")
            else:
                logger.debug(f"Collection {collection_key} is up to date")
        else:
            # Create new collection
            new_collection = ZoteroCollection(
                library_id=library.id,
                zotero_collection_key=collection_key,
                collection_name=data["name"],
                collection_version=collection_version,
                collection_metadata=data
            )
            db.add(new_collection)
            logger.debug(f"Created new collection {collection_key}")
    
    async def _incremental_sync_items(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        progress: ZoteroSyncProgress
    ):
        """Incrementally sync items"""
        
        try:
            # Get items modified since last sync
            batch_size = 100
            start = 0
            
            while True:
                items_data = await api_client.get_items(
                    connection.access_token,
                    library.library_type,
                    library.zotero_library_id,
                    since_version=library.library_version,
                    limit=batch_size,
                    start=start
                )
                
                if not items_data:
                    break
                
                logger.info(f"Processing batch of {len(items_data)} modified items (start: {start})")
                
                for item_data in items_data:
                    try:
                        await self._sync_single_item(
                            db, api_client, connection, library, item_data, progress
                        )
                        progress.items_processed += 1
                        
                    except Exception as e:
                        progress.add_error(
                            f"Failed to sync item: {str(e)}",
                            {"item_key": item_data.get("key")}
                        )
                        continue
                
                # Check if we got fewer items than requested (end of results)
                if len(items_data) < batch_size:
                    break
                
                start += batch_size
                
                # Commit periodically
                if progress.items_processed % 100 == 0:
                    db.commit()
            
            db.commit()
            
        except Exception as e:
            progress.add_error(f"Failed to sync items: {str(e)}")
            raise
    
    async def _sync_single_item(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        item_data: Dict[str, Any],
        progress: ZoteroSyncProgress
    ):
        """Sync a single item with conflict resolution"""
        
        item_key = item_data["key"]
        item_version = item_data["version"]
        data = item_data["data"]
        
        # Check if item exists
        existing_item = db.query(ZoteroItem).filter(
            and_(
                ZoteroItem.library_id == library.id,
                ZoteroItem.zotero_item_key == item_key
            )
        ).first()
        
        # Transform Zotero data to our format
        transformed_data = self._transform_item_data(data)
        
        if existing_item:
            # Handle conflict resolution - Zotero is source of truth
            if item_version > existing_item.item_version:
                # Check if item was deleted in Zotero
                if data.get("deleted", False):
                    existing_item.is_deleted = True
                    existing_item.item_version = item_version
                    existing_item.updated_at = datetime.now()
                    progress.items_deleted += 1
                    logger.debug(f"Marked item {item_key} as deleted")
                else:
                    # Update existing item
                    self._update_item_from_data(existing_item, transformed_data, item_version)
                    progress.items_updated += 1
                    logger.debug(f"Updated item {item_key} to version {item_version}")
                    
                    # Update collections
                    collections = data.get("collections", [])
                    await self._update_item_collections(db, existing_item, collections, library)
            else:
                logger.debug(f"Item {item_key} is up to date")
        else:
            # Create new item (unless it's deleted)
            if not data.get("deleted", False):
                new_item = ZoteroItem(
                    library_id=library.id,
                    zotero_item_key=item_key,
                    item_version=item_version,
                    **transformed_data
                )
                db.add(new_item)
                db.flush()  # Get the ID
                progress.items_added += 1
                logger.debug(f"Created new item {item_key}")
                
                # Handle collections
                collections = data.get("collections", [])
                if collections:
                    await self._link_item_to_collections(db, new_item, collections, library)
    
    async def _update_item_collections(
        self,
        db: Session,
        item: ZoteroItem,
        collection_keys: List[str],
        library: ZoteroLibrary
    ):
        """Update item's collection associations"""
        
        # Remove existing associations
        db.query(ZoteroItemCollection).filter(
            ZoteroItemCollection.item_id == item.id
        ).delete()
        
        # Add new associations
        for collection_key in collection_keys:
            collection = db.query(ZoteroCollection).filter(
                and_(
                    ZoteroCollection.library_id == library.id,
                    ZoteroCollection.zotero_collection_key == collection_key
                )
            ).first()
            
            if collection:
                link = ZoteroItemCollection(
                    item_id=item.id,
                    collection_id=collection.id
                )
                db.add(link)
    
    async def detect_sync_conflicts(
        self,
        connection_id: str,
        library_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect potential sync conflicts before performing sync
        
        Args:
            connection_id: Zotero connection ID
            library_ids: Specific library IDs to check
            
        Returns:
            Dictionary with conflict information
        """
        conflicts = {
            "has_conflicts": False,
            "libraries": [],
            "total_conflicts": 0,
            "conflict_types": {
                "version_mismatch": 0,
                "deleted_items": 0,
                "modified_items": 0
            }
        }
        
        try:
            async with get_db() as db:
                # Get connection
                connection = db.query(ZoteroConnection).filter(
                    ZoteroConnection.id == connection_id
                ).first()
                
                if not connection:
                    raise ValueError(f"Connection {connection_id} not found")
                
                # Get libraries
                libraries_query = db.query(ZoteroLibrary).filter(
                    ZoteroLibrary.connection_id == connection_id,
                    ZoteroLibrary.is_active == True
                )
                
                if library_ids:
                    libraries_query = libraries_query.filter(
                        ZoteroLibrary.zotero_library_id.in_(library_ids)
                    )
                
                libraries = libraries_query.all()
                
                # Check each library for conflicts
                async with self.client as api_client:
                    for library in libraries:
                        library_conflicts = await self._detect_library_conflicts(
                            api_client, connection, library
                        )
                        
                        if library_conflicts["conflict_count"] > 0:
                            conflicts["has_conflicts"] = True
                            conflicts["total_conflicts"] += library_conflicts["conflict_count"]
                            conflicts["libraries"].append(library_conflicts)
                            
                            # Update conflict type counts
                            for conflict_type, count in library_conflicts["conflict_types"].items():
                                conflicts["conflict_types"][conflict_type] += count
                
        except Exception as e:
            logger.error(f"Error detecting sync conflicts: {e}")
            conflicts["error"] = str(e)
        
        return conflicts
    
    async def _detect_library_conflicts(
        self,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary
    ) -> Dict[str, Any]:
        """Detect conflicts for a single library"""
        
        library_conflicts = {
            "library_id": library.zotero_library_id,
            "library_name": library.library_name,
            "conflict_count": 0,
            "conflict_types": {
                "version_mismatch": 0,
                "deleted_items": 0,
                "modified_items": 0
            },
            "conflicts": []
        }
        
        try:
            # Get current library version
            current_version = await api_client.get_library_version(
                connection.access_token,
                library.library_type,
                library.zotero_library_id
            )
            
            if current_version > library.library_version:
                library_conflicts["conflict_types"]["version_mismatch"] = 1
                library_conflicts["conflict_count"] += 1
                library_conflicts["conflicts"].append({
                    "type": "version_mismatch",
                    "description": f"Library version mismatch: local={library.library_version}, remote={current_version}",
                    "local_version": library.library_version,
                    "remote_version": current_version
                })
                
                # Check for modified items
                try:
                    modified_items = await api_client.get_items(
                        connection.access_token,
                        library.library_type,
                        library.zotero_library_id,
                        since_version=library.library_version,
                        limit=10  # Just check first 10 for conflict detection
                    )
                    
                    for item_data in modified_items:
                        if item_data["data"].get("deleted", False):
                            library_conflicts["conflict_types"]["deleted_items"] += 1
                        else:
                            library_conflicts["conflict_types"]["modified_items"] += 1
                        
                        library_conflicts["conflict_count"] += 1
                        library_conflicts["conflicts"].append({
                            "type": "deleted_item" if item_data["data"].get("deleted", False) else "modified_item",
                            "item_key": item_data["key"],
                            "item_title": item_data["data"].get("title", "Untitled"),
                            "item_version": item_data["version"]
                        })
                
                except Exception as e:
                    logger.warning(f"Could not check for modified items: {e}")
        
        except Exception as e:
            logger.warning(f"Could not detect conflicts for library {library.library_name}: {e}")
        
        return library_conflicts
    
    async def resolve_sync_conflicts(
        self,
        connection_id: str,
        resolution_strategy: str = "zotero_wins",
        library_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Resolve sync conflicts using specified strategy
        
        Args:
            connection_id: Zotero connection ID
            resolution_strategy: Strategy for conflict resolution
                - "zotero_wins": Zotero data takes precedence (default)
                - "local_wins": Local data takes precedence
                - "manual": Return conflicts for manual resolution
            library_ids: Specific library IDs to resolve
            
        Returns:
            Dictionary with resolution results
        """
        if resolution_strategy not in ["zotero_wins", "local_wins", "manual"]:
            raise ValueError(f"Invalid resolution strategy: {resolution_strategy}")
        
        # For now, we implement "zotero_wins" strategy (which is our default behavior)
        # This is essentially the same as incremental sync
        if resolution_strategy == "zotero_wins":
            progress = await self.incremental_sync(connection_id, library_ids)
            return {
                "strategy": resolution_strategy,
                "resolved": True,
                "sync_result": progress.get_progress_dict()
            }
        else:
            # Other strategies would be implemented here
            return {
                "strategy": resolution_strategy,
                "resolved": False,
                "message": f"Resolution strategy '{resolution_strategy}' not yet implemented"
            }
    
    async def cancel_sync(self, sync_id: str) -> bool:
        """Cancel an active sync"""
        if sync_id in self._active_syncs:
            progress = self._active_syncs[sync_id]
            progress.complete(SyncStatus.CANCELLED)
            del self._active_syncs[sync_id]
            return True
        return False