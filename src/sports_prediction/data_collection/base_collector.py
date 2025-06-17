"""Base class for data collectors."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
from ..utils.cache import CacheManager
from ..utils.rate_limiter import RateLimiter
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class BaseDataCollector(ABC):
    """Base class for all data collectors."""
    
    def __init__(self, name: str):
        self.name = name
        self.cache = CacheManager()
        self.rate_limiter = RateLimiter()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Sports-Prediction-Bot/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def get_team_stats(self, sport: str, team_id: str, season: str) -> Dict[str, Any]:
        """Get team statistics."""
        pass
    
    @abstractmethod
    async def get_player_stats(self, sport: str, player_id: str, season: str) -> Dict[str, Any]:
        """Get player statistics."""
        pass
    
    @abstractmethod
    async def get_match_history(self, sport: str, team1_id: str, team2_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get head-to-head match history."""
        pass
    
    @abstractmethod
    async def get_upcoming_matches(self, sport: str, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming matches."""
        pass
    
    @abstractmethod
    async def get_recent_matches(self, sport: str, team_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent matches for a team."""
        pass
    
    async def make_request(self, url: str, params: Optional[Dict] = None, cache_key: Optional[str] = None) -> Optional[Dict]:
        """Make HTTP request with caching and rate limiting."""
        
        # Check cache first
        if cache_key:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        
        # Rate limiting
        self.rate_limiter.wait_if_needed(self.name)
        
        try:
            if not self.session:
                raise RuntimeError("Session not initialized. Use async context manager.")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Cache the result
                    if cache_key:
                        self.cache.set(cache_key, data)
                        logger.debug(f"Cached data for {cache_key}")
                    
                    return data
                else:
                    logger.error(f"HTTP {response.status} for {url}")
                    return None
        
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def get_cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        return f"{self.name}:" + ":".join(str(arg) for arg in args)
    
    async def collect_all_data(self, sport: str, team_ids: List[str]) -> Dict[str, Any]:
        """Collect all available data for given teams."""
        data = {
            'teams': {},
            'matches': [],
            'players': {},
            'updated_at': datetime.now().isoformat()
        }
        
        # Collect team data
        for team_id in team_ids:
            try:
                team_stats = await self.get_team_stats(sport, team_id, "2024")
                if team_stats:
                    data['teams'][team_id] = team_stats
                
                recent_matches = await self.get_recent_matches(sport, team_id)
                if recent_matches:
                    data['matches'].extend(recent_matches)
                
                # Add delay between teams
                self.rate_limiter.add_delay(self.name)
                
            except Exception as e:
                logger.error(f"Error collecting data for team {team_id}: {e}")
        
        # Get upcoming matches
        try:
            upcoming = await self.get_upcoming_matches(sport)
            if upcoming:
                data['matches'].extend(upcoming)
        except Exception as e:
            logger.error(f"Error collecting upcoming matches: {e}")
        
        return data
