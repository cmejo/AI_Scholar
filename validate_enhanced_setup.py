#!/usr/bin/env python3
"""
Quick validation script for Enhanced LLM Backend setup
Checks if all components are properly configured
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (missing)")
        return False

def check_command_available(command, description):
    """Check if a command is available"""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        print(f"✅ {description}: Available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ {description}: Not available")
        return False

def check_service_running(url, description):
    """Check if a service is running"""
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            print(f"✅ {description}: Running")
            return True
        else:
            print(f"❌ {description}: Not responding (HTTP {response.status_code})")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ {description}: Not running")
        return False

def main():
    """Run validation checks"""
    print("🔍 Validating Enhanced LLM Backend Setup")
    print("=" * 50)
    
    all_good = True
    
    # Check required files
    print("\n📁 Required Files:")
    files_to_check = [
        ("app.py", "Main application"),
        ("requirements.txt", "Python dependencies"),
        (".env", "Environment configuration"),
        ("services/ollama_service.py", "Ollama service"),
        ("services/chat_service.py", "Chat service"),
        ("services/model_manager.py", "Model manager"),
    ]
    
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_good = False
    
    # Check required commands
    print("\n🛠️  Required Commands:")
    commands_to_check = [
        ("python", "Python interpreter"),
        ("pip", "Python package manager"),
        ("ollama", "Ollama CLI"),
    ]
    
    for command, description in commands_to_check:
        if not check_command_available(command, description):
            all_good = False
    
    # Check services
    print("\n🌐 Services:")
    services_to_check = [
        ("http://localhost:11434/api/tags", "Ollama service"),
    ]
    
    for url, description in services_to_check:
        if not check_service_running(url, description):
            print(f"    💡 Start with: ollama serve")
            all_good = False
    
    # Check Python dependencies
    print("\n🐍 Python Dependencies:")
    try:
        import flask
        import ollama
        import transformers
        import requests
        print("✅ Core dependencies: Available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("    💡 Install with: pip install -r requirements.txt")
        all_good = False
    
    # Check environment configuration
    print("\n⚙️  Environment Configuration:")
    env_vars = [
        "OLLAMA_BASE_URL",
        "DEFAULT_MODEL",
        "SECRET_KEY",
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")
            print(f"    💡 Add to .env file")
            all_good = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All checks passed! Your setup looks good.")
        print("\n🚀 Next steps:")
        print("1. Start the backend: python app.py")
        print("2. Test the setup: python test_enhanced_backend.py")
        print("3. Start the React frontend")
    else:
        print("⚠️  Some issues found. Please fix them before proceeding.")
        print("\n🔧 Common fixes:")
        print("1. Run setup script: python setup_enhanced_llm_backend.py")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Start Ollama: ollama serve")
        print("4. Configure .env file")
    
    return all_good

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)