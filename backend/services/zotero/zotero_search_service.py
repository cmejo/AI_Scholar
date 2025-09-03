"""
Zotero Advanced Search Service

This service provides comprehensive search functionality for Zotero references,
including full-text search, faceted search, and relevance scoring.
"""
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text, desc, asc, case
from sqlalchemy.sql import select
from sqlalchemy.exc import SQLAlchemyError

from core.database import get_db
from models.zotero_models import (
    ZoteroItem, ZoteroLibrary, ZoteroCollection, ZoteroItemCollection,
    ZoteroConnection
)
from models.zotero_schemas import (
    ZoteroSearchRequest, ZoteroSearchResponse, ZoteroItemResponse
)

logger = logging.getLogger(__name__)


class ZoteroSearchService:
    """Service for advanced search functionality in Zotero references"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def search_references(
        self,
        user_id: str,
        search_request: ZoteroSearchRequest
    ) -> ZoteroSearchResponse:
        """
        Perform advanced search across Zotero references
        
        Args:
            user_id: ID of the user performing the search
            search_request: Search parameters and filters
            
        Returns:
            Search results with metadata
        """
        start_time = time.time()
        
        try:
            # Build base query with user access control
            query = self._build_base_query(user_id)
            
            # Apply search filters
            query = await self._apply_search_filters(query, search_request)
            
            # Apply faceted filters
            query = await self._apply_faceted_filters(query, search_request)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply sorting
            query = await self._apply_sorting(query, search_request)
            
            # Apply pagination
            query = query.offset(search_request.offset).limit(search_request.limit)
            
            # Execute query
            references = query.all()
            
            # Convert to response format
            response_items = [self._convert_to_response(ref) for ref in references]
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Handle no results case with suggestions
            suggestions = []
            if total_count == 0 and search_request.query.strip():
                suggestions = await self._get_no_results_suggestions(user_id, search_request.query)
            
            # Build response
            response = ZoteroSearchResponse(
                items=response_items,
                total_count=total_count,
                query=search_request.query,
                filters_applied=self._get_applied_filters(search_request),
                processing_time=processing_time
            )
            
            # Add suggestions if no results
            if suggestions:
                response.suggestions = suggestions
            
            return response
            
        except Exception as e:
            logger.error(f"Search failed for user {user_id}: {str(e)}")
            raise
    
    async def get_search_facets(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        collection_id: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get available facets for search filtering
        
        Args:
            user_id: ID of the user
            library_id: Optional library filter
            collection_id: Optional collection filter
            
        Returns:
            Dictionary of facets with counts
        """
        try:
            # Build base query
            query = self._build_base_query(user_id)
            
            # Apply library filter if specified
            if library_id:
                query = query.filter(ZoteroItem.library_id == library_id)
            
            # Apply collection filter if specified
            if collection_id:
                query = query.join(
                    ZoteroItemCollection,
                    ZoteroItem.id == ZoteroItemCollection.item_id
                ).filter(ZoteroItemCollection.collection_id == collection_id)
            
            # Get all items for facet calculation
            items = query.all()
            
            facets = {
                "item_types": self._calculate_item_type_facets(items),
                "publication_years": self._calculate_year_facets(items),
                "creators": self._calculate_creator_facets(items),
                "tags": self._calculate_tag_facets(items),
                "publishers": self._calculate_publisher_facets(items)
            }
            
            return facets
            
        except Exception as e:
            logger.error(f"Failed to get search facets for user {user_id}: {str(e)}")
            raise
    
    async def suggest_search_terms(
        self,
        user_id: str,
        partial_query: str,
        limit: int = 10
    ) -> List[str]:
        """
        Suggest search terms based on partial input
        
        Args:
            user_id: ID of the user
            partial_query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested search terms
        """
        try:
            if len(partial_query) < 2:
                return []
            
            # Build base query
            query = self._build_base_query(user_id)
            
            suggestions = set()
            
            # Search in titles
            title_matches = query.filter(
                ZoteroItem.title.ilike(f"%{partial_query}%")
            ).limit(limit).all()
            
            for item in title_matches:
                if item.title:
                    # Extract words that contain the partial query
                    words = item.title.split()
                    for word in words:
                        if partial_query.lower() in word.lower():
                            suggestions.add(word.strip('.,!?;:'))
            
            # Search in tags
            tag_query = self.db.query(ZoteroItem).join(ZoteroLibrary).join(ZoteroConnection).filter(
                ZoteroConnection.user_id == user_id,
                ZoteroItem.is_deleted == False,
                func.json_array_length(ZoteroItem.tags) > 0
            )
            
            tag_items = tag_query.all()
            for item in tag_items:
                if item.tags:
                    for tag in item.tags:
                        if partial_query.lower() in tag.lower():
                            suggestions.add(tag)
            
            # Search in creators
            creator_items = query.filter(
                func.json_array_length(ZoteroItem.creators) > 0
            ).all()
            
            for item in creator_items:
                if item.creators:
                    for creator in item.creators:
                        if creator.get('name') and partial_query.lower() in creator['name'].lower():
                            suggestions.add(creator['name'])
                        elif creator.get('last_name') and partial_query.lower() in creator['last_name'].lower():
                            full_name = f"{creator.get('first_name', '')} {creator['last_name']}".strip()
                            suggestions.add(full_name)
            
            return sorted(list(suggestions))[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions for user {user_id}: {str(e)}")
            return []
    
    async def get_similar_references(
        self,
        user_id: str,
        reference_id: str,
        limit: int = 10
    ) -> List[ZoteroItemResponse]:
        """
        Find references similar to the given reference
        
        Args:
            user_id: ID of the user
            reference_id: ID of the reference to find similar items for
            limit: Maximum number of similar references
            
        Returns:
            List of similar references
        """
        try:
            # Get the target reference
            target_ref = self.db.query(ZoteroItem).join(ZoteroLibrary).join(ZoteroConnection).filter(
                ZoteroItem.id == reference_id,
                ZoteroConnection.user_id == user_id,
                ZoteroItem.is_deleted == False
            ).first()
            
            if not target_ref:
                return []
            
            # Build similarity query
            query = self._build_base_query(user_id).filter(
                ZoteroItem.id != reference_id  # Exclude the target reference
            )
            
            # Calculate similarity scores based on various factors
            similarity_conditions = []
            
            # Same item type (high weight)
            if target_ref.item_type:
                similarity_conditions.append(
                    case(
                        (ZoteroItem.item_type == target_ref.item_type, 10),
                        else_=0
                    )
                )
            
            # Same publication year (medium weight)
            if target_ref.publication_year:
                similarity_conditions.append(
                    case(
                        (ZoteroItem.publication_year == target_ref.publication_year, 5),
                        (func.abs(ZoteroItem.publication_year - target_ref.publication_year) <= 2, 2),
                        else_=0
                    )
                )
            
            # Shared tags (high weight)
            if target_ref.tags:
                for tag in target_ref.tags:
                    similarity_conditions.append(
                        case(
                            (func.json_contains(ZoteroItem.tags, f'"{tag}"'), 8),
                            else_=0
                        )
                    )
            
            # Similar title words (medium weight)
            if target_ref.title:
                title_words = target_ref.title.lower().split()
                for word in title_words:
                    if len(word) > 3:  # Only consider meaningful words
                        similarity_conditions.append(
                            case(
                                (func.lower(ZoteroItem.title).like(f"%{word}%"), 3),
                                else_=0
                            )
                        )
            
            # Same creators (high weight)
            if target_ref.creators:
                for creator in target_ref.creators:
                    if creator.get('last_name'):
                        similarity_conditions.append(
                            case(
                                (func.json_contains(
                                    func.cast(ZoteroItem.creators, text),
                                    f'"{creator["last_name"]}"'
                                ), 7),
                                else_=0
                            )
                        )
            
            # Calculate total similarity score
            if similarity_conditions:
                similarity_score = sum(similarity_conditions)
                
                # Order by similarity score and limit results
                similar_refs = query.order_by(desc(similarity_score)).filter(
                    similarity_score > 0
                ).limit(limit).all()
                
                return [self._convert_to_response(ref) for ref in similar_refs]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to find similar references for {reference_id}: {str(e)}")
            return []
    
    async def _get_no_results_suggestions(
        self,
        user_id: str,
        query: str
    ) -> List[str]:
        """
        Generate helpful suggestions when no search results are found
        
        Args:
            user_id: ID of the user
            query: Original search query
            
        Returns:
            List of suggested alternative searches
        """
        try:
            suggestions = []
            query_lower = query.lower().strip()
            
            # Get all available facets to suggest alternatives
            facets = await self.get_search_facets(user_id)
            
            # Suggest similar tags
            if facets.get("tags"):
                for tag_facet in facets["tags"][:10]:  # Top 10 tags
                    tag = tag_facet["value"].lower()
                    if self._calculate_string_similarity(query_lower, tag) > 0.6:
                        suggestions.append(f'Try searching for "{tag_facet["value"]}"')
            
            # Suggest similar creators
            if facets.get("creators"):
                for creator_facet in facets["creators"][:10]:  # Top 10 creators
                    creator = creator_facet["value"].lower()
                    if self._calculate_string_similarity(query_lower, creator) > 0.6:
                        suggestions.append(f'Try searching for author "{creator_facet["value"]}"')
            
            # Suggest broader search terms
            query_words = query_lower.split()
            if len(query_words) > 1:
                # Suggest searching individual words
                for word in query_words:
                    if len(word) > 3:  # Only meaningful words
                        suggestions.append(f'Try searching for just "{word}"')
                        break  # Only suggest one word to avoid too many suggestions
            
            # Suggest removing filters if any are applied
            if len(suggestions) == 0:
                suggestions.extend([
                    "Try removing some search filters",
                    "Try using broader search terms",
                    "Check your spelling",
                    "Try searching in all collections"
                ])
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate no-results suggestions: {str(e)}")
            return ["Try using different search terms", "Check your spelling"]
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using simple character overlap
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0
        
        # Simple character-based similarity
        set1 = set(str1.lower())
        set2 = set(str2.lower())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    # Private helper methods
    
    def _build_base_query(self, user_id: str):
        """Build base query with user access control"""
        return self.db.query(ZoteroItem).join(ZoteroLibrary).join(ZoteroConnection).filter(
            ZoteroConnection.user_id == user_id,
            ZoteroLibrary.is_active == True,
            ZoteroItem.is_deleted == False
        ).options(
            joinedload(ZoteroItem.library),
            joinedload(ZoteroItem.item_collections).joinedload(ZoteroItemCollection.collection)
        )
    
    async def _apply_search_filters(self, query, search_request: ZoteroSearchRequest):
        """Apply full-text search filters"""
        if not search_request.query.strip():
            return query
        
        search_terms = search_request.query.strip().split()
        search_conditions = []
        
        for term in search_terms:
            term_conditions = [
                ZoteroItem.title.ilike(f"%{term}%"),
                ZoteroItem.abstract_note.ilike(f"%{term}%"),
                ZoteroItem.publication_title.ilike(f"%{term}%"),
                ZoteroItem.publisher.ilike(f"%{term}%"),
                ZoteroItem.doi.ilike(f"%{term}%"),
                ZoteroItem.url.ilike(f"%{term}%"),
                func.json_contains(func.cast(ZoteroItem.tags, text), f'"{term}"'),
                func.json_contains(func.cast(ZoteroItem.creators, text), f'"{term}"')
            ]
            
            # Combine term conditions with OR
            search_conditions.append(or_(*term_conditions))
        
        # Combine all search terms with AND
        if search_conditions:
            query = query.filter(and_(*search_conditions))
        
        return query
    
    async def _apply_faceted_filters(self, query, search_request: ZoteroSearchRequest):
        """Apply faceted search filters"""
        # Library filter
        if search_request.library_id:
            query = query.filter(ZoteroItem.library_id == search_request.library_id)
        
        # Collection filter
        if search_request.collection_id:
            query = query.join(
                ZoteroItemCollection,
                ZoteroItem.id == ZoteroItemCollection.item_id
            ).filter(ZoteroItemCollection.collection_id == search_request.collection_id)
        
        # Item type filter
        if search_request.item_type:
            query = query.filter(ZoteroItem.item_type == search_request.item_type)
        
        # Tags filter
        if search_request.tags:
            for tag in search_request.tags:
                query = query.filter(
                    func.json_contains(ZoteroItem.tags, f'"{tag}"')
                )
        
        # Creators filter
        if search_request.creators:
            creator_conditions = []
            for creator in search_request.creators:
                creator_conditions.append(
                    func.json_contains(func.cast(ZoteroItem.creators, text), f'"{creator}"')
                )
            query = query.filter(or_(*creator_conditions))
        
        # Publication year range filter
        if search_request.publication_year_start:
            query = query.filter(ZoteroItem.publication_year >= search_request.publication_year_start)
        
        if search_request.publication_year_end:
            query = query.filter(ZoteroItem.publication_year <= search_request.publication_year_end)
        
        return query
    
    async def _apply_sorting(self, query, search_request: ZoteroSearchRequest):
        """Apply sorting to the query with enhanced relevance scoring"""
        sort_column = getattr(ZoteroItem, search_request.sort_by, None)
        
        if search_request.sort_by == "relevance":
            # Enhanced relevance scoring based on multiple factors
            if search_request.query.strip():
                search_terms = search_request.query.strip().split()
                relevance_score = 0
                
                for term in search_terms:
                    # Title matches get highest score (exact match gets bonus)
                    relevance_score += case(
                        (func.lower(ZoteroItem.title) == term.lower(), 20),  # Exact title match
                        (ZoteroItem.title.ilike(f"{term}%"), 15),  # Title starts with term
                        (ZoteroItem.title.ilike(f"%{term}%"), 10),  # Title contains term
                        else_=0
                    )
                    
                    # Abstract matches get medium-high score
                    relevance_score += case(
                        (ZoteroItem.abstract_note.ilike(f"%{term}%"), 7),
                        else_=0
                    )
                    
                    # Tag matches get high score (exact match gets bonus)
                    relevance_score += case(
                        (func.json_contains(ZoteroItem.tags, f'"{term}"'), 12),  # Exact tag match
                        else_=0
                    )
                    
                    # Creator matches get medium score
                    relevance_score += case(
                        (func.json_contains(func.cast(ZoteroItem.creators, text), f'"{term}"'), 8),
                        else_=0
                    )
                    
                    # Publication title matches get medium score
                    relevance_score += case(
                        (ZoteroItem.publication_title.ilike(f"%{term}%"), 6),
                        else_=0
                    )
                    
                    # DOI matches get medium score
                    relevance_score += case(
                        (ZoteroItem.doi.ilike(f"%{term}%"), 5),
                        else_=0
                    )
                
                # Add recency bonus (newer items get slight boost)
                current_year = datetime.now().year
                relevance_score += case(
                    (ZoteroItem.publication_year == current_year, 2),
                    (ZoteroItem.publication_year >= current_year - 1, 1),
                    else_=0
                )
                
                # Add item type preference (articles typically more relevant)
                relevance_score += case(
                    (ZoteroItem.item_type == 'article', 1),
                    else_=0
                )
                
                if search_request.sort_order.lower() == "asc":
                    query = query.order_by(asc(relevance_score), desc(ZoteroItem.date_modified))
                else:
                    query = query.order_by(desc(relevance_score), desc(ZoteroItem.date_modified))
            else:
                # Default to date_modified for relevance without search terms
                query = query.order_by(desc(ZoteroItem.date_modified))
        
        elif sort_column:
            if search_request.sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column), desc(ZoteroItem.date_modified))
            else:
                query = query.order_by(desc(sort_column), desc(ZoteroItem.date_modified))
        else:
            # Default sorting
            query = query.order_by(desc(ZoteroItem.date_modified))
        
        return query
    
    def _get_applied_filters(self, search_request: ZoteroSearchRequest) -> Dict[str, Any]:
        """Get dictionary of applied filters"""
        filters = {}
        
        if search_request.library_id:
            filters["library_id"] = search_request.library_id
        
        if search_request.collection_id:
            filters["collection_id"] = search_request.collection_id
        
        if search_request.item_type:
            filters["item_type"] = search_request.item_type
        
        if search_request.tags:
            filters["tags"] = search_request.tags
        
        if search_request.creators:
            filters["creators"] = search_request.creators
        
        if search_request.publication_year_start:
            filters["publication_year_start"] = search_request.publication_year_start
        
        if search_request.publication_year_end:
            filters["publication_year_end"] = search_request.publication_year_end
        
        filters["sort_by"] = search_request.sort_by
        filters["sort_order"] = search_request.sort_order
        filters["limit"] = search_request.limit
        filters["offset"] = search_request.offset
        
        return filters
    
    def _calculate_item_type_facets(self, items: List[ZoteroItem]) -> List[Dict[str, Any]]:
        """Calculate item type facets"""
        type_counts = {}
        for item in items:
            if item.item_type:
                type_counts[item.item_type] = type_counts.get(item.item_type, 0) + 1
        
        return [
            {"value": item_type, "count": count}
            for item_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    
    def _calculate_year_facets(self, items: List[ZoteroItem]) -> List[Dict[str, Any]]:
        """Calculate publication year facets"""
        year_counts = {}
        for item in items:
            if item.publication_year:
                year_counts[item.publication_year] = year_counts.get(item.publication_year, 0) + 1
        
        return [
            {"value": year, "count": count}
            for year, count in sorted(year_counts.items(), key=lambda x: x[0], reverse=True)
        ][:20]  # Limit to top 20 years
    
    def _calculate_creator_facets(self, items: List[ZoteroItem]) -> List[Dict[str, Any]]:
        """Calculate creator facets"""
        creator_counts = {}
        for item in items:
            if item.creators:
                for creator in item.creators:
                    name = creator.get('name')
                    if not name and creator.get('last_name'):
                        name = f"{creator.get('first_name', '')} {creator['last_name']}".strip()
                    
                    if name:
                        creator_counts[name] = creator_counts.get(name, 0) + 1
        
        return [
            {"value": creator, "count": count}
            for creator, count in sorted(creator_counts.items(), key=lambda x: x[1], reverse=True)
        ][:50]  # Limit to top 50 creators
    
    def _calculate_tag_facets(self, items: List[ZoteroItem]) -> List[Dict[str, Any]]:
        """Calculate tag facets"""
        tag_counts = {}
        for item in items:
            if item.tags:
                for tag in item.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return [
            {"value": tag, "count": count}
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        ][:100]  # Limit to top 100 tags
    
    def _calculate_publisher_facets(self, items: List[ZoteroItem]) -> List[Dict[str, Any]]:
        """Calculate publisher facets"""
        publisher_counts = {}
        for item in items:
            if item.publisher:
                publisher_counts[item.publisher] = publisher_counts.get(item.publisher, 0) + 1
        
        return [
            {"value": publisher, "count": count}
            for publisher, count in sorted(publisher_counts.items(), key=lambda x: x[1], reverse=True)
        ][:30]  # Limit to top 30 publishers
    
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
def get_search_service(db: Session = None) -> ZoteroSearchService:
    """Get search service instance"""
    if db is None:
        db = next(get_db())
    return ZoteroSearchService(db)