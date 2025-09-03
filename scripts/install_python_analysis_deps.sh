#!/bin/bash
"""
Install Python Backend Analysis Dependencies
Installs additional tools needed for comprehensive Python backend analysis.
"""

set -e

echo "Installing Python backend analysis dependencies..."

# Navigate to backend directory
cd backend

# Install analysis tools
echo "Installing static analysis tools..."
pip install safety pip-audit sqlparse

# Install additional development tools if not present
echo "Installing development tools..."
pip install flake8 black mypy bandit pylint

# Install AST analysis tools
echo "Installing AST analysis tools..."
pip install ast-grep astpretty

echo "Python backend analysis dependencies installed successfully!"

# Verify installations
echo "Verifying installations..."
python -c "import safety; print('✓ safety installed')"
python -c "import pip_audit; print('✓ pip-audit installed')" 2>/dev/null || echo "⚠ pip-audit may need separate installation"
python -c "import sqlparse; print('✓ sqlparse installed')"
python -c "import flake8; print('✓ flake8 installed')" 2>/dev/null || echo "⚠ flake8 may need separate installation"
python -c "import black; print('✓ black installed')" 2>/dev/null || echo "⚠ black may need separate installation"

echo "Installation verification complete!"