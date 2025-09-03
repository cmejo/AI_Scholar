#!/usr/bin/env python3
"""
Task 8.1 Verification: Connect Zotero references to chat system

This script verifies that the Zotero chat integration is working correctly.
It tests the core functionality of connecting Zotero references to the chat system.
"""

import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from services.zotero.zotero_chat_integration_service import ZoteroChatIntegrationService
    from models.zotero_models import ZoteroItem
    print("✓ Successfully imported Zotero chat integration service")
except ImportError as e:
    print(f"✗ Failed to import Zotero chat integration service: {e}")
    sys.exit(1)


async def test_reference_mention_extraction():
    """Test extraction of reference mentions from chat content"""
    print("\n=== Testing Reference Mention Extraction ===")
    
    service = ZoteroChatIntegrationService()
    
    # Test cases
    test_cases = [
        ("Tell me about @[Machine Learning in Healthcare]", ["Machine Learning in Healthcare"]),
        ("Compare @[Smith, 2023] and @[Doe et al., 2022]", ["Smith, 2023", "Doe et al., 2022"]),
        ("No mentions here", []),
        ("@[Paper One] and @[Paper Two] are interesting", ["Paper One", "Paper Two"]),
    ]
    
    for content, expected in test_cases:
        mentions = service.extract_reference_mentions(content)
        if mentions == expected:
            print(f"✓ '{content}' -> {mentions}")
        else:
            print(f"✗ '{content}' -> Expected {expected}, got {mentions}")
            return False
    
    return True


async def test_reference_conversion():
    """Test conversion of Zotero items to chat reference format"""
    print("\n=== Testing Reference Conversion ===")
    
    service = ZoteroChatIntegrationService()
    
    # Create mock Zotero item
    mock_item = ZoteroItem(
        id="item-123",
        title="Machine Learning in Healthcare",
        creators=[
            {"firstName": "John", "lastName": "Smith", "creatorType": "author"},
            {"firstName": "Jane", "lastName": "Doe", "creatorType": "author"}
        ],
        publication_title="Journal of Medical AI",
        date="2023-05-15",
        abstract_note="This paper explores ML applications in healthcare."
    )
    
    references = service.convert_to_chat_references([mock_item])
    
    if len(references) == 1:
        ref = references[0]
        checks = [
            (ref['id'] == "item-123", "ID matches"),
            (ref['title'] == "Machine Learning in Healthcare", "Title matches"),
            (ref['creators'] == ["John Smith", "Jane Doe"], "Creators converted correctly"),
            (ref['year'] == 2023, "Year extracted correctly"),
            (ref['publicationTitle'] == "Journal of Medical AI", "Publication title matches"),
            (ref['citationKey'] == "Smith2023", "Citation key generated correctly"),
        ]
        
        for check, description in checks:
            if check:
                print(f"✓ {description}")
            else:
                print(f"✗ {description}")
                return False
    else:
        print(f"✗ Expected 1 reference, got {len(references)}")
        return False
    
    return True


async def test_context_injection():
    """Test reference context injection"""
    print("\n=== Testing Context Injection ===")
    
    service = ZoteroChatIntegrationService()
    mock_db = Mock()
    user_id = "test-user-123"
    
    # Mock the search service
    service.search_service = Mock()
    service.search_service.search_items = AsyncMock(return_value={
        'items': [ZoteroItem(
            id="item-123",
            title="Machine Learning in Healthcare",
            creators=[{"firstName": "John", "lastName": "Smith"}],
            date="2023",
            publication_title="Journal of Medical AI"
        )],
        'total_count': 1
    })
    
    content = "Tell me about @[Machine Learning in Healthcare]"
    options = {'includeZoteroContext': True, 'contextType': 'research'}
    
    try:
        enhanced_content, references = await service.inject_reference_context(
            content, user_id, mock_db, options
        )
        
        checks = [
            ("[REFERENCE_CONTEXT]" in enhanced_content, "Context marker added"),
            ("Research context from referenced papers:" in enhanced_content, "Context type header correct"),
            (len(references) > 0, "References found"),
            (references[0]['title'] == "Machine Learning in Healthcare", "Reference title correct"),
        ]
        
        for check, description in checks:
            if check:
                print(f"✓ {description}")
            else:
                print(f"✗ {description}")
                return False
                
    except Exception as e:
        print(f"✗ Context injection failed: {e}")
        return False
    
    return True


async def test_research_summary_creation():
    """Test research summary creation"""
    print("\n=== Testing Research Summary Creation ===")
    
    service = ZoteroChatIntegrationService()
    mock_db = Mock()
    user_id = "test-user-123"
    
    # Mock the search service
    service.search_service = Mock()
    service.search_service.search_items = AsyncMock(return_value={
        'items': [
            ZoteroItem(
                id="item-123",
                title="Machine Learning in Healthcare",
                creators=[{"firstName": "John", "lastName": "Smith"}],
                date="2023",
                publication_title="Journal of Medical AI"
            ),
            ZoteroItem(
                id="item-456",
                title="Deep Learning Applications",
                creators=[{"firstName": "Alice", "lastName": "Johnson"}],
                date="2022",
                publication_title="AI Research Quarterly"
            )
        ],
        'total_count': 2
    })
    
    try:
        result = await service.create_research_summary(
            "machine learning in healthcare", user_id, mock_db
        )
        
        checks = [
            ('summary' in result, "Summary field present"),
            ('references' in result, "References field present"),
            ("machine learning in healthcare" in result['summary'], "Topic in summary"),
            ("2 references" in result['summary'], "Reference count correct"),
            (len(result['references']) == 2, "Correct number of references"),
        ]
        
        for check, description in checks:
            if check:
                print(f"✓ {description}")
            else:
                print(f"✗ {description}")
                return False
                
    except Exception as e:
        print(f"✗ Research summary creation failed: {e}")
        return False
    
    return True


async def test_ai_response_processing():
    """Test AI response processing for reference links"""
    print("\n=== Testing AI Response Processing ===")
    
    service = ZoteroChatIntegrationService()
    
    response = "According to Smith2023, machine learning shows great promise in healthcare applications."
    references = [{
        'id': 'item-123',
        'title': 'Machine Learning in Healthcare',
        'creators': ['John Smith'],
        'citationKey': 'Smith2023'
    }]
    
    try:
        processed = service.process_ai_response(response, references)
        
        if "[@Machine Learning in Healthcare](zotero:item-123)" in processed:
            print("✓ Reference link added correctly")
            return True
        else:
            print(f"✗ Reference link not added. Got: {processed}")
            return False
            
    except Exception as e:
        print(f"✗ AI response processing failed: {e}")
        return False


async def main():
    """Run all verification tests"""
    print("=== Task 8.1 Verification: Connect Zotero references to chat system ===")
    
    tests = [
        test_reference_mention_extraction,
        test_reference_conversion,
        test_context_injection,
        test_research_summary_creation,
        test_ai_response_processing,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
            else:
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Task 8.1 implementation is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)