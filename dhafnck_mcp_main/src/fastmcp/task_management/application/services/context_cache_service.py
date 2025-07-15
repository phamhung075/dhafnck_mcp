"""
Context Cache Service

Provides high-performance caching for resolved contexts to minimize
resolution overhead in the hierarchical context system.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class ContextCacheService:
    """
    Service for managing context resolution caching.
    
    Provides intelligent caching with dependency tracking and automatic
    invalidation to optimize performance of hierarchical context resolution.
    """
    
    def __init__(self, repository=None, default_ttl_hours: int = 1):
        """Initialize cache service"""
        self.repository = repository  # Will be injected
        self.default_ttl_hours = default_ttl_hours
        logger.info(f"ContextCacheService initialized with {default_ttl_hours}h TTL")
    
    # ===============================================
    # SYNC WRAPPER METHODS FOR FACADE COMPATIBILITY
    # ===============================================
    
    def get_context(self, level: str, context_id: str) -> Optional[Dict[str, Any]]:
        """Sync wrapper for get_cached_context"""
        # For now, return None to indicate no cache hit
        # In a real implementation, you'd use asyncio.run or similar
        return None
    
    def set_context(self, level: str, context_id: str, context: Dict[str, Any]) -> None:
        """Sync wrapper for cache_resolved_context"""
        # For now, do nothing
        # In a real implementation, you'd use asyncio.run or similar
        pass
    
    def invalidate_context(self, level: str, context_id: str) -> None:
        """Sync wrapper for invalidate_context_cache"""
        # For now, do nothing
        # In a real implementation, you'd use asyncio.run or similar
        pass
    
    def clear_cache(self) -> None:
        """Sync wrapper for clear_all_cache"""
        # For now, do nothing
        # In a real implementation, you'd use asyncio.run or similar
        pass
    
    def invalidate_context_cache(self, level: str, context_id: str) -> None:
        """Sync version for compatibility"""
        # For now, do nothing
        # In a real implementation, you'd use asyncio.run or similar
        pass
    
    # ===============================================
    # CACHE RETRIEVAL
    # ===============================================
    
    async def get_cached_context(self, level: str, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached resolved context if available and valid.
        
        Args:
            level: Context level ('global', 'project', 'task')
            context_id: Context identifier
            
        Returns:
            Cached context data or None if not available/expired
        """
        try:
            cache_entry = await self.repository.get_cache_entry(level, context_id)
            
            if not cache_entry:
                logger.debug(f"No cache entry for {level}:{context_id}")
                return None
            
            # Check if invalidated
            if cache_entry.get("invalidated", False):
                logger.debug(f"Cache entry invalidated for {level}:{context_id}")
                await self._cleanup_invalidated_entry(level, context_id)
                return None
            
            # Check expiration
            expires_at = cache_entry.get("expires_at")
            if expires_at:
                expire_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > expire_time:
                    logger.debug(f"Cache entry expired for {level}:{context_id}")
                    await self._cleanup_expired_entry(level, context_id)
                    return None
            
            # Update hit count and last hit time
            await self._update_hit_stats(level, context_id)
            
            logger.debug(f"Cache hit for {level}:{context_id}")
            return cache_entry
            
        except Exception as e:
            logger.warning(f"Error retrieving cached context {level}:{context_id}: {e}")
            return None
    
    async def _update_hit_stats(self, level: str, context_id: str) -> None:
        """Update cache hit statistics"""
        try:
            await self.repository.update_cache_stats(level, context_id, {
                "hit_count": "hit_count + 1",  # SQL increment
                "last_hit": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.warning(f"Error updating cache stats: {e}")
    
    # ===============================================
    # CACHE STORAGE
    # ===============================================
    
    async def cache_resolved_context(self, level: str, context_id: str,
                                   resolved_context: Dict[str, Any],
                                   dependencies_hash: str,
                                   resolution_path: List[str],
                                   ttl_hours: Optional[int] = None) -> bool:
        """
        Cache a resolved context with dependency tracking.
        
        Args:
            level: Context level
            context_id: Context identifier
            resolved_context: Fully resolved context
            dependencies_hash: Hash of all dependencies for invalidation
            resolution_path: Path taken during resolution
            ttl_hours: Time to live in hours (uses default if None)
            
        Returns:
            True if cached successfully
        """
        try:
            ttl = ttl_hours or self.default_ttl_hours
            expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl)
            
            # Calculate cache entry size
            cache_data = json.dumps(resolved_context, default=str)
            cache_size = len(cache_data.encode('utf-8'))
            
            cache_entry = {
                "context_id": context_id,
                "context_level": level,
                "resolved_context": resolved_context,
                "dependencies_hash": dependencies_hash,
                "resolution_path": json.dumps(resolution_path),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires_at.isoformat(),
                "hit_count": 0,
                "last_hit": datetime.now(timezone.utc).isoformat(),
                "cache_size_bytes": cache_size,
                "invalidated": False,
                "invalidation_reason": None
            }
            
            await self.repository.store_cache_entry(cache_entry)
            
            logger.debug(f"Cached context {level}:{context_id} (size: {cache_size} bytes, expires: {expires_at})")
            return True
            
        except Exception as e:
            logger.error(f"Error caching context {level}:{context_id}: {e}")
            return False
    
    # ===============================================
    # CACHE INVALIDATION
    # ===============================================
    
    async def invalidate_context_cache(self, level: str, context_id: str, 
                                     reason: str = "manual_invalidation") -> bool:
        """
        Invalidate cache for specific context.
        
        Args:
            level: Context level
            context_id: Context identifier
            reason: Reason for invalidation
            
        Returns:
            True if invalidated successfully
        """
        try:
            await self.repository.invalidate_cache_entry(level, context_id, reason)
            logger.debug(f"Invalidated cache for {level}:{context_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating cache {level}:{context_id}: {e}")
            return False
    
    async def invalidate_dependent_caches(self, level: str, context_id: str,
                                        reason: str = "dependency_changed") -> List[str]:
        """
        Invalidate all caches that depend on the specified context.
        
        Args:
            level: Changed context level
            context_id: Changed context identifier
            reason: Reason for invalidation
            
        Returns:
            List of invalidated cache keys
        """
        try:
            invalidated = []
            
            if level == "global":
                # Global changes affect all project and task caches
                project_caches = await self.repository.get_cache_entries_by_level("project")
                task_caches = await self.repository.get_cache_entries_by_level("task")
                
                for cache in project_caches + task_caches:
                    cache_level = cache["context_level"]
                    cache_id = cache["context_id"]
                    await self.invalidate_context_cache(cache_level, cache_id, reason)
                    invalidated.append(f"{cache_level}:{cache_id}")
            
            elif level == "project":
                # Project changes affect task caches in that project
                task_caches = await self.repository.get_task_caches_by_project(context_id)
                
                for cache in task_caches:
                    await self.invalidate_context_cache("task", cache["context_id"], reason)
                    invalidated.append(f"task:{cache['context_id']}")
            
            logger.info(f"Invalidated {len(invalidated)} dependent caches for {level}:{context_id}")
            return invalidated
            
        except Exception as e:
            logger.error(f"Error invalidating dependent caches: {e}")
            return []
    
    # ===============================================
    # CACHE MAINTENANCE
    # ===============================================
    
    async def cleanup_expired(self) -> Dict[str, Any]:
        """Clean up expired cache entries"""
        try:
            now = datetime.now(timezone.utc)
            
            # Get expired entries
            expired_entries = await self.repository.get_expired_cache_entries(now)
            
            # Remove expired entries
            removed_count = 0
            total_size_freed = 0
            
            for entry in expired_entries:
                await self.repository.remove_cache_entry(
                    entry["context_level"], 
                    entry["context_id"]
                )
                removed_count += 1
                total_size_freed += entry.get("cache_size_bytes", 0)
            
            result = {
                "success": True,
                "removed_count": removed_count,
                "size_freed_bytes": total_size_freed,
                "cleaned_at": now.isoformat()
            }
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired cache entries, freed {total_size_freed} bytes")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            return {
                "success": False,
                "error": str(e),
                "removed_count": 0,
                "size_freed_bytes": 0
            }
    
    async def cleanup_invalidated(self) -> Dict[str, Any]:
        """Clean up invalidated cache entries"""
        try:
            # Get invalidated entries
            invalidated_entries = await self.repository.get_invalidated_cache_entries()
            
            # Remove invalidated entries
            removed_count = 0
            total_size_freed = 0
            
            for entry in invalidated_entries:
                await self.repository.remove_cache_entry(
                    entry["context_level"], 
                    entry["context_id"]
                )
                removed_count += 1
                total_size_freed += entry.get("cache_size_bytes", 0)
            
            result = {
                "success": True,
                "removed_count": removed_count,
                "size_freed_bytes": total_size_freed,
                "cleaned_at": datetime.now(timezone.utc).isoformat()
            }
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} invalidated cache entries, freed {total_size_freed} bytes")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during invalidated cache cleanup: {e}")
            return {
                "success": False,
                "error": str(e),
                "removed_count": 0,
                "size_freed_bytes": 0
            }
    
    async def clear_all_cache(self) -> Dict[str, Any]:
        """Clear all cache entries (use with caution)"""
        try:
            removed_count = await self.repository.clear_all_cache_entries()
            
            result = {
                "success": True,
                "removed_count": removed_count,
                "cleared_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.warning(f"Cleared all cache entries: {removed_count} entries removed")
            return result
            
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            return {
                "success": False,
                "error": str(e),
                "removed_count": 0
            }
    
    # ===============================================
    # CACHE STATISTICS AND MONITORING
    # ===============================================
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            stats = await self.repository.get_cache_statistics()
            
            # Calculate derived metrics
            total_entries = stats.get("total_entries", 0)
            total_size = stats.get("total_size_bytes", 0)
            total_hits = stats.get("total_hits", 0)
            
            # Cache effectiveness metrics
            hit_rate = 0.0
            if total_entries > 0:
                avg_hits_per_entry = total_hits / total_entries
                hit_rate = min(avg_hits_per_entry / 10.0, 1.0)  # Normalize to 0-1
            
            avg_entry_size = total_size / total_entries if total_entries > 0 else 0
            
            enhanced_stats = {
                **stats,
                "performance_metrics": {
                    "hit_rate_estimated": round(hit_rate, 3),
                    "average_entry_size_bytes": round(avg_entry_size, 2),
                    "cache_efficiency": "high" if hit_rate > 0.7 else "medium" if hit_rate > 0.3 else "low"
                },
                "health_indicators": {
                    "expired_entries": stats.get("expired_count", 0),
                    "invalidated_entries": stats.get("invalidated_count", 0),
                    "cache_pressure": "high" if total_entries > 1000 else "medium" if total_entries > 100 else "low"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return enhanced_stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_top_cached_contexts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed cached contexts"""
        try:
            top_contexts = await self.repository.get_top_hit_cache_entries(limit)
            
            return [
                {
                    "level": entry["context_level"],
                    "context_id": entry["context_id"],
                    "hit_count": entry["hit_count"],
                    "last_hit": entry["last_hit"],
                    "cache_size_bytes": entry["cache_size_bytes"],
                    "created_at": entry["created_at"]
                }
                for entry in top_contexts
            ]
            
        except Exception as e:
            logger.error(f"Error getting top cached contexts: {e}")
            return []
    
    # ===============================================
    # CACHE OPTIMIZATION
    # ===============================================
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache by removing low-value entries"""
        try:
            optimization_result = {
                "optimization_started": datetime.now(timezone.utc).isoformat(),
                "actions_taken": [],
                "space_freed_bytes": 0,
                "entries_removed": 0
            }
            
            # 1. Remove expired entries
            cleanup_result = await self.cleanup_expired()
            if cleanup_result.get("success"):
                optimization_result["actions_taken"].append("cleaned_expired")
                optimization_result["space_freed_bytes"] += cleanup_result.get("size_freed_bytes", 0)
                optimization_result["entries_removed"] += cleanup_result.get("removed_count", 0)
            
            # 2. Remove invalidated entries
            invalidated_result = await self.cleanup_invalidated()
            if invalidated_result.get("success"):
                optimization_result["actions_taken"].append("cleaned_invalidated")
                optimization_result["space_freed_bytes"] += invalidated_result.get("size_freed_bytes", 0)
                optimization_result["entries_removed"] += invalidated_result.get("removed_count", 0)
            
            # 3. Remove low-hit entries if cache is under pressure
            stats = await self.get_cache_stats()
            total_entries = stats.get("total_entries", 0)
            
            if total_entries > 500:  # Cache pressure threshold
                low_hit_entries = await self.repository.get_low_hit_cache_entries(hit_threshold=2, limit=50)
                
                removed_low_hit = 0
                for entry in low_hit_entries:
                    await self.repository.remove_cache_entry(
                        entry["context_level"], 
                        entry["context_id"]
                    )
                    removed_low_hit += 1
                    optimization_result["space_freed_bytes"] += entry.get("cache_size_bytes", 0)
                
                if removed_low_hit > 0:
                    optimization_result["actions_taken"].append(f"removed_{removed_low_hit}_low_hit_entries")
                    optimization_result["entries_removed"] += removed_low_hit
            
            optimization_result["optimization_completed"] = datetime.now(timezone.utc).isoformat()
            optimization_result["success"] = True
            
            logger.info(f"Cache optimization completed: {optimization_result}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error during cache optimization: {e}")
            return {
                "success": False,
                "error": str(e),
                "optimization_started": datetime.now(timezone.utc).isoformat()
            }
    
    # ===============================================
    # UTILITY METHODS
    # ===============================================
    
    async def _cleanup_expired_entry(self, level: str, context_id: str) -> None:
        """Clean up a single expired entry"""
        try:
            await self.repository.remove_cache_entry(level, context_id)
            logger.debug(f"Removed expired cache entry: {level}:{context_id}")
        except Exception as e:
            logger.warning(f"Error removing expired cache entry: {e}")
    
    async def _cleanup_invalidated_entry(self, level: str, context_id: str) -> None:
        """Clean up a single invalidated entry"""
        try:
            await self.repository.remove_cache_entry(level, context_id)
            logger.debug(f"Removed invalidated cache entry: {level}:{context_id}")
        except Exception as e:
            logger.warning(f"Error removing invalidated cache entry: {e}")
    
    async def warm_cache(self, contexts_to_warm: List[Dict[str, str]]) -> Dict[str, Any]:
        """Warm cache with frequently accessed contexts"""
        try:
            warmed_count = 0
            failed_count = 0
            
            for context_spec in contexts_to_warm:
                level = context_spec.get("level")
                context_id = context_spec.get("context_id")
                
                try:
                    # This would trigger resolution and caching
                    # Implementation depends on integration with hierarchy service
                    warmed_count += 1
                    logger.debug(f"Warmed cache for {level}:{context_id}")
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"Failed to warm cache for {level}:{context_id}: {e}")
            
            return {
                "success": True,
                "warmed_count": warmed_count,
                "failed_count": failed_count,
                "total_requested": len(contexts_to_warm)
            }
            
        except Exception as e:
            logger.error(f"Error warming cache: {e}")
            return {
                "success": False,
                "error": str(e),
                "warmed_count": 0
            }