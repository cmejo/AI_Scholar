#!/bin/bash
# Comprehensive analysis runner script
# Orchestrates all analysis tools for Ubuntu compatibility review

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESULTS_DIR="$PROJECT_ROOT/analysis-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$RESULTS_DIR/comprehensive-analysis-$TIMESTAMP.json"
HTML_REPORT="$RESULTS_DIR/analysis-report-$TIMESTAMP.html"

# Default options
VERBOSE=false
SKIP_INSTALL=false
PARALLEL=true
GENERATE_HTML=true
UBUNTU_FOCUS=true

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

# Help function
show_help() {
    cat << EOF
Comprehensive Codebase Analysis Tool for Ubuntu Compatibility

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -s, --skip-install      Skip tool installation check
    -p, --no-parallel       Disable parallel execution
    -n, --no-html           Skip HTML report generation
    -u, --no-ubuntu-focus   Disable Ubuntu-specific checks
    -o, --output DIR        Output directory (default: analysis-results)
    -r, --root DIR          Project root directory (default: current directory)

Examples:
    $0                      Run full analysis with default settings
    $0 -v -o /tmp/results   Run with verbose output to custom directory
    $0 -s -n                Skip installation and HTML generation

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -s|--skip-install)
                SKIP_INSTALL=true
                shift
                ;;
            -p|--no-parallel)
                PARALLEL=false
                shift
                ;;
            -n|--no-html)
                GENERATE_HTML=false
                shift
                ;;
            -u|--no-ubuntu-focus)
                UBUNTU_FOCUS=false
                shift
                ;;
            -o|--output)
                RESULTS_DIR="$2"
                REPORT_FILE="$RESULTS_DIR/comprehensive-analysis-$TIMESTAMP.json"
                HTML_REPORT="$RESULTS_DIR/analysis-report-$TIMESTAMP.html"
                shift 2
                ;;
            -r|--root)
                PROJECT_ROOT="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/package.json" ]]; then
        log_error "package.json not found. Please run from project root."
        exit 1
    fi
    
    # Create results directory
    mkdir -p "$RESULTS_DIR"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Install or check analysis tools
setup_tools() {
    if [[ "$SKIP_INSTALL" == "true" ]]; then
        log_info "Skipping tool installation check"
        return 0
    fi
    
    log_step "Setting up analysis tools..."
    
    # Check if installation script exists
    if [[ -f "$SCRIPT_DIR/install-analysis-tools.sh" ]]; then
        log_info "Running tool installation script..."
        bash "$SCRIPT_DIR/install-analysis-tools.sh"
    else
        log_warning "Installation script not found, assuming tools are already installed"
    fi
    
    log_success "Tools setup complete"
}

# Run Python backend analysis
analyze_python_backend() {
    log_step "Analyzing Python backend..."
    
    local backend_dir="$PROJECT_ROOT/backend"
    if [[ ! -d "$backend_dir" ]]; then
        log_warning "Backend directory not found, skipping Python analysis"
        return 0
    fi
    
    cd "$backend_dir"
    
    # Create temporary results directory
    local temp_results="$RESULTS_DIR/python-temp"
    mkdir -p "$temp_results"
    
    # Run analysis tools
    local tools=()
    
    if [[ "$PARALLEL" == "true" ]]; then
        # Run tools in parallel
        log_debug "Running Python tools in parallel..."
        
        # Flake8
        (flake8 . --config setup.cfg --output-file "$temp_results/flake8.txt" 2>&1 || true) &
        tools+=($!)
        
        # Black check
        (python -m black --check --diff . > "$temp_results/black.txt" 2>&1 || true) &
        tools+=($!)
        
        # MyPy
        (python -m mypy . > "$temp_results/mypy.txt" 2>&1 || true) &
        tools+=($!)
        
        # Bandit
        (python -m bandit -r . -f json -o "$temp_results/bandit.json" 2>&1 || true) &
        tools+=($!)
        
        # Pylint
        (python -m pylint . --output-format=json > "$temp_results/pylint.json" 2>&1 || true) &
        tools+=($!)
        
        # Safety
        (python -m safety check --json --output "$temp_results/safety.json" 2>&1 || true) &
        tools+=($!)
        
        # Wait for all tools to complete
        for pid in "${tools[@]}"; do
            wait "$pid"
        done
    else
        # Run tools sequentially
        log_debug "Running Python tools sequentially..."
        
        flake8 . --config setup.cfg --output-file "$temp_results/flake8.txt" 2>&1 || true
        python -m black --check --diff . > "$temp_results/black.txt" 2>&1 || true
        python -m mypy . > "$temp_results/mypy.txt" 2>&1 || true
        python -m bandit -r . -f json -o "$temp_results/bandit.json" 2>&1 || true
        python -m pylint . --output-format=json > "$temp_results/pylint.json" 2>&1 || true
        python -m safety check --json --output "$temp_results/safety.json" 2>&1 || true
    fi
    
    cd "$PROJECT_ROOT"
    log_success "Python backend analysis complete"
}

# Run TypeScript frontend analysis
analyze_typescript_frontend() {
    log_step "Analyzing TypeScript frontend..."
    
    cd "$PROJECT_ROOT"
    
    # Create temporary results directory
    local temp_results="$RESULTS_DIR/typescript-temp"
    mkdir -p "$temp_results"
    
    # Install dependencies if needed
    if [[ ! -d "node_modules" ]]; then
        log_info "Installing Node.js dependencies..."
        npm install
    fi
    
    # Run analysis tools
    local tools=()
    
    if [[ "$PARALLEL" == "true" ]]; then
        # Run tools in parallel
        log_debug "Running TypeScript tools in parallel..."
        
        # ESLint
        (npm run lint -- --format json --output-file "$temp_results/eslint.json" 2>&1 || true) &
        tools+=($!)
        
        # Prettier check
        (npm run format:check > "$temp_results/prettier.txt" 2>&1 || true) &
        tools+=($!)
        
        # TypeScript compiler
        (npm run type-check > "$temp_results/typescript.txt" 2>&1 || true) &
        tools+=($!)
        
        # npm audit
        (npm audit --json > "$temp_results/npm-audit.json" 2>&1 || true) &
        tools+=($!)
        
        # Wait for all tools to complete
        for pid in "${tools[@]}"; do
            wait "$pid"
        done
    else
        # Run tools sequentially
        log_debug "Running TypeScript tools sequentially..."
        
        npm run lint -- --format json --output-file "$temp_results/eslint.json" 2>&1 || true
        npm run format:check > "$temp_results/prettier.txt" 2>&1 || true
        npm run type-check > "$temp_results/typescript.txt" 2>&1 || true
        npm audit --json > "$temp_results/npm-audit.json" 2>&1 || true
    fi
    
    log_success "TypeScript frontend analysis complete"
}

# Run Docker and configuration analysis
analyze_docker_configs() {
    log_step "Analyzing Docker and configuration files..."
    
    cd "$PROJECT_ROOT"
    
    # Create temporary results directory
    local temp_results="$RESULTS_DIR/docker-temp"
    mkdir -p "$temp_results"
    
    # Run analysis tools
    local tools=()
    
    if [[ "$PARALLEL" == "true" ]]; then
        # Run tools in parallel
        log_debug "Running Docker tools in parallel..."
        
        # Hadolint on all Dockerfiles
        (find . -name "Dockerfile*" -type f | xargs -I {} hadolint --format json {} > "$temp_results/hadolint.json" 2>&1 || true) &
        tools+=($!)
        
        # YAML lint
        (find . -name "*.yml" -o -name "*.yaml" | xargs yamllint -f parsable > "$temp_results/yamllint.txt" 2>&1 || true) &
        tools+=($!)
        
        # Shellcheck
        (find . -name "*.sh" -type f | xargs shellcheck --format json > "$temp_results/shellcheck.json" 2>&1 || true) &
        tools+=($!)
        
        # Docker Deployment Validator
        (python3 "$SCRIPT_DIR/docker_deployment_validator.py" --json --output "$temp_results/docker-deployment.json" 2>&1 || true) &
        tools+=($!)
        
        # Wait for all tools to complete
        for pid in "${tools[@]}"; do
            wait "$pid"
        done
    else
        # Run tools sequentially
        log_debug "Running Docker tools sequentially..."
        
        find . -name "Dockerfile*" -type f | xargs -I {} hadolint --format json {} > "$temp_results/hadolint.json" 2>&1 || true
        find . -name "*.yml" -o -name "*.yaml" | xargs yamllint -f parsable > "$temp_results/yamllint.txt" 2>&1 || true
        find . -name "*.sh" -type f | xargs shellcheck --format json > "$temp_results/shellcheck.json" 2>&1 || true
        python3 "$SCRIPT_DIR/docker_deployment_validator.py" --json --output "$temp_results/docker-deployment.json" 2>&1 || true
    fi
    
    log_success "Docker and configuration analysis complete"
}

# Run Ubuntu-specific compatibility checks
analyze_ubuntu_compatibility() {
    if [[ "$UBUNTU_FOCUS" == "false" ]]; then
        log_info "Skipping Ubuntu-specific analysis"
        return 0
    fi
    
    log_step "Running Ubuntu compatibility checks..."
    
    cd "$PROJECT_ROOT"
    
    # Create temporary results directory
    local temp_results="$RESULTS_DIR/ubuntu-temp"
    mkdir -p "$temp_results"
    
    # Check for Ubuntu-specific issues
    log_debug "Checking for Ubuntu-specific patterns..."
    
    # Check shell scripts for Ubuntu compatibility
    if command -v shellcheck &> /dev/null; then
        find . -name "*.sh" -type f -exec shellcheck --shell=bash --format=json {} \; > "$temp_results/ubuntu-shell-check.json" 2>&1 || true
    fi
    
    # Check for hardcoded paths that might not work on Ubuntu
    grep -r "/usr/local" --include="*.py" --include="*.js" --include="*.ts" --include="*.sh" . > "$temp_results/hardcoded-paths.txt" 2>&1 || true
    
    # Check for Windows-specific line endings
    find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.sh" \) -exec file {} \; | grep CRLF > "$temp_results/line-endings.txt" 2>&1 || true
    
    # Check Docker base images for Ubuntu compatibility
    grep -r "FROM" --include="Dockerfile*" . | grep -v ubuntu > "$temp_results/non-ubuntu-base-images.txt" 2>&1 || true
    
    log_success "Ubuntu compatibility checks complete"
}

# Run security analysis
analyze_security() {
    log_step "Running security analysis..."
    
    cd "$PROJECT_ROOT"
    
    # Create temporary results directory
    local temp_results="$RESULTS_DIR/security-temp"
    mkdir -p "$temp_results"
    
    # Run security tools
    local tools=()
    
    if [[ "$PARALLEL" == "true" ]]; then
        # Run tools in parallel
        log_debug "Running security tools in parallel..."
        
        # Trivy for container scanning
        if command -v trivy &> /dev/null; then
            (find . -name "Dockerfile*" -type f | head -1 | xargs trivy config --format json > "$temp_results/trivy.json" 2>&1 || true) &
            tools+=($!)
        fi
        
        # Grype for vulnerability scanning
        if command -v grype &> /dev/null; then
            (grype . --output json > "$temp_results/grype.json" 2>&1 || true) &
            tools+=($!)
        fi
        
        # Wait for all tools to complete
        for pid in "${tools[@]}"; do
            wait "$pid"
        done
    else
        # Run tools sequentially
        log_debug "Running security tools sequentially..."
        
        if command -v trivy &> /dev/null; then
            find . -name "Dockerfile*" -type f | head -1 | xargs trivy config --format json > "$temp_results/trivy.json" 2>&1 || true
        fi
        
        if command -v grype &> /dev/null; then
            grype . --output json > "$temp_results/grype.json" 2>&1 || true
        fi
    fi
    
    log_success "Security analysis complete"
}

# Aggregate results
aggregate_results() {
    log_step "Aggregating analysis results..."
    
    cd "$PROJECT_ROOT"
    
    # Run the main Python analysis script
    if [[ -f "$SCRIPT_DIR/codebase-analysis.py" ]]; then
        python3 "$SCRIPT_DIR/codebase-analysis.py" --output "$REPORT_FILE" --project-root "$PROJECT_ROOT" $([ "$VERBOSE" == "true" ] && echo "--verbose")
    else
        log_error "Main analysis script not found"
        exit 1
    fi
    
    log_success "Results aggregated to $REPORT_FILE"
}

# Generate HTML report
generate_html_report() {
    if [[ "$GENERATE_HTML" == "false" ]]; then
        log_info "Skipping HTML report generation"
        return 0
    fi
    
    log_step "Generating HTML report..."
    
    # Create HTML report generator script
    cat > "$SCRIPT_DIR/generate-html-report.py" << 'EOF'
#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

def generate_html_report(json_file, html_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .summary-card .number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .severity-critical {{ color: #dc3545; }}
        .severity-high {{ color: #fd7e14; }}
        .severity-medium {{ color: #ffc107; }}
        .severity-low {{ color: #28a745; }}
        .severity-info {{ color: #17a2b8; }}
        .results-section {{ margin-bottom: 30px; }}
        .tool-result {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        .tool-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .tool-name {{ font-weight: bold; font-size: 1.2em; }}
        .tool-status {{ padding: 4px 8px; border-radius: 4px; color: white; font-size: 0.9em; }}
        .status-success {{ background-color: #28a745; }}
        .status-failed {{ background-color: #dc3545; }}
        .issues-list {{ margin-top: 10px; }}
        .issue {{ margin-bottom: 10px; padding: 10px; border-left: 4px solid #ddd; background: #f8f9fa; }}
        .issue-header {{ font-weight: bold; margin-bottom: 5px; }}
        .issue-details {{ font-size: 0.9em; color: #666; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Codebase Analysis Report</h1>
            <p>Generated on {data.get('analysis_timestamp', 'Unknown')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tools</h3>
                <div class="number">{data.get('total_tools_run', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Successful</h3>
                <div class="number">{data.get('successful_tools', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="number">{data.get('failed_tools', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Total Issues</h3>
                <div class="number">{data.get('total_issues_found', 0)}</div>
            </div>
        </div>
        
        <div class="results-section">
            <h2>Analysis Results</h2>
"""
    
    for result in data.get('results', []):
        tool_name = result.get('tool_name', 'Unknown')
        success = result.get('success', False)
        issues = result.get('issues', [])
        execution_time = result.get('execution_time', 0)
        error_message = result.get('error_message', '')
        
        status_class = 'status-success' if success else 'status-failed'
        status_text = 'Success' if success else 'Failed'
        
        html_content += f"""
            <div class="tool-result">
                <div class="tool-header">
                    <span class="tool-name">{tool_name}</span>
                    <span class="tool-status {status_class}">{status_text}</span>
                </div>
                <div>Execution time: {execution_time:.2f}s | Issues found: {len(issues)}</div>
                {f'<div style="color: red; margin-top: 5px;">Error: {error_message}</div>' if error_message else ''}
                
                <div class="issues-list">
"""
        
        for issue in issues:
            severity = issue.get('severity', 'info')
            issue_type = issue.get('type', 'unknown')
            description = issue.get('description', 'No description')
            file_path = issue.get('file_path', 'Unknown file')
            line_number = issue.get('line_number', '')
            recommendation = issue.get('recommendation', 'No recommendation')
            
            line_info = f":{line_number}" if line_number else ""
            
            html_content += f"""
                    <div class="issue">
                        <div class="issue-header">
                            <span class="severity-{severity}">[{severity.upper()}]</span>
                            {issue_type.replace('_', ' ').title()}
                        </div>
                        <div class="issue-details">
                            <strong>File:</strong> {file_path}{line_info}<br>
                            <strong>Description:</strong> {description}<br>
                            <strong>Recommendation:</strong> {recommendation}
                        </div>
                    </div>
"""
        
        html_content += """
                </div>
            </div>
"""
    
    html_content += f"""
        </div>
        
        <div class="footer">
            <p>Report generated by AI Scholar Codebase Analysis Tool</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(html_file, 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate-html-report.py <json_file> <html_file>")
        sys.exit(1)
    
    generate_html_report(sys.argv[1], sys.argv[2])
EOF
    
    # Generate the HTML report
    python3 "$SCRIPT_DIR/generate-html-report.py" "$REPORT_FILE" "$HTML_REPORT"
    
    log_success "HTML report generated: $HTML_REPORT"
}

# Cleanup temporary files
cleanup() {
    log_step "Cleaning up temporary files..."
    
    # Remove temporary result directories
    rm -rf "$RESULTS_DIR"/*-temp 2>/dev/null || true
    
    log_success "Cleanup complete"
}

# Main execution function
main() {
    log_info "Starting comprehensive codebase analysis..."
    log_info "Project root: $PROJECT_ROOT"
    log_info "Results directory: $RESULTS_DIR"
    
    # Parse command line arguments
    parse_args "$@"
    
    # Setup
    check_prerequisites
    setup_tools
    
    # Run analysis phases
    analyze_python_backend
    analyze_typescript_frontend
    analyze_docker_configs
    analyze_ubuntu_compatibility
    analyze_security
    
    # Generate reports
    aggregate_results
    generate_html_report
    
    # Cleanup
    cleanup
    
    log_success "Comprehensive analysis complete!"
    log_info "JSON Report: $REPORT_FILE"
    if [[ "$GENERATE_HTML" == "true" ]]; then
        log_info "HTML Report: $HTML_REPORT"
    fi
    
    # Show summary
    if [[ -f "$REPORT_FILE" ]]; then
        local total_issues=$(python3 -c "import json; data=json.load(open('$REPORT_FILE')); print(data.get('total_issues_found', 0))")
        local successful_tools=$(python3 -c "import json; data=json.load(open('$REPORT_FILE')); print(data.get('successful_tools', 0))")
        local total_tools=$(python3 -c "import json; data=json.load(open('$REPORT_FILE')); print(data.get('total_tools_run', 0))")
        
        echo
        log_info "Analysis Summary:"
        log_info "  Total issues found: $total_issues"
        log_info "  Successful tools: $successful_tools/$total_tools"
        echo
        
        if [[ $total_issues -gt 0 ]]; then
            log_warning "Issues found! Please review the reports for details."
            exit 1
        else
            log_success "No issues found! Codebase looks good."
        fi
    fi
}

# Run main function with all arguments
main "$@"