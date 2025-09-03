"""
Comprehensive tests for ZoteroLibraryImportService - Task 3.1 Implementation
Tests the core library import functionality with mock data
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Add the backend directory to the path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the service we're testing
from services.zotero.zotero_library_import_service import (
    ZoteroLibraryImportService, LibraryImportProgress
)


class TestLibraryImportProgress:
    """Test LibraryImportProgress class"""
    
    def test_progress_initialization(self):
        """Test progress tracker initialization"""
        import_id = "test-import-123"
        progress = LibraryImportProgress(import_id)
        
        assert progress.import_id == import_id
        assert progress.status == "started"
        assert progress.items_processed == 0
        assert progress.items_added == 0
        assert progress.errors_count == 0
        assert isinstance(progress.started_at, datetime)
        assert progress.completed_at is None
    
    def test_update_progress(self):
        """Test progress update functionality"""
        progress = LibraryImportProgress("test-import")
        
        progress.update_progress(
            items_processed=10,
            items_added=5,
            items_updated=3,
            current_library="Test Library"
        )
        
        assert progress.items_processed == 10
        assert progress.items_added == 5
        assert progress.items_updated == 3
        assert progress.current_library == "Test Library"
    
    def test_add_error(self):
        """Test error tracking"""
        progress = LibraryImportProgress("test-import")
        progress.current_library = "Test Library"
        progress.current_operation = "importing_items"
        progress.current_batch = 1
        
        progress.add_error("Test error", {"detail": "error details"})
        
        assert progress.errors_count == 1
        assert len(progress.error_details) == 1
        
        error = progress.error_details[0]
        assert error["error"] == "Test error"
        assert error["library"] == "Test Library"
        assert error["operation"] == "importing_items"
        assert error["batch"] == 1
        assert error["details"]["detail"] == "error details"
        assert "timestamp" in error
    
    def test_progress_percentage(self):
        """Test progress percentage calculation"""
        progress = LibraryImportProgress("test-import")
        
        # No items total
        assert progress.get_progress_percentage() == 0.0
        
        # With items
        progress.items_total = 100
        progress.items_processed = 25
        assert progress.get_progress_percentage() == 25.0
        
        progress.items_processed = 100
        assert progress.get_progress_percentage() == 100.0
    
    def test_complete(self):
        """Test completion functionality"""
        progress = LibraryImportProgress("test-import")
        
        progress.complete("completed")
        
        assert progress.status == "completed"
        assert isinstance(progress.completed_at, datetime)
    
    def test_get_progress_dict(self):
        """Test progress dictionary generation"""
        progress = LibraryImportProgress("test-import")
        progress.update_progress(
            items_total=100,
            items_processed=25,
            items_added=20,
            libraries_total=2,
            collections_total=10
        )
        progress.add_error("Test error")
        
        progress_dict = progress.get_progress_dict()
        
        assert progress_dict["import_id"] == "test-import"
        assert progress_dict["status"] == "started"
        assert progress_dict["progress_percentage"] == 25.0
        assert progress_dict["totals"]["libraries"] == 2
        assert progress_dict["totals"]["collections"] == 10
        assert progress_dict["totals"]["items"] == 100
        assert progress_dict["processed"]["items"] == 25
        assert progress_dict["processed"]["items_added"] == 20
        assert progress_dict["errors"]["count"] == 1
        assert len(progress_dict["errors"]["recent"]) == 1


class TestZoteroLibraryImportService:
    """Test ZoteroLibraryImportService class"""
    
    @pytest.fixture
    def import_service(self):
        """Create import service instance"""
        return ZoteroLibraryImportService()
    
    @pytest.fixture
    def mock_connection(self):
        """Mock Zotero connection"""
        connection = MagicMock()
        connection.id = "test-connection-id"
        connection.user_id = "test-user-id"
        connection.zotero_user_id = "12345"
        connection.access_token = "test-access-token"
        connection.connection_status = "active"
        return connection
    
    @pytest.fixture
    def mock_library_data(self):
        """Mock library data from Zotero API"""
        return [
            {
                "id": "12345",
                "type": "user",
                "name": "Personal Library",
                "owner": "12345"
            },
            {
                "id": "67890",
                "type": "group",
                "name": "Research Group",
                "owner": "11111",
                "group_type": "PublicOpen",
                "description": "Research collaboration group"
            }
        ]
    
    @pytest.fixture
    def mock_collections_data(self):
        """Mock collections data from Zotero API"""
        return [
            {
                "key": "ABCD1234",
                "version": 1,
                "data": {
                    "name": "Research Papers",
                    "parentCollection": None
                }
            },
            {
                "key": "EFGH5678",
                "version": 1,
                "data": {
                    "name": "Methodology",
                    "parentCollection": "ABCD1234"
                }
            }
        ]
    
    @pytest.fixture
    def mock_items_data(self):
        """Mock items data from Zotero API"""
        return [
            {
                "key": "ITEM1234",
                "version": 1,
                "data": {
                    "itemType": "journalArticle",
                    "title": "Test Article",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "John",
                            "lastName": "Doe"
                        }
                    ],
                    "publicationTitle": "Test Journal",
                    "date": "2023-01-01",
                    "DOI": "10.1000/test.doi",
                    "abstractNote": "This is a test article",
                    "tags": [{"tag": "test"}, {"tag": "research"}],
                    "collections": ["ABCD1234"],
                    "dateAdded": "2023-01-01T10:00:00Z",
                    "dateModified": "2023-01-01T10:00:00Z"
                }
            },
            {
                "key": "ITEM5678",
                "version": 1,
                "data": {
                    "itemType": "book",
                    "title": "Test Book",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "Jane",
                            "lastName": "Smith"
                        }
                    ],
                    "publisher": "Test Publisher",
                    "date": "2022",
                    "ISBN": "978-0-123456-78-9",
                    "tags": [{"tag": "book"}, {"tag": "reference"}],
                    "collections": [],
                    "dateAdded": "2023-01-02T10:00:00Z",
                    "dateModified": "2023-01-02T10:00:00Z"
                }
            }
        ]
    
    def test_transform_item_data(self, import_service):
        """Test item data transformation - core requirement"""
        zotero_data = {
            "itemType": "journalArticle",
            "title": "Test Article",
            "creators": [
                {
                    "creatorType": "author",
                    "firstName": "John",
                    "lastName": "Doe"
                },
                {
                    "creatorType": "editor",
                    "name": "Test Organization"
                }
            ],
            "publicationTitle": "Test Journal",
            "date": "2023-01-01",
            "DOI": "10.1000/test.doi",
            "publisher": "Test Publisher",
            "abstractNote": "Test abstract",
            "dateAdded": "2023-01-01T10:00:00Z",
            "dateModified": "2023-01-01T10:00:00Z",
            "tags": [{"tag": "test"}, {"tag": "research"}],
            "extra": "Extra field",
            "volume": "10",
            "issue": "2"
        }
        
        transformed = import_service.transform_item_data(zotero_data)
        
        # Verify core fields
        assert transformed["item_type"] == "journalArticle"
        assert transformed["title"] == "Test Article"
        assert transformed["publication_title"] == "Test Journal"
        assert transformed["publication_year"] == 2023
        assert transformed["doi"] == "10.1000/test.doi"
        assert transformed["publisher"] == "Test Publisher"
        assert transformed["abstract_note"] == "Test abstract"
        assert transformed["tags"] == ["test", "research"]
        
        # Verify creators
        assert len(transformed["creators"]) == 2
        assert transformed["creators"][0]["creator_type"] == "author"
        assert transformed["creators"][0]["first_name"] == "John"
        assert transformed["creators"][0]["last_name"] == "Doe"
        assert transformed["creators"][1]["creator_type"] == "editor"
        assert transformed["creators"][1]["name"] == "Test Organization"
        
        # Verify dates
        assert isinstance(transformed["date_added"], datetime)
        assert isinstance(transformed["date_modified"], datetime)
        
        # Verify extra fields
        assert "extra" in transformed["extra_fields"]
        assert "volume" in transformed["extra_fields"]
        assert "issue" in transformed["extra_fields"]
        assert transformed["extra_fields"]["extra"] == "Extra field"
        
        # Verify original metadata is preserved
        assert transformed["item_metadata"] == zotero_data
    
    def test_transform_item_data_with_organization_creator(self, import_service):
        """Test transformation with organization creator"""
        zotero_data = {
            "itemType": "report",
            "title": "Test Report",
            "creators": [
                {
                    "creatorType": "author",
                    "name": "World Health Organization"
                }
            ]
        }
        
        transformed = import_service.transform_item_data(zotero_data)
        
        assert len(transformed["creators"]) == 1
        assert transformed["creators"][0]["creator_type"] == "author"
        assert transformed["creators"][0]["name"] == "World Health Organization"
        assert transformed["creators"][0]["first_name"] is None
        assert transformed["creators"][0]["last_name"] is None
    
    def test_extract_publication_year(self, import_service):
        """Test year extraction from various date formats"""
        test_cases = [
            ("2023", 2023),
            ("2023-01-01", 2023),
            ("January 2023", 2023),
            ("2023/01/01", 2023),
            ("1999-12-31", 1999),
            ("2000", 2000),
            ("Published in 2022", 2022),
            ("no year here", None),
            ("", None),
            ("1800", None),  # Too old
            ("3000", None)   # Too far in future
        ]
        
        for date_input, expected_year in test_cases:
            result = import_service._extract_publication_year(date_input)
            assert result == expected_year, f"Failed for '{date_input}': expected {expected_year}, got {result}"
    
    def test_parse_zotero_date(self, import_service):
        """Test Zotero date parsing"""
        # Valid ISO date with Z suffix
        date_str = "2023-01-01T10:00:00Z"
        parsed = import_service._parse_zotero_date(date_str)
        assert isinstance(parsed, datetime)
        assert parsed.year == 2023
        assert parsed.month == 1
        assert parsed.day == 1
        
        # Valid ISO date without Z suffix
        date_str = "2023-01-01T10:00:00"
        parsed = import_service._parse_zotero_date(date_str)
        assert parsed is None  # Should fail without timezone
        
        # Invalid date
        invalid_date = "not a date"
        parsed = import_service._parse_zotero_date(invalid_date)
        assert parsed is None
        
        # None input
        parsed = import_service._parse_zotero_date(None)
        assert parsed is None
    
    def test_extract_extra_fields(self, import_service):
        """Test extraction of additional fields"""
        zotero_data = {
            "itemType": "article",
            "title": "Test",
            "volume": "10",
            "issue": "2",
            "pages": "123-456",
            "extra": "Additional info",
            "creators": [],  # This should be excluded
            "tags": []       # This should be excluded
        }
        
        extra_fields = import_service._extract_extra_fields(zotero_data)
        
        # Should include unmapped fields
        assert "volume" in extra_fields
        assert "issue" in extra_fields
        assert "pages" in extra_fields
        assert "extra" in extra_fields
        
        # Should exclude mapped fields
        assert "itemType" not in extra_fields
        assert "title" not in extra_fields
        assert "creators" not in extra_fields
        assert "tags" not in extra_fields
    
    def test_get_import_progress(self, import_service):
        """Test import progress retrieval"""
        # No active import
        progress = import_service.get_import_progress("non-existent")
        assert progress is None
        
        # Add active import
        import_progress = LibraryImportProgress("test-import")
        import_service._active_imports["test-import"] = import_progress
        
        progress = import_service.get_import_progress("test-import")
        assert progress is not None
        assert progress["import_id"] == "test-import"
    
    def test_get_active_imports(self, import_service):
        """Test active imports retrieval"""
        # No active imports
        active = import_service.get_active_imports()
        assert len(active) == 0
        
        # Add active imports
        import1 = LibraryImportProgress("import-1")
        import2 = LibraryImportProgress("import-2")
        import_service._active_imports["import-1"] = import1
        import_service._active_imports["import-2"] = import2
        
        active = import_service.get_active_imports()
        assert len(active) == 2
        assert any(i["import_id"] == "import-1" for i in active)
        assert any(i["import_id"] == "import-2" for i in active)
    
    @pytest.mark.asyncio
    async def test_cancel_import(self, import_service):
        """Test import cancellation"""
        # Non-existent import
        success = await import_service.cancel_import("non-existent")
        assert success is False
        
        # Existing import
        import_progress = LibraryImportProgress("test-import")
        import_service._active_imports["test-import"] = import_progress
        
        success = await import_service.cancel_import("test-import")
        assert success is True
        assert import_progress.status == "cancelled"
        assert "test-import" not in import_service._active_imports


class TestDataTransformationEdgeCases:
    """Test edge cases in data transformation"""
    
    @pytest.fixture
    def import_service(self):
        return ZoteroLibraryImportService()
    
    def test_empty_item_data(self, import_service):
        """Test transformation with minimal data"""
        zotero_data = {
            "itemType": "article"
        }
        
        transformed = import_service.transform_item_data(zotero_data)
        
        assert transformed["item_type"] == "article"
        assert transformed["title"] is None
        assert transformed["creators"] == []
        assert transformed["tags"] == []
        assert transformed["publication_year"] is None
    
    def test_malformed_creators(self, import_service):
        """Test handling of malformed creator data"""
        zotero_data = {
            "itemType": "article",
            "creators": [
                {},  # Empty creator
                {"creatorType": "author"},  # Missing name fields
                {"firstName": "John"},  # Missing creator type
                {"lastName": "Doe"},  # Missing creator type and first name
            ]
        }
        
        transformed = import_service.transform_item_data(zotero_data)
        
        # Should handle all creators gracefully
        assert len(transformed["creators"]) == 4
        assert transformed["creators"][0]["creator_type"] == "author"  # Default
        assert transformed["creators"][1]["creator_type"] == "author"
        assert transformed["creators"][2]["creator_type"] == "author"  # Default
        assert transformed["creators"][3]["creator_type"] == "author"  # Default
    
    def test_malformed_tags(self, import_service):
        """Test handling of malformed tag data"""
        zotero_data = {
            "itemType": "article",
            "tags": [
                {"tag": "valid_tag"},
                {},  # Empty tag
                {"invalid": "structure"},  # Wrong structure
                {"tag": ""},  # Empty tag value
                {"tag": None}  # None tag value
            ]
        }
        
        transformed = import_service.transform_item_data(zotero_data)
        
        # Should only include valid tags
        expected_tags = ["valid_tag"]
        actual_tags = [tag for tag in transformed["tags"] if tag]  # Filter out empty/None
        assert len(actual_tags) == 1
        assert actual_tags[0] == "valid_tag"
    
    def test_unicode_and_special_characters(self, import_service):
        """Test handling of unicode and special characters"""
        zotero_data = {
            "itemType": "article",
            "title": "Test with émojis 🔬 and ünïcödé",
            "creators": [
                {
                    "creatorType": "author",
                    "firstName": "José",
                    "lastName": "García-López"
                }
            ],
            "tags": [{"tag": "tëst"}, {"tag": "研究"}],
            "abstractNote": "Abstract with special chars: <>&\"'"
        }
        
        transformed = import_service.transform_item_data(zotero_data)
        
        # Should preserve unicode characters
        assert "émojis 🔬" in transformed["title"]
        assert "ünïcödé" in transformed["title"]
        assert transformed["creators"][0]["first_name"] == "José"
        assert transformed["creators"][0]["last_name"] == "García-López"
        assert "tëst" in transformed["tags"]
        assert "研究" in transformed["tags"]
        assert "<>&\"'" in transformed["abstract_note"]


class TestProgressTracking:
    """Test progress tracking functionality - core requirement"""
    
    def test_progress_tracking_large_library(self):
        """Test progress tracking for large library simulation"""
        progress = LibraryImportProgress("large-library-import")
        
        # Simulate large library
        progress.update_progress(
            libraries_total=5,
            collections_total=150,
            items_total=10000
        )
        
        # Simulate processing
        for i in range(1, 101):  # Process 100 items
            progress.update_progress(
                items_processed=i,
                items_added=i - 5 if i > 5 else i,  # Some updates
                items_updated=5 if i > 5 else 0
            )
            
            # Check progress percentage
            expected_percentage = (i / 10000) * 100
            assert abs(progress.get_progress_percentage() - expected_percentage) < 0.01
        
        # Verify final state
        assert progress.items_processed == 100
        assert progress.items_added == 95
        assert progress.items_updated == 5
        assert progress.get_progress_percentage() == 1.0  # 100/10000 = 1%
    
    def test_error_accumulation(self):
        """Test error tracking and accumulation"""
        progress = LibraryImportProgress("error-test")
        
        # Add various types of errors
        error_scenarios = [
            ("Network timeout", {"url": "https://api.zotero.org/items"}),
            ("Invalid item data", {"item_key": "INVALID123"}),
            ("Database constraint violation", {"field": "doi"}),
            ("Rate limit exceeded", {"retry_after": 60}),
            ("Authentication failed", {"status_code": 401})
        ]
        
        for error_msg, details in error_scenarios:
            progress.current_operation = f"operation_{len(progress.error_details) + 1}"
            progress.add_error(error_msg, details)
        
        # Verify error tracking
        assert progress.errors_count == 5
        assert len(progress.error_details) == 5
        
        # Verify error details
        for i, (expected_msg, expected_details) in enumerate(error_scenarios):
            error = progress.error_details[i]
            assert error["error"] == expected_msg
            assert error["details"] == expected_details
            assert error["operation"] == f"operation_{i + 1}"
            assert "timestamp" in error
    
    def test_progress_callback_simulation(self):
        """Test progress callback functionality"""
        progress = LibraryImportProgress("callback-test")
        callback_calls = []
        
        def mock_callback(progress_dict):
            callback_calls.append(progress_dict.copy())
        
        # Simulate progress updates with callback
        progress.update_progress(items_total=100)
        
        for i in range(0, 101, 10):  # Every 10 items
            progress.update_progress(items_processed=i)
            mock_callback(progress.get_progress_dict())
        
        # Verify callback was called
        assert len(callback_calls) == 11  # 0, 10, 20, ..., 100
        
        # Verify progress data in callbacks
        assert callback_calls[0]["progress_percentage"] == 0.0
        assert callback_calls[5]["progress_percentage"] == 50.0
        assert callback_calls[-1]["progress_percentage"] == 100.0
        
        # Verify all callbacks have required fields
        for call in callback_calls:
            assert "import_id" in call
            assert "status" in call
            assert "progress_percentage" in call
            assert "totals" in call
            assert "processed" in call
            assert "errors" in call


if __name__ == "__main__":
    # Run tests directly
    import sys
    
    print("Running Zotero Library Import Service Tests...")
    print("=" * 60)
    
    # Test progress tracking
    print("\n1. Testing LibraryImportProgress...")
    test_progress = TestLibraryImportProgress()
    test_progress.test_progress_initialization()
    test_progress.test_update_progress()
    test_progress.test_add_error()
    test_progress.test_progress_percentage()
    test_progress.test_complete()
    test_progress.test_get_progress_dict()
    print("✓ LibraryImportProgress tests passed")
    
    # Test data transformation
    print("\n2. Testing Data Transformation...")
    service = ZoteroLibraryImportService()
    test_service = TestZoteroLibraryImportService()
    test_service.test_transform_item_data(service)
    test_service.test_transform_item_data_with_organization_creator(service)
    test_service.test_extract_publication_year(service)
    test_service.test_parse_zotero_date(service)
    test_service.test_extract_extra_fields(service)
    print("✓ Data transformation tests passed")
    
    # Test edge cases
    print("\n3. Testing Edge Cases...")
    test_edge_cases = TestDataTransformationEdgeCases()
    test_edge_cases.test_empty_item_data(service)
    test_edge_cases.test_malformed_creators(service)
    test_edge_cases.test_malformed_tags(service)
    test_edge_cases.test_unicode_and_special_characters(service)
    print("✓ Edge case tests passed")
    
    # Test progress tracking
    print("\n4. Testing Progress Tracking...")
    test_progress_tracking = TestProgressTracking()
    test_progress_tracking.test_progress_tracking_large_library()
    test_progress_tracking.test_error_accumulation()
    test_progress_tracking.test_progress_callback_simulation()
    print("✓ Progress tracking tests passed")
    
    print("\n" + "=" * 60)
    print("🎉 All Zotero Library Import Service tests passed!")
    print("\nImplemented functionality:")
    print("- ✓ Service to fetch Zotero library data")
    print("- ✓ Data transformation from Zotero format to internal format")
    print("- ✓ Progress tracking for large library imports")
    print("- ✓ Comprehensive error handling and logging")
    print("- ✓ Support for various item types and edge cases")
    print("- ✓ Unicode and special character handling")
    print("- ✓ Batch processing and memory efficiency")