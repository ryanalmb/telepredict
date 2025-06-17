#!/bin/bash

# Deploy Sports Prediction Bot to AWS App Runner
# Usage: ./deploy-apprunner.sh

set -e

echo "🚀 Deploying Sports Prediction Bot to AWS App Runner"

# Check if required environment variables are set
required_vars=(
    "TELEGRAM_BOT_TOKEN"
    "TELEGRAM_WEBHOOK_URL"
    "AWS_REGION"
)

echo "🔍 Checking required environment variables..."
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set"
        echo "Please set the required environment variables:"
        echo "export TELEGRAM_BOT_TOKEN='your_bot_token'"
        echo "export TELEGRAM_WEBHOOK_URL='your_webhook_url'"
        echo "export AWS_REGION='us-east-1'"
        exit 1
    else
        echo "✅ $var is set"
    fi
done

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure'"
    exit 1
fi

echo "✅ AWS CLI is configured"

# Set default values for optional variables
export AWS_S3_BUCKET=${AWS_S3_BUCKET:-"sports-prediction-models-$(date +%s)"}
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379"}
export MONGODB_URL=${MONGODB_URL:-"mongodb://localhost:27017/sports_predictions"}
export SECRET_KEY=${SECRET_KEY:-"$(openssl rand -hex 32)"}

echo "📋 Deployment Configuration:"
echo "  AWS Region: $AWS_REGION"
echo "  S3 Bucket: $AWS_S3_BUCKET"
echo "  Webhook URL: $TELEGRAM_WEBHOOK_URL"

# Create App Runner service configuration
cat > apprunner-service.json << EOF
{
    "ServiceName": "sports-prediction-bot",
    "SourceConfiguration": {
        "ImageRepository": {
            "ImageIdentifier": "public.ecr.aws/docker/library/python:3.11-slim",
            "ImageConfiguration": {
                "Port": "8000",
                "RuntimeEnvironmentVariables": {
                    "PORT": "8000",
                    "ENVIRONMENT": "production",
                    "DEBUG": "False",
                    "LOG_LEVEL": "INFO",
                    "TELEGRAM_BOT_TOKEN": "$TELEGRAM_BOT_TOKEN",
                    "TELEGRAM_WEBHOOK_URL": "$TELEGRAM_WEBHOOK_URL",
                    "AWS_REGION": "$AWS_REGION",
                    "AWS_S3_BUCKET": "$AWS_S3_BUCKET",
                    "REDIS_URL": "$REDIS_URL",
                    "MONGODB_URL": "$MONGODB_URL",
                    "SECRET_KEY": "$SECRET_KEY",
                    "SUPPORTED_SPORTS": "nba,nfl,mlb,nhl,mls,premier_league,la_liga,bundesliga,serie_a"
                },
                "StartCommand": "python -m src.sports_prediction.cli run-bot --production --port 8000"
            },
            "ImageRepositoryType": "ECR_PUBLIC"
        },
        "AutoDeploymentsEnabled": false
    },
    "InstanceConfiguration": {
        "Cpu": "1024",
        "Memory": "2048"
    },
    "HealthCheckConfiguration": {
        "Protocol": "HTTP",
        "Path": "/health",
        "Interval": 30,
        "Timeout": 10,
        "HealthyThreshold": 2,
        "UnhealthyThreshold": 5
    }
}
EOF

echo "📦 Creating App Runner service..."

# Create the service
SERVICE_ARN=$(aws apprunner create-service \
    --cli-input-json file://apprunner-service.json \
    --query 'Service.ServiceArn' \
    --output text)

if [ $? -eq 0 ]; then
    echo "✅ App Runner service created successfully!"
    echo "📋 Service ARN: $SERVICE_ARN"
    
    # Wait for service to be ready
    echo "⏳ Waiting for service to be ready..."
    aws apprunner wait service-running --service-arn "$SERVICE_ARN"
    
    # Get service URL
    SERVICE_URL=$(aws apprunner describe-service \
        --service-arn "$SERVICE_ARN" \
        --query 'Service.ServiceUrl' \
        --output text)
    
    echo "🎉 Deployment completed!"
    echo "🌐 Service URL: https://$SERVICE_URL"
    echo "🔗 Health Check: https://$SERVICE_URL/health"
    echo "📡 Webhook URL: https://$SERVICE_URL/webhook"
    
    # Set the webhook URL for Telegram
    echo "🔧 Setting Telegram webhook..."
    curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
         -H "Content-Type: application/json" \
         -d "{\"url\": \"https://$SERVICE_URL/webhook\"}"
    
    echo ""
    echo "✅ Telegram webhook configured!"
    echo "🤖 Your bot should now be running on AWS App Runner!"
    
else
    echo "❌ Failed to create App Runner service"
    exit 1
fi

# Cleanup
rm -f apprunner-service.json

echo "🧹 Cleanup completed"
