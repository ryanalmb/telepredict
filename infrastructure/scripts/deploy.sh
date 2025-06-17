#!/bin/bash

# Sports Prediction Bot - CloudFormation Deployment Script
# Usage: ./deploy.sh [environment] [region]
# Example: ./deploy.sh dev us-east-1

set -e

# Default values
ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
PROJECT_NAME="sports-prediction-bot"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod."
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Set AWS region
export AWS_DEFAULT_REGION=$REGION

print_status "Deploying Sports Prediction Bot infrastructure..."
print_status "Environment: $ENVIRONMENT"
print_status "Region: $REGION"
print_status "Stack Name: $STACK_NAME"

# Check if parameter file exists
PARAM_FILE="infrastructure/parameters/${ENVIRONMENT}.json"
if [[ ! -f "$PARAM_FILE" ]]; then
    print_error "Parameter file not found: $PARAM_FILE"
    exit 1
fi

# Validate CloudFormation template
print_status "Validating CloudFormation template..."
if aws cloudformation validate-template --template-body file://infrastructure/infrastructure.yaml > /dev/null; then
    print_success "Template validation passed"
else
    print_error "Template validation failed"
    exit 1
fi

# Check if stack exists
STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [[ "$STACK_EXISTS" == "DOES_NOT_EXIST" ]]; then
    print_status "Creating new stack: $STACK_NAME"
    
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body file://infrastructure/infrastructure.yaml \
        --parameters file://"$PARAM_FILE" \
        --capabilities CAPABILITY_NAMED_IAM \
        --tags Key=Environment,Value="$ENVIRONMENT" Key=Project,Value="$PROJECT_NAME" \
        --enable-termination-protection
    
    print_status "Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME"
    
    if [[ $? -eq 0 ]]; then
        print_success "Stack created successfully!"
    else
        print_error "Stack creation failed!"
        exit 1
    fi
else
    print_status "Updating existing stack: $STACK_NAME"
    
    # Create change set
    CHANGE_SET_NAME="${STACK_NAME}-$(date +%Y%m%d-%H%M%S)"
    
    aws cloudformation create-change-set \
        --stack-name "$STACK_NAME" \
        --template-body file://infrastructure/infrastructure.yaml \
        --parameters file://"$PARAM_FILE" \
        --capabilities CAPABILITY_NAMED_IAM \
        --change-set-name "$CHANGE_SET_NAME"
    
    print_status "Waiting for change set to be created..."
    aws cloudformation wait change-set-create-complete \
        --stack-name "$STACK_NAME" \
        --change-set-name "$CHANGE_SET_NAME"
    
    # Describe changes
    print_status "Proposed changes:"
    aws cloudformation describe-change-set \
        --stack-name "$STACK_NAME" \
        --change-set-name "$CHANGE_SET_NAME" \
        --query 'Changes[].{Action:Action,Resource:ResourceChange.LogicalResourceId,Type:ResourceChange.ResourceType}' \
        --output table
    
    # Confirm execution
    read -p "Do you want to execute these changes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Executing change set..."
        aws cloudformation execute-change-set \
            --stack-name "$STACK_NAME" \
            --change-set-name "$CHANGE_SET_NAME"
        
        print_status "Waiting for stack update to complete..."
        aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME"
        
        if [[ $? -eq 0 ]]; then
            print_success "Stack updated successfully!"
        else
            print_error "Stack update failed!"
            exit 1
        fi
    else
        print_warning "Change set execution cancelled"
        aws cloudformation delete-change-set \
            --stack-name "$STACK_NAME" \
            --change-set-name "$CHANGE_SET_NAME"
        exit 0
    fi
fi

# Display stack outputs
print_status "Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}' \
    --output table

print_success "Deployment completed successfully!"
print_status "Next steps:"
echo "1. Update your .env file with the output values"
echo "2. Deploy your App Runner service using the provided IAM roles"
echo "3. Configure your application to use the created resources"
