#!/bin/bash

# AI Scholar Project - Add All Files to Git
echo "🚀 Adding AI Scholar project files to git..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Run 'git init' first."
    exit 1
fi

# Add backend implementation files
echo "📁 Adding backend files..."
git add backend/services/
git add backend/api/
git add backend/core/
git add backend/tests/
git add backend/*.py
git add backend/requirements.txt

# Add frontend files
echo "🎨 Adding frontend files..."
git add frontend/
git add src/

# Add documentation
echo "📚 Adding documentation..."
git add docs/
git add *.md

# Add configuration files
echo "⚙️ Adding configuration files..."
git add *.yml
git add *.json
git add *.sh
git add *.bat
git add config/
git add monitoring/
git add scripts/

# Add Kiro specs
echo "📋 Adding Kiro specifications..."
git add .kiro/specs/

# Add other important files
echo "📄 Adding other project files..."
git add package.json
git add requirements.txt
git add Dockerfile*
git add docker-compose*.yml
git add .gitignore
git add nginx/
git add security/

# Show status
echo "📊 Current git status:"
git status

echo ""
echo "✅ Files added! Ready to commit with:"
echo "git commit -m 'feat: Complete AI Scholar advanced research ecosystem'"
echo ""
echo "Then push with:"
echo "git push origin main"