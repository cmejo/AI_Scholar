#!/bin/bash

# Script to set up branch protection rules for quality gates
# This script uses GitHub CLI to configure branch protection

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed. Please install it first:"
    echo "  - macOS: brew install gh"
    echo "  - Ubuntu: sudo apt install gh"
    echo "  - Windows: winget install GitHub.cli"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    print_error "Not authenticated with GitHub CLI. Please run 'gh auth login' first."
    exit 1
fi

# Get repository information
REPO_OWNER=$(gh repo view --json owner --jq '.owner.login' 2>/dev/null || echo "")
REPO_NAME=$(gh repo view --json name --jq '.name' 2>/dev/null || echo "")

if [[ -z "$REPO_OWNER" || -z "$REPO_NAME" ]]; then
    print_error "Could not determine repository information. Make sure you're in a git repository."
    exit 1
fi

print_status "Setting up branch protection for $REPO_OWNER/$REPO_NAME"

# Branches to protect
BRANCHES=("main" "develop")

for BRANCH in "${BRANCHES[@]}"; do
    print_status "Setting up protection for branch: $BRANCH"
    
    # Check if branch exists
    if ! gh api "repos/$REPO_OWNER/$REPO_NAME/branches/$BRANCH" &> /dev/null; then
        print_warning "Branch '$BRANCH' does not exist, skipping..."
        continue
    fi
    
    # Set up branch protection
    if gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "repos/$REPO_OWNER/$REPO_NAME/branches/$BRANCH/protection" \
        --input .github/branch-protection-config.json; then
        print_success "Branch protection configured for '$BRANCH'"
    else
        print_error "Failed to configure branch protection for '$BRANCH'"
    fi
done

print_status "Branch protection setup complete!"
print_status "The following status checks are now required:"
echo "  ✓ Quality Gate Status Check"
echo "  ✓ Frontend Quality Checks"
echo "  ✓ Backend Quality Checks"
echo "  ✓ Integration Tests"
echo ""
print_success "Quality gates are now enforced! PRs cannot be merged until all checks pass."