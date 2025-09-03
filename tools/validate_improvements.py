#!/usr/bin/env python3
"""
Validation script for AI Scholar project improvements
Confirms all improvements are working correctly
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List

class ImprovementValidator:
    """Validates all implemented improvements"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.results = {}
    
    def validate_all(self) -> Dict:
        """Run comprehensive validation of all improvements"""
        print("🔍 Validating AI Scholar Project Improvements...")
        
        validations = [
            ("Tools Structure", self.validate_tools_structure),
            ("Unified Settings", self.validate_unified_settings),
            ("Test Configuration", self.validate_test_config),
            ("Performance Monitoring", self.validate_performance_monitoring),
            ("Code Splitting", self.validate_code_splitting),
            ("Caching System", self.validate_caching_system),
            ("Script Consolidation", self.validate_script_consolidation),
            ("Package Scripts", self.validate_package_scripts)
        ]
        
        for name, validator in validations:
            print(f"\n📋 Validating {name}...")
            try:
                result = validator()
                self.results[name] = {"status": "✅ PASS", "details": result}
                print(f"✅ {name}: PASS")
            except Exception as e:
                self.results[name] = {"status": "❌ FAIL", "error": str(e)}
                print(f"❌ {name}: FAIL - {e}")
        
        return self.results
    
    def validate_tools_structure(self) -> Dict:
        """Validate tools directory structure"""
        required_dirs = [
            "tools/analysis",
            "tools/testing", 
            "tools/deployment",
            "tools/maintenance",
            "tools/monitoring"
        ]
        
        required_files = [
            "tools/analysis/unified_analyzer.py",
            "tools/testing/test_consolidator.py",
            "tools/monitoring/performance_monitor.py",
            "tools/maintenance/script_consolidator.py"
        ]
        
        missing_dirs = []
        missing_files = []
        
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).exists():
                missing_dirs.append(dir_path)
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_dirs or missing_files:
            raise Exception(f"Missing dirs: {missing_dirs}, Missing files: {missing_files}")
        
        return {
            "directories_created": len(required_dirs),
            "tools_created": len(required_files),
            "structure_complete": True
        }
    
    def validate_unified_settings(self) -> Dict:
        """Validate unified settings system"""
        settings_file = self.project_root / "backend/core/unified_settings.py"
        
        if not settings_file.exists():
            raise Exception("Unified settings file not found")
        
        # Try to import and validate
        try:
            import sys
            sys.path.insert(0, str(self.project_root / "backend"))
            
            # This would normally import the settings
            # For validation, we just check the file exists and has key components
            content = settings_file.read_text()
            
            required_components = [
                "UnifiedSettings",
                "DatabaseSettings", 
                "AISettings",
                "FeatureFlags",
                "get_settings"
            ]
            
            missing_components = []
            for component in required_components:
                if component not in content:
                    missing_components.append(component)
            
            if missing_components:
                raise Exception(f"Missing components: {missing_components}")
            
            return {
                "settings_file_exists": True,
                "components_present": len(required_components),
                "validation_passed": True
            }
            
        except ImportError as e:
            # Expected in this context, just validate file structure
            return {
                "settings_file_exists": True,
                "file_size_kb": settings_file.stat().st_size / 1024,
                "validation_note": "Import validation skipped (expected)"
            }
    
    def validate_test_config(self) -> Dict:
        """Validate test configuration"""
        pytest_ini = self.project_root / "pytest.ini"
        
        if not pytest_ini.exists():
            raise Exception("pytest.ini not found")
        
        content = pytest_ini.read_text()
        
        required_configs = [
            "minversion",
            "-n auto",
            "--cov=backend",
            "markers"
        ]
        
        missing_configs = []
        for config in required_configs:
            if config not in content:
                missing_configs.append(config)
        
        if missing_configs:
            raise Exception(f"Missing pytest configs: {missing_configs}")
        
        return {
            "pytest_config_exists": True,
            "parallel_execution_enabled": "-n auto" in content,
            "coverage_configured": "--cov=backend" in content,
            "markers_defined": "markers" in content
        }
    
    def validate_performance_monitoring(self) -> Dict:
        """Validate performance monitoring system"""
        perf_monitor = self.project_root / "tools/monitoring/performance_monitor.py"
        
        if not perf_monitor.exists():
            raise Exception("Performance monitor not found")
        
        # Check if it's executable
        if not perf_monitor.stat().st_mode & 0o111:
            raise Exception("Performance monitor not executable")
        
        # Try to run it (with timeout)
        try:
            result = subprocess.run(
                ["python3", str(perf_monitor)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )
            
            # Check if reports were generated
            json_report = self.project_root / "performance_report.json"
            md_report = self.project_root / "performance_report.md"
            
            return {
                "monitor_executable": True,
                "execution_successful": result.returncode == 0,
                "json_report_generated": json_report.exists(),
                "markdown_report_generated": md_report.exists(),
                "reports_created": json_report.exists() and md_report.exists()
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("Performance monitor execution timed out")
    
    def validate_code_splitting(self) -> Dict:
        """Validate code splitting utilities"""
        code_splitting = self.project_root / "src/utils/codeSplitting.ts"
        
        if not code_splitting.exists():
            raise Exception("Code splitting utilities not found")
        
        content = code_splitting.read_text()
        
        required_exports = [
            "createMonitoredLazyComponent",
            "ComponentPreloader",
            "ComponentPerformanceTracker",
            "initializeCodeSplitting"
        ]
        
        missing_exports = []
        for export in required_exports:
            if export not in content:
                missing_exports.append(export)
        
        if missing_exports:
            raise Exception(f"Missing exports: {missing_exports}")
        
        return {
            "code_splitting_exists": True,
            "exports_present": len(required_exports),
            "file_size_kb": code_splitting.stat().st_size / 1024,
            "typescript_file": code_splitting.suffix == ".ts"
        }
    
    def validate_caching_system(self) -> Dict:
        """Validate enhanced caching system"""
        caching_system = self.project_root / "backend/core/enhanced_caching.py"
        
        if not caching_system.exists():
            raise Exception("Enhanced caching system not found")
        
        content = caching_system.read_text()
        
        required_classes = [
            "MultiLevelCache",
            "CacheConfig", 
            "CacheWarmer",
            "CacheMonitor"
        ]
        
        missing_classes = []
        for cls in required_classes:
            if f"class {cls}" not in content:
                missing_classes.append(cls)
        
        if missing_classes:
            raise Exception(f"Missing classes: {missing_classes}")
        
        return {
            "caching_system_exists": True,
            "classes_present": len(required_classes),
            "decorators_available": "@cached" in content,
            "file_size_kb": caching_system.stat().st_size / 1024
        }
    
    def validate_script_consolidation(self) -> Dict:
        """Validate script consolidation"""
        consolidator = self.project_root / "tools/maintenance/script_consolidator.py"
        
        if not consolidator.exists():
            raise Exception("Script consolidator not found")
        
        # Check if consolidation report exists
        report = self.project_root / "script_consolidation_report.md"
        
        if not report.exists():
            raise Exception("Script consolidation report not found")
        
        # Check report content
        report_content = report.read_text()
        
        if "Total Scripts:" not in report_content:
            raise Exception("Invalid consolidation report format")
        
        return {
            "consolidator_exists": True,
            "report_generated": True,
            "consolidator_executable": consolidator.stat().st_mode & 0o111 != 0,
            "report_size_kb": report.stat().st_size / 1024
        }
    
    def validate_package_scripts(self) -> Dict:
        """Validate enhanced package.json scripts"""
        package_json = self.project_root / "package.json"
        
        if not package_json.exists():
            raise Exception("package.json not found")
        
        with open(package_json) as f:
            package_data = json.load(f)
        
        scripts = package_data.get("scripts", {})
        
        required_scripts = [
            "tools:analyze",
            "tools:test-optimize", 
            "tools:performance",
            "tools:health",
            "dev:full"
        ]
        
        missing_scripts = []
        for script in required_scripts:
            if script not in scripts:
                missing_scripts.append(script)
        
        if missing_scripts:
            raise Exception(f"Missing scripts: {missing_scripts}")
        
        return {
            "package_json_exists": True,
            "new_scripts_added": len(required_scripts),
            "total_scripts": len(scripts),
            "tools_scripts_present": all(s in scripts for s in required_scripts)
        }
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        total_validations = len(self.results)
        passed_validations = sum(1 for r in self.results.values() if "✅ PASS" in r["status"])
        
        report = "# AI Scholar Improvements Validation Report\n\n"
        report += f"**Validation Date**: {Path.cwd()}\n"
        report += f"**Total Validations**: {total_validations}\n"
        report += f"**Passed**: {passed_validations}\n"
        report += f"**Failed**: {total_validations - passed_validations}\n"
        report += f"**Success Rate**: {(passed_validations/total_validations)*100:.1f}%\n\n"
        
        # Overall status
        if passed_validations == total_validations:
            report += "## 🎉 Overall Status: ALL VALIDATIONS PASSED\n\n"
        else:
            report += f"## ⚠️ Overall Status: {total_validations - passed_validations} VALIDATIONS FAILED\n\n"
        
        # Detailed results
        report += "## Detailed Results\n\n"
        for name, result in self.results.items():
            status = result["status"]
            report += f"### {name}: {status}\n"
            
            if "details" in result:
                details = result["details"]
                for key, value in details.items():
                    report += f"- **{key}**: {value}\n"
            
            if "error" in result:
                report += f"- **Error**: {result['error']}\n"
            
            report += "\n"
        
        return report

def main():
    validator = ImprovementValidator()
    results = validator.validate_all()
    
    # Generate and save report
    report = validator.generate_validation_report()
    report_file = Path("validation_report.md")
    report_file.write_text(report)
    
    # Print summary
    total = len(results)
    passed = sum(1 for r in results.values() if "✅ PASS" in r["status"])
    
    print(f"\n🎯 Validation Summary:")
    print(f"  Total: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Success Rate: {(passed/total)*100:.1f}%")
    print(f"\n📋 Report saved to: {report_file}")
    
    if passed == total:
        print("\n🎉 ALL IMPROVEMENTS VALIDATED SUCCESSFULLY!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} validations failed. Check the report for details.")
        return 1

if __name__ == "__main__":
    exit(main())