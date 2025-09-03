#!/usr/bin/env python3
"""
User Acceptance Testing Runner
Main entry point for running comprehensive UAT for Zotero integration
"""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from uat_coordinator import UATCoordinator

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('tests/user_acceptance/uat_runner.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("uat_runner")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Run User Acceptance Testing for Zotero Integration"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="tests/user_acceptance/uat_config.json",
        help="Path to UAT configuration file"
    )
    
    parser.add_argument(
        "--phase",
        type=str,
        choices=["all", "beta", "accessibility", "performance", "feedback"],
        default="all",
        help="Specific UAT phase to run"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual testing)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="tests/user_acceptance/results",
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--participants",
        type=int,
        help="Override number of beta testing participants"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        help="Override beta testing duration in days"
    )
    
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip environment setup phase"
    )
    
    parser.add_argument(
        "--generate-report-only",
        action="store_true",
        help="Only generate report from existing results"
    )
    
    return parser.parse_args()

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate UAT configuration"""
    required_sections = ["beta_testing", "accessibility", "performance", "feedback"]
    
    for section in required_sections:
        if section not in config:
            print(f"Error: Missing required configuration section: {section}")
            return False
    
    # Validate beta testing config
    beta_config = config["beta_testing"]
    if beta_config.get("min_participants", 0) > beta_config.get("max_participants", 0):
        print("Error: min_participants cannot be greater than max_participants")
        return False
    
    # Validate performance thresholds
    perf_config = config["performance"]
    if perf_config.get("memory_threshold_mb", 0) <= 0:
        print("Error: memory_threshold_mb must be positive")
        return False
    
    return True

def load_config(config_path: str) -> Optional[Dict[str, Any]]:
    """Load and validate UAT configuration"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if not validate_config(config):
            return None
        
        return config
    
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        return None

def apply_cli_overrides(config: Dict[str, Any], args) -> Dict[str, Any]:
    """Apply command line argument overrides to configuration"""
    if args.participants:
        config["beta_testing"]["max_participants"] = args.participants
        config["beta_testing"]["min_participants"] = min(
            args.participants, 
            config["beta_testing"]["min_participants"]
        )
    
    if args.duration:
        config["beta_testing"]["duration_days"] = args.duration
    
    return config

async def run_specific_phase(coordinator: UATCoordinator, phase: str) -> Dict[str, Any]:
    """Run a specific UAT phase"""
    if phase == "beta":
        return await coordinator.beta_manager.run_beta_program()
    elif phase == "accessibility":
        return await coordinator.accessibility_tester.run_comprehensive_tests()
    elif phase == "performance":
        return await coordinator.performance_validator.validate_real_world_performance()
    elif phase == "feedback":
        return await coordinator.feedback_collector.analyze_comprehensive_feedback()
    else:
        raise ValueError(f"Unknown phase: {phase}")

def print_summary(results: Dict[str, Any], logger: logging.Logger):
    """Print UAT results summary"""
    print("\n" + "="*60)
    print("USER ACCEPTANCE TESTING SUMMARY")
    print("="*60)
    
    print(f"Start Time: {results.get('start_time', 'N/A')}")
    print(f"End Time: {results.get('end_time', 'N/A')}")
    print(f"Duration: {results.get('duration', 'N/A')}")
    print(f"Overall Status: {results.get('overall_status', 'Unknown')}")
    print(f"Success: {'✅ PASSED' if results.get('success') else '❌ FAILED'}")
    
    print("\nPhase Results:")
    for phase_name, phase_results in results.get("test_phases", {}).items():
        status = "✅ PASSED" if phase_results.get("success") else "❌ FAILED"
        print(f"  {phase_name.replace('_', ' ').title()}: {status}")
    
    # Print key metrics if available
    if "overall_metrics" in results:
        metrics = results["overall_metrics"]
        print(f"\nKey Metrics:")
        print(f"  Satisfaction Score: {metrics.get('average_satisfaction_score', 'N/A')}/5")
        print(f"  Recommendation Rate: {metrics.get('recommendation_rate', 'N/A')}%")
        print(f"  Task Completion Rate: {metrics.get('task_completion_rate', 'N/A')}%")
    
    # Print issues found
    issues = results.get("issues_found", [])
    if issues:
        print(f"\nIssues Found: {len(issues)}")
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        if critical_issues:
            print(f"  Critical Issues: {len(critical_issues)}")
    
    print("\n" + "="*60)

def check_quality_gates(results: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Check if results meet quality gate criteria"""
    quality_gates = config.get("quality_gates", {})
    
    if not quality_gates:
        return True
    
    gate_results = []
    
    # Check satisfaction score
    min_satisfaction = quality_gates.get("minimum_satisfaction_score", 0)
    actual_satisfaction = results.get("overall_metrics", {}).get("average_satisfaction_score", 0)
    if actual_satisfaction < min_satisfaction:
        gate_results.append(f"Satisfaction score {actual_satisfaction} below threshold {min_satisfaction}")
    
    # Check critical bugs
    max_critical_bugs = quality_gates.get("maximum_critical_bugs", 999)
    critical_bugs = len([
        i for i in results.get("issues_found", []) 
        if i.get("severity") == "critical"
    ])
    if critical_bugs > max_critical_bugs:
        gate_results.append(f"Critical bugs {critical_bugs} exceeds threshold {max_critical_bugs}")
    
    # Check accessibility score
    min_accessibility = quality_gates.get("minimum_accessibility_score", 0)
    accessibility_score = results.get("test_phases", {}).get("accessibility", {}).get("accessibility_score", 100)
    if accessibility_score < min_accessibility:
        gate_results.append(f"Accessibility score {accessibility_score} below threshold {min_accessibility}")
    
    if gate_results:
        print("\n❌ QUALITY GATES FAILED:")
        for failure in gate_results:
            print(f"  - {failure}")
        return False
    else:
        print("\n✅ ALL QUALITY GATES PASSED")
        return True

async def main():
    """Main UAT runner function"""
    args = parse_arguments()
    logger = setup_logging(args.log_level)
    
    logger.info("Starting User Acceptance Testing for Zotero Integration")
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        sys.exit(1)
    
    # Apply CLI overrides
    config = apply_cli_overrides(config, args)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if args.generate_report_only:
            logger.info("Generating report from existing results")
            # Load existing results and generate report
            # This would be implemented to load the most recent results
            print("Report generation from existing results not yet implemented")
            return
        
        if args.dry_run:
            logger.info("Running in dry-run mode")
            print("Dry-run mode: Would execute UAT with the following configuration:")
            print(json.dumps(config, indent=2))
            return
        
        # Initialize UAT coordinator
        coordinator = UATCoordinator(args.config)
        
        # Run specific phase or full UAT
        if args.phase == "all":
            logger.info("Running comprehensive UAT")
            results = await coordinator.run_comprehensive_uat()
        else:
            logger.info(f"Running UAT phase: {args.phase}")
            results = await run_specific_phase(coordinator, args.phase)
        
        # Print summary
        print_summary(results, logger)
        
        # Check quality gates
        quality_gates_passed = check_quality_gates(results, config)
        
        # Save final results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_results_file = output_dir / f"uat_final_results_{timestamp}.json"
        
        with open(final_results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Final results saved to {final_results_file}")
        
        # Exit with appropriate code
        if results.get("success") and quality_gates_passed:
            logger.info("UAT completed successfully")
            sys.exit(0)
        else:
            logger.error("UAT failed or quality gates not met")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("UAT interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"UAT failed with unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())