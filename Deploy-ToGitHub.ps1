# PowerShell script to deploy Sports Prediction Bot to GitHub
# This script automates the GitHub deployment process

param(
    [string]$GitHubUsername,
    [string]$RepositoryName = "sports-prediction-bot",
    [string]$CommitMessage = "Deploy Sports Prediction Bot with comprehensive testing infrastructure"
)

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ️  $Message" "Cyan"
}

# Main deployment function
function Deploy-ToGitHub {
    Write-ColorOutput "`n========================================" "Cyan"
    Write-ColorOutput "Sports Prediction Bot - GitHub Deployment" "Cyan"
    Write-ColorOutput "========================================`n" "Cyan"

    # Check if Git is installed
    try {
        $gitVersion = git --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Git is installed: $gitVersion"
        } else {
            throw "Git not found"
        }
    }
    catch {
        Write-Error "Git is not installed or not in PATH"
        Write-Info "Please install Git from: https://git-scm.com/download/win"
        Write-Info "Or use winget: winget install Git.Git"
        return $false
    }

    # Check if we're in a git repository
    if (-not (Test-Path ".git")) {
        Write-Info "Initializing Git repository..."
        git init
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Git repository initialized"
        } else {
            Write-Error "Failed to initialize Git repository"
            return $false
        }
    } else {
        Write-Success "Git repository already exists"
    }

    # Check Git configuration
    $gitName = git config user.name 2>$null
    $gitEmail = git config user.email 2>$null

    if (-not $gitName) {
        $gitName = Read-Host "Enter your name for Git commits"
        git config user.name $gitName
    }

    if (-not $gitEmail) {
        $gitEmail = Read-Host "Enter your email for Git commits"
        git config user.email $gitEmail
    }

    Write-Success "Git configured for: $gitName <$gitEmail>"

    # Get GitHub repository details
    if (-not $GitHubUsername) {
        $GitHubUsername = Read-Host "Enter your GitHub username"
    }

    if (-not $RepositoryName) {
        $RepositoryName = Read-Host "Enter repository name (default: sports-prediction-bot)"
        if (-not $RepositoryName) {
            $RepositoryName = "sports-prediction-bot"
        }
    }

    $githubUrl = "https://github.com/$GitHubUsername/$RepositoryName.git"
    Write-Info "Repository will be created at: $githubUrl"

    # Check if remote already exists
    try {
        $existingRemote = git remote get-url origin 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Warning "Remote 'origin' already exists: $existingRemote"
            $continue = Read-Host "Continue with existing remote? (y/N)"
            if ($continue -ne "y" -and $continue -ne "Y") {
                Write-Info "Deployment cancelled"
                return $false
            }
        } else {
            throw "No remote found"
        }
    }
    catch {
        Write-Info "Adding GitHub remote..."
        git remote add origin $githubUrl
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Remote added: $githubUrl"
        } else {
            Write-Error "Failed to add remote"
            return $false
        }
    }

    # Create .gitignore if it doesn't exist
    if (-not (Test-Path ".gitignore")) {
        Write-Info "Creating .gitignore file..."
        $gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log

# Environment variables
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
logs/
data/cache/
data/raw/
data/processed/
models/
test_results.json
test_output.log
test_report.html
test_instance.json

# AWS
.aws/

# Temporary files
*.tmp
*.temp
"@
        $gitignoreContent | Out-File -FilePath ".gitignore" -Encoding UTF8
        Write-Success ".gitignore created"
    }

    # Stage all files
    Write-Info "Staging files for commit..."
    git add .

    # Check if there are changes to commit
    git diff --staged --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Warning "No changes to commit"
        $forceCommit = Read-Host "Force commit anyway? (y/N)"
        if ($forceCommit -ne "y" -and $forceCommit -ne "Y") {
            Write-Info "Deployment cancelled"
            return $false
        }
    }

    # Create commit
    if (-not $CommitMessage) {
        $CommitMessage = Read-Host "Enter commit message (default: 'Deploy Sports Prediction Bot with comprehensive testing infrastructure')"
        if (-not $CommitMessage) {
            $CommitMessage = "Deploy Sports Prediction Bot with comprehensive testing infrastructure"
        }
    }

    git commit -m $CommitMessage
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Changes committed"
    } else {
        Write-Error "Commit failed"
        return $false
    }

    # Set main branch
    git branch -M main

    # Push to GitHub
    Write-Info "Pushing to GitHub..."
    Write-Info "This may prompt for your GitHub credentials or Personal Access Token"

    git push -u origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Successfully pushed to GitHub!"
    } else {
        Write-Error "Push failed"
        Write-Info "Common solutions:"
        Write-Info "1. Create the repository on GitHub first: https://github.com/new"
        Write-Info "2. Use a Personal Access Token instead of password"
        Write-Info "3. Check your internet connection"
        Write-Info "4. Verify the repository URL is correct"
        return $false
    }

    # Success message
    Write-ColorOutput "`n========================================" "Green"
    Write-ColorOutput "✅ SUCCESS: Deployment Complete!" "Green"
    Write-ColorOutput "========================================`n" "Green"

    Write-Info "Your Sports Prediction Bot has been deployed to:"
    Write-ColorOutput $githubUrl "Yellow"

    Write-Info "`nNext steps:"
    Write-Info "1. Visit your repository on GitHub"
    Write-Info "2. Configure GitHub Secrets for CI/CD (see GITHUB_DEPLOYMENT.md)"
    Write-Info "3. Enable GitHub Actions"
    Write-Info "4. Review and merge any pull requests"

    Write-Info "`nGitHub Actions will automatically:"
    Write-Success "Run comprehensive tests"
    Write-Success "Validate infrastructure"
    Write-Success "Test Docker builds"
    Write-Success "Perform security scans"

    Write-Info "`nFor detailed setup instructions, see:"
    Write-Info "- README.md"
    Write-Info "- GITHUB_DEPLOYMENT.md"
    Write-Info "- REMOTE_TESTING_GUIDE.md"

    # Open GitHub repository in browser
    $openBrowser = Read-Host "`nOpen repository in browser? (Y/n)"
    if ($openBrowser -ne "n" -and $openBrowser -ne "N") {
        Start-Process "https://github.com/$GitHubUsername/$RepositoryName"
    }

    Write-ColorOutput "`n🎉 Deployment completed successfully!" "Green"
    return $true
}

# Run the deployment
try {
    $success = Deploy-ToGitHub
    if ($success) {
        exit 0
    } else {
        exit 1
    }
}
catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    exit 1
}
finally {
    Write-Host "`nPress any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
