#!/bin/bash

# Repository Reorganization Script
# This script will reorganize your repository files into a clean, logical structure

echo "🚀 Starting repository reorganization..."

# Create new directory structure
echo "📁 Creating directory structure..."
mkdir -p docs/setup
mkdir -p docs/implementation/task-summaries
mkdir -p docs/guides
mkdir -p scripts/setup
mkdir -p scripts/deployment
mkdir -p config/dockerfiles

# Move documentation files to docs/setup/
echo "📚 Moving setup documentation..."
mv DEPLOYMENT_GUIDE.md docs/setup/ 2>/dev/null || echo "DEPLOYMENT_GUIDE.md not found"
mv QUICK_LAUNCH_GUIDE.md docs/setup/ 2>/dev/null || echo "QUICK_LAUNCH_GUIDE.md not found"
mv SERVER_LAUNCH_PLAN.md docs/setup/ 2>/dev/null || echo "SERVER_LAUNCH_PLAN.md not found"
mv GITHUB_SETUP_GUIDE.md docs/setup/ 2>/dev/null || echo "GITHUB_SETUP_GUIDE.md not found"
mv INTEGRATION_GUIDE.md docs/setup/ 2>/dev/null || echo "INTEGRATION_GUIDE.md not found"
mv PUSH_TO_GITHUB_INSTRUCTIONS.md docs/setup/ 2>/dev/null || echo "PUSH_TO_GITHUB_INSTRUCTIONS.md not found"

# Move guide documentation to docs/guides/
echo "📖 Moving guide documentation..."
mv FILE_ORGANIZATION_GUIDE.md docs/guides/ 2>/dev/null || echo "FILE_ORGANIZATION_GUIDE.md not found"
mv GIT_ORGANIZATION_STRATEGY.md docs/guides/ 2>/dev/null || echo "GIT_ORGANIZATION_STRATEGY.md not found"
mv ADDITIONAL_CONFIG_SUMMARY.md docs/guides/ 2>/dev/null || echo "ADDITIONAL_CONFIG_SUMMARY.md not found"
mv DEPLOYMENT_CHECKLIST.md docs/guides/ 2>/dev/null || echo "DEPLOYMENT_CHECKLIST.md not found"

# Move implementation summaries to docs/implementation/
echo "📊 Moving implementation summaries..."
mv PHASE_1_IMPLEMENTATION_SUMMARY.md docs/implementation/ 2>/dev/null || echo "PHASE_1_IMPLEMENTATION_SUMMARY.md not found"
mv PHASES_2_3_4_IMPLEMENTATION_SUMMARY.md docs/implementation/ 2>/dev/null || echo "PHASES_2_3_4_IMPLEMENTATION_SUMMARY.md not found"
mv PHASE_7_8_COMPLETION_SUMMARY.md docs/implementation/ 2>/dev/null || echo "PHASE_7_8_COMPLETION_SUMMARY.md not found"
mv FINAL_IMPLEMENTATION_SUMMARY.md docs/implementation/ 2>/dev/null || echo "FINAL_IMPLEMENTATION_SUMMARY.md not found"
mv FINAL_ADVANCED_ECOSYSTEM_SUMMARY.md docs/implementation/ 2>/dev/null || echo "FINAL_ADVANCED_ECOSYSTEM_SUMMARY.md not found"
mv COMPREHENSIVE_IMPLEMENTATION_SUMMARY.md docs/implementation/ 2>/dev/null || echo "COMPREHENSIVE_IMPLEMENTATION_SUMMARY.md not found"
mv ADVANCED_ECOSYSTEM_IMPLEMENTATION_STATUS.md docs/implementation/ 2>/dev/null || echo "ADVANCED_ECOSYSTEM_IMPLEMENTATION_STATUS.md not found"

# Move task summaries to docs/implementation/task-summaries/
echo "📋 Moving task summaries..."
mv TASK_8_3_IMPLEMENTATION_SUMMARY.md docs/implementation/task-summaries/ 2>/dev/null || echo "TASK_8_3_IMPLEMENTATION_SUMMARY.md not found"
mv TASK_10_1_IMPLEMENTATION_SUMMARY.md docs/implementation/task-summaries/ 2>/dev/null || echo "TASK_10_1_IMPLEMENTATION_SUMMARY.md not found"
mv TASK_10_2_IMPLEMENTATION_SUMMARY.md docs/implementation/task-summaries/ 2>/dev/null || echo "TASK_10_2_IMPLEMENTATION_SUMMARY.md not found"
mv TASK_10_3_IMPLEMENTATION_SUMMARY.md docs/implementation/task-summaries/ 2>/dev/null || echo "TASK_10_3_IMPLEMENTATION_SUMMARY.md not found"
mv TASK_11_IMPLEMENTATION_SUMMARY.md docs/implementation/task-summaries/ 2>/dev/null || echo "TASK_11_IMPLEMENTATION_SUMMARY.md not found"

# Move setup scripts to scripts/setup/
echo "🔧 Moving setup scripts..."
mv setup_github.sh scripts/setup/ 2>/dev/null || echo "setup_github.sh not found"
mv setup_github.bat scripts/setup/ 2>/dev/null || echo "setup_github.bat not found"
mv add_to_git.sh scripts/setup/ 2>/dev/null || echo "add_to_git.sh not found"

# Move deployment scripts to scripts/deployment/ (if not already there)
echo "🚀 Organizing deployment scripts..."
if [ -f scripts/deploy.sh ]; then
    mv scripts/deploy.sh scripts/deployment/ 2>/dev/null || echo "deploy.sh already in place"
fi
if [ -f scripts/production-deploy.sh ]; then
    mv scripts/production-deploy.sh scripts/deployment/ 2>/dev/null || echo "production-deploy.sh already in place"
fi
if [ -f scripts/backup.sh ]; then
    mv scripts/backup.sh scripts/deployment/ 2>/dev/null || echo "backup.sh already in place"
fi
if [ -f scripts/health-check.sh ]; then
    mv scripts/health-check.sh scripts/deployment/ 2>/dev/null || echo "health-check.sh already in place"
fi
if [ -f scripts/maintenance.sh ]; then
    mv scripts/maintenance.sh scripts/deployment/ 2>/dev/null || echo "maintenance.sh already in place"
fi
if [ -f scripts/update.sh ]; then
    mv scripts/update.sh scripts/deployment/ 2>/dev/null || echo "update.sh already in place"
fi
if [ -f scripts/validate-deployment.sh ]; then
    mv scripts/validate-deployment.sh scripts/deployment/ 2>/dev/null || echo "validate-deployment.sh already in place"
fi

# Move configuration files to config/
echo "⚙️ Moving configuration files..."
mv .env.production config/ 2>/dev/null || echo ".env.production not found"
mv docker-compose.prod.yml config/ 2>/dev/null || echo "docker-compose.prod.yml not found"
mv nginx.conf config/ 2>/dev/null || echo "nginx.conf not found"
mv nginx.prod.conf config/ 2>/dev/null || echo "nginx.prod.conf not found"

# Move Dockerfiles to config/dockerfiles/
echo "🐳 Moving Dockerfiles..."
mv Dockerfile.backend config/dockerfiles/ 2>/dev/null || echo "Dockerfile.backend not found"
mv Dockerfile.frontend config/dockerfiles/ 2>/dev/null || echo "Dockerfile.frontend not found"
mv Dockerfile.streamlit config/dockerfiles/ 2>/dev/null || echo "Dockerfile.streamlit not found"
mv Dockerfile.backup config/dockerfiles/ 2>/dev/null || echo "Dockerfile.backup not found"

# Create a new organized README for the docs directory
echo "📝 Creating documentation index..."
cat > docs/README.md << 'EOF'
# Documentation

This directory contains all project documentation organized by category.

## Directory Structure

- **setup/** - Setup and deployment guides
- **implementation/** - Implementation summaries and progress reports
- **guides/** - User guides and configuration documentation

## Quick Links

### Setup & Deployment
- [Deployment Guide](setup/DEPLOYMENT_GUIDE.md)
- [Quick Launch Guide](setup/QUICK_LAUNCH_GUIDE.md)
- [Server Launch Plan](setup/SERVER_LAUNCH_PLAN.md)
- [GitHub Setup Guide](setup/GITHUB_SETUP_GUIDE.md)

### User Guides
- [User Guide](USER_GUIDE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [File Organization Guide](guides/FILE_ORGANIZATION_GUIDE.md)

### Implementation Status
- [Final Implementation Summary](implementation/FINAL_IMPLEMENTATION_SUMMARY.md)
- [Advanced Ecosystem Summary](implementation/FINAL_ADVANCED_ECOSYSTEM_SUMMARY.md)
- [Implementation Status](implementation/ADVANCED_ECOSYSTEM_IMPLEMENTATION_STATUS.md)
EOF

# Create a scripts README
echo "🔧 Creating scripts documentation..."
cat > scripts/README.md << 'EOF'
# Scripts

This directory contains all project scripts organized by purpose.

## Directory Structure

- **setup/** - Initial setup and configuration scripts
- **deployment/** - Production deployment and maintenance scripts
- **dev.sh** - Development environment script
- **setup.sh** - Main setup script

## Setup Scripts
- `setup/setup_github.sh` - GitHub repository setup (Linux/Mac)
- `setup/setup_github.bat` - GitHub repository setup (Windows)
- `setup/add_to_git.sh` - Add files to git repository

## Deployment Scripts
- `deployment/deploy.sh` - Main deployment script
- `deployment/production-deploy.sh` - Production deployment
- `deployment/backup.sh` - Backup script
- `deployment/health-check.sh` - Health check script
- `deployment/maintenance.sh` - Maintenance script
- `deployment/update.sh` - Update script
- `deployment/validate-deployment.sh` - Deployment validation

## Usage

Make scripts executable:
```bash
chmod +x scripts/**/*.sh
```

Run setup:
```bash
./scripts/setup.sh
```

Deploy to production:
```bash
./scripts/deployment/production-deploy.sh
```
EOF

# Create a config README
echo "⚙️ Creating config documentation..."
cat > config/README.md << 'EOF'
# Configuration

This directory contains all configuration files for the project.

## Files

- `.env.production` - Production environment variables
- `docker-compose.prod.yml` - Production Docker Compose configuration
- `nginx.conf` - Nginx configuration
- `nginx.prod.conf` - Production Nginx configuration

## Dockerfiles

The `dockerfiles/` directory contains all Docker build files:
- `Dockerfile.backend` - Backend service
- `Dockerfile.frontend` - Frontend service
- `Dockerfile.streamlit` - Streamlit app service
- `Dockerfile.backup` - Backup service

## Usage

Copy example environment file:
```bash
cp .env.example .env
```

For production:
```bash
cp config/.env.production .env
```

Build with specific Dockerfile:
```bash
docker build -f config/dockerfiles/Dockerfile.backend -t backend .
```
EOF

# Update main README to reflect new structure
echo "📄 Updating main README..."
if [ -f README.md ]; then
    # Add a note about the new organization at the top
    temp_file=$(mktemp)
    echo "# AI Scholar - Advanced Research Ecosystem" > "$temp_file"
    echo "" >> "$temp_file"
    echo "## 📁 Repository Organization" >> "$temp_file"
    echo "" >> "$temp_file"
    echo "This repository has been organized for better navigation:" >> "$temp_file"
    echo "" >> "$temp_file"
    echo "- **docs/** - All documentation (setup guides, implementation summaries, user guides)" >> "$temp_file"
    echo "- **scripts/** - Setup and deployment scripts" >> "$temp_file"
    echo "- **config/** - Configuration files and Dockerfiles" >> "$temp_file"
    echo "- **backend/** - Backend services and APIs" >> "$temp_file"
    echo "- **frontend/** - Frontend application" >> "$temp_file"
    echo "" >> "$temp_file"
    echo "## 🚀 Quick Start" >> "$temp_file"
    echo "" >> "$temp_file"
    echo "1. See [Quick Launch Guide](docs/setup/QUICK_LAUNCH_GUIDE.md) for immediate setup" >> "$temp_file"
    echo "2. See [Deployment Guide](docs/setup/DEPLOYMENT_GUIDE.md) for production deployment" >> "$temp_file"
    echo "3. See [User Guide](docs/USER_GUIDE.md) for usage instructions" >> "$temp_file"
    echo "" >> "$temp_file"
    echo "---" >> "$temp_file"
    echo "" >> "$temp_file"
    
    # Append the rest of the existing README
    tail -n +1 README.md >> "$temp_file"
    mv "$temp_file" README.md
fi

# Clean up any empty directories
echo "🧹 Cleaning up..."
find . -type d -empty -delete 2>/dev/null || true

# Make scripts executable
echo "🔐 Making scripts executable..."
chmod +x scripts/**/*.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

echo ""
echo "✅ Repository reorganization complete!"
echo ""
echo "📊 Summary of changes:"
echo "  • Documentation moved to docs/ directory"
echo "  • Scripts organized in scripts/ directory"
echo "  • Configuration files moved to config/ directory"
echo "  • Created README files for each directory"
echo "  • Updated main README with new structure"
echo ""
echo "🔄 Next steps:"
echo "  1. Review the changes: git status"
echo "  2. Add to git: git add ."
echo "  3. Commit: git commit -m 'Reorganize repository structure'"
echo "  4. Push: git push origin main"
echo ""
echo "📁 New structure:"
echo "  docs/setup/          - Setup and deployment guides"
echo "  docs/implementation/ - Implementation summaries"
echo "  docs/guides/         - User and configuration guides"
echo "  scripts/setup/       - Setup scripts"
echo "  scripts/deployment/  - Deployment scripts"
echo "  config/              - Configuration files"
echo "  config/dockerfiles/  - Docker build files"