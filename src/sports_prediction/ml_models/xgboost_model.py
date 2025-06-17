"""XGBoost model for sports prediction."""

import xgboost as xgb
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from .base_model import BaseModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


class XGBoostPredictor(BaseModel):
    """XGBoost model for sports prediction."""
    
    def __init__(self, sport: str, **xgb_params):
        super().__init__("xgboost_predictor", sport)
        
        # Default XGBoost parameters
        self.xgb_params = {
            'objective': 'multi:softprob',
            'num_class': 3,
            'eval_metric': 'mlogloss',
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'verbosity': 1
        }
        
        # Update with custom parameters
        self.xgb_params.update(xgb_params)
        
        self.label_encoders = {}
    
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """Train the XGBoost model."""
        logger.info(f"Training XGBoost model for {self.sport}")
        
        X, y = self._prepare_data(X, y)
        
        # Convert to DataFrame if numpy array
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        
        # Handle categorical features
        X_processed = self._process_categorical_features(X, fit=True)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_processed, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Create DMatrix objects
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)
        
        # Set up evaluation list
        evallist = [(dtrain, 'train'), (dval, 'eval')]
        
        # Train model
        self.model = xgb.train(
            self.xgb_params,
            dtrain,
            num_boost_round=1000,
            evals=evallist,
            early_stopping_rounds=50,
            verbose_eval=100
        )
        
        self.is_trained = True
        self.model_metadata['training_samples'] = len(X_processed)
        
        # Calculate feature importance
        feature_importance = self.model.get_score(importance_type='weight')
        self.model_metadata['feature_importance'] = feature_importance
        
        # Validation metrics
        val_predictions = self.model.predict(dval)
        val_pred_classes = np.argmax(val_predictions, axis=1)
        
        return {
            'best_iteration': self.model.best_iteration,
            'best_score': self.model.best_score,
            'feature_importance': feature_importance,
            'num_features': len(X_processed.columns)
        }
    
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X, _ = self._prepare_data(X)
        
        # Convert to DataFrame if numpy array
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        
        # Process categorical features
        X_processed = self._process_categorical_features(X, fit=False)
        
        # Create DMatrix
        dtest = xgb.DMatrix(X_processed)
        
        # Make predictions
        predictions = self.model.predict(dtest, iteration_range=(0, self.model.best_iteration))
        return np.argmax(predictions, axis=1)
    
    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X, _ = self._prepare_data(X)
        
        # Convert to DataFrame if numpy array
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        
        # Process categorical features
        X_processed = self._process_categorical_features(X, fit=False)
        
        # Create DMatrix
        dtest = xgb.DMatrix(X_processed)
        
        # Make predictions
        return self.model.predict(dtest, iteration_range=(0, self.model.best_iteration))
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_trained:
            return {}
        
        return self.model.get_score(importance_type='weight')
    
    def _process_categorical_features(self, X: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Process categorical features."""
        X_processed = X.copy()
        
        # Identify categorical columns
        categorical_cols = X_processed.select_dtypes(include=['object', 'category']).columns
        
        for col in categorical_cols:
            if fit:
                # Fit label encoder
                self.label_encoders[col] = LabelEncoder()
                X_processed[col] = self.label_encoders[col].fit_transform(X_processed[col].astype(str))
            else:
                # Transform using existing encoder
                if col in self.label_encoders:
                    # Handle unseen categories
                    unique_values = set(X_processed[col].astype(str))
                    known_values = set(self.label_encoders[col].classes_)
                    unseen_values = unique_values - known_values
                    
                    if unseen_values:
                        logger.warning(f"Unseen categories in {col}: {unseen_values}")
                        # Replace unseen values with the first known value
                        replacement_value = self.label_encoders[col].classes_[0]
                        X_processed[col] = X_processed[col].astype(str).replace(
                            list(unseen_values), replacement_value
                        )
                    
                    X_processed[col] = self.label_encoders[col].transform(X_processed[col].astype(str))
        
        return X_processed
    
    def get_model_params(self) -> Dict[str, Any]:
        """Get model parameters."""
        return self.xgb_params.copy()
    
    def set_model_params(self, **params) -> None:
        """Set model parameters."""
        self.xgb_params.update(params)
        # If model is already trained, it will need to be retrained
        if self.is_trained:
            logger.warning("Model parameters changed. Model will need to be retrained.")
    
    def plot_feature_importance(self, max_features: int = 20) -> None:
        """Plot feature importance."""
        if not self.is_trained:
            raise ValueError("Model must be trained before plotting feature importance")
        
        try:
            import matplotlib.pyplot as plt
            
            # Get feature importance
            importance = self.get_feature_importance()
            
            # Sort by importance
            sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            
            # Take top features
            top_features = sorted_importance[:max_features]
            features, scores = zip(*top_features)
            
            # Create plot
            plt.figure(figsize=(10, 8))
            plt.barh(range(len(features)), scores)
            plt.yticks(range(len(features)), features)
            plt.xlabel('Feature Importance')
            plt.title(f'Top {max_features} Feature Importance - {self.sport.upper()}')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            logger.warning("Matplotlib not available for plotting")
    
    def plot_tree(self, tree_index: int = 0) -> None:
        """Plot a specific tree."""
        if not self.is_trained:
            raise ValueError("Model must be trained before plotting trees")
        
        try:
            import matplotlib.pyplot as plt
            
            # Plot tree
            fig, ax = plt.subplots(figsize=(20, 10))
            xgb.plot_tree(self.model, num_trees=tree_index, ax=ax)
            plt.title(f'XGBoost Tree {tree_index} - {self.sport.upper()}')
            plt.show()
            
        except ImportError:
            logger.warning("Matplotlib not available for plotting")
    
    def explain_prediction(self, X: Union[np.ndarray, pd.DataFrame], index: int = 0) -> Dict[str, Any]:
        """Explain a single prediction using SHAP values."""
        if not self.is_trained:
            raise ValueError("Model must be trained before explaining predictions")
        
        try:
            import shap
            
            X, _ = self._prepare_data(X)
            
            if isinstance(X, np.ndarray):
                X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
            
            X_processed = self._process_categorical_features(X, fit=False)
            
            # Create SHAP explainer
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(X_processed.iloc[[index]])
            
            # Get prediction
            prediction = self.predict_proba(X_processed.iloc[[index]])[0]
            predicted_class = np.argmax(prediction)
            
            return {
                'prediction_probabilities': prediction.tolist(),
                'predicted_class': int(predicted_class),
                'shap_values': shap_values[0].tolist(),
                'feature_names': X_processed.columns.tolist(),
                'base_value': explainer.expected_value
            }
            
        except ImportError:
            logger.warning("SHAP not available for model explanation")
            return {
                'prediction_probabilities': self.predict_proba(X[[index]]).tolist(),
                'predicted_class': int(self.predict(X[[index]])[0])
            }
    
    def get_model_dump(self) -> List[str]:
        """Get model dump for inspection."""
        if not self.is_trained:
            raise ValueError("Model must be trained before getting model dump")
        
        return self.model.get_dump()
    
    def save_model_native(self, filepath: str) -> None:
        """Save model in XGBoost native format."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        self.model.save_model(filepath)
        logger.info(f"XGBoost model saved to {filepath}")
    
    def load_model_native(self, filepath: str) -> None:
        """Load model from XGBoost native format."""
        self.model = xgb.Booster()
        self.model.load_model(filepath)
        self.is_trained = True
        logger.info(f"XGBoost model loaded from {filepath}")
