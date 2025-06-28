#!/usr/bin/env python3
"""
Setup script for Trust, Safety & Compliance features
Helps configure safety services and compliance settings
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def print_step(step_num, title):
    """Print step header"""
    print(f"\n🔧 Step {step_num}: {title}")
    print("-" * 40)

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def install_dependencies():
    """Install required dependencies for safety features"""
    print_step(1, "Installing Dependencies")
    
    # Required packages for PII detection and content moderation
    packages = [
        "spacy>=3.4.0",
        "transformers>=4.20.0",
        "torch>=1.12.0",
        "requests>=2.28.0",
        "celery>=5.2.0",
        "redis>=4.3.0"
    ]
    
    print("Installing Python packages...")
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            print(f"⚠️ Failed to install {package}, continuing...")
    
    # Download spaCy model
    print("\nDownloading spaCy English model...")
    run_command("python -m spacy download en_core_web_sm", "Downloading spaCy model")

def setup_environment():
    """Setup environment variables for safety features"""
    print_step(2, "Environment Configuration")
    
    env_file = Path('.env')
    
    # Read existing .env file if it exists
    existing_vars = {}
    if env_file.exists():
        print("📁 Found existing .env file")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_vars[key] = value
    
    # Safety and compliance environment variables
    safety_vars = {
        'OPENAI_API_KEY': {
            'description': 'OpenAI API key for content moderation',
            'required': False,
            'default': ''
        },
        'PERSPECTIVE_API_KEY': {
            'description': 'Google Perspective API key for toxicity detection',
            'required': False,
            'default': ''
        },
        'SAFETY_HATE_THRESHOLD': {
            'description': 'Threshold for hate speech detection (0.0-1.0)',
            'required': False,
            'default': '0.7'
        },
        'SAFETY_VIOLENCE_THRESHOLD': {
            'description': 'Threshold for violence detection (0.0-1.0)',
            'required': False,
            'default': '0.7'
        },
        'SAFETY_TOXICITY_THRESHOLD': {
            'description': 'Threshold for toxicity detection (0.0-1.0)',
            'required': False,
            'default': '0.6'
        },
        'DATA_RETENTION_DAYS': {
            'description': 'Data retention period in days',
            'required': False,
            'default': '730'
        },
        'CONSENT_VERSION': {
            'description': 'Current consent version',
            'required': False,
            'default': '1.0'
        },
        'CELERY_BROKER_URL': {
            'description': 'Celery broker URL (Redis)',
            'required': True,
            'default': 'redis://localhost:6379/0'
        },
        'CELERY_RESULT_BACKEND': {
            'description': 'Celery result backend URL (Redis)',
            'required': True,
            'default': 'redis://localhost:6379/0'
        }
    }
    
    new_vars = existing_vars.copy()
    
    print("Configuring safety and compliance settings...")
    print("(Press Enter to use default values)")
    
    for var_name, config in safety_vars.items():
        current_value = existing_vars.get(var_name, config['default'])
        
        if current_value:
            print(f"\nCurrent {var_name}: {current_value}")
        
        prompt = f"{config['description']}"
        if config['default']:
            prompt += f" [{config['default']}]"
        prompt += ": "
        
        new_value = input(prompt).strip()
        if not new_value:
            new_value = config['default']
        
        if new_value:
            new_vars[var_name] = new_value
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.write("# AI Scholar Environment Configuration\n")
        f.write("# Trust, Safety & Compliance Settings\n\n")
        
        # Group variables by category
        categories = {
            'Database': ['DATABASE_URL'],
            'Safety APIs': ['OPENAI_API_KEY', 'PERSPECTIVE_API_KEY'],
            'Safety Thresholds': ['SAFETY_HATE_THRESHOLD', 'SAFETY_VIOLENCE_THRESHOLD', 'SAFETY_TOXICITY_THRESHOLD'],
            'Compliance': ['DATA_RETENTION_DAYS', 'CONSENT_VERSION'],
            'Celery': ['CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND'],
            'Other': []
        }
        
        # Categorize existing variables
        categorized_vars = {cat: [] for cat in categories}
        for var_name, value in new_vars.items():
            categorized = False
            for category, var_list in categories.items():
                if var_name in var_list:
                    categorized_vars[category].append((var_name, value))
                    categorized = True
                    break
            if not categorized:
                categorized_vars['Other'].append((var_name, value))
        
        # Write variables by category
        for category, var_list in categorized_vars.items():
            if var_list:
                f.write(f"# {category}\n")
                for var_name, value in var_list:
                    f.write(f"{var_name}={value}\n")
                f.write("\n")
    
    print(f"\n✅ Environment configuration saved to {env_file}")

def setup_database():
    """Setup database tables for safety features"""
    print_step(3, "Database Setup")
    
    print("Creating safety and compliance database tables...")
    
    # Create the database tables
    setup_script = """
from app_enterprise import app
from models import db

with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
"""
    
    try:
        with open('temp_db_setup.py', 'w') as f:
            f.write(setup_script)
        
        result = subprocess.run([sys.executable, 'temp_db_setup.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database tables created successfully")
        else:
            print(f"❌ Database setup failed: {result.stderr}")
        
        # Clean up temporary file
        os.remove('temp_db_setup.py')
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")

def setup_redis():
    """Setup Redis for Celery"""
    print_step(4, "Redis Setup")
    
    print("Checking Redis installation and configuration...")
    
    # Check if Redis is installed
    if run_command("redis-cli --version", "Checking Redis installation"):
        print("✅ Redis is installed")
        
        # Check if Redis is running
        if run_command("redis-cli ping", "Testing Redis connection"):
            print("✅ Redis is running and accessible")
        else:
            print("⚠️ Redis is not running. Please start Redis server:")
            print("   • Ubuntu/Debian: sudo systemctl start redis-server")
            print("   • macOS: brew services start redis")
            print("   • Manual: redis-server")
    else:
        print("❌ Redis is not installed. Please install Redis:")
        print("   • Ubuntu/Debian: sudo apt-get install redis-server")
        print("   • macOS: brew install redis")
        print("   • Windows: Download from https://redis.io/download")

def create_startup_scripts():
    """Create startup scripts for safety services"""
    print_step(5, "Startup Scripts")
    
    # Create Celery startup script
    celery_script = """#!/bin/bash
# Start Celery workers for AI Scholar safety processing

echo "Starting AI Scholar Safety Services..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first."
    echo "   redis-server"
    exit 1
fi

# Start Celery worker for safety tasks
echo "Starting Celery worker for safety tasks..."
celery -A tasks.safety_tasks worker --loglevel=info --detach --pidfile=celery_safety_worker.pid

# Start Celery beat scheduler for periodic tasks
echo "Starting Celery beat scheduler..."
celery -A tasks.safety_tasks beat --loglevel=info --detach --pidfile=celery_safety_beat.pid

# Optional: Start Celery Flower for monitoring
if command -v flower &> /dev/null; then
    echo "Starting Celery Flower monitoring..."
    celery -A tasks.safety_tasks flower --detach --pidfile=celery_flower.pid
    echo "Flower monitoring available at: http://localhost:5555"
fi

echo "✅ Safety services started successfully!"
echo "To stop services, run: ./stop_safety_services.sh"
"""
    
    with open('start_safety_services.sh', 'w') as f:
        f.write(celery_script)
    
    os.chmod('start_safety_services.sh', 0o755)
    
    # Create stop script
    stop_script = """#!/bin/bash
# Stop Celery workers and safety services

echo "Stopping AI Scholar Safety Services..."

# Stop Celery processes using PID files
if [ -f celery_safety_worker.pid ]; then
    kill $(cat celery_safety_worker.pid) 2>/dev/null
    rm -f celery_safety_worker.pid
    echo "✅ Celery worker stopped"
fi

if [ -f celery_safety_beat.pid ]; then
    kill $(cat celery_safety_beat.pid) 2>/dev/null
    rm -f celery_safety_beat.pid
    echo "✅ Celery beat stopped"
fi

if [ -f celery_flower.pid ]; then
    kill $(cat celery_flower.pid) 2>/dev/null
    rm -f celery_flower.pid
    echo "✅ Celery flower stopped"
fi

# Fallback: kill any remaining celery processes
pkill -f "celery.*safety_tasks" 2>/dev/null

echo "✅ Safety services stopped!"
"""
    
    with open('stop_safety_services.sh', 'w') as f:
        f.write(stop_script)
    
    os.chmod('stop_safety_services.sh', 0o755)
    
    print("✅ Created startup scripts:")
    print("   • start_safety_services.sh - Start all safety services")
    print("   • stop_safety_services.sh - Stop all safety services")

def verify_installation():
    """Verify the safety installation"""
    print_step(6, "Installation Verification")
    
    print("Verifying safety and compliance installation...")
    
    # Check if required files exist
    required_files = [
        'services/pii_redaction_service.py',
        'services/content_moderation_service.py',
        'services/safety_compliance_service.py',
        'tasks/safety_tasks.py',
        'migrations/versions/014_trust_safety_compliance.py',
        '.env'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   • {file_path}")
    else:
        print("✅ All required files are present")
    
    # Test imports
    try:
        print("Testing service imports...")
        import services.pii_redaction_service
        import services.content_moderation_service
        import services.safety_compliance_service
        import tasks.safety_tasks
        print("✅ All services can be imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
    
    # Check environment variables
    env_file = Path('.env')
    if env_file.exists():
        print("✅ Environment configuration file exists")
    else:
        print("❌ Environment configuration file missing")
    
    print("\n🚀 Next Steps:")
    print("1. Start Redis server (if not already running):")
    print("   redis-server")
    
    print("\n2. Start the AI Scholar backend:")
    print("   python app_enterprise.py")
    
    print("\n3. Start safety services:")
    print("   ./start_safety_services.sh")
    
    print("\n4. Test the safety features:")
    print("   python test_trust_safety_compliance.py")
    
    print("\n5. Configure API keys (optional but recommended):")
    print("   • OpenAI API key for advanced content moderation")
    print("   • Google Perspective API key for toxicity detection")

def main():
    """Main setup function"""
    print_header("AI Scholar - Trust, Safety & Compliance Setup")
    print("This script will configure the safety and compliance features:")
    print("• PII (Personally Identifiable Information) Redaction")
    print("• Content Moderation & Safety Guardrails")
    print("• Compliance Framework (GDPR, audit trails)")
    print("• Safety Monitoring & Incident Management")
    
    try:
        install_dependencies()
        setup_environment()
        setup_database()
        setup_redis()
        create_startup_scripts()
        verify_installation()
        
        print_header("Setup Complete! 🛡️")
        print("Your AI Scholar installation now includes:")
        print("✅ PII redaction for privacy protection")
        print("✅ Content moderation for safety")
        print("✅ GDPR compliance features")
        print("✅ Safety monitoring and incident management")
        print("✅ Automated background processing")
        print("\nRefer to TRUST_SAFETY_COMPLIANCE_GUIDE.md for detailed usage instructions.")
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()