"""
Basic test for writing tools service
"""

import asyncio
from services.writing_tools_service import (
    WritingToolsService,
    WritingSuggestion,
    SuggestionType,
    LaTeXDocument
)

def test_basic_functionality():
    """Test basic service functionality"""
    service = WritingToolsService()
    
    # Test getting supported tools
    tools = service.get_supported_tools()
    print(f"Supported tools: {tools}")
    assert "grammarly" in tools
    assert "latex" in tools
    
    # Test getting export platforms
    platforms = service.get_supported_export_platforms()
    print(f"Export platforms: {platforms}")
    assert "markdown" in platforms
    assert "html" in platforms
    assert "pdf" in platforms
    
    # Test creating writing suggestion
    suggestion = WritingSuggestion(
        id="test_1",
        type=SuggestionType.GRAMMAR,
        text="teh",
        start=0,
        end=3,
        message="Possible spelling mistake",
        suggestions=["the"],
        confidence=0.9,
        severity="high"
    )
    
    print(f"Created suggestion: {suggestion.message}")
    assert suggestion.type == SuggestionType.GRAMMAR
    assert suggestion.text == "teh"
    assert suggestion.suggestions == ["the"]
    
    print("All basic tests passed!")

def test_latex_functionality():
    """Test LaTeX functionality"""
    service = WritingToolsService()
    
    # Test creating LaTeX document
    doc = asyncio.run(service.create_latex_document(
        "Test Document",
        r"\section{Introduction}\nThis is a test document."
    ))
    
    print(f"Created LaTeX document: {doc.title}")
    assert doc.title == "Test Document"
    assert "section{Introduction}" in doc.content
    assert doc.id.startswith("latex_")
    
    # Test writing analysis
    analysis = asyncio.run(service.analyze_writing_style(
        "This is a test sentence. It has multiple sentences for analysis. "
        "The analysis should provide various metrics about the writing style."
    ))
    
    print(f"Writing analysis - Word count: {analysis['word_count']}")
    print(f"Readability level: {analysis['readability_level']}")
    
    assert analysis['word_count'] > 0
    assert analysis['sentence_count'] > 0
    assert 'readability_score' in analysis
    
    print("LaTeX functionality tests passed!")

if __name__ == "__main__":
    test_basic_functionality()
    test_latex_functionality()