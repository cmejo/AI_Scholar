#!/usr/bin/env python3
"""
Conflict Cleanup Script for automated scheduling.

Cleans up stale locks, resolves conflicts, and maintains scheduling health.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from .conflict_resolver import ConflictResolver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for conflict cleanup."""
    parser = argparse.ArgumentParser(description="Clean up scheduling conflicts and stale locks")
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be cleaned up without making changes'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force cleanup of all conflicts'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting conflict cleanup")
    
    try:
        # Initialize conflict resolver
        conflict_resolver = ConflictResolver()
        
        if args.dry_run:
            logger.info("DRY RUN - No actual cleanup will be performed")
        
        # Clean up stale locks
        logger.info("Cleaning up stale lock files...")
        if not args.dry_run:
            cleaned_count = conflict_resolver.cleanup_stale_locks()
            logger.info(f"Cleaned up {cleaned_count} stale lock files")
        else:
            logger.info("Would clean up stale lock files")
        
        # Check for current conflicts
        logger.info("Checking for current conflicts...")
        conflicts = await conflict_resolver.detect_conflicts("cleanup_operation")
        
        if conflicts:
            logger.warning(f"Found {len(conflicts)} active conflicts")
            for conflict in conflicts:
                logger.warning(f"  - {conflict.conflict_type.value}: {conflict.description}")
                
                if args.force and not args.dry_run:
                    logger.info(f"Attempting to resolve conflict: {conflict.conflict_type.value}")
                    resolution_result = await conflict_resolver.resolve_conflicts([conflict], "cleanup_operation")
                    if resolution_result.success:
                        logger.info("Conflict resolved successfully")
                    else:
                        logger.warning("Failed to resolve conflict")
        else:
            logger.info("No active conflicts found")
        
        # Get and log statistics
        stats = conflict_resolver.get_conflict_statistics()
        logger.info(f"Conflict resolution statistics:")
        logger.info(f"  Total resolutions: {stats['total_resolutions']}")
        logger.info(f"  Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"  Active locks: {stats['active_locks']}")
        
        logger.info("Conflict cleanup completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Conflict cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)