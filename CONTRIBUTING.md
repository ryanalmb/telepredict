# Contributing to Sports Prediction Bot

Thank you for your interest in contributing to the Sports Prediction Bot! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
- Use the [GitHub Issues](https://github.com/yourusername/sports-prediction-bot/issues) page
- Search existing issues before creating a new one
- Provide detailed information including:
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details
  - Error messages and logs

### Suggesting Features
- Open a [GitHub Discussion](https://github.com/yourusername/sports-prediction-bot/discussions) for feature requests
- Describe the feature and its use case
- Explain why it would be valuable to users
- Consider implementation complexity and maintenance

### Code Contributions
1. **Fork the repository**
2. **Create a feature branch** from `main`
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+
- Git
- Docker (optional but recommended)

### Local Development
```bash
# Clone your fork
git clone https://github.com/yourusername/sports-prediction-bot.git
cd sports-prediction-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Copy environment template
cp .env.example .env
# Edit .env with your test configuration
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_prediction_engine.py

# Run tests for specific module
pytest tests/test_ml_models/
```

### Code Quality Checks
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/

# Run all quality checks
pre-commit run --all-files
```

## 📝 Coding Standards

### Python Style
- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting
- Line length: 100 characters
- Use type hints for all functions and methods

### Code Organization
```python
# Import order (enforced by isort)
# 1. Standard library imports
import asyncio
from typing import Dict, List

# 2. Third-party imports
import pandas as pd
import numpy as np

# 3. Local imports
from ..utils.logger import get_logger
from .base_model import BaseModel
```

### Documentation
- Use Google-style docstrings
- Document all public functions, classes, and modules
- Include type information in docstrings
- Provide examples for complex functions

```python
def predict_match(self, home_team: str, away_team: str) -> Dict[str, Any]:
    """Predict the outcome of a match.
    
    Args:
        home_team: Name or ID of the home team
        away_team: Name or ID of the away team
        
    Returns:
        Dictionary containing prediction results with keys:
        - prediction: Predicted outcome ('home_win', 'draw', 'away_win')
        - confidence: Confidence score (0.0 to 1.0)
        - probabilities: Dict with outcome probabilities
        
    Raises:
        ValueError: If team names are invalid
        
    Example:
        >>> predictor = SportsPredictor('nba')
        >>> result = predictor.predict_match('Lakers', 'Warriors')
        >>> print(result['prediction'])
        'home_win'
    """
```

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately
- Handle edge cases gracefully

```python
try:
    prediction = await self.model.predict(features)
except ModelNotTrainedError:
    logger.error("Model not trained for sport: %s", self.sport)
    raise ValueError(f"Model for {self.sport} is not available")
except Exception as e:
    logger.error("Prediction failed: %s", e)
    raise PredictionError(f"Failed to generate prediction: {e}")
```

## 🧪 Testing Guidelines

### Test Structure
- Use pytest for all tests
- Organize tests to mirror source code structure
- Use descriptive test names

```
tests/
├── test_data_collection/
│   ├── test_espn_collector.py
│   ├── test_sportradar_collector.py
│   └── test_data_manager.py
├── test_ml_models/
│   ├── test_pytorch_models.py
│   ├── test_ensemble.py
│   └── test_feature_engineering.py
└── test_telegram_bot/
    ├── test_handlers.py
    └── test_formatters.py
```

### Test Types
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

### Test Examples
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_predict_match_success():
    """Test successful match prediction."""
    predictor = SportsPredictor('nba')
    
    with patch.object(predictor.ensemble, 'predict') as mock_predict:
        mock_predict.return_value = {
            'prediction': 'home_win',
            'confidence': 0.75,
            'probabilities': {'home_win': 0.6, 'draw': 0.1, 'away_win': 0.3}
        }
        
        result = await predictor.predict_match('Lakers', 'Warriors')
        
        assert result['prediction'] == 'home_win'
        assert result['confidence'] == 0.75
        mock_predict.assert_called_once()

@pytest.mark.asyncio
async def test_predict_match_invalid_team():
    """Test prediction with invalid team name."""
    predictor = SportsPredictor('nba')
    
    with pytest.raises(ValueError, match="Invalid team"):
        await predictor.predict_match('', 'Warriors')
```

## 🏗️ Architecture Guidelines

### Module Organization
- Keep modules focused and cohesive
- Use clear interfaces between components
- Minimize dependencies between modules
- Follow dependency injection patterns

### Async/Await Usage
- Use async/await for I/O operations
- Properly handle async context managers
- Use asyncio.gather() for concurrent operations
- Handle async exceptions appropriately

### Configuration Management
- Use environment variables for configuration
- Provide sensible defaults
- Validate configuration on startup
- Document all configuration options

### Logging
- Use structured logging with loguru
- Include relevant context in log messages
- Use appropriate log levels
- Avoid logging sensitive information

```python
from ..utils.logger import get_logger

logger = get_logger(__name__)

async def collect_data(self, sport: str) -> Dict[str, Any]:
    logger.info("Starting data collection", sport=sport)
    
    try:
        data = await self._fetch_data(sport)
        logger.info("Data collection completed", 
                   sport=sport, 
                   teams_count=len(data.get('teams', {})))
        return data
    except Exception as e:
        logger.error("Data collection failed", 
                    sport=sport, 
                    error=str(e))
        raise
```

## 📦 Adding New Features

### New Sports Support
1. Add sport configuration to `settings.py`
2. Implement sport-specific data collectors
3. Add sport-specific feature engineering
4. Update model training for the new sport
5. Add tests for all new components
6. Update documentation

### New ML Models
1. Inherit from `BaseModel` class
2. Implement required abstract methods
3. Add model to ensemble configuration
4. Include comprehensive tests
5. Document model architecture and usage

### New Data Sources
1. Create collector class inheriting from base collector
2. Implement rate limiting and error handling
3. Add data validation and cleaning
4. Include integration tests
5. Update data manager configuration

## 🔄 Pull Request Process

### Before Submitting
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Pre-commit hooks pass
- [ ] No merge conflicts with main branch

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Review Process
1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Code Review**: Maintainers review code for quality and design
3. **Testing**: Reviewers may test functionality manually
4. **Approval**: At least one maintainer approval required
5. **Merge**: Squash and merge to main branch

## 🐛 Debugging Guidelines

### Common Issues
- **API Rate Limits**: Check rate limiting configuration
- **Model Training Failures**: Verify data quality and quantity
- **Telegram Bot Issues**: Check bot token and webhook configuration
- **Database Connections**: Verify connection strings and credentials

### Debugging Tools
- Use `pdb` or `ipdb` for interactive debugging
- Enable debug logging for detailed information
- Use Docker logs for containerized debugging
- Monitor system resources during debugging

### Performance Profiling
```python
import cProfile
import pstats

# Profile a function
profiler = cProfile.Profile()
profiler.enable()

# Your code here
result = await predictor.predict_match('Lakers', 'Warriors')

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## 📚 Resources

### Documentation
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Async Programming](https://docs.python.org/3/library/asyncio.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Best Practices](https://docs.docker.com/develop/best-practices/)

### Machine Learning
- [PyTorch Documentation](https://pytorch.org/docs/)
- [TensorFlow Documentation](https://www.tensorflow.org/guide)
- [Scikit-learn Documentation](https://scikit-learn.org/stable/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)

### APIs
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [ESPN API Documentation](https://www.espn.com/apis/devcenter/)
- [SportRadar API](https://developer.sportradar.com/)

## 🎯 Contribution Areas

We especially welcome contributions in these areas:

### High Priority
- New sports support (Tennis, Cricket, etc.)
- Model performance improvements
- API optimization and caching
- User interface enhancements

### Medium Priority
- Additional data sources
- Advanced analytics features
- Mobile app development
- Internationalization

### Low Priority
- Documentation improvements
- Code refactoring
- Performance optimizations
- Additional testing

## 📞 Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Discord**: [Join our Discord server](https://discord.gg/sportsprediction)
- **Email**: developers@sportsprediction.com

Thank you for contributing to Sports Prediction Bot! 🏆
