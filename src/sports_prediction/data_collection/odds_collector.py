"""Odds data collector for betting odds comparison."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base_collector import BaseDataCollector
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class OddsCollector(BaseDataCollector):
    """Odds API data collector for betting odds."""
    
    def __init__(self):
        super().__init__("odds")
        self.base_url = "https://api.the-odds-api.com/v4"
        self.api_key = settings.odds_api_key
        
        # Sport keys for The Odds API
        self.sport_keys = {
            'nfl': 'americanfootball_nfl',
            'nba': 'basketball_nba',
            'mlb': 'baseball_mlb',
            'nhl': 'icehockey_nhl',
            'mls': 'soccer_usa_mls',
            'premier_league': 'soccer_epl',
            'champions_league': 'soccer_uefa_champs_league',
            'la_liga': 'soccer_spain_la_liga',
            'bundesliga': 'soccer_germany_bundesliga',
            'serie_a': 'soccer_italy_serie_a',
            'tennis': 'tennis_wta',
            'ufc': 'mma_mixed_martial_arts',
            'boxing': 'boxing_heavyweight',
        }
        
        # Popular bookmakers
        self.bookmakers = [
            'draftkings', 'fanduel', 'betmgm', 'caesars', 'pointsbet',
            'bet365', 'pinnacle', 'betway', 'unibet'
        ]
    
    async def get_team_stats(self, sport: str, team_id: str, season: str) -> Dict[str, Any]:
        """Odds collector doesn't provide team stats."""
        return {}
    
    async def get_player_stats(self, sport: str, player_id: str, season: str) -> Dict[str, Any]:
        """Odds collector doesn't provide player stats."""
        return {}
    
    async def get_match_history(self, sport: str, team1_id: str, team2_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical odds for head-to-head matches."""
        # This would require a premium subscription to get historical odds
        # For now, return empty list
        return []
    
    async def get_upcoming_matches(self, sport: str, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming matches with odds."""
        sport_key = self.sport_keys.get(sport)
        if not sport_key or not self.api_key:
            logger.warning(f"Sport {sport} not supported or API key missing for odds collector")
            return []
        
        cache_key = self.get_cache_key("upcoming_odds", sport, days_ahead)
        url = f"{self.base_url}/sports/{sport_key}/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': 'us,uk,eu',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        
        data = await self.make_request(url, params, cache_key)
        
        if data:
            return [self._parse_odds_event(event) for event in data]
        
        return []
    
    async def get_recent_matches(self, sport: str, team_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Odds collector focuses on upcoming matches."""
        return []
    
    async def get_live_odds(self, sport: str, event_id: str) -> Dict[str, Any]:
        """Get live odds for a specific event."""
        sport_key = self.sport_keys.get(sport)
        if not sport_key or not self.api_key:
            return {}
        
        cache_key = self.get_cache_key("live_odds", sport, event_id)
        url = f"{self.base_url}/sports/{sport_key}/events/{event_id}/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': 'us,uk,eu',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'decimal'
        }
        
        data = await self.make_request(url, params, cache_key)
        
        if data:
            return self._parse_odds_event(data)
        
        return {}
    
    async def get_odds_comparison(self, sport: str, event_id: str) -> Dict[str, Any]:
        """Get odds comparison across multiple bookmakers."""
        odds_data = await self.get_live_odds(sport, event_id)
        
        if not odds_data or 'bookmakers' not in odds_data:
            return {}
        
        comparison = {
            'event_id': event_id,
            'sport': sport,
            'best_odds': {},
            'bookmaker_count': len(odds_data['bookmakers']),
            'markets': {}
        }
        
        # Process each market type
        for bookmaker in odds_data['bookmakers']:
            for market in bookmaker.get('markets', []):
                market_key = market['key']
                
                if market_key not in comparison['markets']:
                    comparison['markets'][market_key] = {
                        'outcomes': {},
                        'best_odds': {},
                        'bookmaker_odds': {}
                    }
                
                # Track odds for each outcome
                for outcome in market.get('outcomes', []):
                    outcome_name = outcome['name']
                    odds_value = outcome['price']
                    
                    # Track best odds
                    if (outcome_name not in comparison['markets'][market_key]['best_odds'] or
                        odds_value > comparison['markets'][market_key]['best_odds'][outcome_name]['odds']):
                        comparison['markets'][market_key]['best_odds'][outcome_name] = {
                            'odds': odds_value,
                            'bookmaker': bookmaker['title']
                        }
                    
                    # Track all bookmaker odds
                    if outcome_name not in comparison['markets'][market_key]['bookmaker_odds']:
                        comparison['markets'][market_key]['bookmaker_odds'][outcome_name] = {}
                    
                    comparison['markets'][market_key]['bookmaker_odds'][outcome_name][bookmaker['title']] = odds_value
        
        return comparison
    
    async def get_arbitrage_opportunities(self, sport: str) -> List[Dict[str, Any]]:
        """Find arbitrage betting opportunities."""
        upcoming_matches = await self.get_upcoming_matches(sport)
        arbitrage_opportunities = []
        
        for match in upcoming_matches:
            if 'bookmakers' not in match or len(match['bookmakers']) < 2:
                continue
            
            # Check for arbitrage in h2h market
            h2h_arb = self._check_arbitrage_h2h(match)
            if h2h_arb:
                arbitrage_opportunities.append({
                    'event_id': match['id'],
                    'sport': sport,
                    'teams': f"{match['home_team']} vs {match['away_team']}",
                    'market': 'h2h',
                    'arbitrage': h2h_arb,
                    'profit_margin': h2h_arb['profit_margin']
                })
        
        return sorted(arbitrage_opportunities, key=lambda x: x['profit_margin'], reverse=True)
    
    def _parse_odds_event(self, event_data: Dict) -> Dict[str, Any]:
        """Parse odds event data."""
        return {
            'id': event_data.get('id'),
            'sport_key': event_data.get('sport_key'),
            'sport_title': event_data.get('sport_title'),
            'commence_time': event_data.get('commence_time'),
            'home_team': event_data.get('home_team'),
            'away_team': event_data.get('away_team'),
            'bookmakers': event_data.get('bookmakers', []),
            'source': 'odds_api'
        }
    
    def _check_arbitrage_h2h(self, match: Dict) -> Optional[Dict[str, Any]]:
        """Check for arbitrage opportunity in head-to-head market."""
        best_home_odds = 0
        best_away_odds = 0
        best_home_bookmaker = ""
        best_away_bookmaker = ""
        
        # Find best odds for each outcome
        for bookmaker in match.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':
                    for outcome in market.get('outcomes', []):
                        if outcome['name'] == match['home_team'] and outcome['price'] > best_home_odds:
                            best_home_odds = outcome['price']
                            best_home_bookmaker = bookmaker['title']
                        elif outcome['name'] == match['away_team'] and outcome['price'] > best_away_odds:
                            best_away_odds = outcome['price']
                            best_away_bookmaker = bookmaker['title']
        
        if best_home_odds > 0 and best_away_odds > 0:
            # Calculate implied probabilities
            home_prob = 1 / best_home_odds
            away_prob = 1 / best_away_odds
            total_prob = home_prob + away_prob
            
            # Check for arbitrage (total probability < 1)
            if total_prob < 1:
                profit_margin = (1 - total_prob) * 100
                
                return {
                    'profit_margin': profit_margin,
                    'home_bet': {
                        'team': match['home_team'],
                        'odds': best_home_odds,
                        'bookmaker': best_home_bookmaker,
                        'stake_percentage': home_prob / total_prob * 100
                    },
                    'away_bet': {
                        'team': match['away_team'],
                        'odds': best_away_odds,
                        'bookmaker': best_away_bookmaker,
                        'stake_percentage': away_prob / total_prob * 100
                    }
                }
        
        return None
