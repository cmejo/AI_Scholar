#!/usr/bin/env python3
"""
Health Check Script for multi-instance ArXiv system.

Runs comprehensive health checks and reports system status.
Can be used standalone or as part of automated scheduling.
"""

import asyncio
import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from health_checker import HealthChecker
from ..shared.multi_instance_data_models import InstanceConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_instance_configs(config_dir: str) -> list:
    """Load instance configurations from directory."""
    configs = []
    config_path = Path(config_dir)
    
    if not config_path.exists():
        logger.warning(f"Configuration directory not found: {config_dir}")
        return configs
    
    # Look for YAML configuration files
    for config_file in config_path.glob("*.yaml"):
        try:
            import yaml
            
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Create basic config for health check (simplified)
            instance_name = config_data.get('instance', {}).get('name', config_file.stem)
            configs.append({'instance_name': instance_name})
            
            logger.info(f"Loaded configuration for instance: {instance_name}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
    
    return configs


async def main():
    """Main entry point for health check."""
    parser = argparse.ArgumentParser(description="Run health check for multi-instance ArXiv system")
    
    parser.add_argument(
        '--config-dir',
        type=str,
        default='/etc/multi_instance_arxiv/instances',
        help='Directory containing instance configuration files'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Output file for health check results (JSON format)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--check-instances',
        action='store_true',
        help='Include instance-specific health checks'
    )
    
    parser.add_argument(
        '--exit-on-failure',
        action='store_true',
        help='Exit with non-zero code if health check fails'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting health check")
    
    try:
        # Initialize health checker
        health_checker = HealthChecker()
        
        # Load instance configurations if requested
        instance_configs = None
        if args.check_instances:
            configs = load_instance_configs(args.config_dir)
            if configs:
                # Convert to simplified InstanceConfig objects for health check
                instance_configs = []
                for config in configs:
                    # Create minimal config for health check
                    instance_configs.append(type('InstanceConfig', (), config)())
        
        # Run comprehensive health check
        health_status = await health_checker.run_comprehensive_health_check(instance_configs)
        
        # Determine if system is ready
        is_ready, blocking_issues = health_checker.is_system_ready_for_update(health_status)
        
        # Print results
        print(f"\n=== Health Check Results ===")
        print(f"Overall Status: {health_status.overall_status.upper()}")
        print(f"System Ready for Updates: {'YES' if is_ready else 'NO'}")
        
        if blocking_issues:
            print(f"\nBlocking Issues:")
            for issue in blocking_issues:
                print(f"  - {issue}")
        
        print(f"\nDetailed Results:")
        for result in health_status.check_results:
            status_symbol = "✓" if result.status == 'healthy' else "⚠" if result.status == 'warning' else "✗"
            print(f"  {status_symbol} {result.check_name}: {result.message}")
        
        # Save results to file if requested
        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(health_status.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Health check results saved to {output_path}")
        
        # Exit with appropriate code
        if args.exit_on_failure and not is_ready:
            logger.error("Health check failed - exiting with error code")
            return 1
        
        logger.info("Health check completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)