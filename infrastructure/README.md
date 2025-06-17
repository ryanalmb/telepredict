# Sports Prediction Bot - AWS Infrastructure

This directory contains the complete AWS infrastructure setup for the Sports Prediction Bot using CloudFormation.

## 🏗️ Architecture Overview

The infrastructure includes:

- **VPC with public/private subnets** across 2 AZs
- **S3 bucket** for ML model storage
- **DynamoDB table** for predictions data
- **ElastiCache Redis** for caching
- **DocumentDB** for MongoDB-compatible database
- **IAM roles** for App Runner service
- **VPC Connector** for App Runner networking
- **Secrets Manager** for secure credential storage

## 📁 Directory Structure

```
infrastructure/
├── infrastructure.yaml          # Main CloudFormation template
├── parameters/                  # Environment-specific parameters
│   ├── dev.json                # Development environment
│   ├── staging.json            # Staging environment
│   └── prod.json               # Production environment
├── scripts/                    # Deployment and management scripts
│   ├── deploy.sh              # Deploy infrastructure
│   ├── destroy.sh             # Destroy infrastructure
│   └── status.sh              # Check infrastructure status
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** installed and configured
2. **AWS credentials** with appropriate permissions
3. **Bash shell** (Linux/macOS/WSL)

### 1. Configure Parameters

Edit the parameter files in `parameters/` directory:

```bash
# Edit development parameters
nano infrastructure/parameters/dev.json

# Edit staging parameters
nano infrastructure/parameters/staging.json

# Edit production parameters
nano infrastructure/parameters/prod.json
```

Replace the placeholder values with your actual API keys and tokens:
- `TELEGRAM_BOT_TOKEN`
- `ESPN_API_KEY`
- `SPORTRADAR_API_KEY`
- `ODDS_API_KEY`

### 2. Deploy Infrastructure

#### Using Scripts (Recommended)

```bash
# Deploy to development
./infrastructure/scripts/deploy.sh dev us-east-1

# Deploy to staging
./infrastructure/scripts/deploy.sh staging us-east-1

# Deploy to production
./infrastructure/scripts/deploy.sh prod us-east-1
```

#### Using Makefile

```bash
# Deploy to development
make infra-deploy ENV=dev REGION=us-east-1

# Deploy to staging
make infra-deploy ENV=staging REGION=us-east-1

# Deploy to production
make infra-deploy ENV=prod REGION=us-east-1
```

#### Using AWS CLI Directly

```bash
# Validate template
aws cloudformation validate-template --template-body file://infrastructure/infrastructure.yaml

# Deploy stack
aws cloudformation create-stack \
    --stack-name sports-prediction-bot-dev \
    --template-body file://infrastructure/infrastructure.yaml \
    --parameters file://infrastructure/parameters/dev.json \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
```

### 3. Check Status

```bash
# Check infrastructure status
./infrastructure/scripts/status.sh dev us-east-1

# Or using Makefile
make infra-status ENV=dev REGION=us-east-1
```

### 4. Update Application Configuration

After deployment, update your application configuration with the output values:

```bash
# Get stack outputs
aws cloudformation describe-stacks \
    --stack-name sports-prediction-bot-dev \
    --query 'Stacks[0].Outputs' \
    --output table
```

## 🔧 Configuration

### Environment Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `Environment` | Environment name | `dev`, `staging`, `prod` |
| `ProjectName` | Project name for resource naming | `sports-prediction-bot` |
| `VpcCidr` | CIDR block for VPC | `10.0.0.0/16` |
| `TelegramBotToken` | Telegram Bot Token | `123456:ABC-DEF...` |
| `EspnApiKey` | ESPN API Key | `your-espn-key` |
| `SportradarApiKey` | Sportradar API Key | `your-sportradar-key` |
| `OddsApiKey` | Odds API Key | `your-odds-key` |

### Environment Mappings

The template automatically configures resources based on environment:

| Environment | Redis Instance | DocumentDB Instance | Auto Scaling |
|-------------|----------------|---------------------|--------------|
| `dev` | `cache.t3.micro` | `db.t3.medium` | 1-3 instances |
| `staging` | `cache.t3.small` | `db.r5.large` | 1-5 instances |
| `prod` | `cache.r6g.large` | `db.r5.xlarge` | 2-10 instances |

## 📊 Resources Created

### Networking
- **VPC** with DNS support
- **2 Public Subnets** across different AZs
- **2 Private Subnets** across different AZs
- **Internet Gateway** for public access
- **NAT Gateway** for private subnet internet access
- **Route Tables** and associations
- **Security Groups** for services

### Storage & Database
- **S3 Bucket** with encryption and versioning
- **DynamoDB Table** with GSI and point-in-time recovery
- **ElastiCache Redis** cluster with encryption
- **DocumentDB** cluster with automated backups

### Security & Access
- **IAM Roles** for App Runner service
- **Secrets Manager** for secure credential storage
- **VPC Connector** for App Runner networking

## 🔍 Monitoring & Management

### Check Infrastructure Status

```bash
# Comprehensive status check
./infrastructure/scripts/status.sh dev us-east-1

# Check specific resources
aws cloudformation list-stack-resources --stack-name sports-prediction-bot-dev
```

### View Logs

```bash
# CloudFormation events
aws cloudformation describe-stack-events --stack-name sports-prediction-bot-dev

# Resource-specific logs
aws logs describe-log-groups --log-group-name-prefix "/aws/apprunner"
```

### Cost Monitoring

```bash
# Estimate monthly costs
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

## 🗑️ Cleanup

### Destroy Infrastructure

⚠️ **Warning**: This will permanently delete all resources and data!

```bash
# Using script (recommended)
./infrastructure/scripts/destroy.sh dev us-east-1

# Using Makefile
make infra-destroy ENV=dev REGION=us-east-1

# Using AWS CLI
aws cloudformation delete-stack --stack-name sports-prediction-bot-dev
```

## 🔒 Security Best Practices

1. **Secrets Management**: All sensitive data is stored in AWS Secrets Manager
2. **Encryption**: All data is encrypted at rest and in transit
3. **Network Security**: Private subnets for databases, security groups for access control
4. **IAM**: Least privilege access with specific resource permissions
5. **Backup**: Automated backups for databases and versioning for S3

## 🚨 Troubleshooting

### Common Issues

1. **Stack Creation Failed**
   ```bash
   # Check events for error details
   aws cloudformation describe-stack-events --stack-name sports-prediction-bot-dev
   ```

2. **Resource Limits**
   ```bash
   # Check service quotas
   aws service-quotas list-service-quotas --service-code ec2
   ```

3. **Permission Issues**
   ```bash
   # Verify IAM permissions
   aws iam simulate-principal-policy \
       --policy-source-arn arn:aws:iam::ACCOUNT:user/USERNAME \
       --action-names cloudformation:CreateStack \
       --resource-arns "*"
   ```

### Support

For issues and questions:
1. Check AWS CloudFormation console for detailed error messages
2. Review CloudWatch logs for service-specific issues
3. Consult AWS documentation for service limits and requirements

## 📝 Next Steps

After infrastructure deployment:

1. **Update App Runner Configuration**: Use the IAM role ARNs from stack outputs
2. **Configure Application**: Update environment variables with resource endpoints
3. **Deploy Application**: Use the App Runner service or container deployment
4. **Set Up Monitoring**: Configure CloudWatch dashboards and alarms
5. **Test Connectivity**: Verify application can connect to all services
