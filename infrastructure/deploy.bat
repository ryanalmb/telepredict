@echo off
REM Windows batch script for deploying CloudFormation infrastructure
REM Usage: deploy.bat [environment] [region]
REM Example: deploy.bat dev us-east-1

setlocal enabledelayedexpansion

REM Default values
set ENVIRONMENT=%1
set REGION=%2
set PROJECT_NAME=sports-prediction-bot

if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev
if "%REGION%"=="" set REGION=us-east-1

set STACK_NAME=%PROJECT_NAME%-%ENVIRONMENT%

echo.
echo ========================================
echo Sports Prediction Bot - Infrastructure Deployment
echo ========================================
echo Environment: %ENVIRONMENT%
echo Region: %REGION%
echo Stack Name: %STACK_NAME%
echo.

REM Validate environment
if not "%ENVIRONMENT%"=="dev" if not "%ENVIRONMENT%"=="staging" if not "%ENVIRONMENT%"=="prod" (
    echo ERROR: Invalid environment: %ENVIRONMENT%. Must be dev, staging, or prod.
    exit /b 1
)

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS CLI is not installed. Please install it first.
    exit /b 1
)

REM Check if AWS credentials are configured
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ERROR: AWS credentials not configured. Please run 'aws configure' first.
    exit /b 1
)

REM Set AWS region
set AWS_DEFAULT_REGION=%REGION%

REM Check if parameter file exists
set PARAM_FILE=infrastructure\parameters\%ENVIRONMENT%.json
if not exist "%PARAM_FILE%" (
    echo ERROR: Parameter file not found: %PARAM_FILE%
    exit /b 1
)

echo INFO: Validating CloudFormation template...
aws cloudformation validate-template --template-body file://infrastructure/infrastructure.yaml >nul 2>&1
if errorlevel 1 (
    echo ERROR: Template validation failed
    exit /b 1
) else (
    echo SUCCESS: Template validation passed
)

echo.
echo INFO: Checking if stack exists...
aws cloudformation describe-stacks --stack-name "%STACK_NAME%" >nul 2>&1
if errorlevel 1 (
    echo INFO: Creating new stack: %STACK_NAME%
    
    aws cloudformation create-stack ^
        --stack-name "%STACK_NAME%" ^
        --template-body file://infrastructure/infrastructure.yaml ^
        --parameters file://"%PARAM_FILE%" ^
        --capabilities CAPABILITY_NAMED_IAM ^
        --tags Key=Environment,Value="%ENVIRONMENT%" Key=Project,Value="%PROJECT_NAME%" ^
        --enable-termination-protection
    
    if errorlevel 1 (
        echo ERROR: Stack creation failed!
        exit /b 1
    )
    
    echo INFO: Waiting for stack creation to complete...
    aws cloudformation wait stack-create-complete --stack-name "%STACK_NAME%"
    
    if errorlevel 1 (
        echo ERROR: Stack creation failed or timed out!
        exit /b 1
    ) else (
        echo SUCCESS: Stack created successfully!
    )
) else (
    echo INFO: Stack exists. Use update functionality if needed.
    echo INFO: For updates, use the AWS Console or AWS CLI directly.
)

echo.
echo INFO: Stack outputs:
aws cloudformation describe-stacks ^
    --stack-name "%STACK_NAME%" ^
    --query "Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}" ^
    --output table

echo.
echo SUCCESS: Deployment completed successfully!
echo.
echo Next steps:
echo 1. Update your .env file with the output values
echo 2. Deploy your App Runner service using the provided IAM roles
echo 3. Configure your application to use the created resources

endlocal
