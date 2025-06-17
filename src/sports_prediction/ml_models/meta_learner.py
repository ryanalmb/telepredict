"""Meta-learner for combining multiple model predictions."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from .base_model import BaseModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MetaLearner(BaseModel):
    """Meta-learner that combines predictions from multiple base models."""
    
    def __init__(self, sport: str, meta_model_type: str = 'logistic_regression'):
        super().__init__("meta_learner", sport)
        self.meta_model_type = meta_model_type
        self.base_models = {}
        self.model_weights = {}
        self.scaler = StandardScaler()
        
        # Initialize meta-model
        if meta_model_type == 'logistic_regression':
            self.model = LogisticRegression(
                random_state=42,
                max_iter=1000,
                multi_class='ovr'
            )
        elif meta_model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown meta-model type: {meta_model_type}")
    
    def add_base_model(self, name: str, model: BaseModel, weight: float = 1.0) -> None:
        """Add a base model to the ensemble."""
        if not model.is_trained:
            logger.warning(f"Base model {name} is not trained")
        
        self.base_models[name] = model
        self.model_weights[name] = weight
        logger.info(f"Added base model: {name} with weight {weight}")
    
    def remove_base_model(self, name: str) -> None:
        """Remove a base model from the ensemble."""
        if name in self.base_models:
            del self.base_models[name]
            del self.model_weights[name]
            logger.info(f"Removed base model: {name}")
    
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """Train the meta-learner using base model predictions."""
        logger.info(f"Training meta-learner for {self.sport}")
        
        if not self.base_models:
            raise ValueError("No base models added. Add base models before training.")
        
        X, y = self._prepare_data(X, y)
        
        # Generate base model predictions
        base_predictions = self._generate_base_predictions(X)
        
        if base_predictions.empty:
            raise ValueError("No valid predictions from base models")
        
        # Split data for meta-learning
        X_meta_train, X_meta_val, y_meta_train, y_meta_val = train_test_split(
            base_predictions, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_meta_train_scaled = self.scaler.fit_transform(X_meta_train)
        X_meta_val_scaled = self.scaler.transform(X_meta_val)
        
        # Train meta-model
        self.model.fit(X_meta_train_scaled, y_meta_train)
        
        self.is_trained = True
        self.model_metadata['training_samples'] = len(base_predictions)
        self.model_metadata['base_models'] = list(self.base_models.keys())
        self.model_metadata['model_weights'] = self.model_weights.copy()
        
        # Validation metrics
        val_score = self.model.score(X_meta_val_scaled, y_meta_val)
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_meta_train_scaled, y_meta_train, cv=5)
        
        # Calculate individual model performance
        individual_scores = self._evaluate_individual_models(X_meta_val, y_meta_val)
        
        return {
            'meta_validation_accuracy': val_score,
            'meta_cv_mean_score': cv_scores.mean(),
            'meta_cv_std_score': cv_scores.std(),
            'individual_model_scores': individual_scores,
            'num_base_models': len(self.base_models),
            'meta_features': base_predictions.columns.tolist()
        }
    
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Make predictions using the meta-learner."""
        if not self.is_trained:
            raise ValueError("Meta-learner must be trained before making predictions")
        
        X, _ = self._prepare_data(X)
        
        # Generate base model predictions
        base_predictions = self._generate_base_predictions(X)
        
        if base_predictions.empty:
            raise ValueError("No valid predictions from base models")
        
        # Scale features
        base_predictions_scaled = self.scaler.transform(base_predictions)
        
        # Make meta-prediction
        return self.model.predict(base_predictions_scaled)
    
    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict probabilities using the meta-learner."""
        if not self.is_trained:
            raise ValueError("Meta-learner must be trained before making predictions")
        
        X, _ = self._prepare_data(X)
        
        # Generate base model predictions
        base_predictions = self._generate_base_predictions(X)
        
        if base_predictions.empty:
            raise ValueError("No valid predictions from base models")
        
        # Scale features
        base_predictions_scaled = self.scaler.transform(base_predictions)
        
        # Make meta-prediction
        return self.model.predict_proba(base_predictions_scaled)
    
    def _generate_base_predictions(self, X: Union[np.ndarray, pd.DataFrame]) -> pd.DataFrame:
        """Generate predictions from all base models."""
        predictions_dict = {}
        
        for name, model in self.base_models.items():
            try:
                if model.is_trained:
                    # Get probability predictions
                    proba = model.predict_proba(X)
                    
                    # Add probability features for each class
                    for class_idx in range(proba.shape[1]):
                        feature_name = f"{name}_class_{class_idx}_proba"
                        predictions_dict[feature_name] = proba[:, class_idx]
                    
                    # Add class predictions
                    class_pred = model.predict(X)
                    predictions_dict[f"{name}_class_pred"] = class_pred
                    
                    # Apply weight
                    weight = self.model_weights.get(name, 1.0)
                    for key in predictions_dict:
                        if key.startswith(name):
                            predictions_dict[key] = predictions_dict[key] * weight
                
                else:
                    logger.warning(f"Base model {name} is not trained, skipping")
            
            except Exception as e:
                logger.error(f"Error generating predictions from {name}: {e}")
        
        return pd.DataFrame(predictions_dict)
    
    def _evaluate_individual_models(self, X_val: pd.DataFrame, y_val: np.ndarray) -> Dict[str, float]:
        """Evaluate individual model performance."""
        scores = {}
        
        for name, model in self.base_models.items():
            try:
                if model.is_trained:
                    # Extract predictions for this model
                    model_features = [col for col in X_val.columns if col.startswith(name)]
                    if model_features:
                        # Use class predictions for evaluation
                        class_pred_col = f"{name}_class_pred"
                        if class_pred_col in X_val.columns:
                            predictions = X_val[class_pred_col].values
                            accuracy = np.mean(predictions == y_val)
                            scores[name] = accuracy
            
            except Exception as e:
                logger.error(f"Error evaluating {name}: {e}")
                scores[name] = 0.0
        
        return scores
    
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """Update model weights."""
        for name, weight in new_weights.items():
            if name in self.model_weights:
                self.model_weights[name] = weight
                logger.info(f"Updated weight for {name}: {weight}")
            else:
                logger.warning(f"Model {name} not found in base models")
        
        # Update metadata
        self.model_metadata['model_weights'] = self.model_weights.copy()
        
        # If meta-learner is trained, it should be retrained with new weights
        if self.is_trained:
            logger.warning("Model weights updated. Consider retraining the meta-learner.")
    
    def get_model_contributions(self, X: Union[np.ndarray, pd.DataFrame]) -> Dict[str, np.ndarray]:
        """Get individual model contributions to final predictions."""
        if not self.is_trained:
            raise ValueError("Meta-learner must be trained before getting contributions")
        
        X, _ = self._prepare_data(X)
        
        # Generate base model predictions
        base_predictions = self._generate_base_predictions(X)
        
        contributions = {}
        
        for name in self.base_models.keys():
            # Get features for this model
            model_features = [col for col in base_predictions.columns if col.startswith(name)]
            if model_features:
                model_data = base_predictions[model_features]
                
                # Calculate contribution (simplified as mean probability weighted by model weight)
                weight = self.model_weights.get(name, 1.0)
                proba_features = [col for col in model_features if 'proba' in col]
                if proba_features:
                    contribution = model_data[proba_features].mean(axis=1).values * weight
                    contributions[name] = contribution
        
        return contributions
    
    def get_ensemble_info(self) -> Dict[str, Any]:
        """Get information about the ensemble."""
        info = {
            'meta_model_type': self.meta_model_type,
            'num_base_models': len(self.base_models),
            'base_models': {},
            'model_weights': self.model_weights.copy(),
            'is_trained': self.is_trained
        }
        
        # Get info for each base model
        for name, model in self.base_models.items():
            info['base_models'][name] = {
                'model_name': model.model_name,
                'is_trained': model.is_trained,
                'training_samples': model.model_metadata.get('training_samples', 0)
            }
        
        return info
    
    def optimize_weights(self, X: Union[np.ndarray, pd.DataFrame], 
                        y: Union[np.ndarray, pd.Series]) -> Dict[str, float]:
        """Optimize model weights using validation performance."""
        logger.info("Optimizing model weights")
        
        X, y = self._prepare_data(X, y)
        
        # Generate base predictions
        base_predictions = self._generate_base_predictions(X)
        
        # Try different weight combinations
        from itertools import product
        
        weight_options = [0.5, 1.0, 1.5, 2.0]
        best_weights = self.model_weights.copy()
        best_score = 0.0
        
        # Grid search over weights (simplified for computational efficiency)
        model_names = list(self.base_models.keys())
        
        for weights in product(weight_options, repeat=min(len(model_names), 3)):  # Limit combinations
            # Create weight dict
            test_weights = {}
            for i, name in enumerate(model_names[:len(weights)]):
                test_weights[name] = weights[i]
            
            # Update weights temporarily
            old_weights = self.model_weights.copy()
            self.update_weights(test_weights)
            
            try:
                # Generate predictions with new weights
                weighted_predictions = self._generate_base_predictions(X)
                
                # Quick evaluation using simple voting
                if not weighted_predictions.empty:
                    # Use class predictions for voting
                    class_cols = [col for col in weighted_predictions.columns if 'class_pred' in col]
                    if class_cols:
                        # Simple majority voting
                        votes = weighted_predictions[class_cols].mode(axis=1)[0]
                        score = np.mean(votes == y)
                        
                        if score > best_score:
                            best_score = score
                            best_weights = test_weights.copy()
            
            except Exception as e:
                logger.error(f"Error evaluating weights {test_weights}: {e}")
            
            # Restore old weights
            self.model_weights = old_weights
        
        # Apply best weights
        self.update_weights(best_weights)
        
        logger.info(f"Optimized weights: {best_weights}, Score: {best_score}")
        return best_weights
