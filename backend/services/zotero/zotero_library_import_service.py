"""
Zotero Library Import Service - Focused implementation for task 3.1
Handles fetching Zotero library data, data transformation, and progress tracking
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.database import get_db
from models.zotero_models import (
    ZoteroConnection, ZoteroLibrary, ZoteroCollection, ZoteroItem,
    ZoteroItemCollection, ZoteroSyncLog
)
from models.zotero_schemas import SyncType, SyncStatus
from services.zotero.zotero_client import ZoteroAPIClient, ZoteroAPIError

logger = logging.getLogger(__name__)


class LibraryImportProgress:
    """Progress tracking for library import operations"""
    
    def __init__(self, import_id: str):
        self.import_id = import_id
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.status = "started"
        
        # Progress counters
        self.libraries_total = 0
        self.libraries_processed = 0
        self.collections_total = 0
        self.collections_processed = 0
        self.items_total = 0
        self.items_processed = 0
        self.items_added = 0
        self.items_updated = 0
        self.items_skipped = 0
        self.errors_count = 0
        self.error_details: List[Dict[str, Any]] = []
        
        # Current operation info
        self.current_library: Optional[str] = None
        self.current_operation: Optional[str] = None
        self.current_batch: Optional[int] = None
        self.estimated_completion: Optional[datetime] = None
        
    def update_progress(self, **kwargs):
        """Update progress counters and status"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def add_error(self, error: str, details: Optional[Dict[str, Any]] = None):
        """Add an error to the import log"""
        self.errors_count += 1
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "library": self.current_library,
            "operation": self.current_operation,
            "batch": self.current_batch
        }
        if details:
            error_entry["details"] = details
        self.error_details.append(error_entry)
        logger.error(f"Import error in {self.import_id}: {error}")
    
    def complete(self, status: str = "completed"):
        """Mark import as completed"""
        self.status = status
        self.completed_at = datetime.now()
    
    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage"""
        if self.items_total == 0:
            return 0.0
        return (self.items_processed / self.items_total) * 100
    
    def get_progress_dict(self) -> Dict[str, Any]:
        """Get progress as dictionary for API responses"""
        duration = None
        if self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            duration = (datetime.now() - self.started_at).total_seconds()
        
        return {
            "import_id": self.import_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": duration,
            "progress_percentage": self.get_progress_percentage(),
            "totals": {
                "libraries": self.libraries_total,
                "collections": self.collections_total,
                "items": self.items_total
            },
            "processed": {
                "libraries": self.libraries_processed,
                "collections": self.collections_processed,
                "items": self.items_processed,
                "items_added": self.items_added,
                "items_updated": self.items_updated,
                "items_skipped": self.items_skipped
            },
            "errors": {
                "count": self.errors_count,
                "recent": self.error_details[-5:] if self.error_details else []
            },
            "current_operation": {
                "library": self.current_library,
                "operation": self.current_operation,
                "batch": self.current_batch
            },
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None
        }


class ZoteroLibraryImportService:
    """Service for importing Zotero library data"""
    
    def __init__(self):
        self.client = ZoteroAPIClient()
        self._active_imports: Dict[str, LibraryImportProgress] = {}
        
    async def import_library(
        self,
        connection_id: str,
        library_ids: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> LibraryImportProgress:
        """
        Import library data from Zotero
        
        Args:
            connection_id: Zotero connection ID
            library_ids: Specific library IDs to import (None for all)
            progress_callback: Optional callback for progress updates
            
        Returns:
            LibraryImportProgress object with import results
        """
        # Create import progress tracker
        import_id = f"import_{connection_id}_{int(datetime.now().timestamp())}"
        progress = LibraryImportProgress(import_id)
        self._active_imports[import_id] = progress
        
        try:
            async with get_db() as db:
                # Validate connection
                connection = await self._validate_connection(db, connection_id)
                
                # Create sync log entry
                sync_log = ZoteroSyncLog(
                    connection_id=connection_id,
                    sync_type=SyncType.FULL.value,
                    sync_status=SyncStatus.IN_PROGRESS.value,
                    started_at=progress.started_at
                )
                db.add(sync_log)
                db.commit()
                
                progress.update_progress(status="in_progress")
                
                # Fetch available libraries
                async with self.client as api_client:
                    libraries = await self._fetch_libraries(
                        api_client, connection, library_ids, progress
                    )
                    
                    if not libraries:
                        progress.complete("completed")
                        return progress
                    
                    progress.libraries_total = len(libraries)
                    
                    # Import each library
                    for library_data in libraries:
                        try:
                            await self._import_single_library(
                                db, api_client, connection, library_data, progress, progress_callback
                            )
                            progress.libraries_processed += 1
                            
                        except Exception as e:
                            progress.add_error(
                                f"Failed to import library {library_data['name']}: {str(e)}",
                                {"library_id": library_data["id"], "library_type": library_data["type"]}
                            )
                            continue
                
                # Update sync log
                progress.complete("completed" if progress.errors_count == 0 else "completed_with_errors")
                sync_log.sync_status = SyncStatus.COMPLETED.value if progress.errors_count == 0 else SyncStatus.FAILED.value
                sync_log.completed_at = progress.completed_at
                sync_log.items_processed = progress.items_processed
                sync_log.items_added = progress.items_added
                sync_log.items_updated = progress.items_updated
                sync_log.errors_count = progress.errors_count
                sync_log.error_details = progress.error_details
                
                db.commit()
                
                # Update connection last sync time
                connection.last_sync_at = progress.completed_at
                db.commit()
                
                logger.info(f"Library import completed: {progress.get_progress_dict()}")
                
        except Exception as e:
            progress.add_error(f"Library import failed: {str(e)}")
            progress.complete("failed")
            logger.error(f"Library import failed for connection {connection_id}: {e}")
            
        finally:
            # Clean up active import tracking after a delay
            asyncio.create_task(self._cleanup_import_tracking(import_id, delay=300))  # 5 minutes
        
        return progress
    
    async def _validate_connection(self, db: Session, connection_id: str) -> ZoteroConnection:
        """Validate that the connection exists and is active"""
        connection = db.query(ZoteroConnection).filter(
            ZoteroConnection.id == connection_id
        ).first()
        
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        if connection.connection_status != "active":
            raise ValueError(f"Connection {connection_id} is not active (status: {connection.connection_status})")
        
        return connection
    
    async def _fetch_libraries(
        self,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library_ids: Optional[List[str]],
        progress: LibraryImportProgress
    ) -> List[Dict[str, Any]]:
        """Fetch available libraries from Zotero API"""
        progress.current_operation = "fetching_libraries"
        
        try:
            libraries = await api_client.get_libraries(
                connection.access_token,
                connection.zotero_user_id
            )
            
            # Filter libraries if specific IDs provided
            if library_ids:
                libraries = [lib for lib in libraries if lib["id"] in library_ids]
            
            logger.info(f"Found {len(libraries)} libraries to import")
            return libraries
            
        except ZoteroAPIError as e:
            progress.add_error(f"Failed to fetch libraries: {e.message}", {"status_code": e.status_code})
            raise
    
    async def _import_single_library(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library_data: Dict[str, Any],
        progress: LibraryImportProgress,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """Import a single library with all its collections and items"""
        progress.current_library = library_data["name"]
        progress.current_operation = "importing_library"
        
        # Create or update library record
        library = await self._create_or_update_library(db, connection, library_data)
        
        # Import collections first (needed for item-collection relationships)
        collections_count = await self._import_library_collections(
            db, api_client, connection, library, progress
        )
        progress.collections_total += collections_count
        
        # Import items
        items_count = await self._import_library_items(
            db, api_client, connection, library, progress, progress_callback
        )
        progress.items_total += items_count
        
        # Update library sync timestamp
        library.last_sync_at = datetime.now()
        db.commit()
        
        logger.info(f"Completed import for library {library.library_name}: {collections_count} collections, {items_count} items")
    
    async def _create_or_update_library(
        self,
        db: Session,
        connection: ZoteroConnection,
        library_data: Dict[str, Any]
    ) -> ZoteroLibrary:
        """Create or update library record"""
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
                group_id=library_data.get("id") if library_data["type"] == "group" else None,
                permissions=library_data.get("permissions", {}),
                library_metadata=library_data
            )
            db.add(library)
            db.flush()  # Get the ID
            logger.info(f"Created new library: {library.library_name}")
        else:
            # Update existing library
            library.library_name = library_data["name"]
            library.is_active = True
            library.permissions = library_data.get("permissions", {})
            library.library_metadata = library_data
            logger.info(f"Updated existing library: {library.library_name}")
        
        return library
    
    async def _import_library_collections(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        progress: LibraryImportProgress
    ) -> int:
        """Import collections for a library and return count"""
        progress.current_operation = "importing_collections"
        
        try:
            collections_data = await api_client.get_collections(
                connection.access_token,
                library.library_type,
                library.zotero_library_id
            )
            
            if not collections_data:
                return 0
            
            logger.info(f"Importing {len(collections_data)} collections for library {library.library_name}")
            
            # Create a mapping of collection keys for hierarchy processing
            collection_map = {}
            
            # First pass: create all collections
            for collection_data in collections_data:
                try:
                    collection = await self._create_or_update_collection(
                        db, library, collection_data
                    )
                    collection_map[collection_data["key"]] = collection
                    progress.collections_processed += 1
                    
                except Exception as e:
                    progress.add_error(
                        f"Failed to import collection: {str(e)}",
                        {"collection_key": collection_data.get("key")}
                    )
                    continue
            
            # Second pass: establish parent-child relationships
            await self._establish_collection_hierarchy(collection_map, collections_data, progress)
            
            db.commit()
            return len(collections_data)
            
        except Exception as e:
            progress.add_error(f"Failed to import collections: {str(e)}")
            return 0
    
    async def _create_or_update_collection(
        self,
        db: Session,
        library: ZoteroLibrary,
        collection_data: Dict[str, Any]
    ) -> ZoteroCollection:
        """Create or update a single collection"""
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
            existing_collection.collection_metadata = data
            return existing_collection
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
            return new_collection
    
    async def _establish_collection_hierarchy(
        self,
        collection_map: Dict[str, ZoteroCollection],
        collections_data: List[Dict[str, Any]],
        progress: LibraryImportProgress
    ):
        """Establish parent-child relationships between collections"""
        for collection_data in collections_data:
            try:
                collection_key = collection_data["key"]
                data = collection_data["data"]
                parent_collection_key = data.get("parentCollection")
                
                if parent_collection_key and parent_collection_key in collection_map:
                    child_collection = collection_map[collection_key]
                    parent_collection = collection_map[parent_collection_key]
                    child_collection.parent_collection_id = parent_collection.id
                    
                    # Build hierarchical path for efficient queries
                    if parent_collection.collection_path:
                        child_collection.collection_path = f"{parent_collection.collection_path}/{child_collection.collection_name}"
                    else:
                        child_collection.collection_path = f"{parent_collection.collection_name}/{child_collection.collection_name}"
                elif not parent_collection_key:
                    # Root collection
                    collection_map[collection_key].collection_path = collection_map[collection_key].collection_name
            
            except Exception as e:
                progress.add_error(
                    f"Failed to set collection hierarchy: {str(e)}",
                    {"collection_key": collection_data.get("key")}
                )
                continue
    
    async def _import_library_items(
        self,
        db: Session,
        api_client: ZoteroAPIClient,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        progress: LibraryImportProgress,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> int:
        """Import items for a library with pagination and return total count"""
        progress.current_operation = "importing_items"
        
        try:
            batch_size = 100
            start = 0
            total_items = 0
            batch_number = 1
            
            while True:
                progress.current_batch = batch_number
                
                items_data = await api_client.get_items(
                    connection.access_token,
                    library.library_type,
                    library.zotero_library_id,
                    limit=batch_size,
                    start=start
                )
                
                if not items_data:
                    break
                
                logger.info(f"Processing batch {batch_number} of {len(items_data)} items (start: {start})")
                
                # Process items in current batch
                for item_data in items_data:
                    try:
                        await self._import_single_item(
                            db, connection, library, item_data, progress
                        )
                        progress.items_processed += 1
                        total_items += 1
                        
                        # Call progress callback periodically
                        if progress_callback and progress.items_processed % 10 == 0:
                            await progress_callback(progress.get_progress_dict())
                        
                    except Exception as e:
                        progress.add_error(
                            f"Failed to import item: {str(e)}",
                            {"item_key": item_data.get("key")}
                        )
                        progress.items_skipped += 1
                        continue
                
                # Check if we got fewer items than requested (end of results)
                if len(items_data) < batch_size:
                    break
                
                start += batch_size
                batch_number += 1
                
                # Commit periodically to avoid large transactions
                if total_items % 500 == 0:
                    db.commit()
                    logger.info(f"Committed {total_items} items so far")
            
            db.commit()
            logger.info(f"Imported {total_items} items for library {library.library_name}")
            return total_items
            
        except Exception as e:
            progress.add_error(f"Failed to import items: {str(e)}")
            return 0
    
    async def _import_single_item(
        self,
        db: Session,
        connection: ZoteroConnection,
        library: ZoteroLibrary,
        item_data: Dict[str, Any],
        progress: LibraryImportProgress
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
        transformed_data = self.transform_item_data(data)
        
        if existing_item:
            # Update existing item if version is newer
            if existing_item.item_version < item_version:
                self._update_item_from_data(existing_item, transformed_data, item_version)
                progress.items_updated += 1
            else:
                progress.items_skipped += 1
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
            collections = data.get("collections", [])
            if collections:
                await self._link_item_to_collections(db, new_item, collections, library)
    
    def transform_item_data(self, zotero_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Zotero item data to our internal format
        
        This is a key method that handles the data transformation requirement
        """
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
        
        # Extract publication year from date using various formats
        publication_year = self._extract_publication_year(zotero_data.get("date", ""))
        
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
            "extra_fields": self._extract_extra_fields(zotero_data),
            "item_metadata": zotero_data  # Store original data for reference
        }
        
        return transformed
    
    def _extract_publication_year(self, date_str: str) -> Optional[int]:
        """Extract publication year from various date formats"""
        if not date_str:
            return None
        
        import re
        # Try to extract 4-digit year (19xx or 20xx)
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            return int(year_match.group())
        
        return None
    
    def _extract_extra_fields(self, zotero_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional fields not mapped to specific columns"""
        # Fields that are mapped to specific columns
        mapped_fields = {
            "itemType", "title", "creators", "publicationTitle", "bookTitle",
            "publisher", "DOI", "ISBN", "ISSN", "url", "abstractNote",
            "dateAdded", "dateModified", "tags", "collections", "relations"
        }
        
        # Return all other fields as extra data
        return {
            k: v for k, v in zotero_data.items()
            if k not in mapped_fields and v is not None
        }
    
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
            # Zotero uses ISO format with Z suffix
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def get_import_progress(self, import_id: str) -> Optional[Dict[str, Any]]:
        """Get progress for an active import"""
        if import_id in self._active_imports:
            return self._active_imports[import_id].get_progress_dict()
        return None
    
    def get_active_imports(self) -> List[Dict[str, Any]]:
        """Get all active imports"""
        return [progress.get_progress_dict() for progress in self._active_imports.values()]
    
    async def cancel_import(self, import_id: str) -> bool:
        """Cancel an active import"""
        if import_id in self._active_imports:
            progress = self._active_imports[import_id]
            progress.complete("cancelled")
            del self._active_imports[import_id]
            logger.info(f"Import {import_id} cancelled")
            return True
        return False
    
    async def _cleanup_import_tracking(self, import_id: str, delay: int = 300):
        """Clean up import tracking after delay"""
        await asyncio.sleep(delay)
        if import_id in self._active_imports:
            del self._active_imports[import_id]
            logger.debug(f"Cleaned up import tracking for {import_id}")