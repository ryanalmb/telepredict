#!/bin/bash

# Deploy Test Environment Script
# Creates and manages remote testing environments for Sports Prediction Bot

set -e

# Configuration
PROJECT_NAME="sports-prediction-bot"
REGION="us-east-1"
INSTANCE_TYPE="t3.medium"
KEY_NAME="sports-bot-test-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  create-ec2     Create EC2 test instance"
    echo "  test-docker    Run Docker-based tests"
    echo "  test-github    Trigger GitHub Actions"
    echo "  cleanup        Clean up test resources"
    echo "  status         Check test environment status"
    echo ""
    echo "Options:"
    echo "  --region REGION        AWS region (default: us-east-1)"
    echo "  --instance-type TYPE   EC2 instance type (default: t3.medium)"
    echo "  --key-name NAME        EC2 key pair name"
    echo "  --s3-bucket BUCKET     S3 bucket for test results"
    echo "  --sns-topic TOPIC      SNS topic for notifications"
    echo ""
    echo "Examples:"
    echo "  $0 create-ec2 --key-name my-key --s3-bucket my-test-bucket"
    echo "  $0 test-docker"
    echo "  $0 cleanup"
}

create_ec2_test_instance() {
    print_status "Creating EC2 test instance..."
    
    # Check if key pair exists
    if ! aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" >/dev/null 2>&1; then
        print_error "Key pair '$KEY_NAME' not found. Please create it first:"
        echo "aws ec2 create-key-pair --key-name $KEY_NAME --region $REGION --query 'KeyMaterial' --output text > $KEY_NAME.pem"
        exit 1
    fi
    
    # Get latest Amazon Linux 2 AMI
    AMI_ID=$(aws ec2 describe-images \
        --owners amazon \
        --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text \
        --region "$REGION")
    
    print_status "Using AMI: $AMI_ID"
    
    # Create security group
    SG_ID=$(aws ec2 create-security-group \
        --group-name "${PROJECT_NAME}-test-sg" \
        --description "Security group for Sports Prediction Bot testing" \
        --region "$REGION" \
        --query 'GroupId' \
        --output text 2>/dev/null || \
        aws ec2 describe-security-groups \
        --group-names "${PROJECT_NAME}-test-sg" \
        --region "$REGION" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
    
    # Add SSH access
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region "$REGION" 2>/dev/null || true
    
    # Create user data script
    USER_DATA=$(base64 -w 0 remote_testing/ec2_test_script.sh)
    
    # Launch instance
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --count 1 \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-group-ids "$SG_ID" \
        --user-data "$USER_DATA" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_NAME}-test},{Key=Project,Value=${PROJECT_NAME}}]" \
        --region "$REGION" \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    print_success "Instance created: $INSTANCE_ID"
    
    # Wait for instance to be running
    print_status "Waiting for instance to be running..."
    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
    
    # Get public IP
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    print_success "Instance is running at: $PUBLIC_IP"
    print_status "SSH command: ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"
    print_status "Test logs: ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP 'tail -f /var/log/sports-bot-test.log'"
    
    # Save instance info
    echo "{\"instance_id\": \"$INSTANCE_ID\", \"public_ip\": \"$PUBLIC_IP\", \"region\": \"$REGION\"}" > test_instance.json
}

test_docker() {
    print_status "Running Docker-based tests..."
    
    # Build test image
    print_status "Building test Docker image..."
    docker build -f remote_testing/Dockerfile.test -t sports-prediction-bot:test .
    
    # Run tests
    print_status "Running tests in Docker container..."
    docker run --rm \
        -v "$(pwd)/test_results:/app/test_results" \
        sports-prediction-bot:test
    
    print_success "Docker tests completed"
    
    # Run development container for debugging
    read -p "Start development container for debugging? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Starting development container..."
        docker run -it --rm \
            -p 8000:8000 \
            -p 6379:6379 \
            -p 27017:27017 \
            -v "$(pwd):/app" \
            --target dev \
            sports-prediction-bot:test
    fi
}

test_github_actions() {
    print_status "Triggering GitHub Actions workflow..."
    
    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) not found. Please install it first."
        print_status "Install: https://cli.github.com/"
        exit 1
    fi
    
    # Trigger workflow
    gh workflow run comprehensive-test.yml
    
    print_success "GitHub Actions workflow triggered"
    print_status "View results: gh run list"
    print_status "Or visit: https://github.com/$(gh repo view --json owner,name -q '.owner.login + \"/\" + .name')/actions"
}

cleanup_resources() {
    print_status "Cleaning up test resources..."
    
    # Clean up EC2 instance
    if [ -f "test_instance.json" ]; then
        INSTANCE_ID=$(jq -r '.instance_id' test_instance.json)
        REGION=$(jq -r '.region' test_instance.json)
        
        print_status "Terminating instance: $INSTANCE_ID"
        aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region "$REGION"
        
        # Wait for termination
        aws ec2 wait instance-terminated --instance-ids "$INSTANCE_ID" --region "$REGION"
        
        rm test_instance.json
        print_success "Instance terminated"
    fi
    
    # Clean up Docker images
    print_status "Cleaning up Docker images..."
    docker rmi sports-prediction-bot:test 2>/dev/null || true
    
    # Clean up test files
    rm -f test_results.json test_output.log test_report.html
    
    print_success "Cleanup completed"
}

check_status() {
    print_status "Checking test environment status..."
    
    # Check EC2 instance
    if [ -f "test_instance.json" ]; then
        INSTANCE_ID=$(jq -r '.instance_id' test_instance.json)
        REGION=$(jq -r '.region' test_instance.json)
        
        STATUS=$(aws ec2 describe-instances \
            --instance-ids "$INSTANCE_ID" \
            --region "$REGION" \
            --query 'Reservations[0].Instances[0].State.Name' \
            --output text 2>/dev/null || echo "not-found")
        
        print_status "EC2 Instance $INSTANCE_ID: $STATUS"
    else
        print_status "No EC2 test instance found"
    fi
    
    # Check Docker images
    if docker images sports-prediction-bot:test --format "table {{.Repository}}:{{.Tag}}" | grep -q "sports-prediction-bot:test"; then
        print_status "Docker test image: Available"
    else
        print_status "Docker test image: Not built"
    fi
    
    # Check GitHub Actions
    if command -v gh &> /dev/null; then
        print_status "Recent GitHub Actions runs:"
        gh run list --limit 5 --workflow comprehensive-test.yml 2>/dev/null || print_status "No GitHub Actions runs found"
    fi
}

# Parse command line arguments
COMMAND=""
while [[ $# -gt 0 ]]; do
    case $1 in
        create-ec2|test-docker|test-github|cleanup|status)
            COMMAND="$1"
            shift
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --instance-type)
            INSTANCE_TYPE="$2"
            shift 2
            ;;
        --key-name)
            KEY_NAME="$2"
            shift 2
            ;;
        --s3-bucket)
            export S3_BUCKET="$2"
            shift 2
            ;;
        --sns-topic)
            export SNS_TOPIC="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Execute command
case $COMMAND in
    create-ec2)
        create_ec2_test_instance
        ;;
    test-docker)
        test_docker
        ;;
    test-github)
        test_github_actions
        ;;
    cleanup)
        cleanup_resources
        ;;
    status)
        check_status
        ;;
    "")
        print_error "No command specified"
        show_usage
        exit 1
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
