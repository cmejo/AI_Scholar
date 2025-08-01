#!/bin/bash

# Quick Git Update Script for AI Scholar Advanced RAG
# Simple script for fast commits and pushes

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Quick Git Update${NC}"
echo ""

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Get commit message from user or use default
if [ -n "$1" ]; then
    COMMIT_MSG="$1"
else
    COMMIT_MSG="feat: Update AI Scholar with latest improvements

- Enhanced production monitoring and testing
- Progressive Web App (PWA) implementation
- Mobile accessibility improvements
- Comprehensive documentation updates
- Infrastructure and deployment enhancements"
fi

echo -e "${YELLOW}📝 Commit message:${NC}"
echo "$COMMIT_MSG"
echo ""

# Show what will be committed
echo -e "${YELLOW}📋 Files to be committed:${NC}"
git status --porcelain | head -20
if [ $(git status --porcelain | wc -l) -gt 20 ]; then
    echo "... and $(( $(git status --porcelain | wc -l) - 20 )) more files"
fi
echo ""

# Confirm
read -p "Continue? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 0
fi

# Add all files
echo -e "${BLUE}📦 Staging files...${NC}"
git add .

# Commit
echo -e "${BLUE}💾 Creating commit...${NC}"
git commit -m "$COMMIT_MSG"

# Push
echo -e "${BLUE}🚀 Pushing to remote...${NC}"
BRANCH=$(git branch --show-current)
git push origin "$BRANCH"

# Success
echo ""
echo -e "${GREEN}✅ Successfully updated repository!${NC}"
echo -e "${GREEN}📍 Branch: $BRANCH${NC}"
echo -e "${GREEN}🔗 Commit: $(git rev-parse --short HEAD)${NC}"
echo ""
echo -e "${YELLOW}💡 Tip: Use './scripts/git/update_repo.sh' for comprehensive updates with tags and release notes${NC}"