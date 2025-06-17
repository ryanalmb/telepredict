# Sports Prediction Bot - Deployment Guide

This guide provides step-by-step instructions for deploying the Sports Prediction Bot to AWS using CloudFormation.

## 📋 Prerequisites

### Required Tools
- [AWS CLI](https://aws.amazon.com/cli/) v2.0 or later
- [Git](https://git-scm.com/) for version control
- [Docker](https://www.docker.com/) for local testing (optional)
- Bash shell (Linux/macOS/WSL on Windows)

### AWS Requirements
- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Sufficient service limits for the resources

### Required Permissions
Your AWS user/role needs the following permissions:
- CloudFormation: Full access
- EC2: VPC, Subnet, Security Group management
- S3: Bucket creation and management
- DynamoDB: Table creation and management
- ElastiCache: Cluster creation and management
- DocumentDB: Cluster creation and management
- IAM: Role and policy creation
- Secrets Manager: Secret creation and management
- App Runner: Service creation and management

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Environment

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd sports-prediction-bot
   ```

2. **Configure AWS CLI**:
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and default region
   ```

3. **Verify AWS access**:
   ```bash
   aws sts get-caller-identity
   ```

### Step 2: Configure API Keys and Secrets

1. **Obtain required API keys**:
   - **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/botfather)
   - **ESPN API Key**: Register at [ESPN Developer](https://developer.espn.com/)
   - **SportRadar API Key**: Register at [SportRadar](https://developer.sportradar.com/)
   - **Odds API Key**: Register at [The Odds API](https://the-odds-api.com/)

2. **Update parameter files**:
   ```bash
   # For development
   nano infrastructure/parameters/dev.json
   
   # For staging
   nano infrastructure/parameters/staging.json
   
   # For production
   nano infrastructure/parameters/prod.json
   ```

   Replace placeholder values with your actual API keys:
   ```json
   {
     "ParameterKey": "TelegramBotToken",
     "ParameterValue": "YOUR_ACTUAL_BOT_TOKEN"
   }
   ```

### Step 3: Deploy Infrastructure

#### Option A: Using Deployment Script (Recommended)

1. **Deploy to development**:
   ```bash
   ./infrastructure/scripts/deploy.sh dev us-east-1
   ```

2. **Deploy to staging**:
   ```bash
   ./infrastructure/scripts/deploy.sh staging us-east-1
   ```

3. **Deploy to production**:
   ```bash
   ./infrastructure/scripts/deploy.sh prod us-east-1
   ```

#### Option B: Using Makefile

```bash
# Deploy to development
make infra-deploy ENV=dev REGION=us-east-1

# Deploy to staging
make infra-deploy ENV=staging REGION=us-east-1

# Deploy to production
make infra-deploy ENV=prod REGION=us-east-1
```

#### Option C: Manual AWS CLI

```bash
# Validate template
aws cloudformation validate-template \
    --template-body file://infrastructure/infrastructure.yaml

# Create stack
aws cloudformation create-stack \
    --stack-name sports-prediction-bot-dev \
    --template-body file://infrastructure/infrastructure.yaml \
    --parameters file://infrastructure/parameters/dev.json \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1 \
    --tags Key=Environment,Value=dev Key=Project,Value=sports-prediction-bot

# Wait for completion
aws cloudformation wait stack-create-complete \
    --stack-name sports-prediction-bot-dev
```

### Step 4: Verify Deployment

1. **Check stack status**:
   ```bash
   ./infrastructure/scripts/status.sh dev us-east-1
   ```

2. **Get stack outputs**:
   ```bash
   aws cloudformation describe-stacks \
       --stack-name sports-prediction-bot-dev \
       --query 'Stacks[0].Outputs' \
       --output table
   ```

3. **Test resource connectivity**:
   ```bash
   # Test S3 bucket
   aws s3 ls s3://sports-prediction-bot-dev-models-<account-id>
   
   # Test DynamoDB table
   aws dynamodb describe-table \
       --table-name sports-prediction-bot-dev-predictions
   ```

### Step 5: Deploy Application

After infrastructure is ready, deploy your application:

1. **Update App Runner configuration**:
   Use the IAM role ARNs from CloudFormation outputs in your `apprunner.yaml`:
   ```yaml
   apprunner:
     access-role-arn: <APP_RUNNER_ACCESS_ROLE_ARN_FROM_OUTPUTS>
   ```

2. **Deploy to App Runner**:
   ```bash
   # Using AWS CLI
   aws apprunner create-service \
       --service-name sports-prediction-bot-dev \
       --source-configuration file://apprunner.yaml
   ```

### Step 6: Configure Application

1. **Update environment variables**:
   Use the resource endpoints from CloudFormation outputs:
   ```bash
   # Redis endpoint
   REDIS_URL=redis://<REDIS_ENDPOINT>:6379
   
   # DocumentDB endpoint
   MONGODB_URL=mongodb://admin:<password>@<DOCDB_ENDPOINT>:27017/sports_predictions
   
   # S3 bucket
   AWS_S3_BUCKET=<MODELS_BUCKET_NAME>
   
   # DynamoDB table
   AWS_DYNAMODB_TABLE=<PREDICTIONS_TABLE_NAME>
   ```

2. **Retrieve database password**:
   ```bash
   aws secretsmanager get-secret-value \
       --secret-id sports-prediction-bot-dev-docdb-credentials \
       --query 'SecretString' \
       --output text | jq -r '.password'
   ```

## 🔍 Post-Deployment Verification

### Health Checks

1. **Infrastructure health**:
   ```bash
   ./infrastructure/scripts/status.sh dev us-east-1
   ```

2. **Application health**:
   ```bash
   # Check App Runner service
   aws apprunner describe-service \
       --service-arn <SERVICE_ARN>
   
   # Test application endpoint
   curl https://<app-runner-url>/health
   ```

3. **Database connectivity**:
   ```bash
   # Test Redis
   redis-cli -h <redis-endpoint> ping
   
   # Test DocumentDB (requires VPC access)
   mongo --host <docdb-endpoint>:27017 \
         --username admin \
         --password <password> \
         --ssl \
         --sslCAFile rds-combined-ca-bundle.pem
   ```

### Monitoring Setup

1. **CloudWatch dashboards**:
   - App Runner metrics
   - Database performance
   - Application logs

2. **Alarms**:
   - High error rates
   - Database connection issues
   - Resource utilization

## 🔧 Environment-Specific Configurations

### Development Environment
- Minimal resources for cost optimization
- Relaxed security for easier debugging
- Single AZ deployment

### Staging Environment
- Production-like setup for testing
- Moderate resource allocation
- Multi-AZ for reliability testing

### Production Environment
- High availability and performance
- Maximum security configurations
- Auto-scaling enabled
- Comprehensive monitoring

## 🚨 Troubleshooting

### Common Issues

1. **Stack creation fails**:
   ```bash
   # Check events
   aws cloudformation describe-stack-events \
       --stack-name sports-prediction-bot-dev
   
   # Common causes:
   # - Insufficient permissions
   # - Service limits exceeded
   # - Invalid parameter values
   ```

2. **Resource creation timeouts**:
   ```bash
   # Check specific resource status
   aws cloudformation describe-stack-resources \
       --stack-name sports-prediction-bot-dev
   ```

3. **Application deployment fails**:
   ```bash
   # Check App Runner logs
   aws logs describe-log-groups \
       --log-group-name-prefix "/aws/apprunner"
   ```

### Recovery Procedures

1. **Rollback failed deployment**:
   ```bash
   aws cloudformation cancel-update-stack \
       --stack-name sports-prediction-bot-dev
   ```

2. **Delete and recreate**:
   ```bash
   ./infrastructure/scripts/destroy.sh dev us-east-1
   ./infrastructure/scripts/deploy.sh dev us-east-1
   ```

## 🔒 Security Considerations

### Best Practices
- Use least privilege IAM policies
- Enable encryption for all data stores
- Use VPC for network isolation
- Store secrets in AWS Secrets Manager
- Enable CloudTrail for audit logging

### Security Checklist
- [ ] All API keys stored in Secrets Manager
- [ ] Database encryption enabled
- [ ] VPC security groups properly configured
- [ ] IAM roles follow least privilege
- [ ] CloudTrail logging enabled
- [ ] Regular security updates scheduled

## 💰 Cost Optimization

### Cost Monitoring
```bash
# Check estimated costs
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

### Optimization Tips
- Use appropriate instance sizes for each environment
- Enable auto-scaling to handle variable loads
- Schedule non-production environments to run only during business hours
- Use Reserved Instances for predictable workloads
- Monitor and optimize data transfer costs

## 📞 Support and Maintenance

### Regular Maintenance
- Monitor CloudWatch metrics and alarms
- Review and rotate API keys quarterly
- Update infrastructure templates for security patches
- Backup critical data regularly
- Test disaster recovery procedures

### Getting Help
- Check AWS CloudFormation console for detailed error messages
- Review CloudWatch logs for application issues
- Consult AWS documentation for service-specific guidance
- Use AWS Support for complex issues (if you have a support plan)

---

**Next Steps**: After successful deployment, refer to the [Infrastructure README](README.md) for ongoing management and the main [README](../README.md) for application usage.
