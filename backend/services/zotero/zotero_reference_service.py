"""
Zotero Reference Management Service

This service provides comprehensive CRUD operations for Zotero references,
including metadata indexing, validation, and data integrity checks.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text, desc, asc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from core.database import get_db
from models.zotero_models import (
    ZoteroItem, ZoteroLibrary, ZoteroCollection, ZoteroItemCollection,
    ZoteroAttachment, ZoteroConnection
)
from models.zotero_schemas import (
    ZoteroItemCreate, ZoteroItemUpdate, ZoteroItemResponse,
    ZoteroCreator, ZoteroSearchRequest, ZoteroSearchResponse
)

logger = logging.getLogger(__name__)


class ZoteroReferenceService:
    """Service for managing Zotero reference items with CRUD operations and validation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # CRUD Operations
    
    async def create_reference(
        self,
        user_id: str,
        library_id: str,
        reference_data: ZoteroItemCreate
    ) -> ZoteroItemResponse:
        """
        Create a new reference item with validation and metadata indexing
        
        Args:
            user_id: ID of the user creating the reference
            library_id: ID of the library to add the reference to
            reference_data: Reference data to create
            
        Returns:
            Created reference item
            
        Raises:
            ValueError: If validation fails
            PermissionError: If user doesn't have access to library
        """
        try:
            # Validate library access
            library = await self._validate_library_access(user_id, library_id)
            
            # Validate reference data
            await self._validate_reference_data(reference_data)
            
            # Create the reference item
            reference = ZoteroItem(
                library_id=library_id,
                zotero_item_key=f"local_{datetime.utcnow().timestamp()}",
                item_type=reference_data.item_type,
                title=reference_data.title,
                creators=self._serialize_creators(reference_data.creators),
                publication_title=reference_data.publication_title,
                publication_year=reference_data.publication_year,
                publisher=reference_data.publisher,
                doi=reference_data.doi,
                isbn=reference_data.isbn,
                issn=reference_data.issn,
                url=reference_data.url,
                abstract_note=reference_data.abstract_note,
                extra_fields=reference_data.extra_fields,
                tags=reference_data.tags,
                date_added=datetime.utcnow(),
                date_modified=datetime.utcnow()
            )
            
            self.db.add(reference)
            self.db.flush()  # Get the ID
            
            # Add to collections if specified
            if reference_data.collection_ids:
                await self._add_to_collections(reference.id, reference_data.collection_ids)
            
            # Update metadata indexing
            await self._update_metadata_index(reference)
            
            self.db.commit()
            
            logger.info(f"Created reference {reference.id} in library {library_id}")
            return await self.get_reference(reference.id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create reference: {str(e)}")
            raise
    
    async def get_reference(self, reference_id: str) -> Optional[ZoteroItemResponse]:
        """
        Retrieve a reference by ID with all related data
        
        Args:
            reference_id: ID of the reference to retrieve
            
        Returns:
            Reference item or None if not found
        """
        try:
            reference = self.db.query(ZoteroItem).options(
                joinedload(ZoteroItem.library),
                joinedload(ZoteroItem.item_collections).joinedload(ZoteroItemCollection.collection),
                joinedload(ZoteroItem.attachments)
            ).filter(
                ZoteroItem.id == reference_id,
                ZoteroItem.is_deleted == False
            ).first()
            
            if not reference:
                return None
            
            return self._convert_to_response(reference)
            
        except Exception as e:
            logger.error(f"Failed to get reference {reference_id}: {str(e)}")
            raise
    
    async def update_reference(
        self,
        user_id: str,
        reference_id: str,
        update_data: ZoteroItemUpdate
    ) -> Optional[ZoteroItemResponse]:
        """
        Update a reference item with validation
        
        Args:
            user_id: ID of the user updating the reference
            reference_id: ID of the reference to update
            update_data: Updated reference data
            
        Returns:
            Updated reference item or None if not found
            
        Raises:
            PermissionError: If user doesn't have access to reference
        """
        try:
            # Get existing reference
            reference = await self._get_reference_with_access_check(user_id, reference_id)
            if not reference:
                return None
            
            # Validate update data
            await self._validate_update_data(update_data)
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if field == "creators":
                    setattr(reference, field, self._serialize_creators(value))
                else:
                    setattr(reference, field, value)
            
            reference.date_modified = datetime.utcnow()
            reference.updated_at = datetime.utcnow()
            
            # Update metadata indexing
            await self._update_metadata_index(reference)
            
            self.db.commit()
            
            logger.info(f"Updated reference {reference_id}")
            return await self.get_reference(reference_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update reference {reference_id}: {str(e)}")
            raise
    
    async def delete_reference(self, user_id: str, reference_id: str) -> bool:
        """
        Soft delete a reference item
        
        Args:
            user_id: ID of the user deleting the reference
            reference_id: ID of the reference to delete
            
        Returns:
            True if deleted successfully, False if not found
            
        Raises:
            PermissionError: If user doesn't have access to reference
        """
        try:
            reference = await self._get_reference_with_access_check(user_id, reference_id)
            if not reference:
                return False
            
            reference.is_deleted = True
            reference.date_modified = datetime.utcnow()
            reference.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Deleted reference {reference_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete reference {reference_id}: {str(e)}")
            raise
    
    async def get_references_by_library(
        self,
        user_id: str,
        library_id: str,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "date_modified",
        sort_order: str = "desc"
    ) -> Tuple[List[ZoteroItemResponse], int]:
        """
        Get references from a specific library with pagination
        
        Args:
            user_id: ID of the user requesting references
            library_id: ID of the library
            limit: Maximum number of results
            offset: Results offset
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Tuple of (references list, total count)
        """
        try:
            # Validate library access
            await self._validate_library_access(user_id, library_id)
            
            # Build query
            query = self.db.query(ZoteroItem).filter(
                ZoteroItem.library_id == library_id,
                ZoteroItem.is_deleted == False
            )
            
            # Apply sorting
            sort_column = getattr(ZoteroItem, sort_by, ZoteroItem.date_modified)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            references = query.offset(offset).limit(limit).all()
            
            # Convert to response format
            response_items = [self._convert_to_response(ref) for ref in references]
            
            return response_items, total_count
            
        except Exception as e:
            logger.error(f"Failed to get references for library {library_id}: {str(e)}")
            raise
    
    async def get_references_by_collection(
        self,
        user_id: str,
        collection_id: str,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "date_modified",
        sort_order: str = "desc"
    ) -> Tuple[List[ZoteroItemResponse], int]:
        """
        Get references from a specific collection with pagination
        
        Args:
            user_id: ID of the user requesting references
            collection_id: ID of the collection
            limit: Maximum number of results
            offset: Results offset
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Tuple of (references list, total count)
        """
        try:
            # Validate collection access
            collection = await self._validate_collection_access(user_id, collection_id)
            
            # Build query
            query = self.db.query(ZoteroItem).join(
                ZoteroItemCollection,
                ZoteroItem.id == ZoteroItemCollection.item_id
            ).filter(
                ZoteroItemCollection.collection_id == collection_id,
                ZoteroItem.is_deleted == False
            )
            
            # Apply sorting
            sort_column = getattr(ZoteroItem, sort_by, ZoteroItem.date_modified)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            references = query.offset(offset).limit(limit).all()
            
            # Convert to response format
            response_items = [self._convert_to_response(ref) for ref in references]
            
            return response_items, total_count
            
        except Exception as e:
            logger.error(f"Failed to get references for collection {collection_id}: {str(e)}")
            raise
    
    # Validation Methods
    
    async def _validate_reference_data(self, reference_data: ZoteroItemCreate) -> None:
        """Validate reference data for creation"""
        errors = []
        
        # Check required fields based on item type
        if not reference_data.item_type:
            errors.append("Item type is required")
        
        # Validate DOI format if provided
        if reference_data.doi and not self._is_valid_doi(reference_data.doi):
            errors.append("Invalid DOI format")
        
        # Validate ISBN format if provided
        if reference_data.isbn and not self._is_valid_isbn(reference_data.isbn):
            errors.append("Invalid ISBN format")
        
        # Validate ISSN format if provided
        if reference_data.issn and not self._is_valid_issn(reference_data.issn):
            errors.append("Invalid ISSN format")
        
        # Validate URL format if provided
        if reference_data.url and not self._is_valid_url(reference_data.url):
            errors.append("Invalid URL format")
        
        # Validate publication year
        if reference_data.publication_year:
            current_year = datetime.now().year
            if reference_data.publication_year < 1000 or reference_data.publication_year > current_year + 5:
                errors.append("Invalid publication year")
        
        # Validate creators
        if reference_data.creators:
            for i, creator in enumerate(reference_data.creators):
                if not creator.creator_type:
                    errors.append(f"Creator {i+1}: creator_type is required")
                if not creator.name and not (creator.first_name or creator.last_name):
                    errors.append(f"Creator {i+1}: name or first_name/last_name is required")
        
        if errors:
            raise ValueError(f"Validation errors: {'; '.join(errors)}")
    
    async def _validate_update_data(self, update_data: ZoteroItemUpdate) -> None:
        """Validate reference data for updates"""
        errors = []
        
        # Validate DOI format if provided
        if update_data.doi and not self._is_valid_doi(update_data.doi):
            errors.append("Invalid DOI format")
        
        # Validate ISBN format if provided
        if update_data.isbn and not self._is_valid_isbn(update_data.isbn):
            errors.append("Invalid ISBN format")
        
        # Validate ISSN format if provided
        if update_data.issn and not self._is_valid_issn(update_data.issn):
            errors.append("Invalid ISSN format")
        
        # Validate URL format if provided
        if update_data.url and not self._is_valid_url(update_data.url):
            errors.append("Invalid URL format")
        
        # Validate publication year
        if update_data.publication_year:
            current_year = datetime.now().year
            if update_data.publication_year < 1000 or update_data.publication_year > current_year + 5:
                errors.append("Invalid publication year")
        
        # Validate creators
        if update_data.creators:
            for i, creator in enumerate(update_data.creators):
                if not creator.creator_type:
                    errors.append(f"Creator {i+1}: creator_type is required")
                if not creator.name and not (creator.first_name or creator.last_name):
                    errors.append(f"Creator {i+1}: name or first_name/last_name is required")
        
        if errors:
            raise ValueError(f"Validation errors: {'; '.join(errors)}")
    
    # Data Integrity Methods
    
    async def check_data_integrity(self, library_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check data integrity for references
        
        Args:
            library_id: Optional library ID to check specific library
            
        Returns:
            Dictionary with integrity check results
        """
        try:
            results = {
                "total_references": 0,
                "orphaned_references": 0,
                "missing_required_fields": 0,
                "duplicate_dois": 0,
                "invalid_years": 0,
                "issues": []
            }
            
            # Build base query
            query = self.db.query(ZoteroItem).filter(ZoteroItem.is_deleted == False)
            if library_id:
                query = query.filter(ZoteroItem.library_id == library_id)
            
            references = query.all()
            results["total_references"] = len(references)
            
            # Check for orphaned references (no library)
            orphaned = self.db.query(ZoteroItem).outerjoin(ZoteroLibrary).filter(
                ZoteroLibrary.id.is_(None),
                ZoteroItem.is_deleted == False
            )
            if library_id:
                orphaned = orphaned.filter(ZoteroItem.library_id == library_id)
            
            orphaned_count = orphaned.count()
            results["orphaned_references"] = orphaned_count
            if orphaned_count > 0:
                results["issues"].append(f"Found {orphaned_count} orphaned references")
            
            # Check for missing required fields
            missing_fields = 0
            for ref in references:
                if not ref.item_type:
                    missing_fields += 1
                    results["issues"].append(f"Reference {ref.id}: missing item_type")
            
            results["missing_required_fields"] = missing_fields
            
            # Check for duplicate DOIs
            if library_id:
                doi_query = self.db.query(ZoteroItem.doi, func.count(ZoteroItem.id)).filter(
                    ZoteroItem.library_id == library_id,
                    ZoteroItem.doi.isnot(None),
                    ZoteroItem.doi != "",
                    ZoteroItem.is_deleted == False
                ).group_by(ZoteroItem.doi).having(func.count(ZoteroItem.id) > 1)
            else:
                doi_query = self.db.query(ZoteroItem.doi, func.count(ZoteroItem.id)).filter(
                    ZoteroItem.doi.isnot(None),
                    ZoteroItem.doi != "",
                    ZoteroItem.is_deleted == False
                ).group_by(ZoteroItem.doi).having(func.count(ZoteroItem.id) > 1)
            
            duplicate_dois = doi_query.all()
            results["duplicate_dois"] = len(duplicate_dois)
            for doi, count in duplicate_dois:
                results["issues"].append(f"DOI {doi} appears {count} times")
            
            # Check for invalid publication years
            current_year = datetime.now().year
            invalid_years = 0
            for ref in references:
                if ref.publication_year and (ref.publication_year < 1000 or ref.publication_year > current_year + 5):
                    invalid_years += 1
                    results["issues"].append(f"Reference {ref.id}: invalid year {ref.publication_year}")
            
            results["invalid_years"] = invalid_years
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to check data integrity: {str(e)}")
            raise
    
    async def repair_data_integrity(self, library_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempt to repair data integrity issues
        
        Args:
            library_id: Optional library ID to repair specific library
            
        Returns:
            Dictionary with repair results
        """
        try:
            results = {
                "repairs_attempted": 0,
                "repairs_successful": 0,
                "repairs_failed": 0,
                "actions": []
            }
            
            # Remove orphaned item-collection relationships
            orphaned_relationships = self.db.query(ZoteroItemCollection).outerjoin(
                ZoteroItem, ZoteroItemCollection.item_id == ZoteroItem.id
            ).outerjoin(
                ZoteroCollection, ZoteroItemCollection.collection_id == ZoteroCollection.id
            ).filter(
                or_(ZoteroItem.id.is_(None), ZoteroCollection.id.is_(None))
            )
            
            if library_id:
                orphaned_relationships = orphaned_relationships.filter(
                    ZoteroItem.library_id == library_id
                )
            
            orphaned_count = orphaned_relationships.count()
            if orphaned_count > 0:
                orphaned_relationships.delete(synchronize_session=False)
                results["repairs_attempted"] += 1
                results["repairs_successful"] += 1
                results["actions"].append(f"Removed {orphaned_count} orphaned item-collection relationships")
            
            # Set default item_type for items missing it
            missing_type_query = self.db.query(ZoteroItem).filter(
                or_(ZoteroItem.item_type.is_(None), ZoteroItem.item_type == ""),
                ZoteroItem.is_deleted == False
            )
            
            if library_id:
                missing_type_query = missing_type_query.filter(ZoteroItem.library_id == library_id)
            
            missing_type_items = missing_type_query.all()
            if missing_type_items:
                for item in missing_type_items:
                    item.item_type = "document"  # Default type
                    item.updated_at = datetime.utcnow()
                
                results["repairs_attempted"] += 1
                results["repairs_successful"] += 1
                results["actions"].append(f"Set default item_type for {len(missing_type_items)} items")
            
            self.db.commit()
            
            return results
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to repair data integrity: {str(e)}")
            results["repairs_failed"] += 1
            results["actions"].append(f"Repair failed: {str(e)}")
            return results
    
    # Helper Methods
    
    async def _validate_library_access(self, user_id: str, library_id: str) -> ZoteroLibrary:
        """Validate user has access to library"""
        library = self.db.query(ZoteroLibrary).join(ZoteroConnection).filter(
            ZoteroLibrary.id == library_id,
            ZoteroConnection.user_id == user_id,
            ZoteroLibrary.is_active == True
        ).first()
        
        if not library:
            raise PermissionError(f"User {user_id} does not have access to library {library_id}")
        
        return library
    
    async def _validate_collection_access(self, user_id: str, collection_id: str) -> ZoteroCollection:
        """Validate user has access to collection"""
        collection = self.db.query(ZoteroCollection).join(ZoteroLibrary).join(ZoteroConnection).filter(
            ZoteroCollection.id == collection_id,
            ZoteroConnection.user_id == user_id,
            ZoteroLibrary.is_active == True
        ).first()
        
        if not collection:
            raise PermissionError(f"User {user_id} does not have access to collection {collection_id}")
        
        return collection
    
    async def _get_reference_with_access_check(self, user_id: str, reference_id: str) -> Optional[ZoteroItem]:
        """Get reference with user access validation"""
        reference = self.db.query(ZoteroItem).join(ZoteroLibrary).join(ZoteroConnection).filter(
            ZoteroItem.id == reference_id,
            ZoteroConnection.user_id == user_id,
            ZoteroItem.is_deleted == False
        ).first()
        
        return reference
    
    async def _add_to_collections(self, item_id: str, collection_ids: List[str]) -> None:
        """Add item to specified collections"""
        for collection_id in collection_ids:
            # Check if relationship already exists
            existing = self.db.query(ZoteroItemCollection).filter(
                ZoteroItemCollection.item_id == item_id,
                ZoteroItemCollection.collection_id == collection_id
            ).first()
            
            if not existing:
                relationship = ZoteroItemCollection(
                    item_id=item_id,
                    collection_id=collection_id
                )
                self.db.add(relationship)
    
    async def _update_metadata_index(self, reference: ZoteroItem) -> None:
        """Update metadata indexing for search optimization"""
        # This would typically update search indexes, but for now we'll just log
        logger.debug(f"Updated metadata index for reference {reference.id}")
    
    def _serialize_creators(self, creators: List[ZoteroCreator]) -> List[Dict[str, Any]]:
        """Serialize creators for database storage"""
        return [creator.dict() for creator in creators]
    
    def _convert_to_response(self, reference: ZoteroItem) -> ZoteroItemResponse:
        """Convert database model to response schema"""
        creators = [ZoteroCreator(**creator) for creator in reference.creators or []]
        
        return ZoteroItemResponse(
            id=reference.id,
            library_id=reference.library_id,
            zotero_item_key=reference.zotero_item_key,
            parent_item_id=reference.parent_item_id,
            item_type=reference.item_type,
            item_version=reference.item_version,
            title=reference.title,
            creators=creators,
            publication_title=reference.publication_title,
            publication_year=reference.publication_year,
            publisher=reference.publisher,
            doi=reference.doi,
            isbn=reference.isbn,
            issn=reference.issn,
            url=reference.url,
            abstract_note=reference.abstract_note,
            date_added=reference.date_added,
            date_modified=reference.date_modified,
            extra_fields=reference.extra_fields or {},
            tags=reference.tags or [],
            is_deleted=reference.is_deleted,
            created_at=reference.created_at,
            updated_at=reference.updated_at
        )
    
    # Validation helper methods
    
    def _is_valid_doi(self, doi: str) -> bool:
        """Validate DOI format"""
        import re
        doi_pattern = r'^10\.\d{4,}\/[-._;()\/:a-zA-Z0-9]+$'$'
        return bool(re.match(doi_pattern, doi.strip()))
    
    def _is_valid_isbn(self, isbn: str) -> bool:
        """Validate ISBN format"""
        import re
        # Remove hyphens and spaces
        isbn_clean = re.sub(r'[-\s]', '', isbn)
        # Check ISBN-10 or ISBN-13 format
        return bool(re.match(r'^(?:\d{9}[\dX]|\d{13})$', isbn_clean))$', isbn_clean))
    
    def _is_valid_issn(self, issn: str) -> bool:
        """Validate ISSN format"""
        import re
        issn_pattern = r'^\d{4}-\d{3}[\dX]$'$'
        return bool(re.match(issn_pattern, issn.strip()))
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        import re
        url_pattern = r'^https?:\/\/(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'$'
        return bool(re.match(url_pattern, url.strip()))


# Factory function for dependency injection
def get_reference_service(db: Session = None) -> ZoteroReferenceService:
    """Get reference service instance"""
    if db is None:
        db = next(get_db())
    return ZoteroReferenceService(db)