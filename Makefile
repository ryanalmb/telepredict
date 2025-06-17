# Sports Prediction Bot Makefile

.PHONY: help install install-dev setup test test-cov lint format type-check security clean build run docker-build docker-run docker-stop deploy

# Default target
help:
	@echo "Sports Prediction Bot - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo "  setup            Setup the project (create directories, etc.)"
	@echo ""
	@echo "Development:"
	@echo "  test             Run tests"
	@echo "  test-cov         Run tests with coverage"
	@echo "  lint             Run all linting checks"
	@echo "  format           Format code with black and isort"
	@echo "  type-check       Run type checking with mypy"
	@echo "  security         Run security checks"
	@echo "  pre-commit       Run pre-commit hooks"
	@echo ""
	@echo "Application:"
	@echo "  run              Run the bot locally"
	@echo "  collect-data     Collect sports data"
	@echo "  train-models     Train ML models"
	@echo "  predict          Make a prediction"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build Docker images"
	@echo "  docker-run       Run with Docker Compose"
	@echo "  docker-stop      Stop Docker containers"
	@echo "  docker-logs      View Docker logs"
	@echo "  docker-clean     Clean Docker resources"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-dev       Deploy to development environment"
	@echo "  deploy-prod      Deploy to production environment"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean temporary files"
	@echo "  docs             Generate documentation"
	@echo "  backup           Backup data and models"

# Setup & Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

setup:
	python -m src.sports_prediction.cli setup
	mkdir -p data logs models cache
	cp .env.example .env
	@echo "Please edit .env with your configuration"

# Development
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

security:
	bandit -r src/ -f json -o bandit-report.json
	safety check

pre-commit:
	pre-commit run --all-files

# Application
run:
	python -m src.sports_prediction.cli run-bot

collect-data:
	python -m src.sports_prediction.cli collect-data --sport nba --days 7

train-models:
	python -m src.sports_prediction.cli train-models --sport nba --start-date 2023-01-01 --end-date 2024-01-01

predict:
	python -m src.sports_prediction.cli predict --sport nba --home-team lakers --away-team warriors

status:
	python -m src.sports_prediction.cli status

# Docker
docker-build:
	docker-compose build

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

docker-shell:
	docker-compose exec sports-prediction-bot bash

# Database
db-init:
	docker-compose exec mongodb mongo sports_predictions /docker-entrypoint-initdb.d/mongo-init.js

db-backup:
	docker-compose exec mongodb mongodump --db sports_predictions --out /data/backup/$(shell date +%Y%m%d_%H%M%S)

db-restore:
	@echo "Usage: make db-restore BACKUP_DIR=<backup_directory>"
	docker-compose exec mongodb mongorestore --db sports_predictions /data/backup/$(BACKUP_DIR)

# Monitoring
monitoring-up:
	docker-compose up -d prometheus grafana

monitoring-down:
	docker-compose stop prometheus grafana

# Deployment
deploy-dev:
	@echo "Deploying to development environment..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

deploy-prod:
	@echo "Deploying to production environment..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Data Management
backup:
	mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	cp -r data/ backups/$(shell date +%Y%m%d_%H%M%S)/
	cp -r models/ backups/$(shell date +%Y%m%d_%H%M%S)/
	@echo "Backup created in backups/$(shell date +%Y%m%d_%H%M%S)/"

restore:
	@echo "Usage: make restore BACKUP_DIR=<backup_directory>"
	cp -r backups/$(BACKUP_DIR)/data/ ./
	cp -r backups/$(BACKUP_DIR)/models/ ./

# Documentation
docs:
	cd docs && make html

docs-serve:
	cd docs/_build/html && python -m http.server 8080

# Infrastructure Management
infra-deploy:
	@echo "Usage: make infra-deploy ENV=<dev|staging|prod> REGION=<aws-region>"
	@if [ -z "$(ENV)" ]; then echo "Error: ENV parameter is required"; exit 1; fi
	@if [ -z "$(REGION)" ]; then echo "Error: REGION parameter is required"; exit 1; fi
	cd infrastructure/scripts && ./deploy.sh $(ENV) $(REGION)

infra-destroy:
	@echo "Usage: make infra-destroy ENV=<dev|staging|prod> REGION=<aws-region>"
	@if [ -z "$(ENV)" ]; then echo "Error: ENV parameter is required"; exit 1; fi
	@if [ -z "$(REGION)" ]; then echo "Error: REGION parameter is required"; exit 1; fi
	cd infrastructure/scripts && ./destroy.sh $(ENV) $(REGION)

infra-status:
	@echo "Usage: make infra-status ENV=<dev|staging|prod> REGION=<aws-region>"
	@if [ -z "$(ENV)" ]; then echo "Error: ENV parameter is required"; exit 1; fi
	@if [ -z "$(REGION)" ]; then echo "Error: REGION parameter is required"; exit 1; fi
	cd infrastructure/scripts && ./status.sh $(ENV) $(REGION)

infra-validate:
	aws cloudformation validate-template --template-body file://infrastructure/infrastructure.yaml

# Utilities
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

clean-data:
	rm -rf data/raw/*
	rm -rf data/processed/*
	rm -rf cache/*

clean-models:
	rm -rf models/*

# Performance
profile:
	python -m cProfile -o profile.stats -m src.sports_prediction.cli predict --sport nba --home-team lakers --away-team warriors
	python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

benchmark:
	python scripts/benchmark.py

# CI/CD
ci-test:
	pytest tests/ --cov=src --cov-report=xml --junitxml=test-results.xml

ci-build:
	docker build -t sports-prediction-bot:$(shell git rev-parse --short HEAD) .

ci-deploy:
	@echo "CI deployment would happen here"

# Development helpers
dev-setup: install-dev setup
	@echo "Development environment setup complete!"

dev-reset: clean clean-data clean-models setup
	@echo "Development environment reset complete!"

# Quick commands
quick-test: format lint test

quick-deploy: docker-build docker-run

# Health checks
health-check:
	curl -f http://localhost:8000/health || exit 1

# Logs
logs-bot:
	docker-compose logs -f sports-prediction-bot

logs-db:
	docker-compose logs -f mongodb redis

logs-monitoring:
	docker-compose logs -f prometheus grafana

# SSL certificate generation (for development)
ssl-cert:
	mkdir -p nginx/ssl
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout nginx/ssl/key.pem \
		-out nginx/ssl/cert.pem \
		-subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Environment management
env-check:
	@echo "Checking environment variables..."
	@python -c "from src.sports_prediction.config.settings import settings; print('✅ Configuration loaded successfully')"

env-template:
	cp .env.example .env.$(ENV)
	@echo "Created .env.$(ENV) from template"

# Database migrations (if using SQL in the future)
migrate:
	@echo "No migrations needed for MongoDB setup"

# API testing
test-api:
	curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{"test": true}'

# Performance monitoring
monitor:
	@echo "Opening monitoring dashboards..."
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000 (admin/admin)"

# Version management
version:
	@python -c "import src.sports_prediction; print(f'Version: {src.sports_prediction.__version__}')"

bump-version:
	@echo "Version bumping would happen here"

# Release management
release: clean test docker-build
	@echo "Release process would happen here"

# Help for specific commands
help-docker:
	@echo "Docker Commands Help:"
	@echo "  docker-build     Build all Docker images"
	@echo "  docker-run       Start all services with Docker Compose"
	@echo "  docker-stop      Stop all running containers"
	@echo "  docker-logs      Follow logs from all containers"
	@echo "  docker-clean     Remove containers and clean up resources"
	@echo "  docker-shell     Open shell in the main application container"

help-dev:
	@echo "Development Commands Help:"
	@echo "  install-dev      Install all development dependencies"
	@echo "  test             Run the test suite"
	@echo "  test-cov         Run tests with coverage reporting"
	@echo "  lint             Run all code quality checks"
	@echo "  format           Auto-format code with black and isort"
	@echo "  pre-commit       Run pre-commit hooks on all files"
