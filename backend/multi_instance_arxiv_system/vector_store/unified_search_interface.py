"""
Unified Search Interface for Multi-Instance Vector Store.

This module provides a unified search interface that can search across multiple
scholar instances with advanced filtering, ranking, and result aggregation.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
    from multi_instance_arxiv_system.shared.multi_instance_data_models import BasePaper
except ImportError as e:
    print(f"Import error: {e}")
    raise

logger = logging.getLogger(__name__)


class SearchScope(Enum):
    """Search scope options."""
    SINGLE_INSTANCE = "single_instance"
    ALL_INSTANCES = "all_instances"
    SPECIFIC_INSTANCES = "specific_instances"


class SortOrder(Enum):
    """Sort order options."""
    RELEVANCE_DESC = "relevance_desc"
    RELEVANCE_ASC = "relevance_asc"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"


@dataclass
class SearchFilter:
    """Search filter configuration."""
    
    # Instance filtering
    instances: Optional[List[str]] = None
    exclude_instances: Optional[List[str]] = None
    
    # Content filtering
    sections: Optional[List[str]] = None
    paper_types: Optional[List[str]] = None  # 'arxiv', 'journal'
    
    # Date filtering
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    # Quality filtering
    min_quality_score: Optional[float] = None
    min_relevance_score: Optional[float] = None
    
    # Metadata filtering
    authors: Optional[List[str]] = None
    journals: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    
    # Advanced filtering
    contains_equations: Optional[bool] = None
    contains_code: Optional[bool] = None
    contains_tables: Optional[bool] = None
    
    # Research area filtering (instance-specific)
    research_areas: Optional[List[str]] = None
    research_domains: Optional[List[str]] = None


@dataclass
class SearchResult:
    """Enhanced search result with unified metadata."""
    
    # Core result data
    id: str
    document: str
    relevance_score: float
    distance: float
    rank: int
    
    # Instance information
    instance_name: str
    collection_name: str
    
    # Document metadata
    metadata: Dict[str, Any]
    
    # Enhanced fields
    paper_id: str
    title: str
    authors: List[str]
    published_date: datetime
    section: str
    chunk_type: str
    
    # Quality indicators
    text_quality_score: float
    section_importance: float
    
    # Instance-specific fields
    instance_specific_data: Dict[str, Any]


@dataclass
class SearchSummary:
    """Summary of search results."""
    
    total_results: int
    instances_searched: List[str]
    instances_with_results: Dict[str, int]
    search_time_seconds: float
    
    # Result distribution
    results_by_section: Dict[str, int]
    results_by_paper_type: Dict[str, int]
    results_by_quality: Dict[str, int]  # high, medium, low
    
    # Quality metrics
    average_relevance: float
    average_quality: float
    
    # Filters applied
    filters_applied: SearchFilter
    query_processed: str


class UnifiedSearchInterface:
    """
    Unified search interface for multi-instance vector store with advanced
    filtering, ranking, and result aggregation capabilities.
    """
    
    def __init__(self, vector_store_service: MultiInstanceVectorStoreService):
        self.vector_store_service = vector_store_service
        self.search_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
        # Default search configuration
        self.default_config = {
            'max_results_per_instance': 50,
            'result_aggregation_strategy': 'interleave',
            'relevance_threshold': 0.0,
            'quality_threshold': 0.0,
            'enable_query_expansion': True,
            'enable_result_reranking': True
        }
    
    async def search(
        self,
        query: str,
        scope: SearchScope = SearchScope.ALL_INSTANCES,
        target_instances: Optional[List[str]] = None,
        filters: Optional[SearchFilter] = None,
        max_results: int = 20,
        sort_order: SortOrder = SortOrder.RELEVANCE_DESC,
        enable_highlighting: bool = False
    ) -> Tuple[List[SearchResult], SearchSummary]:
        """
        Perform unified search across specified instances.
        """
        
        start_time = datetime.now()
        
        try:
            # Validate and prepare search parameters
            instances_to_search = self._determine_search_instances(scope, target_instances)
            processed_query = self._preprocess_query(query)
            search_filters = filters or SearchFilter()
            
            # Execute search across instances
            raw_results = await self._execute_multi_instance_search(
                processed_query,
                instances_to_search,
                search_filters,
                max_results
            )
            
            # Process and enhance results
            enhanced_results = self._enhance_search_results(raw_results)
            
            # Apply post-search filtering
            filtered_results = self._apply_post_search_filters(enhanced_results, search_filters)
            
            # Sort and rank results
            sorted_results = self._sort_and_rank_results(filtered_results, sort_order)
            
            # Limit results
            final_results = sorted_results[:max_results]
            
            # Add highlighting if requested
            if enable_highlighting:
                final_results = self._add_result_highlighting(final_results, processed_query)
            
            # Generate search summary
            search_time = (datetime.now() - start_time).total_seconds()
            summary = self._generate_search_summary(
                final_results,
                instances_to_search,
                search_filters,
                processed_query,
                search_time
            )
            
            # Store in search history
            self._store_search_history(query, scope, filters, len(final_results), search_time)
            
            logger.info(f"Unified search completed: {len(final_results)} results in {search_time:.3f}s")
            return final_results, summary
            
        except Exception as e:
            logger.error(f"Error in unified search: {e}")
            raise
    
    def _determine_search_instances(
        self,
        scope: SearchScope,
        target_instances: Optional[List[str]]
    ) -> List[str]:
        """Determine which instances to search based on scope."""
        
        available_instances = list(self.vector_store_service.initialized_instances)
        
        if scope == SearchScope.SINGLE_INSTANCE:
            if target_instances and len(target_instances) == 1:
                return [target_instances[0]]
            elif available_instances:
                return [available_instances[0]]  # Default to first available
            else:
                return []
        
        elif scope == SearchScope.ALL_INSTANCES:
            return available_instances
        
        elif scope == SearchScope.SPECIFIC_INSTANCES:
            if target_instances:
                # Return intersection of requested and available instances
                return [inst for inst in target_instances if inst in available_instances]
            else:
                return available_instances
        
        return available_instances
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess the search query."""
        
        # Basic query cleaning
        processed_query = query.strip()
        
        # Query expansion (if enabled)
        if self.default_config.get('enable_query_expansion', True):
            processed_query = self._expand_query(processed_query)
        
        return processed_query
    
    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms."""
        
        # Simple query expansion with domain-specific synonyms
        expansions = {
            'machine learning': 'machine learning ML artificial intelligence AI',
            'deep learning': 'deep learning neural networks deep neural networks',
            'natural language processing': 'natural language processing NLP text processing',
            'computer vision': 'computer vision image processing visual recognition',
            'portfolio': 'portfolio asset allocation investment strategy',
            'risk management': 'risk management risk assessment risk control',
            'time series': 'time series temporal data sequential data',
            'regression': 'regression linear regression statistical modeling'
        }
        
        query_lower = query.lower()
        for term, expansion in expansions.items():
            if term in query_lower:
                query = query.replace(term, expansion)
        
        return query
    
    async def _execute_multi_instance_search(
        self,
        query: str,
        instances: List[str],
        filters: SearchFilter,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Execute search across multiple instances."""
        
        all_results = []
        search_tasks = []
        
        # Calculate results per instance
        results_per_instance = min(
            self.default_config['max_results_per_instance'],
            max(1, max_results // len(instances)) if instances else max_results
        )
        
        # Create search tasks for each instance
        for instance_name in instances:
            # Convert SearchFilter to instance-specific filters
            instance_filters = self._convert_to_instance_filters(filters, instance_name)
            
            task = self.vector_store_service.search_instance_papers(
                instance_name=instance_name,
                query=query,
                n_results=results_per_instance,
                filters=instance_filters
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
        
        return all_results
    
    def _convert_to_instance_filters(
        self,
        search_filters: SearchFilter,
        instance_name: str
    ) -> Dict[str, Any]:
        """Convert SearchFilter to instance-specific filter format."""
        
        filters = {}
        
        # Date filters
        if search_filters.date_from:
            filters['year_from'] = search_filters.date_from.year
        if search_filters.date_to:
            filters['year_to'] = search_filters.date_to.year
        
        # Section filters
        if search_filters.sections:
            filters['sections'] = search_filters.sections
        
        # Journal filters
        if search_filters.journals:
            filters['journals'] = search_filters.journals
        
        # Relevance filter
        if search_filters.min_relevance_score:
            filters['min_relevance'] = search_filters.min_relevance_score
        
        return filters
    
    def _enhance_search_results(self, raw_results: List[Dict[str, Any]]) -> List[SearchResult]:
        """Enhance raw search results with unified metadata."""
        
        enhanced_results = []
        
        for result in raw_results:
            try:
                metadata = result.get('metadata', {})
                
                # Extract core information
                enhanced_result = SearchResult(
                    id=result.get('id', ''),
                    document=result.get('document', ''),
                    relevance_score=result.get('relevance_score', 0.0),
                    distance=result.get('distance', 1.0),
                    rank=result.get('rank', 0),
                    
                    # Instance information
                    instance_name=result.get('instance_name', ''),
                    collection_name=result.get('collection_name', ''),
                    
                    # Document metadata
                    metadata=metadata,
                    
                    # Enhanced fields
                    paper_id=metadata.get('paper_id', ''),
                    title=metadata.get('title', ''),
                    authors=metadata.get('authors', []),
                    published_date=self._parse_date(metadata.get('published_date', '')),
                    section=metadata.get('section', ''),
                    chunk_type=metadata.get('chunk_type', ''),
                    
                    # Quality indicators
                    text_quality_score=metadata.get('text_quality_score', 0.0),
                    section_importance=metadata.get('section_importance', 0.5),
                    
                    # Instance-specific data
                    instance_specific_data=self._extract_instance_specific_data(metadata, result.get('instance_name', ''))
                )
                
                enhanced_results.append(enhanced_result)
                
            except Exception as e:
                logger.error(f"Error enhancing search result: {e}")
                continue
        
        return enhanced_results
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        
        if not date_str:
            return datetime.min
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Try other common formats
                return datetime.strptime(date_str, '%Y-%m-%d')
            except:
                return datetime.min
    
    def _extract_instance_specific_data(
        self,
        metadata: Dict[str, Any],
        instance_name: str
    ) -> Dict[str, Any]:
        """Extract instance-specific data from metadata."""
        
        instance_data = {}
        
        if instance_name.lower() in ['ai_scholar', 'ai-scholar']:
            instance_data = {
                'research_area': metadata.get('research_area', ''),
                'technical_complexity': metadata.get('technical_complexity', 0.0),
                'contains_equations': metadata.get('contains_equations', False),
                'contains_code': metadata.get('contains_code', False),
                'ml_keywords_count': metadata.get('ml_keywords_count', 0),
                'citation_density': metadata.get('citation_density', 0.0)
            }
        elif instance_name.lower() in ['quant_scholar', 'quant-scholar']:
            instance_data = {
                'research_domain': metadata.get('research_domain', ''),
                'statistical_complexity': metadata.get('statistical_complexity', 0.0),
                'contains_formulas': metadata.get('contains_formulas', False),
                'contains_tables': metadata.get('contains_tables', False),
                'financial_keywords_count': metadata.get('financial_keywords_count', 0),
                'statistical_methods_count': metadata.get('statistical_methods_count', 0)
            }
        
        return instance_data
    
    def _apply_post_search_filters(
        self,
        results: List[SearchResult],
        filters: SearchFilter
    ) -> List[SearchResult]:
        """Apply additional filters to search results."""
        
        filtered_results = results
        
        # Quality score filter
        if filters.min_quality_score is not None:
            filtered_results = [
                r for r in filtered_results 
                if r.text_quality_score >= filters.min_quality_score
            ]
        
        # Relevance score filter
        if filters.min_relevance_score is not None:
            filtered_results = [
                r for r in filtered_results 
                if r.relevance_score >= filters.min_relevance_score
            ]
        
        # Date range filter
        if filters.date_from or filters.date_to:
            filtered_results = [
                r for r in filtered_results
                if self._date_in_range(r.published_date, filters.date_from, filters.date_to)
            ]
        
        # Author filter
        if filters.authors:
            filtered_results = [
                r for r in filtered_results
                if any(author.lower() in [a.lower() for a in r.authors] for author in filters.authors)
            ]
        
        # Paper type filter
        if filters.paper_types:
            filtered_results = [
                r for r in filtered_results
                if r.metadata.get('paper_type', '') in filters.paper_types
            ]
        
        # Advanced content filters
        if filters.contains_equations is not None:
            filtered_results = [
                r for r in filtered_results
                if r.instance_specific_data.get('contains_equations', False) == filters.contains_equations
            ]
        
        if filters.contains_code is not None:
            filtered_results = [
                r for r in filtered_results
                if r.instance_specific_data.get('contains_code', False) == filters.contains_code
            ]
        
        if filters.contains_tables is not None:
            filtered_results = [
                r for r in filtered_results
                if r.instance_specific_data.get('contains_tables', False) == filters.contains_tables
            ]
        
        return filtered_results
    
    def _date_in_range(
        self,
        date: datetime,
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> bool:
        """Check if date is within specified range."""
        
        if date_from and date < date_from:
            return False
        if date_to and date > date_to:
            return False
        return True
    
    def _sort_and_rank_results(
        self,
        results: List[SearchResult],
        sort_order: SortOrder
    ) -> List[SearchResult]:
        """Sort and re-rank search results."""
        
        if sort_order == SortOrder.RELEVANCE_DESC:
            sorted_results = sorted(results, key=lambda r: r.relevance_score, reverse=True)
        elif sort_order == SortOrder.RELEVANCE_ASC:
            sorted_results = sorted(results, key=lambda r: r.relevance_score)
        elif sort_order == SortOrder.DATE_DESC:
            sorted_results = sorted(results, key=lambda r: r.published_date, reverse=True)
        elif sort_order == SortOrder.DATE_ASC:
            sorted_results = sorted(results, key=lambda r: r.published_date)
        elif sort_order == SortOrder.TITLE_ASC:
            sorted_results = sorted(results, key=lambda r: r.title.lower())
        elif sort_order == SortOrder.TITLE_DESC:
            sorted_results = sorted(results, key=lambda r: r.title.lower(), reverse=True)
        else:
            sorted_results = results
        
        # Re-rank results
        for i, result in enumerate(sorted_results):
            result.rank = i + 1
        
        # Apply result reranking if enabled
        if self.default_config.get('enable_result_reranking', True):
            sorted_results = self._rerank_results(sorted_results)
        
        return sorted_results
    
    def _rerank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Apply advanced reranking based on multiple factors."""
        
        # Calculate composite scores
        for result in results:
            # Base score from relevance
            composite_score = result.relevance_score * 0.6
            
            # Quality factor
            composite_score += result.text_quality_score * 0.2
            
            # Section importance factor
            composite_score += result.section_importance * 0.1
            
            # Recency factor (boost recent papers)
            days_old = (datetime.now() - result.published_date).days
            recency_factor = max(0, 1 - (days_old / 3650))  # 10-year decay
            composite_score += recency_factor * 0.1
            
            result.relevance_score = composite_score
        
        # Re-sort by composite score
        reranked_results = sorted(results, key=lambda r: r.relevance_score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(reranked_results):
            result.rank = i + 1
        
        return reranked_results
    
    def _add_result_highlighting(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """Add highlighting to search results."""
        
        query_terms = query.lower().split()
        
        for result in results:
            # Highlight query terms in document text
            highlighted_text = result.document
            for term in query_terms:
                if len(term) > 2:  # Only highlight meaningful terms
                    highlighted_text = self._highlight_term(highlighted_text, term)
            
            # Store highlighted text in metadata
            result.metadata['highlighted_text'] = highlighted_text
        
        return results
    
    def _highlight_term(self, text: str, term: str) -> str:
        """Highlight a specific term in text."""
        
        import re
        
        # Case-insensitive highlighting
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted = pattern.sub(f'<mark>{term}</mark>', text)
        
        return highlighted
    
    def _generate_search_summary(
        self,
        results: List[SearchResult],
        instances_searched: List[str],
        filters: SearchFilter,
        query: str,
        search_time: float
    ) -> SearchSummary:
        """Generate comprehensive search summary."""
        
        # Count results by instance
        instances_with_results = {}
        for result in results:
            instance = result.instance_name
            instances_with_results[instance] = instances_with_results.get(instance, 0) + 1
        
        # Count results by section
        results_by_section = {}
        for result in results:
            section = result.section
            results_by_section[section] = results_by_section.get(section, 0) + 1
        
        # Count results by paper type
        results_by_paper_type = {}
        for result in results:
            paper_type = result.metadata.get('paper_type', 'unknown')
            results_by_paper_type[paper_type] = results_by_paper_type.get(paper_type, 0) + 1
        
        # Count results by quality
        results_by_quality = {'high': 0, 'medium': 0, 'low': 0}
        for result in results:
            quality = result.text_quality_score
            if quality >= 0.8:
                results_by_quality['high'] += 1
            elif quality >= 0.5:
                results_by_quality['medium'] += 1
            else:
                results_by_quality['low'] += 1
        
        # Calculate averages
        average_relevance = sum(r.relevance_score for r in results) / len(results) if results else 0.0
        average_quality = sum(r.text_quality_score for r in results) / len(results) if results else 0.0
        
        return SearchSummary(
            total_results=len(results),
            instances_searched=instances_searched,
            instances_with_results=instances_with_results,
            search_time_seconds=search_time,
            results_by_section=results_by_section,
            results_by_paper_type=results_by_paper_type,
            results_by_quality=results_by_quality,
            average_relevance=average_relevance,
            average_quality=average_quality,
            filters_applied=filters,
            query_processed=query
        )
    
    def _store_search_history(
        self,
        query: str,
        scope: SearchScope,
        filters: Optional[SearchFilter],
        result_count: int,
        search_time: float
    ) -> None:
        """Store search in history."""
        
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'scope': scope.value,
            'filters': filters.__dict__ if filters else {},
            'result_count': result_count,
            'search_time_seconds': search_time
        }
        
        self.search_history.append(history_entry)
        
        # Maintain history size limit
        if len(self.search_history) > self.max_history_size:
            self.search_history = self.search_history[-self.max_history_size:]
    
    async def search_similar_to_document(
        self,
        document_id: str,
        instance_name: str,
        max_results: int = 10,
        exclude_same_paper: bool = True,
        cross_instance: bool = True
    ) -> Tuple[List[SearchResult], SearchSummary]:
        """Search for documents similar to a specific document."""
        
        try:
            # Get the reference document
            # This would require additional implementation in the vector store service
            # For now, we'll use a placeholder approach
            
            # Find similar papers using the existing method
            similar_results = await self.vector_store_service.search_all_instances(
                query=f"document_id:{document_id}",  # Placeholder query
                n_results=max_results * 2
            )
            
            # Convert to SearchResult format
            enhanced_results = self._enhance_search_results(similar_results)
            
            # Filter out the reference document if requested
            if exclude_same_paper:
                enhanced_results = [
                    r for r in enhanced_results 
                    if r.metadata.get('document_id') != document_id
                ]
            
            # Limit results
            final_results = enhanced_results[:max_results]
            
            # Generate summary
            summary = SearchSummary(
                total_results=len(final_results),
                instances_searched=list(self.vector_store_service.initialized_instances),
                instances_with_results={r.instance_name: 1 for r in final_results},
                search_time_seconds=0.0,  # Placeholder
                results_by_section={},
                results_by_paper_type={},
                results_by_quality={},
                average_relevance=0.0,
                average_quality=0.0,
                filters_applied=SearchFilter(),
                query_processed=f"similar_to:{document_id}"
            )
            
            return final_results, summary
            
        except Exception as e:
            logger.error(f"Error in similar document search: {e}")
            raise
    
    def get_search_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent search history."""
        return self.search_history[-limit:]
    
    def clear_search_history(self) -> int:
        """Clear search history and return number of entries cleared."""
        count = len(self.search_history)
        self.search_history.clear()
        return count
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search usage statistics."""
        
        if not self.search_history:
            return {}
        
        total_searches = len(self.search_history)
        total_results = sum(entry['result_count'] for entry in self.search_history)
        average_results = total_results / total_searches if total_searches > 0 else 0
        average_time = sum(entry['search_time_seconds'] for entry in self.search_history) / total_searches
        
        # Most common queries
        query_counts = {}
        for entry in self.search_history:
            query = entry['query']
            query_counts[query] = query_counts.get(query, 0) + 1
        
        most_common_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_searches': total_searches,
            'total_results': total_results,
            'average_results_per_search': average_results,
            'average_search_time_seconds': average_time,
            'most_common_queries': most_common_queries,
            'search_history_size': len(self.search_history)
        }