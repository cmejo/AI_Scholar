# Code Quality Setup Guide

This document describes the comprehensive code quality setup implemented for the AI Scholar RAG Chatbot project.

## Overview

The project now includes a robust code quality system with:
- **Enhanced ESLint** with strict TypeScript enforcement
- **Prettier** for consistent code formatting
- **Pre-commit hooks** using Husky and lint-staged
- **Python linting tools** (Black, Flake8, MyPy, Bandit)
- **Automated CI/CD quality checks**
- **VS Code integration** for seamless development

## Frontend Quality Tools

### ESLint Configuration
- **File**: `eslint.config.js`
- **Features**:
  - Strict TypeScript rules with no `any` types allowed
  - React hooks exhaustive dependencies checking
  - Import organization and sorting
  - Code complexity limits
  - Security-focused rules

### TypeScript Configuration
- **Files**: `tsconfig.app.json`, `tsconfig.node.json`
- **Features**:
  - Strict mode enabled
  - No unused locals/parameters
  - No unchecked indexed access
  - Exact optional property types

### Prettier Configuration
- **File**: `.prettierrc`
- **Features**:
  - Consistent formatting across all file types
  - 80-character line width
  - Single quotes, trailing commas
  - Automatic formatting on save

## Backend Quality Tools

### Python Code Formatting
- **Black**: Automatic code formatting with 88-character line length
- **isort**: Import sorting and organization

### Python Linting
- **Flake8**: Style guide enforcement and error detection
- **Configuration**: `backend/.flake8`
- **Features**:
  - PEP 8 compliance
  - Complexity limits (max 10)
  - Custom ignore patterns for Black compatibility

### Python Type Checking
- **MyPy**: Static type checking
- **Configuration**: `backend/pyproject.toml`
- **Features**:
  - Strict type checking
  - No untyped definitions allowed
  - Comprehensive error reporting

### Security Analysis
- **Bandit**: Security vulnerability detection
- **Features**:
  - Automatic security issue detection
  - JSON reporting for CI/CD integration

## Pre-commit Hooks

### Husky Setup
- **File**: `.husky/pre-commit`
- **Triggers**: Runs on every commit
- **Actions**: Executes lint-staged for affected files

### Lint-staged Configuration
- **File**: `package.json` (lint-staged section)
- **Actions**:
  - **TypeScript/JavaScript**: Prettier formatting + ESLint fixing + Type checking
  - **Python**: Black formatting + isort + Flake8 + MyPy
  - **JSON/Markdown**: Prettier formatting

## Development Scripts

### Frontend Scripts
```bash
npm run lint              # Run ESLint
npm run lint:fix          # Fix ESLint issues
npm run format            # Format with Prettier
npm run format:check      # Check formatting
npm run type-check        # TypeScript type checking
npm run quality:check     # Run all quality checks
npm run quality:fix       # Fix all quality issues
```

### Backend Scripts
```bash
npm run backend:lint           # Python linting
npm run backend:format         # Python formatting
npm run backend:format:check   # Check Python formatting
npm run backend:type-check     # Python type checking
npm run backend:quality:check  # All Python quality checks
npm run backend:quality:fix    # Fix Python quality issues
```

### Makefile Commands
```bash
make install-dev          # Install all development dependencies
make quality-check        # Run comprehensive quality checks
make quality-fix          # Fix all quality issues
make security-check       # Run security analysis
make clean               # Clean build artifacts
```

## CI/CD Integration

### GitHub Actions
- **File**: `.github/workflows/quality-check.yml`
- **Triggers**: Push to main/develop, Pull requests
- **Checks**:
  - Frontend: TypeScript compilation, ESLint, Prettier, Tests
  - Backend: Python formatting, linting, type checking, security, tests
  - Quality gates prevent merging failing code

### Quality Gates
1. **Pre-commit**: Basic formatting and linting
2. **CI/CD**: Comprehensive quality checks
3. **Deployment**: Final quality validation

## VS Code Integration

### Settings
- **File**: `.vscode/settings.json`
- **Features**:
  - Format on save
  - Auto-fix ESLint issues
  - Python environment configuration
  - File exclusions for better performance

### Recommended Extensions
- ESLint
- Prettier
- Python
- Black Formatter
- MyPy Type Checker
- Flake8

## Quality Metrics

### Key Performance Indicators
- **ESLint Errors**: Target 0
- **TypeScript Errors**: Target 0
- **Code Coverage**: Target >80%
- **Security Issues**: Target 0
- **Code Complexity**: Target <10

### Monitoring
- Quality metrics tracked in CI/CD
- Automated reports generated
- Trend analysis available

## Getting Started

### Initial Setup
1. **Install dependencies**:
   ```bash
   npm install
   make backend-setup
   ```

2. **Run quality checks**:
   ```bash
   make quality-check
   ```

3. **Fix quality issues**:
   ```bash
   make quality-fix
   ```

### Development Workflow
1. Write code with VS Code auto-formatting
2. Pre-commit hooks run automatically
3. CI/CD validates on push/PR
4. Quality gates prevent bad code from merging

### Troubleshooting

#### Common Issues
1. **ESLint errors**: Run `npm run lint:fix`
2. **Formatting issues**: Run `npm run format`
3. **Python issues**: Run `make backend:quality:fix`
4. **Type errors**: Check TypeScript configuration

#### Performance Tips
- Use VS Code settings for real-time feedback
- Run quality checks locally before pushing
- Use `make quality-fix` for bulk fixes

## Configuration Files

### Frontend
- `eslint.config.js` - ESLint configuration
- `.prettierrc` - Prettier configuration
- `tsconfig.*.json` - TypeScript configuration

### Backend
- `backend/.flake8` - Flake8 configuration
- `backend/pyproject.toml` - Python project configuration
- `backend/requirements-dev.txt` - Development dependencies

### Development
- `.husky/pre-commit` - Pre-commit hook
- `.vscode/settings.json` - VS Code settings
- `Makefile` - Development commands
- `scripts/quality-check.sh` - Quality check script

## Best Practices

### Code Quality
1. **No `any` types** - Use proper TypeScript interfaces
2. **Consistent formatting** - Let tools handle formatting
3. **Type safety** - Enable strict TypeScript mode
4. **Security first** - Regular security scans
5. **Test coverage** - Maintain high test coverage

### Development
1. **Commit often** - Small, focused commits
2. **Fix issues early** - Don't ignore quality warnings
3. **Use tools** - Leverage IDE integration
4. **Review code** - Quality checks in PR reviews
5. **Monitor trends** - Track quality metrics over time

## Support

For questions or issues with the quality setup:
1. Check this documentation
2. Review configuration files
3. Run diagnostic scripts
4. Check CI/CD logs
5. Contact the development team

---

This quality setup ensures consistent, maintainable, and secure code across the entire AI Scholar RAG Chatbot project.