# AWS App Runner Deployment Troubleshooting

## 🚨 Common Issues and Solutions

### Issue 1: "apprunner.yaml not found"

**Problem**: AWS App Runner can't find the configuration file.

**Solutions**:

1. **Check file location**: Ensure `apprunner.yaml` is in the root of your repository
2. **Check Git commit**: Make sure the file is committed to your Git repository
3. **Try alternative locations**:
   ```bash
   # Option 1: Root directory (recommended)
   ./apprunner.yaml
   
   # Option 2: .apprunner directory
   ./.apprunner/apprunner.yaml
   ```

4. **Use minimal configuration**: Try the simplified version:
   ```bash
   cp apprunner-minimal.yaml apprunner.yaml
   git add apprunner.yaml
   git commit -m "Add App Runner config"
   git push
   ```

### Issue 2: Build Failures

**Problem**: Docker build fails during deployment.

**Solutions**:

1. **Check Dockerfile**: Ensure the Dockerfile is valid
2. **Test locally**:
   ```bash
   docker build --target production -t sports-prediction-bot .
   docker run -p 8000:8000 sports-prediction-bot
   ```

3. **Simplify dependencies**: Comment out heavy ML libraries temporarily:
   ```dockerfile
   # RUN pip install torch tensorflow  # Comment out for testing
   ```

### Issue 3: Health Check Failures

**Problem**: App Runner health checks fail.

**Solutions**:

1. **Test health endpoint locally**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check logs**: Look for startup errors in App Runner logs

3. **Increase timeout**: Modify health check settings:
   ```yaml
   health-check:
     path: "/health"
     interval: 60
     timeout: 30
     healthy-threshold: 2
     unhealthy-threshold: 10
   ```

### Issue 4: Environment Variables

**Problem**: Missing or incorrect environment variables.

**Solutions**:

1. **Required variables**:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_WEBHOOK_URL=https://your-app-url.amazonaws.com/webhook
   ```

2. **Set in App Runner console**:
   - Go to AWS App Runner console
   - Select your service
   - Go to Configuration → Environment variables
   - Add required variables

### Issue 5: Webhook Setup

**Problem**: Telegram webhook not working.

**Solutions**:

1. **Set webhook URL**:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://your-app-url.amazonaws.com/webhook"}'
   ```

2. **Check webhook status**:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
   ```

## 🔧 Step-by-Step Deployment

### Step 1: Prepare Repository

1. **Ensure files are committed**:
   ```bash
   git add .
   git commit -m "Add App Runner configuration"
   git push origin main
   ```

2. **Verify apprunner.yaml exists**:
   ```bash
   ls -la apprunner.yaml
   cat apprunner.yaml
   ```

### Step 2: Create App Runner Service

1. **Via AWS Console**:
   - Go to AWS App Runner
   - Click "Create service"
   - Choose "Source code repository"
   - Connect your GitHub repository
   - Select branch (usually `main`)
   - Choose "Use a configuration file"
   - Review and create

2. **Via AWS CLI**:
   ```bash
   aws apprunner create-service --cli-input-json file://apprunner-service.json
   ```

### Step 3: Configure Environment Variables

**Required variables**:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_URL=https://your-service-url.amazonaws.com/webhook
AWS_REGION=us-east-1
```

**Optional variables**:
```
ESPN_API_KEY=your_espn_key
SPORTRADAR_API_KEY=your_sportradar_key
ODDS_API_KEY=your_odds_api_key
REDIS_URL=redis://your-redis-url:6379
MONGODB_URL=mongodb://your-mongodb-url:27017/sports_predictions
```

### Step 4: Test Deployment

1. **Check service status**:
   ```bash
   aws apprunner describe-service --service-arn your-service-arn
   ```

2. **Test health endpoint**:
   ```bash
   curl https://your-service-url.amazonaws.com/health
   ```

3. **Test webhook**:
   ```bash
   curl -X POST https://your-service-url.amazonaws.com/webhook \
        -H "Content-Type: application/json" \
        -d '{"test": true}'
   ```

## 🐛 Debugging Tips

### Check App Runner Logs

1. **Via AWS Console**:
   - Go to App Runner service
   - Click "Logs" tab
   - Check "Application logs"

2. **Via AWS CLI**:
   ```bash
   aws logs describe-log-streams --log-group-name /aws/apprunner/your-service-name
   ```

### Common Log Errors

1. **"Module not found"**: Missing dependencies in requirements.txt
2. **"Port already in use"**: Check port configuration
3. **"Permission denied"**: Check file permissions in Dockerfile
4. **"Health check failed"**: Check /health endpoint

### Test Locally First

```bash
# Build and test Docker image
docker build --target production -t sports-prediction-bot .
docker run -p 8000:8000 \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e TELEGRAM_WEBHOOK_URL=http://localhost:8000/webhook \
  sports-prediction-bot

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/
```

## 📞 Getting Help

If you're still having issues:

1. **Check AWS App Runner documentation**: https://docs.aws.amazon.com/apprunner/
2. **Review logs carefully**: Most issues are revealed in the logs
3. **Start simple**: Use minimal configuration first, then add complexity
4. **Test locally**: Always test Docker builds locally before deploying

## 🎯 Quick Fix Checklist

- [ ] `apprunner.yaml` exists in repository root
- [ ] File is committed and pushed to Git
- [ ] TELEGRAM_BOT_TOKEN is set
- [ ] TELEGRAM_WEBHOOK_URL is set correctly
- [ ] Health endpoint returns 200 OK
- [ ] Docker image builds successfully
- [ ] All required dependencies are in requirements.txt
- [ ] Port 8000 is exposed and used consistently
