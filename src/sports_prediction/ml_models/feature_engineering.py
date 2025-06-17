"""Feature engineering for sports prediction models."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FeatureEngineer:
    """Feature engineering for sports data."""
    
    def __init__(self, sport: str):
        self.sport = sport
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        self.feature_names = []
        
    def engineer_features(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Engineer features from raw sports data."""
        logger.info(f"Engineering features for {self.sport}")
        
        features = []
        
        # Team-based features
        if 'home_team' in data and 'away_team' in data:
            home_features = self._extract_team_features(data['home_team'], 'home')
            away_features = self._extract_team_features(data['away_team'], 'away')
            features.extend([home_features, away_features])
        
        # Head-to-head features
        if 'head_to_head' in data:
            h2h_features = self._extract_h2h_features(data['head_to_head'])
            features.append(h2h_features)
        
        # Odds features
        if 'odds' in data and data['odds']:
            odds_features = self._extract_odds_features(data['odds'])
            features.append(odds_features)
        
        # Combine all features
        if features:
            combined_features = pd.concat(features, axis=1)
        else:
            combined_features = pd.DataFrame()
        
        # Sport-specific features
        sport_features = self._extract_sport_specific_features(data)
        if not sport_features.empty:
            combined_features = pd.concat([combined_features, sport_features], axis=1)
        
        # Time-based features
        time_features = self._extract_time_features(data)
        if not time_features.empty:
            combined_features = pd.concat([combined_features, time_features], axis=1)
        
        # Clean and process features
        processed_features = self._process_features(combined_features)
        
        logger.info(f"Generated {len(processed_features.columns)} features")
        return processed_features
    
    def _extract_team_features(self, team_data: Dict[str, Any], prefix: str) -> pd.DataFrame:
        """Extract features from team data."""
        features = {}
        
        # Basic team stats
        for source, stats in team_data.get('team_stats', {}).items():
            if isinstance(stats, dict) and 'statistics' in stats:
                for stat_name, stat_value in stats['statistics'].items():
                    if isinstance(stat_value, (int, float)):
                        features[f"{prefix}_{source}_{stat_name}"] = stat_value
        
        # Recent form features
        recent_matches = []
        for source, matches in team_data.get('recent_matches', {}).items():
            if isinstance(matches, list):
                recent_matches.extend(matches)
        
        if recent_matches:
            form_features = self._calculate_form_features(recent_matches, prefix)
            features.update(form_features)
        
        # Convert to DataFrame
        if features:
            return pd.DataFrame([features])
        else:
            return pd.DataFrame()
    
    def _extract_h2h_features(self, h2h_data: Dict[str, Any]) -> pd.DataFrame:
        """Extract head-to-head features."""
        features = {}
        
        all_matches = []
        for source, matches in h2h_data.items():
            if isinstance(matches, list):
                all_matches.extend(matches)
        
        if all_matches:
            # H2H record
            home_wins = sum(1 for match in all_matches 
                          if self._determine_winner(match) == 'home')
            away_wins = sum(1 for match in all_matches 
                          if self._determine_winner(match) == 'away')
            draws = sum(1 for match in all_matches 
                       if self._determine_winner(match) == 'draw')
            
            total_matches = len(all_matches)
            if total_matches > 0:
                features['h2h_home_win_rate'] = home_wins / total_matches
                features['h2h_away_win_rate'] = away_wins / total_matches
                features['h2h_draw_rate'] = draws / total_matches
                features['h2h_total_matches'] = total_matches
            
            # Average goals/points
            home_scores = [self._extract_score(match, 'home') for match in all_matches]
            away_scores = [self._extract_score(match, 'away') for match in all_matches]
            
            home_scores = [s for s in home_scores if s is not None]
            away_scores = [s for s in away_scores if s is not None]
            
            if home_scores:
                features['h2h_avg_home_score'] = np.mean(home_scores)
                features['h2h_avg_away_score'] = np.mean(away_scores)
                features['h2h_avg_total_score'] = np.mean([h + a for h, a in zip(home_scores, away_scores)])
        
        if features:
            return pd.DataFrame([features])
        else:
            return pd.DataFrame()
    
    def _extract_odds_features(self, odds_data: Dict[str, Any]) -> pd.DataFrame:
        """Extract features from betting odds."""
        features = {}
        
        if 'bookmakers' in odds_data:
            # Extract odds for different markets
            for bookmaker in odds_data['bookmakers']:
                for market in bookmaker.get('markets', []):
                    market_key = market['key']
                    
                    for outcome in market.get('outcomes', []):
                        outcome_name = outcome['name']
                        odds_value = outcome['price']
                        
                        # Use first bookmaker's odds as baseline
                        feature_name = f"odds_{market_key}_{outcome_name}".replace(' ', '_').lower()
                        if feature_name not in features:
                            features[feature_name] = odds_value
                            
                            # Convert to implied probability
                            prob_feature_name = f"prob_{market_key}_{outcome_name}".replace(' ', '_').lower()
                            features[prob_feature_name] = 1 / odds_value if odds_value > 0 else 0
        
        if features:
            return pd.DataFrame([features])
        else:
            return pd.DataFrame()
    
    def _extract_sport_specific_features(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Extract sport-specific features."""
        if self.sport in ['mls', 'premier_league', 'la_liga', 'bundesliga', 'serie_a', 'champions_league']:
            return self._extract_soccer_features(data)
        elif self.sport == 'nba':
            return self._extract_basketball_features(data)
        elif self.sport == 'nfl':
            return self._extract_football_features(data)
        elif self.sport == 'nhl':
            return self._extract_hockey_features(data)
        elif self.sport == 'mlb':
            return self._extract_baseball_features(data)
        else:
            return pd.DataFrame()
    
    def _extract_soccer_features(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Extract soccer-specific features."""
        features = {}
        
        # Extract possession, shots, corners, etc. from team stats
        for team_type in ['home_team', 'away_team']:
            if team_type in data:
                team_data = data[team_type]
                prefix = team_type.split('_')[0]
                
                # Look for soccer-specific stats
                for source, stats in team_data.get('team_stats', {}).items():
                    if isinstance(stats, dict) and 'statistics' in stats:
                        soccer_stats = stats['statistics']
                        
                        # Common soccer statistics
                        soccer_features = [
                            'goals_for', 'goals_against', 'shots_per_game',
                            'shots_on_target', 'possession', 'pass_accuracy',
                            'corners_per_game', 'fouls_per_game', 'cards_per_game'
                        ]
                        
                        for stat in soccer_features:
                            if stat in soccer_stats:
                                features[f"{prefix}_{stat}"] = soccer_stats[stat]
        
        if features:
            return pd.DataFrame([features])
        else:
            return pd.DataFrame()
    
    def _extract_basketball_features(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Extract basketball-specific features."""
        features = {}
        
        for team_type in ['home_team', 'away_team']:
            if team_type in data:
                team_data = data[team_type]
                prefix = team_type.split('_')[0]
                
                for source, stats in team_data.get('team_stats', {}).items():
                    if isinstance(stats, dict) and 'statistics' in stats:
                        basketball_stats = stats['statistics']
                        
                        # Common basketball statistics
                        basketball_features = [
                            'points_per_game', 'rebounds_per_game', 'assists_per_game',
                            'field_goal_percentage', 'three_point_percentage', 'free_throw_percentage',
                            'turnovers_per_game', 'steals_per_game', 'blocks_per_game'
                        ]
                        
                        for stat in basketball_features:
                            if stat in basketball_stats:
                                features[f"{prefix}_{stat}"] = basketball_stats[stat]
        
        if features:
            return pd.DataFrame([features])
        else:
            return pd.DataFrame()
    
    def _extract_football_features(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Extract American football-specific features."""
        features = {}
        
        for team_type in ['home_team', 'away_team']:
            if team_type in data:
                team_data = data[team_type]
                prefix = team_type.split('_')[0]
                
                for source, stats in team_data.get('team_stats', {}).items():
                    if isinstance(stats, dict) and 'statistics' in stats:
                        football_stats = stats['statistics']
                        
                        # Common football statistics
                        football_features = [
                            'points_per_game', 'yards_per_game', 'passing_yards_per_game',
                            'rushing_yards_per_game', 'turnovers_per_game', 'sacks_per_game',
                            'third_down_percentage', 'red_zone_percentage'
                        ]
                        
                        for stat in football_features:
                            if stat in football_stats:
                                features[f"{prefix}_{stat}"] = football_stats[stat]
        
        if features:
            return pd.DataFrame([features])
        else:
            return pd.DataFrame()
    
    def _extract_hockey_features(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Extract hockey-specific features."""
        features = {}
        
        for team_type in ['home_team', 'away_team']:
            if team_type in data:
                team_data = data[team_type]
                prefix = team_type.split('_')[0]
                
                for source, stats in team_data.get('team_stats', {}).items():
                    if isinstance(stats, dict) and 'statistics' in stats:
                        hockey_stats = stats['statistics']
                        
                        # Common hockey statistics
                        hockey_features = [
                            'goals_per_game', 'assists_per_game', 'shots_per_game',
                            'power_play_percentage', 'penalty_kill_percentage',
                            'face_off_percentage', 'hits_per_game', 'blocked_shots_per_game'
                        ]
                        
                        for stat in hockey_features:
                            if stat in hockey_stats:
                                features[f"{prefix}_{stat}"] = hockey_stats[stat]
        
        if features:
            return pd.DataFrame([features])
        else:
            return pd.DataFrame()
    
    def _extract_baseball_features(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Extract baseball-specific features."""
        features = {}
        
        for team_type in ['home_team', 'away_team']:
            if team_type in data:
                team_data = data[team_type]
                prefix = team_type.split('_')[0]
                
                for source, stats in team_data.get('team_stats', {}).items():
                    if isinstance(stats, dict) and 'statistics' in stats:
                        baseball_stats = stats['statistics']
                        
                        # Common baseball statistics
                        baseball_features = [
                            'batting_average', 'on_base_percentage', 'slugging_percentage',
                            'era', 'whip', 'strikeouts_per_nine', 'home_runs_per_game',
                            'runs_per_game', 'stolen_bases_per_game'
                        ]
                        
                        for stat in baseball_features:
                            if stat in baseball_stats:
                                features[f"{prefix}_{stat}"] = baseball_stats[stat]
        
        if features:
            return pd.DataFrame([features])
        else:
            return pd.DataFrame()
    
    def _extract_time_features(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Extract time-based features."""
        features = {}
        
        # Day of week, month, season features
        if 'date' in data or 'commence_time' in data:
            date_str = data.get('date') or data.get('commence_time')
            if date_str:
                try:
                    match_date = pd.to_datetime(date_str)
                    
                    features['day_of_week'] = match_date.dayofweek
                    features['month'] = match_date.month
                    features['hour'] = match_date.hour
                    features['is_weekend'] = 1 if match_date.dayofweek >= 5 else 0
                    
                    # Season features (assuming Northern Hemisphere seasons)
                    if match_date.month in [12, 1, 2]:
                        features['season'] = 0  # Winter
                    elif match_date.month in [3, 4, 5]:
                        features['season'] = 1  # Spring
                    elif match_date.month in [6, 7, 8]:
                        features['season'] = 2  # Summer
                    else:
                        features['season'] = 3  # Fall
                        
                except Exception as e:
                    logger.warning(f"Error parsing date {date_str}: {e}")
        
        if features:
            return pd.DataFrame([features])
        else:
            return pd.DataFrame()
    
    def _calculate_form_features(self, matches: List[Dict], prefix: str) -> Dict[str, float]:
        """Calculate team form features from recent matches."""
        features = {}
        
        if not matches:
            return features
        
        # Sort matches by date (most recent first)
        sorted_matches = sorted(matches, key=lambda x: x.get('date', ''), reverse=True)
        
        # Take last 5 matches
        recent_matches = sorted_matches[:5]
        
        wins = 0
        draws = 0
        losses = 0
        goals_for = 0
        goals_against = 0
        
        for match in recent_matches:
            result = self._determine_result_for_team(match, prefix)
            if result == 'win':
                wins += 1
            elif result == 'draw':
                draws += 1
            elif result == 'loss':
                losses += 1
            
            # Extract scores
            home_score = self._extract_score(match, 'home')
            away_score = self._extract_score(match, 'away')
            
            if home_score is not None and away_score is not None:
                if prefix == 'home':
                    goals_for += home_score
                    goals_against += away_score
                else:
                    goals_for += away_score
                    goals_against += home_score
        
        total_matches = len(recent_matches)
        if total_matches > 0:
            features[f'{prefix}_form_win_rate'] = wins / total_matches
            features[f'{prefix}_form_draw_rate'] = draws / total_matches
            features[f'{prefix}_form_loss_rate'] = losses / total_matches
            features[f'{prefix}_form_goals_per_game'] = goals_for / total_matches
            features[f'{prefix}_form_goals_against_per_game'] = goals_against / total_matches
            
            # Form points (3 for win, 1 for draw, 0 for loss)
            form_points = wins * 3 + draws * 1
            features[f'{prefix}_form_points'] = form_points
            features[f'{prefix}_form_points_per_game'] = form_points / total_matches
        
        return features
    
    def _determine_winner(self, match: Dict) -> str:
        """Determine the winner of a match."""
        home_score = self._extract_score(match, 'home')
        away_score = self._extract_score(match, 'away')
        
        if home_score is None or away_score is None:
            return 'unknown'
        
        if home_score > away_score:
            return 'home'
        elif away_score > home_score:
            return 'away'
        else:
            return 'draw'
    
    def _determine_result_for_team(self, match: Dict, team_prefix: str) -> str:
        """Determine the result for a specific team."""
        winner = self._determine_winner(match)
        
        if winner == 'unknown':
            return 'unknown'
        elif winner == 'draw':
            return 'draw'
        elif (winner == 'home' and team_prefix == 'home') or (winner == 'away' and team_prefix == 'away'):
            return 'win'
        else:
            return 'loss'
    
    def _extract_score(self, match: Dict, team_type: str) -> Optional[float]:
        """Extract score for home or away team."""
        try:
            team_key = f'{team_type}_team'
            if team_key in match and 'score' in match[team_key]:
                score = match[team_key]['score']
                return float(score) if score is not None else None
        except (ValueError, TypeError):
            pass
        return None
    
    def _process_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Process and clean features."""
        if features.empty:
            return features
        
        # Handle missing values
        numeric_columns = features.select_dtypes(include=[np.number]).columns
        categorical_columns = features.select_dtypes(include=['object']).columns
        
        # Impute numeric features
        if len(numeric_columns) > 0:
            if 'numeric' not in self.imputers:
                self.imputers['numeric'] = SimpleImputer(strategy='median')
                features[numeric_columns] = self.imputers['numeric'].fit_transform(features[numeric_columns])
            else:
                features[numeric_columns] = self.imputers['numeric'].transform(features[numeric_columns])
        
        # Impute categorical features
        if len(categorical_columns) > 0:
            if 'categorical' not in self.imputers:
                self.imputers['categorical'] = SimpleImputer(strategy='most_frequent')
                features[categorical_columns] = self.imputers['categorical'].fit_transform(features[categorical_columns])
            else:
                features[categorical_columns] = self.imputers['categorical'].transform(features[categorical_columns])
        
        # Store feature names
        self.feature_names = features.columns.tolist()
        
        return features
