"""SportRadar data collector for comprehensive sports data."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base_collector import BaseDataCollector
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class SportRadarCollector(BaseDataCollector):
    """SportRadar API data collector."""
    
    def __init__(self):
        super().__init__("sportradar")
        self.base_url = "https://api.sportradar.us"
        self.api_key = settings.sportradar_api_key
        
        # Sport API endpoints for SportRadar
        self.sport_endpoints = {
            'nfl': f"{self.base_url}/nfl/official/trial/v7/en",
            'nba': f"{self.base_url}/nba/trial/v8/en",
            'mlb': f"{self.base_url}/mlb/trial/v7/en",
            'nhl': f"{self.base_url}/nhl/trial/v7/en",
            'mls': f"{self.base_url}/soccer-t3/global/trial/v4/en",
            'premier_league': f"{self.base_url}/soccer-t3/global/trial/v4/en",
            'champions_league': f"{self.base_url}/soccer-t3/global/trial/v4/en",
            'tennis': f"{self.base_url}/tennis/trial/v3/en",
        }
        
        # League IDs for soccer competitions
        self.soccer_leagues = {
            'mls': 'sr:tournament:242',
            'premier_league': 'sr:tournament:17',
            'champions_league': 'sr:tournament:7',
            'la_liga': 'sr:tournament:8',
            'bundesliga': 'sr:tournament:35',
            'serie_a': 'sr:tournament:23',
        }
    
    async def get_team_stats(self, sport: str, team_id: str, season: str) -> Dict[str, Any]:
        """Get team statistics from SportRadar."""
        if sport not in self.sport_endpoints:
            logger.warning(f"Sport {sport} not supported by SportRadar collector")
            return {}
        
        cache_key = self.get_cache_key("team_stats", sport, team_id, season)
        
        if sport in ['mls', 'premier_league', 'champions_league', 'la_liga', 'bundesliga', 'serie_a']:
            return await self._get_soccer_team_stats(sport, team_id, season, cache_key)
        else:
            return await self._get_us_sport_team_stats(sport, team_id, season, cache_key)
    
    async def get_player_stats(self, sport: str, player_id: str, season: str) -> Dict[str, Any]:
        """Get player statistics from SportRadar."""
        if sport not in self.sport_endpoints:
            return {}
        
        cache_key = self.get_cache_key("player_stats", sport, player_id, season)
        
        if sport in ['mls', 'premier_league', 'champions_league', 'la_liga', 'bundesliga', 'serie_a']:
            return await self._get_soccer_player_stats(sport, player_id, season, cache_key)
        else:
            return await self._get_us_sport_player_stats(sport, player_id, season, cache_key)
    
    async def get_match_history(self, sport: str, team1_id: str, team2_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get head-to-head match history."""
        if sport not in self.sport_endpoints:
            return []
        
        cache_key = self.get_cache_key("match_history", sport, team1_id, team2_id, limit)
        
        # Get recent matches for team1 and filter for head-to-head
        team1_matches = await self.get_recent_matches(sport, team1_id, limit * 3)
        
        h2h_matches = []
        for match in team1_matches:
            if self._is_head_to_head_match(match, team1_id, team2_id):
                h2h_matches.append(match)
                if len(h2h_matches) >= limit:
                    break
        
        return h2h_matches
    
    async def get_upcoming_matches(self, sport: str, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming matches."""
        if sport not in self.sport_endpoints:
            return []
        
        cache_key = self.get_cache_key("upcoming_matches", sport, days_ahead)
        
        if sport in ['mls', 'premier_league', 'champions_league', 'la_liga', 'bundesliga', 'serie_a']:
            return await self._get_soccer_upcoming_matches(sport, days_ahead, cache_key)
        else:
            return await self._get_us_sport_upcoming_matches(sport, days_ahead, cache_key)
    
    async def get_recent_matches(self, sport: str, team_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent matches for a team."""
        if sport not in self.sport_endpoints:
            return []
        
        cache_key = self.get_cache_key("recent_matches", sport, team_id, limit)
        
        if sport in ['mls', 'premier_league', 'champions_league', 'la_liga', 'bundesliga', 'serie_a']:
            return await self._get_soccer_recent_matches(sport, team_id, limit, cache_key)
        else:
            return await self._get_us_sport_recent_matches(sport, team_id, limit, cache_key)
    
    async def _get_us_sport_team_stats(self, sport: str, team_id: str, season: str, cache_key: str) -> Dict[str, Any]:
        """Get US sport team statistics."""
        base_url = self.sport_endpoints[sport]
        url = f"{base_url}/seasons/{season}/teams/{team_id}/statistics.json"
        
        params = {"api_key": self.api_key} if self.api_key else {}
        data = await self.make_request(url, params, cache_key)
        
        if data:
            return self._parse_us_sport_team_stats(data)
        return {}
    
    async def _get_soccer_team_stats(self, sport: str, team_id: str, season: str, cache_key: str) -> Dict[str, Any]:
        """Get soccer team statistics."""
        base_url = self.sport_endpoints[sport]
        league_id = self.soccer_leagues.get(sport)
        
        if not league_id:
            return {}
        
        url = f"{base_url}/tournaments/{league_id}/seasons/{season}/teams/{team_id}/statistics.json"
        
        params = {"api_key": self.api_key} if self.api_key else {}
        data = await self.make_request(url, params, cache_key)
        
        if data:
            return self._parse_soccer_team_stats(data)
        return {}
    
    async def _get_us_sport_upcoming_matches(self, sport: str, days_ahead: int, cache_key: str) -> List[Dict[str, Any]]:
        """Get upcoming US sport matches."""
        base_url = self.sport_endpoints[sport]
        
        # Get current season schedule
        current_year = datetime.now().year
        url = f"{base_url}/games/{current_year}/schedule.json"
        
        params = {"api_key": self.api_key} if self.api_key else {}
        data = await self.make_request(url, params, cache_key)
        
        if data and 'games' in data:
            upcoming = []
            cutoff_date = datetime.now() + timedelta(days=days_ahead)
            
            for game in data['games']:
                game_date = datetime.fromisoformat(game.get('scheduled', '').replace('Z', '+00:00'))
                if datetime.now() <= game_date <= cutoff_date:
                    upcoming.append(self._parse_us_sport_match(game))
            
            return upcoming
        
        return []
    
    async def _get_soccer_upcoming_matches(self, sport: str, days_ahead: int, cache_key: str) -> List[Dict[str, Any]]:
        """Get upcoming soccer matches."""
        base_url = self.sport_endpoints[sport]
        league_id = self.soccer_leagues.get(sport)
        
        if not league_id:
            return []
        
        # Get current season schedule
        current_year = datetime.now().year
        url = f"{base_url}/tournaments/{league_id}/seasons/{current_year}/schedule.json"
        
        params = {"api_key": self.api_key} if self.api_key else {}
        data = await self.make_request(url, params, cache_key)
        
        if data and 'sport_events' in data:
            upcoming = []
            cutoff_date = datetime.now() + timedelta(days=days_ahead)
            
            for event in data['sport_events']:
                event_date = datetime.fromisoformat(event.get('scheduled', '').replace('Z', '+00:00'))
                if datetime.now() <= event_date <= cutoff_date:
                    upcoming.append(self._parse_soccer_match(event))
            
            return upcoming
        
        return []
    
    def _parse_us_sport_team_stats(self, data: Dict) -> Dict[str, Any]:
        """Parse US sport team statistics."""
        team = data.get('team', {})
        stats = data.get('statistics', {})
        
        return {
            'id': team.get('id'),
            'name': team.get('name'),
            'market': team.get('market'),
            'statistics': stats,
            'source': 'sportradar'
        }
    
    def _parse_soccer_team_stats(self, data: Dict) -> Dict[str, Any]:
        """Parse soccer team statistics."""
        team = data.get('team', {})
        stats = data.get('statistics', {})
        
        return {
            'id': team.get('id'),
            'name': team.get('name'),
            'statistics': stats,
            'source': 'sportradar'
        }
    
    def _parse_us_sport_match(self, game_data: Dict) -> Dict[str, Any]:
        """Parse US sport match data."""
        return {
            'id': game_data.get('id'),
            'date': game_data.get('scheduled'),
            'status': game_data.get('status'),
            'home_team': {
                'id': game_data.get('home', {}).get('id'),
                'name': game_data.get('home', {}).get('name'),
                'score': game_data.get('home_points')
            },
            'away_team': {
                'id': game_data.get('away', {}).get('id'),
                'name': game_data.get('away', {}).get('name'),
                'score': game_data.get('away_points')
            },
            'venue': game_data.get('venue', {}).get('name'),
            'source': 'sportradar'
        }
    
    def _parse_soccer_match(self, event_data: Dict) -> Dict[str, Any]:
        """Parse soccer match data."""
        competitors = event_data.get('competitors', [])
        home_team = next((c for c in competitors if c.get('qualifier') == 'home'), {})
        away_team = next((c for c in competitors if c.get('qualifier') == 'away'), {})
        
        return {
            'id': event_data.get('id'),
            'date': event_data.get('scheduled'),
            'status': event_data.get('status'),
            'home_team': {
                'id': home_team.get('id'),
                'name': home_team.get('name')
            },
            'away_team': {
                'id': away_team.get('id'),
                'name': away_team.get('name')
            },
            'venue': event_data.get('venue', {}).get('name'),
            'source': 'sportradar'
        }
    
    async def _get_us_sport_player_stats(self, sport: str, player_id: str, season: str, cache_key: str) -> Dict[str, Any]:
        """Get US sport player statistics."""
        base_url = self.sport_endpoints[sport]
        url = f"{base_url}/players/{player_id}/profile.json"

        params = {"api_key": self.api_key} if self.api_key else {}
        data = await self.make_request(url, params, cache_key)

        if data:
            return self._parse_us_sport_player_stats(data)
        return {}

    async def _get_soccer_player_stats(self, sport: str, player_id: str, season: str, cache_key: str) -> Dict[str, Any]:
        """Get soccer player statistics."""
        base_url = self.sport_endpoints[sport]
        url = f"{base_url}/players/{player_id}/profile.json"

        params = {"api_key": self.api_key} if self.api_key else {}
        data = await self.make_request(url, params, cache_key)

        if data:
            return self._parse_soccer_player_stats(data)
        return {}

    async def _get_us_sport_recent_matches(self, sport: str, team_id: str, limit: int, cache_key: str) -> List[Dict[str, Any]]:
        """Get recent US sport matches for a team."""
        base_url = self.sport_endpoints[sport]
        current_year = datetime.now().year
        url = f"{base_url}/teams/{team_id}/schedule.json"

        params = {"api_key": self.api_key} if self.api_key else {}
        data = await self.make_request(url, params, cache_key)

        if data and 'games' in data:
            recent = []
            for game in data['games']:
                game_date = datetime.fromisoformat(game.get('scheduled', '').replace('Z', '+00:00'))
                if game_date <= datetime.now() and game.get('status') == 'closed':
                    recent.append(self._parse_us_sport_match(game))
                    if len(recent) >= limit:
                        break
            return recent
        return []

    async def _get_soccer_recent_matches(self, sport: str, team_id: str, limit: int, cache_key: str) -> List[Dict[str, Any]]:
        """Get recent soccer matches for a team."""
        base_url = self.sport_endpoints[sport]
        url = f"{base_url}/teams/{team_id}/results.json"

        params = {"api_key": self.api_key} if self.api_key else {}
        data = await self.make_request(url, params, cache_key)

        if data and 'results' in data:
            recent = []
            for event in data['results'][:limit]:
                recent.append(self._parse_soccer_match(event))
            return recent
        return []

    def _parse_us_sport_player_stats(self, data: Dict) -> Dict[str, Any]:
        """Parse US sport player statistics."""
        player = data.get('player', {})

        return {
            'id': player.get('id'),
            'name': player.get('full_name'),
            'position': player.get('position'),
            'team_id': player.get('team', {}).get('id'),
            'statistics': data.get('statistics', {}),
            'source': 'sportradar'
        }

    def _parse_soccer_player_stats(self, data: Dict) -> Dict[str, Any]:
        """Parse soccer player statistics."""
        player = data.get('player', {})

        return {
            'id': player.get('id'),
            'name': player.get('name'),
            'position': player.get('type'),
            'team_id': player.get('team', {}).get('id'),
            'statistics': data.get('statistics', {}),
            'source': 'sportradar'
        }

    def _is_head_to_head_match(self, match: Dict, team1_id: str, team2_id: str) -> bool:
        """Check if match is between two specific teams."""
        home_id = match.get('home_team', {}).get('id')
        away_id = match.get('away_team', {}).get('id')
        return (home_id == team1_id and away_id == team2_id) or (home_id == team2_id and away_id == team1_id)
