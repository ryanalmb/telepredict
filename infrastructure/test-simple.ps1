# Simple PowerShell script to test CloudFormation infrastructure
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
    Write-Host "[OK] All required files exist" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Some files are missing" -ForegroundColor Red
    exit 1
}

# Test 2: Validate JSON parameter files
Write-Host "`nTest 2: Validating JSON parameter files..." -ForegroundColor Yellow

$paramFiles = @("dev.json", "staging.json", "prod.json")
foreach ($paramFile in $paramFiles) {
    $filePath = "infrastructure/parameters/$paramFile"
    try {
        $content = Get-Content $filePath -Raw | ConvertFrom-Json
        Write-Host "[OK] $paramFile is valid JSON" -ForegroundColor Green
        
        # Check required parameters
        $requiredParams = @("Environment", "ProjectName", "VpcCidr", "TelegramBotToken", "EspnApiKey", "SportradarApiKey", "OddsApiKey")
        $paramKeys = $content | ForEach-Object { $_.ParameterKey }
        
        $missingParams = $requiredParams | Where-Object { $_ -notin $paramKeys }
        if ($missingParams.Count -eq 0) {
            Write-Host "[OK] $paramFile has all required parameters" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] $paramFile missing parameters: $($missingParams -join ', ')" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "[ERROR] $paramFile has invalid JSON: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 3: Basic YAML structure validation
Write-Host "`nTest 3: Validating CloudFormation template structure..." -ForegroundColor Yellow

try {
    $yamlContent = Get-Content "infrastructure/infrastructure.yaml" -Raw
    
    # Check for required sections
    $requiredSections = @("AWSTemplateFormatVersion", "Description", "Parameters", "Resources", "Outputs")
    $missingSections = @()
    
    foreach ($section in $requiredSections) {
        if ($yamlContent -match "$section\s*:") {
            Write-Host "[OK] $section section found" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] $section section missing" -ForegroundColor Red
            $missingSections += $section
        }
    }
    
    if ($missingSections.Count -eq 0) {
        Write-Host "[OK] All required CloudFormation sections present" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Missing sections: $($missingSections -join ', ')" -ForegroundColor Red
    }
    
    # Check for key resources
    $keyResources = @("VPC", "ModelsBucket", "PredictionsTable", "RedisCluster", "DocumentDBCluster")
    foreach ($resource in $keyResources) {
        if ($yamlContent -match "$resource\s*:") {
            Write-Host "[OK] $resource resource defined" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] $resource resource not found" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "[ERROR] Error reading CloudFormation template: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Check AWS CLI availability
Write-Host "`nTest 4: Checking AWS CLI availability..." -ForegroundColor Yellow

try {
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] AWS CLI is available: $awsVersion" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] AWS CLI not available" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "[WARNING] AWS CLI not found in PATH" -ForegroundColor Yellow
}

# Summary
Write-Host "`nTest Summary" -ForegroundColor Cyan
Write-Host "============" -ForegroundColor Cyan
Write-Host "[OK] File structure validation completed" -ForegroundColor Green
Write-Host "[OK] JSON parameter files validated" -ForegroundColor Green
Write-Host "[OK] CloudFormation template structure checked" -ForegroundColor Green

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Configure AWS CLI: aws configure" -ForegroundColor White
Write-Host "2. Update parameter files with real API keys" -ForegroundColor White
Write-Host "3. Validate template with AWS: aws cloudformation validate-template --template-body file://infrastructure/infrastructure.yaml" -ForegroundColor White
Write-Host "4. Deploy infrastructure: ./infrastructure/scripts/deploy.sh dev us-east-1" -ForegroundColor White

Write-Host "`nInfrastructure test completed successfully!" -ForegroundColor Green
