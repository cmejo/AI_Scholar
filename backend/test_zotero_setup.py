#!/usr/bin/env python3
"""
Test script to verify Zotero integration setup
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_zotero_client():
    """Test Zotero API client initialization"""
    try:
        from services.zotero.zotero_client import ZoteroAPIClient
        
        async with ZoteroAPIClient() as client:
            logger.info("✓ Zotero API client initialized successfully")
            return True
    except Exception as e:
        logger.error(f"✗ Zotero API client initialization failed: {e}")
        return False


async def test_zotero_auth_service():
    """Test Zotero authentication service"""
    try:
        from services.zotero.zotero_auth_service import ZoteroAuthService
        
        auth_service = ZoteroAuthService()
        
        # Test state generation
        state = auth_service.generate_oauth_state()
        if len(state) > 20:
            logger.info("✓ OAuth state generation working")
        else:
            logger.error("✗ OAuth state generation failed")
            return False
        
        # Test authorization URL generation
        auth_url = auth_service.get_authorization_url(state, "test-user-id")
        if "zotero.org" in auth_url and "oauth" in auth_url:
            logger.info("✓ OAuth authorization URL generation working")
        else:
            logger.error("✗ OAuth authorization URL generation failed")
            return False
        
        logger.info("✓ Zotero authentication service working")
        return True
        
    except Exception as e:
        logger.error(f"✗ Zotero authentication service failed: {e}")
        return False


def test_database_tables():
    """Test that Zotero database tables exist"""
    try:
        import sqlite3
        
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
        
        # Check citation styles were inserted
        cursor.execute("SELECT COUNT(*) FROM zotero_citation_styles")
        style_count = cursor.fetchone()[0]
        
        if style_count >= 3:
            logger.info(f"✓ Database tables exist with {style_count} citation styles")
        else:
            logger.error(f"✗ Citation styles not properly inserted (found {style_count})")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Database table check failed: {e}")
        return False


def test_pydantic_schemas():
    """Test Zotero Pydantic schemas"""
    try:
        from models.zotero_schemas import (
            ZoteroConnectionCreate,
            ZoteroConnectionResponse,
            ZoteroItemResponse,
            ZoteroSearchRequest,
            CitationRequest
        )
        
        # Test schema creation
        connection_create = ZoteroConnectionCreate(
            connection_type="api_key",
            api_key="test-key",
            zotero_user_id="12345"
        )
        
        search_request = ZoteroSearchRequest(
            query="machine learning",
            limit=10
        )
        
        citation_request = CitationRequest(
            item_ids=["item1", "item2"],
            citation_style="apa"
        )
        
        logger.info("✓ Pydantic schemas working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Pydantic schemas test failed: {e}")
        return False


def test_configuration():
    """Test Zotero configuration settings"""
    try:
        # Simple config test without importing the full settings
        import os
        
        # Check if Zotero directories exist
        attachments_dir = Path("backend/zotero_attachments")
        if attachments_dir.exists():
            logger.info("✓ Zotero attachments directory exists")
        else:
            logger.warning("⚠ Zotero attachments directory not found")
        
        logger.info("✓ Configuration check completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("Starting Zotero integration setup tests...")
    
    tests = [
        ("Database Tables", test_database_tables),
        ("Pydantic Schemas", test_pydantic_schemas),
        ("Configuration", test_configuration),
        ("Zotero API Client", test_zotero_client),
        ("Zotero Auth Service", test_zotero_auth_service),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
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
        logger.info("🎉 All Zotero integration setup tests passed!")
        return True
    else:
        logger.error(f"❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)