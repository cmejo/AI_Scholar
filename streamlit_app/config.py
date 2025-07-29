"""
Configuration for Streamlit app
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Streamlit Configuration
STREAMLIT_CONFIG = {
    "page_title": "AI Scholar RAG",
    "page_icon": "🧠",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# UI Settings
UI_SETTINGS = {
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "supported_file_types": ['pdf', 'txt', 'md', 'docx'],
    "default_model": "mistral",
    "default_temperature": 0.7,
    "default_max_sources": 5
}