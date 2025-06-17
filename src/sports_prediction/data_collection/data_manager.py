"""Data manager for coordinating multiple data sources."""

import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
from .espn_collector import ESPNCollector
from .sportradar_collector import SportRadarCollector
from .odds_collector import OddsCollector
from .web_scraper import WebScraper
from ..utils.cache import CacheManager
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class DataManager:
    """Manages data collection from multiple sources."""
    
    def __init__(self):
        self.cache = CacheManager()
        self.collectors = {}
        self.scraper = None
        
        # Initialize collectors
        self.collectors['espn'] = ESPNCollector()
        self.collectors['sportradar'] = SportRadarCollector()
        self.collectors['odds'] = OddsCollector()
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Initialize all collectors
        for collector in self.collectors.values():
            await collector.__aenter__()
        
        # Initialize scraper
        self.scraper = WebScraper()
        await self.scraper.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Close all collectors
        for collector in self.collectors.values():
            await collector.__aexit__(exc_type, exc_val, exc_tb)
        
        # Close scraper
        if self.scraper:
            await self.scraper.__aexit__(exc_type, exc_val, exc_tb)
    
    async def collect_comprehensive_data(self, sport: str, team_ids: List[str]) -> Dict[str, Any]:
        """Collect comprehensive data from all sources."""
        logger.info(f"Starting comprehensive data collection for {sport}")
        
        # Collect data from all sources concurrently
        tasks = []
        
        # API collectors
        for source_name, collector in self.collectors.items():
            if source_name != 'odds':  # Odds collector doesn't provide team stats
                task = asyncio.create_task(
                    collector.collect_all_data(sport, team_ids),
                    name=f"{source_name}_collection"
                )
                tasks.append((source_name, task))
        
        # Odds data
        odds_task = asyncio.create_task(
            self.collectors['odds'].get_upcoming_matches(sport),
            name="odds_collection"
        )
        tasks.append(('odds', odds_task))
        
        # Web scraping tasks
        if self.scraper:
            for team_id in team_ids[:3]:  # Limit scraping to avoid rate limits
                scrape_task = asyncio.create_task(
                    self._scrape_team_data(sport, team_id),
                    name=f"scrape_{team_id}"
                )
                tasks.append((f'scrape_{team_id}', scrape_task))
        
        # Wait for all tasks to complete
        results = {}
        for source_name, task in tasks:
            try:
                result = await task
                results[source_name] = result
                logger.info(f"Completed data collection from {source_name}")
            except Exception as e:
                logger.error(f"Error collecting data from {source_name}: {e}")
                results[source_name] = {}
        
        # Merge and process results
        merged_data = self._merge_data_sources(results, sport)
        
        # Save to cache and file
        await self._save_data(merged_data, sport)
        
        logger.info(f"Comprehensive data collection completed for {sport}")
        return merged_data
    
    async def get_team_analysis(self, sport: str, team_id: str) -> Dict[str, Any]:
        """Get comprehensive team analysis from all sources."""
        cache_key = f"team_analysis:{sport}:{team_id}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Collect team data from multiple sources
        tasks = []
        
        for source_name, collector in self.collectors.items():
            if source_name != 'odds':
                task = asyncio.create_task(
                    collector.get_team_stats(sport, team_id, "2024")
                )
                tasks.append((source_name, task))
        
        # Recent matches
        recent_matches_tasks = []
        for source_name, collector in self.collectors.items():
            if source_name != 'odds':
                task = asyncio.create_task(
                    collector.get_recent_matches(sport, team_id, 10)
                )
                recent_matches_tasks.append((source_name, task))
        
        # Execute all tasks
        team_stats = {}
        recent_matches = {}
        
        for source_name, task in tasks:
            try:
                result = await task
                team_stats[source_name] = result
            except Exception as e:
                logger.error(f"Error getting team stats from {source_name}: {e}")
                team_stats[source_name] = {}
        
        for source_name, task in recent_matches_tasks:
            try:
                result = await task
                recent_matches[source_name] = result
            except Exception as e:
                logger.error(f"Error getting recent matches from {source_name}: {e}")
                recent_matches[source_name] = []
        
        # Web scraping data
        scraped_data = {}
        if self.scraper:
            try:
                scraped_data = await self._scrape_team_data(sport, team_id)
            except Exception as e:
                logger.error(f"Error scraping team data: {e}")
        
        # Merge all data
        analysis = {
            'team_id': team_id,
            'sport': sport,
            'team_stats': team_stats,
            'recent_matches': recent_matches,
            'scraped_data': scraped_data,
            'updated_at': datetime.now().isoformat()
        }
        
        # Cache the result
        self.cache.set(cache_key, analysis, ttl=1800)  # 30 minutes
        
        return analysis
    
    async def get_match_prediction_data(self, sport: str, home_team_id: str, away_team_id: str) -> Dict[str, Any]:
        """Get all data needed for match prediction."""
        logger.info(f"Collecting prediction data for {home_team_id} vs {away_team_id}")
        
        # Get team analyses
        home_analysis_task = asyncio.create_task(
            self.get_team_analysis(sport, home_team_id)
        )
        away_analysis_task = asyncio.create_task(
            self.get_team_analysis(sport, away_team_id)
        )
        
        # Get head-to-head history
        h2h_tasks = []
        for source_name, collector in self.collectors.items():
            if source_name != 'odds':
                task = asyncio.create_task(
                    collector.get_match_history(sport, home_team_id, away_team_id, 10)
                )
                h2h_tasks.append((source_name, task))
        
        # Get odds data
        odds_task = asyncio.create_task(
            self.collectors['odds'].get_upcoming_matches(sport)
        )
        
        # Wait for all tasks
        home_analysis = await home_analysis_task
        away_analysis = await away_analysis_task
        
        h2h_history = {}
        for source_name, task in h2h_tasks:
            try:
                result = await task
                h2h_history[source_name] = result
            except Exception as e:
                logger.error(f"Error getting H2H history from {source_name}: {e}")
                h2h_history[source_name] = []
        
        try:
            odds_data = await odds_task
            # Find odds for this specific match
            match_odds = None
            for match in odds_data:
                if ((match.get('home_team') == home_team_id or match.get('home_team') in home_analysis.get('team_stats', {}).get('espn', {}).get('name', '')) and
                    (match.get('away_team') == away_team_id or match.get('away_team') in away_analysis.get('team_stats', {}).get('espn', {}).get('name', ''))):
                    match_odds = match
                    break
        except Exception as e:
            logger.error(f"Error getting odds data: {e}")
            match_odds = None
        
        return {
            'home_team': home_analysis,
            'away_team': away_analysis,
            'head_to_head': h2h_history,
            'odds': match_odds,
            'sport': sport,
            'updated_at': datetime.now().isoformat()
        }
    
    async def _scrape_team_data(self, sport: str, team_id: str) -> Dict[str, Any]:
        """Scrape additional team data from web sources."""
        if not self.scraper:
            return {}
        
        scraped_data = {}
        
        # Determine appropriate scraping sources based on sport
        sources = []
        if sport in ['mls', 'premier_league', 'la_liga', 'bundesliga', 'serie_a', 'champions_league']:
            sources = ['transfermarkt', 'fbref']
        elif sport == 'nba':
            sources = ['basketball_reference']
        elif sport == 'nfl':
            sources = ['pro_football_reference']
        elif sport == 'nhl':
            sources = ['hockey_reference']
        
        for source in sources:
            try:
                data = await self.scraper.scrape_team_data(source, sport, team_id)
                if data:
                    scraped_data[source] = data
            except Exception as e:
                logger.error(f"Error scraping from {source}: {e}")
        
        return scraped_data
    
    def _merge_data_sources(self, results: Dict[str, Any], sport: str) -> Dict[str, Any]:
        """Merge data from multiple sources."""
        merged = {
            'sport': sport,
            'sources': list(results.keys()),
            'teams': {},
            'matches': [],
            'odds': [],
            'scraped_data': {},
            'updated_at': datetime.now().isoformat()
        }
        
        # Merge team data
        for source, data in results.items():
            if isinstance(data, dict) and 'teams' in data:
                for team_id, team_data in data['teams'].items():
                    if team_id not in merged['teams']:
                        merged['teams'][team_id] = {}
                    merged['teams'][team_id][source] = team_data
        
        # Merge match data
        for source, data in results.items():
            if isinstance(data, dict) and 'matches' in data:
                for match in data['matches']:
                    match['source'] = source
                    merged['matches'].append(match)
            elif isinstance(data, list) and source == 'odds':
                merged['odds'] = data
        
        # Merge scraped data
        for source, data in results.items():
            if source.startswith('scrape_'):
                merged['scraped_data'][source] = data
        
        return merged
    
    async def _save_data(self, data: Dict[str, Any], sport: str) -> None:
        """Save collected data to file and cache."""
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sport}_data_{timestamp}.json"
        filepath = settings.raw_data_dir / filename
        
        try:
            import json
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Data saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving data to file: {e}")
        
        # Save to cache
        cache_key = f"comprehensive_data:{sport}"
        self.cache.set(cache_key, data, ttl=3600)  # 1 hour
