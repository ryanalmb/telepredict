"""Ensemble predictor combining all ML models."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import asyncio
from .pytorch_models import LSTMPredictor, TransformerPredictor
from .tensorflow_models import TeamEmbeddingModel, PlayerEmbeddingModel
from .lightgbm_model import LightGBMPredictor
from .xgboost_model import XGBoostPredictor
from .sklearn_models import SklearnPredictor
from .meta_learner import MetaLearner
from .feature_engineering import FeatureEngineer
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class EnsemblePredictor:
    """Main ensemble predictor combining all ML models."""
    
    def __init__(self, sport: str):
        self.sport = sport
        self.feature_engineer = FeatureEngineer(sport)
        self.models = {}
        self.meta_learner = None
        self.is_trained = False
        
        # Initialize all models
        self._initialize_models()
    
    def _initialize_models(self) -> None:
        """Initialize all ML models."""
        logger.info(f"Initializing ensemble models for {self.sport}")
        
        # PyTorch models
        self.models['lstm'] = LSTMPredictor(self.sport)
        self.models['transformer'] = TransformerPredictor(self.sport)
        
        # TensorFlow models
        self.models['team_embedding'] = TeamEmbeddingModel(self.sport)
        self.models['player_embedding'] = PlayerEmbeddingModel(self.sport)
        
        # Tree-based models
        self.models['lightgbm'] = LightGBMPredictor(self.sport)
        self.models['xgboost'] = XGBoostPredictor(self.sport)
        
        # Sklearn models
        self.models['random_forest'] = SklearnPredictor(self.sport, 'random_forest')
        self.models['gradient_boosting'] = SklearnPredictor(self.sport, 'gradient_boosting')
        self.models['logistic_regression'] = SklearnPredictor(self.sport, 'logistic_regression')
        self.models['svm'] = SklearnPredictor(self.sport, 'svm')
        
        # Initialize meta-learner
        self.meta_learner = MetaLearner(self.sport)
        
        logger.info(f"Initialized {len(self.models)} base models")
    
    async def train_ensemble(self, training_data: List[Dict[str, Any]], 
                           validation_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Train the entire ensemble."""
        logger.info(f"Training ensemble for {self.sport}")
        
        # Engineer features
        X_train, y_train = self._prepare_training_data(training_data)
        X_val, y_val = None, None
        
        if validation_data:
            X_val, y_val = self._prepare_training_data(validation_data)
        
        if X_train.empty:
            raise ValueError("No training data available")
        
        # Train individual models
        training_results = {}
        
        # Train models that can handle tabular data directly
        tabular_models = ['lightgbm', 'xgboost', 'random_forest', 'gradient_boosting', 
                         'logistic_regression', 'svm']
        
        for model_name in tabular_models:
            try:
                logger.info(f"Training {model_name}")
                result = self.models[model_name].train(X_train, y_train)
                training_results[model_name] = result
                
                # Add to meta-learner
                self.meta_learner.add_base_model(model_name, self.models[model_name])
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                training_results[model_name] = {'error': str(e)}
        
        # Train deep learning models (requires sequence data)
        sequence_models = ['lstm', 'transformer']
        
        for model_name in sequence_models:
            try:
                logger.info(f"Training {model_name}")
                
                # Create sequence data for time-series models
                X_seq = self._create_sequence_data(X_train)
                
                if X_seq is not None:
                    result = self.models[model_name].train(X_seq, y_train)
                    training_results[model_name] = result
                    
                    # Add to meta-learner
                    self.meta_learner.add_base_model(model_name, self.models[model_name])
                else:
                    logger.warning(f"Could not create sequence data for {model_name}")
                    
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                training_results[model_name] = {'error': str(e)}
        
        # Train embedding models
        embedding_models = ['team_embedding', 'player_embedding']
        
        for model_name in embedding_models:
            try:
                logger.info(f"Training {model_name}")
                
                # Prepare data for embedding models
                X_emb = self._prepare_embedding_data(X_train)
                
                if X_emb is not None:
                    result = self.models[model_name].train(X_emb, y_train)
                    training_results[model_name] = result
                    
                    # Add to meta-learner
                    self.meta_learner.add_base_model(model_name, self.models[model_name])
                else:
                    logger.warning(f"Could not prepare embedding data for {model_name}")
                    
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                training_results[model_name] = {'error': str(e)}
        
        # Train meta-learner
        try:
            logger.info("Training meta-learner")
            meta_result = self.meta_learner.train(X_train, y_train)
            training_results['meta_learner'] = meta_result
            
        except Exception as e:
            logger.error(f"Error training meta-learner: {e}")
            training_results['meta_learner'] = {'error': str(e)}
        
        self.is_trained = True
        
        # Validation if provided
        validation_results = {}
        if X_val is not None and y_val is not None:
            validation_results = self._validate_ensemble(X_val, y_val)
        
        return {
            'training_results': training_results,
            'validation_results': validation_results,
            'num_training_samples': len(X_train),
            'num_models_trained': len([r for r in training_results.values() if 'error' not in r])
        }
    
    def predict(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction for a single match."""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before making predictions")
        
        # Engineer features
        features = self.feature_engineer.engineer_features(match_data)
        
        if features.empty:
            raise ValueError("Could not engineer features from match data")
        
        # Get predictions from all models
        predictions = {}
        probabilities = {}
        
        # Tabular models
        tabular_models = ['lightgbm', 'xgboost', 'random_forest', 'gradient_boosting', 
                         'logistic_regression', 'svm']
        
        for model_name in tabular_models:
            try:
                if self.models[model_name].is_trained:
                    pred = self.models[model_name].predict(features)
                    proba = self.models[model_name].predict_proba(features)
                    
                    predictions[model_name] = pred[0] if len(pred) > 0 else None
                    probabilities[model_name] = proba[0].tolist() if len(proba) > 0 else None
            
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {e}")
        
        # Deep learning models
        sequence_models = ['lstm', 'transformer']
        
        for model_name in sequence_models:
            try:
                if self.models[model_name].is_trained:
                    X_seq = self._create_sequence_data(features)
                    if X_seq is not None:
                        pred = self.models[model_name].predict(X_seq)
                        proba = self.models[model_name].predict_proba(X_seq)
                        
                        predictions[model_name] = pred[0] if len(pred) > 0 else None
                        probabilities[model_name] = proba[0].tolist() if len(proba) > 0 else None
            
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {e}")
        
        # Embedding models
        embedding_models = ['team_embedding', 'player_embedding']
        
        for model_name in embedding_models:
            try:
                if self.models[model_name].is_trained:
                    X_emb = self._prepare_embedding_data(features)
                    if X_emb is not None:
                        pred = self.models[model_name].predict(X_emb)
                        proba = self.models[model_name].predict_proba(X_emb)
                        
                        predictions[model_name] = pred[0] if len(pred) > 0 else None
                        probabilities[model_name] = proba[0].tolist() if len(proba) > 0 else None
            
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {e}")
        
        # Meta-learner prediction
        meta_prediction = None
        meta_probabilities = None
        
        try:
            if self.meta_learner.is_trained:
                meta_pred = self.meta_learner.predict(features)
                meta_proba = self.meta_learner.predict_proba(features)
                
                meta_prediction = meta_pred[0] if len(meta_pred) > 0 else None
                meta_probabilities = meta_proba[0].tolist() if len(meta_proba) > 0 else None
        
        except Exception as e:
            logger.error(f"Error predicting with meta-learner: {e}")
        
        # Calculate ensemble prediction (simple voting if meta-learner fails)
        ensemble_prediction = meta_prediction
        ensemble_probabilities = meta_probabilities
        
        if ensemble_prediction is None:
            # Fallback to simple voting
            valid_predictions = [p for p in predictions.values() if p is not None]
            if valid_predictions:
                ensemble_prediction = max(set(valid_predictions), key=valid_predictions.count)
            
            # Average probabilities
            valid_probabilities = [p for p in probabilities.values() if p is not None]
            if valid_probabilities:
                ensemble_probabilities = np.mean(valid_probabilities, axis=0).tolist()
        
        # Calculate confidence
        confidence = self._calculate_confidence(probabilities, ensemble_probabilities)
        
        return {
            'ensemble_prediction': ensemble_prediction,
            'ensemble_probabilities': ensemble_probabilities,
            'confidence': confidence,
            'individual_predictions': predictions,
            'individual_probabilities': probabilities,
            'meta_prediction': meta_prediction,
            'meta_probabilities': meta_probabilities,
            'prediction_labels': ['home_win', 'draw', 'away_win']  # Adjust based on sport
        }
    
    def _prepare_training_data(self, data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, np.ndarray]:
        """Prepare training data from match data."""
        features_list = []
        targets = []
        
        for match in data:
            try:
                # Engineer features
                features = self.feature_engineer.engineer_features(match)
                
                if not features.empty:
                    features_list.append(features)
                    
                    # Extract target (match result)
                    target = self._extract_target(match)
                    if target is not None:
                        targets.append(target)
            
            except Exception as e:
                logger.error(f"Error processing match data: {e}")
        
        if features_list:
            X = pd.concat(features_list, ignore_index=True)
            y = np.array(targets)
            return X, y
        else:
            return pd.DataFrame(), np.array([])
    
    def _extract_target(self, match: Dict[str, Any]) -> Optional[int]:
        """Extract target variable from match data."""
        # This is a simplified implementation
        # In practice, you would extract the actual match result
        
        # Look for result in various formats
        if 'result' in match:
            result = match['result']
            if result == 'home_win':
                return 0
            elif result == 'draw':
                return 1
            elif result == 'away_win':
                return 2
        
        # Try to determine from scores
        home_score = None
        away_score = None
        
        if 'home_team' in match and 'score' in match['home_team']:
            home_score = match['home_team']['score']
        
        if 'away_team' in match and 'score' in match['away_team']:
            away_score = match['away_team']['score']
        
        if home_score is not None and away_score is not None:
            try:
                home_score = float(home_score)
                away_score = float(away_score)
                
                if home_score > away_score:
                    return 0  # home_win
                elif home_score == away_score:
                    return 1  # draw
                else:
                    return 2  # away_win
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _create_sequence_data(self, X: pd.DataFrame) -> Optional[np.ndarray]:
        """Create sequence data for time-series models."""
        # This is a simplified implementation
        # In practice, you would create proper time sequences
        
        if len(X) < 10:  # Need minimum sequence length
            return None
        
        # Create dummy sequences by reshaping data
        try:
            sequence_length = 10
            feature_size = X.shape[1]
            
            # Pad or truncate to create sequences
            if len(X) >= sequence_length:
                sequences = []
                for i in range(len(X) - sequence_length + 1):
                    sequences.append(X.iloc[i:i + sequence_length].values)
                return np.array(sequences)
            else:
                # Pad with zeros if not enough data
                padded = np.zeros((sequence_length, feature_size))
                padded[:len(X)] = X.values
                return np.array([padded])
        
        except Exception as e:
            logger.error(f"Error creating sequence data: {e}")
            return None
    
    def _prepare_embedding_data(self, X: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Prepare data for embedding models."""
        # This is a simplified implementation
        # In practice, you would extract team/player IDs and other categorical features
        
        try:
            # Add dummy team columns if not present
            if 'home_team_id' not in X.columns:
                X = X.copy()
                X['home_team_id'] = 0  # Dummy team ID
                X['away_team_id'] = 1  # Dummy team ID
            
            return X
        
        except Exception as e:
            logger.error(f"Error preparing embedding data: {e}")
            return None
    
    def _validate_ensemble(self, X_val: pd.DataFrame, y_val: np.ndarray) -> Dict[str, Any]:
        """Validate the ensemble on validation data."""
        validation_results = {}
        
        # Validate individual models
        for model_name, model in self.models.items():
            try:
                if model.is_trained:
                    metrics = model.validate(X_val, y_val)
                    validation_results[model_name] = metrics
            
            except Exception as e:
                logger.error(f"Error validating {model_name}: {e}")
                validation_results[model_name] = {'error': str(e)}
        
        # Validate meta-learner
        try:
            if self.meta_learner.is_trained:
                meta_metrics = self.meta_learner.validate(X_val, y_val)
                validation_results['meta_learner'] = meta_metrics
        
        except Exception as e:
            logger.error(f"Error validating meta-learner: {e}")
            validation_results['meta_learner'] = {'error': str(e)}
        
        return validation_results
    
    def _calculate_confidence(self, individual_probabilities: Dict[str, List], 
                            ensemble_probabilities: Optional[List]) -> float:
        """Calculate prediction confidence."""
        if not ensemble_probabilities:
            return 0.0
        
        # Confidence based on maximum probability
        max_prob = max(ensemble_probabilities)
        
        # Adjust confidence based on agreement between models
        valid_probs = [p for p in individual_probabilities.values() if p is not None]
        
        if len(valid_probs) > 1:
            # Calculate variance in predictions
            prob_array = np.array(valid_probs)
            variance = np.var(prob_array, axis=0)
            avg_variance = np.mean(variance)
            
            # Lower variance = higher confidence
            agreement_factor = 1.0 / (1.0 + avg_variance)
            confidence = max_prob * agreement_factor
        else:
            confidence = max_prob
        
        return min(confidence, 1.0)
    
    def save_ensemble(self, filepath: Optional[Path] = None) -> Path:
        """Save the entire ensemble."""
        if filepath is None:
            filepath = settings.models_dir / f"ensemble_{self.sport}.joblib"
        
        # Save individual models
        model_paths = {}
        for name, model in self.models.items():
            if model.is_trained:
                model_path = model.save_model()
                model_paths[name] = str(model_path)
        
        # Save meta-learner
        if self.meta_learner.is_trained:
            meta_path = self.meta_learner.save_model()
            model_paths['meta_learner'] = str(meta_path)
        
        # Save ensemble metadata
        import joblib
        ensemble_data = {
            'sport': self.sport,
            'model_paths': model_paths,
            'is_trained': self.is_trained,
            'feature_engineer': self.feature_engineer
        }
        
        joblib.dump(ensemble_data, filepath)
        logger.info(f"Ensemble saved to {filepath}")
        
        return filepath
    
    def load_ensemble(self, filepath: Path) -> None:
        """Load the entire ensemble."""
        import joblib
        
        ensemble_data = joblib.load(filepath)
        
        self.sport = ensemble_data['sport']
        self.is_trained = ensemble_data['is_trained']
        self.feature_engineer = ensemble_data['feature_engineer']
        
        # Load individual models
        for name, model_path in ensemble_data['model_paths'].items():
            if name == 'meta_learner':
                self.meta_learner.load_model(Path(model_path))
            elif name in self.models:
                self.models[name].load_model(Path(model_path))
        
        logger.info(f"Ensemble loaded from {filepath}")
    
    def get_ensemble_info(self) -> Dict[str, Any]:
        """Get information about the ensemble."""
        info = {
            'sport': self.sport,
            'is_trained': self.is_trained,
            'models': {},
            'meta_learner': None
        }
        
        # Get model info
        for name, model in self.models.items():
            info['models'][name] = model.get_model_info()
        
        # Get meta-learner info
        if self.meta_learner:
            info['meta_learner'] = self.meta_learner.get_ensemble_info()
        
        return info
