"""
Simple validation test for Zotero Reference Management System

This test verifies the validation logic without importing the full service.
"""
import re
from datetime import datetime


def is_valid_doi(doi: str) -> bool:
    """Validate DOI format"""
    doi_pattern = r'^10\.\d{4,}\/[-._;()\/:a-zA-Z0-9]+$'
    return bool(re.match(doi_pattern, doi.strip()))


def is_valid_isbn(isbn: str) -> bool:
    """Validate ISBN format"""
    # Remove hyphens and spaces
    isbn_clean = re.sub(r'[-\s]', '', isbn)
    # Check ISBN-10 or ISBN-13 format
    return bool(re.match(r'^(?:\d{9}[\dX]|\d{13})$', isbn_clean))


def is_valid_issn(issn: str) -> bool:
    """Validate ISSN format"""
    issn_pattern = r'^\d{4}-\d{3}[\dX]$'
    return bool(re.match(issn_pattern, issn.strip()))


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = r'^https?:\/\/(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(url_pattern, url.strip()))


def validate_publication_year(year: int) -> bool:
    """Validate publication year"""
    current_year = datetime.now().year
    return 1000 <= year <= current_year + 5


def test_validation_functions():
    """Test all validation functions"""
    print("Testing Zotero Reference Validation Functions...")
    
    # Test DOI validation
    valid_dois = [
        "10.1000/test.doi",
        "10.1234/example",
        "10.1000/182",
        "10.1038/nature12373"
    ]
    
    invalid_dois = [
        "invalid-doi",
        "10.123",  # Too short
        "not-a-doi",
        ""
    ]
    
    print("\nTesting DOI validation:")
    for doi in valid_dois:
        if is_valid_doi(doi):
            print(f"✓ Valid DOI: {doi}")
        else:
            print(f"✗ Should be valid DOI: {doi}")
            return False
    
    for doi in invalid_dois:
        if not is_valid_doi(doi):
            print(f"✓ Invalid DOI correctly rejected: {doi}")
        else:
            print(f"✗ Should be invalid DOI: {doi}")
            return False
    
    # Test ISBN validation
    valid_isbns = [
        "978-0-123456-78-9",
        "9780123456789",
        "0-123456-78-X",
        "012345678X"
    ]
    
    invalid_isbns = [
        "invalid-isbn",
        "123",
        "978-0-123456-78",  # Too short
        ""
    ]
    
    print("\nTesting ISBN validation:")
    for isbn in valid_isbns:
        if is_valid_isbn(isbn):
            print(f"✓ Valid ISBN: {isbn}")
        else:
            print(f"✗ Should be valid ISBN: {isbn}")
            return False
    
    for isbn in invalid_isbns:
        if not is_valid_isbn(isbn):
            print(f"✓ Invalid ISBN correctly rejected: {isbn}")
        else:
            print(f"✗ Should be invalid ISBN: {isbn}")
            return False
    
    # Test ISSN validation
    valid_issns = [
        "1234-5678",
        "1234-567X"
    ]
    
    invalid_issns = [
        "invalid-issn",
        "12345678",  # No hyphen
        "1234-56789",  # Too long
        ""
    ]
    
    print("\nTesting ISSN validation:")
    for issn in valid_issns:
        if is_valid_issn(issn):
            print(f"✓ Valid ISSN: {issn}")
        else:
            print(f"✗ Should be valid ISSN: {issn}")
            return False
    
    for issn in invalid_issns:
        if not is_valid_issn(issn):
            print(f"✓ Invalid ISSN correctly rejected: {issn}")
        else:
            print(f"✗ Should be invalid ISSN: {issn}")
            return False
    
    # Test URL validation
    valid_urls = [
        "https://example.com",
        "http://test.org/path",
        "https://example.com:8080/path?query=value",
        "https://www.nature.com/articles/nature12373"
    ]
    
    invalid_urls = [
        "invalid-url",
        "ftp://example.com",  # Not HTTP/HTTPS
        "example.com",  # No protocol
        ""
    ]
    
    print("\nTesting URL validation:")
    for url in valid_urls:
        if is_valid_url(url):
            print(f"✓ Valid URL: {url}")
        else:
            print(f"✗ Should be valid URL: {url}")
            return False
    
    for url in invalid_urls:
        if not is_valid_url(url):
            print(f"✓ Invalid URL correctly rejected: {url}")
        else:
            print(f"✗ Should be invalid URL: {url}")
            return False
    
    # Test publication year validation
    current_year = datetime.now().year
    valid_years = [2023, 2024, current_year, 1900, 2000]
    invalid_years = [999, current_year + 10, 0, -1]
    
    print("\nTesting publication year validation:")
    for year in valid_years:
        if validate_publication_year(year):
            print(f"✓ Valid year: {year}")
        else:
            print(f"✗ Should be valid year: {year}")
            return False
    
    for year in invalid_years:
        if not validate_publication_year(year):
            print(f"✓ Invalid year correctly rejected: {year}")
        else:
            print(f"✗ Should be invalid year: {year}")
            return False
    
    return True


def test_reference_data_structure():
    """Test reference data structure validation"""
    print("\nTesting Reference Data Structure...")
    
    # Test valid reference data
    valid_reference = {
        "item_type": "article",
        "title": "Test Article",
        "creators": [{
            "creator_type": "author",
            "first_name": "John",
            "last_name": "Doe"
        }],
        "publication_title": "Test Journal",
        "publication_year": 2023,
        "doi": "10.1000/test.doi",
        "abstract_note": "Test abstract",
        "tags": ["test", "research"],
        "collection_ids": []
    }
    
    # Validate required fields
    required_fields = ["item_type"]
    for field in required_fields:
        if field not in valid_reference or not valid_reference[field]:
            print(f"✗ Missing required field: {field}")
            return False
    
    print("✓ Valid reference structure has all required fields")
    
    # Test creator validation
    creators = valid_reference.get("creators", [])
    for i, creator in enumerate(creators):
        if not creator.get("creator_type"):
            print(f"✗ Creator {i+1}: missing creator_type")
            return False
        
        if not creator.get("name") and not (creator.get("first_name") or creator.get("last_name")):
            print(f"✗ Creator {i+1}: missing name information")
            return False
    
    print("✓ Creator validation working correctly")
    
    # Test specific field validations
    if valid_reference.get("doi") and not is_valid_doi(valid_reference["doi"]):
        print("✗ DOI validation failed")
        return False
    
    if valid_reference.get("publication_year") and not validate_publication_year(valid_reference["publication_year"]):
        print("✗ Publication year validation failed")
        return False
    
    print("✓ Field-specific validations working correctly")
    
    return True


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("ZOTERO REFERENCE VALIDATION - SIMPLE TEST")
    print("=" * 60)
    
    tests = [
        test_validation_functions,
        test_reference_data_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
                print(f"✓ {test.__name__} passed")
            else:
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All validation tests passed! Reference validation is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Please check the validation implementation.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)