"""
Default configurations for scholar instances.

This module defines the default configuration values for AI Scholar and
Quant Scholar instances, including arXiv categories, storage paths, and
processing settings.
"""

from typing import List, Dict, Any

DEFAULT_AI_SCHOLAR_CONFIG = {
    "instance": {
        "name": "ai_scholar",
        "display_name": "AI Scholar",
        "description": "General AI and Physics Research Papers"
    },
    
    "data_sources": {
        "arxiv": {
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
            "start_date": "2020-01-01"
        },
        "journals": []
    },
    
    "storage": {
        "pdf_directory": "/datapool/aischolar/ai-scholar-arxiv-dataset/pdf",
        "processed_directory": "/datapool/aischolar/ai-scholar-arxiv-dataset/processed",
        "state_directory": "/datapool/aischolar/ai-scholar-arxiv-dataset/state",
        "error_log_directory": "/datapool/aischolar/ai-scholar-arxiv-dataset/errors",
        "archive_directory": "/datapool/aischolar/ai-scholar-arxiv-dataset/archive"
    },
    
    "processing": {
        "batch_size": 20,
        "max_concurrent_downloads": 5,
        "max_concurrent_processing": 3,
        "retry_attempts": 3,
        "timeout_seconds": 300,
        "memory_limit_mb": 4096
    },
    
    "vector_store": {
        "collection_name": "ai_scholar_papers",
        "embedding_model": "all-MiniLM-L6-v2",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "host": "localhost",
        "port": 8082
    },
    
    "notifications": {
        "enabled": False,
        "recipients": [],
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "from_email": "ai-scholar@aischolar.com"
    },
    
    "monthly_updates": {
        "enabled": True,
        "schedule": {
            "day_of_month": 1,
            "hour": 2,
            "minute": 0
        },
        "retention": {
            "keep_reports_days": 90,
            "keep_logs_days": 30,
            "keep_state_files_days": 7
        }
    },
    
    "performance": {
        "memory_limit_mb": 4096,
        "disk_space_warning_gb": 10,
        "processing_timeout": 3600,
        "health_check_interval": 300,
        "progress_update_interval": 2
    }
}

DEFAULT_QUANT_SCHOLAR_CONFIG = {
    "instance": {
        "name": "quant_scholar",
        "display_name": "Quant Scholar",
        "description": "Quantitative Finance and Statistics Research Papers"
    },
    
    "data_sources": {
        "arxiv": {
            "categories": [
                "econ.EM",
                "econ.GN",
                "econ.TH",
                "eess.SY",
                "math.ST",
                "math.PR",
                "math.OC",
                "q-fin.*",
                "stat.*"
            ],
            "start_date": "2020-01-01"
        },
        "journals": [
            {
                "name": "Journal of Statistical Software",
                "url": "https://www.jstatsoft.org/index",
                "handler": "JStatSoftwareHandler",
                "enabled": True
            },
            {
                "name": "R Journal",
                "url": "https://journal.r-project.org/issues.html",
                "handler": "RJournalHandler",
                "enabled": True
            }
        ]
    },
    
    "storage": {
        "pdf_directory": "/datapool/aischolar/quant-scholar-dataset/pdf",
        "processed_directory": "/datapool/aischolar/quant-scholar-dataset/processed",
        "state_directory": "/datapool/aischolar/quant-scholar-dataset/state",
        "error_log_directory": "/datapool/aischolar/quant-scholar-dataset/errors",
        "archive_directory": "/datapool/aischolar/quant-scholar-dataset/archive"
    },
    
    "processing": {
        "batch_size": 15,  # Slightly smaller for journal processing
        "max_concurrent_downloads": 4,  # More conservative for journal sources
        "max_concurrent_processing": 3,
        "retry_attempts": 3,
        "timeout_seconds": 450,  # Longer timeout for journal processing
        "memory_limit_mb": 4096
    },
    
    "vector_store": {
        "collection_name": "quant_scholar_papers",
        "embedding_model": "all-MiniLM-L6-v2",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "host": "localhost",
        "port": 8082
    },
    
    "notifications": {
        "enabled": False,
        "recipients": [],
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "from_email": "quant-scholar@aischolar.com"
    },
    
    "monthly_updates": {
        "enabled": True,
        "schedule": {
            "day_of_month": 2,  # Day after AI Scholar
            "hour": 2,
            "minute": 30
        },
        "retention": {
            "keep_reports_days": 90,
            "keep_logs_days": 30,
            "keep_state_files_days": 7
        }
    },
    
    "performance": {
        "memory_limit_mb": 4096,
        "disk_space_warning_gb": 10,
        "processing_timeout": 4500,  # Longer for journal processing
        "health_check_interval": 300,
        "progress_update_interval": 2
    },
    
    "journal_processing": {
        "jss": {
            "base_url": "https://www.jstatsoft.org",
            "rate_limit_delay": 2.0,
            "request_timeout": 30,
            "max_retries": 3
        },
        "rjournal": {
            "base_url": "https://journal.r-project.org",
            "rate_limit_delay": 2.0,
            "request_timeout": 30,
            "max_retries": 3
        }
    }
}

# Configuration templates for creating new instances
INSTANCE_CONFIG_TEMPLATE = {
    "instance": {
        "name": "{instance_name}",
        "display_name": "{display_name}",
        "description": "{description}"
    },
    
    "data_sources": {
        "arxiv": {
            "categories": [],
            "start_date": "2020-01-01"
        },
        "journals": []
    },
    
    "storage": {
        "pdf_directory": "/datapool/aischolar/{instance_name}-dataset/pdf",
        "processed_directory": "/datapool/aischolar/{instance_name}-dataset/processed",
        "state_directory": "/datapool/aischolar/{instance_name}-dataset/state",
        "error_log_directory": "/datapool/aischolar/{instance_name}-dataset/errors",
        "archive_directory": "/datapool/aischolar/{instance_name}-dataset/archive"
    },
    
    "processing": {
        "batch_size": 20,
        "max_concurrent_downloads": 5,
        "max_concurrent_processing": 3,
        "retry_attempts": 3,
        "timeout_seconds": 300,
        "memory_limit_mb": 4096
    },
    
    "vector_store": {
        "collection_name": "{instance_name}_papers",
        "embedding_model": "all-MiniLM-L6-v2",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "host": "localhost",
        "port": 8082
    },
    
    "notifications": {
        "enabled": False,
        "recipients": [],
        "smtp_server": "localhost",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "from_email": "{instance_name}@localhost"
    },
    
    "monthly_updates": {
        "enabled": True,
        "schedule": {
            "day_of_month": 1,
            "hour": 2,
            "minute": 0
        },
        "retention": {
            "keep_reports_days": 90,
            "keep_logs_days": 30,
            "keep_state_files_days": 7
        }
    },
    
    "performance": {
        "memory_limit_mb": 4096,
        "disk_space_warning_gb": 10,
        "processing_timeout": 3600,
        "health_check_interval": 300,
        "progress_update_interval": 2
    }
}

# Common arXiv categories by field
ARXIV_CATEGORIES_BY_FIELD = {
    "ai_ml": [
        "cs.AI",  # Artificial Intelligence
        "cs.LG",  # Machine Learning
        "cs.CL",  # Computation and Language
        "cs.CV",  # Computer Vision and Pattern Recognition
        "cs.NE",  # Neural and Evolutionary Computing
        "stat.ML"  # Machine Learning (Statistics)
    ],
    
    "physics": [
        "cond-mat",  # Condensed Matter
        "gr-qc",     # General Relativity and Quantum Cosmology
        "hep-ph",    # High Energy Physics - Phenomenology
        "hep-th",    # High Energy Physics - Theory
        "math-ph",   # Mathematical Physics
        "physics",   # Physics (general)
        "quant-ph"   # Quantum Physics
    ],
    
    "mathematics": [
        "math.AG",  # Algebraic Geometry
        "math.AT",  # Algebraic Topology
        "math.CA",  # Classical Analysis and ODEs
        "math.CO",  # Combinatorics
        "math.CT",  # Category Theory
        "math.CV",  # Complex Variables
        "math.DG",  # Differential Geometry
        "math.DS",  # Dynamical Systems
        "math.FA",  # Functional Analysis
        "math.GM",  # General Mathematics
        "math.GN",  # General Topology
        "math.GR",  # Group Theory
        "math.GT",  # Geometric Topology
        "math.HO",  # History and Overview
        "math.IT",  # Information Theory
        "math.KT",  # K-Theory and Homology
        "math.LO",  # Logic
        "math.MG",  # Metric Geometry
        "math.MP",  # Mathematical Physics
        "math.NA",  # Numerical Analysis
        "math.NT",  # Number Theory
        "math.OA",  # Operator Algebras
        "math.OC",  # Optimization and Control
        "math.PR",  # Probability
        "math.QA",  # Quantum Algebra
        "math.RA",  # Rings and Algebras
        "math.RT",  # Representation Theory
        "math.SG",  # Symplectic Geometry
        "math.SP",  # Spectral Theory
        "math.ST"   # Statistics Theory
    ],
    
    "economics_finance": [
        "econ.EM",  # Econometrics
        "econ.GN",  # General Economics
        "econ.TH",  # Theoretical Economics
        "q-fin.CP", # Computational Finance
        "q-fin.EC", # Economics
        "q-fin.GN", # General Finance
        "q-fin.MF", # Mathematical Finance
        "q-fin.PM", # Portfolio Management
        "q-fin.PR", # Pricing of Securities
        "q-fin.RM", # Risk Management
        "q-fin.ST", # Statistical Finance
        "q-fin.TR"  # Trading and Market Microstructure
    ],
    
    "statistics": [
        "stat.AP",  # Applications
        "stat.CO",  # Computation
        "stat.ME",  # Methodology
        "stat.ML",  # Machine Learning
        "stat.OT",  # Other Statistics
        "stat.TH"   # Theory
    ],
    
    "computer_science": [
        "cs.AI",  # Artificial Intelligence
        "cs.AR",  # Hardware Architecture
        "cs.CC",  # Computational Complexity
        "cs.CE",  # Computational Engineering, Finance, and Science
        "cs.CG",  # Computational Geometry
        "cs.CL",  # Computation and Language
        "cs.CR",  # Cryptography and Security
        "cs.CV",  # Computer Vision and Pattern Recognition
        "cs.CY",  # Computers and Society
        "cs.DB",  # Databases
        "cs.DC",  # Distributed, Parallel, and Cluster Computing
        "cs.DL",  # Digital Libraries
        "cs.DM",  # Discrete Mathematics
        "cs.DS",  # Data Structures and Algorithms
        "cs.ET",  # Emerging Technologies
        "cs.FL",  # Formal Languages and Automata Theory
        "cs.GL",  # General Literature
        "cs.GR",  # Graphics
        "cs.GT",  # Computer Science and Game Theory
        "cs.HC",  # Human-Computer Interaction
        "cs.IR",  # Information Retrieval
        "cs.IT",  # Information Theory
        "cs.LG",  # Machine Learning
        "cs.LO",  # Logic in Computer Science
        "cs.MA",  # Multiagent Systems
        "cs.MM",  # Multimedia
        "cs.MS",  # Mathematical Software
        "cs.NA",  # Numerical Analysis
        "cs.NE",  # Neural and Evolutionary Computing
        "cs.NI",  # Networking and Internet Architecture
        "cs.OH",  # Other Computer Science
        "cs.OS",  # Operating Systems
        "cs.PF",  # Performance
        "cs.PL",  # Programming Languages
        "cs.RO",  # Robotics
        "cs.SC",  # Symbolic Computation
        "cs.SD",  # Sound
        "cs.SE",  # Software Engineering
        "cs.SI",  # Social and Information Networks
        "cs.SY"   # Systems and Control
    ]
}


def get_categories_for_field(field: str) -> List[str]:
    """
    Get arXiv categories for a specific field.
    
    Args:
        field: Field name (e.g., 'ai_ml', 'physics', 'mathematics')
        
    Returns:
        List of arXiv categories for the field
    """
    return ARXIV_CATEGORIES_BY_FIELD.get(field, [])


def create_custom_instance_config(instance_name: str, 
                                display_name: str,
                                description: str,
                                arxiv_categories: List[str],
                                base_directory: str = "/datapool/aischolar") -> Dict[str, Any]:
    """
    Create a custom instance configuration.
    
    Args:
        instance_name: Name of the instance
        display_name: Human-readable display name
        description: Description of the instance
        arxiv_categories: List of arXiv categories
        base_directory: Base directory for storage
        
    Returns:
        Configuration dictionary
    """
    config = INSTANCE_CONFIG_TEMPLATE.copy()
    
    # Replace placeholders
    config_str = str(config).replace("{instance_name}", instance_name)
    config_str = config_str.replace("{display_name}", display_name)
    config_str = config_str.replace("{description}", description)
    
    # Convert back to dict (this is a simple approach, could be improved)
    import ast
    config = ast.literal_eval(config_str)
    
    # Set arXiv categories
    config["data_sources"]["arxiv"]["categories"] = arxiv_categories
    
    # Update base directory if different
    if base_directory != "/datapool/aischolar":
        for key in config["storage"]:
            config["storage"][key] = config["storage"][key].replace(
                "/datapool/aischolar", base_directory
            )
    
    return config