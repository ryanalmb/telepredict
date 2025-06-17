"""Odds analysis for betting value identification."""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OddsAnalyzer:
    """Analyzes betting odds for value identification."""
    
    def __init__(self, sport: str):
        self.sport = sport
        self.min_value_threshold = 0.05  # 5% minimum edge
        self.confidence_threshold = 0.6
    
    async def analyze_match_odds(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze odds for a specific match."""
        logger.info("Analyzing match odds")
        
        odds_data = match_data.get('odds')
        if not odds_data or 'bookmakers' not in odds_data:
            return {
                'odds_available': False,
                'value_bets': [],
                'arbitrage_opportunities': [],
                'confidence': 0.0,
                'recommendation': 'No odds data available'
            }
        
        # Extract odds from bookmakers
        odds_summary = self._extract_odds_summary(odds_data)
        
        # Calculate implied probabilities
        implied_probabilities = self._calculate_implied_probabilities(odds_summary)
        
        # Identify value bets (requires model predictions)
        value_bets = self._identify_value_bets(odds_summary, implied_probabilities)
        
        # Check for arbitrage opportunities
        arbitrage_opportunities = self._find_arbitrage_opportunities(odds_summary)
        
        # Calculate market efficiency
        market_efficiency = self._calculate_market_efficiency(implied_probabilities)
        
        # Generate recommendations
        recommendations = self._generate_betting_recommendations(
            value_bets, arbitrage_opportunities, market_efficiency
        )
        
        return {
            'odds_available': True,
            'odds_summary': odds_summary,
            'implied_probabilities': implied_probabilities,
            'value_bets': value_bets,
            'arbitrage_opportunities': arbitrage_opportunities,
            'market_efficiency': market_efficiency,
            'recommendations': recommendations,
            'confidence': self._calculate_odds_confidence(odds_summary)
        }
    
    def _extract_odds_summary(self, odds_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and summarize odds from all bookmakers."""
        odds_summary = {
            'h2h': {'home': [], 'away': [], 'draw': []},
            'spreads': {'home': [], 'away': []},
            'totals': {'over': [], 'under': []},
            'bookmakers': []
        }
        
        for bookmaker in odds_data.get('bookmakers', []):
            bookmaker_name = bookmaker.get('title', 'Unknown')
            odds_summary['bookmakers'].append(bookmaker_name)
            
            for market in bookmaker.get('markets', []):
                market_key = market.get('key')
                
                if market_key == 'h2h':
                    for outcome in market.get('outcomes', []):
                        outcome_name = outcome.get('name', '').lower()
                        odds_value = outcome.get('price', 0)
                        
                        if 'home' in outcome_name or outcome_name == odds_data.get('home_team', '').lower():
                            odds_summary['h2h']['home'].append({
                                'odds': odds_value,
                                'bookmaker': bookmaker_name
                            })
                        elif 'away' in outcome_name or outcome_name == odds_data.get('away_team', '').lower():
                            odds_summary['h2h']['away'].append({
                                'odds': odds_value,
                                'bookmaker': bookmaker_name
                            })
                        elif 'draw' in outcome_name or 'tie' in outcome_name:
                            odds_summary['h2h']['draw'].append({
                                'odds': odds_value,
                                'bookmaker': bookmaker_name
                            })
                
                elif market_key == 'spreads':
                    for outcome in market.get('outcomes', []):
                        outcome_name = outcome.get('name', '').lower()
                        odds_value = outcome.get('price', 0)
                        point_spread = outcome.get('point', 0)
                        
                        if 'home' in outcome_name:
                            odds_summary['spreads']['home'].append({
                                'odds': odds_value,
                                'spread': point_spread,
                                'bookmaker': bookmaker_name
                            })
                        elif 'away' in outcome_name:
                            odds_summary['spreads']['away'].append({
                                'odds': odds_value,
                                'spread': point_spread,
                                'bookmaker': bookmaker_name
                            })
                
                elif market_key == 'totals':
                    for outcome in market.get('outcomes', []):
                        outcome_name = outcome.get('name', '').lower()
                        odds_value = outcome.get('price', 0)
                        total_points = outcome.get('point', 0)
                        
                        if 'over' in outcome_name:
                            odds_summary['totals']['over'].append({
                                'odds': odds_value,
                                'total': total_points,
                                'bookmaker': bookmaker_name
                            })
                        elif 'under' in outcome_name:
                            odds_summary['totals']['under'].append({
                                'odds': odds_value,
                                'total': total_points,
                                'bookmaker': bookmaker_name
                            })
        
        return odds_summary
    
    def _calculate_implied_probabilities(self, odds_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate implied probabilities from odds."""
        implied_probs = {}
        
        # H2H probabilities
        h2h_odds = odds_summary.get('h2h', {})
        if h2h_odds:
            home_odds = [item['odds'] for item in h2h_odds.get('home', [])]
            away_odds = [item['odds'] for item in h2h_odds.get('away', [])]
            draw_odds = [item['odds'] for item in h2h_odds.get('draw', [])]
            
            implied_probs['h2h'] = {
                'home': np.mean([1/odds for odds in home_odds]) if home_odds else 0,
                'away': np.mean([1/odds for odds in away_odds]) if away_odds else 0,
                'draw': np.mean([1/odds for odds in draw_odds]) if draw_odds else 0
            }
            
            # Normalize probabilities
            total_prob = sum(implied_probs['h2h'].values())
            if total_prob > 0:
                for outcome in implied_probs['h2h']:
                    implied_probs['h2h'][outcome] /= total_prob
        
        # Spreads probabilities
        spreads_odds = odds_summary.get('spreads', {})
        if spreads_odds:
            home_spread_odds = [item['odds'] for item in spreads_odds.get('home', [])]
            away_spread_odds = [item['odds'] for item in spreads_odds.get('away', [])]
            
            implied_probs['spreads'] = {
                'home': np.mean([1/odds for odds in home_spread_odds]) if home_spread_odds else 0,
                'away': np.mean([1/odds for odds in away_spread_odds]) if away_spread_odds else 0
            }
        
        # Totals probabilities
        totals_odds = odds_summary.get('totals', {})
        if totals_odds:
            over_odds = [item['odds'] for item in totals_odds.get('over', [])]
            under_odds = [item['odds'] for item in totals_odds.get('under', [])]
            
            implied_probs['totals'] = {
                'over': np.mean([1/odds for odds in over_odds]) if over_odds else 0,
                'under': np.mean([1/odds for odds in under_odds]) if under_odds else 0
            }
        
        return implied_probs
    
    def _identify_value_bets(self, odds_summary: Dict[str, Any], 
                           implied_probabilities: Dict[str, Any],
                           model_probabilities: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Identify value betting opportunities."""
        value_bets = []
        
        # For demonstration, use simplified model probabilities
        # In practice, these would come from your ML models
        if model_probabilities is None:
            model_probabilities = {
                'home': 0.45,
                'draw': 0.25,
                'away': 0.30
            }
        
        # Check H2H value bets
        h2h_odds = odds_summary.get('h2h', {})
        h2h_implied = implied_probabilities.get('h2h', {})
        
        for outcome in ['home', 'away', 'draw']:
            if outcome in model_probabilities and outcome in h2h_implied:
                model_prob = model_probabilities[outcome]
                market_prob = h2h_implied[outcome]
                
                if model_prob > market_prob:
                    # Find best odds for this outcome
                    outcome_odds = h2h_odds.get(outcome, [])
                    if outcome_odds:
                        best_odds_info = max(outcome_odds, key=lambda x: x['odds'])
                        best_odds = best_odds_info['odds']
                        
                        # Calculate expected value
                        expected_value = (model_prob * best_odds) - 1
                        
                        if expected_value > self.min_value_threshold:
                            value_bets.append({
                                'market': 'h2h',
                                'outcome': outcome,
                                'model_probability': model_prob,
                                'market_probability': market_prob,
                                'best_odds': best_odds,
                                'bookmaker': best_odds_info['bookmaker'],
                                'expected_value': expected_value,
                                'value_percentage': expected_value * 100,
                                'recommended_stake': self._calculate_kelly_stake(model_prob, best_odds)
                            })
        
        return sorted(value_bets, key=lambda x: x['expected_value'], reverse=True)
    
    def _find_arbitrage_opportunities(self, odds_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find arbitrage betting opportunities."""
        arbitrage_opportunities = []
        
        # Check H2H arbitrage
        h2h_odds = odds_summary.get('h2h', {})
        
        if all(outcome in h2h_odds and h2h_odds[outcome] for outcome in ['home', 'away', 'draw']):
            # Find best odds for each outcome
            best_home = max(h2h_odds['home'], key=lambda x: x['odds'])
            best_away = max(h2h_odds['away'], key=lambda x: x['odds'])
            best_draw = max(h2h_odds['draw'], key=lambda x: x['odds'])
            
            # Calculate arbitrage
            total_inverse = (1/best_home['odds']) + (1/best_away['odds']) + (1/best_draw['odds'])
            
            if total_inverse < 1:  # Arbitrage opportunity exists
                profit_margin = (1 - total_inverse) * 100
                
                arbitrage_opportunities.append({
                    'market': 'h2h',
                    'profit_margin': profit_margin,
                    'bets': [
                        {
                            'outcome': 'home',
                            'odds': best_home['odds'],
                            'bookmaker': best_home['bookmaker'],
                            'stake_percentage': (1/best_home['odds']) / total_inverse * 100
                        },
                        {
                            'outcome': 'away',
                            'odds': best_away['odds'],
                            'bookmaker': best_away['bookmaker'],
                            'stake_percentage': (1/best_away['odds']) / total_inverse * 100
                        },
                        {
                            'outcome': 'draw',
                            'odds': best_draw['odds'],
                            'bookmaker': best_draw['bookmaker'],
                            'stake_percentage': (1/best_draw['odds']) / total_inverse * 100
                        }
                    ]
                })
        
        # Check spreads arbitrage (simplified for two outcomes)
        spreads_odds = odds_summary.get('spreads', {})
        if spreads_odds.get('home') and spreads_odds.get('away'):
            best_home_spread = max(spreads_odds['home'], key=lambda x: x['odds'])
            best_away_spread = max(spreads_odds['away'], key=lambda x: x['odds'])
            
            total_inverse = (1/best_home_spread['odds']) + (1/best_away_spread['odds'])
            
            if total_inverse < 1:
                profit_margin = (1 - total_inverse) * 100
                
                arbitrage_opportunities.append({
                    'market': 'spreads',
                    'profit_margin': profit_margin,
                    'bets': [
                        {
                            'outcome': 'home_spread',
                            'odds': best_home_spread['odds'],
                            'spread': best_home_spread.get('spread', 0),
                            'bookmaker': best_home_spread['bookmaker'],
                            'stake_percentage': (1/best_home_spread['odds']) / total_inverse * 100
                        },
                        {
                            'outcome': 'away_spread',
                            'odds': best_away_spread['odds'],
                            'spread': best_away_spread.get('spread', 0),
                            'bookmaker': best_away_spread['bookmaker'],
                            'stake_percentage': (1/best_away_spread['odds']) / total_inverse * 100
                        }
                    ]
                })
        
        return sorted(arbitrage_opportunities, key=lambda x: x['profit_margin'], reverse=True)
    
    def _calculate_market_efficiency(self, implied_probabilities: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate market efficiency metrics."""
        efficiency_metrics = {}
        
        # H2H market efficiency
        h2h_probs = implied_probabilities.get('h2h', {})
        if h2h_probs:
            total_prob = sum(h2h_probs.values())
            overround = total_prob - 1.0
            efficiency = 1.0 / total_prob if total_prob > 0 else 0
            
            efficiency_metrics['h2h'] = {
                'total_probability': total_prob,
                'overround': overround,
                'efficiency': efficiency,
                'margin_percentage': overround * 100
            }
        
        # Spreads market efficiency
        spreads_probs = implied_probabilities.get('spreads', {})
        if spreads_probs:
            total_prob = sum(spreads_probs.values())
            overround = total_prob - 1.0
            efficiency = 1.0 / total_prob if total_prob > 0 else 0
            
            efficiency_metrics['spreads'] = {
                'total_probability': total_prob,
                'overround': overround,
                'efficiency': efficiency,
                'margin_percentage': overround * 100
            }
        
        return efficiency_metrics
    
    def _generate_betting_recommendations(self, value_bets: List[Dict[str, Any]],
                                        arbitrage_opportunities: List[Dict[str, Any]],
                                        market_efficiency: Dict[str, Any]) -> List[str]:
        """Generate betting recommendations."""
        recommendations = []
        
        # Arbitrage recommendations
        if arbitrage_opportunities:
            best_arbitrage = arbitrage_opportunities[0]
            recommendations.append(
                f"Arbitrage opportunity available with {best_arbitrage['profit_margin']:.2f}% guaranteed profit"
            )
        
        # Value bet recommendations
        if value_bets:
            best_value = value_bets[0]
            if best_value['expected_value'] > 0.1:  # 10% edge
                recommendations.append(
                    f"Strong value bet: {best_value['outcome']} at {best_value['best_odds']} "
                    f"({best_value['value_percentage']:.1f}% edge)"
                )
            elif best_value['expected_value'] > 0.05:  # 5% edge
                recommendations.append(
                    f"Moderate value bet: {best_value['outcome']} at {best_value['best_odds']} "
                    f"({best_value['value_percentage']:.1f}% edge)"
                )
        
        # Market efficiency insights
        h2h_efficiency = market_efficiency.get('h2h', {})
        if h2h_efficiency:
            margin = h2h_efficiency.get('margin_percentage', 0)
            if margin > 10:
                recommendations.append(f"High bookmaker margin ({margin:.1f}%) - consider avoiding")
            elif margin < 5:
                recommendations.append(f"Competitive market with low margin ({margin:.1f}%)")
        
        if not recommendations:
            recommendations.append("No significant betting opportunities identified")
        
        return recommendations
    
    def _calculate_kelly_stake(self, probability: float, odds: float) -> float:
        """Calculate Kelly criterion stake percentage."""
        if odds <= 1 or probability <= 0:
            return 0
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = probability, q = 1 - p
        b = odds - 1
        p = probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Cap at 25% for safety
        return max(0, min(kelly_fraction, 0.25))
    
    def _calculate_odds_confidence(self, odds_summary: Dict[str, Any]) -> float:
        """Calculate confidence in odds analysis."""
        confidence_factors = []
        
        # Number of bookmakers
        num_bookmakers = len(odds_summary.get('bookmakers', []))
        if num_bookmakers >= 5:
            confidence_factors.append(0.9)
        elif num_bookmakers >= 3:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Market coverage
        markets_available = sum(1 for market in ['h2h', 'spreads', 'totals'] 
                              if odds_summary.get(market) and any(odds_summary[market].values()))
        
        if markets_available >= 2:
            confidence_factors.append(0.8)
        elif markets_available >= 1:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)
        
        # Odds consistency (simplified)
        h2h_odds = odds_summary.get('h2h', {})
        if h2h_odds.get('home'):
            home_odds_values = [item['odds'] for item in h2h_odds['home']]
            if len(home_odds_values) > 1:
                odds_std = np.std(home_odds_values)
                if odds_std < 0.1:  # Low variance = high confidence
                    confidence_factors.append(0.8)
                elif odds_std < 0.2:
                    confidence_factors.append(0.6)
                else:
                    confidence_factors.append(0.4)
        
        return np.mean(confidence_factors) if confidence_factors else 0.5
