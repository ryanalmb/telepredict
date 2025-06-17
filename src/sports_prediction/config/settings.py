"""Configuration settings for the sports prediction system."""

import os
from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot Configuration
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_URL")
    
    # Sports Data APIs
    espn_api_key: Optional[str] = Field(None, env="ESPN_API_KEY")
    sportradar_api_key: Optional[str] = Field(None, env="SPORTRADAR_API_KEY")
    odds_api_key: Optional[str] = Field(None, env="ODDS_API_KEY")
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    aws_s3_bucket: str = Field("sports-prediction-models", env="AWS_S3_BUCKET")
    aws_dynamodb_table: str = Field("sports-predictions", env="AWS_DYNAMODB_TABLE")
    
    # Database Configuration
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    mongodb_url: str = Field("mongodb://localhost:27017/sports_predictions", env="MONGODB_URL")
    
    # ML Model Configuration
    model_update_interval: int = Field(3600, env="MODEL_UPDATE_INTERVAL")
    prediction_confidence_threshold: float = Field(0.7, env="PREDICTION_CONFIDENCE_THRESHOLD")
    ensemble_weights_update_frequency: int = Field(24, env="ENSEMBLE_WEIGHTS_UPDATE_FREQUENCY")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/sports_prediction.log", env="LOG_FILE")
    
    # Cache Configuration
    cache_ttl: int = Field(3600, env="CACHE_TTL")
    max_cache_size: int = Field(1000, env="MAX_CACHE_SIZE")
    
    # Rate Limiting
    api_rate_limit: int = Field(100, env="API_RATE_LIMIT")
    scraper_delay: int = Field(2, env="SCRAPER_DELAY")
    
    # Development
    debug: bool = Field(False, env="DEBUG")
    testing: bool = Field(False, env="TESTING")
    
    # Supported Sports
    supported_sports: List[str] = [
        "mls", "nba", "nfl", "nhl", "mlb", 
        "premier_league", "champions_league", "la_liga", "bundesliga", "serie_a",
        "ufc", "boxing", "tennis", "rugby"
    ]
    
    # Model Paths
    @property
    def models_dir(self) -> Path:
        return Path("models")
    
    @property
    def data_dir(self) -> Path:
        return Path("data")
    
    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"
    
    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"
    
    @property
    def processed_data_dir(self) -> Path:
        return self.data_dir / "processed"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


# Global settings instance
settings = Settings()
