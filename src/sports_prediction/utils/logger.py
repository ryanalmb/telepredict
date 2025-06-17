"""Logging configuration for the sports prediction system."""

import sys
from pathlib import Path
from loguru import logger
from ..config.settings import settings


def get_logger(name: str = "sports_prediction"):
    """Get configured logger instance."""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file handler
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    return logger
