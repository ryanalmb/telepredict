"""ESPN data collector for sports statistics."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base_collector import BaseDataCollector
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class ESPNCollector(BaseDataCollector):
    """ESPN API data collector."""
    
    def __init__(self):
        super().__init__("espn")
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports"
        self.api_key = settings.espn_api_key
        
        # Sport mappings for ESPN API
        self.sport_mappings = {
            'nfl': 'football/nfl',
            'nba': 'basketball/nba',
            'mlb': 'baseball/mlb',
            'nhl': 'hockey/nhl',
            'mls': 'soccer/usa.1',
            'premier_league': 'soccer/eng.1',
            'champions_league': 'soccer/uefa.champions',
            'la_liga': 'soccer/esp.1',
            'bundesliga': 'soccer/ger.1',
            'serie_a': 'soccer/ita.1',
            'tennis': 'tennis',
        }
    
    async def get_team_stats(self, sport: str, team_id: str, season: str) -> Dict[str, Any]:
        """Get team statistics from ESPN."""
        sport_path = self.sport_mappings.get(sport)
        if not sport_path:
            logger.warning(f"Sport {sport} not supported by ESPN collector")
            return {}
        
        cache_key = self.get_cache_key("team_stats", sport, team_id, season)
        url = f"{self.base_url}/{sport_path}/teams/{team_id}/statistics"
        
        params = {"season": season}
        if self.api_key:
            params["apikey"] = self.api_key
        
        data = await self.make_request(url, params, cache_key)
        
        if data and 'team' in data:
            return self._parse_team_stats(data['team'])
        
        return {}
    
    async def get_player_stats(self, sport: str, player_id: str, season: str) -> Dict[str, Any]:
        """Get player statistics from ESPN."""
        sport_path = self.sport_mappings.get(sport)
        if not sport_path:
            return {}
        
        cache_key = self.get_cache_key("player_stats", sport, player_id, season)
        url = f"{self.base_url}/{sport_path}/athletes/{player_id}/statistics"
        
        params = {"season": season}
        if self.api_key:
            params["apikey"] = self.api_key
        
        data = await self.make_request(url, params, cache_key)
        
        if data and 'athlete' in data:
            return self._parse_player_stats(data['athlete'])
        
        return {}
    
    async def get_match_history(self, sport: str, team1_id: str, team2_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get head-to-head match history."""
        sport_path = self.sport_mappings.get(sport)
        if not sport_path:
            return []
        
        cache_key = self.get_cache_key("match_history", sport, team1_id, team2_id, limit)
        url = f"{self.base_url}/{sport_path}/teams/{team1_id}/events"
        
        params = {"limit": limit * 2}  # Get more to filter for head-to-head
        if self.api_key:
            params["apikey"] = self.api_key
        
        data = await self.make_request(url, params, cache_key)
        
        if data and 'events' in data:
            # Filter for matches against team2
            h2h_matches = []
            for event in data['events']:
                if self._is_head_to_head_match(event, team1_id, team2_id):
                    h2h_matches.append(self._parse_match(event))
                    if len(h2h_matches) >= limit:
                        break
            return h2h_matches
        
        return []
    
    async def get_upcoming_matches(self, sport: str, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming matches."""
        sport_path = self.sport_mappings.get(sport)
        if not sport_path:
            return []
        
        cache_key = self.get_cache_key("upcoming_matches", sport, days_ahead)
        url = f"{self.base_url}/{sport_path}/scoreboard"
        
        # Calculate date range
        start_date = datetime.now().strftime("%Y%m%d")
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y%m%d")
        
        params = {
            "dates": f"{start_date}-{end_date}",
            "limit": 100
        }
        if self.api_key:
            params["apikey"] = self.api_key
        
        data = await self.make_request(url, params, cache_key)
        
        if data and 'events' in data:
            return [self._parse_match(event) for event in data['events']]
        
        return []
    
    async def get_recent_matches(self, sport: str, team_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent matches for a team."""
        sport_path = self.sport_mappings.get(sport)
        if not sport_path:
            return []
        
        cache_key = self.get_cache_key("recent_matches", sport, team_id, limit)
        url = f"{self.base_url}/{sport_path}/teams/{team_id}/events"
        
        params = {"limit": limit}
        if self.api_key:
            params["apikey"] = self.api_key
        
        data = await self.make_request(url, params, cache_key)
        
        if data and 'events' in data:
            return [self._parse_match(event) for event in data['events']]
        
        return []
    
    def _parse_team_stats(self, team_data: Dict) -> Dict[str, Any]:
        """Parse team statistics data."""
        stats = {}
        
        if 'statistics' in team_data:
            for stat in team_data['statistics']:
                stats[stat.get('name', '')] = stat.get('value', 0)
        
        return {
            'id': team_data.get('id'),
            'name': team_data.get('displayName'),
            'abbreviation': team_data.get('abbreviation'),
            'logo': team_data.get('logo'),
            'statistics': stats,
            'record': team_data.get('record', {}),
            'source': 'espn'
        }
    
    def _parse_player_stats(self, player_data: Dict) -> Dict[str, Any]:
        """Parse player statistics data."""
        stats = {}
        
        if 'statistics' in player_data:
            for stat in player_data['statistics']:
                stats[stat.get('name', '')] = stat.get('value', 0)
        
        return {
            'id': player_data.get('id'),
            'name': player_data.get('displayName'),
            'position': player_data.get('position', {}).get('displayName'),
            'team_id': player_data.get('team', {}).get('id'),
            'statistics': stats,
            'source': 'espn'
        }
    
    def _parse_match(self, event_data: Dict) -> Dict[str, Any]:
        """Parse match/event data."""
        competitors = event_data.get('competitions', [{}])[0].get('competitors', [])
        
        home_team = next((c for c in competitors if c.get('homeAway') == 'home'), {})
        away_team = next((c for c in competitors if c.get('homeAway') == 'away'), {})
        
        return {
            'id': event_data.get('id'),
            'date': event_data.get('date'),
            'status': event_data.get('status', {}).get('type', {}).get('name'),
            'home_team': {
                'id': home_team.get('team', {}).get('id'),
                'name': home_team.get('team', {}).get('displayName'),
                'score': home_team.get('score'),
                'record': home_team.get('records', [{}])[0].get('summary') if home_team.get('records') else None
            },
            'away_team': {
                'id': away_team.get('team', {}).get('id'),
                'name': away_team.get('team', {}).get('displayName'),
                'score': away_team.get('score'),
                'record': away_team.get('records', [{}])[0].get('summary') if away_team.get('records') else None
            },
            'venue': event_data.get('competitions', [{}])[0].get('venue', {}).get('fullName'),
            'source': 'espn'
        }
    
    def _is_head_to_head_match(self, event: Dict, team1_id: str, team2_id: str) -> bool:
        """Check if event is a head-to-head match between two teams."""
        competitors = event.get('competitions', [{}])[0].get('competitors', [])
        team_ids = [c.get('team', {}).get('id') for c in competitors]
        return team1_id in team_ids and team2_id in team_ids
