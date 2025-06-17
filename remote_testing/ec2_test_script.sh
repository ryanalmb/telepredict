#!/bin/bash

# EC2 User Data Script for Sports Prediction Bot Testing
# This script sets up a complete testing environment on a fresh EC2 instance

set -e

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/sports-bot-test.log
}

log "Starting Sports Prediction Bot test setup on EC2"

# Update system
log "Updating system packages..."
yum update -y

# Install required packages
log "Installing system dependencies..."
yum install -y git python3 python3-pip docker redis mongodb-org

# Install Python 3.11 from source if needed
log "Setting up Python environment..."
python3 -m pip install --upgrade pip

# Start services
log "Starting services..."
systemctl start docker
systemctl enable docker
systemctl start redis
systemctl enable redis
systemctl start mongod
systemctl enable mongod

# Add ec2-user to docker group
usermod -a -G docker ec2-user

# Clone the repository (assuming it's public or using deploy keys)
log "Cloning repository..."
cd /home/ec2-user
git clone https://github.com/YOUR_USERNAME/sports-prediction-bot.git
cd sports-prediction-bot
chown -R ec2-user:ec2-user /home/ec2-user/sports-prediction-bot

# Switch to ec2-user for the rest
sudo -u ec2-user bash << 'EOF'

cd /home/ec2-user/sports-prediction-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create test environment file
cat > .env << 'ENVEOF'
TELEGRAM_BOT_TOKEN=test_token_123456
ESPN_API_KEY=test_espn_key
SPORTRADAR_API_KEY=test_sportradar_key
ODDS_API_KEY=test_odds_key
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017/test
LOG_LEVEL=INFO
DEBUG=True
TESTING=True
AWS_REGION=us-east-1
ENVEOF

# Run comprehensive tests
echo "Running comprehensive test suite..."
python remote_testing/full_test_suite.py > test_output.log 2>&1

# Test Docker build
echo "Testing Docker build..."
docker build -t sports-prediction-bot:test . >> test_output.log 2>&1

# Test CLI commands
echo "Testing CLI commands..."
python -m src.sports_prediction.cli --help >> test_output.log 2>&1
python -m src.sports_prediction.cli setup >> test_output.log 2>&1

# Generate final report
cat > test_report.html << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <title>Sports Prediction Bot - EC2 Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .success { color: green; }
        .error { color: red; }
        .warning { color: orange; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Sports Prediction Bot - EC2 Test Report</h1>
        <p><strong>Test Date:</strong> $(date)</p>
        <p><strong>Instance:</strong> $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>
        <p><strong>Region:</strong> $(curl -s http://169.254.169.254/latest/meta-data/placement/region)</p>
    </div>
    
    <h2>Test Results</h2>
    <pre>$(cat test_output.log)</pre>
    
    <h2>System Information</h2>
    <pre>
Python Version: $(python --version)
Docker Version: $(docker --version)
Redis Status: $(systemctl is-active redis)
MongoDB Status: $(systemctl is-active mongod)
Disk Usage: $(df -h /)
Memory Usage: $(free -h)
    </pre>
    
    <h2>Test Files</h2>
    <ul>
        <li><a href="test_results.json">Detailed Test Results (JSON)</a></li>
        <li><a href="test_output.log">Full Test Output</a></li>
    </ul>
</body>
</html>
HTMLEOF

# Upload results to S3 if configured
if [ -n "$S3_BUCKET" ]; then
    echo "Uploading results to S3..."
    aws s3 cp test_report.html s3://$S3_BUCKET/test-reports/$(date +%Y%m%d-%H%M%S)/
    aws s3 cp test_results.json s3://$S3_BUCKET/test-reports/$(date +%Y%m%d-%H%M%S)/
    aws s3 cp test_output.log s3://$S3_BUCKET/test-reports/$(date +%Y%m%d-%H%M%S)/
fi

# Send notification if SNS topic is configured
if [ -n "$SNS_TOPIC" ]; then
    PASS_COUNT=$(grep -c "PASSED" test_output.log || echo "0")
    FAIL_COUNT=$(grep -c "FAILED" test_output.log || echo "0")
    
    aws sns publish \
        --topic-arn "$SNS_TOPIC" \
        --subject "Sports Prediction Bot Test Results" \
        --message "EC2 Test Completed: $PASS_COUNT passed, $FAIL_COUNT failed. Instance: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)"
fi

echo "Test completed. Results available in test_report.html"

EOF

log "EC2 test setup completed"
