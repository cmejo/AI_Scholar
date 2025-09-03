#!/usr/bin/env python3
"""
Performance Analysis Integration

This module integrates the performance analyzer with the overall codebase
analysis system, providing unified reporting and coordination with other
analysis tools.

Requirements: 5.1, 5.2, 5.3, 5.4
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from performance_analyzer import PerformanceAnalyzer, PerformanceAnalysisResult

class PerformanceAnalysisIntegration:
    """Integration layer for performance analysis"""
    
    def __init__(self):
        self.analyzer = PerformanceAnalyzer()
        self.integration_config = {
            "enabled": True,
            "focus_areas": ["memory", "database", "cpu", "caching"],
            "severity_threshold": "medium",
            "output_formats": ["json", "summary"],
            "integration_points": {
                "python_backend_analyzer": True,
                "comprehensive_analysis": True,
                "ci_cd_integration": True
            }
        }
    
    def run_integrated_analysis(self, directory: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run performance analysis as part of integrated codebase analysis"""
        if config:
            self.integration_config.update(config)
        
        if not self.integration_config.get("enabled", True):
            return {"status": "disabled", "results": None}
        
        print("Running Performance Analysis...")
        
        try:
            # Run the performance analysis
            results = self.analyzer.analyze_directory(directory)
            
            # Convert to integration format
            integration_results = self._convert_to_integration_format(results)
            
            # Apply filters based on configuration
            filtered_results = self._apply_filters(integration_results)
            
            return {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "results": filtered_results,
                "summary": self._generate_integration_summary(filtered_results),
                "recommendations": self._generate_integration_recommendations(filtered_results)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "results": None
            }
    
    def _convert_to_integration_format(self, results: PerformanceAnalysisResult) -> Dict[str, Any]:
        """Convert performance analysis results to integration format"""
        return {
            "memory_leaks": [
                {
                    "id": f"perf_mem_{i}",
                    "type": "performance_memory_leak",
                    "severity": issue.severity,
                    "category": "performance",
                    "subcategory": "memory_management",
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "description": issue.description,
                    "leak_type": issue.leak_type,
                    "memory_growth_rate": issue.memory_growth_rate,
                    "recommendations": issue.recommendations,
                    "auto_fixable": False,
                    "ubuntu_specific": False
                }
                for i, issue in enumerate(results.memory_leaks)
            ],
            "database_issues": [
                {
                    "id": f"perf_db_{i}",
                    "type": "performance_database",
                    "severity": issue.severity,
                    "category": "performance",
                    "subcategory": "database_optimization",
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "description": issue.description,
                    "query_type": issue.query_type,
                    "query_text": issue.query_text[:200] + "..." if len(issue.query_text) > 200 else issue.query_text,
                    "execution_time": issue.execution_time,
                    "optimization_suggestions": issue.optimization_suggestions,
                    "auto_fixable": self._is_auto_fixable_db_issue(issue),
                    "ubuntu_specific": False
                }
                for i, issue in enumerate(results.database_issues)
            ],
            "cpu_bottlenecks": [
                {
                    "id": f"perf_cpu_{i}",
                    "type": "performance_cpu_bottleneck",
                    "severity": issue.severity,
                    "category": "performance",
                    "subcategory": "cpu_optimization",
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "description": issue.description,
                    "function_name": issue.function_name,
                    "cpu_usage_percent": issue.cpu_usage_percent,
                    "execution_time": issue.execution_time,
                    "optimization_suggestions": issue.optimization_suggestions,
                    "auto_fixable": False,
                    "ubuntu_specific": False
                }
                for i, issue in enumerate(results.cpu_bottlenecks)
            ],
            "caching_issues": [
                {
                    "id": f"perf_cache_{i}",
                    "type": "performance_caching",
                    "severity": issue.severity,
                    "category": "performance",
                    "subcategory": "caching_optimization",
                    "file_path": issue.file_path,
                    "line_number": None,
                    "description": issue.description,
                    "cache_type": issue.cache_type,
                    "hit_rate": issue.hit_rate,
                    "miss_rate": issue.miss_rate,
                    "optimization_suggestions": issue.optimization_suggestions,
                    "auto_fixable": self._is_auto_fixable_cache_issue(issue),
                    "ubuntu_specific": False
                }
                for i, issue in enumerate(results.caching_issues)
            ]
        }
    
    def _is_auto_fixable_db_issue(self, issue) -> bool:
        """Determine if a database issue is auto-fixable"""
        auto_fixable_types = [
            "SELECT * which may be inefficient",
            "lacks LIMIT clause"
        ]
        return any(fixable_type in issue.description for fixable_type in auto_fixable_types)
    
    def _is_auto_fixable_cache_issue(self, issue) -> bool:
        """Determine if a caching issue is auto-fixable"""
        auto_fixable_types = [
            "lru_cache_no_maxsize",
            "cache_no_timeout"
        ]
        return issue.cache_type in auto_fixable_types
    
    def _apply_filters(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration filters to results"""
        severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_severity = severity_levels.get(self.integration_config.get("severity_threshold", "medium"), 1)
        
        focus_areas = self.integration_config.get("focus_areas", ["memory", "database", "cpu", "caching"])
        
        filtered_results = {}
        
        # Filter by focus areas and severity
        if "memory" in focus_areas:
            filtered_results["memory_leaks"] = [
                issue for issue in results.get("memory_leaks", [])
                if severity_levels.get(issue["severity"], 0) >= min_severity
            ]
        
        if "database" in focus_areas:
            filtered_results["database_issues"] = [
                issue for issue in results.get("database_issues", [])
                if severity_levels.get(issue["severity"], 0) >= min_severity
            ]
        
        if "cpu" in focus_areas:
            filtered_results["cpu_bottlenecks"] = [
                issue for issue in results.get("cpu_bottlenecks", [])
                if severity_levels.get(issue["severity"], 0) >= min_severity
            ]
        
        if "caching" in focus_areas:
            filtered_results["caching_issues"] = [
                issue for issue in results.get("caching_issues", [])
                if severity_levels.get(issue["severity"], 0) >= min_severity
            ]
        
        return filtered_results
    
    def _generate_integration_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary for integration reporting"""
        total_issues = sum(len(issues) for issues in results.values())
        
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        category_counts = {"memory": 0, "database": 0, "cpu": 0, "caching": 0}
        
        for category, issues in results.items():
            if category == "memory_leaks":
                category_counts["memory"] = len(issues)
            elif category == "database_issues":
                category_counts["database"] = len(issues)
            elif category == "cpu_bottlenecks":
                category_counts["cpu"] = len(issues)
            elif category == "caching_issues":
                category_counts["caching"] = len(issues)
            
            for issue in issues:
                severity = issue.get("severity", "low")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_performance_issues": total_issues,
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "critical_issues_found": severity_counts["critical"] > 0,
            "high_priority_issues": severity_counts["critical"] + severity_counts["high"],
            "auto_fixable_issues": sum(
                1 for issues in results.values()
                for issue in issues
                if issue.get("auto_fixable", False)
            )
        }
    
    def _generate_integration_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for integration reporting"""
        recommendations = []
        
        # Memory leak recommendations
        if results.get("memory_leaks"):
            recommendations.append({
                "category": "memory_management",
                "priority": "high",
                "title": "Implement Proper Resource Management",
                "description": "Use context managers and proper cleanup for all resources",
                "affected_files": len(set(issue["file_path"] for issue in results["memory_leaks"] if issue["file_path"])),
                "estimated_effort": "medium"
            })
        
        # Database performance recommendations
        if results.get("database_issues"):
            recommendations.append({
                "category": "database_optimization",
                "priority": "high",
                "title": "Optimize Database Queries",
                "description": "Add indexes, use specific column selection, and implement query limits",
                "affected_files": len(set(issue["file_path"] for issue in results["database_issues"] if issue["file_path"])),
                "estimated_effort": "medium"
            })
        
        # CPU optimization recommendations
        if results.get("cpu_bottlenecks"):
            recommendations.append({
                "category": "cpu_optimization",
                "priority": "medium",
                "title": "Optimize CPU-Intensive Operations",
                "description": "Use async operations, optimize algorithms, and reduce nested loops",
                "affected_files": len(set(issue["file_path"] for issue in results["cpu_bottlenecks"] if issue["file_path"])),
                "estimated_effort": "high"
            })
        
        # Caching recommendations
        if results.get("caching_issues"):
            recommendations.append({
                "category": "caching_optimization",
                "priority": "medium",
                "title": "Implement Comprehensive Caching Strategy",
                "description": "Add caching for expensive operations and optimize cache configuration",
                "affected_files": len(set(issue["file_path"] for issue in results["caching_issues"] if issue["file_path"])),
                "estimated_effort": "medium"
            })
        
        return recommendations
    
    def generate_ci_cd_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CI/CD compatible report"""
        summary = results.get("summary", {})
        
        # Determine if build should fail
        critical_issues = summary.get("critical_issues_found", False)
        high_priority_count = summary.get("high_priority_issues", 0)
        
        build_status = "success"
        if critical_issues:
            build_status = "failure"
        elif high_priority_count > 10:  # Configurable threshold
            build_status = "warning"
        
        return {
            "build_status": build_status,
            "performance_score": self._calculate_performance_score(summary),
            "total_issues": summary.get("total_performance_issues", 0),
            "critical_issues": summary.get("severity_breakdown", {}).get("critical", 0),
            "high_issues": summary.get("severity_breakdown", {}).get("high", 0),
            "auto_fixable": summary.get("auto_fixable_issues", 0),
            "recommendations_count": len(results.get("recommendations", [])),
            "quality_gate_passed": not critical_issues and high_priority_count <= 10
        }
    
    def _calculate_performance_score(self, summary: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""
        total_issues = summary.get("total_performance_issues", 0)
        severity_breakdown = summary.get("severity_breakdown", {})
        
        if total_issues == 0:
            return 100.0
        
        # Weight issues by severity
        weighted_issues = (
            severity_breakdown.get("critical", 0) * 4 +
            severity_breakdown.get("high", 0) * 3 +
            severity_breakdown.get("medium", 0) * 2 +
            severity_breakdown.get("low", 0) * 1
        )
        
        # Calculate score (higher weighted issues = lower score)
        max_possible_score = total_issues * 4  # All critical
        score = max(0, 100 - (weighted_issues / max_possible_score * 100))
        
        return round(score, 1)
    
    def save_integration_results(self, results: Dict[str, Any], output_dir: str) -> None:
        """Save integration results in multiple formats"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save detailed JSON results
        with open(os.path.join(output_dir, "performance_analysis_detailed.json"), "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save CI/CD report
        ci_cd_report = self.generate_ci_cd_report(results)
        with open(os.path.join(output_dir, "performance_analysis_ci_cd.json"), "w") as f:
            json.dump(ci_cd_report, f, indent=2)
        
        # Save summary report
        summary_report = {
            "timestamp": results.get("timestamp"),
            "status": results.get("status"),
            "summary": results.get("summary"),
            "recommendations": results.get("recommendations"),
            "ci_cd_report": ci_cd_report
        }
        
        with open(os.path.join(output_dir, "performance_analysis_summary.json"), "w") as f:
            json.dump(summary_report, f, indent=2, default=str)
        
        print(f"Performance analysis integration results saved to: {output_dir}")

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Analysis Integration")
    parser.add_argument("directory", help="Directory to analyze")
    parser.add_argument("--output-dir", "-o", default="performance_analysis_output",
                       help="Output directory for results")
    parser.add_argument("--config", "-c", help="Configuration file (JSON)")
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Run integration analysis
    integration = PerformanceAnalysisIntegration()
    results = integration.run_integrated_analysis(args.directory, config)
    
    # Save results
    integration.save_integration_results(results, args.output_dir)
    
    # Print summary
    if results["status"] == "completed":
        summary = results["summary"]
        print(f"\nPerformance Analysis Integration Complete")
        print(f"Total Issues: {summary['total_performance_issues']}")
        print(f"Critical Issues: {summary['severity_breakdown']['critical']}")
        print(f"High Priority Issues: {summary['high_priority_issues']}")
        print(f"Auto-fixable Issues: {summary['auto_fixable_issues']}")
        
        ci_cd_report = integration.generate_ci_cd_report(results)
        print(f"Performance Score: {ci_cd_report['performance_score']}/100")
        print(f"Quality Gate: {'PASSED' if ci_cd_report['quality_gate_passed'] else 'FAILED'}")
    else:
        print(f"Analysis failed: {results.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()