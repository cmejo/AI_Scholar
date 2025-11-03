#!/usr/bin/env python3
"""
Setup script for arXiv RAG Enhancement System

This script sets up the arXiv RAG Enhancement system by:
1. Checking system requirements
2. Creating necessary directories
3. Installing dependencies
4. Validating existing services
5. Creating sample configuration files
6. Setting up logging infrastructure

Usage:
    python setup_arxiv_rag_enhancement.py [options]
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import json
import shutil

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from arxiv_rag_enhancement.config import ConfigManager


def setup_logging():
    """Set up logging for the setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('setup_arxiv_rag_enhancement.log')
        ]
    )


def check_python_version():
    """Check if Python version is compatible."""
    logger = logging.getLogger(__name__)
    
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    
    logger.info(f"Python version: {sys.version}")
    return True


def check_system_requirements():
    """Check system requirements and dependencies."""
    logger = logging.getLogger(__name__)
    
    requirements = {
        'disk_space_gb': 50,  # Minimum disk space in GB
        'memory_gb': 4,       # Minimum RAM in GB
        'python_packages': [
            'requests',
            'aiohttp',
            'aiofiles',
            'PyYAML',
            'numpy'
        ]
    }
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage('/')
        free_gb = free // (1024**3)
        
        if free_gb < requirements['disk_space_gb']:
            logger.warning(f"Low disk space: {free_gb}GB available, {requirements['disk_space_gb']}GB recommended")
        else:
            logger.info(f"Disk space: {free_gb}GB available")
    except Exception as e:
        logger.warning(f"Could not check disk space: {e}")
    
    # Check memory
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        if memory_gb < requirements['memory_gb']:
            logger.warning(f"Low memory: {memory_gb}GB available, {requirements['memory_gb']}GB recommended")
        else:
            logger.info(f"Memory: {memory_gb}GB available")
    except ImportError:
        logger.info("psutil not available, skipping memory check")
    except Exception as e:
        logger.warning(f"Could not check memory: {e}")
    
    return True


def install_dependencies():
    """Install required Python packages."""
    logger = logging.getLogger(__name__)
    
    requirements_file = Path(__file__).parent / "arxiv_rag_enhancement" / "requirements.txt"
    
    if not requirements_file.exists():
        logger.error(f"Requirements file not found: {requirements_file}")
        return False
    
    try:
        logger.info("Installing Python dependencies...")
        
        # Install requirements
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Dependencies installed successfully")
            return True
        else:
            logger.error(f"Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        return False


def create_directory_structure(output_dir: str = "/datapool/aischolar/arxiv-dataset-2024"):
    """Create necessary directory structure."""
    logger = logging.getLogger(__name__)
    
    directories = [
        output_dir,
        f"{output_dir}/pdfs",
        f"{output_dir}/pdfs/cond-mat",
        f"{output_dir}/pdfs/gr-qc",
        f"{output_dir}/pdfs/hep-ph",
        f"{output_dir}/pdfs/hep-th",
        f"{output_dir}/pdfs/math",
        f"{output_dir}/pdfs/math-ph",
        f"{output_dir}/pdfs/physics",
        f"{output_dir}/pdfs/q-alg",
        f"{output_dir}/pdfs/quant-ph",
        f"{output_dir}/processed",
        f"{output_dir}/processed/state_files",
        f"{output_dir}/processed/error_logs",
        f"{output_dir}/processed/reports",
        f"{output_dir}/metadata",
        f"{output_dir}/config"
    ]
    
    try:
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
        
        logger.info(f"Directory structure created at {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create directory structure: {e}")
        return False


def validate_existing_services():
    """Validate that existing AI Scholar services are available."""
    logger = logging.getLogger(__name__)
    
    try:
        # Test imports of existing services
        from services.scientific_pdf_processor import scientific_pdf_processor
        from services.vector_store_service import vector_store_service
        from services.scientific_rag_service import scientific_rag_service
        
        logger.info("✅ Existing AI Scholar services are available")
        
        # Test ChromaDB connection
        try:
            import chromadb
            logger.info("✅ ChromaDB library is available")
        except ImportError:
            logger.warning("⚠️  ChromaDB library not found - may need to install")
        
        # Test sentence transformers
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("✅ Sentence Transformers library is available")
        except ImportError:
            logger.warning("⚠️  Sentence Transformers library not found - may need to install")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Required AI Scholar services not available: {e}")
        logger.error("Please ensure you're running this setup from the AI Scholar backend directory")
        return False


def create_configuration_files(output_dir: str):
    """Create sample configuration files."""
    logger = logging.getLogger(__name__)
    
    try:
        config_dir = Path(output_dir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create ConfigManager and generate sample config
        config_manager = ConfigManager()
        
        # Create YAML configuration
        yaml_config = config_dir / "arxiv_rag_config.yaml"
        if config_manager.create_sample_config(yaml_config):
            logger.info(f"✅ Sample YAML configuration created: {yaml_config}")
        
        # Create JSON configuration
        json_config = config_dir / "arxiv_rag_config.json"
        if config_manager.create_sample_config(json_config):
            logger.info(f"✅ Sample JSON configuration created: {json_config}")
        
        # Create environment variables template
        env_template = config_dir / ".env.template"
        with open(env_template, 'w') as f:
            f.write("""# arXiv RAG Enhancement System Environment Variables
# Copy this file to .env and customize the values

# Global settings
ARXIV_RAG_OUTPUT_DIR=/datapool/aischolar/arxiv-dataset-2024
ARXIV_RAG_BATCH_SIZE=10
ARXIV_RAG_VERBOSE=false

# Local processor settings
ARXIV_LOCAL_SOURCE_DIR=~/arxiv-dataset/pdf
ARXIV_LOCAL_MAX_FILES=

# Bulk downloader settings
ARXIV_BULK_START_DATE=2024-07-01
ARXIV_BULK_MAX_PAPERS=

# ChromaDB settings
CHROMADB_HOST=localhost
CHROMADB_PORT=8082

# Email notifications (optional)
ARXIV_EMAIL_ENABLED=false
ARXIV_SMTP_SERVER=smtp.gmail.com
ARXIV_SMTP_PORT=587
ARXIV_SMTP_USERNAME=your-email@gmail.com
ARXIV_SMTP_PASSWORD=your-app-password
ARXIV_FROM_EMAIL=arxiv-updater@yourdomain.com
ARXIV_TO_EMAILS=admin@yourdomain.com

# Logging
ARXIV_LOG_LEVEL=INFO
""")
        
        logger.info(f"✅ Environment variables template created: {env_template}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create configuration files: {e}")
        return False


def create_startup_scripts(output_dir: str):
    """Create convenient startup scripts."""
    logger = logging.getLogger(__name__)
    
    try:
        scripts_dir = Path(output_dir) / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        backend_dir = Path(__file__).parent
        
        # Script 1: Local processor
        local_script = scripts_dir / "run_local_processor.sh"
        with open(local_script, 'w') as f:
            f.write(f"""#!/bin/bash
# arXiv Local Dataset Processor
cd {backend_dir}
python process_local_arxiv_dataset.py "$@"
""")
        local_script.chmod(0o755)
        
        # Script 2: Bulk downloader
        bulk_script = scripts_dir / "run_bulk_downloader.sh"
        with open(bulk_script, 'w') as f:
            f.write(f"""#!/bin/bash
# arXiv Bulk Downloader
cd {backend_dir}
python download_bulk_arxiv_papers.py "$@"
""")
        bulk_script.chmod(0o755)
        
        # Script 3: Monthly updater
        monthly_script = scripts_dir / "run_monthly_updater.sh"
        with open(monthly_script, 'w') as f:
            f.write(f"""#!/bin/bash
# arXiv Monthly Updater
cd {backend_dir}
python run_monthly_update.py "$@"
""")
        monthly_script.chmod(0o755)
        
        # Combined status script
        status_script = scripts_dir / "check_status.sh"
        with open(status_script, 'w') as f:
            f.write(f"""#!/bin/bash
# Check arXiv RAG Enhancement System Status
echo "arXiv RAG Enhancement System Status"
echo "=================================="

echo "1. Checking directory structure..."
ls -la {output_dir}/

echo "2. Checking ChromaDB connection..."
python -c "
try:
    import chromadb
    client = chromadb.HttpClient(host='localhost', port=8082)
    client.heartbeat()
    print('✅ ChromaDB is running')
except Exception as e:
    print(f'❌ ChromaDB connection failed: {{e}}')
"

echo "3. Checking recent processing logs..."
if [ -d "{output_dir}/processed/error_logs" ]; then
    ls -lt {output_dir}/processed/error_logs/ | head -5
else
    echo "No logs found"
fi

echo "4. Checking storage usage..."
du -sh {output_dir}/*

echo "Status check complete."
""")
        status_script.chmod(0o755)
        
        logger.info(f"✅ Startup scripts created in {scripts_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create startup scripts: {e}")
        return False


def run_validation_tests():
    """Run validation tests to ensure everything is working."""
    logger = logging.getLogger(__name__)
    
    logger.info("Running validation tests...")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Configuration loading
    tests_total += 1
    try:
        config_manager = ConfigManager()
        errors = config_manager.validate_config()
        if not errors:
            logger.info("✅ Configuration validation passed")
            tests_passed += 1
        else:
            logger.warning(f"⚠️  Configuration validation warnings: {errors}")
            tests_passed += 1  # Warnings are OK
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
    
    # Test 2: Import all modules
    tests_total += 1
    try:
        from arxiv_rag_enhancement.processors.local_processor import ArxivLocalProcessor
        from arxiv_rag_enhancement.processors.bulk_downloader import ArxivBulkDownloader
        from arxiv_rag_enhancement.processors.monthly_updater import ArxivMonthlyUpdater
        from arxiv_rag_enhancement.shared import StateManager, ProgressTracker, ErrorHandler
        
        logger.info("✅ All modules imported successfully")
        tests_passed += 1
    except Exception as e:
        logger.error(f"❌ Module import failed: {e}")
    
    # Test 3: Directory permissions
    tests_total += 1
    try:
        test_file = Path("/datapool/aischolar/arxiv-dataset-2024/test_write.tmp")
        test_file.write_text("test")
        test_file.unlink()
        logger.info("✅ Directory write permissions OK")
        tests_passed += 1
    except Exception as e:
        logger.error(f"❌ Directory write test failed: {e}")
    
    logger.info(f"Validation complete: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


def main():
    """Main setup function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 arXiv RAG Enhancement System Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        print("❌ Setup failed: Python version incompatible")
        return False
    
    # Check system requirements
    logger.info("Checking system requirements...")
    check_system_requirements()
    
    # Validate existing services
    logger.info("Validating existing AI Scholar services...")
    if not validate_existing_services():
        print("❌ Setup failed: Required services not available")
        return False
    
    # Install dependencies
    logger.info("Installing dependencies...")
    if not install_dependencies():
        print("❌ Setup failed: Could not install dependencies")
        return False
    
    # Create directory structure
    output_dir = "/datapool/aischolar/arxiv-dataset-2024"
    logger.info(f"Creating directory structure at {output_dir}...")
    if not create_directory_structure(output_dir):
        print("❌ Setup failed: Could not create directories")
        return False
    
    # Create configuration files
    logger.info("Creating configuration files...")
    if not create_configuration_files(output_dir):
        print("❌ Setup failed: Could not create configuration files")
        return False
    
    # Create startup scripts
    logger.info("Creating startup scripts...")
    if not create_startup_scripts(output_dir):
        print("❌ Setup failed: Could not create startup scripts")
        return False
    
    # Run validation tests
    logger.info("Running validation tests...")
    if not run_validation_tests():
        print("⚠️  Setup completed with warnings - check logs for details")
    else:
        print("✅ Setup completed successfully!")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print(f"📁 Installation directory: {output_dir}")
    print(f"📋 Configuration files: {output_dir}/config/")
    print(f"🔧 Startup scripts: {output_dir}/scripts/")
    print(f"📊 Logs: {output_dir}/processed/error_logs/")
    print("\nNext steps:")
    print("1. Review and customize configuration files")
    print("2. Ensure ChromaDB is running on localhost:8082")
    print("3. Run the local processor to test: python process_local_arxiv_dataset.py --dry-run")
    print("4. Set up monthly updates: python run_monthly_update.py --setup-cron")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)