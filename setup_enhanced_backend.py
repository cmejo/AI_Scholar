#!/usr/bin/env python3
"""
Enhanced LLM Backend Setup Script
Sets up the AI Scholar chatbot with open source LLM integration
"""

import os
import sys
import subprocess
import json
import requests
import time
from pathlib import Path

def print_status(message, status="INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m", 
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, '')}{status}: {message}{colors['RESET']}")

def check_system_requirements():
    """Check if system requirements are met"""
    print_status("Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_status("Python 3.8+ is required", "ERROR")
        return False
    
    # Check if Docker is available (for optional containerized deployment)
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        print_status("Docker is available", "SUCCESS")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_status("Docker not found (optional for development)", "WARNING")
    
    # Check available disk space (need at least 10GB for models)
    import shutil
    free_space = shutil.disk_usage('.').free / (1024**3)  # GB
    if free_space < 10:
        print_status(f"Low disk space: {free_space:.1f}GB available. Recommend 10GB+ for models", "WARNING")
    else:
        print_status(f"Disk space OK: {free_space:.1f}GB available", "SUCCESS")
    
    return True

def install_ollama():
    """Install Ollama if not already installed"""
    print_status("Checking Ollama installation...")
    
    try:
        # Check if Ollama is already installed
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"Ollama already installed: {result.stdout.strip()}", "SUCCESS")
            return True
    except FileNotFoundError:
        pass
    
    print_status("Installing Ollama...")
    
    # Install Ollama based on OS
    import platform
    system = platform.system().lower()
    
    if system == "linux" or system == "darwin":  # Linux or macOS
        try:
            # Download and run Ollama install script
            install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
            subprocess.run(install_cmd, shell=True, check=True)
            print_status("Ollama installed successfully", "SUCCESS")
            return True
        except subprocess.CalledProcessError:
            print_status("Failed to install Ollama automatically", "ERROR")
            print_status("Please install Ollama manually from https://ollama.ai", "INFO")
            return False
    
    elif system == "windows":
        print_status("Please download and install Ollama from https://ollama.ai/download/windows", "INFO")
        return False
    
    else:
        print_status(f"Unsupported OS: {system}", "ERROR")
        return False

def start_ollama_service():
    """Start Ollama service"""
    print_status("Starting Ollama service...")
    
    try:
        # Try to start Ollama service
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for service to start
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    print_status("Ollama service started successfully", "SUCCESS")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print_status("Ollama service failed to start", "ERROR")
        return False
        
    except Exception as e:
        print_status(f"Error starting Ollama: {e}", "ERROR")
        return False

def pull_recommended_models():
    """Pull recommended models for different use cases"""
    print_status("Pulling recommended models...")
    
    # Recommended models by size and use case
    models = {
        "lightweight": ["tinyllama:1.1b"],
        "general": ["llama2:7b-chat", "mistral:7b-instruct"],
        "code": ["codellama:7b-instruct"],
        "advanced": ["llama2:13b-chat"]
    }
    
    # Ask user which models to install
    print("\nAvailable model categories:")
    for category, model_list in models.items():
        print(f"  {category}: {', '.join(model_list)}")
    
    print("\nChoose models to install:")
    print("1. Lightweight only (tinyllama - ~1GB)")
    print("2. General purpose (llama2:7b, mistral:7b - ~8GB)")
    print("3. Code assistance (codellama:7b - ~4GB)")
    print("4. All recommended models (~15GB)")
    print("5. Skip model installation")
    
    choice = input("Enter choice (1-5): ").strip()
    
    models_to_pull = []
    if choice == "1":
        models_to_pull = models["lightweight"]
    elif choice == "2":
        models_to_pull = models["general"]
    elif choice == "3":
        models_to_pull = models["code"]
    elif choice == "4":
        models_to_pull = sum(models.values(), [])
    elif choice == "5":
        print_status("Skipping model installation", "INFO")
        return True
    else:
        print_status("Invalid choice, skipping model installation", "WARNING")
        return True
    
    # Pull selected models
    for model in models_to_pull:
        print_status(f"Pulling model: {model}", "INFO")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            print_status(f"Successfully pulled {model}", "SUCCESS")
        except subprocess.CalledProcessError:
            print_status(f"Failed to pull {model}", "ERROR")
    
    return True

def setup_python_environment():
    """Set up Python virtual environment and install dependencies"""
    print_status("Setting up Python environment...")
    
    # Create virtual environment if it doesn't exist
    venv_path = Path("venv")
    if not venv_path.exists():
        print_status("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_status("Virtual environment created", "SUCCESS")
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        pip_path = venv_path / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
    
    # Install requirements
    print_status("Installing Python dependencies...")
    try:
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        print_status("Dependencies installed successfully", "SUCCESS")
    except subprocess.CalledProcessError:
        print_status("Failed to install dependencies", "ERROR")
        return False
    
    return True

def setup_database():
    """Set up database"""
    print_status("Setting up database...")
    
    # Check if PostgreSQL is available
    try:
        subprocess.run(["psql", "--version"], capture_output=True, check=True)
        postgres_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        postgres_available = False
    
    if postgres_available:
        print_status("PostgreSQL detected", "SUCCESS")
        # You could add automatic database setup here
        print_status("Please ensure your database is configured in .env file", "INFO")
    else:
        print_status("PostgreSQL not found, will use SQLite for development", "WARNING")
    
    return True

def create_env_file():
    """Create .env file with default configuration"""
    print_status("Creating environment configuration...")
    
    env_file = Path(".env")
    if env_file.exists():
        print_status(".env file already exists", "INFO")
        return True
    
    env_content = """# AI Scholar Chatbot Configuration

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama2:7b-chat

# Database Configuration (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chatbot_db
DB_USER=chatbot_user
DB_PASSWORD=chatbot_password

# For SQLite (development only)
# DATABASE_URL=sqlite:///chatbot.db

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production
JWT_EXPIRES_HOURS=24
JWT_REFRESH_EXPIRES_DAYS=30

# Frontend Configuration
REACT_APP_API_URL=http://localhost:5000

# Optional: HuggingFace Hub Token for model downloads
# HUGGINGFACE_HUB_TOKEN=your_token_here

# Optional: OpenAI API Key for comparison/fallback
# OPENAI_API_KEY=your_openai_key_here

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=True
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print_status(".env file created", "SUCCESS")
    print_status("Please review and update the .env file with your settings", "INFO")
    return True

def run_tests():
    """Run basic tests to verify setup"""
    print_status("Running setup verification tests...")
    
    try:
        # Test Ollama connection
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print_status(f"Ollama connection OK - {len(models)} models available", "SUCCESS")
        else:
            print_status("Ollama connection failed", "ERROR")
            return False
    except requests.exceptions.RequestException:
        print_status("Ollama service not responding", "ERROR")
        return False
    
    # Test Python imports
    try:
        import flask
        import ollama
        import transformers
        print_status("Python dependencies OK", "SUCCESS")
    except ImportError as e:
        print_status(f"Missing Python dependency: {e}", "ERROR")
        return False
    
    return True

def create_startup_scripts():
    """Create convenient startup scripts"""
    print_status("Creating startup scripts...")
    
    # Create start script for Unix/Linux/macOS
    start_script = """#!/bin/bash
# AI Scholar Chatbot Startup Script

echo "🚀 Starting AI Scholar Chatbot..."

# Start Ollama service if not running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "📡 Starting Ollama service..."
    ollama serve &
    sleep 3
fi

# Activate virtual environment
source venv/bin/activate

# Start the Flask application
echo "🌐 Starting Flask backend..."
python app.py
"""
    
    with open("start.sh", 'w') as f:
        f.write(start_script)
    os.chmod("start.sh", 0o755)
    
    # Create start script for Windows
    start_script_win = """@echo off
REM AI Scholar Chatbot Startup Script for Windows

echo 🚀 Starting AI Scholar Chatbot...

REM Start Ollama service if not running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo 📡 Starting Ollama service...
    start /B ollama serve
    timeout /t 3 /nobreak >nul
)

REM Activate virtual environment
call venv\\Scripts\\activate.bat

REM Start the Flask application
echo 🌐 Starting Flask backend...
python app.py
"""
    
    with open("start.bat", 'w') as f:
        f.write(start_script_win)
    
    print_status("Startup scripts created", "SUCCESS")

def main():
    """Main setup function"""
    print_status("🤖 AI Scholar Chatbot Enhanced LLM Backend Setup", "INFO")
    print_status("=" * 60, "INFO")
    
    # Check system requirements
    if not check_system_requirements():
        print_status("System requirements not met", "ERROR")
        return False
    
    # Install and setup Ollama
    if not install_ollama():
        print_status("Ollama installation failed", "ERROR")
        return False
    
    if not start_ollama_service():
        print_status("Failed to start Ollama service", "ERROR")
        return False
    
    # Setup Python environment
    if not setup_python_environment():
        print_status("Python environment setup failed", "ERROR")
        return False
    
    # Setup database
    if not setup_database():
        print_status("Database setup failed", "ERROR")
        return False
    
    # Create configuration
    if not create_env_file():
        print_status("Configuration setup failed", "ERROR")
        return False
    
    # Pull recommended models
    if not pull_recommended_models():
        print_status("Model installation had issues", "WARNING")
    
    # Create startup scripts
    create_startup_scripts()
    
    # Run verification tests
    if not run_tests():
        print_status("Setup verification failed", "ERROR")
        return False
    
    print_status("=" * 60, "SUCCESS")
    print_status("🎉 Setup completed successfully!", "SUCCESS")
    print_status("=" * 60, "SUCCESS")
    
    print("\n📋 Next steps:")
    print("1. Review and update the .env file with your settings")
    print("2. Start the application:")
    print("   - Unix/Linux/macOS: ./start.sh")
    print("   - Windows: start.bat")
    print("   - Manual: python app.py")
    print("3. Access the application at http://localhost:5000")
    print("4. The React frontend should be at http://localhost:3000")
    
    print("\n🔧 Available API endpoints:")
    print("- Health check: GET /api/health")
    print("- Models: GET /api/models")
    print("- Chat: POST /api/chat")
    print("- Streaming chat: POST /api/chat/stream")
    print("- RAG: POST /api/rag/chat")
    print("- HuggingFace search: GET /api/huggingface/search")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("\nSetup interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Setup failed with error: {e}", "ERROR")
        sys.exit(1)
