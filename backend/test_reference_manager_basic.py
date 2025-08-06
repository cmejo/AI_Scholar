"""
Basic test for reference manager service
"""

import asyncio
from services.reference_manager_service import (
    ReferenceManagerService,
    BibliographicData,
    AuthCredentials,
    ReferenceManagerType
)

def test_basic_functionality():
    """Test basic service functionality"""
    service = ReferenceManagerService()
    
    # Test getting supported managers
    managers = service.get_supported_managers()
    print(f"Supported managers: {managers}")
    assert "zotero" in managers
    assert "mendeley" in managers
    assert "endnote" in managers
    
    # Test creating bibliographic data
    data = BibliographicData(
        title="Test Article",
        authors=["John Doe", "Jane Smith"],
        journal="Test Journal",
        year=2023,
        doi="10.1000/test"
    )
    
    print(f"Created bibliographic data: {data.title}")
    assert data.title == "Test Article"
    assert len(data.authors) == 2
    
    # Test credential validation
    valid_creds = AuthCredentials(access_token="test_token")
    invalid_creds = AuthCredentials(access_token="")
    
    assert service.validate_credentials(valid_creds) is True
    assert service.validate_credentials(invalid_creds) is False
    
    print("All basic tests passed!")

if __name__ == "__main__":
    test_basic_functionality()