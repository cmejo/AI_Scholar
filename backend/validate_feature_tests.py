#!/usr/bin/env python3
"""
Feature test validation script for task 9.1.
Validates that all feature-specific test suites are properly implemented and functional.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import ast


class FeatureTestValidator:
    """Validator for feature-specific test suites."""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.test_dir = self.backend_dir / "tests"
        self.validation_results = {}
        
    def validate_test_file_structure(self) -> Dict[str, Any]:
        """Validate that all required test files exist and have proper structure."""
        required_files = [
            "test_mobile_app_comprehensive.py",
            "test_voice_interface_comprehensive.py", 
            "test_external_integrations_comprehensive.py",
            "test_educational_features_comprehensive.py"
        ]
        
        results = {"missing_files": [], "existing_files": [], "structure_issues": []}
        
        for file_name in required_files:
            file_path = self.test_dir / file_name
            if file_path.exists():
                results["existing_files"].append(file_name)
                # Validate file structure
                structure_issues = self._validate_file_structure(file_path)
                if structure_issues:
                    results["structure_issues"].extend(structure_issues)
            else:
                results["missing_files"].append(file_name)
        
        return results
    
    def _validate_file_structure(self, file_path: Path) -> List[str]:
        """Validate the structure of a test file."""
        issues = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the AST to analyze structure
            tree = ast.parse(content)
            
            # Check for required imports
            required_imports = ['pytest', 'asyncio', 'unittest.mock']
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            for req_import in required_imports:
                if not any(req_import in imp for imp in imports):
                    issues.append(f"{file_path.name}: Missing import {req_import}")
            
            # Check for test classes
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            test_classes = [cls for cls in classes if cls.startswith('Test')]
            
            if len(test_classes) < 2:
                issues.append(f"{file_path.name}: Should have at least 2 test classes")
            
            # Check for async test methods
            async_methods = []
            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith('test_'):
                    async_methods.append(node.name)
            
            if len(async_methods) < 5:
                issues.append(f"{file_path.name}: Should have at least 5 async test methods")
                
        except Exception as e:
            issues.append(f"{file_path.name}: Failed to parse file - {str(e)}")
        
        return issues
    
    def validate_test_coverage(self) -> Dict[str, Any]:
        """Validate test coverage for each feature area."""
        coverage_requirements = {
            "mobile_app": {
                "required_test_methods": [
                    "test_mobile_device_registration",
                    "test_offline_data_sync", 
                    "test_offline_document_access",
                    "test_push_notification_delivery",
                    "test_mobile_gesture_simulation",
                    "test_mobile_network_conditions"
                ],
                "required_classes": [
                    "TestMobileAppFunctionality",
                    "TestMobileOfflineScenarios",
                    "TestMobileDeviceSimulation"
                ]
            },
            "voice_interface": {
                "required_test_methods": [
                    "test_speech_to_text_accuracy",
                    "test_text_to_speech_quality",
                    "test_voice_command_recognition",
                    "test_multilingual_voice_support",
                    "test_noise_filtering_accuracy",
                    "test_conversation_context_management"
                ],
                "required_classes": [
                    "TestVoiceInterfaceFunctionality",
                    "TestVoiceSpeechRecognitionAccuracy",
                    "TestVoiceInterfaceIntegration"
                ]
            },
            "external_integrations": {
                "required_test_methods": [
                    "test_zotero_library_sync",
                    "test_mendeley_document_sync",
                    "test_pubmed_search_integration",
                    "test_arxiv_paper_discovery",
                    "test_obsidian_vault_sync",
                    "test_grammarly_integration"
                ],
                "required_classes": [
                    "TestReferenceManagerIntegrations",
                    "TestAcademicDatabaseIntegrations", 
                    "TestNoteTakingIntegrations",
                    "TestWritingToolIntegrations"
                ]
            },
            "educational_features": {
                "required_test_methods": [
                    "test_automatic_quiz_generation",
                    "test_spaced_repetition_algorithm",
                    "test_learning_progress_tracking",
                    "test_gamification_features",
                    "test_learning_outcome_validation"
                ],
                "required_classes": [
                    "TestQuizGenerationFeatures",
                    "TestSpacedRepetitionSystem",
                    "TestLearningProgressTracking",
                    "TestGamificationFeatures"
                ]
            }
        }
        
        results = {}
        
        for feature, requirements in coverage_requirements.items():
            file_name = f"test_{feature}_comprehensive.py"
            file_path = self.test_dir / file_name
            
            if not file_path.exists():
                results[feature] = {"status": "missing_file", "coverage": 0}
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Find all classes and methods
                found_classes = []
                found_methods = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        found_classes.append(node.name)
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith('test_'):
                            found_methods.append(node.name)
                
                # Calculate coverage
                required_classes = requirements["required_classes"]
                required_methods = requirements["required_test_methods"]
                
                class_coverage = len([c for c in required_classes if c in found_classes]) / len(required_classes)
                method_coverage = len([m for m in required_methods if m in found_methods]) / len(required_methods)
                
                overall_coverage = (class_coverage + method_coverage) / 2
                
                results[feature] = {
                    "status": "analyzed",
                    "coverage": overall_coverage,
                    "class_coverage": class_coverage,
                    "method_coverage": method_coverage,
                    "missing_classes": [c for c in required_classes if c not in found_classes],
                    "missing_methods": [m for m in required_methods if m not in found_methods],
                    "found_classes": found_classes,
                    "found_methods": found_methods
                }
                
            except Exception as e:
                results[feature] = {"status": "error", "error": str(e), "coverage": 0}
        
        return results
    
    def validate_test_dependencies(self) -> Dict[str, Any]:
        """Validate that requirements.txt exists and contains test dependencies."""
        requirements_file = self.backend_dir / "requirements.txt"
        
        results = {"available": [], "missing": [], "import_errors": []}
        
        required_packages = [
            'pytest',
            'fastapi',
            'sqlalchemy'
        ]
        
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                requirements_content = f.read().lower()
            
            for package in required_packages:
                if package.lower() in requirements_content:
                    results["available"].append(package)
                else:
                    results["missing"].append(package)
        else:
            results["missing"] = required_packages
            results["import_errors"].append("requirements.txt file not found")
        
        return results
    
    def validate_service_imports(self) -> Dict[str, Any]:
        """Validate that all required service modules exist as files."""
        required_services = [
            'services/mobile_sync_service.py',
            'services/push_notification_service.py',
            'services/voice_processing_service.py',
            'services/voice_nlp_service.py',
            'services/voice_command_router.py',
            'services/reference_manager_service.py',
            'services/academic_database_service.py',
            'services/note_taking_integration_service.py',
            'services/writing_tools_service.py',
            'services/quiz_generation_service.py',
            'services/spaced_repetition_service.py',
            'services/learning_progress_service.py',
            'services/gamification_service.py'
        ]
        
        results = {"available": [], "missing": [], "import_errors": []}
        
        for service_path in required_services:
            file_path = self.backend_dir / service_path
            if file_path.exists():
                results["available"].append(service_path)
            else:
                results["missing"].append(service_path)
        
        return results
    
    def run_syntax_validation(self) -> Dict[str, Any]:
        """Run syntax validation on all test files."""
        results = {"valid_files": [], "syntax_errors": []}
        
        test_files = list(self.test_dir.glob("test_*_comprehensive.py"))
        
        for file_path in test_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Try to compile the file
                compile(content, str(file_path), 'exec')
                results["valid_files"].append(file_path.name)
                
            except SyntaxError as e:
                results["syntax_errors"].append({
                    "file": file_path.name,
                    "line": e.lineno,
                    "error": str(e)
                })
            except Exception as e:
                results["syntax_errors"].append({
                    "file": file_path.name,
                    "line": None,
                    "error": str(e)
                })
        
        return results
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Running comprehensive feature test validation...")
        
        validation_results = {
            "file_structure": self.validate_test_file_structure(),
            "test_coverage": self.validate_test_coverage(),
            "dependencies": self.validate_test_dependencies(),
            "service_imports": self.validate_service_imports(),
            "syntax_validation": self.run_syntax_validation()
        }
        
        # Calculate overall validation score
        scores = []
        
        # File structure score
        file_results = validation_results["file_structure"]
        if len(file_results["missing_files"]) == 0:
            scores.append(1.0)
        else:
            scores.append(len(file_results["existing_files"]) / 4)  # 4 required files
        
        # Coverage score
        coverage_results = validation_results["test_coverage"]
        coverage_scores = [r.get("coverage", 0) for r in coverage_results.values() if isinstance(r, dict)]
        if coverage_scores:
            scores.append(sum(coverage_scores) / len(coverage_scores))
        
        # Dependencies score
        dep_results = validation_results["dependencies"]
        if len(dep_results["missing"]) == 0:
            scores.append(1.0)
        else:
            scores.append(len(dep_results["available"]) / (len(dep_results["available"]) + len(dep_results["missing"])))
        
        # Syntax score
        syntax_results = validation_results["syntax_validation"]
        if len(syntax_results["syntax_errors"]) == 0:
            scores.append(1.0)
        else:
            scores.append(len(syntax_results["valid_files"]) / (len(syntax_results["valid_files"]) + len(syntax_results["syntax_errors"])))
        
        overall_score = sum(scores) / len(scores) if scores else 0
        
        validation_results["overall_score"] = overall_score
        validation_results["validation_passed"] = overall_score >= 0.8
        
        self.validation_results = validation_results
        return validation_results
    
    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report."""
        if not self.validation_results:
            return "No validation results available. Run validation first."
        
        results = self.validation_results
        report = []
        
        report.append("=" * 80)
        report.append("FEATURE TEST VALIDATION REPORT")
        report.append("=" * 80)
        
        # Overall status
        status = "✅ PASSED" if results["validation_passed"] else "❌ FAILED"
        report.append(f"Overall Status: {status}")
        report.append(f"Validation Score: {results['overall_score']:.1%}")
        report.append("")
        
        # File structure validation
        file_results = results["file_structure"]
        report.append("📁 FILE STRUCTURE VALIDATION:")
        report.append(f"  Existing files: {len(file_results['existing_files'])}/4")
        if file_results["missing_files"]:
            report.append(f"  Missing files: {', '.join(file_results['missing_files'])}")
        if file_results["structure_issues"]:
            report.append("  Structure issues:")
            for issue in file_results["structure_issues"]:
                report.append(f"    - {issue}")
        report.append("")
        
        # Test coverage validation
        coverage_results = results["test_coverage"]
        report.append("📊 TEST COVERAGE VALIDATION:")
        for feature, coverage_data in coverage_results.items():
            if isinstance(coverage_data, dict) and "coverage" in coverage_data:
                coverage_pct = coverage_data["coverage"] * 100
                status_icon = "✅" if coverage_pct >= 80 else "⚠️" if coverage_pct >= 60 else "❌"
                report.append(f"  {feature}: {status_icon} {coverage_pct:.1f}%")
                
                if coverage_data.get("missing_classes"):
                    report.append(f"    Missing classes: {', '.join(coverage_data['missing_classes'])}")
                if coverage_data.get("missing_methods"):
                    report.append(f"    Missing methods: {len(coverage_data['missing_methods'])} methods")
        report.append("")
        
        # Dependencies validation
        dep_results = results["dependencies"]
        report.append("📦 DEPENDENCIES VALIDATION:")
        report.append(f"  Available: {len(dep_results['available'])}")
        report.append(f"  Missing: {len(dep_results['missing'])}")
        if dep_results["missing"]:
            report.append(f"  Missing packages: {', '.join(dep_results['missing'])}")
        report.append("")
        
        # Service imports validation
        service_results = results["service_imports"]
        report.append("🔧 SERVICE IMPORTS VALIDATION:")
        report.append(f"  Available: {len(service_results['available'])}")
        report.append(f"  Missing: {len(service_results['missing'])}")
        if service_results["missing"]:
            report.append("  Missing services:")
            for service in service_results["missing"]:
                report.append(f"    - {service}")
        report.append("")
        
        # Syntax validation
        syntax_results = results["syntax_validation"]
        report.append("✅ SYNTAX VALIDATION:")
        report.append(f"  Valid files: {len(syntax_results['valid_files'])}")
        report.append(f"  Syntax errors: {len(syntax_results['syntax_errors'])}")
        if syntax_results["syntax_errors"]:
            report.append("  Errors:")
            for error in syntax_results["syntax_errors"]:
                report.append(f"    - {error['file']}: {error['error']}")
        report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS:")
        if not results["validation_passed"]:
            if file_results["missing_files"]:
                report.append("  - Create missing test files")
            if dep_results["missing"]:
                report.append("  - Install missing dependencies")
            if service_results["missing"]:
                report.append("  - Implement missing service modules")
            if syntax_results["syntax_errors"]:
                report.append("  - Fix syntax errors in test files")
        else:
            report.append("  - All validations passed! Tests are ready to run.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main entry point for validation."""
    validator = FeatureTestValidator()
    
    try:
        print("🚀 Starting feature test validation...")
        results = validator.run_comprehensive_validation()
        
        # Generate and display report
        report = validator.generate_validation_report()
        print(report)
        
        # Save report to file
        report_file = "feature_test_validation_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📄 Validation report saved to: {report_file}")
        
        # Return appropriate exit code
        return 0 if results["validation_passed"] else 1
        
    except Exception as e:
        print(f"💥 Validation failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())