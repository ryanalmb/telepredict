"""PyTorch models for sports prediction."""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from sklearn.preprocessing import StandardScaler
from .base_model import BaseModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LSTMPredictor(BaseModel):
    """LSTM model for time-series sports prediction."""
    
    def __init__(self, sport: str, input_size: int = 50, hidden_size: int = 128, 
                 num_layers: int = 2, num_classes: int = 3, sequence_length: int = 10):
        super().__init__("lstm_predictor", sport)
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_classes = num_classes
        self.sequence_length = sequence_length
        self.scaler = StandardScaler()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize model
        self.model = LSTMNetwork(input_size, hidden_size, num_layers, num_classes).to(self.device)
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
    
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """Train the LSTM model."""
        logger.info(f"Training LSTM model for {self.sport}")
        
        X, y = self._prepare_data(X, y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        
        # Convert to tensors
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        y_tensor = torch.LongTensor(y).to(self.device)
        
        # Create data loader
        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        # Training loop
        self.model.train()
        total_loss = 0
        num_epochs = 100
        
        for epoch in range(num_epochs):
            epoch_loss = 0
            for batch_X, batch_y in dataloader:
                self.optimizer.zero_grad()
                
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                
                loss.backward()
                self.optimizer.step()
                
                epoch_loss += loss.item()
            
            total_loss += epoch_loss
            
            if (epoch + 1) % 20 == 0:
                logger.info(f"Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss:.4f}")
        
        self.is_trained = True
        self.model_metadata['training_samples'] = len(X)
        
        return {
            'final_loss': total_loss / num_epochs,
            'epochs': num_epochs,
            'device': str(self.device)
        }
    
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X, _ = self._prepare_data(X)
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_tensor)
            _, predicted = torch.max(outputs.data, 1)
        
        return predicted.cpu().numpy()
    
    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X, _ = self._prepare_data(X)
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_tensor)
            probabilities = torch.softmax(outputs, dim=1)
        
        return probabilities.cpu().numpy()
    
    def _prepare_data(self, X: Union[np.ndarray, pd.DataFrame], 
                     y: Optional[Union[np.ndarray, pd.Series]] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Prepare data for LSTM (create sequences)."""
        X, y = super()._prepare_data(X, y)
        
        # If X is not already in sequence format, create sequences
        if len(X.shape) == 2:
            X = self._create_sequences(X)
        
        return X, y
    
    def _create_sequences(self, data: np.ndarray) -> np.ndarray:
        """Create sequences for LSTM input."""
        sequences = []
        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data[i:i + self.sequence_length])
        return np.array(sequences)


class LSTMNetwork(nn.Module):
    """LSTM neural network."""
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, num_classes: int):
        super(LSTMNetwork, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden_size, num_classes)
    
    def forward(self, x):
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # LSTM forward pass
        out, _ = self.lstm(x, (h0, c0))
        
        # Take the last output
        out = out[:, -1, :]
        out = self.dropout(out)
        out = self.fc(out)
        
        return out


class TransformerPredictor(BaseModel):
    """Transformer model for sports prediction."""
    
    def __init__(self, sport: str, input_size: int = 50, d_model: int = 128, 
                 nhead: int = 8, num_layers: int = 6, num_classes: int = 3, sequence_length: int = 10):
        super().__init__("transformer_predictor", sport)
        self.input_size = input_size
        self.d_model = d_model
        self.nhead = nhead
        self.num_layers = num_layers
        self.num_classes = num_classes
        self.sequence_length = sequence_length
        self.scaler = StandardScaler()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize model
        self.model = TransformerNetwork(input_size, d_model, nhead, num_layers, num_classes).to(self.device)
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.0001)
    
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> Dict[str, Any]:
        """Train the Transformer model."""
        logger.info(f"Training Transformer model for {self.sport}")
        
        X, y = self._prepare_data(X, y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        
        # Convert to tensors
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        y_tensor = torch.LongTensor(y).to(self.device)
        
        # Create data loader
        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
        
        # Training loop
        self.model.train()
        total_loss = 0
        num_epochs = 50
        
        for epoch in range(num_epochs):
            epoch_loss = 0
            for batch_X, batch_y in dataloader:
                self.optimizer.zero_grad()
                
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                
                loss.backward()
                self.optimizer.step()
                
                epoch_loss += loss.item()
            
            total_loss += epoch_loss
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss:.4f}")
        
        self.is_trained = True
        self.model_metadata['training_samples'] = len(X)
        
        return {
            'final_loss': total_loss / num_epochs,
            'epochs': num_epochs,
            'device': str(self.device)
        }
    
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X, _ = self._prepare_data(X)
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_tensor)
            _, predicted = torch.max(outputs.data, 1)
        
        return predicted.cpu().numpy()
    
    def predict_proba(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict probabilities."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        X, _ = self._prepare_data(X)
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_tensor)
            probabilities = torch.softmax(outputs, dim=1)
        
        return probabilities.cpu().numpy()
    
    def _prepare_data(self, X: Union[np.ndarray, pd.DataFrame], 
                     y: Optional[Union[np.ndarray, pd.Series]] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Prepare data for Transformer (create sequences)."""
        X, y = super()._prepare_data(X, y)
        
        # If X is not already in sequence format, create sequences
        if len(X.shape) == 2:
            X = self._create_sequences(X)
        
        return X, y
    
    def _create_sequences(self, data: np.ndarray) -> np.ndarray:
        """Create sequences for Transformer input."""
        sequences = []
        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data[i:i + self.sequence_length])
        return np.array(sequences)


class TransformerNetwork(nn.Module):
    """Transformer neural network."""
    
    def __init__(self, input_size: int, d_model: int, nhead: int, num_layers: int, num_classes: int):
        super(TransformerNetwork, self).__init__()
        self.d_model = d_model
        
        # Input projection
        self.input_projection = nn.Linear(input_size, d_model)
        
        # Positional encoding
        self.pos_encoding = PositionalEncoding(d_model)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output layers
        self.dropout = nn.Dropout(0.1)
        self.fc = nn.Linear(d_model, num_classes)
    
    def forward(self, x):
        # Project input to d_model dimensions
        x = self.input_projection(x)
        
        # Add positional encoding
        x = self.pos_encoding(x)
        
        # Transformer encoding
        x = self.transformer(x)
        
        # Global average pooling
        x = torch.mean(x, dim=1)
        
        # Output
        x = self.dropout(x)
        x = self.fc(x)
        
        return x


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer."""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        return x + self.pe[:x.size(1), :].transpose(0, 1)
