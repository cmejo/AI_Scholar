"""
Default configuration for arXiv RAG Enhancement system.

This module defines the default configuration values for all processing scripts.
"""

DEFAULT_CONFIG = {
    # Global settings
    "global": {
        "output_dir": "/datapool/aischolar/arxiv-dataset-2024",
        "categories": [
            "cond-mat",
            "gr-qc", 
            "hep-ph",
            "hep-th",
            "math",
            "math-ph",
            "physics",
            "q-alg",
            "quant-ph"
        ],
        "batch_size": 10,
        "max_concurrent": 3,
        "verbose_logging": False
    },
    
    # Local processor settings
    "local_processor": {
        "source_dir": "~/arxiv-dataset/pdf",
        "batch_size": 10,
        "max_files": None,
        "resume_enabled": True,
        "skip_existing": True
    },
    
    # Bulk downloader settings
    "bulk_downloader": {
        "start_date": "2024-07-01",
        "end_date": None,  # Current date
        "max_papers": None,
        "max_concurrent_downloads": 5,
        "download_timeout": 300,  # 5 minutes
        "retry_attempts": 3,
        "retry_delay": 5  # seconds
    },
    
    # Monthly updater settings
    "monthly_updater": {
        "enabled": True,
        "schedule": {
            "day_of_month": 1,
            "hour": 2,
            "minute": 0
        },
        "email_notifications": {
            "enabled": False,
            "smtp_server": "localhost",
            "smtp_port": 587,
            "use_tls": True,
            "username": "",
            "password": "",
            "from_email": "arxiv-updater@localhost",
            "to_emails": []
        },
        "retention": {
            "keep_reports_days": 90,
            "keep_logs_days": 30,
            "keep_state_files_days": 7,
            "cleanup_old_pdfs": False
        }
    },
    
    # RAG system integration
    "rag_integration": {
        "chromadb": {
            "host": "localhost",
            "port": 8082,
            "collection_name": "scientific_papers",
            "embedding_model": "all-MiniLM-L6-v2"
        },
        "processing": {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "min_chunk_size": 100,
            "max_chunks_per_document": 50
        }
    },
    
    # Error handling and logging
    "error_handling": {
        "max_error_rate": 50.0,  # percentage
        "continue_on_errors": True,
        "log_level": "INFO",
        "log_rotation": {
            "max_size_mb": 100,
            "backup_count": 5
        },
        "error_reporting": {
            "create_detailed_reports": True,
            "include_stack_traces": True,
            "max_errors_in_summary": 10
        }
    },
    
    # Performance settings
    "performance": {
        "memory_limit_mb": 4096,
        "disk_space_warning_gb": 10,
        "processing_timeout": 3600,  # 1 hour
        "health_check_interval": 300,  # 5 minutes
        "progress_update_interval": 2  # seconds
    },
    
    # Network settings
    "network": {
        "arxiv_api": {
            "base_url": "http://export.arxiv.org/api/query",
            "rate_limit_delay": 3.0,  # seconds
            "request_timeout": 30,
            "max_retries": 3
        },
        "download": {
            "user_agent": "AI-Scholar-RAG-Enhancement/1.0",
            "connection_timeout": 30,
            "read_timeout": 300,
            "max_redirects": 5
        }
    },
    
    # Security settings
    "security": {
        "file_permissions": {
            "directories": 0o755,
            "files": 0o644,
            "executables": 0o755
        },
        "allowed_file_extensions": [".pdf"],
        "max_file_size_mb": 50,
        "scan_for_malware": False
    }
}