"""
Zotero Citation Management Service

This service handles citation management features including citation history,
favorites, style switching, and clipboard integration support.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_

from models.zotero_models import (
    ZoteroItem, ZoteroCitationStyle, ZoteroUserPreferences,
    ZoteroCitationHistory, ZoteroCitationFavorites, ZoteroCitationStylePreview
)
from core.database import get_db
from core.logging_config import get_logger
from services.zotero.zotero_citation_service import ZoteroCitationService

logger = get_logger(__name__)


class CitationManagementError(Exception):
    """Exception raised for citation management related errors"""
    pass


class ZoteroCitationManagementService:
    """Service for handling citation management functionality"""
    
    def __init__(self, db: Session):
        self.db = db
        self.citation_service = ZoteroCitationService(db)
    
    async def add_to_citation_history(
        self,
        user_id: str,
        item_ids: List[str],
        citation_style: str,
        format_type: str,
        citations: List[str],
        session_id: Optional[str] = None
    ) -> str:
        """
        Add citations to user's citation history
        
        Args:
            user_id: User ID
            item_ids: List of item IDs that were cited
            citation_style: Citation style used
            format_type: Output format used
            citations: Generated citations
            session_id: Optional session identifier
            
        Returns:
            History entry ID
        """
        try:
            # Check if similar entry exists (same items, style, format within last hour)
            recent_cutoff = datetime.now() - timedelta(hours=1)
            existing_entry = self.db.query(ZoteroCitationHistory).filter(
                and_(
                    ZoteroCitationHistory.user_id == user_id,
                    ZoteroCitationHistory.item_ids == item_ids,
                    ZoteroCitationHistory.citation_style == citation_style,
                    ZoteroCitationHistory.format_type == format_type,
                    ZoteroCitationHistory.created_at > recent_cutoff
                )
            ).first()
            
            if existing_entry:
                # Update access count and timestamp
                existing_entry.access_count += 1
                existing_entry.last_accessed = datetime.now()
                self.db.commit()
                logger.info(f"Updated existing citation history entry for user {user_id}")
                return existing_entry.id
            
            # Create new history entry
            history_entry = ZoteroCitationHistory(
                user_id=user_id,
                item_ids=item_ids,
                citation_style=citation_style,
                format_type=format_type,
                citations=citations,
                session_id=session_id,
                access_count=1,
                last_accessed=datetime.now()
            )
            
            self.db.add(history_entry)
            self.db.commit()
            
            # Clean up old entries (keep only last 100 per user)
            await self._cleanup_old_history_entries(user_id, keep_count=100)
            
            logger.info(f"Added citation to history for user {user_id}")
            return history_entry.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add citation to history: {str(e)}")
            raise CitationManagementError(f"Failed to add citation to history: {str(e)}")
    
    async def get_citation_history(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get user's citation history
        
        Args:
            user_id: User ID
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            
        Returns:
            Dictionary with history entries and metadata
        """
        try:
            # Get total count
            total_count = self.db.query(ZoteroCitationHistory).filter(
                ZoteroCitationHistory.user_id == user_id
            ).count()
            
            # Get paginated history entries
            history_entries = self.db.query(ZoteroCitationHistory).filter(
                ZoteroCitationHistory.user_id == user_id
            ).order_by(desc(ZoteroCitationHistory.last_accessed)).offset(offset).limit(limit).all()
            
            # Convert to response format
            history = []
            for entry in history_entries:
                history.append({
                    'id': entry.id,
                    'item_ids': entry.item_ids,
                    'citation_style': entry.citation_style,
                    'format_type': entry.format_type,
                    'citations': entry.citations,
                    'access_count': entry.access_count,
                    'last_accessed': entry.last_accessed.isoformat(),
                    'created_at': entry.created_at.isoformat(),
                    'session_id': entry.session_id
                })
            
            return {
                'history': history,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get citation history: {str(e)}")
            raise CitationManagementError(f"Failed to get citation history: {str(e)}")
    
    async def clear_citation_history(self, user_id: str) -> None:
        """Clear user's citation history"""
        try:
            deleted_count = self.db.query(ZoteroCitationHistory).filter(
                ZoteroCitationHistory.user_id == user_id
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleared {deleted_count} citation history entries for user {user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to clear citation history: {str(e)}")
            raise CitationManagementError(f"Failed to clear citation history: {str(e)}")
    
    async def add_to_favorites(
        self,
        user_id: str,
        item_id: str,
        citation_style: str,
        format_type: str,
        citation: str,
        note: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Add citation to user's favorites
        
        Args:
            user_id: User ID
            item_id: Item ID
            citation_style: Citation style
            format_type: Output format
            citation: Generated citation
            note: Optional user note
            tags: Optional user-defined tags
            
        Returns:
            Favorite ID
        """
        try:
            if tags is None:
                tags = []
            
            # Check if already in favorites (same user, item, and style)
            existing_favorite = self.db.query(ZoteroCitationFavorites).filter(
                and_(
                    ZoteroCitationFavorites.user_id == user_id,
                    ZoteroCitationFavorites.item_id == item_id,
                    ZoteroCitationFavorites.citation_style == citation_style
                )
            ).first()
            
            if existing_favorite:
                # Update existing favorite
                existing_favorite.citation = citation
                existing_favorite.format_type = format_type
                existing_favorite.user_note = note
                existing_favorite.tags = tags
                existing_favorite.last_accessed = datetime.now()
                existing_favorite.updated_at = datetime.now()
                self.db.commit()
                
                logger.info(f"Updated existing favorite citation for user {user_id}")
                return existing_favorite.id
            
            # Create new favorite
            favorite_entry = ZoteroCitationFavorites(
                user_id=user_id,
                item_id=item_id,
                citation_style=citation_style,
                format_type=format_type,
                citation=citation,
                user_note=note,
                tags=tags,
                access_count=0,
                last_accessed=datetime.now()
            )
            
            self.db.add(favorite_entry)
            self.db.commit()
            
            logger.info(f"Added citation to favorites for user {user_id}")
            return favorite_entry.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add citation to favorites: {str(e)}")
            raise CitationManagementError(f"Failed to add citation to favorites: {str(e)}")
    
    async def get_citation_favorites(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get user's favorite citations
        
        Args:
            user_id: User ID
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            
        Returns:
            Dictionary with favorite entries and metadata
        """
        try:
            # Get total count
            total_count = self.db.query(ZoteroCitationFavorites).filter(
                ZoteroCitationFavorites.user_id == user_id
            ).count()
            
            # Get paginated favorites
            favorite_entries = self.db.query(ZoteroCitationFavorites).filter(
                ZoteroCitationFavorites.user_id == user_id
            ).order_by(desc(ZoteroCitationFavorites.last_accessed)).offset(offset).limit(limit).all()
            
            # Convert to response format
            favorites = []
            for entry in favorite_entries:
                favorites.append({
                    'id': entry.id,
                    'item_id': entry.item_id,
                    'citation_style': entry.citation_style,
                    'format_type': entry.format_type,
                    'citation': entry.citation,
                    'user_note': entry.user_note,
                    'tags': entry.tags,
                    'access_count': entry.access_count,
                    'last_accessed': entry.last_accessed.isoformat(),
                    'created_at': entry.created_at.isoformat(),
                    'updated_at': entry.updated_at.isoformat()
                })
            
            return {
                'favorites': favorites,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get citation favorites: {str(e)}")
            raise CitationManagementError(f"Failed to get citation favorites: {str(e)}")
    
    async def remove_from_favorites(self, user_id: str, favorite_id: str) -> bool:
        """
        Remove citation from user's favorites
        
        Args:
            user_id: User ID
            favorite_id: Favorite ID to remove
            
        Returns:
            True if removed, False if not found
        """
        try:
            deleted_count = self.db.query(ZoteroCitationFavorites).filter(
                and_(
                    ZoteroCitationFavorites.user_id == user_id,
                    ZoteroCitationFavorites.id == favorite_id
                )
            ).delete()
            
            self.db.commit()
            
            if deleted_count > 0:
                logger.info(f"Removed citation from favorites for user {user_id}")
                return True
            else:
                logger.warning(f"Favorite {favorite_id} not found for user {user_id}")
                return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove citation from favorites: {str(e)}")
            raise CitationManagementError(f"Failed to remove citation from favorites: {str(e)}")
    
    async def preview_citation_styles(
        self,
        item_id: str,
        styles: Optional[List[str]] = None,
        format_type: str = 'text',
        user_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate citation previews in multiple styles
        
        Args:
            item_id: Item ID to preview
            styles: List of styles to preview (defaults to all supported)
            format_type: Output format
            user_id: User ID for caching
            
        Returns:
            Dictionary mapping style names to citation previews
        """
        try:
            # Get supported styles if not specified
            if not styles:
                supported_styles = await self.citation_service.get_supported_styles()
                styles = list(supported_styles.keys())
            
            previews = {}
            cache_expiry = datetime.now() + timedelta(minutes=30)  # Cache for 30 minutes
            
            for style in styles:
                # Check cache first
                cached_preview = self.db.query(ZoteroCitationStylePreview).filter(
                    and_(
                        ZoteroCitationStylePreview.item_id == item_id,
                        ZoteroCitationStylePreview.citation_style == style,
                        ZoteroCitationStylePreview.format_type == format_type,
                        ZoteroCitationStylePreview.cache_expires_at > datetime.now()
                    )
                ).first()
                
                if cached_preview:
                    previews[style] = cached_preview.citation_preview
                    continue
                
                # Generate new preview
                try:
                    response = await self.citation_service.generate_citations(
                        item_ids=[item_id],
                        citation_style=style,
                        format_type=format_type,
                        user_id=user_id
                    )
                    
                    if response.citations:
                        citation_preview = response.citations[0]
                        previews[style] = citation_preview
                        
                        # Cache the preview
                        preview_cache = ZoteroCitationStylePreview(
                            item_id=item_id,
                            citation_style=style,
                            format_type=format_type,
                            citation_preview=citation_preview,
                            cache_expires_at=cache_expiry
                        )
                        self.db.add(preview_cache)
                        
                    else:
                        previews[style] = f"[Unable to generate {style} citation]"
                        
                except Exception as e:
                    logger.warning(f"Failed to generate {style} preview: {str(e)}")
                    previews[style] = f"[Error generating {style} citation]"
            
            # Commit cache entries
            try:
                self.db.commit()
            except Exception as e:
                logger.warning(f"Failed to cache style previews: {str(e)}")
                self.db.rollback()
            
            return previews
            
        except Exception as e:
            logger.error(f"Failed to generate citation style previews: {str(e)}")
            raise CitationManagementError(f"Failed to generate citation style previews: {str(e)}")
    
    async def get_clipboard_data(
        self,
        citations: List[str],
        format_type: str = 'text',
        include_metadata: bool = False
    ) -> Dict[str, Any]:
        """
        Prepare citation data for clipboard integration
        
        Args:
            citations: List of citations to prepare
            format_type: Output format
            include_metadata: Whether to include metadata
            
        Returns:
            Dictionary with clipboard-ready data
        """
        try:
            if format_type == 'html':
                # Prepare HTML format for rich text clipboard
                html_content = '<div class="citations">\n'
                for i, citation in enumerate(citations):
                    html_content += f'<p class="citation" data-index="{i}">{citation}</p>\n'
                html_content += '</div>'
                
                clipboard_data = {
                    'text': '\n\n'.join(citations),
                    'html': html_content,
                    'format': format_type
                }
                
            elif format_type == 'rtf':
                # Prepare RTF format
                rtf_content = '{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}\\f0\\fs24 '
                for citation in citations:
                    rtf_content += citation.replace('\n', '\\par\n') + '\\par\\par\n'
                rtf_content += '}'
                
                clipboard_data = {
                    'text': '\n\n'.join(citations),
                    'rtf': rtf_content,
                    'format': format_type
                }
                
            else:
                # Plain text format
                clipboard_data = {
                    'text': '\n\n'.join(citations),
                    'format': format_type
                }
            
            if include_metadata:
                clipboard_data['metadata'] = {
                    'citation_count': len(citations),
                    'generated_at': datetime.now().isoformat(),
                    'source': 'AI Scholar Zotero Integration'
                }
            
            return clipboard_data
            
        except Exception as e:
            logger.error(f"Failed to prepare clipboard data: {str(e)}")
            raise CitationManagementError(f"Failed to prepare clipboard data: {str(e)}")
    
    async def get_citation_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get citation usage statistics for user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with usage statistics
        """
        try:
            # Get total counts
            total_citations = self.db.query(ZoteroCitationHistory).filter(
                ZoteroCitationHistory.user_id == user_id
            ).count()
            
            total_favorites = self.db.query(ZoteroCitationFavorites).filter(
                ZoteroCitationFavorites.user_id == user_id
            ).count()
            
            # Recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_citations_count = self.db.query(ZoteroCitationHistory).filter(
                and_(
                    ZoteroCitationHistory.user_id == user_id,
                    ZoteroCitationHistory.created_at > week_ago
                )
            ).count()
            
            # Style usage statistics
            style_usage_query = self.db.query(
                ZoteroCitationHistory.citation_style,
                func.count(ZoteroCitationHistory.id).label('count')
            ).filter(
                ZoteroCitationHistory.user_id == user_id
            ).group_by(ZoteroCitationHistory.citation_style).all()
            
            style_usage = {style: count for style, count in style_usage_query}
            most_used_style = max(style_usage.items(), key=lambda x: x[1])[0] if style_usage else None
            
            # Format usage statistics
            format_usage_query = self.db.query(
                ZoteroCitationHistory.format_type,
                func.count(ZoteroCitationHistory.id).label('count')
            ).filter(
                ZoteroCitationHistory.user_id == user_id
            ).group_by(ZoteroCitationHistory.format_type).all()
            
            format_usage = {format_type: count for format_type, count in format_usage_query}
            
            # Calculate average citations per session
            unique_sessions = self.db.query(
                func.count(func.distinct(ZoteroCitationHistory.session_id))
            ).filter(
                and_(
                    ZoteroCitationHistory.user_id == user_id,
                    ZoteroCitationHistory.session_id.isnot(None)
                )
            ).scalar() or 1
            
            average_citations_per_session = total_citations / max(unique_sessions, 1)
            
            return {
                'total_citations': total_citations,
                'total_favorites': total_favorites,
                'recent_citations_count': recent_citations_count,
                'most_used_style': most_used_style,
                'style_usage': style_usage,
                'format_usage': format_usage,
                'average_citations_per_session': average_citations_per_session
            }
            
        except Exception as e:
            logger.error(f"Failed to get citation statistics: {str(e)}")
            raise CitationManagementError(f"Failed to get citation statistics: {str(e)}")
    
    async def search_citation_history(
        self,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search through user's citation history
        
        Args:
            user_id: User ID
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching history entries
        """
        try:
            query_lower = query.lower()
            
            # Search in citation text and style using SQL LIKE
            history_entries = self.db.query(ZoteroCitationHistory).filter(
                and_(
                    ZoteroCitationHistory.user_id == user_id,
                    or_(
                        func.lower(ZoteroCitationHistory.citations.astext).like(f'%{query_lower}%'),
                        func.lower(ZoteroCitationHistory.citation_style).like(f'%{query_lower}%')
                    )
                )
            ).order_by(desc(ZoteroCitationHistory.last_accessed)).limit(limit).all()
            
            # Convert to response format
            matching_entries = []
            for entry in history_entries:
                matching_entries.append({
                    'id': entry.id,
                    'item_ids': entry.item_ids,
                    'citation_style': entry.citation_style,
                    'format_type': entry.format_type,
                    'citations': entry.citations,
                    'access_count': entry.access_count,
                    'last_accessed': entry.last_accessed.isoformat(),
                    'created_at': entry.created_at.isoformat(),
                    'session_id': entry.session_id
                })
            
            return matching_entries
            
        except Exception as e:
            logger.error(f"Failed to search citation history: {str(e)}")
            raise CitationManagementError(f"Failed to search citation history: {str(e)}")
    
    async def export_citation_history(
        self,
        user_id: str,
        export_format: str = 'json'
    ) -> str:
        """
        Export user's citation history
        
        Args:
            user_id: User ID
            export_format: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        try:
            # Get all history entries
            history_entries = self.db.query(ZoteroCitationHistory).filter(
                ZoteroCitationHistory.user_id == user_id
            ).order_by(desc(ZoteroCitationHistory.created_at)).all()
            
            # Get all favorites
            favorite_entries = self.db.query(ZoteroCitationFavorites).filter(
                ZoteroCitationFavorites.user_id == user_id
            ).order_by(desc(ZoteroCitationFavorites.created_at)).all()
            
            if export_format == 'json':
                # Convert to JSON format
                history_data = []
                for entry in history_entries:
                    history_data.append({
                        'id': entry.id,
                        'item_ids': entry.item_ids,
                        'citation_style': entry.citation_style,
                        'format_type': entry.format_type,
                        'citations': entry.citations,
                        'access_count': entry.access_count,
                        'last_accessed': entry.last_accessed.isoformat(),
                        'created_at': entry.created_at.isoformat(),
                        'session_id': entry.session_id
                    })
                
                favorites_data = []
                for entry in favorite_entries:
                    favorites_data.append({
                        'id': entry.id,
                        'item_id': entry.item_id,
                        'citation_style': entry.citation_style,
                        'format_type': entry.format_type,
                        'citation': entry.citation,
                        'user_note': entry.user_note,
                        'tags': entry.tags,
                        'access_count': entry.access_count,
                        'last_accessed': entry.last_accessed.isoformat(),
                        'created_at': entry.created_at.isoformat(),
                        'updated_at': entry.updated_at.isoformat()
                    })
                
                export_data = {
                    'user_id': user_id,
                    'exported_at': datetime.now().isoformat(),
                    'citation_history': history_data,
                    'citation_favorites': favorites_data
                }
                return json.dumps(export_data, indent=2, ensure_ascii=False)
                
            elif export_format == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    'Type', 'ID', 'Citation Style', 'Format', 'Citation Text', 
                    'Created At', 'Access Count', 'Note'
                ])
                
                # Write history entries
                for entry in history_entries:
                    for citation in entry.citations:
                        writer.writerow([
                            'History', entry.id, entry.citation_style,
                            entry.format_type, citation, entry.created_at.isoformat(),
                            entry.access_count, ''
                        ])
                
                # Write favorites
                for fav in favorite_entries:
                    writer.writerow([
                        'Favorite', fav.id, fav.citation_style,
                        fav.format_type, fav.citation, fav.created_at.isoformat(),
                        fav.access_count, fav.user_note or ''
                    ])
                
                return output.getvalue()
            
            else:
                raise CitationManagementError(f"Unsupported export format: {export_format}")
                
        except Exception as e:
            logger.error(f"Failed to export citation history: {str(e)}")
            raise CitationManagementError(f"Failed to export citation history: {str(e)}")
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Clean up old citation history data
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Clean old history entries
            cleaned_history = self.db.query(ZoteroCitationHistory).filter(
                ZoteroCitationHistory.created_at < cutoff_date
            ).delete()
            
            # Clean expired cache entries
            cleaned_cache = self.db.query(ZoteroCitationStylePreview).filter(
                ZoteroCitationStylePreview.cache_expires_at < datetime.now()
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {cleaned_history} history entries and {cleaned_cache} cache entries")
            
            return {
                'cleaned_history_entries': cleaned_history,
                'cleaned_cache_entries': cleaned_cache,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup old data: {str(e)}")
            raise CitationManagementError(f"Failed to cleanup old data: {str(e)}")
    
    async def _cleanup_old_history_entries(self, user_id: str, keep_count: int = 100) -> None:
        """
        Clean up old history entries for a specific user, keeping only the most recent ones
        
        Args:
            user_id: User ID
            keep_count: Number of entries to keep
        """
        try:
            # Get total count for user
            total_count = self.db.query(ZoteroCitationHistory).filter(
                ZoteroCitationHistory.user_id == user_id
            ).count()
            
            if total_count <= keep_count:
                return
            
            # Get IDs of entries to keep (most recent)
            entries_to_keep = self.db.query(ZoteroCitationHistory.id).filter(
                ZoteroCitationHistory.user_id == user_id
            ).order_by(desc(ZoteroCitationHistory.last_accessed)).limit(keep_count).all()
            
            keep_ids = [entry.id for entry in entries_to_keep]
            
            # Delete old entries
            deleted_count = self.db.query(ZoteroCitationHistory).filter(
                and_(
                    ZoteroCitationHistory.user_id == user_id,
                    ~ZoteroCitationHistory.id.in_(keep_ids)
                )
            ).delete(synchronize_session=False)
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old history entries for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to cleanup old history entries: {str(e)}")
    
    async def update_favorite_access(self, user_id: str, favorite_id: str) -> bool:
        """
        Update access count and timestamp for a favorite citation
        
        Args:
            user_id: User ID
            favorite_id: Favorite ID
            
        Returns:
            True if updated, False if not found
        """
        try:
            favorite = self.db.query(ZoteroCitationFavorites).filter(
                and_(
                    ZoteroCitationFavorites.user_id == user_id,
                    ZoteroCitationFavorites.id == favorite_id
                )
            ).first()
            
            if favorite:
                favorite.access_count += 1
                favorite.last_accessed = datetime.now()
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update favorite access: {str(e)}")
            return False