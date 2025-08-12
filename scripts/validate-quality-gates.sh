#!/bin/bash

# Script to validate that quality gates are properly configured
# This script checks all the necessary files and configurations

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

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Initialize validation results
VALIDATION_ERRORS=0
VALIDATION_WARNINGS=0

validate_file() {
    local file_path="$1"
    local description="$2"
    
    if [ -f "$file_path" ]; then
        print_success "$description exists: $file_path"
    else
        print_error "$description missing: $file_path"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
    fi
}

validate_directory() {
    local dir_path="$1"
    local description="$2"
    
    if [ -d "$dir_path" ]; then
        print_success "$description exists: $dir_path"
    else
        print_warning "$description missing: $dir_path"
        VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
    fi
}

validate_npm_script() {
    local script_name="$1"
    local description="$2"
    
    if npm run "$script_name" --silent 2>/dev/null | grep -q "Missing script"; then
        print_error "$description script missing: $script_name"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
    else
        print_success "$description script exists: $script_name"
    fi
}

print_header "QUALITY GATES VALIDATION"

print_status "Validating quality gates configuration..."

# Check core configuration files
print_status "Checking core configuration files..."
validate_file ".github/workflows/quality-check.yml" "GitHub Actions workflow"
validate_file "package.json" "Package configuration"
validate_file "eslint.config.js" "ESLint configuration"
validate_file "tsconfig.json" "TypeScript configuration"
validate_file "tsconfig.app.json" "TypeScript app configuration"
validate_file "vitest.config.ts" "Vitest configuration"
validate_file ".prettierrc" "Prettier configuration"

# Check backend configuration files
print_status "Checking backend configuration files..."
validate_file "backend/pyproject.toml" "Python project configuration"
validate_file "backend/.flake8" "Flake8 configuration"
validate_file "backend/pytest.ini" "Pytest configuration"
validate_file "backend/requirements.txt" "Python dependencies"
validate_file "backend/requirements-dev.txt" "Python dev dependencies"

# Check quality gates specific files
print_status "Checking quality gates specific files..."
validate_file ".github/quality-gates-config.yml" "Quality gates configuration"
validate_file ".github/branch-protection-config.json" "Branch protection configuration"
validate_file ".github/QUALITY_GATES.md" "Quality gates documentation"
validate_file "scripts/quality-check.sh" "Quality check script"
validate_file "scripts/setup-branch-protection.sh" "Branch protection setup script"

# Check directories
print_status "Checking required directories..."
validate_directory ".github/workflows" "GitHub workflows directory"
validate_directory "scripts" "Scripts directory"
validate_directory "src" "Source code directory"
validate_directory "backend" "Backend directory"

# Check npm scripts
print_status "Checking npm scripts..."
validate_npm_script "lint" "ESLint"
validate_npm_script "type-check" "TypeScript compilation"
validate_npm_script "format:check" "Prettier format check"
validate_npm_script "test:coverage" "Test coverage"
validate_npm_script "backend:lint" "Backend linting"
validate_npm_script "backend:type-check" "Backend type checking"
validate_npm_script "backend:format:check" "Backend format check"

# Check if husky is configured
print_status "Checking pre-commit hooks..."
if [ -d ".husky" ]; then
    print_success "Husky pre-commit hooks configured"
    if [ -f ".husky/pre-commit" ]; then
        print_success "Pre-commit hook exists"
    else
        print_warning "Pre-commit hook file missing"
        VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
    fi
else
    print_warning "Husky not configured - pre-commit hooks may not work"
    VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
fi

# Check if lint-staged is configured
print_status "Checking lint-staged configuration..."
if grep -q "lint-staged" package.json; then
    print_success "lint-staged configuration found in package.json"
else
    print_warning "lint-staged configuration not found"
    VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
fi

# Test basic functionality
print_status "Testing basic functionality..."

# Test TypeScript compilation
if npm run type-check --silent >/dev/null 2>&1; then
    print_success "TypeScript compilation test passed"
else
    print_error "TypeScript compilation test failed"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

# Test ESLint
if npm run lint --silent >/dev/null 2>&1; then
    print_success "ESLint test passed"
else
    print_warning "ESLint test failed (may have linting issues to fix)"
    VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
fi

# Test Prettier
if npm run format:check --silent >/dev/null 2>&1; then
    print_success "Prettier format check passed"
else
    print_warning "Prettier format check failed (may need formatting)"
    VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
fi

# Check backend tools if backend exists
if [ -d "backend" ]; then
    cd backend
    
    # Check if Python virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
        
        # Test Python tools
        if python -m black --check . >/dev/null 2>&1; then
            print_success "Python Black formatting test passed"
        else
            print_warning "Python Black formatting test failed"
            VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
        fi
        
        if python -m flake8 . >/dev/null 2>&1; then
            print_success "Python flake8 linting test passed"
        else
            print_warning "Python flake8 linting test failed"
            VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
        fi
        
        if python -m mypy . >/dev/null 2>&1; then
            print_success "Python mypy type checking test passed"
        else
            print_warning "Python mypy type checking test failed"
            VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
        fi
    else
        print_warning "Python virtual environment not found - backend tests skipped"
        VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
    fi
    
    cd ..
fi

# Summary
print_header "VALIDATION SUMMARY"

print_status "Validation Results:"
echo "  Errors: $VALIDATION_ERRORS"
echo "  Warnings: $VALIDATION_WARNINGS"

if [ $VALIDATION_ERRORS -eq 0 ]; then
    print_success "✅ Quality gates validation passed!"
    
    if [ $VALIDATION_WARNINGS -gt 0 ]; then
        print_warning "⚠️ $VALIDATION_WARNINGS warning(s) found - consider addressing them"
    fi
    
    echo ""
    print_status "Quality gates are properly configured and ready to use!"
    print_status "Next steps:"
    echo "  1. Run './scripts/setup-branch-protection.sh' to enable branch protection"
    echo "  2. Test the full quality check with './scripts/quality-check.sh'"
    echo "  3. Review the documentation in '.github/QUALITY_GATES.md'"
    
    exit 0
else
    print_error "❌ Quality gates validation failed with $VALIDATION_ERRORS error(s)"
    print_error "Please fix the missing files and configurations before proceeding"
    exit 1
fi