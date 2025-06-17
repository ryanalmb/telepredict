"""
Sports Prediction System

A comprehensive sports prediction system with ML ensemble and Telegram bot interface.
"""

__version__ = "1.0.0"
__author__ = "Sports Prediction Team"
__email__ = "team@sportsprediction.com"

from .config.settings import Settings

# Conditional imports to avoid dependency issues during testing
__all__ = ["Settings"]

try:
    from .prediction_engine.predictor import SportsPredictor
    __all__.append("SportsPredictor")
except ImportError:
    pass

try:
    from .telegram_bot.bot import SportsPredictionBot
    __all__.append("SportsPredictionBot")
except ImportError:
    pass
