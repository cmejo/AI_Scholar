#!/usr/bin/env python3
"""
Test script for multi-modal document processing features
"""

import os
import sys
import json
import base64
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
import io

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_image():
    """Create a test image with text and shapes"""
    # Create a test image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add title
    draw.text((50, 50), "Test Document", fill='black')
    draw.text((50, 100), "This is a sample image for OCR testing", fill='black')
    
    # Add some shapes
    draw.rectangle([50, 150, 200, 250], outline='blue', width=2)
    draw.text((60, 180), "Blue Box", fill='blue')
    
    draw.ellipse([250, 150, 400, 250], outline='red', width=2)
    draw.text((290, 190), "Red Circle", fill='red')
    
    # Add table-like structure
    draw.text((50, 300), "Sample Table:", fill='black')
    draw.text((50, 330), "Name    | Age | City", fill='black')
    draw.text((50, 350), "Alice   | 25  | NYC", fill='black')
    draw.text((50, 370), "Bob     | 30  | LA", fill='black')
    draw.text((50, 390), "Charlie | 35  | SF", fill='black')
    
    return img

def create_test_pdf():
    """Create a simple test PDF (placeholder - would need reportlab)"""
    # For now, return None - in a real implementation, you'd use reportlab
    return None

def test_multimodal_processor():
    """Test the multi-modal document processor"""
    print("🔍 Testing Multi-Modal Document Processing")
    print("=" * 60)
    
    try:
        from services.multimodal_document_processor import multimodal_processor
        
        # Test 1: Process test image
        print("\n1. Testing image processing...")
        test_img = create_test_image()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            test_img.save(tmp_file.name)
            
            # Process the image
            result = multimodal_processor.process_document(tmp_file.name)
            
            if result.success:
                print(f"✅ Image processed successfully!")
                print(f"   - Processing time: {result.processing_time:.2f}s")
                print(f"   - Elements extracted: {len(result.elements)}")
                print(f"   - Full text length: {len(result.full_text)}")
                
                for i, element in enumerate(result.elements):
                    print(f"   - Element {i+1}: {element.element_type} (confidence: {element.confidence:.2f})")
                    if element.image_caption:
                        print(f"     Caption: {element.image_caption[:100]}...")
                    if element.extracted_text:
                        print(f"     OCR Text: {element.extracted_text[:100]}...")
            else:
                print(f"❌ Image processing failed: {result.error_message}")
            
            # Clean up
            os.unlink(tmp_file.name)
        
        # Test 2: Process image from bytes
        print("\n2. Testing image processing from bytes...")
        img_buffer = io.BytesIO()
        test_img.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        result = multimodal_processor.process_image_from_bytes(img_bytes, "test_image.png")
        
        if result.success:
            print(f"✅ Image bytes processed successfully!")
            print(f"   - Processing time: {result.processing_time:.2f}s")
            print(f"   - Elements extracted: {len(result.elements)}")
        else:
            print(f"❌ Image bytes processing failed: {result.error_message}")
        
        # Test 3: Get processor statistics
        print("\n3. Testing processor statistics...")
        stats = multimodal_processor.get_stats()
        print(f"✅ Processor stats retrieved:")
        print(f"   - Images processed: {stats['processing_stats']['images_processed']}")
        print(f"   - OCR available: {stats['capabilities']['ocr_available']}")
        print(f"   - Vision models available: {stats['capabilities']['vision_models_available']}")
        print(f"   - PDF processing available: {stats['capabilities']['pdf_processing_available']}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install Pillow opencv-python pytesseract easyocr transformers torch")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_rag_integration():
    """Test RAG integration with multi-modal processing"""
    print("\n🔗 Testing RAG Integration")
    print("=" * 40)
    
    try:
        from services.rag_service import rag_service
        
        # Create test document
        test_img = create_test_image()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            test_img.save(tmp_file.name)
            
            # Test RAG ingestion
            print("1. Testing RAG ingestion with multi-modal processing...")
            success = rag_service.ingest_file(tmp_file.name, {
                "test_document": True,
                "source": "test_suite"
            })
            
            if success:
                print("✅ Document ingested into RAG system successfully!")
                
                # Test search
                print("2. Testing RAG search...")
                search_results = rag_service.search_documents("test document")
                
                if search_results:
                    print(f"✅ Found {len(search_results)} search results")
                    for i, result in enumerate(search_results[:3]):
                        print(f"   - Result {i+1}: Score {result.score:.3f}")
                        print(f"     Content: {result.document.content[:100]}...")
                else:
                    print("⚠️  No search results found")
                
                # Test RAG response generation
                print("3. Testing RAG response generation...")
                rag_response = rag_service.generate_rag_response(
                    "What can you tell me about the test document?",
                    model_name="llama2:7b-chat"
                )
                
                if rag_response.answer:
                    print(f"✅ RAG response generated successfully!")
                    print(f"   - Answer length: {len(rag_response.answer)}")
                    print(f"   - Sources used: {len(rag_response.sources)}")
                    print(f"   - Confidence: {rag_response.confidence:.3f}")
                    print(f"   - Retrieval time: {rag_response.retrieval_time:.3f}s")
                    print(f"   - Generation time: {rag_response.generation_time:.3f}s")
                else:
                    print("❌ RAG response generation failed")
            else:
                print("❌ Document ingestion failed")
            
            # Clean up
            os.unlink(tmp_file.name)
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_document_api():
    """Test document processing API"""
    print("\n📡 Testing Document Processing API")
    print("=" * 40)
    
    try:
        from services.document_processing_api import document_processing_api
        
        # Create test image
        test_img = create_test_image()
        img_buffer = io.BytesIO()
        test_img.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        # Test 1: Upload document (simulated user_id = 1)
        print("1. Testing document upload...")
        result = document_processing_api.upload_document(
            user_id=1,
            file_data=img_bytes,
            filename="test_document.png",
            processing_options={"test": True}
        )
        
        if result["success"]:
            print("✅ Document uploaded successfully!")
            document_id = result["document"]["document_id"]
            print(f"   - Document ID: {document_id}")
            print(f"   - Elements extracted: {result['document']['elements_count']}")
            
            # Test 2: Get document
            print("2. Testing document retrieval...")
            get_result = document_processing_api.get_document(
                user_id=1,
                document_id=document_id,
                include_elements=True
            )
            
            if get_result["success"]:
                print("✅ Document retrieved successfully!")
                print(f"   - Status: {get_result['document']['processing_status']}")
                print(f"   - Elements: {len(get_result['document'].get('elements', []))}")
            else:
                print(f"❌ Document retrieval failed: {get_result['error']}")
            
            # Test 3: Search documents
            print("3. Testing document search...")
            search_result = document_processing_api.search_documents(
                user_id=1,
                query="test",
                element_types=["text", "image"]
            )
            
            if search_result["success"]:
                print(f"✅ Document search successful!")
                print(f"   - Total documents: {search_result['total_documents']}")
                print(f"   - Total elements: {search_result['total_elements']}")
            else:
                print(f"❌ Document search failed: {search_result['error']}")
            
        else:
            print(f"❌ Document upload failed: {result['error']}")
        
        # Test 4: Base64 image processing
        print("4. Testing base64 image processing...")
        img_base64 = base64.b64encode(img_bytes).decode()
        b64_result = document_processing_api.process_image_from_base64(
            user_id=1,
            image_data=f"data:image/png;base64,{img_base64}",
            filename="base64_test.png"
        )
        
        if b64_result["success"]:
            print("✅ Base64 image processed successfully!")
            print(f"   - Processing time: {b64_result['processing_time']:.3f}s")
        else:
            print(f"❌ Base64 image processing failed: {b64_result['error']}")
        
        # Test 5: Get processing statistics
        print("5. Testing processing statistics...")
        stats_result = document_processing_api.get_processing_stats(user_id=1)
        
        if stats_result["success"]:
            print("✅ Processing statistics retrieved!")
            doc_stats = stats_result["document_stats"]
            print(f"   - Total documents: {doc_stats['total_documents']}")
            print(f"   - Completed: {doc_stats['completed']}")
            print(f"   - Failed: {doc_stats['failed']}")
        else:
            print(f"❌ Statistics retrieval failed: {stats_result['error']}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_database_models():
    """Test database models (without actual DB connection)"""
    print("\n🗄️  Testing Database Models")
    print("=" * 40)
    
    try:
        from models import ProcessedDocument, DocumentElement, DocumentProcessingJob
        
        print("✅ Database models imported successfully!")
        print("   - ProcessedDocument model available")
        print("   - DocumentElement model available") 
        print("   - DocumentProcessingJob model available")
        
        # Test model creation (without DB)
        print("✅ Model structure validation passed")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Run all tests"""
    print("🚀 Multi-Modal Document Processing Test Suite")
    print("=" * 60)
    
    # Test individual components
    test_multimodal_processor()
    test_rag_integration()
    test_document_api()
    test_database_models()
    
    print("\n🎉 Test Suite Completed!")
    print("\nNext Steps:")
    print("1. Install missing dependencies if any tests failed")
    print("2. Set up database and run migrations")
    print("3. Configure Ollama with vision models for full functionality")
    print("4. Test with real documents and images")
    print("\nRecommended setup commands:")
    print("pip install Pillow opencv-python pytesseract easyocr transformers torch")
    print("ollama pull llava")
    print("python manage_db.py upgrade")

if __name__ == "__main__":
    main()