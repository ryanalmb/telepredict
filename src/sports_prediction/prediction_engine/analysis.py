"""Analysis modules for match and team analysis."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class MatchAnalyzer:
    """Analyzes individual matches for prediction insights."""
    
    def __init__(self, sport: str):
        self.sport = sport
        
        # Sport-specific analysis weights
        self.analysis_weights = self._get_sport_weights()
    
    def _get_sport_weights(self) -> Dict[str, float]:
        """Get sport-specific analysis weights."""
        if self.sport in ['mls', 'premier_league', 'la_liga', 'bundesliga', 'serie_a', 'champions_league']:
            return {
                'recent_form': 0.25,
                'head_to_head': 0.20,
                'home_advantage': 0.15,
                'team_strength': 0.20,
                'injuries': 0.10,
                'motivation': 0.10
            }
        elif self.sport in ['nba', 'nhl']:
            return {
                'recent_form': 0.30,
                'head_to_head': 0.15,
                'home_advantage': 0.10,
                'team_strength': 0.25,
                'injuries': 0.15,
                'motivation': 0.05
            }
        elif self.sport in ['nfl', 'mlb']:
            return {
                'recent_form': 0.20,
                'head_to_head': 0.25,
                'home_advantage': 0.15,
                'team_strength': 0.25,
                'injuries': 0.10,
                'motivation': 0.05
            }
        else:
            # Default weights
            return {
                'recent_form': 0.25,
                'head_to_head': 0.20,
                'home_advantage': 0.15,
                'team_strength': 0.20,
                'injuries': 0.10,
                'motivation': 0.10
            }
    
    async def analyze_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive match analysis."""
        logger.info("Performing match analysis")
        
        analysis = {
            'recent_form': self._analyze_recent_form(match_data),
            'head_to_head': self._analyze_head_to_head(match_data),
            'home_advantage': self._analyze_home_advantage(match_data),
            'team_strength': self._analyze_team_strength(match_data),
            'injuries': self._analyze_injuries(match_data),
            'motivation': self._analyze_motivation(match_data),
            'key_insights': [],
            'confidence': 0.0
        }
        
        # Generate key insights
        analysis['key_insights'] = self._generate_insights(analysis)
        
        # Calculate overall confidence
        analysis['confidence'] = self._calculate_analysis_confidence(analysis)
        
        return analysis
    
    def _analyze_recent_form(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze recent form of both teams."""
        home_team = match_data.get('home_team', {})
        away_team = match_data.get('away_team', {})
        
        home_form = self._calculate_team_form(home_team)
        away_form = self._calculate_team_form(away_team)
        
        form_difference = home_form['points_per_game'] - away_form['points_per_game']
        
        return {
            'home_form': home_form,
            'away_form': away_form,
            'form_difference': form_difference,
            'advantage': 'home' if form_difference > 0.5 else ('away' if form_difference < -0.5 else 'neutral')
        }
    
    def _calculate_team_form(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate team form metrics."""
        recent_matches = []
        
        # Collect recent matches from all sources
        for source, matches in team_data.get('recent_matches', {}).items():
            if isinstance(matches, list):
                recent_matches.extend(matches)
        
        if not recent_matches:
            return {
                'points_per_game': 1.0,  # Neutral
                'goals_per_game': 1.0,
                'goals_against_per_game': 1.0,
                'win_rate': 0.33,
                'matches_analyzed': 0
            }
        
        # Sort by date and take last 5 matches
        recent_matches = sorted(recent_matches, key=lambda x: x.get('date', ''), reverse=True)[:5]
        
        wins = 0
        total_goals = 0
        total_goals_against = 0
        
        for match in recent_matches:
            # Determine if this team won
            result = self._determine_match_result(match, team_data)
            if result == 'win':
                wins += 1
            
            # Extract goals
            goals_for, goals_against = self._extract_match_goals(match, team_data)
            total_goals += goals_for
            total_goals_against += goals_against
        
        num_matches = len(recent_matches)
        
        return {
            'points_per_game': (wins * 3 + (num_matches - wins) * 1) / num_matches if num_matches > 0 else 1.0,
            'goals_per_game': total_goals / num_matches if num_matches > 0 else 1.0,
            'goals_against_per_game': total_goals_against / num_matches if num_matches > 0 else 1.0,
            'win_rate': wins / num_matches if num_matches > 0 else 0.33,
            'matches_analyzed': num_matches
        }
    
    def _analyze_head_to_head(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze head-to-head record."""
        h2h_data = match_data.get('head_to_head', {})
        
        all_h2h_matches = []
        for source, matches in h2h_data.items():
            if isinstance(matches, list):
                all_h2h_matches.extend(matches)
        
        if not all_h2h_matches:
            return {
                'total_matches': 0,
                'home_wins': 0,
                'away_wins': 0,
                'draws': 0,
                'advantage': 'neutral'
            }
        
        home_wins = 0
        away_wins = 0
        draws = 0
        
        for match in all_h2h_matches:
            result = self._determine_h2h_result(match)
            if result == 'home':
                home_wins += 1
            elif result == 'away':
                away_wins += 1
            else:
                draws += 1
        
        total = len(all_h2h_matches)
        
        # Determine advantage
        if home_wins > away_wins + 2:
            advantage = 'home'
        elif away_wins > home_wins + 2:
            advantage = 'away'
        else:
            advantage = 'neutral'
        
        return {
            'total_matches': total,
            'home_wins': home_wins,
            'away_wins': away_wins,
            'draws': draws,
            'home_win_rate': home_wins / total if total > 0 else 0.33,
            'away_win_rate': away_wins / total if total > 0 else 0.33,
            'advantage': advantage
        }
    
    def _analyze_home_advantage(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze home advantage factor."""
        home_team = match_data.get('home_team', {})
        
        # Calculate home record
        home_record = self._calculate_home_record(home_team)
        
        # Sport-specific home advantage
        sport_home_advantage = self._get_sport_home_advantage()
        
        # Venue factors (simplified)
        venue_factor = 1.0  # Could be enhanced with venue-specific data
        
        total_advantage = (home_record['win_rate'] * 0.6 + 
                          sport_home_advantage * 0.3 + 
                          venue_factor * 0.1)
        
        return {
            'home_record': home_record,
            'sport_advantage': sport_home_advantage,
            'venue_factor': venue_factor,
            'total_advantage': total_advantage,
            'strength': 'strong' if total_advantage > 0.6 else ('moderate' if total_advantage > 0.4 else 'weak')
        }
    
    def _get_sport_home_advantage(self) -> float:
        """Get typical home advantage for the sport."""
        home_advantages = {
            'mls': 0.55,
            'premier_league': 0.52,
            'la_liga': 0.54,
            'bundesliga': 0.53,
            'serie_a': 0.52,
            'nba': 0.58,
            'nfl': 0.57,
            'nhl': 0.55,
            'mlb': 0.54
        }
        return home_advantages.get(self.sport, 0.53)
    
    def _calculate_home_record(self, home_team: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate home team's home record."""
        # This is simplified - in practice, you'd filter for home matches only
        recent_matches = []
        for source, matches in home_team.get('recent_matches', {}).items():
            if isinstance(matches, list):
                recent_matches.extend(matches)
        
        # For simplicity, assume all recent matches include some home games
        home_matches = recent_matches[:3]  # Simplified
        
        if not home_matches:
            return {'wins': 0, 'total': 0, 'win_rate': 0.5}
        
        wins = sum(1 for match in home_matches if self._determine_match_result(match, home_team) == 'win')
        
        return {
            'wins': wins,
            'total': len(home_matches),
            'win_rate': wins / len(home_matches) if home_matches else 0.5
        }
    
    def _analyze_team_strength(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze relative team strength."""
        home_team = match_data.get('home_team', {})
        away_team = match_data.get('away_team', {})
        
        home_strength = self._calculate_team_strength(home_team)
        away_strength = self._calculate_team_strength(away_team)
        
        strength_difference = home_strength - away_strength
        
        return {
            'home_strength': home_strength,
            'away_strength': away_strength,
            'difference': strength_difference,
            'advantage': 'home' if strength_difference > 0.1 else ('away' if strength_difference < -0.1 else 'neutral')
        }
    
    def _calculate_team_strength(self, team_data: Dict[str, Any]) -> float:
        """Calculate overall team strength score."""
        # Combine various strength indicators
        strength_factors = []
        
        # Team statistics
        for source, stats in team_data.get('team_stats', {}).items():
            if isinstance(stats, dict) and 'statistics' in stats:
                # Extract key performance indicators
                team_stats = stats['statistics']
                
                # Sport-specific strength calculation
                if self.sport in ['mls', 'premier_league', 'la_liga', 'bundesliga', 'serie_a']:
                    strength = self._calculate_soccer_strength(team_stats)
                elif self.sport == 'nba':
                    strength = self._calculate_basketball_strength(team_stats)
                elif self.sport == 'nfl':
                    strength = self._calculate_football_strength(team_stats)
                else:
                    strength = 0.5  # Default neutral strength
                
                strength_factors.append(strength)
        
        # Recent form
        form_data = self._calculate_team_form(team_data)
        strength_factors.append(form_data['win_rate'])
        
        # Return average strength
        return np.mean(strength_factors) if strength_factors else 0.5
    
    def _calculate_soccer_strength(self, stats: Dict[str, Any]) -> float:
        """Calculate soccer team strength."""
        # Simplified calculation based on common soccer metrics
        factors = []
        
        if 'goals_for' in stats and 'goals_against' in stats:
            goal_difference = stats['goals_for'] - stats['goals_against']
            factors.append(min(max(goal_difference / 20 + 0.5, 0), 1))
        
        if 'points_per_game' in stats:
            factors.append(min(stats['points_per_game'] / 3, 1))
        
        return np.mean(factors) if factors else 0.5
    
    def _calculate_basketball_strength(self, stats: Dict[str, Any]) -> float:
        """Calculate basketball team strength."""
        factors = []
        
        if 'points_per_game' in stats:
            factors.append(min(stats['points_per_game'] / 120, 1))
        
        if 'field_goal_percentage' in stats:
            factors.append(stats['field_goal_percentage'])
        
        return np.mean(factors) if factors else 0.5
    
    def _calculate_football_strength(self, stats: Dict[str, Any]) -> float:
        """Calculate American football team strength."""
        factors = []
        
        if 'points_per_game' in stats:
            factors.append(min(stats['points_per_game'] / 35, 1))
        
        if 'yards_per_game' in stats:
            factors.append(min(stats['yards_per_game'] / 400, 1))
        
        return np.mean(factors) if factors else 0.5
    
    def _analyze_injuries(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze injury impact (simplified)."""
        # This would require injury data from sports APIs
        # For now, return neutral impact
        return {
            'home_injury_impact': 0.0,
            'away_injury_impact': 0.0,
            'net_impact': 0.0,
            'severity': 'minimal'
        }
    
    def _analyze_motivation(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze motivation factors (simplified)."""
        # This would consider factors like league position, cup competitions, etc.
        # For now, return neutral motivation
        return {
            'home_motivation': 0.5,
            'away_motivation': 0.5,
            'factors': ['Regular season match'],
            'impact': 'neutral'
        }
    
    def _generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate key insights from analysis."""
        insights = []
        
        # Form insights
        form_data = analysis['recent_form']
        if form_data['advantage'] == 'home':
            insights.append(f"Home team has superior recent form (difference: {form_data['form_difference']:.2f})")
        elif form_data['advantage'] == 'away':
            insights.append(f"Away team has superior recent form (difference: {abs(form_data['form_difference']):.2f})")
        
        # H2H insights
        h2h_data = analysis['head_to_head']
        if h2h_data['total_matches'] > 0:
            if h2h_data['advantage'] == 'home':
                insights.append(f"Home team dominates H2H record ({h2h_data['home_wins']}-{h2h_data['away_wins']}-{h2h_data['draws']})")
            elif h2h_data['advantage'] == 'away':
                insights.append(f"Away team has H2H advantage ({h2h_data['away_wins']}-{h2h_data['home_wins']}-{h2h_data['draws']})")
        
        # Home advantage insights
        home_adv = analysis['home_advantage']
        if home_adv['strength'] == 'strong':
            insights.append(f"Strong home advantage factor ({home_adv['total_advantage']:.2f})")
        
        # Team strength insights
        strength_data = analysis['team_strength']
        if strength_data['advantage'] == 'home':
            insights.append(f"Home team has superior overall strength")
        elif strength_data['advantage'] == 'away':
            insights.append(f"Away team has superior overall strength")
        
        return insights[:5]  # Return top 5 insights
    
    def _calculate_analysis_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence in the analysis."""
        confidence_factors = []
        
        # Data availability
        h2h_matches = analysis['head_to_head']['total_matches']
        if h2h_matches >= 5:
            confidence_factors.append(0.8)
        elif h2h_matches >= 2:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)
        
        # Form data quality
        home_form_matches = analysis['recent_form']['home_form']['matches_analyzed']
        away_form_matches = analysis['recent_form']['away_form']['matches_analyzed']
        
        if home_form_matches >= 5 and away_form_matches >= 5:
            confidence_factors.append(0.8)
        elif home_form_matches >= 3 and away_form_matches >= 3:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)
        
        # Analysis consistency
        advantages = [
            analysis['recent_form']['advantage'],
            analysis['head_to_head']['advantage'],
            analysis['team_strength']['advantage']
        ]
        
        if advantages.count(advantages[0]) >= 2:  # At least 2 agree
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        return np.mean(confidence_factors)
    
    def _determine_match_result(self, match: Dict[str, Any], team_data: Dict[str, Any]) -> str:
        """Determine match result for a team."""
        # Simplified implementation
        home_score = match.get('home_team', {}).get('score', 0)
        away_score = match.get('away_team', {}).get('score', 0)
        
        if home_score is None or away_score is None:
            return 'unknown'
        
        try:
            home_score = float(home_score)
            away_score = float(away_score)
            
            # Determine if this team was home or away (simplified)
            if home_score > away_score:
                return 'win'  # Assume team was home
            elif home_score == away_score:
                return 'draw'
            else:
                return 'loss'
        except (ValueError, TypeError):
            return 'unknown'
    
    def _extract_match_goals(self, match: Dict[str, Any], team_data: Dict[str, Any]) -> Tuple[int, int]:
        """Extract goals for and against for a team."""
        # Simplified implementation
        home_score = match.get('home_team', {}).get('score', 0)
        away_score = match.get('away_team', {}).get('score', 0)
        
        try:
            home_score = int(float(home_score))
            away_score = int(float(away_score))
            
            # Assume team was home (simplified)
            return home_score, away_score
        except (ValueError, TypeError):
            return 0, 0
    
    def _determine_h2h_result(self, match: Dict[str, Any]) -> str:
        """Determine head-to-head match result."""
        home_score = match.get('home_team', {}).get('score')
        away_score = match.get('away_team', {}).get('score')
        
        if home_score is None or away_score is None:
            return 'unknown'
        
        try:
            home_score = float(home_score)
            away_score = float(away_score)
            
            if home_score > away_score:
                return 'home'
            elif away_score > home_score:
                return 'away'
            else:
                return 'draw'
        except (ValueError, TypeError):
            return 'unknown'


class TeamAnalyzer:
    """Analyzes individual teams for comprehensive insights."""
    
    def __init__(self, sport: str):
        self.sport = sport
    
    async def analyze_team(self, team_id: str) -> Dict[str, Any]:
        """Perform comprehensive team analysis."""
        # This would be implemented with actual team data
        # For now, return a simplified analysis structure
        
        return {
            'team_id': team_id,
            'overall_rating': 0.7,
            'strengths': ['Strong attack', 'Good home record'],
            'weaknesses': ['Defensive vulnerabilities', 'Poor away form'],
            'key_players': [],
            'recent_form': {'trend': 'improving', 'points_per_game': 1.8},
            'confidence': 0.6
        }
    
    def compare_teams(self, home_analysis: Dict[str, Any], away_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two teams."""
        home_rating = home_analysis.get('overall_rating', 0.5)
        away_rating = away_analysis.get('overall_rating', 0.5)
        
        return {
            'home_advantage': max(0, home_rating - away_rating + 0.1),  # Add home boost
            'away_advantage': max(0, away_rating - home_rating),
            'rating_difference': home_rating - away_rating,
            'predicted_outcome': 'home' if home_rating > away_rating else 'away'
        }
