#!/bin/bash

# Sports Prediction Bot - CloudFormation Destruction Script
# Usage: ./destroy.sh [environment] [region]
# Example: ./destroy.sh dev us-east-1

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

print_warning "⚠️  DANGER: This will destroy ALL resources in the $ENVIRONMENT environment!"
print_status "Environment: $ENVIRONMENT"
print_status "Region: $REGION"
print_status "Stack Name: $STACK_NAME"

# Check if stack exists
STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [[ "$STACK_EXISTS" == "DOES_NOT_EXIST" ]]; then
    print_warning "Stack $STACK_NAME does not exist."
    exit 0
fi

# Display stack resources
print_status "Resources that will be deleted:"
aws cloudformation list-stack-resources \
    --stack-name "$STACK_NAME" \
    --query 'StackResourceSummaries[].{Type:ResourceType,LogicalId:LogicalResourceId,Status:ResourceStatus}' \
    --output table

# Confirmation prompts
echo
print_warning "This action cannot be undone!"
read -p "Are you sure you want to delete the $ENVIRONMENT environment? Type 'DELETE' to confirm: " -r
if [[ $REPLY != "DELETE" ]]; then
    print_status "Destruction cancelled."
    exit 0
fi

read -p "Last chance! Type the environment name '$ENVIRONMENT' to proceed: " -r
if [[ $REPLY != "$ENVIRONMENT" ]]; then
    print_status "Destruction cancelled."
    exit 0
fi

# Disable termination protection if enabled
print_status "Disabling termination protection..."
aws cloudformation update-termination-protection \
    --stack-name "$STACK_NAME" \
    --no-enable-termination-protection || true

# Empty S3 bucket before deletion (CloudFormation can't delete non-empty buckets)
print_status "Emptying S3 buckets..."
BUCKET_NAME=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --logical-resource-id "ModelsBucket" \
    --query 'StackResources[0].PhysicalResourceId' \
    --output text 2>/dev/null || echo "")

if [[ -n "$BUCKET_NAME" && "$BUCKET_NAME" != "None" ]]; then
    print_status "Emptying bucket: $BUCKET_NAME"
    aws s3 rm s3://"$BUCKET_NAME" --recursive || true
    
    # Delete all versions if versioning is enabled
    aws s3api list-object-versions \
        --bucket "$BUCKET_NAME" \
        --query 'Versions[].{Key:Key,VersionId:VersionId}' \
        --output text | while read key version; do
        if [[ -n "$key" && -n "$version" ]]; then
            aws s3api delete-object --bucket "$BUCKET_NAME" --key "$key" --version-id "$version" || true
        fi
    done
    
    # Delete delete markers
    aws s3api list-object-versions \
        --bucket "$BUCKET_NAME" \
        --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' \
        --output text | while read key version; do
        if [[ -n "$key" && -n "$version" ]]; then
            aws s3api delete-object --bucket "$BUCKET_NAME" --key "$key" --version-id "$version" || true
        fi
    done
fi

# Delete the stack
print_status "Deleting CloudFormation stack: $STACK_NAME"
aws cloudformation delete-stack --stack-name "$STACK_NAME"

print_status "Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME"

if [[ $? -eq 0 ]]; then
    print_success "Stack deleted successfully!"
else
    print_error "Stack deletion failed or timed out. Check the AWS Console for details."
    exit 1
fi

print_success "Environment $ENVIRONMENT has been completely destroyed."
