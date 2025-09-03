#!/usr/bin/env python3
"""
Zotero Integration Database Migration and Upgrade Script

This script handles database schema upgrades for the Zotero integration,
including version tracking, backup creation, and rollback capabilities.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZoteroMigrationManager:
    """Manages Zotero database migrations and upgrades."""
    
    def __init__(self, config_path: str, environment: str = 'production'):
        self.environment = environment
        self.config = self._load_config(config_path)
        self.db_config = self.config['database']['connection']
        self.migrations_dir = Path(__file__).parent
        self.backup_dir = Path('backups') / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Replace environment variables
            config_str = json.dumps(config)
            for key, value in os.environ.items():
                config_str = config_str.replace(f"${{{key}}}", value)
            
            return json.loads(config_str)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
    
    def _get_db_connection(self):
        """Create database connection."""
        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password'],
                sslmode=self.db_config.get('ssl_mode', 'prefer')
            )
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            sys.exit(1)
    
    def _execute_sql_file(self, conn, sql_file: Path):
        """Execute SQL file."""
        try:
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            cursor = conn.cursor()
            cursor.execute(sql_content)
            conn.commit()
            cursor.close()
            
            logger.info(f"Successfully executed: {sql_file.name}")
        except Exception as e:
            logger.error(f"Failed to execute {sql_file.name}: {e}")
            conn.rollback()
            raise
    
    def create_backup(self):
        """Create database backup before migration."""
        logger.info("Creating database backup...")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = self.backup_dir / "database_backup.sql"
        
        try:
            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['username'],
                '-d', self.db_config['database'],
                '-f', str(backup_file),
                '--verbose'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                return False
            
            logger.info(f"Backup created: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def get_current_version(self) -> Optional[str]:
        """Get current schema version."""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Check if version table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'zotero' 
                    AND table_name = 'schema_version'
                );
            """)
            
            if not cursor.fetchone()[0]:
                return None
            
            # Get current version
            cursor.execute("""
                SELECT version FROM zotero.schema_version 
                ORDER BY applied_at DESC LIMIT 1;
            """)
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to get current version: {e}")
            return None
        finally:
            conn.close()
    
    def get_available_migrations(self) -> List[Path]:
        """Get list of available migration files."""
        migration_files = []
        
        # Zotero-specific migrations in order
        migration_names = [
            "001_zotero_integration_foundation.sql",
            "002_zotero_auth_tables.sql",
            "003_zotero_sync_tables.sql",
            "004_zotero_reference_tables.sql",
            "005_citation_management_tables.sql",
            "006_zotero_export_sharing_tables.sql",
            "007_zotero_annotation_sync_tables.sql",
            "008_zotero_monitoring_tables.sql",
            "009_zotero_performance_indexes.sql",
            "010_zotero_security_enhancements.sql"
        ]
        
        for migration_name in migration_names:
            migration_file = self.migrations_dir / migration_name
            if migration_file.exists():
                migration_files.append(migration_file)
        
        return migration_files
    
    def apply_migration(self, migration_file: Path):
        """Apply a single migration."""
        conn = self._get_db_connection()
        try:
            logger.info(f"Applying migration: {migration_file.name}")
            
            # Execute migration
            self._execute_sql_file(conn, migration_file)
            
            # Record migration in version table
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO zotero.schema_version (version, applied_at, migration_file)
                VALUES (%s, %s, %s);
            """, (
                migration_file.stem,
                datetime.now(),
                migration_file.name
            ))
            conn.commit()
            cursor.close()
            
            logger.info(f"Migration {migration_file.name} applied successfully")
            
        except Exception as e:
            logger.error(f"Migration {migration_file.name} failed: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def create_schema_version_table(self):
        """Create schema version tracking table."""
        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Create zotero schema if it doesn't exist
            cursor.execute("CREATE SCHEMA IF NOT EXISTS zotero;")
            
            # Create version tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zotero.schema_version (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    migration_file VARCHAR(255) NOT NULL,
                    UNIQUE(version)
                );
            """)
            
            conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to create schema version table: {e}")
            raise
        finally:
            conn.close()
    
    def upgrade(self, target_version: Optional[str] = None):
        """Upgrade database to target version or latest."""
        logger.info(f"Starting Zotero database upgrade for {self.environment}")
        
        # Create backup if configured
        if self.config['database']['migrations'].get('backup_before_migration', True):
            if not self.create_backup():
                logger.error("Backup failed. Aborting migration.")
                return False
        
        # Create version tracking table
        self.create_schema_version_table()
        
        # Get current version
        current_version = self.get_current_version()
        logger.info(f"Current schema version: {current_version or 'None'}")
        
        # Get available migrations
        migrations = self.get_available_migrations()
        
        if not migrations:
            logger.info("No migrations found")
            return True
        
        # Filter migrations to apply
        migrations_to_apply = []
        for migration in migrations:
            migration_version = migration.stem
            
            # Skip if already applied
            if current_version and migration_version <= current_version:
                continue
            
            # Stop if target version reached
            if target_version and migration_version > target_version:
                break
            
            migrations_to_apply.append(migration)
        
        if not migrations_to_apply:
            logger.info("Database is up to date")
            return True
        
        # Apply migrations
        logger.info(f"Applying {len(migrations_to_apply)} migrations")
        
        for migration in migrations_to_apply:
            try:
                self.apply_migration(migration)
            except Exception as e:
                logger.error(f"Migration failed: {e}")
                logger.info(f"Backup available at: {self.backup_dir}")
                return False
        
        logger.info("Database upgrade completed successfully")
        return True
    
    def rollback(self, target_version: str):
        """Rollback to specific version."""
        logger.info(f"Rolling back to version: {target_version}")
        
        # This is a simplified rollback - in production, you'd want
        # proper down migrations or restore from backup
        backup_file = input("Enter path to backup file for rollback: ")
        
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            cmd = [
                'psql',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['username'],
                '-d', self.db_config['database'],
                '-f', backup_file
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            result = subprocess.run(cmd, env=env)
            
            if result.returncode == 0:
                logger.info("Rollback completed successfully")
                return True
            else:
                logger.error("Rollback failed")
                return False
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def status(self):
        """Show migration status."""
        current_version = self.get_current_version()
        available_migrations = self.get_available_migrations()
        
        print(f"\nZotero Integration Migration Status")
        print(f"Environment: {self.environment}")
        print(f"Current Version: {current_version or 'None'}")
        print(f"Available Migrations: {len(available_migrations)}")
        
        if available_migrations:
            print("\nMigration Files:")
            for migration in available_migrations:
                status = "✓ Applied" if current_version and migration.stem <= current_version else "○ Pending"
                print(f"  {status} {migration.name}")
        
        print()

def main():
    parser = argparse.ArgumentParser(description='Zotero Integration Database Migration Tool')
    parser.add_argument('command', choices=['upgrade', 'rollback', 'status'], 
                       help='Migration command to execute')
    parser.add_argument('--environment', '-e', default='production',
                       choices=['production', 'staging', 'development'],
                       help='Environment to migrate')
    parser.add_argument('--config', '-c', 
                       help='Configuration file path')
    parser.add_argument('--target-version', '-t',
                       help='Target version for upgrade/rollback')
    
    args = parser.parse_args()
    
    # Determine config file
    if args.config:
        config_path = args.config
    else:
        config_path = f"../config/zotero_config.{args.environment}.json"
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    # Create migration manager
    manager = ZoteroMigrationManager(config_path, args.environment)
    
    # Execute command
    try:
        if args.command == 'upgrade':
            success = manager.upgrade(args.target_version)
            sys.exit(0 if success else 1)
        elif args.command == 'rollback':
            if not args.target_version:
                logger.error("Target version required for rollback")
                sys.exit(1)
            success = manager.rollback(args.target_version)
            sys.exit(0 if success else 1)
        elif args.command == 'status':
            manager.status()
            sys.exit(0)
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()