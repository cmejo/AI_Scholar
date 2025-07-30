@echo off
REM Repository Reorganization Script for Windows
REM This script will reorganize your repository files into a clean, logical structure

echo 🚀 Starting repository reorganization...

REM Create new directory structure
echo 📁 Creating directory structure...
mkdir docs\setup 2>nul
mkdir docs\implementation\task-summaries 2>nul
mkdir docs\guides 2>nul
mkdir scripts\setup 2>nul
mkdir scripts\deployment 2>nul
mkdir config\dockerfiles 2>nul

REM Move documentation files to docs\setup\
echo 📚 Moving setup documentation...
move DEPLOYMENT_GUIDE.md docs\setup\ 2>nul
move QUICK_LAUNCH_GUIDE.md docs\setup\ 2>nul
move SERVER_LAUNCH_PLAN.md docs\setup\ 2>nul
move GITHUB_SETUP_GUIDE.md docs\setup\ 2>nul
move INTEGRATION_GUIDE.md docs\setup\ 2>nul
move PUSH_TO_GITHUB_INSTRUCTIONS.md docs\setup\ 2>nul

REM Move guide documentation to docs\guides\
echo 📖 Moving guide documentation...
move FILE_ORGANIZATION_GUIDE.md docs\guides\ 2>nul
move GIT_ORGANIZATION_STRATEGY.md docs\guides\ 2>nul
move ADDITIONAL_CONFIG_SUMMARY.md docs\guides\ 2>nul
move DEPLOYMENT_CHECKLIST.md docs\guides\ 2>nul

REM Move implementation summaries to docs\implementation\
echo 📊 Moving implementation summaries...
move PHASE_1_IMPLEMENTATION_SUMMARY.md docs\implementation\ 2>nul
move PHASES_2_3_4_IMPLEMENTATION_SUMMARY.md docs\implementation\ 2>nul
move PHASE_7_8_COMPLETION_SUMMARY.md docs\implementation\ 2>nul
move FINAL_IMPLEMENTATION_SUMMARY.md docs\implementation\ 2>nul
move FINAL_ADVANCED_ECOSYSTEM_SUMMARY.md docs\implementation\ 2>nul
move COMPREHENSIVE_IMPLEMENTATION_SUMMARY.md docs\implementation\ 2>nul
move ADVANCED_ECOSYSTEM_IMPLEMENTATION_STATUS.md docs\implementation\ 2>nul

REM Move task summaries to docs\implementation\task-summaries\
echo 📋 Moving task summaries...
move TASK_8_3_IMPLEMENTATION_SUMMARY.md docs\implementation\task-summaries\ 2>nul
move TASK_10_1_IMPLEMENTATION_SUMMARY.md docs\implementation\task-summaries\ 2>nul
move TASK_10_2_IMPLEMENTATION_SUMMARY.md docs\implementation\task-summaries\ 2>nul
move TASK_10_3_IMPLEMENTATION_SUMMARY.md docs\implementation\task-summaries\ 2>nul
move TASK_11_IMPLEMENTATION_SUMMARY.md docs\implementation\task-summaries\ 2>nul

REM Move setup scripts to scripts\setup\
echo 🔧 Moving setup scripts...
move setup_github.sh scripts\setup\ 2>nul
move setup_github.bat scripts\setup\ 2>nul
move add_to_git.sh scripts\setup\ 2>nul

REM Move deployment scripts to scripts\deployment\
echo 🚀 Organizing deployment scripts...
if exist scripts\deploy.sh move scripts\deploy.sh scripts\deployment\ 2>nul
if exist scripts\production-deploy.sh move scripts\production-deploy.sh scripts\deployment\ 2>nul
if exist scripts\backup.sh move scripts\backup.sh scripts\deployment\ 2>nul
if exist scripts\health-check.sh move scripts\health-check.sh scripts\deployment\ 2>nul
if exist scripts\maintenance.sh move scripts\maintenance.sh scripts\deployment\ 2>nul
if exist scripts\update.sh move scripts\update.sh scripts\deployment\ 2>nul
if exist scripts\validate-deployment.sh move scripts\validate-deployment.sh scripts\deployment\ 2>nul

REM Move configuration files to config\
echo ⚙️ Moving configuration files...
move .env.production config\ 2>nul
move docker-compose.prod.yml config\ 2>nul
move nginx.conf config\ 2>nul
move nginx.prod.conf config\ 2>nul

REM Move Dockerfiles to config\dockerfiles\
echo 🐳 Moving Dockerfiles...
move Dockerfile.backend config\dockerfiles\ 2>nul
move Dockerfile.frontend config\dockerfiles\ 2>nul
move Dockerfile.streamlit config\dockerfiles\ 2>nul
move Dockerfile.backup config\dockerfiles\ 2>nul

echo.
echo ✅ Repository reorganization complete!
echo.
echo 📊 Summary of changes:
echo   • Documentation moved to docs\ directory
echo   • Scripts organized in scripts\ directory
echo   • Configuration files moved to config\ directory
echo   • Created organized directory structure
echo.
echo 🔄 Next steps:
echo   1. Review the changes: git status
echo   2. Add to git: git add .
echo   3. Commit: git commit -m "Reorganize repository structure"
echo   4. Push: git push origin main
echo.
echo 📁 New structure:
echo   docs\setup\          - Setup and deployment guides
echo   docs\implementation\ - Implementation summaries
echo   docs\guides\         - User and configuration guides
echo   scripts\setup\       - Setup scripts
echo   scripts\deployment\  - Deployment scripts
echo   config\              - Configuration files
echo   config\dockerfiles\  - Docker build files

pause