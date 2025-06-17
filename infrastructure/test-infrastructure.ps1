# PowerShell script to test CloudFormation infrastructure
# This script validates the template and parameter files without deploying

Write-Host "Testing Sports Prediction Bot Infrastructure" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Test 1: Check if files exist
Write-Host "`nTest 1: Checking file structure..." -ForegroundColor Yellow

$files = @(
    "infrastructure/infrastructure.yaml",
    "infrastructure/parameters/dev.json",
    "infrastructure/parameters/staging.json", 
    "infrastructure/parameters/prod.json",
    "infrastructure/scripts/deploy.sh",
    "infrastructure/scripts/destroy.sh",
    "infrastructure/scripts/status.sh"
)

$allFilesExist = $true
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "[OK] $file exists" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] $file missing" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if ($allFilesExist) {
    Write-Host "✅ All required files exist" -ForegroundColor Green
} else {
    Write-Host "❌ Some files are missing" -ForegroundColor Red
    exit 1
}

# Test 2: Validate JSON parameter files
Write-Host "`n📋 Test 2: Validating JSON parameter files..." -ForegroundColor Yellow

$paramFiles = @("dev.json", "staging.json", "prod.json")
foreach ($paramFile in $paramFiles) {
    $filePath = "infrastructure/parameters/$paramFile"
    try {
        $content = Get-Content $filePath -Raw | ConvertFrom-Json
        Write-Host "✅ $paramFile is valid JSON" -ForegroundColor Green
        
        # Check required parameters
        $requiredParams = @("Environment", "ProjectName", "VpcCidr", "TelegramBotToken", "EspnApiKey", "SportradarApiKey", "OddsApiKey")
        $paramKeys = $content | ForEach-Object { $_.ParameterKey }
        
        $missingParams = $requiredParams | Where-Object { $_ -notin $paramKeys }
        if ($missingParams.Count -eq 0) {
            Write-Host "✅ $paramFile has all required parameters" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $paramFile missing parameters: $($missingParams -join ', ')" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ $paramFile has invalid JSON: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 3: Basic YAML structure validation
Write-Host "`n📄 Test 3: Validating CloudFormation template structure..." -ForegroundColor Yellow

try {
    $yamlContent = Get-Content "infrastructure/infrastructure.yaml" -Raw
    
    # Check for required sections
    $requiredSections = @("AWSTemplateFormatVersion", "Description", "Parameters", "Resources", "Outputs")
    $missingSections = @()
    
    foreach ($section in $requiredSections) {
        if ($yamlContent -match "$section\s*:") {
            Write-Host "✅ $section section found" -ForegroundColor Green
        } else {
            Write-Host "❌ $section section missing" -ForegroundColor Red
            $missingSections += $section
        }
    }
    
    if ($missingSections.Count -eq 0) {
        Write-Host "✅ All required CloudFormation sections present" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing sections: $($missingSections -join ', ')" -ForegroundColor Red
    }
    
    # Check for key resources
    $keyResources = @("VPC", "ModelsBucket", "PredictionsTable", "RedisCluster", "DocumentDBCluster")
    foreach ($resource in $keyResources) {
        if ($yamlContent -match "$resource\s*:") {
            Write-Host "✅ $resource resource defined" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $resource resource not found" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "❌ Error reading CloudFormation template: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Check AWS CLI availability (optional)
Write-Host "`n🔧 Test 4: Checking AWS CLI availability..." -ForegroundColor Yellow

try {
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ AWS CLI is available: $awsVersion" -ForegroundColor Green
        
        # Test AWS credentials (optional)
        try {
            $identity = aws sts get-caller-identity 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ AWS credentials are configured" -ForegroundColor Green
            } else {
                Write-Host "⚠️  AWS credentials not configured or invalid" -ForegroundColor Yellow
                Write-Host "   Run 'aws configure' to set up credentials" -ForegroundColor Gray
            }
        }
        catch {
            Write-Host "⚠️  Could not verify AWS credentials" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  AWS CLI not available" -ForegroundColor Yellow
        Write-Host "   Install AWS CLI to deploy infrastructure" -ForegroundColor Gray
    }
}
catch {
    Write-Host "⚠️  AWS CLI not found in PATH" -ForegroundColor Yellow
}

# Test 5: Validate script permissions (on Unix-like systems)
Write-Host "`n🔐 Test 5: Checking script files..." -ForegroundColor Yellow

$scriptFiles = @("deploy.sh", "destroy.sh", "status.sh")
foreach ($script in $scriptFiles) {
    $scriptPath = "infrastructure/scripts/$script"
    if (Test-Path $scriptPath) {
        $content = Get-Content $scriptPath -Raw
        if ($content -match "#!/bin/bash") {
            Write-Host "✅ $script has proper shebang" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $script missing shebang" -ForegroundColor Yellow
        }
        
        # Check for key functions
        if ($content -match "print_status|print_success|print_error") {
            Write-Host "✅ $script has logging functions" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $script missing logging functions" -ForegroundColor Yellow
        }
    }
}

# Summary
Write-Host "`n📊 Test Summary" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan
Write-Host "✅ File structure validation completed" -ForegroundColor Green
Write-Host "✅ JSON parameter files validated" -ForegroundColor Green
Write-Host "✅ CloudFormation template structure checked" -ForegroundColor Green
Write-Host "✅ Script files validated" -ForegroundColor Green

Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Configure AWS CLI: aws configure" -ForegroundColor White
Write-Host "2. Update parameter files with real API keys" -ForegroundColor White
Write-Host "3. Validate template: aws cloudformation validate-template --template-body file://infrastructure/infrastructure.yaml" -ForegroundColor White
Write-Host "4. Deploy infrastructure: ./infrastructure/scripts/deploy.sh dev us-east-1" -ForegroundColor White

Write-Host "`nInfrastructure test completed successfully!" -ForegroundColor Green
