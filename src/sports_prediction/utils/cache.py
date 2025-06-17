"""Cache management utilities."""

import json
import pickle
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import redis
from pathlib import Path
from ..config.settings import settings
from .logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manages caching for sports data and predictions."""
    
    def __init__(self):
        self.redis_client = None
        self.file_cache_dir = settings.cache_dir
        self.file_cache_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Redis not available, using file cache: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return pickle.loads(value)
            else:
                return self._get_from_file(key)
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            ttl = ttl or settings.cache_ttl
            
            if self.redis_client:
                serialized = pickle.dumps(value)
                return self.redis_client.setex(key, ttl, serialized)
            else:
                return self._set_to_file(key, value, ttl)
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                return self._delete_from_file(key)
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def _get_from_file(self, key: str) -> Optional[Any]:
        """Get value from file cache."""
        cache_file = self.file_cache_dir / f"{key}.cache"
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            # Check if expired
            if data['expires_at'] < datetime.now():
                cache_file.unlink()
                return None
            
            return data['value']
        except Exception as e:
            logger.error(f"Error reading file cache: {e}")
            return None
    
    def _set_to_file(self, key: str, value: Any, ttl: int) -> bool:
        """Set value to file cache."""
        cache_file = self.file_cache_dir / f"{key}.cache"
        
        try:
            data = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            return True
        except Exception as e:
            logger.error(f"Error writing file cache: {e}")
            return False
    
    def _delete_from_file(self, key: str) -> bool:
        """Delete key from file cache."""
        cache_file = self.file_cache_dir / f"{key}.cache"
        try:
            if cache_file.exists():
                cache_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting file cache: {e}")
            return False
    
    def clear_expired(self):
        """Clear expired cache entries."""
        if self.redis_client:
            # Redis handles expiration automatically
            return
        
        # Clean up file cache
        for cache_file in self.file_cache_dir.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                
                if data['expires_at'] < datetime.now():
                    cache_file.unlink()
                    logger.debug(f"Removed expired cache file: {cache_file}")
            except Exception as e:
                logger.error(f"Error checking cache file {cache_file}: {e}")
                # Remove corrupted cache files
                cache_file.unlink()
