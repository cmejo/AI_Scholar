#!/usr/bin/env python3
"""
Master script to generate all figures for AI Scholar academic paper
"""

import os
import sys
import subprocess

def ensure_directory():
    """Ensure figures directory exists"""
    if not os.path.exists('papers/figures'):
        os.makedirs('papers/figures')

def install_requirements():
    """Install required packages"""
    packages = [
        'matplotlib',
        'seaborn',
        'numpy',
        'pandas',
        'networkx',
        'scipy'
    ]
    
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def main():
    """Generate all figures"""
    ensure_directory()
    install_requirements()
    
    print("Generating AI Scholar academic paper figures...")
    
    # Import and run diagram generation scripts
    try:
        from generate_diagrams import create_system_architecture, create_multimodal_architecture
        from generate_additional_diagrams import (
            create_blockchain_consensus, 
            create_knowledge_graph_3d,
            create_performance_comparison,
            create_user_satisfaction
        )
        
        print("Creating system architecture diagram...")
        create_system_architecture()
        
        print("Creating multi-modal architecture diagram...")
        create_multimodal_architecture()
        
        print("Creating blockchain consensus diagram...")
        create_blockchain_consensus()
        
        print("Creating 3D knowledge graph visualization...")
        create_knowledge_graph_3d()
        
        print("Creating performance comparison charts...")
        create_performance_comparison()
        
        print("Creating user satisfaction visualization...")
        create_user_satisfaction()
        
        print("\nAll figures generated successfully!")
        print("Generated files:")
        print("- papers/figures/system_architecture.png")
        print("- papers/figures/multimodal_architecture.png")
        print("- papers/figures/blockchain_consensus.png")
        print("- papers/figures/knowledge_graph_3d.png")
        print("- papers/figures/performance_comparison.png")
        print("- papers/figures/user_satisfaction.png")
        
    except Exception as e:
        print(f"Error generating figures: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())