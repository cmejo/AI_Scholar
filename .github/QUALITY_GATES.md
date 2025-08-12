# Quality Gates Documentation

This document describes the comprehensive quality gates system implemented for the AI Scholar RAG Chatbot project.

## Overview

Quality gates are automated checks that ensure code quality, security, and reliability standards are maintained throughout the development lifecycle. These gates prevent low-quality code from being merged into protected branches.

## Quality Gates Structure

### 1. Frontend Quality Gates

#### TypeScript Compilation
- **Requirement**: All TypeScript code must compile without errors
- **Enforcement**: Hard gate - build fails if compilation errors exist
- **Configuration**: `tsconfig.app.json` with strict mode enabled

#### Code Formatting
- **Requirement**: All code must follow Prettier formatting standards
- **Enforcement**: Hard gate - build fails if formatting is inconsistent
- **Auto-fix**: Run `npm run format` to automatically fix formatting issues

#### ESLint Analysis
- **Requirements**:
  - Zero ESLint errors allowed
  - Maximum 10 ESLint warnings (configurable)
  - No `any` types allowed
  - All React hook dependencies must be declared
- **Enforcement**: Hard gate for errors, soft gate for warnings
- **Auto-fix**: Run `npm run lint:fix` to automatically fix many issues

#### Test Coverage
- **Requirement**: Minimum 80% code coverage
- **Enforcement**: Hard gate - build fails if coverage is below threshold
- **Reporting**: Coverage reports generated in HTML and LCOV formats

#### Bundle Size
- **Requirement**: Maximum 5MB bundle size (configurable)
- **Enforcement**: Soft gate - warning if exceeded
- **Monitoring**: Bundle analysis reports generated for optimization

### 2. Backend Quality Gates

#### Python Code Formatting
- **Requirements**:
  - Black formatting standards
  - isort import organization
- **Enforcement**: Hard gate - build fails if formatting is inconsistent
- **Auto-fix**: Run `npm run backend:format` to automatically fix formatting

#### Python Linting
- **Requirements**:
  - Zero flake8 errors allowed
  - Maximum complexity of 10 per function
  - PEP 8 compliance
- **Enforcement**: Hard gate - build fails if linting errors exist
- **Configuration**: `.flake8` and `pyproject.toml`

#### Type Checking
- **Requirements**:
  - All functions must have type hints
  - Zero mypy errors allowed
  - Strict type checking enabled
- **Enforcement**: Hard gate - build fails if type errors exist
- **Configuration**: `pyproject.toml` with strict mypy settings

#### Security Analysis
- **Requirements**:
  - Zero high-severity security issues
  - Maximum 5 medium-severity issues (configurable)
  - Dependency vulnerability scanning
- **Tools**: Bandit for code analysis, Safety for dependency scanning
- **Enforcement**: Hard gate for high-severity, soft gate for medium/low

#### Test Coverage
- **Requirement**: Minimum 80% code coverage
- **Enforcement**: Hard gate - build fails if coverage is below threshold
- **Reporting**: Coverage reports in XML, HTML, and JSON formats

### 3. Integration Quality Gates

#### End-to-End Tests
- **Requirement**: All integration tests must pass
- **Enforcement**: Hard gate - build fails if any integration test fails
- **Scope**: API endpoints, database operations, external service integrations

#### Performance Tests
- **Requirements**:
  - Build time under 10 minutes
  - Test execution under 5 minutes
- **Enforcement**: Soft gate - warnings if thresholds exceeded

## Configuration

### Environment Variables

The following environment variables control quality gate behavior:

```yaml
NODE_VERSION: '18'
PYTHON_VERSION: '3.11'
COVERAGE_THRESHOLD: 80
MAX_ESLINT_WARNINGS: 10
MAX_BUNDLE_SIZE_MB: 5
MAX_BUILD_TIME_MINUTES: 10
```

### Quality Gates Configuration

Quality thresholds can be customized in `.github/quality-gates-config.yml`:

```yaml
quality_gates:
  coverage:
    frontend_minimum: 80
    backend_minimum: 80
  errors:
    eslint_max: 0
    typescript_max: 0
  warnings:
    eslint_max: 10
```

## Branch Protection

### Protected Branches

The following branches are protected with quality gates:
- `main` - Production branch
- `develop` - Development branch

### Required Status Checks

All protected branches require these status checks to pass:
- ✅ Quality Gate Status Check
- ✅ Frontend Quality Checks
- ✅ Backend Quality Checks
- ✅ Integration Tests

### Setting Up Branch Protection

Run the setup script to configure branch protection:

```bash
./scripts/setup-branch-protection.sh
```

## Workflow Integration

### GitHub Actions Workflow

The quality gates are implemented in `.github/workflows/quality-check.yml`:

1. **Frontend Quality Job**
   - TypeScript compilation
   - Code formatting check
   - ESLint analysis
   - Unit tests with coverage
   - Bundle size analysis

2. **Backend Quality Job**
   - Python formatting check
   - Linting with flake8
   - Type checking with mypy
   - Security analysis
   - Unit tests with coverage

3. **Integration Tests Job**
   - End-to-end API tests
   - Database integration tests
   - Performance benchmarks

4. **Quality Gate Evaluation**
   - Aggregate all quality metrics
   - Generate comprehensive reports
   - Make final pass/fail decision

### Local Development

Run quality checks locally before pushing:

```bash
# Full quality check
npm run quality:check

# Auto-fix issues
npm run quality:fix

# Generate quality report
./scripts/quality-check.sh
```

## Quality Reports

### Generated Reports

Each quality check run generates detailed reports:

- **ESLint Report**: `eslint-report-{timestamp}.json`
- **Coverage Reports**: HTML and LCOV formats
- **Security Analysis**: Bandit and Safety reports
- **Test Results**: JUnit XML format
- **Quality Summary**: Comprehensive markdown report

### Report Locations

- **CI/CD Reports**: Uploaded as GitHub Actions artifacts
- **Local Reports**: Saved to `quality-reports/` directory
- **Coverage Reports**: Available in `coverage/` and `backend/htmlcov/`

### Viewing Reports

1. **GitHub Actions**: Download artifacts from workflow runs
2. **Local Development**: Open HTML reports in browser
3. **Pull Requests**: Quality summary posted as PR comment

## Troubleshooting

### Common Issues

#### TypeScript Compilation Errors
```bash
# Check specific errors
npm run type-check

# Fix common issues
npm run lint:fix
```

#### ESLint Errors
```bash
# View detailed errors
npm run lint

# Auto-fix many issues
npm run lint:fix
```

#### Test Coverage Below Threshold
```bash
# Run tests with coverage report
npm run test:coverage

# View detailed coverage report
open coverage/index.html
```

#### Python Formatting Issues
```bash
# Auto-fix formatting
npm run backend:format

# Check what would be changed
cd backend && python -m black --diff .
```

### Emergency Procedures

#### Bypassing Quality Gates

In emergency situations, quality gates can be bypassed:

1. **Temporary Bypass**: Add `[skip ci]` to commit message
2. **Admin Override**: Repository admins can force merge
3. **Emergency Branch**: Create emergency branch without protection

⚠️ **Warning**: Bypassing quality gates should only be done in critical situations and followed by immediate remediation.

## Metrics and Monitoring

### Quality Metrics Dashboard

Access quality metrics through:
- GitHub Actions workflow summaries
- Generated quality reports
- Coverage trend analysis

### Key Performance Indicators

- **Error Rate**: Number of quality gate failures per week
- **Coverage Trend**: Test coverage percentage over time
- **Build Success Rate**: Percentage of successful builds
- **Time to Fix**: Average time to resolve quality issues

### Alerts and Notifications

Configure notifications for:
- Quality gate failures
- Coverage drops below threshold
- Security vulnerabilities detected
- Build time exceeding limits

## Best Practices

### For Developers

1. **Run Local Checks**: Always run quality checks before pushing
2. **Fix Issues Early**: Address quality issues as soon as they're detected
3. **Write Tests**: Maintain high test coverage for new code
4. **Follow Standards**: Adhere to established coding standards

### For Teams

1. **Regular Reviews**: Review quality metrics in team meetings
2. **Continuous Improvement**: Regularly update quality thresholds
3. **Training**: Ensure all team members understand quality standards
4. **Documentation**: Keep quality documentation up to date

### For Maintainers

1. **Monitor Trends**: Track quality metrics over time
2. **Update Tools**: Keep quality tools and configurations current
3. **Adjust Thresholds**: Modify quality gates based on project needs
4. **Performance**: Optimize quality checks for faster feedback

## Support

For questions or issues with quality gates:

1. **Documentation**: Check this document and related configuration files
2. **Local Testing**: Run `./scripts/quality-check.sh` for detailed analysis
3. **GitHub Issues**: Create an issue for bugs or feature requests
4. **Team Discussion**: Discuss quality standards in team meetings

---

*This quality gates system ensures high code quality and reliability for the AI Scholar RAG Chatbot project.*