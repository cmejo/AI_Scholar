#!/usr/bin/env python3
"""
Code Quality Analysis Integration

This module integrates the code quality analyzer with the broader codebase review system,
providing unified reporting and coordination with other analysis tools.

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code_quality_analyzer import CodeQualityAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeQualityIntegration:
    """Integration layer for code quality analysis within the broader review system"""
    
    def __init__(self, root_directory: str = "."):
        self.root_directory = os.path.abspath(root_directory)
        self.analyzer = CodeQualityAnalyzer()
        self.results_cache = {}
    
    def run_integrated_analysis(self) -> Dict[str, Any]:
        """Run code quality analysis integrated with the broader review system"""
        logger.info("Starting integrated code quality analysis...")
        
        try:
            # Run core analysis
            results = self.analyzer.analyze_codebase(self.root_directory)
            
            # Enhance results with integration-specific data
            enhanced_results = self._enhance_results(results)
            
            # Cache results for potential reuse
            self.results_cache = enhanced_results
            
            logger.info("Integrated code quality analysis completed successfully")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error during integrated analysis: {e}")
            raise
    
    def _enhance_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance analysis results with integration-specific information"""
        enhanced = results.copy()
        
        # Add integration metadata
        enhanced["integration_info"] = {
            "analyzer_version": "1.0.0",
            "integration_timestamp": datetime.now().isoformat(),
            "root_directory": self.root_directory,
            "analysis_scope": self._determine_analysis_scope()
        }
        
        # Add priority scoring for issues
        enhanced["prioritized_issues"] = self._prioritize_issues(results)
        
        # Add fix suggestions
        enhanced["fix_suggestions"] = self._generate_fix_suggestions(results)
        
        # Add compatibility notes
        enhanced["ubuntu_compatibility_notes"] = self._add_ubuntu_compatibility_notes(results)
        
        return enhanced
    
    def _determine_analysis_scope(self) -> Dict[str, Any]:
        """Determine the scope of analysis based on project structure"""
        scope = {
            "has_backend": os.path.exists(os.path.join(self.root_directory, "backend")),
            "has_frontend": os.path.exists(os.path.join(self.root_directory, "frontend")),
            "has_docker": os.path.exists(os.path.join(self.root_directory, "docker-compose.yml")),
            "has_tests": any(
                os.path.exists(os.path.join(self.root_directory, test_dir))
                for test_dir in ["tests", "test", "backend/tests"]
            ),
            "python_files_count": self._count_files_by_extension(".py"),
            "typescript_files_count": self._count_files_by_extension(".ts") + self._count_files_by_extension(".tsx"),
            "javascript_files_count": self._count_files_by_extension(".js") + self._count_files_by_extension(".jsx")
        }
        
        return scope
    
    def _count_files_by_extension(self, extension: str) -> int:
        """Count files with a specific extension"""
        count = 0
        for root, dirs, files in os.walk(self.root_directory):
            # Skip common directories that shouldn't be analyzed
            dirs[:] = [d for d in dirs if d not in ['node_modules', 'venv', '__pycache__', '.git']]
            count += sum(1 for file in files if file.endswith(extension))
        return count
    
    def _prioritize_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize all issues across different categories"""
        all_issues = []
        
        # Process code structure issues
        for issue in results.get("code_structure_issues", []):
            priority_score = self._calculate_priority_score(issue, "structure")
            all_issues.append({
                **issue,
                "priority_score": priority_score,
                "category": "code_structure"
            })
        
        # Process error handling issues
        for issue in results.get("error_handling_issues", []):
            priority_score = self._calculate_priority_score(issue, "error_handling")
            all_issues.append({
                **issue,
                "priority_score": priority_score,
                "category": "error_handling"
            })
        
        # Process dependency issues (convert to common format)
        for issue in results.get("dependency_issues", []):
            priority_score = self._calculate_dependency_priority_score(issue)
            all_issues.append({
                "type": issue["issue_type"],
                "severity": self._map_dependency_severity(issue["issue_type"]),
                "file_path": issue["file_path"],
                "description": f"Package {issue['package_name']} {issue['issue_type']}",
                "recommendation": issue["recommendation"],
                "priority_score": priority_score,
                "category": "dependency",
                "package_name": issue["package_name"],
                "current_version": issue["current_version"]
            })
        
        # Process documentation gaps (convert to common format)
        for gap in results.get("documentation_gaps", []):
            priority_score = self._calculate_documentation_priority_score(gap)
            all_issues.append({
                "type": gap["gap_type"],
                "severity": "low",  # Documentation gaps are typically low severity
                "file_path": gap["file_path"],
                "description": gap["description"],
                "recommendation": gap["recommendation"],
                "priority_score": priority_score,
                "category": "documentation",
                "function_name": gap.get("function_name"),
                "class_name": gap.get("class_name")
            })
        
        # Sort by priority score (highest first)
        all_issues.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return all_issues
    
    def _calculate_priority_score(self, issue: Dict[str, Any], category: str) -> float:
        """Calculate priority score for code structure and error handling issues"""
        base_scores = {
            "critical": 100,
            "high": 75,
            "medium": 50,
            "low": 25
        }
        
        category_multipliers = {
            "structure": 1.0,
            "error_handling": 1.2  # Error handling is slightly more important
        }
        
        type_multipliers = {
            "syntax_error": 2.0,
            "missing_error_handling": 1.5,
            "bare_except": 1.3,
            "function_too_long": 1.1,
            "too_many_parameters": 1.1,
            "missing_docstring": 0.8
        }
        
        score = base_scores.get(issue.get("severity", "low"), 25)
        score *= category_multipliers.get(category, 1.0)
        score *= type_multipliers.get(issue.get("type", ""), 1.0)
        
        # Boost score for auto-fixable issues (easier to address)
        if issue.get("auto_fixable", False):
            score *= 1.1
        
        return score
    
    def _calculate_dependency_priority_score(self, issue: Dict[str, Any]) -> float:
        """Calculate priority score for dependency issues"""
        base_scores = {
            "vulnerable": 90,
            "potentially_outdated": 40,
            "unnecessary": 30
        }
        
        # Critical packages get higher priority
        critical_packages = [
            "django", "flask", "fastapi", "requests", "urllib3",
            "react", "vue", "angular", "express", "lodash"
        ]
        
        score = base_scores.get(issue.get("issue_type", ""), 30)
        
        if issue.get("package_name", "").lower() in critical_packages:
            score *= 1.3
        
        return score
    
    def _calculate_documentation_priority_score(self, gap: Dict[str, Any]) -> float:
        """Calculate priority score for documentation gaps"""
        base_scores = {
            "missing_module_docstring": 20,
            "missing_docstring": 15,
            "incomplete_docstring": 10,
            "missing_type_hints": 25
        }
        
        score = base_scores.get(gap.get("gap_type", ""), 10)
        
        # Public APIs get higher priority
        if gap.get("function_name") and not gap.get("function_name", "").startswith("_"):
            score *= 1.2
        
        return score
    
    def _map_dependency_severity(self, issue_type: str) -> str:
        """Map dependency issue types to severity levels"""
        mapping = {
            "vulnerable": "high",
            "potentially_outdated": "medium",
            "unnecessary": "low"
        }
        return mapping.get(issue_type, "low")
    
    def _generate_fix_suggestions(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable fix suggestions"""
        suggestions = []
        
        # Analyze patterns in issues to generate targeted suggestions
        structure_issues = results.get("code_structure_issues", [])
        error_handling_issues = results.get("error_handling_issues", [])
        dependency_issues = results.get("dependency_issues", [])
        documentation_gaps = results.get("documentation_gaps", [])
        
        # Function length issues
        long_function_count = sum(1 for issue in structure_issues if issue.get("type") == "function_too_long")
        if long_function_count > 3:
            suggestions.append({
                "category": "refactoring",
                "priority": "medium",
                "title": "Refactor Long Functions",
                "description": f"Found {long_function_count} functions that exceed recommended length",
                "action": "Break down large functions into smaller, more focused functions",
                "estimated_effort": "medium",
                "files_affected": [issue["file_path"] for issue in structure_issues if issue.get("type") == "function_too_long"]
            })
        
        # Error handling issues
        if len(error_handling_issues) > 5:
            suggestions.append({
                "category": "error_handling",
                "priority": "high",
                "title": "Improve Error Handling",
                "description": f"Found {len(error_handling_issues)} error handling issues",
                "action": "Add try-except blocks and specific exception handling",
                "estimated_effort": "high",
                "files_affected": list(set(issue["file_path"] for issue in error_handling_issues))
            })
        
        # Documentation gaps
        if len(documentation_gaps) > 10:
            suggestions.append({
                "category": "documentation",
                "priority": "low",
                "title": "Improve Documentation Coverage",
                "description": f"Found {len(documentation_gaps)} documentation gaps",
                "action": "Add docstrings and type hints to public functions and classes",
                "estimated_effort": "medium",
                "files_affected": list(set(gap["file_path"] for gap in documentation_gaps))
            })
        
        # Dependency updates
        outdated_deps = [dep for dep in dependency_issues if dep.get("issue_type") == "potentially_outdated"]
        if len(outdated_deps) > 3:
            suggestions.append({
                "category": "dependencies",
                "priority": "medium",
                "title": "Update Dependencies",
                "description": f"Found {len(outdated_deps)} potentially outdated dependencies",
                "action": "Review and update package versions, test for compatibility",
                "estimated_effort": "medium",
                "packages_affected": [dep["package_name"] for dep in outdated_deps]
            })
        
        return suggestions
    
    def _add_ubuntu_compatibility_notes(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add Ubuntu-specific compatibility notes"""
        notes = []
        
        # Check for common Ubuntu compatibility issues
        dependency_issues = results.get("dependency_issues", [])
        
        # Python version compatibility
        notes.append({
            "category": "python_compatibility",
            "title": "Python Version Compatibility",
            "description": "Ensure all dependencies are compatible with Python 3.11 on Ubuntu 24.04.2",
            "recommendation": "Test installation and functionality on Ubuntu 24.04.2 with Python 3.11"
        })
        
        # Node.js compatibility
        if any("package.json" in dep.get("file_path", "") for dep in dependency_issues):
            notes.append({
                "category": "nodejs_compatibility",
                "title": "Node.js Version Compatibility",
                "description": "Verify Node.js packages work with Node 20 LTS on Ubuntu",
                "recommendation": "Test npm install and build processes on Ubuntu 24.04.2 with Node 20"
            })
        
        # System dependencies
        notes.append({
            "category": "system_dependencies",
            "title": "System Package Dependencies",
            "description": "Some Python packages may require system libraries",
            "recommendation": "Document required apt packages and test installation on clean Ubuntu system"
        })
        
        return notes
    
    def generate_integration_report(self, output_file: str):
        """Generate a comprehensive integration report"""
        if not self.results_cache:
            raise ValueError("No analysis results available. Run analysis first.")
        
        results = self.results_cache
        
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "analyzer": "Code Quality and Technical Debt Analyzer",
                "version": "1.0.0",
                "scope": results.get("integration_info", {}).get("analysis_scope", {})
            },
            "executive_summary": self._generate_executive_summary(results),
            "detailed_findings": {
                "prioritized_issues": results.get("prioritized_issues", [])[:20],  # Top 20 issues
                "fix_suggestions": results.get("fix_suggestions", []),
                "ubuntu_compatibility": results.get("ubuntu_compatibility_notes", [])
            },
            "metrics": results.get("analysis_summary", {}),
            "raw_results": results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Integration report saved to {output_file}")
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of findings"""
        summary = results.get("analysis_summary", {})
        prioritized_issues = results.get("prioritized_issues", [])
        
        # Get top issues by category
        top_issues_by_category = {}
        for issue in prioritized_issues[:10]:  # Top 10 issues
            category = issue.get("category", "unknown")
            if category not in top_issues_by_category:
                top_issues_by_category[category] = []
            top_issues_by_category[category].append(issue)
        
        # Calculate risk assessment
        critical_count = summary.get("severity_breakdown", {}).get("critical", 0)
        high_count = summary.get("severity_breakdown", {}).get("high", 0)
        
        risk_level = "low"
        if critical_count > 0:
            risk_level = "critical"
        elif high_count > 5:
            risk_level = "high"
        elif high_count > 0:
            risk_level = "medium"
        
        return {
            "total_issues": summary.get("total_issues", 0),
            "risk_level": risk_level,
            "critical_issues": critical_count,
            "high_priority_issues": high_count,
            "auto_fixable_count": summary.get("auto_fixable_issues", 0),
            "top_categories": list(top_issues_by_category.keys()),
            "key_recommendations": results.get("recommendations", [])[:3]  # Top 3 recommendations
        }

def main():
    """Main function for integration testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run integrated code quality analysis")
    parser.add_argument("--directory", "-d", default=".", help="Directory to analyze")
    parser.add_argument("--output", "-o", help="Output file for integration report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        integration = CodeQualityIntegration(args.directory)
        results = integration.run_integrated_analysis()
        
        if args.output:
            integration.generate_integration_report(args.output)
            print(f"Integration report saved to {args.output}")
        else:
            print(json.dumps(results, indent=2))
    
    except Exception as e:
        logger.error(f"Integration analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()