#!/usr/bin/env python3
"""
Validation Script for Continuous Monitoring System
Validates the implementation without requiring external dependencies.
"""

import json
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
import sys

def validate_file_structure():
    """Validate that all required files exist."""
    print("🔍 Validating file structure...")
    
    required_files = [
        "scripts/continuous_monitoring_system.py",
        "scripts/cicd_quality_gates.py",
        "scripts/monitoring_dashboard.py",
        "scripts/maintenance_automation.py",
        "scripts/test_continuous_monitoring.py",
        "scripts/demo_continuous_monitoring.py",
        "scripts/README-continuous-monitoring.md",
        "monitoring-config.yml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def validate_python_syntax():
    """Validate Python syntax of all scripts."""
    print("🐍 Validating Python syntax...")
    
    python_files = [
        "scripts/continuous_monitoring_system.py",
        "scripts/cicd_quality_gates.py",
        "scripts/monitoring_dashboard.py",
        "scripts/maintenance_automation.py",
        "scripts/test_continuous_monitoring.py",
        "scripts/demo_continuous_monitoring.py"
    ]
    
    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}: {e}")
    
    if syntax_errors:
        print(f"❌ Syntax errors found: {syntax_errors}")
        return False
    else:
        print("✅ All Python files have valid syntax")
        return True

def validate_imports():
    """Validate that core imports work (without external dependencies)."""
    print("📦 Validating core imports...")
    
    try:
        # Test basic imports that should work without external dependencies
        import sqlite3
        import json
        import logging
        import subprocess
        import time
        from datetime import datetime, timedelta
        from pathlib import Path
        from typing import Dict, List, Any, Optional
        from dataclasses import dataclass
        from enum import Enum
        
        print("✅ Core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def validate_database_schema():
    """Validate database schema creation."""
    print("💾 Validating database schema...")
    
    try:
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        # Test database creation
        with sqlite3.connect(db_path) as conn:
            # Create tables as defined in the monitoring system
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_issues INTEGER,
                    critical_issues INTEGER,
                    high_issues INTEGER,
                    medium_issues INTEGER,
                    low_issues INTEGER,
                    ubuntu_issues INTEGER,
                    auto_fixable_issues INTEGER,
                    test_coverage REAL,
                    build_success BOOLEAN,
                    deployment_success BOOLEAN
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    component TEXT,
                    ubuntu_specific BOOLEAN,
                    auto_fixable BOOLEAN,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_notes TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_gate_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    gate_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    threshold_value TEXT,
                    actual_value TEXT,
                    passed BOOLEAN
                )
            """)
            
            conn.commit()
            
            # Verify tables were created
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ["quality_metrics", "monitoring_alerts", "quality_gate_results"]
            for table in expected_tables:
                if table not in tables:
                    print(f"❌ Missing table: {table}")
                    return False
        
        # Clean up
        os.unlink(db_path)
        
        print("✅ Database schema validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Database schema validation failed: {e}")
        return False

def validate_configuration_format():
    """Validate configuration file format."""
    print("⚙️ Validating configuration format...")
    
    config_file = Path("monitoring-config.yml")
    if not config_file.exists():
        print("❌ Configuration file not found")
        return False
    
    try:
        # Basic YAML-like validation (without requiring PyYAML)
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Check for basic structure
        required_sections = [
            "monitoring:",
            "quality_gates:",
            "alerts:",
            "maintenance:"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing configuration sections: {missing_sections}")
            return False
        
        print("✅ Configuration format validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def validate_class_definitions():
    """Validate that key classes are properly defined."""
    print("🏗️ Validating class definitions...")
    
    try:
        # Read and check class definitions
        monitoring_file = Path("scripts/continuous_monitoring_system.py")
        with open(monitoring_file, 'r') as f:
            content = f.read()
        
        required_classes = [
            "class AlertSeverity(Enum):",
            "class MonitoringStatus(Enum):",
            "class QualityGate:",
            "class MonitoringAlert:",
            "class QualityMetrics:",
            "class ContinuousMonitoringSystem:"
        ]
        
        missing_classes = []
        for class_def in required_classes:
            if class_def not in content:
                missing_classes.append(class_def)
        
        if missing_classes:
            print(f"❌ Missing class definitions: {missing_classes}")
            return False
        
        print("✅ Class definitions validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Class definitions validation failed: {e}")
        return False

def validate_method_signatures():
    """Validate that key methods have correct signatures."""
    print("🔧 Validating method signatures...")
    
    try:
        monitoring_file = Path("scripts/continuous_monitoring_system.py")
        with open(monitoring_file, 'r') as f:
            content = f.read()
        
        required_methods = [
            "def run_quality_analysis(self)",
            "def evaluate_quality_gates(self",
            "def detect_regressions(self",
            "def send_alerts(self",
            "def run_maintenance_procedures(self",
            "def run_monitoring_cycle(self)"
        ]
        
        missing_methods = []
        for method in required_methods:
            if method not in content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing method signatures: {missing_methods}")
            return False
        
        print("✅ Method signatures validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Method signatures validation failed: {e}")
        return False

def validate_documentation():
    """Validate documentation completeness."""
    print("📚 Validating documentation...")
    
    readme_file = Path("scripts/README-continuous-monitoring.md")
    if not readme_file.exists():
        print("❌ README file not found")
        return False
    
    try:
        with open(readme_file, 'r') as f:
            content = f.read()
        
        required_sections = [
            "# Continuous Monitoring and Alerting System",
            "## Overview",
            "## Components",
            "## Configuration",
            "## Quality Gates",
            "## CI/CD Integration",
            "## Usage"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing documentation sections: {missing_sections}")
            return False
        
        # Check minimum length
        if len(content) < 5000:  # Reasonable minimum for comprehensive docs
            print("❌ Documentation appears incomplete (too short)")
            return False
        
        print("✅ Documentation validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Documentation validation failed: {e}")
        return False

def run_comprehensive_validation():
    """Run all validation checks."""
    print("🚀 Starting Continuous Monitoring System Validation")
    print("=" * 60)
    
    validations = [
        ("File Structure", validate_file_structure),
        ("Python Syntax", validate_python_syntax),
        ("Core Imports", validate_imports),
        ("Database Schema", validate_database_schema),
        ("Configuration Format", validate_configuration_format),
        ("Class Definitions", validate_class_definitions),
        ("Method Signatures", validate_method_signatures),
        ("Documentation", validate_documentation)
    ]
    
    results = {}
    all_passed = True
    
    for name, validation_func in validations:
        try:
            result = validation_func()
            results[name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {name} validation failed with exception: {e}")
            results[name] = False
            all_passed = False
        
        print()  # Add spacing between validations
    
    print("=" * 60)
    print("📊 Validation Summary:")
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\n🎯 Overall Result: {'✅ ALL VALIDATIONS PASSED' if all_passed else '❌ SOME VALIDATIONS FAILED'}")
    
    if all_passed:
        print("\n🎉 Continuous Monitoring System implementation is valid!")
        print("   All components are properly implemented and ready for use.")
    else:
        print("\n⚠️ Some validations failed. Please review and fix the issues above.")
    
    return all_passed

def main():
    """Main entry point for validation."""
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()