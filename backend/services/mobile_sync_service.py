"""
Mobile synchronization service for offline/online data management
Handles PWA caching, offline storage, and data synchronization
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import aioredis
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.redis_client import redis_client
from models.schemas import DocumentResponse

logger = logging.getLogger(__name__)

@dataclass
class SyncItem:
    id: str
    type: str  # document, note, quiz, etc.
    data: Dict[str, Any]
    last_modified: datetime
    sync_status: str  # pending, synced, conflict
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class SyncResult:
    success: bool
    synced_items: int
    failed_items: int
    conflicts: List[Dict[str, Any]]
    last_sync: datetime

@dataclass
class OfflineCacheItem:
    key: str
    data: Any
    expires_at: datetime
    size_bytes: int
    access_count: int = 0
    last_accessed: datetime = None

class MobileSyncService:
    def __init__(self):
        self.redis_prefix = "mobile_sync:"
        self.cache_prefix = "offline_cache:"
        self.max_cache_size = 100 * 1024 * 1024  # 100MB
        self.sync_batch_size = 50
        
    async def health_check(self) -> Dict[str, Any]:
        """Health check for mobile sync service"""
        try:
            # Check Redis connection
            await redis_client.ping()
            
            # Check sync queue status
            queue_size = await redis_client.llen(f"{self.redis_prefix}sync_queue")
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "sync_queue_size": queue_size,
                "cache_size": await self._get_cache_size()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def sync_data(self, user_id: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synchronize user data between mobile and server"""
        try:
            # Get pending sync items
            pending_items = await self._get_pending_sync_items(user_id)
            
            # Process uploads (mobile to server)
            upload_results = await self._process_uploads(user_id, pending_items.get("uploads", []))
            
            # Process downloads (server to mobile)
            download_results = await self._process_downloads(user_id, parameters)
            
            # Resolve conflicts
            conflicts = await self._resolve_conflicts(user_id)
            
            # Update sync status
            sync_result = SyncResult(
                success=True,
                synced_items=upload_results["synced"] + download_results["synced"],
                failed_items=upload_results["failed"] + download_results["failed"],
                conflicts=conflicts,
                last_sync=datetime.now()
            )
            
            # Store sync status
            await self._store_sync_status(user_id, sync_result)
            
            return {
                "status": "completed",
                "synced_items": sync_result.synced_items,
                "failed_items": sync_result.failed_items,
                "conflicts": len(sync_result.conflicts),
                "last_sync": sync_result.last_sync.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sync failed for user {user_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_sync": datetime.now().isoformat()
            }

    async def manage_offline_cache(self, user_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Manage offline cache for mobile app"""
        try:
            action = parameters.get("action", "status")
            
            if action == "status":
                return await self._get_cache_status(user_id)
            elif action == "clear":
                return await self._clear_cache(user_id)
            elif action == "optimize":
                return await self._optimize_cache(user_id)
            elif action == "preload":
                return await self._preload_cache(user_id, parameters.get("items", []))
            else:
                raise ValueError(f"Unknown cache action: {action}")
                
        except Exception as e:
            logger.error(f"Cache management failed for user {user_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def send_push_notification(self, user_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send push notification to mobile device"""
        try:
            notification_type = parameters.get("type", "general")
            title = parameters.get("title", "AI Scholar")
            message = parameters.get("message", "")
            data = parameters.get("data", {})
            
            # Store notification for delivery
            notification = {
                "id": f"notif_{datetime.now().timestamp()}",
                "user_id": user_id,
                "type": notification_type,
                "title": title,
                "message": message,
                "data": data,
                "created_at": datetime.now().isoformat(),
                "delivered": False
            }
            
            # Add to notification queue
            await redis_client.lpush(
                f"{self.redis_prefix}notifications:{user_id}",
                json.dumps(notification)
            )
            
            # Set expiration for notification queue
            await redis_client.expire(
                f"{self.redis_prefix}notifications:{user_id}",
                86400  # 24 hours
            )
            
            return {
                "status": "queued",
                "notification_id": notification["id"],
                "delivery_method": "push"
            }
            
        except Exception as e:
            logger.error(f"Push notification failed for user {user_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_sync_status(self, user_id: str) -> Dict[str, Any]:
        """Get current synchronization status"""
        try:
            # Get stored sync status
            sync_data = await redis_client.get(f"{self.redis_prefix}status:{user_id}")
            if sync_data:
                status = json.loads(sync_data)
            else:
                status = {
                    "last_sync": None,
                    "status": "never_synced",
                    "cached_items": 0,
                    "pending_uploads": 0
                }
            
            # Get current pending items
            pending_uploads = await redis_client.llen(f"{self.redis_prefix}uploads:{user_id}")
            cached_items = await redis_client.scard(f"{self.cache_prefix}items:{user_id}")
            
            status.update({
                "pending_uploads": pending_uploads,
                "cached_items": cached_items,
                "cache_size": await self._get_user_cache_size(user_id)
            })
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get sync status for user {user_id}: {e}")
            return {
                "last_sync": None,
                "status": "error",
                "cached_items": 0,
                "pending_uploads": 0,
                "error": str(e)
            }

    async def _get_pending_sync_items(self, user_id: str) -> Dict[str, List[SyncItem]]:
        """Get pending synchronization items"""
        try:
            # Get upload queue
            upload_data = await redis_client.lrange(f"{self.redis_prefix}uploads:{user_id}", 0, -1)
            uploads = []
            for item_data in upload_data:
                item = json.loads(item_data)
                uploads.append(SyncItem(
                    id=item["id"],
                    type=item["type"],
                    data=item["data"],
                    last_modified=datetime.fromisoformat(item["last_modified"]),
                    sync_status=item.get("sync_status", "pending"),
                    priority=item.get("priority", 1)
                ))
            
            # Get download requirements (items modified on server)
            downloads = await self._get_server_updates(user_id)
            
            return {
                "uploads": uploads,
                "downloads": downloads
            }
            
        except Exception as e:
            logger.error(f"Failed to get pending sync items: {e}")
            return {"uploads": [], "downloads": []}

    async def _process_uploads(self, user_id: str, upload_items: List[SyncItem]) -> Dict[str, int]:
        """Process items to upload from mobile to server"""
        synced = 0
        failed = 0
        
        try:
            for item in upload_items:
                try:
                    # Process based on item type
                    if item.type == "document":
                        await self._upload_document(user_id, item)
                    elif item.type == "note":
                        await self._upload_note(user_id, item)
                    elif item.type == "quiz_response":
                        await self._upload_quiz_response(user_id, item)
                    elif item.type == "progress_update":
                        await self._upload_progress_update(user_id, item)
                    else:
                        logger.warning(f"Unknown upload item type: {item.type}")
                        failed += 1
                        continue
                    
                    # Remove from upload queue
                    await redis_client.lrem(
                        f"{self.redis_prefix}uploads:{user_id}",
                        1,
                        json.dumps(asdict(item))
                    )
                    synced += 1
                    
                except Exception as e:
                    logger.error(f"Failed to upload item {item.id}: {e}")
                    failed += 1
                    
        except Exception as e:
            logger.error(f"Upload processing failed: {e}")
            
        return {"synced": synced, "failed": failed}

    async def _process_downloads(self, user_id: str, parameters: Optional[Dict[str, Any]]) -> Dict[str, int]:
        """Process items to download from server to mobile"""
        synced = 0
        failed = 0
        
        try:
            # Get items that need to be downloaded
            download_types = parameters.get("download_types", ["documents", "quizzes", "progress"]) if parameters else ["documents", "quizzes", "progress"]
            
            for download_type in download_types:
                try:
                    if download_type == "documents":
                        count = await self._download_documents(user_id)
                    elif download_type == "quizzes":
                        count = await self._download_quizzes(user_id)
                    elif download_type == "progress":
                        count = await self._download_progress(user_id)
                    else:
                        continue
                    
                    synced += count
                    
                except Exception as e:
                    logger.error(f"Failed to download {download_type}: {e}")
                    failed += 1
                    
        except Exception as e:
            logger.error(f"Download processing failed: {e}")
            
        return {"synced": synced, "failed": failed}

    async def _resolve_conflicts(self, user_id: str) -> List[Dict[str, Any]]:
        """Resolve synchronization conflicts"""
        try:
            conflicts = []
            
            # Get conflict items
            conflict_data = await redis_client.lrange(f"{self.redis_prefix}conflicts:{user_id}", 0, -1)
            
            for conflict_item in conflict_data:
                conflict = json.loads(conflict_item)
                
                # Apply conflict resolution strategy
                resolution = await self._apply_conflict_resolution(conflict)
                
                if resolution["resolved"]:
                    # Remove from conflicts
                    await redis_client.lrem(
                        f"{self.redis_prefix}conflicts:{user_id}",
                        1,
                        conflict_item
                    )
                else:
                    conflicts.append(conflict)
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")
            return []

    async def _apply_conflict_resolution(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply conflict resolution strategy"""
        try:
            strategy = conflict.get("resolution_strategy", "server_wins")
            
            if strategy == "server_wins":
                # Server version takes precedence
                return {"resolved": True, "action": "use_server_version"}
            elif strategy == "client_wins":
                # Client version takes precedence
                return {"resolved": True, "action": "use_client_version"}
            elif strategy == "merge":
                # Attempt to merge changes
                merge_result = await self._merge_conflict_data(conflict)
                return {"resolved": merge_result["success"], "action": "merged"}
            else:
                # Manual resolution required
                return {"resolved": False, "action": "manual_resolution_required"}
                
        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")
            return {"resolved": False, "action": "error"}

    async def _get_cache_status(self, user_id: str) -> Dict[str, Any]:
        """Get offline cache status"""
        try:
            cache_items = await redis_client.smembers(f"{self.cache_prefix}items:{user_id}")
            total_size = 0
            item_count = len(cache_items)
            
            # Calculate total cache size
            for item_key in cache_items:
                item_data = await redis_client.get(f"{self.cache_prefix}data:{item_key}")
                if item_data:
                    total_size += len(item_data.encode('utf-8'))
            
            return {
                "status": "active",
                "item_count": item_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "max_size_mb": round(self.max_cache_size / (1024 * 1024), 2),
                "usage_percentage": round((total_size / self.max_cache_size) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _clear_cache(self, user_id: str) -> Dict[str, Any]:
        """Clear offline cache"""
        try:
            # Get all cache items
            cache_items = await redis_client.smembers(f"{self.cache_prefix}items:{user_id}")
            
            # Delete cache data
            for item_key in cache_items:
                await redis_client.delete(f"{self.cache_prefix}data:{item_key}")
            
            # Clear cache items set
            await redis_client.delete(f"{self.cache_prefix}items:{user_id}")
            
            return {
                "status": "cleared",
                "items_removed": len(cache_items)
            }
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _optimize_cache(self, user_id: str) -> Dict[str, Any]:
        """Optimize offline cache by removing least used items"""
        try:
            # Get cache items with access info
            cache_items = await redis_client.smembers(f"{self.cache_prefix}items:{user_id}")
            
            # Get current cache size
            current_size = await self._get_user_cache_size(user_id)
            
            if current_size <= self.max_cache_size * 0.8:  # 80% threshold
                return {
                    "status": "no_optimization_needed",
                    "current_size_mb": round(current_size / (1024 * 1024), 2)
                }
            
            # Remove least accessed items
            removed_items = 0
            for item_key in cache_items:
                if current_size <= self.max_cache_size * 0.6:  # Target 60%
                    break
                
                # Remove item
                item_data = await redis_client.get(f"{self.cache_prefix}data:{item_key}")
                if item_data:
                    item_size = len(item_data.encode('utf-8'))
                    await redis_client.delete(f"{self.cache_prefix}data:{item_key}")
                    await redis_client.srem(f"{self.cache_prefix}items:{user_id}", item_key)
                    current_size -= item_size
                    removed_items += 1
            
            return {
                "status": "optimized",
                "items_removed": removed_items,
                "new_size_mb": round(current_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _store_sync_status(self, user_id: str, sync_result: SyncResult):
        """Store synchronization status"""
        try:
            status_data = {
                "last_sync": sync_result.last_sync.isoformat(),
                "status": "completed" if sync_result.success else "failed",
                "synced_items": sync_result.synced_items,
                "failed_items": sync_result.failed_items,
                "conflicts": len(sync_result.conflicts)
            }
            
            await redis_client.setex(
                f"{self.redis_prefix}status:{user_id}",
                86400,  # 24 hours
                json.dumps(status_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to store sync status: {e}")

    async def _get_cache_size(self) -> int:
        """Get total cache size across all users"""
        try:
            # This is a simplified implementation
            # In production, you might want to track this more efficiently
            total_size = 0
            cache_keys = await redis_client.keys(f"{self.cache_prefix}data:*")
            
            for key in cache_keys:
                data = await redis_client.get(key)
                if data:
                    total_size += len(data.encode('utf-8'))
            
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to get cache size: {e}")
            return 0

    async def _get_user_cache_size(self, user_id: str) -> int:
        """Get cache size for specific user"""
        try:
            total_size = 0
            cache_items = await redis_client.smembers(f"{self.cache_prefix}items:{user_id}")
            
            for item_key in cache_items:
                item_data = await redis_client.get(f"{self.cache_prefix}data:{item_key}")
                if item_data:
                    total_size += len(item_data.encode('utf-8'))
            
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to get user cache size: {e}")
            return 0

    # Placeholder methods for specific upload/download operations
    async def _upload_document(self, user_id: str, item: SyncItem):
        """Upload document from mobile"""
        # Implementation would integrate with document processor
        pass

    async def _upload_note(self, user_id: str, item: SyncItem):
        """Upload note from mobile"""
        # Implementation would integrate with note-taking service
        pass

    async def _upload_quiz_response(self, user_id: str, item: SyncItem):
        """Upload quiz response from mobile"""
        # Implementation would integrate with quiz service
        pass

    async def _upload_progress_update(self, user_id: str, item: SyncItem):
        """Upload progress update from mobile"""
        # Implementation would integrate with learning progress service
        pass

    async def _download_documents(self, user_id: str) -> int:
        """Download documents to mobile cache"""
        # Implementation would fetch recent documents
        return 0

    async def _download_quizzes(self, user_id: str) -> int:
        """Download quizzes to mobile cache"""
        # Implementation would fetch user quizzes
        return 0

    async def _download_progress(self, user_id: str) -> int:
        """Download progress data to mobile cache"""
        # Implementation would fetch learning progress
        return 0

    async def _get_server_updates(self, user_id: str) -> List[SyncItem]:
        """Get items that have been updated on server"""
        # Implementation would check for server-side updates
        return []

    async def _merge_conflict_data(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Merge conflicting data"""
        # Implementation would merge data based on conflict type
        return {"success": False}

    async def _preload_cache(self, user_id: str, items: List[str]) -> Dict[str, Any]:
        """Preload specific items into cache"""
        try:
            preloaded = 0
            failed = 0
            
            for item_id in items:
                try:
                    # Fetch item data and add to cache
                    # Implementation would fetch actual data
                    item_data = {"id": item_id, "preloaded": True}
                    
                    await redis_client.set(
                        f"{self.cache_prefix}data:{item_id}",
                        json.dumps(item_data)
                    )
                    await redis_client.sadd(f"{self.cache_prefix}items:{user_id}", item_id)
                    
                    preloaded += 1
                    
                except Exception as e:
                    logger.error(f"Failed to preload item {item_id}: {e}")
                    failed += 1
            
            return {
                "status": "completed",
                "preloaded": preloaded,
                "failed": failed
            }
            
        except Exception as e:
            logger.error(f"Cache preload failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }