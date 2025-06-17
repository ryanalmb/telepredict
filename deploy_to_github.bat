@echo off
REM Windows batch script to deploy Sports Prediction Bot to GitHub
REM This script automates the GitHub deployment process

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Sports Prediction Bot - GitHub Deployment
echo ========================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo Or use winget: winget install Git.Git
    echo.
    pause
    exit /b 1
)

echo ✅ Git is installed

REM Check if we're in a git repository
if not exist ".git" (
    echo.
    echo Initializing Git repository...
    git init
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already exists
)

REM Check Git configuration
for /f "tokens=*" %%i in ('git config user.name 2^>nul') do set GIT_NAME=%%i
for /f "tokens=*" %%i in ('git config user.email 2^>nul') do set GIT_EMAIL=%%i

if "%GIT_NAME%"=="" (
    echo.
    set /p GIT_NAME="Enter your name for Git commits: "
    git config user.name "!GIT_NAME!"
)

if "%GIT_EMAIL%"=="" (
    echo.
    set /p GIT_EMAIL="Enter your email for Git commits: "
    git config user.email "!GIT_EMAIL!"
)

echo ✅ Git configured for: !GIT_NAME! ^<!GIT_EMAIL!^>

REM Get GitHub repository details
echo.
set /p GITHUB_USERNAME="Enter your GitHub username: "
set /p REPO_NAME="Enter repository name (default: sports-prediction-bot): "
if "%REPO_NAME%"=="" set REPO_NAME=sports-prediction-bot

set GITHUB_URL=https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git

echo.
echo Repository will be created at: %GITHUB_URL%
echo.

REM Check if remote already exists
git remote get-url origin >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  Remote 'origin' already exists
    for /f "tokens=*" %%i in ('git remote get-url origin') do set EXISTING_REMOTE=%%i
    echo Current remote: !EXISTING_REMOTE!
    echo.
    set /p CONTINUE="Continue with existing remote? (y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo Deployment cancelled
        pause
        exit /b 0
    )
) else (
    echo Adding GitHub remote...
    git remote add origin %GITHUB_URL%
    echo ✅ Remote added: %GITHUB_URL%
)

REM Create .gitignore if it doesn't exist
if not exist ".gitignore" (
    echo Creating .gitignore file...
    echo # Python > .gitignore
    echo __pycache__/ >> .gitignore
    echo *.py[cod] >> .gitignore
    echo .env >> .gitignore
    echo .venv/ >> .gitignore
    echo venv/ >> .gitignore
    echo logs/ >> .gitignore
    echo *.log >> .gitignore
    echo test_results.json >> .gitignore
    echo ✅ .gitignore created
)

REM Stage all files
echo.
echo Staging files for commit...
git add .

REM Check if there are changes to commit
git diff --staged --quiet
if not errorlevel 1 (
    echo ⚠️  No changes to commit
    echo.
    set /p FORCE_COMMIT="Force commit anyway? (y/N): "
    if /i not "!FORCE_COMMIT!"=="y" (
        echo Deployment cancelled
        pause
        exit /b 0
    )
)

REM Create commit
echo.
set /p COMMIT_MESSAGE="Enter commit message (default: 'Deploy Sports Prediction Bot with comprehensive testing infrastructure'): "
if "%COMMIT_MESSAGE%"=="" set COMMIT_MESSAGE=Deploy Sports Prediction Bot with comprehensive testing infrastructure

git commit -m "%COMMIT_MESSAGE%"
if errorlevel 1 (
    echo ❌ Commit failed
    pause
    exit /b 1
)

echo ✅ Changes committed

REM Set main branch
git branch -M main

REM Push to GitHub
echo.
echo Pushing to GitHub...
echo This may prompt for your GitHub credentials or Personal Access Token
echo.

git push -u origin main
if errorlevel 1 (
    echo.
    echo ❌ Push failed
    echo.
    echo Common solutions:
    echo 1. Create the repository on GitHub first: https://github.com/new
    echo 2. Use a Personal Access Token instead of password
    echo 3. Check your internet connection
    echo 4. Verify the repository URL is correct
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ SUCCESS: Deployment Complete!
echo ========================================
echo.
echo Your Sports Prediction Bot has been deployed to:
echo %GITHUB_URL%
echo.
echo Next steps:
echo 1. Visit your repository on GitHub
echo 2. Configure GitHub Secrets for CI/CD (see GITHUB_DEPLOYMENT.md)
echo 3. Enable GitHub Actions
echo 4. Review and merge any pull requests
echo.
echo GitHub Actions will automatically:
echo ✅ Run comprehensive tests
echo ✅ Validate infrastructure
echo ✅ Test Docker builds
echo ✅ Perform security scans
echo.
echo For detailed setup instructions, see:
echo - README.md
echo - GITHUB_DEPLOYMENT.md
echo - REMOTE_TESTING_GUIDE.md
echo.

REM Open GitHub repository in browser
set /p OPEN_BROWSER="Open repository in browser? (Y/n): "
if /i not "!OPEN_BROWSER!"=="n" (
    start https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
)

echo.
echo 🎉 Deployment completed successfully!
echo.
pause

endlocal
