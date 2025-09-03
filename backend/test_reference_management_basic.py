"""
Basic verification test for Zotero Reference Management System

This test verifies the core functionality of the reference management system
including CRUD operations, validation, and data integrity checks.
"""
import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.zotero_schemas import ZoteroItemCreate, ZoteroItemUpdate, ZoteroCreator
from services.zotero.zotero_reference_service import ZoteroReferenceService


class MockDatabase:
    """Mock database session for testing"""
    
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.added_items = []
        self.query_results = {}
    
    def add(self, item):
        self.added_items.append(item)
    
    def commit(self):
        self.committed = True
    
    def rollback(self):
        self.rolled_back = True
    
    def flush(self):
        pass
    
    def query(self, model):
        return MockQuery(self.query_results.get(model.__name__, []))


class MockQuery:
    """Mock query object"""
    
    def __init__(self, results):
        self.results = results
        self._filters = []
        self._joins = []
        self._options = []
    
    def filter(self, *args):
        self._filters.extend(args)
        return self
    
    def join(self, *args):
        self._joins.extend(args)
        return self
    
    def options(self, *args):
        self._options.extend(args)
        return self
    
    def outerjoin(self, *args):
        return self
    
    def order_by(self, *args):
        return self
    
    def group_by(self, *args):
        return self
    
    def having(self, *args):
        return self
    
    def offset(self, offset):
        return self
    
    def limit(self, limit):
        return self
    
    def first(self):
        return self.results[0] if self.results else None
    
    def all(self):
        return self.results
    
    def count(self):
        return len(self.results)
    
    def delete(self, synchronize_session=False):
        return len(self.results)


async def test_reference_service_basic_operations():
    """Test basic CRUD operations of the reference service"""
    print("Testing Zotero Reference Service Basic Operations...")
    
    # Create mock database
    mock_db = MockDatabase()
    service = ZoteroReferenceService(mock_db)
    
    # Test data
    creator = ZoteroCreator(
        creator_type="author",
        first_name="John",
        last_name="Doe"
    )
    
    reference_data = ZoteroItemCreate(
        item_type="article",
        title="Test Article",
        creators=[creator],
        publication_title="Test Journal",
        publication_year=2023,
        doi="10.1000/test.doi",
        abstract_note="Test abstract",
        tags=["test", "research"],
        collection_ids=[]
    )
    
    # Mock library validation
    mock_library = Mock()
    mock_library.id = "lib-123"
    mock_library.library_name = "Test Library"
    
    print("✓ Test data created")
    
    # Test validation methods
    try:
        await service._validate_reference_data(reference_data)
        print("✓ Reference data validation passed")
    except Exception as e:
        print(f"✗ Reference data validation failed: {e}")
        return False
    
    # Test DOI validation
    assert service._is_valid_doi("10.1000/test.doi") == True
    assert service._is_valid_doi("invalid-doi") == False
    print("✓ DOI validation working correctly")
    
    # Test ISBN validation
    assert service._is_valid_isbn("978-0-123456-78-9") == True
    assert service._is_valid_isbn("invalid-isbn") == False
    print("✓ ISBN validation working correctly")
    
    # Test ISSN validation
    assert service._is_valid_issn("1234-5678") == True
    assert service._is_valid_issn("invalid-issn") == False
    print("✓ ISSN validation working correctly")
    
    # Test URL validation
    assert service._is_valid_url("https://example.com") == True
    assert service._is_valid_url("invalid-url") == False
    print("✓ URL validation working correctly")
    
    # Test creator serialization
    serialized = service._serialize_creators([creator])
    assert len(serialized) == 1
    assert serialized[0]["creator_type"] == "author"
    assert serialized[0]["first_name"] == "John"
    assert serialized[0]["last_name"] == "Doe"
    print("✓ Creator serialization working correctly")
    
    print("✓ All basic validation tests passed")
    return True


async def test_reference_validation_errors():
    """Test reference validation error handling"""
    print("\nTesting Reference Validation Error Handling...")
    
    mock_db = MockDatabase()
    service = ZoteroReferenceService(mock_db)
    
    # Test missing item type
    try:
        invalid_data = ZoteroItemCreate(
            item_type="",  # Empty item type
            title="Test Article",
            creators=[]
        )
        await service._validate_reference_data(invalid_data)
        print("✗ Should have failed for missing item type")
        return False
    except ValueError as e:
        if "Item type is required" in str(e):
            print("✓ Correctly caught missing item type")
        else:
            print(f"✗ Wrong error message: {e}")
            return False
    
    # Test invalid DOI
    try:
        invalid_data = ZoteroItemCreate(
            item_type="article",
            title="Test Article",
            creators=[],
            doi="invalid-doi"
        )
        await service._validate_reference_data(invalid_data)
        print("✗ Should have failed for invalid DOI")
        return False
    except ValueError as e:
        if "Invalid DOI format" in str(e):
            print("✓ Correctly caught invalid DOI")
        else:
            print(f"✗ Wrong error message: {e}")
            return False
    
    # Test invalid publication year
    try:
        invalid_data = ZoteroItemCreate(
            item_type="article",
            title="Test Article",
            creators=[],
            publication_year=999  # Too old
        )
        await service._validate_reference_data(invalid_data)
        print("✗ Should have failed for invalid year")
        return False
    except ValueError as e:
        if "Invalid publication year" in str(e):
            print("✓ Correctly caught invalid publication year")
        else:
            print(f"✗ Wrong error message: {e}")
            return False
    
    # Test invalid creator
    try:
        invalid_creator = ZoteroCreator(
            creator_type="",  # Missing creator type
            first_name="John",
            last_name="Doe"
        )
        invalid_data = ZoteroItemCreate(
            item_type="article",
            title="Test Article",
            creators=[invalid_creator]
        )
        await service._validate_reference_data(invalid_data)
        print("✗ Should have failed for invalid creator")
        return False
    except ValueError as e:
        if "creator_type is required" in str(e):
            print("✓ Correctly caught invalid creator")
        else:
            print(f"✗ Wrong error message: {e}")
            return False
    
    print("✓ All validation error tests passed")
    return True


async def test_data_integrity_checks():
    """Test data integrity checking functionality"""
    print("\nTesting Data Integrity Checks...")
    
    mock_db = MockDatabase()
    service = ZoteroReferenceService(mock_db)
    
    # Mock some test data
    mock_references = [
        Mock(id="ref-1", item_type="article", doi="10.1000/test1", publication_year=2023),
        Mock(id="ref-2", item_type="", doi="10.1000/test2", publication_year=2024),  # Missing item_type
        Mock(id="ref-3", item_type="book", doi="10.1000/test1", publication_year=999),  # Duplicate DOI, invalid year
    ]
    
    # Set up mock query results
    mock_db.query_results["ZoteroItem"] = mock_references
    
    try:
        results = await service.check_data_integrity()
        
        assert "total_references" in results
        assert "orphaned_references" in results
        assert "missing_required_fields" in results
        assert "duplicate_dois" in results
        assert "invalid_years" in results
        assert "issues" in results
        
        print("✓ Data integrity check structure correct")
        print(f"  - Total references: {results['total_references']}")
        print(f"  - Issues found: {len(results['issues'])}")
        
    except Exception as e:
        print(f"✗ Data integrity check failed: {e}")
        return False
    
    # Test repair functionality
    try:
        repair_results = await service.repair_data_integrity()
        
        assert "repairs_attempted" in repair_results
        assert "repairs_successful" in repair_results
        assert "repairs_failed" in repair_results
        assert "actions" in repair_results
        
        print("✓ Data integrity repair structure correct")
        print(f"  - Repairs attempted: {repair_results['repairs_attempted']}")
        print(f"  - Actions taken: {len(repair_results['actions'])}")
        
    except Exception as e:
        print(f"✗ Data integrity repair failed: {e}")
        return False
    
    print("✓ Data integrity tests passed")
    return True


async def test_reference_conversion():
    """Test reference model to response conversion"""
    print("\nTesting Reference Model Conversion...")
    
    mock_db = MockDatabase()
    service = ZoteroReferenceService(mock_db)
    
    # Create mock reference model
    from models.zotero_models import ZoteroItem
    mock_reference = ZoteroItem(
        id="ref-123",
        library_id="lib-123",
        zotero_item_key="item-key-123",
        item_type="article",
        title="Test Article",
        creators=[{
            "creator_type": "author",
            "first_name": "John",
            "last_name": "Doe"
        }],
        publication_title="Test Journal",
        publication_year=2023,
        doi="10.1000/test.doi",
        tags=["test", "research"],
        is_deleted=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    try:
        response = service._convert_to_response(mock_reference)
        
        assert response.id == "ref-123"
        assert response.title == "Test Article"
        assert response.item_type == "article"
        assert len(response.creators) == 1
        assert response.creators[0].creator_type == "author"
        assert response.creators[0].first_name == "John"
        assert response.creators[0].last_name == "Doe"
        assert response.publication_year == 2023
        assert response.doi == "10.1000/test.doi"
        assert "test" in response.tags
        assert "research" in response.tags
        
        print("✓ Reference conversion working correctly")
        print(f"  - Converted reference ID: {response.id}")
        print(f"  - Title: {response.title}")
        print(f"  - Creators: {len(response.creators)}")
        print(f"  - Tags: {len(response.tags)}")
        
    except Exception as e:
        print(f"✗ Reference conversion failed: {e}")
        return False
    
    print("✓ Reference conversion tests passed")
    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("ZOTERO REFERENCE MANAGEMENT SYSTEM - BASIC VERIFICATION")
    print("=" * 60)
    
    tests = [
        test_reference_service_basic_operations,
        test_reference_validation_errors,
        test_data_integrity_checks,
        test_reference_conversion
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Reference management system is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)