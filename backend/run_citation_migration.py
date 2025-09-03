#!/usr/bin/env python3
"""
Run citation management tables migration
"""
import psycopg2
import os
from dotenv import load_dotenv

def run_migration():
    load_dotenv()
    
    try:
        # Database connection
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'ai_scholar'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        # Read and execute migration
        with open('migrations/005_citation_management_tables.sql', 'r') as f:
            migration_sql = f.read()
        
        with conn.cursor() as cur:
            cur.execute(migration_sql)
            conn.commit()
        
        print('Citation management tables created successfully')
        conn.close()
        return True
        
    except Exception as e:
        print(f'Migration failed: {str(e)}')
        return False

if __name__ == '__main__':
    run_migration()