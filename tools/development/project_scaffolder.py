"""
Project Scaffolder for AI Scholar
Intelligent project structure generation with best practices and templates
"""
import asyncio
import json
import logging
import os
import shutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import yaml
import subprocess

logger = logging.getLogger(__name__)

@dataclass
class ProjectTemplate:
    """Project template configuration"""
    name: str
    description: str
    language: str
    framework: Optional[str]
    structure: Dict[str, Any]
    dependencies: List[str]
    dev_dependencies: List[str]
    scripts: Dict[str, str]
    config_files: Dict[str, str]
    documentation: List[str]

@dataclass
class ScaffoldingOptions:
    """Project scaffolding options"""
    project_name: str
    template: str
    target_directory: str
    include_tests: bool = True
    include_docs: bool = True
    include_ci_cd: bool = True
    include_docker: bool = True
    git_init: bool = True
    install_dependencies: bool = True
    custom_options: Dict[str, Any] = None

class ProjectScaffolder:
    """Intelligent project scaffolding system"""
    
    def __init__(self):
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Load project templates"""
        self.templates = {
            "fastapi_backend": ProjectTemplate(
                name="FastAPI Backend",
                description="Modern Python backend with FastAPI, async support, and best practices",
                language="python",
                framework="fastapi",
                structure={
                    "app": {
                        "__init__.py": "",
                        "main.py": "fastapi_main_template",
                        "core": {
                            "__init__.py": "",
                            "config.py": "config_template",
                            "database.py": "database_template",
                            "security.py": "security_template"
                        },
                        "api": {
                            "__init__.py": "",
                            "v1": {
                                "__init__.py": "",
                                "endpoints": {
                                    "__init__.py": "",
                                    "auth.py": "auth_endpoints_template",
                                    "users.py": "users_endpoints_template"
                                }
                            }
                        },
                        "models": {
                            "__init__.py": "",
                            "user.py": "user_model_template"
                        },
                        "services": {
                            "__init__.py": "",
                            "auth_service.py": "auth_service_template"
                        },
                        "utils": {
                            "__init__.py": "",
                            "helpers.py": "helpers_template"
                        }
                    },
                    "tests": {
                        "__init__.py": "",
                        "conftest.py": "pytest_conftest_template",
                        "test_auth.py": "auth_test_template",
                        "test_users.py": "users_test_template"
                    },
                    "docs": {
                        "README.md": "readme_template",
                        "API.md": "api_docs_template"
                    },
                    "requirements.txt": "requirements_template",
                    "requirements-dev.txt": "dev_requirements_template",
                    "Dockerfile": "dockerfile_template",
                    "docker-compose.yml": "docker_compose_template",
                    ".env.example": "env_example_template",
                    ".gitignore": "python_gitignore_template",
                    "pyproject.toml": "pyproject_template"
                },
                dependencies=[
                    "fastapi>=0.104.0",
                    "uvicorn[standard]>=0.24.0",
                    "pydantic>=2.4.0",
                    "sqlalchemy>=2.0.0",
                    "alembic>=1.12.0",
                    "python-jose[cryptography]>=3.3.0",
                    "passlib[bcrypt]>=1.7.4",
                    "python-multipart>=0.0.6",
                    "aiofiles>=23.2.1"
                ],
                dev_dependencies=[
                    "pytest>=7.4.0",
                    "pytest-asyncio>=0.21.0",
                    "httpx>=0.25.0",
                    "black>=23.9.0",
                    "isort>=5.12.0",
                    "flake8>=6.1.0",
                    "mypy>=1.6.0"
                ],
                scripts={
                    "start": "uvicorn app.main:app --reload",
                    "test": "pytest",
                    "lint": "flake8 app tests",
                    "format": "black app tests && isort app tests",
                    "type-check": "mypy app"
                },
                config_files={
                    ".flake8": "flake8_config",
                    "mypy.ini": "mypy_config"
                },
                documentation=["README.md", "API.md", "CONTRIBUTING.md"]
            ),
            
            "react_frontend": ProjectTemplate(
                name="React Frontend",
                description="Modern React frontend with TypeScript, Vite, and best practices",
                language="typescript",
                framework="react",
                structure={
                    "src": {
                        "components": {
                            "common": {
                                "Button.tsx": "button_component_template",
                                "Input.tsx": "input_component_template",
                                "Modal.tsx": "modal_component_template"
                            },
                            "layout": {
                                "Header.tsx": "header_component_template",
                                "Sidebar.tsx": "sidebar_component_template",
                                "Layout.tsx": "layout_component_template"
                            }
                        },
                        "pages": {
                            "Home.tsx": "home_page_template",
                            "Login.tsx": "login_page_template",
                            "Dashboard.tsx": "dashboard_page_template"
                        },
                        "hooks": {
                            "useAuth.ts": "auth_hook_template",
                            "useApi.ts": "api_hook_template"
                        },
                        "services": {
                            "api.ts": "api_service_template",
                            "auth.ts": "auth_service_template"
                        },
                        "utils": {
                            "helpers.ts": "helpers_template",
                            "constants.ts": "constants_template"
                        },
                        "types": {
                            "index.ts": "types_template"
                        },
                        "styles": {
                            "globals.css": "global_styles_template",
                            "components.css": "component_styles_template"
                        },
                        "App.tsx": "app_component_template",
                        "main.tsx": "main_template",
                        "vite-env.d.ts": "vite_env_template"
                    },
                    "public": {
                        "index.html": "index_html_template",
                        "favicon.ico": "favicon_placeholder"
                    },
                    "tests": {
                        "setup.ts": "test_setup_template",
                        "components": {
                            "Button.test.tsx": "button_test_template"
                        }
                    },
                    "package.json": "package_json_template",
                    "tsconfig.json": "tsconfig_template",
                    "vite.config.ts": "vite_config_template",
                    ".eslintrc.json": "eslint_config_template",
                    ".prettierrc": "prettier_config_template",
                    "tailwind.config.js": "tailwind_config_template",
                    "postcss.config.js": "postcss_config_template"
                },
                dependencies=[
                    "react@^18.2.0",
                    "react-dom@^18.2.0",
                    "react-router-dom@^6.16.0",
                    "@tanstack/react-query@^4.35.0",
                    "axios@^1.5.0",
                    "tailwindcss@^3.3.0"
                ],
                dev_dependencies=[
                    "@types/react@^18.2.0",
                    "@types/react-dom@^18.2.0",
                    "@vitejs/plugin-react@^4.1.0",
                    "vite@^4.4.0",
                    "typescript@^5.2.0",
                    "@testing-library/react@^13.4.0",
                    "@testing-library/jest-dom@^6.1.0",
                    "vitest@^0.34.0",
                    "eslint@^8.50.0",
                    "prettier@^3.0.0"
                ],
                scripts={
                    "dev": "vite",
                    "build": "tsc && vite build",
                    "preview": "vite preview",
                    "test": "vitest",
                    "lint": "eslint src --ext ts,tsx",
                    "format": "prettier --write src"
                },
                config_files={},
                documentation=["README.md", "CONTRIBUTING.md"]
            ),
            
            "fullstack_ai": ProjectTemplate(
                name="Full-Stack AI Application",
                description="Complete AI application with FastAPI backend and React frontend",
                language="mixed",
                framework="fullstack",
                structure={
                    "backend": "fastapi_backend_structure",
                    "frontend": "react_frontend_structure",
                    "shared": {
                        "types": {
                            "api.ts": "shared_api_types_template"
                        },
                        "utils": {
                            "validation.py": "shared_validation_template"
                        }
                    },
                    "docker-compose.yml": "fullstack_docker_compose_template",
                    "README.md": "fullstack_readme_template",
                    "Makefile": "makefile_template"
                },
                dependencies=[],  # Inherited from sub-templates
                dev_dependencies=[],
                scripts={
                    "dev": "docker-compose up -d",
                    "build": "docker-compose build",
                    "test": "make test",
                    "deploy": "make deploy"
                },
                config_files={},
                documentation=["README.md", "DEPLOYMENT.md", "DEVELOPMENT.md"]
            )
        }
    
    async def scaffold_project(self, options: ScaffoldingOptions) -> Dict[str, Any]:
        """Scaffold a new project"""
        if options.template not in self.templates:
            raise ValueError(f"Template '{options.template}' not found")
        
        template = self.templates[options.template]
        project_path = Path(options.target_directory) / options.project_name
        
        # Create project directory
        project_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🏗️ Scaffolding {template.name} project: {options.project_name}")
        
        # Create directory structure and files
        await self._create_structure(project_path, template.structure, options)
        
        # Generate configuration files
        await self._generate_config_files(project_path, template, options)
        
        # Initialize git repository
        if options.git_init:
            await self._init_git_repo(project_path)
        
        # Install dependencies
        if options.install_dependencies:
            await self._install_dependencies(project_path, template)
        
        # Generate documentation
        if options.include_docs:
            await self._generate_documentation(project_path, template, options)
        
        # Setup CI/CD
        if options.include_ci_cd:
            await self._setup_ci_cd(project_path, template)
        
        # Generate project summary
        summary = await self._generate_project_summary(project_path, template, options)
        
        logger.info(f"✅ Project scaffolded successfully: {project_path}")
        
        return {
            "project_path": str(project_path),
            "template": template.name,
            "summary": summary,
            "next_steps": self._get_next_steps(template, options)
        }
    
    async def _create_structure(
        self, 
        base_path: Path, 
        structure: Dict[str, Any], 
        options: ScaffoldingOptions
    ):
        """Create directory structure and files"""
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # It's a directory
                path.mkdir(exist_ok=True)
                await self._create_structure(path, content, options)
            else:
                # It's a file
                file_content = await self._get_file_content(content, options)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
    
    async def _get_file_content(self, template_name: str, options: ScaffoldingOptions) -> str:
        """Get file content from template"""
        templates = {
            "fastapi_main_template": '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import auth, users

app = FastAPI(
    title="{project_name} API",
    description="API for {project_name}",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

@app.get("/")
async def root():
    return {{"message": "Welcome to {project_name} API"}}

@app.get("/health")
async def health_check():
    return {{"status": "healthy"}}
''',
            
            "config_template": '''from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "{project_name}"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
''',
            
            "package_json_template": '''{
  "name": "{project_name}",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write src"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.16.0",
    "@tanstack/react-query": "^4.35.0",
    "axios": "^1.5.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@vitejs/plugin-react": "^4.0.3",
    "vite": "^4.4.5",
    "typescript": "^5.0.2",
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^6.1.0",
    "vitest": "^0.34.0",
    "eslint": "^8.45.0",
    "prettier": "^3.0.0"
  }
}''',
            
            "app_component_template": '''import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import './styles/globals.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
''',
            
            "dockerfile_template": '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
            
            "readme_template": '''# {project_name}

{description}

## Features

- Modern architecture with best practices
- Comprehensive testing suite
- Docker support for easy deployment
- CI/CD pipeline ready
- Comprehensive documentation

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd {project_name}
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app tests
isort app tests
```

### Type Checking

```bash
mypy app
```

## Deployment

### Using Docker

```bash
docker build -t {project_name} .
docker run -p 8000:8000 {project_name}
```

### Using Docker Compose

```bash
docker-compose up -d
```

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.
'''
        }
        
        # Replace placeholders
        content = templates.get(template_name, f"# TODO: Implement {template_name}")
        content = content.format(
            project_name=options.project_name,
            description=f"Generated {options.template} project"
        )
        
        return content
    
    async def _generate_config_files(
        self, 
        project_path: Path, 
        template: ProjectTemplate, 
        options: ScaffoldingOptions
    ):
        """Generate configuration files"""
        config_templates = {
            "flake8_config": '''[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,docs/source/conf.py,old,build,dist
''',
            "mypy_config": '''[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
''',
            "pyproject_template": f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{options.project_name}"
version = "1.0.0"
description = "Generated {template.name} project"
authors = [{{name = "Developer", email = "dev@example.com"}}]
license = {{text = "MIT"}}
requires-python = ">=3.11"
dependencies = {template.dependencies}

[project.optional-dependencies]
dev = {template.dev_dependencies}

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88
'''
        }
        
        for config_file, template_name in template.config_files.items():
            config_path = project_path / config_file
            content = config_templates.get(template_name, f"# {config_file} configuration")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    async def _init_git_repo(self, project_path: Path):
        """Initialize git repository"""
        try:
            subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"], 
                cwd=project_path, 
                check=True, 
                capture_output=True
            )
            logger.info("✅ Git repository initialized")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to initialize git repository: {e}")
    
    async def _install_dependencies(self, project_path: Path, template: ProjectTemplate):
        """Install project dependencies"""
        try:
            if template.language == "python":
                # Create virtual environment
                subprocess.run(
                    ["python", "-m", "venv", "venv"], 
                    cwd=project_path, 
                    check=True, 
                    capture_output=True
                )
                
                # Install dependencies
                pip_path = project_path / "venv" / "bin" / "pip"
                if not pip_path.exists():
                    pip_path = project_path / "venv" / "Scripts" / "pip.exe"  # Windows
                
                subprocess.run(
                    [str(pip_path), "install", "-r", "requirements.txt"], 
                    cwd=project_path, 
                    check=True, 
                    capture_output=True
                )
                
            elif template.language == "typescript":
                subprocess.run(
                    ["npm", "install"], 
                    cwd=project_path, 
                    check=True, 
                    capture_output=True
                )
            
            logger.info("✅ Dependencies installed")
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to install dependencies: {e}")
    
    async def _generate_documentation(
        self, 
        project_path: Path, 
        template: ProjectTemplate, 
        options: ScaffoldingOptions
    ):
        """Generate project documentation"""
        docs_dir = project_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Generate CONTRIBUTING.md
        contributing_content = f'''# Contributing to {options.project_name}

Thank you for your interest in contributing! Here's how you can help:

## Development Setup

1. Fork and clone the repository
2. Install dependencies
3. Create a feature branch
4. Make your changes
5. Add tests
6. Submit a pull request

## Code Style

- Follow the existing code style
- Run linting and formatting tools
- Add type hints where appropriate
- Write comprehensive tests

## Testing

Run the test suite before submitting:

```bash
{template.scripts.get("test", "pytest")}
```

## Questions?

Feel free to open an issue for any questions or concerns.
'''
        
        with open(docs_dir / "CONTRIBUTING.md", 'w', encoding='utf-8') as f:
            f.write(contributing_content)
    
    async def _setup_ci_cd(self, project_path: Path, template: ProjectTemplate):
        """Setup CI/CD pipeline"""
        github_dir = project_path / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)
        
        ci_content = f'''name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 app tests
        black --check app tests
        isort --check-only app tests
    
    - name: Run type checking
      run: mypy app
    
    - name: Run tests
      run: pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
'''
        
        with open(github_dir / "ci.yml", 'w', encoding='utf-8') as f:
            f.write(ci_content)
    
    async def _generate_project_summary(
        self, 
        project_path: Path, 
        template: ProjectTemplate, 
        options: ScaffoldingOptions
    ) -> Dict[str, Any]:
        """Generate project summary"""
        file_count = sum(1 for _ in project_path.rglob("*") if _.is_file())
        
        return {
            "template_used": template.name,
            "language": template.language,
            "framework": template.framework,
            "files_created": file_count,
            "features_included": {
                "tests": options.include_tests,
                "documentation": options.include_docs,
                "ci_cd": options.include_ci_cd,
                "docker": options.include_docker,
                "git": options.git_init
            },
            "dependencies": len(template.dependencies),
            "dev_dependencies": len(template.dev_dependencies)
        }
    
    def _get_next_steps(self, template: ProjectTemplate, options: ScaffoldingOptions) -> List[str]:
        """Get next steps for the user"""
        steps = [
            f"Navigate to your project: cd {options.project_name}",
            "Review and update the .env file with your configuration"
        ]
        
        if template.language == "python":
            steps.extend([
                "Activate virtual environment: source venv/bin/activate (or venv\\Scripts\\activate on Windows)",
                f"Start development server: {template.scripts.get('start', 'uvicorn app.main:app --reload')}"
            ])
        elif template.language == "typescript":
            steps.extend([
                f"Start development server: {template.scripts.get('dev', 'npm run dev')}",
                "Open http://localhost:3000 in your browser"
            ])
        
        steps.extend([
            "Run tests to ensure everything works: " + template.scripts.get('test', 'pytest'),
            "Start building your application!",
            "Consider setting up your database and environment variables",
            "Review the generated documentation in the docs/ folder"
        ])
        
        return steps
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List available templates"""
        return [
            {
                "name": name,
                "description": template.description,
                "language": template.language,
                "framework": template.framework
            }
            for name, template in self.templates.items()
        ]
    
    async def create_custom_template(
        self, 
        name: str, 
        template_config: Dict[str, Any]
    ) -> bool:
        """Create a custom template"""
        try:
            template = ProjectTemplate(**template_config)
            self.templates[name] = template
            logger.info(f"✅ Custom template '{name}' created")
            return True
        except Exception as e:
            logger.error(f"Failed to create custom template: {e}")
            return False

# Global scaffolder instance
project_scaffolder = ProjectScaffolder()

# Convenience functions
async def scaffold_project(
    project_name: str,
    template: str,
    target_directory: str = ".",
    **kwargs
) -> Dict[str, Any]:
    """Scaffold a new project"""
    options = ScaffoldingOptions(
        project_name=project_name,
        template=template,
        target_directory=target_directory,
        **kwargs
    )
    return await project_scaffolder.scaffold_project(options)

def list_available_templates() -> List[Dict[str, Any]]:
    """List available project templates"""
    return project_scaffolder.list_templates()

if __name__ == "__main__":
    # Example usage
    async def test_scaffolder():
        print("🧪 Testing Project Scaffolder...")
        
        # List available templates
        templates = list_available_templates()
        print(f"Available templates: {[t['name'] for t in templates]}")
        
        # Scaffold a FastAPI project
        result = await scaffold_project(
            project_name="test_api",
            template="fastapi_backend",
            target_directory="/tmp",
            install_dependencies=False  # Skip for testing
        )
        
        print(f"Project scaffolded: {result['project_path']}")
        print(f"Files created: {result['summary']['files_created']}")
        print(f"Next steps: {len(result['next_steps'])} items")
    
    asyncio.run(test_scaffolder())