#!/usr/bin/env python3
"""
Ubuntu Compatibility Testing Integration

This script integrates the Ubuntu compatibility testing framework with the
existing codebase analysis tools and provides a unified interface for
comprehensive Ubuntu server deployment readiness assessment.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ubuntu_compatibility_tester import UbuntuCompatibilityTestFramework, TestResult

# Import existing analysis tools if available
try:
    from python_backend_analyzer import PythonBackendAnalyzer
    PYTHON_ANALYZER_AVAILABLE = True
except ImportError:
    PYTHON_ANALYZER_AVAILABLE = False
    logging.warning("Python backend analyzer not available")

try:
    from typescript_frontend_analyzer import TypeScriptFrontendAnalyzer
    TYPESCRIPT_ANALYZER_AVAILABLE = True
except ImportError:
    TYPESCRIPT_ANALYZER_AVAILABLE = False
    logging.warning("TypeScript frontend analyzer not available")

try:
    from docker_deployment_validator import DockerDeploymentValidator
    DOCKER_VALIDATOR_AVAILABLE = True
except ImportError:
    DOCKER_VALIDATOR_AVAILABLE = False
    logging.warning("Docker deployment validator not available")

class UbuntuCompatibilityIntegration:
    """Integration class for Ubuntu compatibility testing with existing analysis tools"""
    
    def __init__(self, ubuntu_version: str = "24.04"):
        self.ubuntu_version = ubuntu_version
        self.ubuntu_framework = UbuntuCompatibilityTestFramework(ubuntu_version)
        self.integration_results = {}
        
        # Initialize existing analyzers if available
        self.python_analyzer = PythonBackendAnalyzer() if PYTHON_ANALYZER_AVAILABLE else None
        self.typescript_analyzer = TypeScriptFrontendAnalyzer() if TYPESCRIPT_ANALYZER_AVAILABLE else None
        self.docker_validator = DockerDeploymentValidator() if DOCKER_VALIDATOR_AVAILABLE else None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def run_integrated_analysis(self) -> Dict[str, Any]:
        """Run integrated analysis combining Ubuntu compatibility with existing tools"""
        self.logger.info("Starting integrated Ubuntu compatibility analysis...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "ubuntu_version": self.ubuntu_version,
            "analysis_components": {
                "ubuntu_compatibility": True,
                "python_backend": PYTHON_ANALYZER_AVAILABLE,
                "typescript_frontend": TYPESCRIPT_ANALYZER_AVAILABLE,
                "docker_deployment": DOCKER_VALIDATOR_AVAILABLE
            },
            "results": {}
        }
        
        # Run Ubuntu compatibility tests
        self.logger.info("Running Ubuntu compatibility tests...")
        ubuntu_results = self.ubuntu_framework.run_all_tests()
        ubuntu_report = self.ubuntu_framework.generate_report()
        results["results"]["ubuntu_compatibility"] = ubuntu_report
        
        # Run Python backend analysis if available
        if self.python_analyzer:
            self.logger.info("Running Python backend analysis...")
            try:
                python_results = self.python_analyzer.analyze_codebase()
                results["results"]["python_backend"] = self._integrate_python_results(python_results, ubuntu_report)
            except Exception as e:
                self.logger.error(f"Python backend analysis failed: {e}")
                results["results"]["python_backend"] = {"error": str(e)}
        
        # Run TypeScript frontend analysis if available
        if self.typescript_analyzer:
            self.logger.info("Running TypeScript frontend analysis...")
            try:
                typescript_results = self.typescript_analyzer.analyze_codebase()
                results["results"]["typescript_frontend"] = self._integrate_typescript_results(typescript_results, ubuntu_report)
            except Exception as e:
                self.logger.error(f"TypeScript frontend analysis failed: {e}")
                results["results"]["typescript_frontend"] = {"error": str(e)}
        
        # Run Docker deployment validation if available
        if self.docker_validator:
            self.logger.info("Running Docker deployment validation...")
            try:
                docker_results = self.docker_validator.validate_deployment()
                results["results"]["docker_deployment"] = self._integrate_docker_results(docker_results, ubuntu_report)
            except Exception as e:
                self.logger.error(f"Docker deployment validation failed: {e}")
                results["results"]["docker_deployment"] = {"error": str(e)}
        
        # Generate integrated recommendations
        results["integrated_recommendations"] = self._generate_integrated_recommendations(results)
        results["deployment_readiness"] = self._assess_deployment_readiness(results)
        
        self.integration_results = results
        return results
    
    def _integrate_python_results(self, python_results: Dict[str, Any], ubuntu_report: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate Python analysis results with Ubuntu compatibility findings"""
        integration = {
            "python_analysis": python_results,
            "ubuntu_integration": {
                "python_dependency_compatibility": None,
                "ubuntu_specific_issues": [],
                "recommendations": []
            }
        }
        
        # Find Ubuntu-specific Python issues
        for test_result in ubuntu_report.get("test_results", []):
            if "python" in test_result.get("test_name", "").lower():
                if test_result.get("result") in ["FAIL", "WARNING"]:
                    integration["ubuntu_integration"]["ubuntu_specific_issues"].append({
                        "test": test_result["test_name"],
                        "status": test_result["result"],
                        "message": test_result["message"]
                    })
        
        # Cross-reference Python package issues
        if "dependencies" in python_results:
            python_packages = python_results["dependencies"].get("packages", [])
            ubuntu_python_test = next(
                (r for r in ubuntu_report.get("test_results", []) if r["test_name"] == "python_dependencies"),
                None
            )
            
            if ubuntu_python_test:
                integration["ubuntu_integration"]["python_dependency_compatibility"] = {
                    "status": ubuntu_python_test["result"],
                    "message": ubuntu_python_test["message"],
                    "total_packages_analyzed": len(python_packages)
                }
        
        # Generate integration-specific recommendations
        if integration["ubuntu_integration"]["ubuntu_specific_issues"]:
            integration["ubuntu_integration"]["recommendations"].append(
                "Review Python package compatibility with Ubuntu server environment"
            )
        
        return integration
    
    def _integrate_typescript_results(self, typescript_results: Dict[str, Any], ubuntu_report: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate TypeScript analysis results with Ubuntu compatibility findings"""
        integration = {
            "typescript_analysis": typescript_results,
            "ubuntu_integration": {
                "nodejs_dependency_compatibility": None,
                "ubuntu_specific_issues": [],
                "recommendations": []
            }
        }
        
        # Find Ubuntu-specific Node.js issues
        for test_result in ubuntu_report.get("test_results", []):
            if "nodejs" in test_result.get("test_name", "").lower():
                if test_result.get("result") in ["FAIL", "WARNING"]:
                    integration["ubuntu_integration"]["ubuntu_specific_issues"].append({
                        "test": test_result["test_name"],
                        "status": test_result["result"],
                        "message": test_result["message"]
                    })
        
        # Cross-reference Node.js package issues
        ubuntu_nodejs_test = next(
            (r for r in ubuntu_report.get("test_results", []) if r["test_name"] == "nodejs_dependencies"),
            None
        )
        
        if ubuntu_nodejs_test:
            integration["ubuntu_integration"]["nodejs_dependency_compatibility"] = {
                "status": ubuntu_nodejs_test["result"],
                "message": ubuntu_nodejs_test["message"]
            }
        
        # Generate integration-specific recommendations
        if integration["ubuntu_integration"]["ubuntu_specific_issues"]:
            integration["ubuntu_integration"]["recommendations"].append(
                "Review Node.js package compatibility with Ubuntu server environment"
            )
        
        return integration
    
    def _integrate_docker_results(self, docker_results: Dict[str, Any], ubuntu_report: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate Docker validation results with Ubuntu compatibility findings"""
        integration = {
            "docker_analysis": docker_results,
            "ubuntu_integration": {
                "docker_ubuntu_compatibility": None,
                "container_networking_compatibility": None,
                "ubuntu_specific_issues": [],
                "recommendations": []
            }
        }
        
        # Find Ubuntu-specific Docker issues
        docker_tests = ["docker_build_ubuntu", "container_networking_ubuntu"]
        for test_name in docker_tests:
            test_result = next(
                (r for r in ubuntu_report.get("test_results", []) if r["test_name"] == test_name),
                None
            )
            
            if test_result:
                if test_name == "docker_build_ubuntu":
                    integration["ubuntu_integration"]["docker_ubuntu_compatibility"] = {
                        "status": test_result["result"],
                        "message": test_result["message"],
                        "details": test_result.get("details", {})
                    }
                elif test_name == "container_networking_ubuntu":
                    integration["ubuntu_integration"]["container_networking_compatibility"] = {
                        "status": test_result["result"],
                        "message": test_result["message"],
                        "details": test_result.get("details", {})
                    }
                
                if test_result.get("result") in ["FAIL", "WARNING"]:
                    integration["ubuntu_integration"]["ubuntu_specific_issues"].append({
                        "test": test_result["test_name"],
                        "status": test_result["result"],
                        "message": test_result["message"]
                    })
        
        # Generate integration-specific recommendations
        if integration["ubuntu_integration"]["ubuntu_specific_issues"]:
            integration["ubuntu_integration"]["recommendations"].append(
                "Update Docker configurations for optimal Ubuntu server compatibility"
            )
        
        return integration
    
    def _generate_integrated_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate integrated recommendations based on all analysis results"""
        recommendations = []
        
        # Ubuntu compatibility recommendations
        ubuntu_results = results["results"].get("ubuntu_compatibility", {})
        ubuntu_recommendations = ubuntu_results.get("recommendations", [])
        recommendations.extend(ubuntu_recommendations)
        
        # Cross-component recommendations
        failed_components = []
        warning_components = []
        
        for component, component_results in results["results"].items():
            if isinstance(component_results, dict):
                if component == "ubuntu_compatibility":
                    summary = component_results.get("test_summary", {})
                    if summary.get("failed", 0) > 0:
                        failed_components.append(component)
                    elif summary.get("warnings", 0) > 0:
                        warning_components.append(component)
                else:
                    # Check for errors in other components
                    if "error" in component_results:
                        failed_components.append(component)
        
        # Generate cross-component recommendations
        if len(failed_components) > 1:
            recommendations.append(
                f"Multiple components have critical issues: {', '.join(failed_components)}. "
                "Prioritize fixing Ubuntu compatibility issues first."
            )
        
        if "python_backend" in results["results"] and "ubuntu_compatibility" in results["results"]:
            python_integration = results["results"]["python_backend"].get("ubuntu_integration", {})
            if python_integration.get("ubuntu_specific_issues"):
                recommendations.append(
                    "Python backend has Ubuntu-specific compatibility issues that need attention"
                )
        
        if "docker_deployment" in results["results"] and "ubuntu_compatibility" in results["results"]:
            docker_integration = results["results"]["docker_deployment"].get("ubuntu_integration", {})
            if docker_integration.get("ubuntu_specific_issues"):
                recommendations.append(
                    "Docker deployment configuration needs updates for Ubuntu server compatibility"
                )
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _assess_deployment_readiness(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall deployment readiness for Ubuntu servers"""
        readiness = {
            "overall_status": "UNKNOWN",
            "readiness_score": 0,
            "critical_blockers": [],
            "warnings": [],
            "ready_components": [],
            "assessment": ""
        }
        
        # Analyze Ubuntu compatibility results
        ubuntu_results = results["results"].get("ubuntu_compatibility", {})
        if ubuntu_results:
            summary = ubuntu_results.get("test_summary", {})
            failed_tests = summary.get("failed", 0)
            warning_tests = summary.get("warnings", 0)
            passed_tests = summary.get("passed", 0)
            total_tests = summary.get("total_tests", 1)
            
            # Calculate base readiness score from Ubuntu compatibility
            ubuntu_score = (passed_tests + warning_tests * 0.5) / total_tests * 100
            readiness["readiness_score"] = ubuntu_score
            
            # Identify critical blockers
            for test_result in ubuntu_results.get("test_results", []):
                if test_result.get("result") == "FAIL":
                    readiness["critical_blockers"].append(
                        f"Ubuntu compatibility: {test_result['test_name']} - {test_result['message']}"
                    )
                elif test_result.get("result") == "WARNING":
                    readiness["warnings"].append(
                        f"Ubuntu compatibility: {test_result['test_name']} - {test_result['message']}"
                    )
        
        # Factor in other component results
        component_scores = []
        for component, component_results in results["results"].items():
            if component != "ubuntu_compatibility" and isinstance(component_results, dict):
                if "error" not in component_results:
                    readiness["ready_components"].append(component)
                    component_scores.append(75)  # Assume good if no errors
                else:
                    readiness["critical_blockers"].append(
                        f"{component}: Analysis failed - {component_results['error']}"
                    )
                    component_scores.append(0)
        
        # Adjust readiness score based on all components
        if component_scores:
            avg_component_score = sum(component_scores) / len(component_scores)
            readiness["readiness_score"] = (readiness["readiness_score"] + avg_component_score) / 2
        
        # Determine overall status
        if len(readiness["critical_blockers"]) == 0:
            if len(readiness["warnings"]) == 0:
                readiness["overall_status"] = "READY"
                readiness["assessment"] = "Application is ready for Ubuntu server deployment"
            elif len(readiness["warnings"]) <= 2:
                readiness["overall_status"] = "READY_WITH_WARNINGS"
                readiness["assessment"] = "Application is ready for deployment with minor issues to monitor"
            else:
                readiness["overall_status"] = "NEEDS_ATTENTION"
                readiness["assessment"] = "Application has several warnings that should be addressed"
        elif len(readiness["critical_blockers"]) <= 2:
            readiness["overall_status"] = "NEEDS_FIXES"
            readiness["assessment"] = "Application has critical issues that must be fixed before deployment"
        else:
            readiness["overall_status"] = "NOT_READY"
            readiness["assessment"] = "Application has multiple critical issues and is not ready for deployment"
        
        return readiness
    
    def save_integrated_report(self, output_file: str):
        """Save integrated analysis report to file"""
        if not self.integration_results:
            raise ValueError("No integration results available. Run run_integrated_analysis() first.")
        
        with open(output_file, 'w') as f:
            json.dump(self.integration_results, f, indent=2)
        
        self.logger.info(f"Integrated report saved to: {output_file}")
    
    def print_summary(self):
        """Print a summary of the integrated analysis results"""
        if not self.integration_results:
            print("No integration results available. Run analysis first.")
            return
        
        readiness = self.integration_results.get("deployment_readiness", {})
        
        print("\n" + "="*70)
        print("UBUNTU DEPLOYMENT READINESS ASSESSMENT")
        print("="*70)
        print(f"Ubuntu Version: {self.ubuntu_version}")
        print(f"Overall Status: {readiness.get('overall_status', 'UNKNOWN')}")
        print(f"Readiness Score: {readiness.get('readiness_score', 0):.1f}%")
        print(f"Assessment: {readiness.get('assessment', 'No assessment available')}")
        
        if readiness.get("critical_blockers"):
            print(f"\nCritical Blockers ({len(readiness['critical_blockers'])}):")
            for blocker in readiness["critical_blockers"][:5]:  # Show first 5
                print(f"  ❌ {blocker}")
        
        if readiness.get("warnings"):
            print(f"\nWarnings ({len(readiness['warnings'])}):")
            for warning in readiness["warnings"][:3]:  # Show first 3
                print(f"  ⚠️  {warning}")
        
        if readiness.get("ready_components"):
            print(f"\nReady Components: {', '.join(readiness['ready_components'])}")
        
        recommendations = self.integration_results.get("integrated_recommendations", [])
        if recommendations:
            print(f"\nTop Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec}")
        
        print("="*70)

def main():
    """Main function for integrated Ubuntu compatibility testing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Integrated Ubuntu compatibility testing with existing analysis tools"
    )
    parser.add_argument(
        "--ubuntu-version", 
        default="24.04", 
        help="Ubuntu version to test against"
    )
    parser.add_argument(
        "--output", "-o", 
        help="Output file for integrated report (JSON)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run integrated analysis
    integration = UbuntuCompatibilityIntegration(args.ubuntu_version)
    results = integration.run_integrated_analysis()
    
    # Save report if requested
    if args.output:
        integration.save_integrated_report(args.output)
    
    # Print summary
    integration.print_summary()
    
    # Exit with appropriate code based on readiness
    readiness = results.get("deployment_readiness", {})
    status = readiness.get("overall_status", "UNKNOWN")
    
    if status in ["READY", "READY_WITH_WARNINGS"]:
        return 0
    elif status == "NEEDS_ATTENTION":
        return 1
    else:
        return 2

if __name__ == "__main__":
    sys.exit(main())