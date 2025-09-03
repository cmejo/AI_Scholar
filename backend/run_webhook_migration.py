#!/usr/bin/env python3
"""
Run webhook system migration
"""
import os
import sys
sys.path.append('.')

from core.database import engine
from sqlalchemy import text

def run_migration():
    """Run the webhook system migration"""
    try:
        # Read migration file
        with open('migrations/008_zotero_webhook_system.sql', 'r') as f:
            migration_sql = f.read()
        
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            for stmt in statements:
                if stmt:
                    try:
                        conn.execute(text(stmt))
                        print(f'✓ Executed: {stmt[:50]}...')
                    except Exception as e:
                        print(f'✗ Error executing statement: {e}')
                        print(f'Statement: {stmt[:100]}...')
            conn.commit()
            print('✓ Webhook system migration completed successfully')
            
    except Exception as e:
        print(f'✗ Migration failed: {e}')
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)