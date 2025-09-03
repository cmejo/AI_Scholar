"""
Zotero Reference Browsing and Filtering Service

This service provides comprehensive browsing and filtering functionality
for Zotero references with collection-based filtering, sorting, and pagination.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text, desc, asc, case
from sqlalchemy.sql import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

from core.database import get_db
from models.zotero_models import (
    ZoteroItem, ZoteroLibrary, ZoteroCollection, ZoteroItemCollection,
    ZoteroConnection
)
from models.zotero_schemas import ZoteroItemResponse

logger = logging.getLogger(__name__)


class ZoteroBrowseService:
    """Service for browsing and filtering Zotero references"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def browse_references(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        item_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        creators: Optional[List[str]] = None,
        publication_year_start: Optional[int] = None,
        publication_year_end: Optional[int] = None,
        publisher: Optional[str] = None,
        has_doi: Optional[bool] = None,
        has_attachments: Optional[bool] = None,
        date_added_start: Optional[datetime] = None,
        date_added_end: Optional[datetime] = None,
        sort_by: str = "date_modified",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ZoteroItemResponse], int, Dict[str, Any]]:
        """
        Browse references with comprehensive filtering options
        
        Args:
            user_id: ID of the user browsing references
            library_id: Optional library filter
            collection_id: Optional collection filter
            item_type: Optional item type filter
            tags: Optional list of tags to filter by
            creators: Optional list of creators to filter by
            publication_year_start: Optional start year filter
            publication_year_end: Optional end year filter
            publisher: Optional publisher filter
            has_doi: Optional filter for items with/without DOI
            has_attachments: Optional filter for items with/without attachments
            date_added_start: Optional start date for date added filter
            date_added_end: Optional end date for date added filter
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Results offset
            
        Returns:
            Tuple of (references list, total count, browse metadata)
        """
        try:
            # Build base query with user access control
            query = self._build_base_query(user_id)
            
            # Apply filters
            query = await self._apply_browse_filters(
                query, library_id, collection_id, item_type, tags, creators,
                publication_year_start, publication_year_end, publisher,
                has_doi, has_attachments, date_added_start, date_added_end
            )
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply sorting
            query = await self._apply_sorting(query, sort_by, sort_order)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            references = query.all()
            
            # Convert to response format
            response_items = [self._convert_to_response(ref) for ref in references]
            
            # Generate helpful suggestions if no results found
            suggestions = []
            if total_count == 0:
                suggestions = await self._generate_helpful_suggestions(
                    user_id, library_id, collection_id, item_type, tags, creators,
                    publication_year_start, publication_year_end, publisher
                )
            
            # Build browse metadata
            browse_metadata = {
                "filters_applied": {
                    "library_id": library_id,
                    "collection_id": collection_id,
                    "item_type": item_type,
                    "tags": tags or [],
                    "creators": creators or [],
                    "publication_year_start": publication_year_start,
                    "publication_year_end": publication_year_end,
                    "publisher": publisher,
                    "has_doi": has_doi,
                    "has_attachments": has_attachments,
                    "date_added_start": date_added_start.isoformat() if date_added_start else None,
                    "date_added_end": date_added_end.isoformat() if date_added_end else None
                },
                "sort_by": sort_by,
                "sort_order": sort_order,
                "limit": limit,
                "offset": offset,
                "total_count": total_count,
                "page_count": (total_count + limit - 1) // limit if limit > 0 else 1,
                "current_page": (offset // limit) + 1 if limit > 0 else 1,
                "has_next_page": offset + limit < total_count,
                "has_previous_page": offset > 0,
                "suggestions": suggestions
            }
            
            return response_items, total_count, browse_metadata
            
        except Exception as e:
            logger.error(f"Browse failed for user {user_id}: {str(e)}")
            raise
    
    async def get_recent_references(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        days: int = 30,
        limit: int = 20
    ) -> List[ZoteroItemResponse]:
        """
        Get recently added or modified references
        
        Args:
            user_id: ID of the user
            library_id: Optional library filter
            days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of recent references
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = self._build_base_query(user_id)
            
            if library_id:
                query = query.filter(ZoteroItem.library_id == library_id)
            
            # Filter by recent activity
            query = query.filter(
                or_(
                    ZoteroItem.date_added >= cutoff_date,
                    ZoteroItem.date_modified >= cutoff_date,
                    ZoteroItem.created_at >= cutoff_date,
                    ZoteroItem.updated_at >= cutoff_date
                )
            )
            
            # Sort by most recent first
            query = query.order_by(
                desc(
                    case(
                        (ZoteroItem.date_modified.isnot(None), ZoteroItem.date_modified),
                        (ZoteroItem.date_added.isnot(None), ZoteroItem.date_added),
                        else_=ZoteroItem.updated_at
                    )
                )
            ).limit(limit)
            
            references = query.all()
            return [self._convert_to_response(ref) for ref in references]
            
        except Exception as e:
            logger.error(f"Failed to get recent references for user {user_id}: {str(e)}")
            raise
    
    async def get_popular_references(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        limit: int = 20
    ) -> List[ZoteroItemResponse]:
        """
        Get popular references based on various metrics
        
        Args:
            user_id: ID of the user
            library_id: Optional library filter
            limit: Maximum number of results
            
        Returns:
            List of popular references
        """
        try:
            query = self._build_base_query(user_id)
            
            if library_id:
                query = query.filter(ZoteroItem.library_id == library_id)
            
            # Calculate popularity score based on various factors
            popularity_score = (
                # Items with more tags are considered more popular
                func.coalesce(func.json_array_length(ZoteroItem.tags), 0) * 2 +
                # Items with attachments are more popular
                case(
                    (func.exists().where(
                        ZoteroItem.attachments.any()
                    ), 5),
                    else_=0
                ) +
                # Recent items get a boost
                case(
                    (ZoteroItem.date_added >= datetime.utcnow() - timedelta(days=30), 3),
                    (ZoteroItem.date_added >= datetime.utcnow() - timedelta(days=90), 1),
                    else_=0
                ) +
                # Items with DOI are more credible
                case(
                    (ZoteroItem.doi.isnot(None), 2),
                    else_=0
                )
            )
            
            query = query.order_by(desc(popularity_score)).limit(limit)
            
            references = query.all()
            return [self._convert_to_response(ref) for ref in references]
            
        except Exception as e:
            logger.error(f"Failed to get popular references for user {user_id}: {str(e)}")
            raise
    
    async def get_references_by_year(
        self,
        user_id: str,
        year: int,
        library_id: Optional[str] = None,
        sort_by: str = "title",
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[ZoteroItemResponse], int]:
        """
        Get references from a specific publication year
        
        Args:
            user_id: ID of the user
            year: Publication year to filter by
            library_id: Optional library filter
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Results offset
            
        Returns:
            Tuple of (references list, total count)
        """
        try:
            query = self._build_base_query(user_id)
            
            if library_id:
                query = query.filter(ZoteroItem.library_id == library_id)
            
            query = query.filter(ZoteroItem.publication_year == year)
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            query = await self._apply_sorting(query, sort_by, sort_order)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            references = query.all()
            response_items = [self._convert_to_response(ref) for ref in references]
            
            return response_items, total_count
            
        except Exception as e:
            logger.error(f"Failed to get references for year {year}: {str(e)}")
            raise
    
    async def get_references_by_tag(
        self,
        user_id: str,
        tag: str,
        library_id: Optional[str] = None,
        sort_by: str = "date_modified",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[ZoteroItemResponse], int]:
        """
        Get references with a specific tag
        
        Args:
            user_id: ID of the user
            tag: Tag to filter by
            library_id: Optional library filter
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Results offset
            
        Returns:
            Tuple of (references list, total count)
        """
        try:
            query = self._build_base_query(user_id)
            
            if library_id:
                query = query.filter(ZoteroItem.library_id == library_id)
            
            query = query.filter(
                func.json_contains(ZoteroItem.tags, f'"{tag}"')
            )
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            query = await self._apply_sorting(query, sort_by, sort_order)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            references = query.all()
            response_items = [self._convert_to_response(ref) for ref in references]
            
            return response_items, total_count
            
        except Exception as e:
            logger.error(f"Failed to get references for tag '{tag}': {str(e)}")
            raise
    
    async def get_references_by_creator(
        self,
        user_id: str,
        creator_name: str,
        library_id: Optional[str] = None,
        sort_by: str = "publication_year",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[ZoteroItemResponse], int]:
        """
        Get references by a specific creator
        
        Args:
            user_id: ID of the user
            creator_name: Creator name to search for
            library_id: Optional library filter
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Results offset
            
        Returns:
            Tuple of (references list, total count)
        """
        try:
            query = self._build_base_query(user_id)
            
            if library_id:
                query = query.filter(ZoteroItem.library_id == library_id)
            
            # Search in creators JSON field
            query = query.filter(
                func.json_contains(func.cast(ZoteroItem.creators, text), f'"{creator_name}"')
            )
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            query = await self._apply_sorting(query, sort_by, sort_order)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            references = query.all()
            response_items = [self._convert_to_response(ref) for ref in references]
            
            return response_items, total_count
            
        except Exception as e:
            logger.error(f"Failed to get references for creator '{creator_name}': {str(e)}")
            raise
    
    async def get_collection_hierarchy(
        self,
        user_id: str,
        library_id: str,
        include_item_counts: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get hierarchical collection structure for browsing
        
        Args:
            user_id: ID of the user
            library_id: Library ID to get collections for
            include_item_counts: Whether to include item counts
            
        Returns:
            Hierarchical collection structure
        """
        try:
            # Validate library access
            library = self.db.query(ZoteroLibrary).join(ZoteroConnection).filter(
                ZoteroLibrary.id == library_id,
                ZoteroConnection.user_id == user_id,
                ZoteroLibrary.is_active == True
            ).first()
            
            if not library:
                raise PermissionError(f"User {user_id} does not have access to library {library_id}")
            
            # Get all collections for the library
            collections = self.db.query(ZoteroCollection).filter(
                ZoteroCollection.library_id == library_id
            ).order_by(ZoteroCollection.collection_name).all()
            
            # Build hierarchy
            collection_map = {}
            root_collections = []
            
            for collection in collections:
                collection_data = {
                    "id": collection.id,
                    "name": collection.collection_name,
                    "parent_id": collection.parent_collection_id,
                    "path": collection.collection_path,
                    "item_count": collection.item_count if include_item_counts else 0,
                    "children": []
                }
                
                collection_map[collection.id] = collection_data
                
                if collection.parent_collection_id is None:
                    root_collections.append(collection_data)
            
            # Build parent-child relationships
            for collection in collections:
                if collection.parent_collection_id and collection.parent_collection_id in collection_map:
                    parent = collection_map[collection.parent_collection_id]
                    child = collection_map[collection.id]
                    parent["children"].append(child)
            
            return root_collections
            
        except Exception as e:
            logger.error(f"Failed to get collection hierarchy for library {library_id}: {str(e)}")
            raise
    
    async def get_browse_statistics(
        self,
        user_id: str,
        library_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get browsing statistics for the user's references
        
        Args:
            user_id: ID of the user
            library_id: Optional library filter
            
        Returns:
            Dictionary with browsing statistics
        """
        try:
            query = self._build_base_query(user_id)
            
            if library_id:
                query = query.filter(ZoteroItem.library_id == library_id)
            
            # Get all references for statistics
            references = query.all()
            
            # Calculate statistics
            total_count = len(references)
            
            # Item type distribution
            type_counts = {}
            for ref in references:
                if ref.item_type:
                    type_counts[ref.item_type] = type_counts.get(ref.item_type, 0) + 1
            
            # Year distribution
            year_counts = {}
            for ref in references:
                if ref.publication_year:
                    year_counts[ref.publication_year] = year_counts.get(ref.publication_year, 0) + 1
            
            # Recent activity
            recent_cutoff = datetime.utcnow() - timedelta(days=30)
            recent_count = sum(1 for ref in references if (
                ref.date_added and ref.date_added >= recent_cutoff
            ) or (
                ref.date_modified and ref.date_modified >= recent_cutoff
            ) or (
                ref.created_at and ref.created_at >= recent_cutoff
            ))
            
            # Items with attachments
            with_attachments = sum(1 for ref in references if ref.attachments)
            
            # Items with DOI
            with_doi = sum(1 for ref in references if ref.doi)
            
            # Most common tags
            tag_counts = {}
            for ref in references:
                if ref.tags:
                    for tag in ref.tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "total_references": total_count,
                "item_types": [
                    {"type": item_type, "count": count}
                    for item_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
                ],
                "publication_years": [
                    {"year": year, "count": count}
                    for year, count in sorted(year_counts.items(), key=lambda x: x[0], reverse=True)
                ][:10],
                "recent_activity": {
                    "count": recent_count,
                    "percentage": (recent_count / total_count * 100) if total_count > 0 else 0
                },
                "with_attachments": {
                    "count": with_attachments,
                    "percentage": (with_attachments / total_count * 100) if total_count > 0 else 0
                },
                "with_doi": {
                    "count": with_doi,
                    "percentage": (with_doi / total_count * 100) if total_count > 0 else 0
                },
                "top_tags": [
                    {"tag": tag, "count": count}
                    for tag, count in top_tags
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get browse statistics for user {user_id}: {str(e)}")
            raise
    
    # Private helper methods
    
    def _build_base_query(self, user_id: str):
        """Build base query with user access control"""
        return self.db.query(ZoteroItem).join(ZoteroLibrary).join(ZoteroConnection).filter(
            ZoteroConnection.user_id == user_id,
            ZoteroLibrary.is_active == True,
            ZoteroItem.is_deleted == False
        ).options(
            joinedload(ZoteroItem.library),
            joinedload(ZoteroItem.item_collections).joinedload(ZoteroItemCollection.collection),
            joinedload(ZoteroItem.attachments)
        )
    
    async def _apply_browse_filters(
        self, query, library_id, collection_id, item_type, tags, creators,
        publication_year_start, publication_year_end, publisher,
        has_doi, has_attachments, date_added_start, date_added_end
    ):
        """Apply all browse filters to the query"""
        
        # Library filter
        if library_id:
            query = query.filter(ZoteroItem.library_id == library_id)
        
        # Collection filter
        if collection_id:
            query = query.join(
                ZoteroItemCollection,
                ZoteroItem.id == ZoteroItemCollection.item_id
            ).filter(ZoteroItemCollection.collection_id == collection_id)
        
        # Item type filter
        if item_type:
            query = query.filter(ZoteroItem.item_type == item_type)
        
        # Tags filter
        if tags:
            for tag in tags:
                query = query.filter(
                    func.json_contains(ZoteroItem.tags, f'"{tag}"')
                )
        
        # Creators filter
        if creators:
            creator_conditions = []
            for creator in creators:
                creator_conditions.append(
                    func.json_contains(func.cast(ZoteroItem.creators, text), f'"{creator}"')
                )
            query = query.filter(or_(*creator_conditions))
        
        # Publication year range filter
        if publication_year_start:
            query = query.filter(ZoteroItem.publication_year >= publication_year_start)
        
        if publication_year_end:
            query = query.filter(ZoteroItem.publication_year <= publication_year_end)
        
        # Publisher filter
        if publisher:
            query = query.filter(ZoteroItem.publisher.ilike(f"%{publisher}%"))
        
        # DOI filter
        if has_doi is not None:
            if has_doi:
                query = query.filter(ZoteroItem.doi.isnot(None), ZoteroItem.doi != "")
            else:
                query = query.filter(or_(ZoteroItem.doi.is_(None), ZoteroItem.doi == ""))
        
        # Attachments filter
        if has_attachments is not None:
            if has_attachments:
                query = query.filter(ZoteroItem.attachments.any())
            else:
                query = query.filter(~ZoteroItem.attachments.any())
        
        # Date added range filter
        if date_added_start:
            query = query.filter(ZoteroItem.date_added >= date_added_start)
        
        if date_added_end:
            query = query.filter(ZoteroItem.date_added <= date_added_end)
        
        return query
    
    async def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to the query"""
        sort_column = getattr(ZoteroItem, sort_by, None)
        
        if sort_column:
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
        else:
            # Default sorting
            query = query.order_by(desc(ZoteroItem.date_modified))
        
        return query
    
    async def _generate_helpful_suggestions(
        self, user_id: str, library_id: Optional[str], collection_id: Optional[str],
        item_type: Optional[str], tags: Optional[List[str]], creators: Optional[List[str]],
        publication_year_start: Optional[int], publication_year_end: Optional[int],
        publisher: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate helpful suggestions when no results are found"""
        suggestions = []
        
        try:
            # Get base query for user's references
            base_query = self._build_base_query(user_id)
            if library_id:
                base_query = base_query.filter(ZoteroItem.library_id == library_id)
            
            # Suggestion 1: Try removing the most restrictive filter
            if collection_id:
                suggestions.append({
                    "type": "remove_filter",
                    "message": "Try browsing all collections instead of the selected collection",
                    "action": "remove_collection_filter",
                    "filter_removed": "collection"
                })
            
            if item_type:
                # Check if there are other item types available
                other_types = base_query.with_entities(ZoteroItem.item_type).distinct().all()
                if other_types:
                    available_types = [t[0] for t in other_types if t[0] != item_type]
                    if available_types:
                        suggestions.append({
                            "type": "alternative_filter",
                            "message": f"No {item_type} items found. Try these item types instead:",
                            "action": "change_item_type",
                            "alternatives": available_types[:5]
                        })
            
            if tags:
                # Suggest similar tags
                all_refs = base_query.all()
                all_tags = set()
                for ref in all_refs:
                    if ref.tags:
                        all_tags.update(ref.tags)
                
                # Find tags that are similar to the searched tags
                similar_tags = []
                for tag in tags:
                    for available_tag in all_tags:
                        if (tag.lower() in available_tag.lower() or 
                            available_tag.lower() in tag.lower()) and available_tag not in tags:
                            similar_tags.append(available_tag)
                
                if similar_tags:
                    suggestions.append({
                        "type": "similar_tags",
                        "message": "Try these similar tags:",
                        "action": "use_similar_tags",
                        "alternatives": similar_tags[:5]
                    })
            
            if creators:
                # Suggest similar creators
                all_refs = base_query.all()
                all_creators = set()
                for ref in all_refs:
                    if ref.creators:
                        for creator in ref.creators:
                            if isinstance(creator, dict) and 'name' in creator:
                                all_creators.add(creator['name'])
                            elif hasattr(creator, 'name'):
                                all_creators.add(creator.name)
                
                similar_creators = []
                for creator in creators:
                    for available_creator in all_creators:
                        # Check for partial name matches
                        creator_parts = creator.lower().split()
                        available_parts = available_creator.lower().split()
                        if any(part in available_creator.lower() for part in creator_parts):
                            if available_creator not in creators:
                                similar_creators.append(available_creator)
                
                if similar_creators:
                    suggestions.append({
                        "type": "similar_creators",
                        "message": "Try these similar authors:",
                        "action": "use_similar_creators",
                        "alternatives": similar_creators[:5]
                    })
            
            if publication_year_start or publication_year_end:
                # Suggest expanding year range
                all_years = base_query.with_entities(ZoteroItem.publication_year).filter(
                    ZoteroItem.publication_year.isnot(None)
                ).distinct().all()
                
                if all_years:
                    available_years = sorted([y[0] for y in all_years])
                    min_year = min(available_years)
                    max_year = max(available_years)
                    
                    suggestions.append({
                        "type": "expand_year_range",
                        "message": f"Try expanding the year range. Available years: {min_year}-{max_year}",
                        "action": "expand_year_range",
                        "suggested_range": {"min": min_year, "max": max_year}
                    })
            
            if publisher:
                # Suggest similar publishers
                all_publishers = base_query.with_entities(ZoteroItem.publisher).filter(
                    ZoteroItem.publisher.isnot(None)
                ).distinct().all()
                
                similar_publishers = []
                for pub in all_publishers:
                    pub_name = pub[0]
                    if (publisher.lower() in pub_name.lower() or 
                        pub_name.lower() in publisher.lower()) and pub_name != publisher:
                        similar_publishers.append(pub_name)
                
                if similar_publishers:
                    suggestions.append({
                        "type": "similar_publishers",
                        "message": "Try these similar publishers:",
                        "action": "use_similar_publishers",
                        "alternatives": similar_publishers[:5]
                    })
            
            # General suggestions if no specific suggestions were generated
            if not suggestions:
                total_refs = base_query.count()
                if total_refs > 0:
                    suggestions.extend([
                        {
                            "type": "remove_all_filters",
                            "message": f"Try removing all filters to see all {total_refs} references",
                            "action": "clear_all_filters"
                        },
                        {
                            "type": "browse_recent",
                            "message": "Browse recently added references",
                            "action": "show_recent"
                        },
                        {
                            "type": "browse_popular",
                            "message": "Browse most popular references",
                            "action": "show_popular"
                        }
                    ])
                else:
                    suggestions.append({
                        "type": "no_references",
                        "message": "No references found in your library. Try importing from Zotero first.",
                        "action": "import_library"
                    })
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {str(e)}")
            # Fallback suggestions
            suggestions = [
                {
                    "type": "general",
                    "message": "Try removing some filters or check your search terms",
                    "action": "modify_search"
                }
            ]
        
        return suggestions

    def _convert_to_response(self, reference: ZoteroItem) -> ZoteroItemResponse:
        """Convert database model to response schema"""
        from models.zotero_schemas import ZoteroCreator
        
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


# Factory function for dependency injection
def get_browse_service(db: Session = None) -> ZoteroBrowseService:
    """Get browse service instance"""
    if db is None:
        db = next(get_db())
    return ZoteroBrowseService(db)