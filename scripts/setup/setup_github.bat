@echo off
setlocal enabledelayedexpansion

REM Advanced RAG Research Ecosystem - GitHub Setup Script (Windows)
REM This script helps you set up the GitHub repository quickly

echo.
echo 🚀 Advanced RAG Research Ecosystem - GitHub Setup
echo ==================================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed. Please install Git first.
    pause
    exit /b 1
)

echo [SUCCESS] Git is installed ✓
echo.

REM Get repository information
echo [INFO] Please provide your GitHub repository information:
echo.

set /p GITHUB_USERNAME="Enter your GitHub username: "
set /p REPO_NAME="Enter your repository name (default: advanced-rag-research-ecosystem): "
if "%REPO_NAME%"=="" set REPO_NAME=advanced-rag-research-ecosystem

echo.
echo [INFO] Repository URL will be: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
echo.

set /p CONFIRM="Is this correct? (y/n): "
if /i not "%CONFIRM%"=="y" if /i not "%CONFIRM%"=="yes" (
    echo [ERROR] Setup cancelled.
    pause
    exit /b 1
)

REM Check if we're already in a git repository
if exist ".git" (
    echo [WARNING] This directory is already a git repository.
    set /p CONTINUE="Do you want to continue? This will add a new remote. (y/n): "
    if /i not "!CONTINUE!"=="y" if /i not "!CONTINUE!"=="yes" (
        echo [ERROR] Setup cancelled.
        pause
        exit /b 1
    )
    set EXISTING_REPO=true
) else (
    set EXISTING_REPO=false
)

echo.
echo [INFO] Setting up local git repository...

REM Initialize git repository if not exists
if "%EXISTING_REPO%"=="false" (
    git init
    echo [SUCCESS] Git repository initialized
)

REM Create .env file from template if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [SUCCESS] Created .env file from template
        echo [WARNING] Please edit .env file with your actual configuration values
    ) else (
        echo [WARNING] .env.example not found, skipping .env creation
    )
)

REM Add all files to git
echo [INFO] Adding files to git...
git add .

REM Check if there are any changes to commit
git diff --staged --quiet
if errorlevel 1 (
    REM Create initial commit
    echo [INFO] Creating initial commit...
    git commit -m "Initial commit: Advanced RAG Research Ecosystem

- Complete database schema with 20+ models for research ecosystem
- Research Memory Engine with persistent context management
- Intelligent Research Planner with AI-powered roadmap generation
- Research Quality Assurance Engine with automated validation
- Comprehensive API endpoints and service architecture
- Real-time intelligence and personalization integration
- Multilingual research support framework
- Impact prediction and optimization capabilities
- Ethics compliance and funding assistance frameworks
- Reproducibility engine and trend analysis systems
- Collaboration matchmaking and team optimization
- Full documentation and setup guides
- Production-ready configuration and deployment files

Features implemented:
✅ Research Memory & Context Persistence
✅ Intelligent Research Planning & Roadmapping  
✅ Research Quality Assurance & Validation
🏗️ Cross-Language Research Support (Framework)
🏗️ Research Impact Prediction & Optimization (Framework)
🏗️ Automated Research Ethics & Compliance (Framework)
🏗️ Research Funding & Grant Assistant (Framework)
🏗️ Research Reproducibility Engine (Framework)
🏗️ Research Trend Prediction & Early Warning (Framework)
🏗️ Research Collaboration Matchmaking (Framework)

This represents a transformative advancement in AI-powered research assistance,
providing researchers with an intelligent, adaptive, and comprehensive research
companion that supports the entire research lifecycle from ideation to publication
and impact measurement."

    echo [SUCCESS] Initial commit created
) else (
    echo [WARNING] No changes to commit
)

REM Set main branch
echo [INFO] Setting main branch...
git branch -M main

REM Add remote origin
echo [INFO] Adding GitHub remote...
set REPO_URL=https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git

REM Check if remote already exists
git remote get-url origin >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Remote 'origin' already exists
    set /p UPDATE_REMOTE="Do you want to update it? (y/n): "
    if /i "!UPDATE_REMOTE!"=="y" (
        git remote set-url origin !REPO_URL!
        echo [SUCCESS] Remote origin updated
    )
) else (
    git remote add origin %REPO_URL%
    echo [SUCCESS] Remote origin added
)

REM Push to GitHub
echo.
echo [INFO] Pushing to GitHub...
echo [WARNING] Make sure you have created the repository on GitHub first!
echo [WARNING] Repository should be at: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
echo.

set /p REPO_CREATED="Have you created the repository on GitHub? (y/n): "
if /i not "%REPO_CREATED%"=="y" if /i not "%REPO_CREATED%"=="yes" (
    echo.
    echo [WARNING] Please create the repository on GitHub first:
    echo 1. Go to https://github.com/new
    echo 2. Repository name: %REPO_NAME%
    echo 3. Description: AI-powered research assistance platform with comprehensive research lifecycle support
    echo 4. Choose Public or Private
    echo 5. Do NOT initialize with README, .gitignore, or license (we have them already)
    echo 6. Click 'Create repository'
    echo.
    pause
)

REM Attempt to push
echo [INFO] Pushing to GitHub...
git push -u origin main
if errorlevel 1 (
    echo [ERROR] Failed to push to GitHub
    echo.
    echo Common solutions:
    echo 1. Make sure the repository exists on GitHub
    echo 2. Check your GitHub authentication (username/password or SSH key)
    echo 3. Verify the repository URL is correct
    echo 4. Try using a personal access token instead of password
    echo.
    echo Manual push command:
    echo git push -u origin main
    pause
    exit /b 1
) else (
    echo [SUCCESS] Successfully pushed to GitHub! 🎉
    echo.
    echo 🔗 Your repository is now available at:
    echo    https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
    echo.
    echo 📋 Next steps:
    echo 1. Edit .env file with your actual configuration
    echo 2. Set up your development environment
    echo 3. Review and customize the README.md
    echo 4. Set up GitHub Actions for CI/CD (optional)
    echo 5. Enable GitHub features like Issues, Projects, and Discussions
    echo.
    echo 📚 Documentation:
    echo - Setup Guide: GITHUB_SETUP_GUIDE.md
    echo - User Guide: docs/USER_GUIDE.md
    echo - Implementation Summary: FINAL_ADVANCED_ECOSYSTEM_SUMMARY.md
    echo.
    echo [SUCCESS] Setup complete! Happy researching! 🚀
    pause
)

endlocal