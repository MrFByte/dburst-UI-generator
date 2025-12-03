from django.core.cache import cache
from django.core.cache.backends.redis import RedisCache
import jsonpatch
import json
import logging
import time
import requests
from typing import Optional, Dict, Any
from django.conf import settings
from functools import wraps
from .codegen import ReactCodeGenerator

logger = logging.getLogger(__name__)

class GenerationCache:
    """Redis-based caching with patch support"""
    
    TTL_DEFAULT = 86400 * 3
    
    @staticmethod
    def store_generation(generation_id: str, schema: Dict, code: str, meta: Dict):
        """Store generation in Redis"""
        cache.set(f"gen:{generation_id}:schema", json.dumps(schema), GenerationCache.TTL_DEFAULT)
        cache.set(f"gen:{generation_id}:code", code, GenerationCache.TTL_DEFAULT)
        cache.set(f"gen:{generation_id}:meta", json.dumps(meta), GenerationCache.TTL_DEFAULT)
    
    @staticmethod
    def get_generation(generation_id: str) -> Optional[Dict]:
        """Retrieve generation from Redis"""
        schema_json = cache.get(f"gen:{generation_id}:schema")
        code = cache.get(f"gen:{generation_id}:code")
        meta_json = cache.get(f"gen:{generation_id}:meta")
        
        if not schema_json or not code:
            return None
        
        return {
            "schema": json.loads(schema_json),
            "code": code,
            "meta": json.loads(meta_json),
        }
    
    @staticmethod
    def apply_patch(generation_id: str, patch: Dict) -> Optional[Dict]:
        """Apply JSON Patch to schema"""
        schema_json = cache.get(f"gen:{generation_id}:schema")
        if not schema_json:
            return None
        
        current_schema = json.loads(schema_json)
        
        try:
            patched_schema = jsonpatch.apply_patch(current_schema, patch)
            cache.set(f"gen:{generation_id}:schema", json.dumps(patched_schema), GenerationCache.TTL_DEFAULT)
            
            # Regenerate code from patched schema
            generator = ReactCodeGenerator(patched_schema)
            new_code = generator.generate()
            cache.set(f"gen:{generation_id}:code", new_code, GenerationCache.TTL_DEFAULT)
            
            return patched_schema
        except Exception as e:
            logger.error(f"Patch application failed: {e}")
            return None