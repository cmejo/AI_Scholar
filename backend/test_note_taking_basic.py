"""
Basic test for note-taking integration service
"""

import asyncio
import tempfile
import os
from pathlib import Path
from services.note_taking_integration_service import (
    NoteTakingIntegrationService,
    Note,
    SyncConfig,
    NoteTakingApp,
    ObsidianIntegration
)

def test_basic_functionality():
    """Test basic service functionality"""
    service = NoteTakingIntegrationService()
    
    # Test getting supported apps
    apps = service.get_supported_apps()
    print(f"Supported apps: {apps}")
    assert "obsidian" in apps
    assert "notion" in apps
    assert "roam" in apps
    
    # Test creating a note
    note = Note(
        id="test_note_1",
        title="Test Note",
        content="This is a test note content.",
        tags=["test", "demo"],
        app_source="obsidian"
    )
    
    print(f"Created note: {note.title}")
    assert note.title == "Test Note"
    assert len(note.tags) == 2
    assert note.app_source == "obsidian"
    assert note.links == []
    assert note.backlinks == []
    
    # Test creating sync config
    config = SyncConfig(
        app_type=NoteTakingApp.OBSIDIAN,
        credentials={"vault_path": "/tmp/test_vault"},
        sync_direction="bidirectional"
    )
    
    print(f"Created sync config for: {config.app_type.value}")
    assert config.app_type == NoteTakingApp.OBSIDIAN
    assert config.sync_direction == "bidirectional"
    assert config.preserve_formatting is True
    
    print("All basic tests passed!")

def test_obsidian_integration():
    """Test Obsidian integration with temporary vault"""
    # Create temporary vault directory
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        
        # Create some test markdown files
        test_file1 = vault_path / "Test Note 1.md"
        test_file1.write_text("""---
title: Test Note 1
tags: [test, demo]
---

# Test Note 1

This is a test note with a [[Test Note 2]] link.

#inline-tag
""")
        
        test_file2 = vault_path / "Test Note 2.md"
        test_file2.write_text("""# Test Note 2

This note is referenced by [[Test Note 1]].

- Bullet point 1
- Bullet point 2
""")
        
        # Test Obsidian integration
        obsidian = ObsidianIntegration(str(vault_path))
        
        # Test reading vault notes
        notes = asyncio.run(obsidian._read_vault_notes())
        
        print(f"Found {len(notes)} notes in vault")
        assert len(notes) == 2
        
        # Check first note
        note1 = next((n for n in notes if n.title == "Test Note 1"), None)
        assert note1 is not None
        assert "test" in note1.tags
        assert "demo" in note1.tags
        assert "inline-tag" in note1.tags
        assert "Test Note 2" in note1.links
        
        # Check second note
        note2 = next((n for n in notes if n.title == "Test Note 2"), None)
        assert note2 is not None
        
        print("Obsidian integration test passed!")

if __name__ == "__main__":
    test_basic_functionality()
    test_obsidian_integration()