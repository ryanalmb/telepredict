"""TensorFlow models for sports prediction."""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from sklearn.preprocessing import StandardScaler, LabelEncoder
from .base_model import BaseModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TeamEmbeddingModel(BaseModel):
    """Team embedding model using TensorFlow."""
    
    def __init__(self, sport: str, num_teams: int = 100, embedding_dim: int = 64, 
                 hidden_units: List[int] = [128, 64], num_classes: int = 3):
        super().__init__("team_embedding", sport)
        self.num_teams = num_teams
        self.embedding_dim = embedding_dim
        self.hidden_units = hidden_units
        self.num_classes = num_classes
        self.scaler = StandardScaler()
        self.team_encoder = LabelEncoder()
        
        # Build model
        self.model = self._build_model()
    
    def _build_model(self) -> keras.Model:
        """Build the team embedding model."""
        # Team inputs
        home_team_input = layers.Input(shape=(), name='home_team', dtype='int32')
        away_team_input = layers.Input(shape=(), name='away_team', dtype='int32')
        
        # Numerical features input
        numerical_input = layers.Input(shape=(None,), name='numerical_features')
        
        # Team embeddings
        team_embedding = layers.Embedding(
            input_dim=self.num_teams,
            output_dim=self.embedding_dim,
            name='team_embedding'
        )
        
        home_team_emb = team_embedding(home_team_input)
        away_team_emb = team_embedding(away_team_input)
        
        # Flatten embeddings
        home_team_emb = layers.Flatten()(home_team_emb)
        away_team_emb = layers.Flatten()(away_team_emb)
        
        # Combine team embeddings
        team_features = layers.Concatenate()([home_team_emb, away_team_emb])
        
        # Normalize numerical features
        numerical_normalized = layers.BatchNormalization()(numerical_input)
        
        # Combine all features
        combined_features = layers.Concatenate()([team_features, numerical_normalized])
        
        # Hidden layers
        x = combined_features
        for units in self.hidden_units:
            x = layers.Dense(units, activation='relu')(x)
            x = layers.Dropout(0.3)(x)
            x = layers.BatchNormalization()(x)
        
        # Output layer
        output = layers.Dense(self.num_classes, activation='softmax', name='output')(x)
        
        # Create model
        model = keras.Model(
            inputs=[home_team_input, away_team_input, numerical_input],
            outputs=output,
            name='team_embedding_model'
        )
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """Train the team embedding model."""
        logger.info(f"Training team embedding model for {self.sport}")
        
        # Prepare data
        X_processed, y_processed = self._prepare_training_data(X, y)
        
        # Split data
        split_idx = int(0.8 * len(y_processed))
        X_train = {key: val[:split_idx] for key, val in X_processed.items()}
        X_val = {key: val[split_idx:] for key, val in X_processed.items()}
        y_train = y_processed[:split_idx]
        y_val = y_processed[split_idx:]
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        self.model_metadata['training_samples'] = len(y_processed)
        
        return {
            'final_loss': history.history['loss'][-1],
            'final_val_loss': history.history['val_loss'][-1],
            'final_accuracy': history.history['accuracy'][-1],
            'final_val_accuracy': history.history['val_accuracy'][-1],
            'epochs_trained': len(history.history['loss'])
        }
    
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X_processed = self._prepare_prediction_data(X)
        predictions = self.model.predict(X_processed)
        return np.argmax(predictions, axis=1)
    
    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X_processed = self._prepare_prediction_data(X)
        return self.model.predict(X_processed)
    
    def _prepare_training_data(self, X: Union[np.ndarray, pd.DataFrame], 
                              y: Union[np.ndarray, pd.Series]) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
        """Prepare data for training."""
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
        
        # Extract team columns (assuming they exist)
        home_team_col = None
        away_team_col = None
        
        for col in X.columns:
            if 'home_team' in str(col).lower():
                home_team_col = col
            elif 'away_team' in str(col).lower():
                away_team_col = col
        
        if home_team_col is None or away_team_col is None:
            # Create dummy team IDs if not available
            home_teams = np.random.randint(0, self.num_teams, len(X))
            away_teams = np.random.randint(0, self.num_teams, len(X))
        else:
            # Encode team names to IDs
            all_teams = pd.concat([X[home_team_col], X[away_team_col]]).unique()
            self.team_encoder.fit(all_teams)
            
            home_teams = self.team_encoder.transform(X[home_team_col])
            away_teams = self.team_encoder.transform(X[away_team_col])
            
            # Remove team columns from numerical features
            X = X.drop([home_team_col, away_team_col], axis=1)
        
        # Scale numerical features
        numerical_features = self.scaler.fit_transform(X.select_dtypes(include=[np.number]))
        
        # Prepare target
        if isinstance(y, pd.Series):
            y = y.values
        
        return {
            'home_team': home_teams,
            'away_team': away_teams,
            'numerical_features': numerical_features
        }, y
    
    def _prepare_prediction_data(self, X: Union[np.ndarray, pd.DataFrame]) -> Dict[str, np.ndarray]:
        """Prepare data for prediction."""
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
        
        # Extract team columns
        home_team_col = None
        away_team_col = None
        
        for col in X.columns:
            if 'home_team' in str(col).lower():
                home_team_col = col
            elif 'away_team' in str(col).lower():
                away_team_col = col
        
        if home_team_col is None or away_team_col is None:
            # Create dummy team IDs if not available
            home_teams = np.random.randint(0, self.num_teams, len(X))
            away_teams = np.random.randint(0, self.num_teams, len(X))
        else:
            # Encode team names to IDs
            home_teams = self.team_encoder.transform(X[home_team_col])
            away_teams = self.team_encoder.transform(X[away_team_col])
            
            # Remove team columns from numerical features
            X = X.drop([home_team_col, away_team_col], axis=1)
        
        # Scale numerical features
        numerical_features = self.scaler.transform(X.select_dtypes(include=[np.number]))
        
        return {
            'home_team': home_teams,
            'away_team': away_teams,
            'numerical_features': numerical_features
        }


class PlayerEmbeddingModel(BaseModel):
    """Player embedding model using TensorFlow."""
    
    def __init__(self, sport: str, num_players: int = 1000, embedding_dim: int = 32,
                 hidden_units: List[int] = [128, 64], num_classes: int = 3):
        super().__init__("player_embedding", sport)
        self.num_players = num_players
        self.embedding_dim = embedding_dim
        self.hidden_units = hidden_units
        self.num_classes = num_classes
        self.scaler = StandardScaler()
        self.player_encoder = LabelEncoder()
        
        # Build model
        self.model = self._build_model()
    
    def _build_model(self) -> keras.Model:
        """Build the player embedding model."""
        # Player inputs (top players for each team)
        home_players_input = layers.Input(shape=(5,), name='home_players', dtype='int32')
        away_players_input = layers.Input(shape=(5,), name='away_players', dtype='int32')
        
        # Numerical features input
        numerical_input = layers.Input(shape=(None,), name='numerical_features')
        
        # Player embeddings
        player_embedding = layers.Embedding(
            input_dim=self.num_players,
            output_dim=self.embedding_dim,
            name='player_embedding'
        )
        
        # Embed players and aggregate
        home_players_emb = player_embedding(home_players_input)
        away_players_emb = player_embedding(away_players_input)
        
        # Aggregate player embeddings (mean pooling)
        home_team_emb = layers.GlobalAveragePooling1D()(home_players_emb)
        away_team_emb = layers.GlobalAveragePooling1D()(away_players_emb)
        
        # Combine team embeddings
        team_features = layers.Concatenate()([home_team_emb, away_team_emb])
        
        # Normalize numerical features
        numerical_normalized = layers.BatchNormalization()(numerical_input)
        
        # Combine all features
        combined_features = layers.Concatenate()([team_features, numerical_normalized])
        
        # Hidden layers
        x = combined_features
        for units in self.hidden_units:
            x = layers.Dense(units, activation='relu')(x)
            x = layers.Dropout(0.3)(x)
            x = layers.BatchNormalization()(x)
        
        # Output layer
        output = layers.Dense(self.num_classes, activation='softmax', name='output')(x)
        
        # Create model
        model = keras.Model(
            inputs=[home_players_input, away_players_input, numerical_input],
            outputs=output,
            name='player_embedding_model'
        )
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """Train the player embedding model."""
        logger.info(f"Training player embedding model for {self.sport}")
        
        # Prepare data
        X_processed, y_processed = self._prepare_training_data(X, y)
        
        # Split data
        split_idx = int(0.8 * len(y_processed))
        X_train = {key: val[:split_idx] for key, val in X_processed.items()}
        X_val = {key: val[split_idx:] for key, val in X_processed.items()}
        y_train = y_processed[:split_idx]
        y_val = y_processed[split_idx:]
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=100,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        self.model_metadata['training_samples'] = len(y_processed)
        
        return {
            'final_loss': history.history['loss'][-1],
            'final_val_loss': history.history['val_loss'][-1],
            'final_accuracy': history.history['accuracy'][-1],
            'final_val_accuracy': history.history['val_accuracy'][-1],
            'epochs_trained': len(history.history['loss'])
        }
    
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X_processed = self._prepare_prediction_data(X)
        predictions = self.model.predict(X_processed)
        return np.argmax(predictions, axis=1)
    
    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X_processed = self._prepare_prediction_data(X)
        return self.model.predict(X_processed)
    
    def _prepare_training_data(self, X: Union[np.ndarray, pd.DataFrame], 
                              y: Union[np.ndarray, pd.Series]) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
        """Prepare data for training."""
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
        
        # For simplicity, create dummy player data
        # In a real implementation, you would extract actual player IDs
        home_players = np.random.randint(0, self.num_players, (len(X), 5))
        away_players = np.random.randint(0, self.num_players, (len(X), 5))
        
        # Scale numerical features
        numerical_features = self.scaler.fit_transform(X.select_dtypes(include=[np.number]))
        
        # Prepare target
        if isinstance(y, pd.Series):
            y = y.values
        
        return {
            'home_players': home_players,
            'away_players': away_players,
            'numerical_features': numerical_features
        }, y
    
    def _prepare_prediction_data(self, X: Union[np.ndarray, pd.DataFrame]) -> Dict[str, np.ndarray]:
        """Prepare data for prediction."""
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
        
        # Create dummy player data
        home_players = np.random.randint(0, self.num_players, (len(X), 5))
        away_players = np.random.randint(0, self.num_players, (len(X), 5))
        
        # Scale numerical features
        numerical_features = self.scaler.transform(X.select_dtypes(include=[np.number]))
        
        return {
            'home_players': home_players,
            'away_players': away_players,
            'numerical_features': numerical_features
        }
