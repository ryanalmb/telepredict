"""Main sports predictor class."""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

from ..ml_models.ensemble import EnsemblePredictor
from ..data_collection.data_manager import DataManager
from .analysis import MatchAnalyzer, TeamAnalyzer
from .odds_analyzer import OddsAnalyzer
from ..utils.cache import CacheManager
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class SportsPredictor:
    """Main sports prediction system."""
    
    def __init__(self, sport: str):
        self.sport = sport
        self.ensemble = EnsemblePredictor(sport)
        self.match_analyzer = MatchAnalyzer(sport)
        self.team_analyzer = TeamAnalyzer(sport)
        self.odds_analyzer = OddsAnalyzer(sport)
        self.cache = CacheManager()
        self.data_manager = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.data_manager = DataManager()
        await self.data_manager.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.data_manager:
            await self.data_manager.__aexit__(exc_type, exc_val, exc_tb)
    
    async def predict_match(self, home_team_id: str, away_team_id: str, 
                           match_date: Optional[str] = None) -> Dict[str, Any]:
        """Predict the outcome of a specific match."""
        logger.info(f"Predicting match: {home_team_id} vs {away_team_id}")
        
        if not self.ensemble.is_trained:
            raise ValueError("Ensemble model must be trained before making predictions")
        
        # Get comprehensive match data
        match_data = await self._collect_match_data(home_team_id, away_team_id, match_date)
        
        # Generate ML prediction
        ml_prediction = self.ensemble.predict(match_data)
        
        # Perform detailed analysis
        match_analysis = await self.match_analyzer.analyze_match(match_data)
        team_analysis = await self._analyze_teams(home_team_id, away_team_id)
        odds_analysis = await self.odds_analyzer.analyze_match_odds(match_data)
        
        # Combine all analyses
        prediction_result = {
            'match_info': {
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'sport': self.sport,
                'prediction_date': datetime.now().isoformat(),
                'match_date': match_date
            },
            'ml_prediction': ml_prediction,
            'match_analysis': match_analysis,
            'team_analysis': team_analysis,
            'odds_analysis': odds_analysis,
            'final_recommendation': self._generate_final_recommendation(
                ml_prediction, match_analysis, team_analysis, odds_analysis
            )
        }
        
        # Cache the prediction
        cache_key = f"prediction:{self.sport}:{home_team_id}:{away_team_id}:{match_date or 'upcoming'}"
        self.cache.set(cache_key, prediction_result, ttl=1800)  # 30 minutes
        
        return prediction_result
    
    async def predict_upcoming_matches(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Predict outcomes for upcoming matches."""
        logger.info(f"Predicting upcoming matches for {self.sport} ({days_ahead} days ahead)")
        
        if not self.data_manager:
            raise ValueError("Data manager not initialized. Use async context manager.")
        
        # Get upcoming matches
        upcoming_matches = await self.data_manager.collectors['espn'].get_upcoming_matches(
            self.sport, days_ahead
        )
        
        predictions = []
        
        for match in upcoming_matches:
            try:
                home_team_id = match.get('home_team', {}).get('id')
                away_team_id = match.get('away_team', {}).get('id')
                match_date = match.get('date')
                
                if home_team_id and away_team_id:
                    prediction = await self.predict_match(home_team_id, away_team_id, match_date)
                    prediction['match_info'].update({
                        'home_team_name': match.get('home_team', {}).get('name'),
                        'away_team_name': match.get('away_team', {}).get('name'),
                        'venue': match.get('venue')
                    })
                    predictions.append(prediction)
            
            except Exception as e:
                logger.error(f"Error predicting match {match}: {e}")
        
        return predictions
    
    async def train_models(self, start_date: str, end_date: str, 
                          team_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Train the prediction models with historical data."""
        logger.info(f"Training models for {self.sport} from {start_date} to {end_date}")
        
        if not self.data_manager:
            raise ValueError("Data manager not initialized. Use async context manager.")
        
        # Collect training data
        training_data = await self._collect_training_data(start_date, end_date, team_ids)
        
        if not training_data:
            raise ValueError("No training data collected")
        
        # Split into training and validation
        split_idx = int(0.8 * len(training_data))
        train_data = training_data[:split_idx]
        val_data = training_data[split_idx:]
        
        # Train ensemble
        training_results = await self.ensemble.train_ensemble(train_data, val_data)
        
        # Save trained models
        model_path = self.ensemble.save_ensemble()
        
        return {
            'training_results': training_results,
            'model_path': str(model_path),
            'training_samples': len(train_data),
            'validation_samples': len(val_data),
            'sport': self.sport
        }
    
    async def _collect_match_data(self, home_team_id: str, away_team_id: str, 
                                 match_date: Optional[str] = None) -> Dict[str, Any]:
        """Collect comprehensive data for a match prediction."""
        if not self.data_manager:
            raise ValueError("Data manager not initialized")
        
        # Check cache first
        cache_key = f"match_data:{self.sport}:{home_team_id}:{away_team_id}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Collect match prediction data
        match_data = await self.data_manager.get_match_prediction_data(
            self.sport, home_team_id, away_team_id
        )
        
        # Add match date if provided
        if match_date:
            match_data['date'] = match_date
        
        # Cache the data
        self.cache.set(cache_key, match_data, ttl=3600)  # 1 hour
        
        return match_data
    
    async def _analyze_teams(self, home_team_id: str, away_team_id: str) -> Dict[str, Any]:
        """Analyze both teams comprehensively."""
        home_analysis_task = asyncio.create_task(
            self.team_analyzer.analyze_team(home_team_id)
        )
        away_analysis_task = asyncio.create_task(
            self.team_analyzer.analyze_team(away_team_id)
        )
        
        home_analysis = await home_analysis_task
        away_analysis = await away_analysis_task
        
        return {
            'home_team': home_analysis,
            'away_team': away_analysis,
            'comparison': self.team_analyzer.compare_teams(home_analysis, away_analysis)
        }
    
    async def _collect_training_data(self, start_date: str, end_date: str, 
                                   team_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Collect historical data for training."""
        # This is a simplified implementation
        # In practice, you would collect historical match data with results
        
        training_data = []
        
        # For demonstration, create some dummy training data
        # In a real implementation, you would:
        # 1. Query historical matches from your data sources
        # 2. Collect team stats, player stats, etc. for each match
        # 3. Include the actual match results as targets
        
        if team_ids:
            for i, team_id in enumerate(team_ids[:10]):  # Limit for demo
                try:
                    # Get team analysis
                    team_data = await self.data_manager.get_team_analysis(self.sport, team_id)
                    
                    # Create dummy match data
                    dummy_match = {
                        'home_team': team_data,
                        'away_team': team_data,  # Simplified
                        'result': 'home_win' if i % 3 == 0 else ('draw' if i % 3 == 1 else 'away_win'),
                        'date': start_date
                    }
                    
                    training_data.append(dummy_match)
                
                except Exception as e:
                    logger.error(f"Error collecting training data for {team_id}: {e}")
        
        return training_data
    
    def _generate_final_recommendation(self, ml_prediction: Dict[str, Any],
                                     match_analysis: Dict[str, Any],
                                     team_analysis: Dict[str, Any],
                                     odds_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final prediction recommendation."""
        
        # Extract ML prediction
        ml_probs = ml_prediction.get('ensemble_probabilities', [0.33, 0.33, 0.34])
        ml_confidence = ml_prediction.get('confidence', 0.5)
        
        # Extract analysis insights
        match_insights = match_analysis.get('key_insights', [])
        team_comparison = team_analysis.get('comparison', {})
        odds_insights = odds_analysis.get('value_bets', [])
        
        # Calculate final probabilities (weighted combination)
        weights = {
            'ml_prediction': 0.6,
            'match_analysis': 0.2,
            'team_analysis': 0.15,
            'odds_analysis': 0.05
        }
        
        # Start with ML probabilities
        final_probs = np.array(ml_probs) * weights['ml_prediction']
        
        # Adjust based on team comparison
        if team_comparison.get('home_advantage', 0) > 0.6:
            final_probs[0] += 0.05  # Boost home win probability
        elif team_comparison.get('away_advantage', 0) > 0.6:
            final_probs[2] += 0.05  # Boost away win probability
        
        # Normalize probabilities
        final_probs = final_probs / np.sum(final_probs)
        
        # Determine recommendation
        max_prob_idx = np.argmax(final_probs)
        labels = ['home_win', 'draw', 'away_win']
        recommendation = labels[max_prob_idx]
        
        # Calculate overall confidence
        confidence_factors = [
            ml_confidence,
            match_analysis.get('confidence', 0.5),
            team_analysis.get('confidence', 0.5),
            odds_analysis.get('confidence', 0.5)
        ]
        overall_confidence = np.mean(confidence_factors)
        
        return {
            'recommendation': recommendation,
            'probabilities': {
                'home_win': float(final_probs[0]),
                'draw': float(final_probs[1]),
                'away_win': float(final_probs[2])
            },
            'confidence': float(overall_confidence),
            'key_factors': self._extract_key_factors(
                match_insights, team_comparison, odds_insights
            ),
            'risk_assessment': self._assess_risk(final_probs, overall_confidence),
            'betting_recommendation': self._generate_betting_recommendation(
                final_probs, odds_analysis
            )
        }
    
    def _extract_key_factors(self, match_insights: List[str], 
                           team_comparison: Dict[str, Any],
                           odds_insights: List[Dict]) -> List[str]:
        """Extract key factors influencing the prediction."""
        factors = []
        
        # Add match insights
        factors.extend(match_insights[:3])  # Top 3 insights
        
        # Add team comparison insights
        if team_comparison.get('home_advantage', 0) > 0.6:
            factors.append("Strong home team advantage")
        elif team_comparison.get('away_advantage', 0) > 0.6:
            factors.append("Strong away team advantage")
        
        if team_comparison.get('form_difference', 0) > 0.2:
            factors.append("Significant difference in recent form")
        
        # Add odds insights
        for insight in odds_insights[:2]:  # Top 2 value bets
            factors.append(f"Value bet opportunity: {insight.get('description', '')}")
        
        return factors[:5]  # Return top 5 factors
    
    def _assess_risk(self, probabilities: np.ndarray, confidence: float) -> str:
        """Assess the risk level of the prediction."""
        max_prob = np.max(probabilities)
        prob_spread = np.max(probabilities) - np.min(probabilities)
        
        if confidence > 0.8 and max_prob > 0.6:
            return "Low Risk"
        elif confidence > 0.6 and max_prob > 0.5:
            return "Medium Risk"
        elif confidence > 0.4 and prob_spread > 0.2:
            return "Medium-High Risk"
        else:
            return "High Risk"
    
    def _generate_betting_recommendation(self, probabilities: np.ndarray, 
                                       odds_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate betting recommendations."""
        value_bets = odds_analysis.get('value_bets', [])
        
        if not value_bets:
            return {
                'recommended': False,
                'reason': 'No value bets identified'
            }
        
        # Find best value bet
        best_value = max(value_bets, key=lambda x: x.get('value', 0))
        
        if best_value.get('value', 0) > 0.05:  # 5% edge
            return {
                'recommended': True,
                'bet_type': best_value.get('outcome'),
                'expected_value': best_value.get('value'),
                'recommended_stake': '2-3% of bankroll',
                'odds': best_value.get('odds'),
                'bookmaker': best_value.get('bookmaker')
            }
        else:
            return {
                'recommended': False,
                'reason': 'Insufficient value in available odds'
            }
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics of the trained models."""
        if not self.ensemble.is_trained:
            return {'error': 'Models not trained'}
        
        return self.ensemble.get_ensemble_info()
    
    def load_trained_models(self, model_path: Path) -> None:
        """Load pre-trained models."""
        self.ensemble.load_ensemble(model_path)
        logger.info(f"Loaded trained models for {self.sport}")
    
    async def update_models(self, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update models with new data (incremental learning)."""
        logger.info(f"Updating models with {len(new_data)} new samples")
        
        # For now, retrain with new data
        # In practice, you might implement incremental learning
        if new_data:
            training_results = await self.ensemble.train_ensemble(new_data)
            return {
                'update_results': training_results,
                'new_samples': len(new_data),
                'updated_at': datetime.now().isoformat()
            }
        
        return {'error': 'No new data provided'}
