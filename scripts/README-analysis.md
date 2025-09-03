# Comprehensive Codebase Analysis Infrastructure

This directory contains a comprehensive analysis infrastructure for the AI Scholar project, designed specifically for Ubuntu compatibility and code quality review.

## Overview

The analysis infrastructure provides:

- **Python Backend Analysis**: flake8, black, mypy, bandit, pylint, safety
- **TypeScript/React Frontend Analysis**: ESLint, Prettier, TypeScript compiler, npm audit
- **Docker & Configuration Analysis**: Hadolint, YAML lint, Shellcheck
- **Ubuntu Compatibility Checks**: Shell script validation, path checking, line ending validation
- **Security Analysis**: Trivy, Grype, dependency vulnerability scanning
- **Automated Reporting**: JSON and HTML reports with issue prioritization

## Quick Start

### 1. Install Analysis Tools

Run the installation script to set up all required tools:

```bash
./scripts/install-analysis-tools.sh
```

This will install:
- System dependencies (shellcheck, yamllint, etc.)
- Docker and Hadolint
- Node.js analysis tools
- Python analysis tools in a virtual environment
- Security scanning tools

### 2. Test Setup

Verify that all tools are properly installed:

```bash
python3 scripts/test-analysis-setup.py
```

### 3. Run Analysis

Execute comprehensive analysis:

```bash
# Full analysis with all features
./scripts/run-comprehensive-analysis.sh

# Verbose output
./scripts/run-comprehensive-analysis.sh -v

# Skip tool installation check
./scripts/run-comprehensive-analysis.sh -s

# Custom output directory
./scripts/run-comprehensive-analysis.sh -o /path/to/results
```

### 4. View Results

Results are generated in multiple formats:
- **JSON Report**: `analysis-results/comprehensive-analysis-TIMESTAMP.json`
- **HTML Report**: `analysis-results/analysis-report-TIMESTAMP.html`

## File Structure

```
scripts/
├── codebase-analysis.py           # Main analysis orchestrator
├── run-comprehensive-analysis.sh  # Comprehensive analysis runner
├── install-analysis-tools.sh      # Tool installation script
├── test-analysis-setup.py         # Setup verification script
├── analysis-requirements.txt      # Python tool dependencies
└── README-analysis.md             # This documentation

# Configuration files (project root)
├── .hadolint.yaml                 # Docker analysis config
├── .yamllint.yml                  # YAML analysis config
├── .eslintrc.analysis.js          # Enhanced ESLint config
├── backend/setup.cfg              # Python flake8 config
└── backend/.pylintrc              # Python pylint config
```

## Configuration Files

### Python Analysis Configuration

- **`backend/setup.cfg`**: Flake8 configuration with Ubuntu-specific rules
- **`backend/.pylintrc`**: Comprehensive Pylint configuration
- **`backend/pyproject.toml`**: Black, isort, mypy, and other tool configurations

### TypeScript/React Analysis Configuration

- **`.eslintrc.analysis.js`**: Enhanced ESLint configuration with comprehensive rules
- **`.prettierrc`**: Code formatting configuration
- **`eslint.config.js`**: Main ESLint configuration (extended by analysis config)

### Docker and Infrastructure Configuration

- **`.hadolint.yaml`**: Docker best practices and Ubuntu compatibility rules
- **`.yamllint.yml`**: YAML file validation with Docker Compose focus
- Shell scripts are analyzed with Shellcheck for Ubuntu bash compatibility

## Analysis Categories

### 1. Code Quality Issues
- Syntax errors and compilation issues
- Type checking and annotation problems
- Code style and formatting violations
- Import organization and dependency issues

### 2. Security Vulnerabilities
- Dependency vulnerabilities (Python and Node.js)
- Code security issues (Bandit analysis)
- Container security problems (Trivy/Grype)
- File permission and access control issues

### 3. Ubuntu Compatibility
- Shell script compatibility with Ubuntu bash
- Docker base image and package compatibility
- File path and permission issues
- Line ending problems (CRLF vs LF)

### 4. Performance Issues
- Inefficient code patterns
- Bundle size and optimization opportunities
- Database query performance
- Memory and CPU usage patterns

### 5. Technical Debt
- Code complexity and maintainability
- Documentation coverage
- Test coverage gaps
- Outdated dependencies

## Issue Severity Levels

- **CRITICAL**: Blocks deployment or core functionality
- **HIGH**: Significant impact on reliability or security
- **MEDIUM**: Moderate impact, should be addressed
- **LOW**: Minor improvement opportunities
- **INFO**: Informational, no immediate action required

## Ubuntu-Specific Checks

The analysis includes specific checks for Ubuntu server compatibility:

1. **Shell Script Compatibility**: Validates bash scripts for Ubuntu-specific features
2. **Docker Base Images**: Checks for Ubuntu-compatible base images
3. **Package Dependencies**: Validates system package availability on Ubuntu
4. **File Permissions**: Checks for Ubuntu-compatible file permissions
5. **Path Handling**: Identifies hardcoded paths that may not work on Ubuntu
6. **Line Endings**: Detects Windows line endings that cause issues on Ubuntu

## Command Line Options

### Main Analysis Script (`codebase-analysis.py`)

```bash
python3 scripts/codebase-analysis.py [OPTIONS]

Options:
  -o, --output FILE     Output file for results (default: analysis-results.json)
  -r, --root DIR        Project root directory (default: current directory)
  -v, --verbose         Enable verbose logging
  -h, --help            Show help message
```

### Comprehensive Runner (`run-comprehensive-analysis.sh`)

```bash
./scripts/run-comprehensive-analysis.sh [OPTIONS]

Options:
  -h, --help              Show help message
  -v, --verbose           Enable verbose output
  -s, --skip-install      Skip tool installation check
  -p, --no-parallel       Disable parallel execution
  -n, --no-html           Skip HTML report generation
  -u, --no-ubuntu-focus   Disable Ubuntu-specific checks
  -o, --output DIR        Output directory (default: analysis-results)
  -r, --root DIR          Project root directory (default: current directory)
```

## Integration with CI/CD

The analysis tools can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions integration
- name: Run Codebase Analysis
  run: |
    ./scripts/install-analysis-tools.sh
    ./scripts/run-comprehensive-analysis.sh -s -n
    
- name: Upload Analysis Results
  uses: actions/upload-artifact@v3
  with:
    name: analysis-results
    path: analysis-results/
```

## Troubleshooting

### Common Issues

1. **Tool Installation Failures**
   - Ensure you're running on Ubuntu or compatible Linux distribution
   - Check internet connectivity for package downloads
   - Verify you have sudo privileges for system package installation

2. **Permission Errors**
   - Make sure scripts are executable: `chmod +x scripts/*.sh`
   - Check file permissions in the project directory

3. **Python Virtual Environment Issues**
   - Ensure Python 3.9+ is installed
   - Check that `python3-venv` package is available

4. **Node.js Dependency Issues**
   - Run `npm install` to ensure all dependencies are available
   - Check Node.js version compatibility (requires Node 16+)

### Getting Help

1. Run the test script to identify specific issues:
   ```bash
   python3 scripts/test-analysis-setup.py
   ```

2. Check the installation log for detailed error messages

3. Run analysis with verbose output for debugging:
   ```bash
   ./scripts/run-comprehensive-analysis.sh -v
   ```

## Extending the Analysis

### Adding New Tools

1. Add tool installation to `install-analysis-tools.sh`
2. Add tool execution to `codebase-analysis.py`
3. Add configuration file if needed
4. Update test script to verify the new tool

### Custom Rules

1. Modify configuration files for existing tools
2. Add custom patterns to the analysis script
3. Update issue classification in the main script

### Output Formats

The analysis results are structured JSON that can be easily processed by other tools or integrated into dashboards and monitoring systems.

## Performance Considerations

- **Parallel Execution**: Tools run in parallel by default for faster analysis
- **Incremental Analysis**: Consider running only specific tool categories for faster feedback
- **Resource Usage**: Large codebases may require significant memory and CPU resources
- **Timeout Handling**: Long-running tools have timeout protection

## Security Considerations

- Analysis tools run with user privileges (not root)
- Temporary files are cleaned up after analysis
- No sensitive data is logged or stored in results
- Network access is only required for tool installation and updates