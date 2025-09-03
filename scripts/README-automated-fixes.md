# Automated Fix Application System

This system provides comprehensive automated fixing capabilities for common code issues, dependency updates, configuration problems, and Ubuntu-specific optimizations.

## Overview

The Automated Fix Application System consists of several components:

1. **AutoFixEngine** - Core engine for applying various types of fixes
2. **CodeFormattingFixer** - Handles code formatting and style issues
3. **DependencyUpdater** - Updates dependencies with compatibility checking
4. **ConfigurationFixer** - Fixes configuration file issues
5. **UbuntuOptimizer** - Applies Ubuntu-specific optimizations
6. **AutomatedFixIntegration** - Integrates fixes with analysis results

## Features

### Code Formatting Fixes
- **Python**: Black formatting, isort import sorting
- **TypeScript/JavaScript**: Prettier formatting, ESLint auto-fixes
- **Automatic backup creation** before applying changes

### Dependency Updates
- **Python**: Updates requirements.txt with Ubuntu-compatible versions
- **Node.js**: Updates package.json dependencies
- **Compatibility checking** against Ubuntu 24.04.2 LTS
- **Version constraint validation**

### Configuration Fixes
- **Docker Compose**: Ubuntu-compatible base images, volume optimizations
- **Dockerfiles**: Ubuntu-specific optimizations, layer caching
- **JSON/YAML**: Proper formatting and validation
- **Environment files**: Syntax and structure validation

### Ubuntu Optimizations
- **Shell scripts**: Ubuntu-compatible commands, error handling
- **Docker configurations**: Ubuntu-specific networking and storage
- **Package management**: apt optimizations over apk
- **Permission and path fixes**

## Usage

### Standalone Mode

Run specific types of fixes without analysis integration:

```bash
# Apply all fix types
python scripts/run_automated_fixes.py

# Apply specific fix types
python scripts/run_automated_fixes.py --fix-types formatting dependencies

# Dry run to see what would be fixed
python scripts/run_automated_fixes.py --dry-run

# Apply fixes to specific project
python scripts/run_automated_fixes.py --project-root /path/to/project
```

### Integrated Mode

Run fixes based on analysis results:

```bash
# Run integrated analysis and fixes
python scripts/run_automated_fixes.py --integrated

# Use existing analysis report
python scripts/run_automated_fixes.py --integrated --analysis-report report.json

# Dry run with integration
python scripts/run_automated_fixes.py --integrated --dry-run
```

### Configuration

Create and customize configuration:

```bash
# Create default configuration file
python scripts/run_automated_fixes.py --create-config
```

Edit `scripts/automated_fix_config.json`:

```json
{
  "auto_apply_safe_fixes": true,
  "require_confirmation_for_medium_risk": true,
  "skip_high_risk_fixes": true,
  "create_backups": true,
  "max_fixes_per_run": 50,
  "fix_types_enabled": {
    "code_formatting": true,
    "dependency_updates": true,
    "configuration_fixes": true,
    "ubuntu_optimizations": true
  }
}
```

## Fix Types and Risk Levels

### Fix Types

1. **CODE_FORMATTING** - Safe formatting and style fixes
2. **DEPENDENCY_UPDATE** - Package version updates
3. **CONFIGURATION_FIX** - Configuration file corrections
4. **UBUNTU_OPTIMIZATION** - Ubuntu-specific improvements
5. **SECURITY_FIX** - Security vulnerability fixes

### Risk Levels

1. **SAFE** - No risk, can be applied automatically
2. **LOW_RISK** - Minimal risk, may require confirmation
3. **MEDIUM_RISK** - Some risk, requires review
4. **HIGH_RISK** - High risk, manual intervention needed

## Examples

### Basic Usage

```python
from automated_fix_engine import AutoFixEngine

# Initialize fix engine
fix_engine = AutoFixEngine(".")

# Apply code formatting fixes
formatting_results = fix_engine.apply_code_formatting_fixes()

# Apply dependency updates
dependency_results = fix_engine.apply_dependency_updates()

# Generate report
report = fix_engine.generate_fix_report()
```

### Integrated Usage

```python
from automated_fix_integration import AutomatedFixIntegration

# Initialize integration system
integration = AutomatedFixIntegration(".")

# Run analysis and apply fixes
report = integration.analyze_and_fix()

# Save report
integration.save_integrated_report("fix_report.json")
```

## Supported File Types

### Code Files
- **Python**: `.py` files
- **TypeScript**: `.ts`, `.tsx` files
- **JavaScript**: `.js`, `.jsx` files

### Configuration Files
- **Docker**: `Dockerfile*`, `docker-compose*.yml`
- **Package management**: `requirements.txt`, `package.json`
- **Config files**: `.json`, `.yml`, `.yaml`, `.env*`

### Scripts
- **Shell scripts**: `.sh` files
- **Deployment scripts**: Various deployment automation scripts

## Ubuntu Compatibility

The system is specifically designed for Ubuntu 24.04.2 LTS compatibility:

### Python Environment
- Python 3.11 support
- Ubuntu-compatible package versions
- System library dependencies

### Node.js Environment
- Node.js 20 LTS support
- Ubuntu-compatible npm packages
- Build tool compatibility

### Docker Environment
- Ubuntu-based container images
- Ubuntu-specific Docker configurations
- Volume mounting optimizations

## Testing

Run the test suite:

```bash
# Run all tests
python scripts/test_automated_fix_engine.py

# Run specific test class
python -m pytest scripts/test_automated_fix_engine.py::TestAutoFixEngine -v
```

## Demo

Run the demonstration:

```bash
# Run comprehensive demo
python scripts/demo_automated_fixes.py

# Run specific demo type
python scripts/demo_automated_fixes.py --demo-type formatting
python scripts/demo_automated_fixes.py --demo-type dependencies
python scripts/demo_automated_fixes.py --demo-type config
python scripts/demo_automated_fixes.py --demo-type ubuntu
python scripts/demo_automated_fixes.py --demo-type integrated
```

## Output Reports

### Standalone Report Format

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "total_fixes": 15,
  "successful_fixes": 14,
  "failed_fixes": 1,
  "results": [
    {
      "success": true,
      "fix_type": "code_formatting",
      "file_path": "backend/main.py",
      "description": "Applied Python code formatting",
      "changes_made": ["Applied black formatting", "Sorted imports with isort"],
      "backup_created": true
    }
  ]
}
```

### Integrated Report Format

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "analysis_summary": {
    "total_issues": 25
  },
  "fix_recommendations": {
    "total_recommendations": 20,
    "auto_applicable": 15,
    "requires_review": 5
  },
  "applied_fixes": {
    "total_applied": 15,
    "successful": 14,
    "failed": 1
  },
  "remaining_issues": {
    "total_original": 25,
    "fixed": 14,
    "remaining": 11,
    "fix_rate": 56.0
  }
}
```

## Backup and Recovery

### Automatic Backups
- All modified files are automatically backed up
- Backups stored in `.fix_backups/` directory
- Timestamped backup files for version tracking

### Manual Recovery
```bash
# List available backups
ls .fix_backups/

# Restore from backup
cp .fix_backups/main.py_20240101_120000.backup backend/main.py
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Automated Fixes
on: [push, pull_request]

jobs:
  automated-fixes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          npm install
      - name: Run automated fixes
        run: |
          python scripts/run_automated_fixes.py --integrated --dry-run
      - name: Upload fix report
        uses: actions/upload-artifact@v3
        with:
          name: fix-report
          path: integrated_fix_report_*.json
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure write permissions on project files
   - Check backup directory permissions

2. **Tool Dependencies**
   - Install required formatting tools: `pip install black isort`
   - Install Node.js tools: `npm install -g prettier eslint`

3. **Configuration Errors**
   - Validate JSON configuration syntax
   - Check file path patterns in config

### Debug Mode

Enable verbose logging:

```bash
python scripts/run_automated_fixes.py --verbose
```

### Dry Run Testing

Always test with dry run first:

```bash
python scripts/run_automated_fixes.py --dry-run
```

## Contributing

### Adding New Fix Types

1. Extend the `FixType` enum
2. Implement fix logic in appropriate fixer class
3. Add configuration mapping
4. Update tests and documentation

### Adding New File Types

1. Update file pattern matching in `_should_skip_file`
2. Add file type detection logic
3. Implement specific fix methods
4. Add test cases

## Requirements

### Python Dependencies
- `pyyaml` - YAML file processing
- `toml` - TOML file processing (if needed)
- `subprocess` - External tool execution

### External Tools
- `black` - Python code formatting
- `isort` - Python import sorting
- `prettier` - JavaScript/TypeScript formatting
- `eslint` - JavaScript/TypeScript linting

### System Requirements
- Ubuntu 24.04.2 LTS (recommended)
- Python 3.11+
- Node.js 20 LTS
- Docker 24.0+

## License

This automated fix system is part of the AI Scholar project and follows the same licensing terms.