#!/bin/bash

# Advanced RAG Research Ecosystem - GitHub Setup Script
# This script helps you set up the GitHub repository quickly

set -e  # Exit on any error

echo "🚀 Advanced RAG Research Ecosystem - GitHub Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

print_success "Git is installed ✓"

# Get repository information
echo ""
print_status "Please provide your GitHub repository information:"
echo ""

read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter your repository name (default: advanced-rag-research-ecosystem): " REPO_NAME
REPO_NAME=${REPO_NAME:-advanced-rag-research-ecosystem}

echo ""
print_status "Repository URL will be: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""

read -p "Is this correct? (y/n): " CONFIRM
if [[ $CONFIRM != [yY] && $CONFIRM != [yY][eE][sS] ]]; then
    print_error "Setup cancelled."
    exit 1
fi

# Check if we're already in a git repository
if [ -d ".git" ]; then
    print_warning "This directory is already a git repository."
    read -p "Do you want to continue? This will add a new remote. (y/n): " CONTINUE
    if [[ $CONTINUE != [yY] && $CONTINUE != [yY][eE][sS] ]]; then
        print_error "Setup cancelled."
        exit 1
    fi
    EXISTING_REPO=true
else
    EXISTING_REPO=false
fi

echo ""
print_status "Setting up local git repository..."

# Initialize git repository if not exists
if [ "$EXISTING_REPO" = false ]; then
    git init
    print_success "Git repository initialized"
fi

# Create .env file from template if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env file from template"
        print_warning "Please edit .env file with your actual configuration values"
    else
        print_warning ".env.example not found, skipping .env creation"
    fi
fi

# Add all files to git
print_status "Adding files to git..."
git add .

# Check if there are any changes to commit
if git diff --staged --quiet; then
    print_warning "No changes to commit"
else
    # Create initial commit
    print_status "Creating initial commit..."
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

    print_success "Initial commit created"
fi

# Set main branch
print_status "Setting main branch..."
git branch -M main

# Add remote origin
print_status "Adding GitHub remote..."
REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"

# Check if remote already exists
if git remote get-url origin &> /dev/null; then
    print_warning "Remote 'origin' already exists"
    read -p "Do you want to update it? (y/n): " UPDATE_REMOTE
    if [[ $UPDATE_REMOTE == [yY] || $UPDATE_REMOTE == [yY][eE][sS] ]]; then
        git remote set-url origin $REPO_URL
        print_success "Remote origin updated"
    fi
else
    git remote add origin $REPO_URL
    print_success "Remote origin added"
fi

# Push to GitHub
echo ""
print_status "Pushing to GitHub..."
print_warning "Make sure you have created the repository on GitHub first!"
print_warning "Repository should be at: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""

read -p "Have you created the repository on GitHub? (y/n): " REPO_CREATED
if [[ $REPO_CREATED != [yY] && $REPO_CREATED != [yY][eE][sS] ]]; then
    echo ""
    print_warning "Please create the repository on GitHub first:"
    echo "1. Go to https://github.com/new"
    echo "2. Repository name: $REPO_NAME"
    echo "3. Description: AI-powered research assistance platform with comprehensive research lifecycle support"
    echo "4. Choose Public or Private"
    echo "5. Do NOT initialize with README, .gitignore, or license (we have them already)"
    echo "6. Click 'Create repository'"
    echo ""
    read -p "Press Enter when you've created the repository..."
fi

# Attempt to push
print_status "Pushing to GitHub..."
if git push -u origin main; then
    print_success "Successfully pushed to GitHub! 🎉"
    echo ""
    echo "🔗 Your repository is now available at:"
    echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo ""
    echo "📋 Next steps:"
    echo "1. Edit .env file with your actual configuration"
    echo "2. Set up your development environment"
    echo "3. Review and customize the README.md"
    echo "4. Set up GitHub Actions for CI/CD (optional)"
    echo "5. Enable GitHub features like Issues, Projects, and Discussions"
    echo ""
    echo "📚 Documentation:"
    echo "- Setup Guide: GITHUB_SETUP_GUIDE.md"
    echo "- User Guide: docs/USER_GUIDE.md"
    echo "- Implementation Summary: FINAL_ADVANCED_ECOSYSTEM_SUMMARY.md"
    echo ""
    print_success "Setup complete! Happy researching! 🚀"
else
    print_error "Failed to push to GitHub"
    echo ""
    echo "Common solutions:"
    echo "1. Make sure the repository exists on GitHub"
    echo "2. Check your GitHub authentication (username/password or SSH key)"
    echo "3. Verify the repository URL is correct"
    echo "4. Try using a personal access token instead of password"
    echo ""
    echo "Manual push command:"
    echo "git push -u origin main"
    exit 1
fi