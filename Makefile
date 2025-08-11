# AI Scholar RAG Chatbot - Development Makefile

.PHONY: help install install-dev clean lint format type-check test quality-check quality-fix

# Default target
help:
	@echo "AI Scholar RAG Chatbot - Development Commands"
	@echo "============================================="
	@echo ""
	@echo "📦 Installation:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo "  backend-setup    Set up backend Python environment"
	@echo ""
	@echo "🧹 Cleaning:"
	@echo "  clean            Clean build artifacts and caches"
	@echo "  clean-reports    Clean quality reports"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  lint             Run linting for frontend and backend"
	@echo "  format           Format code for frontend and backend"
	@echo "  format-check     Check code formatting"
	@echo "  type-check       Run type checking"
	@echo "  quality-check    Run comprehensive quality checks with metrics"
	@echo "  quality-check-fast  Run basic quality checks (faster)"
	@echo "  quality-fix      Fix all quality issues"
	@echo "  quality-report   Generate quality metrics report"
	@echo ""
	@echo "🔒 Security:"
	@echo "  security-check   Run security analysis"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test             Run tests"
	@echo "  test-coverage    Run tests with coverage reports"
	@echo ""
	@echo "🚪 Quality Gates (CI/CD):"
	@echo "  quality-gates    Run all quality gates"
	@echo "  quality-gate-frontend  Run frontend quality gates"
	@echo "  quality-gate-backend   Run backend quality gates"
	@echo "  ci-quality       Full CI/CD quality pipeline"
	@echo ""
	@echo "📊 Metrics & Reporting:"
	@echo "  quality-metrics       Collect comprehensive quality metrics"
	@echo "  quality-metrics-backend  Collect backend-specific metrics"
	@echo "  quality-dashboard     Generate interactive quality dashboard"
	@echo "  quality-full-report   Generate complete quality report with dashboard"
	@echo "  quality-alerts        Run quality alerts monitoring"
	@echo "  quality-monitor       Complete quality monitoring with alerts"
	@echo ""
	@echo "🚀 Development:"
	@echo "  dev              Start development server"
	@echo "  build            Build for production"

# Installation
install:
	npm install
	cd backend && pip install -r requirements.txt

install-dev: install
	cd backend && pip install -r requirements-dev.txt

# Backend Python environment setup
backend-setup:
	cd backend && python -m venv venv
	cd backend && source venv/bin/activate && pip install --upgrade pip
	cd backend && source venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

# Cleaning
clean:
	rm -rf node_modules/.cache
	rm -rf dist/
	rm -rf coverage/
	rm -rf .nyc_output/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

# Frontend quality
lint-frontend:
	npm run lint

format-frontend:
	npm run format

format-check-frontend:
	npm run format:check

type-check-frontend:
	npm run type-check

# Backend quality
lint-backend:
	cd backend && python -m flake8 .

format-backend:
	cd backend && python -m black . && python -m isort .

format-check-backend:
	cd backend && python -m black --check . && python -m isort --check-only .

type-check-backend:
	cd backend && python -m mypy .

# Combined commands
lint: lint-frontend lint-backend

format: format-frontend format-backend

format-check: format-check-frontend format-check-backend

type-check: type-check-frontend type-check-backend

# Testing
test:
	npm run test:run
	cd backend && python -m pytest

test-coverage:
	npm run test:coverage
	cd backend && python -m pytest --cov=. --cov-report=html

# Quality checks
quality-check:
	@echo "Running comprehensive quality checks..."
	./scripts/quality-check.sh

quality-check-fast: format-check lint type-check test

quality-fix: format lint

quality-report:
	@echo "Generating quality metrics report..."
	./scripts/quality-check.sh || true
	@echo "Quality reports available in quality-reports/ directory"

# Security checks
security-check:
	@echo "Running security analysis..."
	cd backend && python -m bandit -r . -f json -o bandit-report.json || true
	cd backend && python -m safety check --json --output safety-report.json || true
	@echo "Security reports generated: backend/bandit-report.json, backend/safety-report.json"

# Quality gates (for CI/CD)
quality-gate-frontend:
	@echo "Running frontend quality gates..."
	npm run type-check
	npm run format:check
	npm run lint
	npm run test:coverage

quality-gate-backend:
	@echo "Running backend quality gates..."
	cd backend && python -m black --check .
	cd backend && python -m isort --check-only .
	cd backend && python -m flake8 .
	cd backend && python -m mypy .
	cd backend && python -m bandit -r . -q
	cd backend && python -m pytest --cov=. --cov-fail-under=80

quality-gates: quality-gate-frontend quality-gate-backend

# Development server
dev:
	npm run dev

# Build
build:
	npm run build

# Full quality pipeline (CI/CD)
ci-quality: install-dev quality-gates security-check

# Quality monitoring and metrics
quality-metrics:
	@echo "🔍 Collecting comprehensive quality metrics..."
	npm run quality:metrics

quality-metrics-backend:
	@echo "🐍 Collecting backend-specific quality metrics..."
	npm run quality:metrics:backend

quality-dashboard:
	@echo "📊 Generating interactive quality dashboard..."
	npm run quality:dashboard

quality-full-report:
	@echo "📈 Generating comprehensive quality report with dashboard..."
	npm run quality:full-report

quality-alerts:
	@echo "🚨 Running quality alerts monitoring..."
	npm run quality:alerts

quality-monitor:
	@echo "👁️ Running complete quality monitoring with alerts..."
	npm run quality:monitor

# Clean quality reports
clean-reports:
	rm -rf quality-reports/
	@echo "Quality reports cleaned"