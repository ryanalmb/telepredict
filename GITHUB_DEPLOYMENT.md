# 🚀 GitHub Deployment Guide

## Sports Prediction Bot - Complete Deployment to GitHub

This guide walks you through deploying the Sports Prediction Bot project to GitHub with all the comprehensive testing infrastructure.

## 📋 Prerequisites

### 1. Install Git
**Windows:**
```bash
# Download and install Git from: https://git-scm.com/download/win
# Or use winget:
winget install Git.Git
```

**macOS:**
```bash
# Using Homebrew:
brew install git

# Or download from: https://git-scm.com/download/mac
```

**Linux:**
```bash
# Ubuntu/Debian:
sudo apt-get install git

# CentOS/RHEL:
sudo yum install git
```

### 2. Configure Git
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3. GitHub Account
- Create account at [github.com](https://github.com)
- Generate Personal Access Token (Settings → Developer settings → Personal access tokens)

## 🎯 Step-by-Step Deployment

### Step 1: Initialize Git Repository
```bash
# Navigate to project directory
cd /path/to/sports-prediction-bot

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Sports Prediction Bot with comprehensive testing infrastructure"
```

### Step 2: Create GitHub Repository
**Option A: Using GitHub Web Interface**
1. Go to [github.com](https://github.com)
2. Click "New repository"
3. Name: `sports-prediction-bot`
4. Description: `AI-powered sports prediction bot with comprehensive AWS infrastructure and testing`
5. Set to Public or Private
6. **Don't** initialize with README (we already have one)
7. Click "Create repository"

**Option B: Using GitHub CLI**
```bash
# Install GitHub CLI first: https://cli.github.com/
gh repo create sports-prediction-bot --public --description "AI-powered sports prediction bot with comprehensive AWS infrastructure and testing"
```

### Step 3: Connect Local Repository to GitHub
```bash
# Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/sports-prediction-bot.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Configure GitHub Secrets (for CI/CD)
Go to your repository → Settings → Secrets and variables → Actions

Add these secrets for full testing functionality:

```bash
# AWS Credentials (for infrastructure testing)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# API Keys (for integration testing)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ESPN_API_KEY=your_espn_api_key
SPORTRADAR_API_KEY=your_sportradar_api_key
ODDS_API_KEY=your_odds_api_key

# Optional: Notification settings
SLACK_WEBHOOK_URL=your_slack_webhook
DISCORD_WEBHOOK_URL=your_discord_webhook
```

### Step 5: Verify GitHub Actions
After pushing, GitHub Actions will automatically:
1. Run comprehensive tests
2. Validate infrastructure
3. Test Docker builds
4. Perform security scans
5. Generate test reports

Check: Repository → Actions tab

## 📁 What Gets Deployed

### Core Application
```
src/sports_prediction/          # Main application code
├── cli/                       # Command-line interface
├── config/                    # Configuration management
├── data_collection/           # Sports data collection
├── ml_models/                 # Machine learning models
├── prediction_engine/         # Prediction logic
├── telegram_bot/              # Telegram bot implementation
└── utils/                     # Utility functions
```

### Infrastructure
```
infrastructure/                # AWS CloudFormation
├── infrastructure.yaml        # Main template
├── parameters/               # Environment configs
├── scripts/                  # Deployment scripts
└── README.md                 # Infrastructure docs
```

### Testing Infrastructure
```
remote_testing/               # Comprehensive testing
├── full_test_suite.py       # Main test suite
├── Dockerfile.test          # Docker test environment
├── ec2_test_script.sh       # AWS EC2 testing
└── deploy_test_environment.sh # Test deployment

.github/workflows/            # GitHub Actions
└── comprehensive-test.yml    # CI/CD pipeline
```

### Documentation
```
README.md                     # Main project documentation
GITHUB_DEPLOYMENT.md          # This deployment guide
REMOTE_TESTING_GUIDE.md       # Testing documentation
PROJECT_TEST_RESULTS.md       # Test results summary
infrastructure/README.md      # Infrastructure guide
infrastructure/DEPLOYMENT.md  # Deployment guide
```

## 🔧 Post-Deployment Configuration

### 1. Enable GitHub Actions
- Go to repository → Actions
- Enable workflows if prompted
- First run will trigger automatically

### 2. Configure Branch Protection
Repository → Settings → Branches → Add rule:
- Branch name pattern: `main`
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Require pull request reviews

### 3. Setup Notifications
Repository → Settings → Webhooks:
- Add webhook for Slack/Discord notifications
- Configure for push, pull request, and release events

### 4. Configure Security
Repository → Settings → Security:
- ✅ Enable Dependabot alerts
- ✅ Enable Dependabot security updates
- ✅ Enable secret scanning

## 🧪 Triggering Remote Tests

### Automatic Testing
Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual workflow dispatch

### Manual Testing
```bash
# Using GitHub CLI
gh workflow run comprehensive-test.yml

# Using web interface
Repository → Actions → Comprehensive Testing → Run workflow
```

### Monitoring Test Results
```bash
# List recent runs
gh run list

# View specific run
gh run view RUN_ID --log

# Download artifacts
gh run download RUN_ID
```

## 📊 Understanding Test Results

### GitHub Actions Dashboard
- **Green checkmark**: All tests passed
- **Red X**: Tests failed
- **Yellow circle**: Tests in progress

### Test Categories
1. **Basic Tests**: Project structure, dependencies
2. **Full Dependencies**: ML libraries, databases
3. **Infrastructure**: CloudFormation validation
4. **Docker**: Container builds
5. **Security**: Vulnerability scanning
6. **Performance**: Memory and timing tests

### Artifacts Generated
- `test-results`: JSON test results
- `security-reports`: Security scan results
- Test logs and reports

## 🚀 Deployment Workflows

### Development Workflow
```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes
# ... edit files ...

# 3. Commit and push
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 4. Create pull request
gh pr create --title "Add new feature" --body "Description of changes"

# 5. Tests run automatically
# 6. Merge after approval and tests pass
gh pr merge --squash
```

### Release Workflow
```bash
# 1. Create release branch
git checkout -b release/v1.0.0

# 2. Update version numbers
# ... update version in files ...

# 3. Create release
git tag v1.0.0
git push origin v1.0.0

# 4. GitHub will create release automatically
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes"
```

## 🔒 Security Best Practices

### 1. Secrets Management
- ✅ Never commit API keys or passwords
- ✅ Use GitHub Secrets for sensitive data
- ✅ Rotate secrets regularly
- ✅ Use least privilege access

### 2. Branch Protection
- ✅ Require pull request reviews
- ✅ Require status checks
- ✅ Restrict force pushes
- ✅ Require signed commits (optional)

### 3. Dependency Security
- ✅ Enable Dependabot
- ✅ Regular security updates
- ✅ Vulnerability scanning
- ✅ License compliance checking

## 🎯 Next Steps After Deployment

### 1. Immediate Actions
- [ ] Verify all GitHub Actions pass
- [ ] Configure repository settings
- [ ] Add collaborators if needed
- [ ] Setup branch protection rules

### 2. Development Setup
- [ ] Clone repository to development machines
- [ ] Setup local development environment
- [ ] Configure IDE/editor settings
- [ ] Test local development workflow

### 3. Production Deployment
- [ ] Deploy AWS infrastructure using CloudFormation
- [ ] Configure production environment variables
- [ ] Setup monitoring and alerting
- [ ] Deploy application to production

### 4. Ongoing Maintenance
- [ ] Monitor test results
- [ ] Update dependencies regularly
- [ ] Review security alerts
- [ ] Maintain documentation

## 📞 Support and Troubleshooting

### Common Issues

1. **Git not recognized**
   - Install Git from official website
   - Restart terminal/command prompt
   - Verify installation: `git --version`

2. **Authentication failed**
   - Use Personal Access Token instead of password
   - Configure Git credentials: `git config --global credential.helper store`

3. **Large files rejected**
   - Use Git LFS for large files: `git lfs track "*.pkl"`
   - Or add to .gitignore if not needed

4. **Tests failing**
   - Check GitHub Actions logs
   - Verify secrets are configured
   - Review error messages in test output

### Getting Help
- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Community support
- **Documentation**: Check README files
- **GitHub Support**: For platform issues

---

## 🎉 Congratulations!

Your Sports Prediction Bot is now deployed to GitHub with:
- ✅ Complete source code
- ✅ Comprehensive testing infrastructure
- ✅ AWS deployment automation
- ✅ CI/CD pipeline
- ✅ Security scanning
- ✅ Documentation

**Your project is now ready for collaborative development and production deployment!** 🚀
