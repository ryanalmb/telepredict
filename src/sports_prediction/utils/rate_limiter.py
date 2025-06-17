"""Rate limiting utilities for API calls and web scraping."""

import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from ..config.settings import settings
from .logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for API calls and web scraping."""
    
    def __init__(self, requests_per_minute: Optional[int] = None):
        self.requests_per_minute = requests_per_minute or settings.api_rate_limit
        self.request_times: Dict[str, deque] = defaultdict(deque)
        self.last_request_time: Dict[str, float] = {}
    
    def wait_if_needed(self, identifier: str = "default") -> None:
        """Wait if rate limit would be exceeded."""
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        cutoff_time = current_time - 60
        while (self.request_times[identifier] and 
               self.request_times[identifier][0] < cutoff_time):
            self.request_times[identifier].popleft()
        
        # Check if we need to wait
        if len(self.request_times[identifier]) >= self.requests_per_minute:
            # Calculate wait time
            oldest_request = self.request_times[identifier][0]
            wait_time = 60 - (current_time - oldest_request)
            
            if wait_time > 0:
                logger.info(f"Rate limit reached for {identifier}, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
        
        # Add current request
        self.request_times[identifier].append(current_time)
        self.last_request_time[identifier] = current_time
    
    def add_delay(self, identifier: str = "default", delay: Optional[float] = None) -> None:
        """Add a delay between requests."""
        delay = delay or settings.scraper_delay
        
        if identifier in self.last_request_time:
            elapsed = time.time() - self.last_request_time[identifier]
            if elapsed < delay:
                sleep_time = delay - elapsed
                logger.debug(f"Adding delay of {sleep_time:.2f} seconds for {identifier}")
                time.sleep(sleep_time)
    
    def reset(self, identifier: str = "default") -> None:
        """Reset rate limiter for a specific identifier."""
        if identifier in self.request_times:
            self.request_times[identifier].clear()
        if identifier in self.last_request_time:
            del self.last_request_time[identifier]
