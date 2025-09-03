#!/usr/bin/env python3
"""
Docker Deployment Analysis Integration

This script integrates the Docker deployment validator with the existing
comprehensive analysis system, providing unified reporting and task tracking.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_deployment_validator import DockerDeploymentValidator


def integrate_with_comprehensive_analysis():
    """Integrate Docker deployment analysis with the comprehensive analysis system"""
    
    logger = logging.getLogger(__name__)
    
    # Check if comprehensive analysis results exist
    comprehensive_results_pattern = "comprehensive_analysis_results_*.json"
    comprehensive_files = list(Path(".").glob(comprehensive_results_pattern))
    
    if not comprehensive_files:
        logger.warning("No comprehensive analysis results found. Running standalone analysis.")
        return run_standalone_analysis()
    
    # Get the most recent comprehensive analysis
    latest_comprehensive = max(comprehensive_files, key=os.path.getctime)
    logger.info(f"Found comprehensive analysis: {latest_comprehensive}")
    
    # Load existing results
    try:
        with open(latest_comprehensive, 'r') as f:
            comprehensive_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load comprehensive analysis: {e}")
        return run_standalone_analysis()
    
    # Run Docker deployment analysis
    validator = DockerDeploymentValidator(".")
    docker_result = validator.validate_all()
    
    # Convert Docker results to the comprehensive format
    docker_analysis = {
        "analysis_type": "docker_deployment",
        "timestamp": datetime.now().isoformat(),
        "files_analyzed": docker_result.files_analyzed,
        "total_issues": docker_result.total_issues,
        "severity_breakdown": {
            "critical": docker_result.critical_issues,
            "high": docker_result.high_issues,
            "medium": docker_result.medium_issues,
            "low": docker_result.low_issues,
            "info": docker_result.info_issues
        },
        "ubuntu_compatibility": {
            "total_ubuntu_issues": len([i for i in docker_result.issues if i.ubuntu_specific]),
            "ubuntu_specific_files": list(set([i.file_path for i in docker_result.issues if i.ubuntu_specific]))
        },
        "issue_categories": {
            "dockerfile_issues": len([i for i in docker_result.issues if "dockerfile" in i.issue_type.value]),
            "docker_compose_issues": len([i for i in docker_result.issues if "docker_compose" in i.issue_type.value]),
            "deployment_script_issues": len([i for i in docker_result.issues if "deployment_script" in i.issue_type.value]),
            "environment_config_issues": len([i for i in docker_result.issues if "environment_config" in i.issue_type.value]),
            "security_issues": len([i for i in docker_result.issues if "security" in i.issue_type.value])
        },
        "detailed_issues": [
            {
                "file_path": issue.file_path,
                "line_number": issue.line_number,
                "issue_type": issue.issue_type.value,
                "severity": issue.severity.value,
                "description": issue.description,
                "recommendation": issue.recommendation,
                "ubuntu_specific": issue.ubuntu_specific,
                "auto_fixable": issue.auto_fixable,
                "rule_id": issue.rule_id
            }
            for issue in docker_result.issues
        ]
    }
    
    # Add Docker analysis to comprehensive results
    if "analysis_results" not in comprehensive_data:
        comprehensive_data["analysis_results"] = {}
    
    comprehensive_data["analysis_results"]["docker_deployment"] = docker_analysis
    
    # Update summary statistics
    if "summary" not in comprehensive_data:
        comprehensive_data["summary"] = {}
    
    comprehensive_data["summary"]["docker_deployment"] = {
        "files_analyzed": docker_result.files_analyzed,
        "total_issues": docker_result.total_issues,
        "critical_issues": docker_result.critical_issues,
        "ubuntu_compatibility_issues": len([i for i in docker_result.issues if i.ubuntu_specific])
    }
    
    # Save updated comprehensive results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    updated_file = f"comprehensive_analysis_with_docker_{timestamp}.json"
    
    with open(updated_file, 'w') as f:
        json.dump(comprehensive_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Updated comprehensive analysis saved to: {updated_file}")
    
    # Generate integrated report
    generate_integrated_report(comprehensive_data, docker_analysis, timestamp)
    
    return docker_result


def run_standalone_analysis():
    """Run standalone Docker deployment analysis"""
    logger = logging.getLogger(__name__)
    logger.info("Running standalone Docker deployment analysis")
    
    validator = DockerDeploymentValidator(".")
    result = validator.validate_all()
    
    # Generate standalone reports
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON report
    json_output = f"docker_deployment_standalone_{timestamp}.json"
    json_data = {
        "analysis_info": {
            "timestamp": datetime.now().isoformat(),
            "analyzer": "docker_deployment_validator",
            "mode": "standalone"
        },
        "summary": {
            "files_analyzed": result.files_analyzed,
            "total_issues": result.total_issues,
            "critical_issues": result.critical_issues,
            "high_issues": result.high_issues,
            "medium_issues": result.medium_issues,
            "low_issues": result.low_issues,
            "info_issues": result.info_issues,
            "ubuntu_compatibility_issues": len([i for i in result.issues if i.ubuntu_specific])
        },
        "issues": [
            {
                "file_path": issue.file_path,
                "line_number": issue.line_number,
                "issue_type": issue.issue_type.value,
                "severity": issue.severity.value,
                "description": issue.description,
                "recommendation": issue.recommendation,
                "ubuntu_specific": issue.ubuntu_specific,
                "auto_fixable": issue.auto_fixable,
                "rule_id": issue.rule_id
            }
            for issue in result.issues
        ]
    }
    
    with open(json_output, 'w') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    # Markdown report
    markdown_output = f"docker_deployment_standalone_{timestamp}.md"
    validator.generate_report(result, markdown_output)
    
    logger.info(f"Standalone analysis complete. Reports saved:")
    logger.info(f"- JSON: {json_output}")
    logger.info(f"- Markdown: {markdown_output}")
    
    return result


def generate_integrated_report(comprehensive_data, docker_analysis, timestamp):
    """Generate an integrated report combining all analysis results"""
    
    report_lines = []
    
    # Header
    report_lines.append("# Comprehensive Codebase Analysis with Docker Deployment Validation")
    report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("")
    
    total_files = 0
    total_issues = 0
    
    if "summary" in comprehensive_data:
        for analysis_type, summary in comprehensive_data["summary"].items():
            total_files += summary.get("files_analyzed", 0)
            total_issues += summary.get("total_issues", 0)
    
    report_lines.append(f"- **Total Files Analyzed**: {total_files}")
    report_lines.append(f"- **Total Issues Found**: {total_issues}")
    report_lines.append("")
    
    # Analysis Breakdown
    report_lines.append("## Analysis Breakdown")
    report_lines.append("")
    
    if "summary" in comprehensive_data:
        for analysis_type, summary in comprehensive_data["summary"].items():
            analysis_name = analysis_type.replace("_", " ").title()
            report_lines.append(f"### {analysis_name}")
            report_lines.append(f"- Files analyzed: {summary.get('files_analyzed', 0)}")
            report_lines.append(f"- Issues found: {summary.get('total_issues', 0)}")
            
            if analysis_type == "docker_deployment":
                report_lines.append(f"- Critical issues: {summary.get('critical_issues', 0)}")
                report_lines.append(f"- Ubuntu compatibility issues: {summary.get('ubuntu_compatibility_issues', 0)}")
            
            report_lines.append("")
    
    # Docker Deployment Specific Findings
    report_lines.append("## Docker Deployment Analysis Highlights")
    report_lines.append("")
    
    if docker_analysis:
        report_lines.append(f"### Issue Categories")
        for category, count in docker_analysis["issue_categories"].items():
            category_name = category.replace("_", " ").title()
            report_lines.append(f"- {category_name}: {count}")
        
        report_lines.append("")
        report_lines.append("### Ubuntu Compatibility")
        ubuntu_info = docker_analysis["ubuntu_compatibility"]
        report_lines.append(f"- Total Ubuntu-specific issues: {ubuntu_info['total_ubuntu_issues']}")
        report_lines.append(f"- Files with Ubuntu issues: {len(ubuntu_info['ubuntu_specific_files'])}")
        
        if ubuntu_info['ubuntu_specific_files']:
            report_lines.append("\nFiles requiring Ubuntu compatibility review:")
            for file_path in ubuntu_info['ubuntu_specific_files'][:10]:  # Show first 10
                report_lines.append(f"- {file_path}")
        
        report_lines.append("")
    
    # Priority Recommendations
    report_lines.append("## Priority Recommendations")
    report_lines.append("")
    report_lines.append("1. **Critical Issues**: Address immediately to prevent deployment failures")
    report_lines.append("2. **Ubuntu Compatibility**: Review and fix Ubuntu-specific issues for server deployment")
    report_lines.append("3. **Security Issues**: Address security vulnerabilities in Docker configurations")
    report_lines.append("4. **Configuration Validation**: Fix docker-compose and environment configuration issues")
    report_lines.append("5. **Deployment Scripts**: Update deployment scripts for Ubuntu compatibility")
    report_lines.append("")
    
    # Next Steps
    report_lines.append("## Next Steps")
    report_lines.append("")
    report_lines.append("1. Review detailed analysis reports for each component")
    report_lines.append("2. Prioritize fixes based on severity and Ubuntu compatibility impact")
    report_lines.append("3. Test fixes in Ubuntu environment before production deployment")
    report_lines.append("4. Implement continuous validation in CI/CD pipeline")
    report_lines.append("5. Regular monitoring and maintenance of configuration quality")
    
    # Save integrated report
    integrated_report_file = f"integrated_analysis_report_{timestamp}.md"
    with open(integrated_report_file, 'w') as f:
        f.write("\n".join(report_lines))
    
    logging.getLogger(__name__).info(f"Integrated report saved to: {integrated_report_file}")


def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Docker Deployment Analysis Integration")
    
    try:
        result = integrate_with_comprehensive_analysis()
        
        logger.info("Docker deployment analysis integration completed successfully")
        logger.info(f"Total issues found: {result.total_issues}")
        logger.info(f"Critical issues: {result.critical_issues}")
        logger.info(f"Ubuntu compatibility issues: {len([i for i in result.issues if i.ubuntu_specific])}")
        
        # Return appropriate exit code
        if result.critical_issues > 0:
            return 1
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Integration failed: {str(e)}")
        logger.exception("Full error details:")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)