#!/usr/bin/env python3
"""
Frontend Analysis Integration Script

This script integrates the TypeScript/React frontend analysis with the main
codebase analysis system, providing a unified interface for frontend code quality checks.

Requirements: 2.1, 2.2, 2.3
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typescript_frontend_analyzer import TypeScriptFrontendAnalyzer

class FrontendAnalysisIntegration:
    """Integration class for frontend analysis with the main analysis system"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.analyzer = TypeScriptFrontendAnalyzer(str(project_root))
        
    def run_frontend_analysis(self) -> Dict[str, Any]:
        """Run comprehensive frontend analysis and return standardized results"""
        print("Running comprehensive frontend analysis...")
        
        # Run the analysis
        result = self.analyzer.run_comprehensive_analysis()
        
        # Convert to standardized format for integration
        standardized_result = self._standardize_results(result)
        
        return standardized_result
    
    def _standardize_results(self, result) -> Dict[str, Any]:
        """Convert analysis results to standardized format"""
        
        # Extract all issues
        all_issues = []
        
        # TypeScript issues
        all_issues.extend(result.typescript_analysis.compilation_errors)
        all_issues.extend(result.typescript_analysis.type_errors)
        all_issues.extend(result.typescript_analysis.warnings)
        
        # React issues
        all_issues.extend(result.react_analysis.unused_imports)
        all_issues.extend(result.react_analysis.component_issues)
        all_issues.extend(result.react_analysis.hook_issues)
        
        # Bundle issues
        all_issues.extend(result.bundle_analysis.bundle_size_issues)
        all_issues.extend(result.bundle_analysis.optimization_opportunities)
        all_issues.extend(result.bundle_analysis.dependency_issues)
        all_issues.extend(result.bundle_analysis.performance_recommendations)
        
        # Accessibility issues
        all_issues.extend(result.accessibility_analysis.accessibility_violations)
        all_issues.extend(result.accessibility_analysis.wcag_compliance_issues)
        all_issues.extend(result.accessibility_analysis.semantic_issues)
        
        # Categorize issues by severity
        issues_by_severity = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        
        for issue in all_issues:
            severity = issue.severity.value
            issues_by_severity[severity].append({
                'id': issue.id,
                'type': issue.type.value,
                'file_path': issue.file_path,
                'line_number': issue.line_number,
                'column_number': issue.column_number,
                'description': issue.description,
                'recommendation': issue.recommendation,
                'auto_fixable': issue.auto_fixable
            })
        
        # Generate metrics
        metrics = {
            'total_issues': len(all_issues),
            'critical_issues': len(issues_by_severity['critical']),
            'high_issues': len(issues_by_severity['high']),
            'medium_issues': len(issues_by_severity['medium']),
            'low_issues': len(issues_by_severity['low']),
            'info_issues': len(issues_by_severity['info']),
            'auto_fixable_issues': sum(1 for issue in all_issues if issue.auto_fixable),
            'typescript_files_analyzed': result.typescript_analysis.total_files_analyzed,
            'react_components_analyzed': result.react_analysis.total_components_analyzed,
            'accessibility_components_checked': result.accessibility_analysis.total_components_checked
        }
        
        # Generate file-level summary
        files_with_issues = {}
        for issue in all_issues:
            file_path = issue.file_path
            if file_path not in files_with_issues:
                files_with_issues[file_path] = {
                    'total_issues': 0,
                    'critical': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0,
                    'info': 0,
                    'types': set()
                }
            
            files_with_issues[file_path]['total_issues'] += 1
            files_with_issues[file_path][issue.severity.value] += 1
            files_with_issues[file_path]['types'].add(issue.type.value)
        
        # Convert sets to lists for JSON serialization
        for file_info in files_with_issues.values():
            file_info['types'] = list(file_info['types'])
        
        return {
            'analysis_type': 'frontend',
            'timestamp': result.timestamp,
            'success': result.summary['overall_success'],
            'metrics': metrics,
            'issues_by_severity': issues_by_severity,
            'files_with_issues': files_with_issues,
            'bundle_stats': result.bundle_analysis.bundle_stats,
            'recommendations': self._generate_prioritized_recommendations(all_issues, result),
            'raw_results': {
                'typescript_analysis': {
                    'compilation_errors': len(result.typescript_analysis.compilation_errors),
                    'type_errors': len(result.typescript_analysis.type_errors),
                    'warnings': len(result.typescript_analysis.warnings),
                    'success': result.typescript_analysis.success
                },
                'react_analysis': {
                    'unused_imports': len(result.react_analysis.unused_imports),
                    'component_issues': len(result.react_analysis.component_issues),
                    'hook_issues': len(result.react_analysis.hook_issues),
                    'success': result.react_analysis.success
                },
                'bundle_analysis': {
                    'bundle_size_issues': len(result.bundle_analysis.bundle_size_issues),
                    'optimization_opportunities': len(result.bundle_analysis.optimization_opportunities),
                    'dependency_issues': len(result.bundle_analysis.dependency_issues),
                    'performance_recommendations': len(result.bundle_analysis.performance_recommendations),
                    'success': result.bundle_analysis.success
                },
                'accessibility_analysis': {
                    'accessibility_violations': len(result.accessibility_analysis.accessibility_violations),
                    'wcag_compliance_issues': len(result.accessibility_analysis.wcag_compliance_issues),
                    'semantic_issues': len(result.accessibility_analysis.semantic_issues),
                    'success': result.accessibility_analysis.success
                }
            }
        }
    
    def _generate_prioritized_recommendations(self, all_issues: List, result) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations based on analysis results"""
        recommendations = []
        
        # Critical and high priority issues first
        critical_high_issues = [issue for issue in all_issues 
                               if issue.severity.value in ['critical', 'high']]
        
        if critical_high_issues:
            recommendations.append({
                'priority': 'high',
                'category': 'critical_fixes',
                'title': 'Fix Critical and High Priority Issues',
                'description': f'Address {len(critical_high_issues)} critical/high priority issues that may block deployment or cause runtime errors',
                'action_items': [
                    'Review TypeScript compilation errors',
                    'Fix accessibility violations',
                    'Address React hooks rule violations',
                    'Resolve type safety issues'
                ]
            })
        
        # Bundle optimization
        bundle_issues = (len(result.bundle_analysis.bundle_size_issues) + 
                        len(result.bundle_analysis.optimization_opportunities))
        if bundle_issues > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'performance',
                'title': 'Optimize Bundle Performance',
                'description': f'Address {bundle_issues} bundle-related issues to improve loading performance',
                'action_items': [
                    'Implement code splitting for large components',
                    'Remove unused dependencies',
                    'Configure tree shaking',
                    'Optimize chunk sizes'
                ]
            })
        
        # Dependency updates
        dependency_issues = len(result.bundle_analysis.dependency_issues)
        if dependency_issues > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'maintenance',
                'title': 'Update Dependencies',
                'description': f'Update {dependency_issues} outdated dependencies to latest versions',
                'action_items': [
                    'Review and update outdated packages',
                    'Test compatibility after updates',
                    'Remove unused dependencies',
                    'Audit for security vulnerabilities'
                ]
            })
        
        # Code quality improvements
        code_quality_issues = [issue for issue in all_issues 
                              if issue.type.value in ['unused_import', 'component_issue']]
        if code_quality_issues:
            recommendations.append({
                'priority': 'low',
                'category': 'code_quality',
                'title': 'Improve Code Quality',
                'description': f'Clean up {len(code_quality_issues)} code quality issues',
                'action_items': [
                    'Remove unused imports',
                    'Fix component naming conventions',
                    'Remove console statements',
                    'Improve error handling'
                ]
            })
        
        # Accessibility improvements
        a11y_issues = (len(result.accessibility_analysis.accessibility_violations) + 
                      len(result.accessibility_analysis.wcag_compliance_issues) + 
                      len(result.accessibility_analysis.semantic_issues))
        if a11y_issues > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'accessibility',
                'title': 'Improve Accessibility',
                'description': f'Address {a11y_issues} accessibility issues to ensure inclusive user experience',
                'action_items': [
                    'Add alt text to images',
                    'Ensure proper heading hierarchy',
                    'Add ARIA labels to interactive elements',
                    'Implement keyboard navigation support'
                ]
            })
        
        return recommendations
    
    def generate_integration_report(self, output_file: str = "frontend_integration_report.json"):
        """Generate integration report for the main analysis system"""
        try:
            result = self.run_frontend_analysis()
            
            # Add integration metadata
            result['integration_metadata'] = {
                'analyzer_version': '1.0.0',
                'requirements_covered': ['2.1', '2.2', '2.3'],
                'analysis_scope': [
                    'TypeScript compilation errors and type mismatches',
                    'React component analysis for unused imports and issues',
                    'Bundle analysis for performance optimization',
                    'Accessibility compliance checking'
                ],
                'generated_at': datetime.now().isoformat(),
                'project_root': str(self.project_root)
            }
            
            # Save the report
            output_path = self.project_root / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"Frontend integration report saved to: {output_path}")
            
            return result
            
        except Exception as e:
            print(f"Error generating integration report: {e}")
            return None
    
    def get_quick_status(self) -> Dict[str, Any]:
        """Get quick status for dashboard integration"""
        try:
            result = self.run_frontend_analysis()
            
            return {
                'status': 'success' if result['success'] else 'issues_found',
                'total_issues': result['metrics']['total_issues'],
                'critical_issues': result['metrics']['critical_issues'],
                'high_issues': result['metrics']['high_issues'],
                'files_analyzed': (result['metrics']['typescript_files_analyzed'] + 
                                 result['metrics']['react_components_analyzed']),
                'auto_fixable_issues': result['metrics']['auto_fixable_issues'],
                'last_analysis': result['timestamp']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_analysis': datetime.now().isoformat()
            }

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Frontend Analysis Integration")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", default="frontend_integration_report.json", help="Output file")
    parser.add_argument("--quick-status", action="store_true", help="Show quick status only")
    
    args = parser.parse_args()
    
    integration = FrontendAnalysisIntegration(args.project_root)
    
    if args.quick_status:
        status = integration.get_quick_status()
        print(json.dumps(status, indent=2))
    else:
        result = integration.generate_integration_report(args.output)
        if result:
            print(f"\nFrontend Analysis Summary:")
            print(f"Total Issues: {result['metrics']['total_issues']}")
            print(f"Critical Issues: {result['metrics']['critical_issues']}")
            print(f"High Priority Issues: {result['metrics']['high_issues']}")
            print(f"Auto-fixable Issues: {result['metrics']['auto_fixable_issues']}")
            print(f"Overall Success: {result['success']}")

if __name__ == "__main__":
    main()