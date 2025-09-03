#!/usr/bin/env python3
"""
Docker and Deployment Configuration Analysis Runner

This script runs the Docker and deployment configuration validator
and integrates with the existing analysis infrastructure.

Requirements covered:
- 3.1: Ubuntu-compatible Docker configurations
- 3.2: Docker-compose service definitions and networking
- 3.3: Ubuntu shell compatibility for deployment scripts
- 3.4: Environment variable and configuration validation
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_deployment_validator import DockerDeploymentValidator, ValidationResult


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('docker_deployment_analysis.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def save_json_results(result: ValidationResult, output_file: str):
    """Save validation results in JSON format"""
    json_result = {
        "analysis_info": {
            "timestamp": datetime.now().isoformat(),
            "analyzer": "docker_deployment_validator",
            "version": "1.0.0"
        },
        "summary": {
            "files_analyzed": result.files_analyzed,
            "total_issues": result.total_issues,
            "critical_issues": result.critical_issues,
            "high_issues": result.high_issues,
            "medium_issues": result.medium_issues,
            "low_issues": result.low_issues,
            "info_issues": result.info_issues
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
        ],
        "ubuntu_compatibility": {
            "total_ubuntu_issues": len([i for i in result.issues if i.ubuntu_specific]),
            "ubuntu_issues": [
                {
                    "file_path": issue.file_path,
                    "description": issue.description,
                    "severity": issue.severity.value,
                    "recommendation": issue.recommendation
                }
                for issue in result.issues if issue.ubuntu_specific
            ]
        },
        "auto_fixable_issues": {
            "total_auto_fixable": len([i for i in result.issues if i.auto_fixable]),
            "auto_fixable_issues": [
                {
                    "file_path": issue.file_path,
                    "description": issue.description,
                    "recommendation": issue.recommendation
                }
                for issue in result.issues if issue.auto_fixable
            ]
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_result, f, indent=2, ensure_ascii=False)


def generate_summary_report(result: ValidationResult) -> str:
    """Generate a concise summary report"""
    ubuntu_issues = [i for i in result.issues if i.ubuntu_specific]
    critical_issues = [i for i in result.issues if i.severity.value == 'critical']
    high_issues = [i for i in result.issues if i.severity.value == 'high']
    
    summary = f"""
Docker and Deployment Configuration Analysis Summary
==================================================

Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Files Analyzed: {result.files_analyzed}
Total Issues Found: {result.total_issues}

Issue Breakdown:
- Critical: {result.critical_issues}
- High: {result.high_issues}
- Medium: {result.medium_issues}
- Low: {result.low_issues}
- Info: {result.info_issues}

Ubuntu Compatibility:
- Ubuntu-specific issues: {len(ubuntu_issues)}
- Auto-fixable issues: {len([i for i in result.issues if i.auto_fixable])}

Priority Issues Requiring Immediate Attention:
"""
    
    if critical_issues:
        summary += "\nCRITICAL ISSUES:\n"
        for issue in critical_issues[:5]:  # Show first 5
            summary += f"- {issue.file_path}: {issue.description}\n"
    
    if high_issues:
        summary += "\nHIGH PRIORITY ISSUES:\n"
        for issue in high_issues[:5]:  # Show first 5
            summary += f"- {issue.file_path}: {issue.description}\n"
    
    if ubuntu_issues:
        summary += "\nUBUNTU COMPATIBILITY ISSUES:\n"
        for issue in ubuntu_issues[:5]:  # Show first 5
            summary += f"- {issue.file_path}: {issue.description}\n"
    
    summary += f"""
Recommendations:
1. Address all critical issues immediately
2. Review Ubuntu-specific compatibility issues for deployment
3. Consider implementing auto-fixes for simple issues
4. Review security-related findings
5. Update deployment scripts for Ubuntu compatibility

For detailed analysis, see the full report files.
"""
    
    return summary


def main():
    """Main function to run Docker deployment analysis"""
    logger = setup_logging()
    
    logger.info("Starting Docker and Deployment Configuration Analysis")
    logger.info("=" * 60)
    
    # Initialize validator
    project_root = "."
    validator = DockerDeploymentValidator(project_root)
    
    try:
        # Run comprehensive validation
        logger.info("Running comprehensive Docker and deployment validation...")
        result = validator.validate_all()
        
        # Generate output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON results
        json_output = f"docker_deployment_analysis_results_{timestamp}.json"
        save_json_results(result, json_output)
        logger.info(f"JSON results saved to: {json_output}")
        
        # Generate detailed markdown report
        markdown_output = f"docker_deployment_analysis_report_{timestamp}.md"
        validator.generate_report(result, markdown_output)
        logger.info(f"Detailed report saved to: {markdown_output}")
        
        # Generate summary report
        summary_output = f"docker_deployment_analysis_summary_{timestamp}.txt"
        summary = generate_summary_report(result)
        with open(summary_output, 'w', encoding='utf-8') as f:
            f.write(summary)
        logger.info(f"Summary report saved to: {summary_output}")
        
        # Print summary to console
        print("\n" + "=" * 60)
        print(summary)
        print("=" * 60)
        
        # Log final statistics
        logger.info("Analysis completed successfully")
        logger.info(f"Files analyzed: {result.files_analyzed}")
        logger.info(f"Total issues: {result.total_issues}")
        logger.info(f"Critical issues: {result.critical_issues}")
        logger.info(f"High priority issues: {result.high_issues}")
        logger.info(f"Ubuntu-specific issues: {len([i for i in result.issues if i.ubuntu_specific])}")
        
        # Return appropriate exit code
        if result.critical_issues > 0:
            logger.warning("Critical issues found - review required")
            return 1
        elif result.high_issues > 0:
            logger.warning("High priority issues found - review recommended")
            return 0
        else:
            logger.info("No critical issues found")
            return 0
            
    except Exception as e:
        logger.error(f"Analysis failed with error: {str(e)}")
        logger.exception("Full error details:")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)