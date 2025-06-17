#!/bin/bash

# Sports Prediction Bot - CloudFormation Status Script
# Usage: ./status.sh [environment] [region]
# Example: ./status.sh dev us-east-1

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

print_status "Checking status for Sports Prediction Bot infrastructure..."
print_status "Environment: $ENVIRONMENT"
print_status "Region: $REGION"
print_status "Stack Name: $STACK_NAME"
echo

# Check if stack exists
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [[ "$STACK_STATUS" == "DOES_NOT_EXIST" ]]; then
    print_warning "Stack $STACK_NAME does not exist."
    exit 0
fi

# Display stack information
print_status "Stack Status: $STACK_STATUS"
echo

# Stack details
print_status "Stack Details:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].{Status:StackStatus,Created:CreationTime,Updated:LastUpdatedTime,TerminationProtection:EnableTerminationProtection}' \
    --output table
echo

# Stack outputs
print_status "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue,Description:Description}' \
    --output table
echo

# Stack resources
print_status "Stack Resources:"
aws cloudformation list-stack-resources \
    --stack-name "$STACK_NAME" \
    --query 'StackResourceSummaries[].{Type:ResourceType,LogicalId:LogicalResourceId,Status:ResourceStatus,Updated:LastUpdatedTimestamp}' \
    --output table
echo

# Check for any failed resources
FAILED_RESOURCES=$(aws cloudformation list-stack-resources \
    --stack-name "$STACK_NAME" \
    --query 'StackResourceSummaries[?contains(ResourceStatus, `FAILED`)].LogicalResourceId' \
    --output text)

if [[ -n "$FAILED_RESOURCES" ]]; then
    print_error "Failed Resources Found:"
    echo "$FAILED_RESOURCES"
    echo
    
    print_status "Resource Events (last 10):"
    aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --query 'StackEvents[0:10].{Time:Timestamp,Resource:LogicalResourceId,Status:ResourceStatus,Reason:ResourceStatusReason}' \
        --output table
else
    print_success "All resources are in a healthy state."
fi

# Check specific service health
print_status "Service Health Checks:"

# Check S3 bucket
BUCKET_NAME=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --logical-resource-id "ModelsBucket" \
    --query 'StackResources[0].PhysicalResourceId' \
    --output text 2>/dev/null || echo "")

if [[ -n "$BUCKET_NAME" && "$BUCKET_NAME" != "None" ]]; then
    if aws s3 ls "s3://$BUCKET_NAME" &>/dev/null; then
        print_success "✓ S3 Bucket ($BUCKET_NAME) is accessible"
    else
        print_error "✗ S3 Bucket ($BUCKET_NAME) is not accessible"
    fi
fi

# Check DynamoDB table
TABLE_NAME=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --logical-resource-id "PredictionsTable" \
    --query 'StackResources[0].PhysicalResourceId' \
    --output text 2>/dev/null || echo "")

if [[ -n "$TABLE_NAME" && "$TABLE_NAME" != "None" ]]; then
    TABLE_STATUS=$(aws dynamodb describe-table --table-name "$TABLE_NAME" --query 'Table.TableStatus' --output text 2>/dev/null || echo "ERROR")
    if [[ "$TABLE_STATUS" == "ACTIVE" ]]; then
        print_success "✓ DynamoDB Table ($TABLE_NAME) is active"
    else
        print_warning "⚠ DynamoDB Table ($TABLE_NAME) status: $TABLE_STATUS"
    fi
fi

# Check Redis cluster
REDIS_ID=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --logical-resource-id "RedisCluster" \
    --query 'StackResources[0].PhysicalResourceId' \
    --output text 2>/dev/null || echo "")

if [[ -n "$REDIS_ID" && "$REDIS_ID" != "None" ]]; then
    REDIS_STATUS=$(aws elasticache describe-replication-groups --replication-group-id "$REDIS_ID" --query 'ReplicationGroups[0].Status' --output text 2>/dev/null || echo "ERROR")
    if [[ "$REDIS_STATUS" == "available" ]]; then
        print_success "✓ Redis Cluster ($REDIS_ID) is available"
    else
        print_warning "⚠ Redis Cluster ($REDIS_ID) status: $REDIS_STATUS"
    fi
fi

# Check DocumentDB cluster
DOCDB_ID=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --logical-resource-id "DocumentDBCluster" \
    --query 'StackResources[0].PhysicalResourceId' \
    --output text 2>/dev/null || echo "")

if [[ -n "$DOCDB_ID" && "$DOCDB_ID" != "None" ]]; then
    DOCDB_STATUS=$(aws docdb describe-db-clusters --db-cluster-identifier "$DOCDB_ID" --query 'DBClusters[0].Status' --output text 2>/dev/null || echo "ERROR")
    if [[ "$DOCDB_STATUS" == "available" ]]; then
        print_success "✓ DocumentDB Cluster ($DOCDB_ID) is available"
    else
        print_warning "⚠ DocumentDB Cluster ($DOCDB_ID) status: $DOCDB_STATUS"
    fi
fi

echo
print_status "Status check completed."
