#!/usr/bin/env python3
"""
Basic test script to verify Zotero integration foundation setup
"""
import logging
import sys
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_tables():
    """Test that Zotero database tables exist and are properly structured"""
    try:
        conn = sqlite3.connect("ai_scholar.db")
        cursor = conn.cursor()
        
        # Check for Zotero tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'zotero_%'")
        tables = cursor.fetchall()
        
        expected_tables = [
            'zotero_connections',
            'zotero_libraries',
            'zotero_collections',
            'zotero_items',
            'zotero_item_collections',
            'zotero_attachments',
            'zotero_annotations',
            'zotero_sync_log',
            'zotero_citation_styles',
            'zotero_user_preferences'
        ]
        
        table_names = [table[0] for table in tables]
        
        missing_tables = []
        for expected_table in expected_tables:
            if expected_table not in table_names:
                missing_tables.append(expected_table)
        
        if missing_tables:
            logger.error(f"✗ Missing database tables: {missing_tables}")
            return False
        
        logger.info(f"✓ All {len(expected_tables)} Zotero tables exist")
        
        # Test table structure by checking key columns
        test_queries = [
            ("zotero_connections", "SELECT user_id, zotero_user_id, access_token, connection_type FROM zotero_connections LIMIT 0"),
            ("zotero_items", "SELECT title, creators, publication_year, doi FROM zotero_items LIMIT 0"),
            ("zotero_citation_styles", "SELECT style_name, style_title, csl_content FROM zotero_citation_styles LIMIT 0")
        ]
        
        for table_name, query in test_queries:
            try:
                cursor.execute(query)
                logger.info(f"✓ {table_name} table structure is correct")
            except Exception as e:
                logger.error(f"✗ {table_name} table structure issue: {e}")
                return False
        
        # Check citation styles were inserted
        cursor.execute("SELECT COUNT(*) FROM zotero_citation_styles")
        style_count = cursor.fetchone()[0]
        
        if style_count >= 3:
            logger.info(f"✓ {style_count} default citation styles inserted")
        else:
            logger.error(f"✗ Citation styles not properly inserted (found {style_count})")
            return False
        
        # Test foreign key relationships by checking table schema
        cursor.execute("PRAGMA foreign_key_list(zotero_libraries)")
        fk_info = cursor.fetchall()
        if fk_info:
            logger.info("✓ Foreign key relationships are defined")
        else:
            logger.warning("⚠ Foreign key relationships may not be properly defined")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Database table check failed: {e}")
        return False


def test_pydantic_schemas():
    """Test Zotero Pydantic schemas without SQLAlchemy dependencies"""
    try:
        # Add backend directory to path
        backend_dir = Path(__file__).parent
        sys.path.insert(0, str(backend_dir))
        
        from models.zotero_schemas import (
            ZoteroConnectionCreate,
            ZoteroSearchRequest,
            CitationRequest,
            ConnectionType,
            SyncType
        )
        
        # Test enum values
        assert ConnectionType.OAUTH == "oauth"
        assert ConnectionType.API_KEY == "api_key"
        assert SyncType.FULL == "full"
        logger.info("✓ Zotero enums working correctly")
        
        # Test schema creation and validation
        connection_create = ZoteroConnectionCreate(
            connection_type=ConnectionType.API_KEY,
            api_key="test-key-12345",
            zotero_user_id="67890"
        )
        assert connection_create.connection_type == "api_key"
        assert connection_create.api_key == "test-key-12345"
        logger.info("✓ ZoteroConnectionCreate schema working")
        
        search_request = ZoteroSearchRequest(
            query="artificial intelligence",
            limit=25,
            offset=10,
            sort_by="date",
            sort_order="desc"
        )
        assert search_request.query == "artificial intelligence"
        assert search_request.limit == 25
        logger.info("✓ ZoteroSearchRequest schema working")
        
        citation_request = CitationRequest(
            item_ids=["ABC123", "DEF456", "GHI789"],
            citation_style="apa",
            format="html",
            locale="en-US"
        )
        assert len(citation_request.item_ids) == 3
        assert citation_request.citation_style == "apa"
        logger.info("✓ CitationRequest schema working")
        
        # Test validation
        try:
            invalid_search = ZoteroSearchRequest(query="")  # Empty query should fail
            logger.error("✗ Schema validation not working - empty query accepted")
            return False
        except Exception:
            logger.info("✓ Schema validation working - empty query rejected")
        
        logger.info("✓ All Pydantic schemas working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Pydantic schemas test failed: {e}")
        return False


def test_file_structure():
    """Test that all required files and directories exist"""
    try:
        backend_dir = Path(__file__).parent
        
        required_files = [
            "migrations/001_zotero_integration_foundation.sql",
            "models/zotero_models.py",
            "models/zotero_schemas.py",
            "services/zotero/__init__.py",
            "services/zotero/zotero_client.py",
            "services/zotero/zotero_auth_service.py",
            "api/zotero_endpoints.py",
            "create_zotero_tables.py"
        ]
        
        required_dirs = [
            "zotero_attachments",
            "services/zotero"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = backend_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = backend_dir / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if missing_files:
            logger.error(f"✗ Missing required files: {missing_files}")
            return False
        
        if missing_dirs:
            logger.error(f"✗ Missing required directories: {missing_dirs}")
            return False
        
        logger.info(f"✓ All {len(required_files)} required files exist")
        logger.info(f"✓ All {len(required_dirs)} required directories exist")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ File structure test failed: {e}")
        return False


def test_configuration_files():
    """Test that configuration files have been updated"""
    try:
        backend_dir = Path(__file__).parent
        
        # Check if config.py has Zotero settings
        config_file = backend_dir / "core" / "config.py"
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_content = f.read()
            
            if "ZOTERO_CLIENT_ID" in config_content and "ZOTERO_API_BASE_URL" in config_content:
                logger.info("✓ Zotero configuration added to config.py")
            else:
                logger.error("✗ Zotero configuration missing from config.py")
                return False
        else:
            logger.error("✗ config.py file not found")
            return False
        
        # Check if .env has Zotero settings
        env_file = backend_dir.parent / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            if "ZOTERO_CLIENT_ID" in env_content and "ZOTERO_CLIENT_SECRET" in env_content:
                logger.info("✓ Zotero configuration added to .env")
            else:
                logger.error("✗ Zotero configuration missing from .env")
                return False
        else:
            logger.warning("⚠ .env file not found")
        
        # Check if app.py includes Zotero router
        app_file = backend_dir / "app.py"
        if app_file.exists():
            with open(app_file, 'r') as f:
                app_content = f.read()
            
            if "zotero_router" in app_content and "include_router(zotero_router)" in app_content:
                logger.info("✓ Zotero router added to app.py")
            else:
                logger.error("✗ Zotero router not properly added to app.py")
                return False
        else:
            logger.error("✗ app.py file not found")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration files test failed: {e}")
        return False


def main():
    """Run all basic tests"""
    logger.info("Starting Zotero integration foundation tests...")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Database Tables", test_database_tables),
        ("Pydantic Schemas", test_pydantic_schemas),
        ("Configuration Files", test_configuration_files),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} test crashed: {e}")
            failed += 1
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("🎉 All Zotero integration foundation tests passed!")
        logger.info("\nNext steps:")
        logger.info("1. Configure Zotero OAuth credentials in .env file")
        logger.info("2. Test the API endpoints with a real Zotero account")
        logger.info("3. Implement the remaining service methods")
        return True
    else:
        logger.error(f"❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)