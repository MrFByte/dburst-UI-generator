from django.core.cache import cache
from django.core.cache.backends.redis import RedisCache
import jsonpatch
import json
import logging
import time
import requests
from typing import Optional, Dict, Any, List
from django.conf import settings
from functools import wraps
from .codegen import ReactCodeGenerator

logger = logging.getLogger(__name__)

class GenerationCache:
    """Redis-based caching with patch support"""
    
    TTL_DEFAULT = 86400 * 3  # 3 days
    PATCH_SNAPSHOT_THRESHOLD = 10  # Create snapshot every 10 patches
    
    @staticmethod
    def store_generation(generation_id: str, schema: Dict, code: str, meta: Dict):
        """Store generation in Redis"""
        cache.set(f"gen:{generation_id}:schema", json.dumps(schema), GenerationCache.TTL_DEFAULT)
        cache.set(f"gen:{generation_id}:code", code, GenerationCache.TTL_DEFAULT)
        cache.set(f"gen:{generation_id}:meta", json.dumps(meta), GenerationCache.TTL_DEFAULT)
        logger.info(f"Stored generation {generation_id} in Redis cache")
    
    @staticmethod
    def get_generation(generation_id: str) -> Optional[Dict]:
        """Retrieve generation from Redis"""
        schema_json = cache.get(f"gen:{generation_id}:schema")
        code = cache.get(f"gen:{generation_id}:code")
        meta_json = cache.get(f"gen:{generation_id}:meta")
        
        if not schema_json or not code:
            logger.warning(f"Generation {generation_id} not found in cache")
            return None
        
        return {
            "schema": json.loads(schema_json),
            "code": code,
            "meta": json.loads(meta_json) if meta_json else {},
        }
    
    @staticmethod
    def apply_patch(generation_id: str, patch: Dict) -> Optional[Dict]:
        """Apply JSON Patch to schema and regenerate code"""
        schema_json = cache.get(f"gen:{generation_id}:schema")
        if not schema_json:
            logger.error(f"Cannot apply patch: schema for {generation_id} not in cache")
            return None
        
        current_schema = json.loads(schema_json)
        
        try:
            patched_schema = jsonpatch.apply_patch(current_schema, patch)
            
            cache.set(f"gen:{generation_id}:schema", json.dumps(patched_schema), GenerationCache.TTL_DEFAULT)
            
            generator = ReactCodeGenerator(patched_schema)
            new_code = generator.generate()
            cache.set(f"gen:{generation_id}:code", new_code, GenerationCache.TTL_DEFAULT)
            
            logger.info(f"Applied patch to generation {generation_id}")
            return patched_schema
        except Exception as e:
            logger.error(f"Patch application failed for {generation_id}: {e}")
            return None
    
    @staticmethod
    def store_patch(generation_id: str, patch: List[Dict], user_id: str, description: str = "") -> bool:
        """
        Store a patch in Redis list with metadata
        
        Args:
            generation_id: UUID of the generation
            patch: JSON Patch operations (RFC 6902)
            user_id: UUID of user who created the patch
            description: Optional description of the change
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            patch_data = {
                "patch": patch,
                "user_id": str(user_id),
                "description": description,
                "timestamp": time.time(),
            }
            
            cache_key = f"gen:{generation_id}:patches"
            
            current_count = GenerationCache.get_patch_count(generation_id)
            
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            redis_conn.lpush(cache_key, json.dumps(patch_data))
            redis_conn.expire(cache_key, GenerationCache.TTL_DEFAULT)
            
            logger.info(f"Stored patch #{current_count + 1} for generation {generation_id}")
            
            if (current_count + 1) % GenerationCache.PATCH_SNAPSHOT_THRESHOLD == 0:
                logger.info(f"Snapshot threshold reached for {generation_id} (patch #{current_count + 1})")
            
            return True
        except Exception as e:
            logger.error(f"Failed to store patch for {generation_id}: {e}")
            return False
    
    @staticmethod
    def get_patches(generation_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Retrieve patch history for a generation
        
        Args:
            generation_id: UUID of the generation
            limit: Maximum number of patches to return
            offset: Number of patches to skip (for pagination)
            
        Returns:
            List of patch objects with metadata
        """
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            
            cache_key = f"gen:{generation_id}:patches"
            
            end = offset + limit - 1
            patch_strings = redis_conn.lrange(cache_key, offset, end)
            
            patches = []
            for patch_str in patch_strings:
                try:
                    patch_data = json.loads(patch_str)
                    patches.append(patch_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode patch: {e}")
                    continue
            
            logger.info(f"Retrieved {len(patches)} patches for generation {generation_id}")
            return patches
        except Exception as e:
            logger.error(f"Failed to retrieve patches for {generation_id}: {e}")
            return []
    
    @staticmethod
    def get_patch_count(generation_id: str) -> int:
        """
        Get total number of patches for a generation
        
        Args:
            generation_id: UUID of the generation
            
        Returns:
            Total patch count
        """
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            
            cache_key = f"gen:{generation_id}:patches"
            count = redis_conn.llen(cache_key)
            return count
        except Exception as e:
            logger.error(f"Failed to get patch count for {generation_id}: {e}")
            return 0
    
    @staticmethod
    def get_schema(generation_id: str) -> Optional[Dict]:
        """
        Get current schema from cache
        
        Args:
            generation_id: UUID of the generation
            
        Returns:
            Schema dictionary or None if not found
        """
        schema_json = cache.get(f"gen:{generation_id}:schema")
        if schema_json:
            return json.loads(schema_json)
        return None
    
    @staticmethod
    def clear_generation(generation_id: str) -> bool:
        """
        Clear all cached data for a generation
        
        Args:
            generation_id: UUID of the generation
            
        Returns:
            True if cleared successfully
        """
        try:
            cache.delete(f"gen:{generation_id}:schema")
            cache.delete(f"gen:{generation_id}:code")
            cache.delete(f"gen:{generation_id}:meta")
            
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            redis_conn.delete(f"gen:{generation_id}:patches")
            
            logger.info(f"Cleared cache for generation {generation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache for {generation_id}: {e}")
            return False