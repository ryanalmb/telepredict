"""Scikit-learn models for sports prediction."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from .base_model import BaseModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SklearnPredictor(BaseModel):
    """Scikit-learn ensemble model for sports prediction."""
    
    def __init__(self, sport: str, model_type: str = 'ensemble'):
        super().__init__(f"sklearn_{model_type}", sport)
        self.model_type = model_type
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
        # Initialize model based on type
        if model_type == 'ensemble':
            self.model = self._create_ensemble_model()
        elif model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        elif model_type == 'logistic_regression':
            self.model = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', LogisticRegression(
                    random_state=42,
                    max_iter=1000,
                    multi_class='ovr'
                ))
            ])
        elif model_type == 'svm':
            self.model = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', SVC(
                    probability=True,
                    random_state=42,
                    kernel='rbf'
                ))
            ])
        elif model_type == 'naive_bayes':
            self.model = GaussianNB()
        elif model_type == 'knn':
            self.model = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', KNeighborsClassifier(
                    n_neighbors=5,
                    weights='distance'
                ))
            ])
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _create_ensemble_model(self) -> VotingClassifier:
        """Create ensemble voting classifier."""
        # Individual models
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        gb = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        lr = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression(
                random_state=42,
                max_iter=1000,
                multi_class='ovr'
            ))
        ])
        
        svm = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', SVC(
                probability=True,
                random_state=42,
                kernel='rbf'
            ))
        ])
        
        # Create voting classifier
        ensemble = VotingClassifier(
            estimators=[
                ('rf', rf),
                ('gb', gb),
                ('lr', lr),
                ('svm', svm)
            ],
            voting='soft'
        )
        
        return ensemble
    
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """Train the sklearn model."""
        logger.info(f"Training {self.model_type} model for {self.sport}")
        
        X, y = self._prepare_data(X, y)
        
        # Convert to DataFrame if numpy array
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        
        # Handle categorical features
        X_processed = self._process_categorical_features(X, fit=True)
        
        # Split data for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_processed, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        self.model_metadata['training_samples'] = len(X_processed)
        
        # Calculate feature importance if available
        feature_importance = self._get_feature_importance(X_processed.columns)
        self.model_metadata['feature_importance'] = feature_importance
        
        # Validation metrics
        val_score = self.model.score(X_val, y_val)
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5)
        
        return {
            'validation_accuracy': val_score,
            'cv_mean_score': cv_scores.mean(),
            'cv_std_score': cv_scores.std(),
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
        
        return self.model.predict(X_processed)
    
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
        
        return self.model.predict_proba(X_processed)
    
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
    
    def _get_feature_importance(self, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance if available."""
        importance_dict = {}
        
        try:
            if hasattr(self.model, 'feature_importances_'):
                # Direct feature importance (RandomForest, GradientBoosting)
                importance_dict = dict(zip(feature_names, self.model.feature_importances_))
            elif hasattr(self.model, 'estimators_'):
                # Voting classifier - get average importance from tree-based models
                importances = []
                for name, estimator in self.model.estimators_:
                    if hasattr(estimator, 'feature_importances_'):
                        importances.append(estimator.feature_importances_)
                    elif hasattr(estimator, 'named_steps') and hasattr(estimator.named_steps.get('classifier'), 'feature_importances_'):
                        importances.append(estimator.named_steps['classifier'].feature_importances_)
                
                if importances:
                    avg_importance = np.mean(importances, axis=0)
                    importance_dict = dict(zip(feature_names, avg_importance))
            elif hasattr(self.model, 'named_steps') and hasattr(self.model.named_steps.get('classifier'), 'coef_'):
                # Linear models - use coefficient magnitude
                coef = self.model.named_steps['classifier'].coef_
                if len(coef.shape) > 1:
                    # Multi-class: use mean absolute coefficient
                    importance = np.mean(np.abs(coef), axis=0)
                else:
                    importance = np.abs(coef)
                importance_dict = dict(zip(feature_names, importance))
        
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
        
        return importance_dict
    
    def hyperparameter_tuning(self, X: Union[np.ndarray, pd.DataFrame], 
                             y: Union[np.ndarray, pd.Series],
                             param_grid: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform hyperparameter tuning."""
        logger.info(f"Performing hyperparameter tuning for {self.model_type}")
        
        X, y = self._prepare_data(X, y)
        
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        
        X_processed = self._process_categorical_features(X, fit=True)
        
        # Default parameter grids
        if param_grid is None:
            param_grid = self._get_default_param_grid()
        
        # Perform grid search
        grid_search = GridSearchCV(
            self.model,
            param_grid,
            cv=5,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_processed, y)
        
        # Update model with best parameters
        self.model = grid_search.best_estimator_
        self.is_trained = True
        self.model_metadata['training_samples'] = len(X_processed)
        self.model_metadata['best_params'] = grid_search.best_params_
        
        return {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }
    
    def _get_default_param_grid(self) -> Dict[str, List]:
        """Get default parameter grid for tuning."""
        if self.model_type == 'random_forest':
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        elif self.model_type == 'gradient_boosting':
            return {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 0.9, 1.0]
            }
        elif self.model_type == 'logistic_regression':
            return {
                'classifier__C': [0.1, 1.0, 10.0],
                'classifier__penalty': ['l1', 'l2'],
                'classifier__solver': ['liblinear', 'saga']
            }
        elif self.model_type == 'svm':
            return {
                'classifier__C': [0.1, 1.0, 10.0],
                'classifier__gamma': ['scale', 'auto', 0.001, 0.01],
                'classifier__kernel': ['rbf', 'poly']
            }
        elif self.model_type == 'knn':
            return {
                'classifier__n_neighbors': [3, 5, 7, 9],
                'classifier__weights': ['uniform', 'distance'],
                'classifier__metric': ['euclidean', 'manhattan']
            }
        else:
            return {}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        info = super().get_model_info()
        info['model_type'] = self.model_type
        
        if hasattr(self.model, 'get_params'):
            info['model_params'] = self.model.get_params()
        
        return info
