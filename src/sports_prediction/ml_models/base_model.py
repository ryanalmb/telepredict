"""Base class for all machine learning models."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from pathlib import Path
import joblib
import json
from datetime import datetime
from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class BaseModel(ABC):
    """Base class for all prediction models."""
    
    def __init__(self, model_name: str, sport: str):
        self.model_name = model_name
        self.sport = sport
        self.model = None
        self.is_trained = False
        self.feature_columns = []
        self.target_columns = []
        self.model_metadata = {
            'created_at': datetime.now().isoformat(),
            'model_name': model_name,
            'sport': sport,
            'version': '1.0.0',
            'training_samples': 0,
            'validation_score': None,
            'feature_importance': {}
        }
    
    @abstractmethod
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """Train the model."""
        pass
    
    @abstractmethod
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Make predictions."""
        pass
    
    @abstractmethod
    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict probabilities."""
        pass
    
    def validate(self, X_val: Union[np.ndarray, pd.DataFrame], y_val: Union[np.ndarray, pd.Series]) -> Dict[str, float]:
        """Validate the model."""
        if not self.is_trained:
            raise ValueError("Model must be trained before validation")
        
        predictions = self.predict(X_val)
        probabilities = self.predict_proba(X_val)
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_val, predictions, probabilities)
        
        # Update metadata
        self.model_metadata['validation_score'] = metrics.get('accuracy', 0.0)
        
        return metrics
    
    def save_model(self, filepath: Optional[Path] = None) -> Path:
        """Save the trained model."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.model_name}_{self.sport}_{timestamp}.joblib"
            filepath = settings.models_dir / filename
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model and metadata
        model_data = {
            'model': self.model,
            'metadata': self.model_metadata,
            'feature_columns': self.feature_columns,
            'target_columns': self.target_columns,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, filepath)
        
        # Save metadata separately as JSON
        metadata_path = filepath.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(self.model_metadata, f, indent=2)
        
        logger.info(f"Model saved to {filepath}")
        return filepath
    
    def load_model(self, filepath: Path) -> None:
        """Load a trained model."""
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        try:
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.model_metadata = model_data['metadata']
            self.feature_columns = model_data['feature_columns']
            self.target_columns = model_data['target_columns']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Model loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_trained:
            return {}
        
        # This will be overridden by specific model implementations
        return self.model_metadata.get('feature_importance', {})
    
    def _calculate_metrics(self, y_true: Union[np.ndarray, pd.Series], 
                          y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
        """Calculate evaluation metrics."""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, log_loss
        
        metrics = {}
        
        try:
            # Convert to numpy arrays
            y_true = np.array(y_true)
            y_pred = np.array(y_pred)
            
            # Basic classification metrics
            metrics['accuracy'] = accuracy_score(y_true, y_pred)
            
            # Handle multiclass vs binary classification
            if len(np.unique(y_true)) > 2:
                # Multiclass
                metrics['precision'] = precision_score(y_true, y_pred, average='weighted')
                metrics['recall'] = recall_score(y_true, y_pred, average='weighted')
                metrics['f1'] = f1_score(y_true, y_pred, average='weighted')
                
                # AUC for multiclass (one-vs-rest)
                if y_proba.shape[1] > 2:
                    metrics['auc'] = roc_auc_score(y_true, y_proba, multi_class='ovr', average='weighted')
            else:
                # Binary classification
                metrics['precision'] = precision_score(y_true, y_pred)
                metrics['recall'] = recall_score(y_true, y_pred)
                metrics['f1'] = f1_score(y_true, y_pred)
                
                # AUC for binary classification
                if y_proba.shape[1] == 2:
                    metrics['auc'] = roc_auc_score(y_true, y_proba[:, 1])
            
            # Log loss
            metrics['log_loss'] = log_loss(y_true, y_proba)
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            metrics['accuracy'] = 0.0
        
        return metrics
    
    def _prepare_data(self, X: Union[np.ndarray, pd.DataFrame], 
                     y: Optional[Union[np.ndarray, pd.Series]] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Prepare data for training/prediction."""
        # Convert to numpy arrays
        if isinstance(X, pd.DataFrame):
            self.feature_columns = X.columns.tolist()
            X = X.values
        
        if y is not None:
            if isinstance(y, pd.Series):
                y = y.values
        
        return X, y
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'model_name': self.model_name,
            'sport': self.sport,
            'is_trained': self.is_trained,
            'metadata': self.model_metadata,
            'feature_count': len(self.feature_columns),
            'target_count': len(self.target_columns)
        }
    
    def update_metadata(self, **kwargs) -> None:
        """Update model metadata."""
        self.model_metadata.update(kwargs)
        self.model_metadata['updated_at'] = datetime.now().isoformat()
