#!/usr/bin/env python3
"""
Setup script for Multi-Modal Document Processing
Installs dependencies, configures models, and validates setup
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, description=""):
    """Run a shell command and return success status"""
    try:
        logger.info(f"Running: {description or command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Success: {description or command}")
            return True
        else:
            logger.error(f"❌ Failed: {description or command}")
            logger.error(f"Error: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Exception running command: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    logger.info("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        logger.error(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible. Need Python 3.8+")
        return False

def install_system_dependencies():
    """Install system-level dependencies"""
    logger.info("Installing system dependencies...")
    
    system = platform.system().lower()
    
    if system == "linux":
        # Ubuntu/Debian
        commands = [
            ("sudo apt-get update", "Updating package list"),
            ("sudo apt-get install -y tesseract-ocr", "Installing Tesseract OCR"),
            ("sudo apt-get install -y poppler-utils", "Installing Poppler utilities"),
            ("sudo apt-get install -y libgl1-mesa-glx", "Installing OpenGL libraries"),
            ("sudo apt-get install -y libglib2.0-0", "Installing GLib libraries"),
        ]
    elif system == "darwin":
        # macOS
        commands = [
            ("brew install tesseract", "Installing Tesseract OCR"),
            ("brew install poppler", "Installing Poppler utilities"),
        ]
    elif system == "windows":
        logger.warning("⚠️  Windows detected. Please install dependencies manually:")
        logger.warning("1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
        logger.warning("2. Download Poppler from: https://blog.alivate.com.au/poppler-windows/")
        logger.warning("3. Add both to your PATH environment variable")
        return True
    else:
        logger.warning(f"⚠️  Unknown system: {system}. Please install dependencies manually.")
        return True
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    return success

def install_python_dependencies():
    """Install Python dependencies"""
    logger.info("Installing Python dependencies...")
    
    # Core dependencies
    core_deps = [
        "Pillow>=10.1.0",
        "opencv-python>=4.8.1.78",
        "pytesseract>=0.3.10",
        "easyocr>=1.7.0",
        "pdf2image>=1.16.3",
        "pdfplumber>=0.10.3",
        "pandas>=2.1.4",
        "numpy>=1.24.4",
    ]
    
    # Advanced dependencies (optional)
    advanced_deps = [
        "tabula-py>=2.8.2",
        "camelot-py[cv]>=0.11.0",
        "transformers>=4.36.2",
        "torch>=2.1.2",
        "timm>=0.9.12",
    ]
    
    # Layout analysis (optional, requires additional setup)
    layout_deps = [
        "layoutparser>=0.3.4",
        # "detectron2>=0.6",  # Requires special installation
    ]
    
    success = True
    
    # Install core dependencies
    logger.info("Installing core dependencies...")
    for dep in core_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            success = False
    
    # Install advanced dependencies
    logger.info("Installing advanced dependencies...")
    for dep in advanced_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            logger.warning(f"⚠️  Failed to install {dep}, continuing...")
    
    # Install layout analysis dependencies
    logger.info("Installing layout analysis dependencies...")
    for dep in layout_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            logger.warning(f"⚠️  Failed to install {dep}, continuing...")
    
    return success

def download_models():
    """Download and cache AI models"""
    logger.info("Downloading AI models...")
    
    try:
        # Test model downloads
        logger.info("Testing model downloads...")
        
        # Import and test transformers
        import transformers
        from transformers import BlipProcessor, BlipForConditionalGeneration
        
        logger.info("Downloading BLIP image captioning model...")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        
        logger.info("✅ BLIP model downloaded successfully")
        
        # Test EasyOCR model download
        import easyocr
        logger.info("Downloading EasyOCR models...")
        reader = easyocr.Reader(['en'])
        logger.info("✅ EasyOCR models downloaded successfully")
        
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️  Could not download models due to missing dependencies: {e}")
        return False
    except Exception as e:
        logger.warning(f"⚠️  Model download failed: {e}")
        return False

def test_installation():
    """Test the installation"""
    logger.info("Testing installation...")
    
    try:
        # Test imports
        logger.info("Testing imports...")
        
        import PIL
        logger.info("✅ PIL/Pillow imported successfully")
        
        import cv2
        logger.info("✅ OpenCV imported successfully")
        
        import pytesseract
        logger.info("✅ Pytesseract imported successfully")
        
        try:
            import easyocr
            logger.info("✅ EasyOCR imported successfully")
        except ImportError:
            logger.warning("⚠️  EasyOCR not available")
        
        try:
            import transformers
            logger.info("✅ Transformers imported successfully")
        except ImportError:
            logger.warning("⚠️  Transformers not available")
        
        # Test Tesseract
        logger.info("Testing Tesseract OCR...")
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract version: {version}")
        except Exception as e:
            logger.error(f"❌ Tesseract test failed: {e}")
            return False
        
        # Test basic functionality
        logger.info("Testing basic functionality...")
        from PIL import Image, ImageDraw
        
        # Create test image
        img = Image.new('RGB', (200, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Test OCR", fill='black')
        
        # Test OCR
        text = pytesseract.image_to_string(img)
        if "Test" in text or "OCR" in text:
            logger.info("✅ Basic OCR functionality working")
        else:
            logger.warning("⚠️  OCR may not be working correctly")
        
        # Test our multimodal processor
        logger.info("Testing multimodal processor...")
        try:
            from services.multimodal_document_processor import multimodal_processor
            stats = multimodal_processor.get_stats()
            logger.info("✅ Multimodal processor loaded successfully")
            logger.info(f"   Capabilities: {stats['capabilities']}")
        except ImportError:
            logger.warning("⚠️  Multimodal processor not available (may need to run from project root)")
        except Exception as e:
            logger.warning(f"⚠️  Multimodal processor test failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Installation test failed: {e}")
        return False

def setup_database():
    """Setup database for multimodal processing"""
    logger.info("Setting up database...")
    
    try:
        # Check if we can run migrations
        if os.path.exists("manage_db.py"):
            logger.info("Running database migrations...")
            if run_command("python manage_db.py upgrade", "Running database migrations"):
                logger.info("✅ Database migrations completed")
                return True
            else:
                logger.warning("⚠️  Database migrations failed")
                return False
        else:
            logger.warning("⚠️  manage_db.py not found, skipping database setup")
            return True
            
    except Exception as e:
        logger.warning(f"⚠️  Database setup failed: {e}")
        return False

def create_upload_directories():
    """Create necessary upload directories"""
    logger.info("Creating upload directories...")
    
    directories = [
        "uploads/documents",
        "vector_db",
        "temp"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✅ Created directory: {directory}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to create directory {directory}: {e}")
    
    return True

def main():
    """Main setup function"""
    logger.info("🚀 Multi-Modal Document Processing Setup")
    logger.info("=" * 60)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        logger.error("❌ Python version check failed")
        return False
    
    # Install system dependencies
    if not install_system_dependencies():
        logger.warning("⚠️  Some system dependencies failed to install")
        success = False
    
    # Install Python dependencies
    if not install_python_dependencies():
        logger.warning("⚠️  Some Python dependencies failed to install")
        success = False
    
    # Download models
    if not download_models():
        logger.warning("⚠️  Model download failed")
    
    # Create directories
    create_upload_directories()
    
    # Setup database
    if not setup_database():
        logger.warning("⚠️  Database setup failed")
    
    # Test installation
    if not test_installation():
        logger.error("❌ Installation test failed")
        success = False
    
    # Final status
    if success:
        logger.info("\n🎉 Setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Run the test suite: python test_multimodal_document_processing.py")
        logger.info("2. Start the application and test document upload")
        logger.info("3. Check the documentation: MULTIMODAL_DOCUMENT_PROCESSING.md")
    else:
        logger.error("\n❌ Setup completed with warnings/errors")
        logger.error("Please check the logs above and resolve any issues")
        logger.error("You may need to install some dependencies manually")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)