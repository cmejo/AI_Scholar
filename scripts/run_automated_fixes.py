#!/usr/bin/env python3
"""
Automated Fix Runner
Main entry point for running automated fixes on the codebase.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automated_fix_engine import AutoFixEngine, FixType
from automated_fix_integration import AutomatedFixIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_default_config():
    """Create default configuration file"""
    config = {
        "auto_apply_safe_fixes": True,
        "require_confirmation_for_medium_risk": True,
        "skip_high_risk_fixes": True,
        "create_backups": True,
        "max_fixes_per_run": 50,
        "fix_types_enabled": {
            "code_formatting": True,
            "dependency_updates": True,
            "configuration_fixes": True,
            "ubuntu_optimizations": True
        },
        "issue_type_mapping": {
            "syntax_error": "code_formatting",
            "style_violation": "code_formatting",
            "formatting_issue": "code_formatting",
            "outdated_dependency": "dependency_updates",
            "configuration_error": "configuration_fixes",
            "ubuntu_compatibility": "ubuntu_optimizations",
            "docker_issue": "configuration_fixes",
            "security_vulnerability": "dependency_updates"
        },
        "file_patterns": {
            "python": ["**/*.py"],
            "typescript": ["**/*.ts", "**/*.tsx"],
            "javascript": ["**/*.js", "**/*.jsx"],
            "config": ["**/*.json", "**/*.yml", "**/*.yaml", "**/Dockerfile*", "**/docker-compose*.yml"],
            "scripts": ["**/*.sh"]
        },
        "exclude_patterns": [
            "node_modules/**",
            ".git/**",
            "__pycache__/**",
            ".pytest_cache/**",
            "venv/**",
            ".venv/**",
            "dist/**",
            "build/**",
            ".next/**",
            "coverage/**"
        ]
    }
    
    config_file = Path("scripts/automated_fix_config.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Created default configuration at {config_file}")
    return config

def run_standalone_fixes(project_root: str, fix_types: list, dry_run: bool = False):
    """Run standalone fixes without analysis integration"""
    logger.info("Running standalone automated fixes...")
    
    fix_engine = AutoFixEngine(project_root)
    
    results = []
    
    if "formatting" in fix_types:
        logger.info("Applying code formatting fixes...")
        if not dry_run:
            formatting_results = fix_engine.apply_code_formatting_fixes()
            results.extend(formatting_results)
        else:
            logger.info("DRY RUN: Would apply code formatting fixes")
    
    if "dependencies" in fix_types:
        logger.info("Applying dependency updates...")
        if not dry_run:
            dependency_results = fix_engine.apply_dependency_updates()
            results.extend(dependency_results)
        else:
            logger.info("DRY RUN: Would apply dependency updates")
    
    if "config" in fix_types:
        logger.info("Applying configuration fixes...")
        if not dry_run:
            config_results = fix_engine.apply_configuration_fixes()
            results.extend(config_results)
        else:
            logger.info("DRY RUN: Would apply configuration fixes")
    
    if "ubuntu" in fix_types:
        logger.info("Applying Ubuntu optimizations...")
        if not dry_run:
            ubuntu_results = fix_engine.apply_ubuntu_optimizations()
            results.extend(ubuntu_results)
        else:
            logger.info("DRY RUN: Would apply Ubuntu optimizations")
    
    return results

def run_integrated_fixes(project_root: str, analysis_report: str = None, dry_run: bool = False):
    """Run integrated fixes with analysis"""
    logger.info("Running integrated analysis and fixes...")
    
    integration = AutomatedFixIntegration(project_root)
    
    # Override config for dry run
    if dry_run:
        integration.config["auto_apply_safe_fixes"] = False
        integration.config["require_confirmation_for_medium_risk"] = True
        integration.config["skip_high_risk_fixes"] = True
        logger.info("DRY RUN: No fixes will be applied")
    
    report = integration.analyze_and_fix(analysis_report)
    return report

def print_fix_summary(results, integrated_report=None):
    """Print summary of applied fixes"""
    print("\n" + "="*60)
    print("AUTOMATED FIX SUMMARY")
    print("="*60)
    
    if integrated_report:
        # Integrated report summary
        print(f"Analysis Issues Found: {integrated_report.get('analysis_summary', {}).get('total_issues', 0)}")
        print(f"Fix Recommendations: {integrated_report['fix_recommendations']['total_recommendations']}")
        print(f"Auto-applicable: {integrated_report['fix_recommendations']['auto_applicable']}")
        print(f"Requiring Review: {integrated_report['fix_recommendations']['requires_review']}")
        print(f"Fixes Applied: {integrated_report['applied_fixes']['total_applied']}")
        print(f"Successful: {integrated_report['applied_fixes']['successful']}")
        print(f"Failed: {integrated_report['applied_fixes']['failed']}")
        
        if integrated_report.get('remaining_issues'):
            print(f"Fix Rate: {integrated_report['remaining_issues']['fix_rate']:.1f}%")
        
        print("\nFixes by Type:")
        for fix_type, count in integrated_report['applied_fixes']['by_type'].items():
            print(f"  {fix_type}: {count}")
    
    else:
        # Standalone results summary
        successful = len([r for r in results if r.success])
        failed = len([r for r in results if not r.success])
        
        print(f"Total Fixes Applied: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        # Group by fix type
        by_type = {}
        for result in results:
            fix_type = result.fix_type.value
            by_type[fix_type] = by_type.get(fix_type, 0) + 1
        
        print("\nFixes by Type:")
        for fix_type, count in by_type.items():
            print(f"  {fix_type}: {count}")
        
        if failed > 0:
            print("\nFailed Fixes:")
            for result in results:
                if not result.success:
                    print(f"  {result.file_path}: {result.error_message}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Automated Fix Application System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all fixes with analysis integration
  python run_automated_fixes.py --integrated
  
  # Run specific fix types standalone
  python run_automated_fixes.py --fix-types formatting dependencies
  
  # Dry run to see what would be fixed
  python run_automated_fixes.py --dry-run
  
  # Use existing analysis report
  python run_automated_fixes.py --integrated --analysis-report analysis_report.json
  
  # Create default configuration
  python run_automated_fixes.py --create-config
        """
    )
    
    parser.add_argument("--project-root", default=".", 
                       help="Project root directory (default: current directory)")
    
    parser.add_argument("--integrated", action="store_true",
                       help="Run integrated analysis and fixes")
    
    parser.add_argument("--fix-types", nargs="+", 
                       choices=["formatting", "dependencies", "config", "ubuntu"],
                       default=["formatting", "dependencies", "config", "ubuntu"],
                       help="Types of fixes to apply (for standalone mode)")
    
    parser.add_argument("--analysis-report", 
                       help="Path to existing analysis report (for integrated mode)")
    
    parser.add_argument("--output", default=None,
                       help="Output report file")
    
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be fixed without applying changes")
    
    parser.add_argument("--create-config", action="store_true",
                       help="Create default configuration file")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create default config if requested
    if args.create_config:
        create_default_config()
        return
    
    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)
    
    logger.info(f"Running automated fixes on project: {project_root}")
    
    # Determine output file
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.integrated:
            args.output = f"integrated_fix_report_{timestamp}.json"
        else:
            args.output = f"automated_fix_report_{timestamp}.json"
    
    try:
        if args.integrated:
            # Run integrated analysis and fixes
            report = run_integrated_fixes(
                str(project_root), 
                args.analysis_report, 
                args.dry_run
            )
            
            # Save integrated report
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print_fix_summary([], report)
            
        else:
            # Run standalone fixes
            results = run_standalone_fixes(
                str(project_root), 
                args.fix_types, 
                args.dry_run
            )
            
            # Create standalone report
            report = {
                "timestamp": datetime.now().isoformat(),
                "project_root": str(project_root),
                "fix_types": args.fix_types,
                "dry_run": args.dry_run,
                "total_fixes": len(results),
                "successful_fixes": len([r for r in results if r.success]),
                "failed_fixes": len([r for r in results if not r.success]),
                "results": [
                    {
                        "success": r.success,
                        "fix_type": r.fix_type.value,
                        "file_path": r.file_path,
                        "description": r.description,
                        "changes_made": r.changes_made,
                        "backup_created": r.backup_created,
                        "error_message": r.error_message,
                        "warnings": r.warnings
                    }
                    for r in results
                ]
            }
            
            # Save standalone report
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print_fix_summary(results)
        
        print(f"\nDetailed report saved to: {args.output}")
        
        if args.dry_run:
            print("\nThis was a dry run - no changes were applied.")
            print("Remove --dry-run flag to apply fixes.")
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error during fix application: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()