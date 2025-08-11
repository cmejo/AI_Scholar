#!/bin/bash

# AI Scholar RAG Chatbot - Enhanced Quality Check Script
# This script runs comprehensive quality checks for both frontend and backend
# with detailed metrics collection and reporting

set -e  # Exit on any error

echo "🔍 Starting comprehensive quality checks with metrics collection..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_THRESHOLD=80
QUALITY_REPORT_DIR="quality-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Initialize metrics
FRONTEND_ERRORS=0
BACKEND_ERRORS=0
TOTAL_WARNINGS=0
FRONTEND_COVERAGE=0
BACKEND_COVERAGE=0

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

print_metric() {
    echo -e "${PURPLE}[METRIC]${NC} $1"
}

print_header() {
    echo -e "${CYAN}=== $1 ===${NC}"
}

# Function to create quality reports directory
setup_reporting() {
    mkdir -p "$QUALITY_REPORT_DIR"
    print_status "Quality reports will be saved to: $QUALITY_REPORT_DIR"
}

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Please run this script from the project root."
    exit 1
fi

# Setup reporting
setup_reporting

# Check for required tools
print_status "Checking for required tools..."
command -v jq >/dev/null 2>&1 || { print_error "jq is required but not installed. Please install jq."; exit 1; }
command -v bc >/dev/null 2>&1 || { print_error "bc is required but not installed. Please install bc."; exit 1; }

print_header "FRONTEND QUALITY CHECKS"

print_status "1. Checking TypeScript compilation..."
if npm run type-check 2>&1 | tee "$QUALITY_REPORT_DIR/typescript-check-$TIMESTAMP.log"; then
    print_success "TypeScript compilation passed"
else
    print_error "TypeScript compilation failed"
    FRONTEND_ERRORS=$((FRONTEND_ERRORS + 1))
    exit 1
fi

print_status "2. Checking code formatting..."
if npm run format:check 2>&1 | tee "$QUALITY_REPORT_DIR/prettier-check-$TIMESTAMP.log"; then
    print_success "Code formatting is correct"
else
    print_warning "Code formatting issues found. Run 'npm run format' to fix."
    TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
fi

print_status "3. Running ESLint with detailed reporting..."
if npm run lint -- --format json --output-file "$QUALITY_REPORT_DIR/eslint-report-$TIMESTAMP.json" 2>/dev/null; then
    print_success "ESLint checks passed"
    
    # Extract ESLint metrics
    if [ -f "$QUALITY_REPORT_DIR/eslint-report-$TIMESTAMP.json" ]; then
        eslint_errors=$(jq '[.[] | select(.errorCount > 0) | .errorCount] | add // 0' "$QUALITY_REPORT_DIR/eslint-report-$TIMESTAMP.json")
        eslint_warnings=$(jq '[.[] | select(.warningCount > 0) | .warningCount] | add // 0' "$QUALITY_REPORT_DIR/eslint-report-$TIMESTAMP.json")
        print_metric "ESLint Errors: $eslint_errors"
        print_metric "ESLint Warnings: $eslint_warnings"
        FRONTEND_ERRORS=$((FRONTEND_ERRORS + eslint_errors))
        TOTAL_WARNINGS=$((TOTAL_WARNINGS + eslint_warnings))
    fi
else
    print_error "ESLint checks failed"
    npm run lint  # Show detailed output
    FRONTEND_ERRORS=$((FRONTEND_ERRORS + 1))
    exit 1
fi

print_status "4. Running frontend tests with coverage..."
if npm run test:coverage -- --reporter=json --outputFile="$QUALITY_REPORT_DIR/test-results-$TIMESTAMP.json" 2>&1 | tee "$QUALITY_REPORT_DIR/test-output-$TIMESTAMP.log"; then
    print_success "Frontend tests passed"
    
    # Extract coverage metrics
    if [ -f "coverage/coverage-summary.json" ]; then
        FRONTEND_COVERAGE=$(jq -r '.total.statements.pct' coverage/coverage-summary.json 2>/dev/null || echo "0")
        print_metric "Frontend Coverage: $FRONTEND_COVERAGE%"
        
        # Copy coverage report
        cp -r coverage "$QUALITY_REPORT_DIR/frontend-coverage-$TIMESTAMP" 2>/dev/null || true
        
        # Check coverage threshold
        if (( $(echo "$FRONTEND_COVERAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
            print_warning "Frontend coverage below threshold: $FRONTEND_COVERAGE% < $COVERAGE_THRESHOLD%"
            TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
        fi
    fi
else
    print_error "Frontend tests failed"
    FRONTEND_ERRORS=$((FRONTEND_ERRORS + 1))
    exit 1
fi

print_status "5. Analyzing bundle size and performance..."
if npm run build 2>&1 | tee "$QUALITY_REPORT_DIR/build-output-$TIMESTAMP.log"; then
    print_success "Build completed successfully"
    
    # Analyze bundle size if dist directory exists
    if [ -d "dist" ]; then
        bundle_size=$(du -sh dist | cut -f1)
        print_metric "Bundle Size: $bundle_size"
        
        # List largest files
        echo "Largest bundle files:" > "$QUALITY_REPORT_DIR/bundle-analysis-$TIMESTAMP.txt"
        find dist -type f -name "*.js" -o -name "*.css" | xargs ls -lh | sort -k5 -hr | head -10 >> "$QUALITY_REPORT_DIR/bundle-analysis-$TIMESTAMP.txt"
    fi
else
    print_warning "Build failed - bundle analysis skipped"
    TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
fi

print_header "BACKEND QUALITY CHECKS"

if [ -d "backend" ]; then
    cd backend
    
    # Check if Python virtual environment exists
    if [ ! -d "venv" ]; then
        print_warning "Python virtual environment not found. Creating one..."
        python -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt -r requirements-dev.txt
    else
        source venv/bin/activate
    fi
    
    print_status "6. Checking Python code formatting..."
    if python -m black --check --diff . 2>&1 | tee "../$QUALITY_REPORT_DIR/black-check-$TIMESTAMP.log" && \
       python -m isort --check-only --diff . 2>&1 | tee "../$QUALITY_REPORT_DIR/isort-check-$TIMESTAMP.log"; then
        print_success "Python code formatting is correct"
    else
        print_warning "Python code formatting issues found. Run 'npm run backend:format' to fix."
        TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
    fi
    
    print_status "7. Running Python linting with detailed reporting..."
    if python -m flake8 --format=json --output-file="../$QUALITY_REPORT_DIR/flake8-report-$TIMESTAMP.json" . 2>/dev/null; then
        print_success "Python linting passed"
        print_metric "Flake8 Issues: 0"
    else
        flake8_errors=$(jq 'length' "../$QUALITY_REPORT_DIR/flake8-report-$TIMESTAMP.json" 2>/dev/null || echo "1")
        print_error "Python linting failed with $flake8_errors issues"
        python -m flake8 . 2>&1 | tee "../$QUALITY_REPORT_DIR/flake8-output-$TIMESTAMP.log"
        BACKEND_ERRORS=$((BACKEND_ERRORS + flake8_errors))
        cd ..
        exit 1
    fi
    
    print_status "8. Running Python type checking..."
    if python -m mypy --json-report "../$QUALITY_REPORT_DIR/mypy-report-$TIMESTAMP" . 2>&1 | tee "../$QUALITY_REPORT_DIR/mypy-output-$TIMESTAMP.log"; then
        print_success "Python type checking passed"
        print_metric "MyPy Errors: 0"
    else
        mypy_errors=$(grep -c "error:" "../$QUALITY_REPORT_DIR/mypy-output-$TIMESTAMP.log" 2>/dev/null || echo "1")
        print_error "Python type checking failed with $mypy_errors errors"
        BACKEND_ERRORS=$((BACKEND_ERRORS + mypy_errors))
        cd ..
        exit 1
    fi
    
    print_status "9. Running Python security analysis..."
    python -m bandit -r . -f json -o "../$QUALITY_REPORT_DIR/bandit-report-$TIMESTAMP.json" 2>&1 | tee "../$QUALITY_REPORT_DIR/bandit-output-$TIMESTAMP.log" || true
    
    if [ -f "../$QUALITY_REPORT_DIR/bandit-report-$TIMESTAMP.json" ]; then
        high_issues=$(jq '[.results[] | select(.issue_severity == "HIGH")] | length' "../$QUALITY_REPORT_DIR/bandit-report-$TIMESTAMP.json" 2>/dev/null || echo "0")
        medium_issues=$(jq '[.results[] | select(.issue_severity == "MEDIUM")] | length' "../$QUALITY_REPORT_DIR/bandit-report-$TIMESTAMP.json" 2>/dev/null || echo "0")
        low_issues=$(jq '[.results[] | select(.issue_severity == "LOW")] | length' "../$QUALITY_REPORT_DIR/bandit-report-$TIMESTAMP.json" 2>/dev/null || echo "0")
        
        print_metric "Security Issues - High: $high_issues, Medium: $medium_issues, Low: $low_issues"
        
        if [ "$high_issues" -gt 0 ]; then
            print_error "High-severity security issues found: $high_issues"
            BACKEND_ERRORS=$((BACKEND_ERRORS + high_issues))
            cd ..
            exit 1
        else
            print_success "No high-severity security issues found"
        fi
        
        if [ "$medium_issues" -gt 0 ]; then
            print_warning "Medium-severity security issues found: $medium_issues"
            TOTAL_WARNINGS=$((TOTAL_WARNINGS + medium_issues))
        fi
    fi
    
    print_status "10. Running dependency security check..."
    if python -m safety check --json --output "../$QUALITY_REPORT_DIR/safety-report-$TIMESTAMP.json" 2>&1 | tee "../$QUALITY_REPORT_DIR/safety-output-$TIMESTAMP.log"; then
        print_success "Dependency security check passed"
    else
        print_warning "Vulnerable dependencies found - check safety report"
        TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
    fi
    
    print_status "11. Running backend tests with coverage..."
    if python -m pytest \
        --cov=. \
        --cov-report=xml \
        --cov-report=html \
        --cov-report=json \
        --cov-report=term-missing \
        --junit-xml="../$QUALITY_REPORT_DIR/pytest-report-$TIMESTAMP.xml" \
        --tb=short 2>&1 | tee "../$QUALITY_REPORT_DIR/pytest-output-$TIMESTAMP.log"; then
        print_success "Backend tests passed"
        
        # Extract coverage metrics
        if [ -f "coverage.json" ]; then
            BACKEND_COVERAGE=$(jq -r '.totals.percent_covered' coverage.json 2>/dev/null || echo "0")
            print_metric "Backend Coverage: $BACKEND_COVERAGE%"
            
            # Copy coverage reports
            cp coverage.json "../$QUALITY_REPORT_DIR/backend-coverage-$TIMESTAMP.json" 2>/dev/null || true
            cp -r htmlcov "../$QUALITY_REPORT_DIR/backend-coverage-html-$TIMESTAMP" 2>/dev/null || true
            
            # Check coverage threshold
            if (( $(echo "$BACKEND_COVERAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
                print_warning "Backend coverage below threshold: $BACKEND_COVERAGE% < $COVERAGE_THRESHOLD%"
                TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
            fi
        fi
    else
        print_error "Backend tests failed"
        BACKEND_ERRORS=$((BACKEND_ERRORS + 1))
        cd ..
        exit 1
    fi
    
    cd ..
else
    print_warning "Backend directory not found - skipping backend checks"
    TOTAL_WARNINGS=$((TOTAL_WARNINGS + 1))
fi

print_header "QUALITY METRICS SUMMARY"

# Calculate overall metrics
TOTAL_ERRORS=$((FRONTEND_ERRORS + BACKEND_ERRORS))
if [ "$FRONTEND_COVERAGE" != "0" ] && [ "$BACKEND_COVERAGE" != "0" ]; then
    OVERALL_COVERAGE=$(echo "scale=2; ($FRONTEND_COVERAGE + $BACKEND_COVERAGE) / 2" | bc)
elif [ "$FRONTEND_COVERAGE" != "0" ]; then
    OVERALL_COVERAGE=$FRONTEND_COVERAGE
elif [ "$BACKEND_COVERAGE" != "0" ]; then
    OVERALL_COVERAGE=$BACKEND_COVERAGE
else
    OVERALL_COVERAGE=0
fi

print_metric "Total Errors: $TOTAL_ERRORS"
print_metric "Total Warnings: $TOTAL_WARNINGS"
print_metric "Frontend Coverage: $FRONTEND_COVERAGE%"
print_metric "Backend Coverage: $BACKEND_COVERAGE%"
print_metric "Overall Coverage: $OVERALL_COVERAGE%"

# Generate comprehensive quality report
print_status "Generating comprehensive quality report..."
cat > "$QUALITY_REPORT_DIR/quality-summary-$TIMESTAMP.md" << EOF
# Comprehensive Quality Check Report

**Generated on:** $(date)  
**Report ID:** $TIMESTAMP  
**Coverage Threshold:** $COVERAGE_THRESHOLD%

## 📊 Quality Metrics Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total Errors | $TOTAL_ERRORS | $([ $TOTAL_ERRORS -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL") |
| Total Warnings | $TOTAL_WARNINGS | $([ $TOTAL_WARNINGS -eq 0 ] && echo "✅ PASS" || echo "⚠️ REVIEW") |
| Frontend Coverage | $FRONTEND_COVERAGE% | $([ $(echo "$FRONTEND_COVERAGE >= $COVERAGE_THRESHOLD" | bc -l) -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL") |
| Backend Coverage | $BACKEND_COVERAGE% | $([ $(echo "$BACKEND_COVERAGE >= $COVERAGE_THRESHOLD" | bc -l) -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL") |
| Overall Coverage | $OVERALL_COVERAGE% | $([ $(echo "$OVERALL_COVERAGE >= $COVERAGE_THRESHOLD" | bc -l) -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL") |

## 🎯 Quality Gates Status

### Frontend Quality Gates
- **TypeScript Compilation:** $([ $FRONTEND_ERRORS -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")
- **Code Formatting:** ✅ CHECKED
- **ESLint Rules:** $([ $FRONTEND_ERRORS -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")
- **Unit Tests:** $([ $FRONTEND_ERRORS -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")
- **Coverage Threshold:** $([ $(echo "$FRONTEND_COVERAGE >= $COVERAGE_THRESHOLD" | bc -l) -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL")

### Backend Quality Gates
- **Code Formatting:** ✅ CHECKED
- **Linting (flake8):** $([ $BACKEND_ERRORS -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")
- **Type Checking (mypy):** $([ $BACKEND_ERRORS -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")
- **Security Analysis:** ✅ CHECKED
- **Unit Tests:** $([ $BACKEND_ERRORS -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")
- **Coverage Threshold:** $([ $(echo "$BACKEND_COVERAGE >= $COVERAGE_THRESHOLD" | bc -l) -eq 1 ] && echo "✅ PASS" || echo "❌ FAIL")

## 📁 Generated Reports

The following detailed reports have been generated in \`$QUALITY_REPORT_DIR/\`:

### Frontend Reports
- \`typescript-check-$TIMESTAMP.log\` - TypeScript compilation output
- \`prettier-check-$TIMESTAMP.log\` - Code formatting check results
- \`eslint-report-$TIMESTAMP.json\` - ESLint analysis results
- \`test-results-$TIMESTAMP.json\` - Test execution results
- \`frontend-coverage-$TIMESTAMP/\` - Coverage reports (HTML)
- \`build-output-$TIMESTAMP.log\` - Build process output
- \`bundle-analysis-$TIMESTAMP.txt\` - Bundle size analysis

### Backend Reports
- \`black-check-$TIMESTAMP.log\` - Code formatting check results
- \`isort-check-$TIMESTAMP.log\` - Import sorting check results
- \`flake8-report-$TIMESTAMP.json\` - Linting analysis results
- \`mypy-report-$TIMESTAMP/\` - Type checking detailed report
- \`bandit-report-$TIMESTAMP.json\` - Security analysis results
- \`safety-report-$TIMESTAMP.json\` - Dependency security check
- \`pytest-report-$TIMESTAMP.xml\` - Test execution results (JUnit format)
- \`backend-coverage-$TIMESTAMP.json\` - Coverage metrics
- \`backend-coverage-html-$TIMESTAMP/\` - Coverage reports (HTML)

## 🔧 Recommended Actions

$(if [ $TOTAL_ERRORS -gt 0 ]; then
    echo "### ❌ Critical Issues (Must Fix)"
    echo "- Fix $TOTAL_ERRORS error(s) before proceeding"
    echo "- Review detailed error reports above"
    echo ""
fi)

$(if [ $TOTAL_WARNINGS -gt 0 ]; then
    echo "### ⚠️ Warnings (Should Fix)"
    echo "- Address $TOTAL_WARNINGS warning(s) for better code quality"
    echo "- Run \`npm run quality:fix\` to auto-fix formatting issues"
    echo ""
fi)

$(if [ $(echo "$OVERALL_COVERAGE < $COVERAGE_THRESHOLD" | bc -l) -eq 1 ]; then
    echo "### 📈 Coverage Improvement"
    echo "- Current coverage ($OVERALL_COVERAGE%) is below threshold ($COVERAGE_THRESHOLD%)"
    echo "- Add tests for uncovered code paths"
    echo "- Review coverage reports for specific areas needing attention"
    echo ""
fi)

### 🚀 Next Steps
1. Review all generated reports in \`$QUALITY_REPORT_DIR/\`
2. Fix any critical errors identified
3. Address warnings to improve code quality
4. Improve test coverage where needed
5. Re-run quality checks to verify improvements

---
*This report was generated by the AI Scholar Quality Check System*
EOF

# Create a simple summary for quick reference
cat > "$QUALITY_REPORT_DIR/quality-status-$TIMESTAMP.txt" << EOF
QUALITY CHECK SUMMARY - $TIMESTAMP

Status: $([ $TOTAL_ERRORS -eq 0 ] && echo "PASS" || echo "FAIL")
Errors: $TOTAL_ERRORS
Warnings: $TOTAL_WARNINGS
Coverage: $OVERALL_COVERAGE%
Threshold: $COVERAGE_THRESHOLD%

$([ $TOTAL_ERRORS -eq 0 ] && echo "✅ All quality gates passed!" || echo "❌ Quality gates failed - review errors")
EOF

# Final status
if [ $TOTAL_ERRORS -eq 0 ]; then
    print_success "🎉 All quality checks completed successfully!"
    print_success "📊 Quality report generated: $QUALITY_REPORT_DIR/quality-summary-$TIMESTAMP.md"
    
    if [ $TOTAL_WARNINGS -gt 0 ]; then
        print_warning "⚠️ $TOTAL_WARNINGS warning(s) found - consider addressing them"
    fi
    
    exit 0
else
    print_error "💥 Quality checks failed with $TOTAL_ERRORS error(s)"
    print_error "📊 Detailed report: $QUALITY_REPORT_DIR/quality-summary-$TIMESTAMP.md"
    exit 1
fi