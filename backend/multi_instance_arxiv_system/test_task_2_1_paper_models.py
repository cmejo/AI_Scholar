#!/usr/bin/env python3
"""
Test script for Task 2.1: Enhanced Paper Data Models

This script validates that the enhanced paper data models are properly implemented
with instance information, unified handling, and all required fields.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_enhanced_paper_models():
    """Test the enhanced paper data models."""
    print("=" * 60)
    print("TESTING ENHANCED PAPER DATA MODELS")
    print("=" * 60)
    
    try:
        # Test 1: Import paper models
        print("\n1. Testing paper model imports...")
        
        from multi_instance_arxiv_system.shared.multi_instance_data_models import (
            BasePaper, ArxivPaper, JournalPaper
        )
        
        print("✅ All paper models imported successfully")
        
        # Test 2: Test BasePaper abstract class
        print("\n2. Testing BasePaper abstract class...")
        
        # Verify BasePaper is abstract
        try:
            # This should fail because BasePaper is abstract
            base_paper = BasePaper(
                paper_id="test",
                title="Test Paper",
                authors=["Test Author"],
                abstract="Test abstract",
                published_date=datetime.now(),
                source_type="test",
                instance_name="test_instance"
            )
            print("❌ BasePaper should be abstract and not instantiable")
            return False
        except TypeError as e:
            if "abstract" in str(e).lower():
                print("✅ BasePaper is properly abstract")
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        
        # Test 3: Test ArxivPaper model
        print("\n3. Testing ArxivPaper model...")
        
        arxiv_paper = ArxivPaper(
            paper_id="2023.12345",
            title="Test ArXiv Paper on Multi-Instance Systems",
            authors=["John Doe", "Jane Smith"],
            abstract="This is a test abstract for an ArXiv paper about multi-instance systems.",
            published_date=datetime(2023, 12, 15),
            instance_name="ai_scholar",
            arxiv_id="2023.12345",
            categories=["cs.AI", "cs.LG"],
            updated_date=datetime(2023, 12, 16),
            pdf_url="https://arxiv.org/pdf/2023.12345.pdf",
            doi="10.48550/arXiv.2023.12345"
        )
        
        # Test ArxivPaper functionality
        print(f"   - Paper ID: {arxiv_paper.paper_id}")
        print(f"   - Instance Name: {arxiv_paper.instance_name}")
        print(f"   - Source Type: {arxiv_paper.source_type}")
        print(f"   - Categories: {arxiv_paper.categories}")
        
        # Test document ID generation
        doc_id = arxiv_paper.get_document_id()
        expected_doc_id = "ai_scholar_arxiv_2023_12345"
        if doc_id == expected_doc_id:
            print(f"✅ Document ID generation: {doc_id}")
        else:
            print(f"❌ Document ID mismatch. Expected: {expected_doc_id}, Got: {doc_id}")
            return False
        
        # Test filename generation
        filename = arxiv_paper.get_filename()
        if filename.startswith("2023_12345_") and filename.endswith(".pdf"):
            print(f"✅ Filename generation: {filename}")
        else:
            print(f"❌ Invalid filename format: {filename}")
            return False
        
        # Test serialization
        arxiv_dict = arxiv_paper.to_dict()
        if isinstance(arxiv_dict['published_date'], str) and isinstance(arxiv_dict['updated_date'], str):
            print("✅ ArxivPaper serialization works")
        else:
            print("❌ ArxivPaper serialization failed")
            return False
        
        # Test deserialization
        arxiv_paper_restored = ArxivPaper.from_dict(arxiv_dict)
        if (arxiv_paper_restored.paper_id == arxiv_paper.paper_id and 
            arxiv_paper_restored.instance_name == arxiv_paper.instance_name):
            print("✅ ArxivPaper deserialization works")
        else:
            print("❌ ArxivPaper deserialization failed")
            return False
        
        # Test 4: Test JournalPaper model
        print("\n4. Testing JournalPaper model...")
        
        journal_paper = JournalPaper(
            paper_id="jss_2023_001",
            title="Advanced Statistical Methods in R",
            authors=["Alice Johnson", "Bob Wilson"],
            abstract="This paper presents advanced statistical methods implemented in R.",
            published_date=datetime(2023, 11, 20),
            instance_name="quant_scholar",
            journal_name="Journal of Statistical Software",
            volume="108",
            issue="3",
            pages="1-25",
            doi="10.18637/jss.v108.i03",
            pdf_url="https://www.jstatsoft.org/article/view/v108i03/v108i03.pdf",
            journal_url="https://www.jstatsoft.org/article/view/v108i03"
        )
        
        # Test JournalPaper functionality
        print(f"   - Paper ID: {journal_paper.paper_id}")
        print(f"   - Instance Name: {journal_paper.instance_name}")
        print(f"   - Source Type: {journal_paper.source_type}")
        print(f"   - Journal Name: {journal_paper.journal_name}")
        print(f"   - Volume/Issue: {journal_paper.volume}/{journal_paper.issue}")
        
        # Test document ID generation
        doc_id = journal_paper.get_document_id()
        if "quant_scholar_journal_" in doc_id and "journal_of_statistical_software" in doc_id:
            print(f"✅ Document ID generation: {doc_id}")
        else:
            print(f"❌ Invalid document ID format: {doc_id}")
            return False
        
        # Test filename generation
        filename = journal_paper.get_filename()
        if "Journal of Statistical Software" in filename or "jss_2023_001" in filename:
            print(f"✅ Filename generation: {filename}")
        else:
            print(f"❌ Invalid filename format: {filename}")
            return False
        
        # Test serialization/deserialization
        journal_dict = journal_paper.to_dict()
        journal_paper_restored = JournalPaper.from_dict(journal_dict)
        if (journal_paper_restored.paper_id == journal_paper.paper_id and 
            journal_paper_restored.journal_name == journal_paper.journal_name):
            print("✅ JournalPaper serialization/deserialization works")
        else:
            print("❌ JournalPaper serialization/deserialization failed")
            return False
        
        # Test 5: Test instance-specific metadata
        print("\n5. Testing instance-specific metadata...")
        
        # Add custom metadata to papers
        arxiv_paper.metadata = {
            "processing_version": "1.0",
            "embedding_model": "all-MiniLM-L6-v2",
            "chunk_count": 15,
            "ai_scholar_specific": {
                "physics_category": True,
                "complexity_score": 0.85
            }
        }
        
        journal_paper.metadata = {
            "processing_version": "1.0",
            "embedding_model": "all-MiniLM-L6-v2",
            "chunk_count": 22,
            "quant_scholar_specific": {
                "statistical_methods": ["regression", "time_series"],
                "r_packages": ["ggplot2", "dplyr"]
            }
        }
        
        # Verify metadata is preserved
        if (arxiv_paper.metadata.get("ai_scholar_specific") and 
            journal_paper.metadata.get("quant_scholar_specific")):
            print("✅ Instance-specific metadata support works")
        else:
            print("❌ Instance-specific metadata support failed")
            return False
        
        # Test 6: Test unified paper handling
        print("\n6. Testing unified paper handling...")
        
        papers = [arxiv_paper, journal_paper]
        
        # Test that both papers can be handled uniformly through BasePaper interface
        for i, paper in enumerate(papers):
            paper_type = "ArXiv" if isinstance(paper, ArxivPaper) else "Journal"
            print(f"   - Paper {i+1} ({paper_type}):")
            print(f"     * Document ID: {paper.get_document_id()}")
            print(f"     * Filename: {paper.get_filename()}")
            print(f"     * Instance: {paper.instance_name}")
            print(f"     * Source Type: {paper.source_type}")
        
        print("✅ Unified paper handling works")
        
        # Test 7: Test instance separation
        print("\n7. Testing instance separation...")
        
        # Verify papers have different instances
        if arxiv_paper.instance_name != journal_paper.instance_name:
            print("✅ Papers have different instance names")
        else:
            print("❌ Papers should have different instance names")
            return False
        
        # Verify document IDs include instance information
        arxiv_doc_id = arxiv_paper.get_document_id()
        journal_doc_id = journal_paper.get_document_id()
        
        if (arxiv_paper.instance_name in arxiv_doc_id and 
            journal_paper.instance_name in journal_doc_id):
            print("✅ Document IDs include instance information")
        else:
            print("❌ Document IDs missing instance information")
            return False
        
        # Test 8: Test paper type detection
        print("\n8. Testing paper type detection...")
        
        def get_paper_info(paper: BasePaper) -> str:
            """Get paper information using polymorphism."""
            if isinstance(paper, ArxivPaper):
                return f"ArXiv paper {paper.arxiv_id} in categories {paper.categories}"
            elif isinstance(paper, JournalPaper):
                return f"Journal paper from {paper.journal_name}, Vol {paper.volume}"
            else:
                return f"Unknown paper type: {type(paper)}"
        
        arxiv_info = get_paper_info(arxiv_paper)
        journal_info = get_paper_info(journal_paper)
        
        if "ArXiv paper 2023.12345" in arxiv_info and "Journal of Statistical Software" in journal_info:
            print("✅ Paper type detection works")
            print(f"   - ArXiv: {arxiv_info}")
            print(f"   - Journal: {journal_info}")
        else:
            print("❌ Paper type detection failed")
            return False
        
        print("\n" + "=" * 60)
        print("✅ ALL PAPER MODEL TESTS PASSED!")
        print("✅ Task 2.1: Enhanced Paper Data Models - COMPLETE")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Paper model test failed: {e}")
        logger.exception("Paper model test error")
        return False


def test_paper_model_requirements():
    """Test that paper models meet all specified requirements."""
    print("\n" + "=" * 60)
    print("TESTING PAPER MODEL REQUIREMENTS COMPLIANCE")
    print("=" * 60)
    
    try:
        from multi_instance_arxiv_system.shared.multi_instance_data_models import (
            BasePaper, ArxivPaper, JournalPaper
        )
        
        # Requirement 8.1: Extend existing ArxivPaper model with instance information
        print("\n1. Testing ArxivPaper extension with instance information...")
        
        arxiv_paper = ArxivPaper(
            paper_id="test.001",
            title="Test Paper",
            authors=["Test Author"],
            abstract="Test abstract",
            published_date=datetime.now(),
            instance_name="ai_scholar",
            arxiv_id="test.001"
        )
        
        # Check instance information is included
        if hasattr(arxiv_paper, 'instance_name') and arxiv_paper.instance_name:
            print("✅ ArxivPaper has instance information")
        else:
            print("❌ ArxivPaper missing instance information")
            return False
        
        # Requirement 8.4: Implement JournalPaper model for non-arXiv sources
        print("\n2. Testing JournalPaper model for non-arXiv sources...")
        
        journal_paper = JournalPaper(
            paper_id="journal.001",
            title="Test Journal Paper",
            authors=["Journal Author"],
            abstract="Journal abstract",
            published_date=datetime.now(),
            instance_name="quant_scholar",
            journal_name="Test Journal"
        )
        
        # Check journal-specific fields
        journal_fields = ['journal_name', 'volume', 'issue', 'pages', 'journal_url']
        missing_fields = [field for field in journal_fields if not hasattr(journal_paper, field)]
        
        if not missing_fields:
            print("✅ JournalPaper has all required journal-specific fields")
        else:
            print(f"❌ JournalPaper missing fields: {missing_fields}")
            return False
        
        # Requirement 10.3: Create BasePaper abstract class for unified paper handling
        print("\n3. Testing BasePaper abstract class for unified handling...")
        
        # Test polymorphic behavior
        papers = [arxiv_paper, journal_paper]
        
        for paper in papers:
            # All papers should have these methods from BasePaper
            if (hasattr(paper, 'get_document_id') and 
                hasattr(paper, 'get_filename') and
                hasattr(paper, 'to_dict') and
                hasattr(paper, 'from_dict')):
                continue
            else:
                print("❌ Paper missing required BasePaper methods")
                return False
        
        print("✅ BasePaper provides unified paper handling")
        
        # Test instance-specific metadata fields
        print("\n4. Testing instance-specific metadata fields...")
        
        # Add instance-specific metadata
        arxiv_paper.metadata['ai_scholar_processing'] = {'version': '1.0'}
        journal_paper.metadata['quant_scholar_processing'] = {'version': '1.0'}
        
        if (arxiv_paper.metadata and journal_paper.metadata and
            'ai_scholar_processing' in arxiv_paper.metadata and
            'quant_scholar_processing' in journal_paper.metadata):
            print("✅ Instance-specific metadata fields supported")
        else:
            print("❌ Instance-specific metadata fields not working")
            return False
        
        print("\n✅ ALL REQUIREMENTS COMPLIANCE TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Requirements compliance test failed: {e}")
        logger.exception("Requirements compliance test error")
        return False


def main():
    """Run all paper model tests."""
    print("Starting Enhanced Paper Data Models Tests...")
    print(f"Test started at: {datetime.now()}")
    
    # Run paper model tests
    model_success = test_enhanced_paper_models()
    
    # Run requirements compliance tests
    requirements_success = test_paper_model_requirements()
    
    # Overall result
    if model_success and requirements_success:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("Task 2.1: Enhanced Paper Data Models is COMPLETE")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Task 2.1: Enhanced Paper Data Models needs attention")
        return 1


if __name__ == "__main__":
    exit(main())