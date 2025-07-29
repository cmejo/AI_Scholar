"""
Demo script for Multi-Modal Document Processing
"""
import asyncio
import sys
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import tempfile

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from core.database import SessionLocal, Document, DocumentChunk, User, init_db
from services.multimodal_processor import (
    MultiModalProcessor, ContentType, ProcessingMethod,
    MultiModalElement, ImageAnalysisResult
)
import uuid

async def create_sample_documents(db: Session):
    """Create sample documents with multi-modal content for testing"""
    print("Creating sample documents with multi-modal content...")
    
    # Get or create test user
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            name="Test User",
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create sample images for testing
    sample_images = await create_sample_images()
    
    documents = []
    
    # Create documents with different types of content
    for i, (image_name, image_data, description) in enumerate(sample_images):
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(image_data)
            tmp_file_path = tmp_file.name
        
        # Create document record
        doc = Document(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name=f"Sample Document {i+1}: {image_name}",
            file_path=tmp_file_path,
            content_type="image/png",
            size=len(image_data),
            status="completed",
            chunks_count=0,
            embeddings_count=0,
            created_at=datetime.utcnow()
        )
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        documents.append((doc, description))
    
    print(f"Created {len(documents)} sample documents")
    return user, documents

async def create_sample_images():
    """Create sample images with different types of content"""
    images = []
    
    # 1. Chart/Graph Image
    chart_img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(chart_img)
    
    # Draw a simple bar chart
    bars = [(50, 250, 100, 150), (120, 250, 170, 100), (190, 250, 240, 180), (260, 250, 310, 120)]
    colors = ['red', 'blue', 'green', 'orange']
    
    for i, (x1, y1, x2, y2) in enumerate(bars):
        draw.rectangle([x1, y2, x2, y1], fill=colors[i])
    
    # Add title and labels
    try:
        font = ImageFont.load_default()
        draw.text((150, 20), "Sample Bar Chart", fill='black', font=font)
        draw.text((50, 260), "Q1", fill='black', font=font)
        draw.text((120, 260), "Q2", fill='black', font=font)
        draw.text((190, 260), "Q3", fill='black', font=font)
        draw.text((260, 260), "Q4", fill='black', font=font)
    except:
        pass  # Font loading might fail in some environments
    
    chart_bytes = io.BytesIO()
    chart_img.save(chart_bytes, format='PNG')
    images.append(("Bar Chart", chart_bytes.getvalue(), "A bar chart showing quarterly data"))
    
    # 2. Diagram/Flowchart Image
    diagram_img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(diagram_img)
    
    # Draw flowchart elements
    boxes = [(50, 50, 150, 100), (200, 50, 300, 100), (125, 150, 225, 200)]
    for box in boxes:
        draw.rectangle(box, outline='black', width=2)
    
    # Draw arrows
    draw.line([(150, 75), (200, 75)], fill='black', width=2)
    draw.line([(250, 100), (175, 150)], fill='black', width=2)
    
    # Add text
    try:
        font = ImageFont.load_default()
        draw.text((75, 70), "Start", fill='black', font=font)
        draw.text((225, 70), "Process", fill='black', font=font)
        draw.text((155, 170), "End", fill='black', font=font)
    except:
        pass
    
    diagram_bytes = io.BytesIO()
    diagram_img.save(diagram_bytes, format='PNG')
    images.append(("Flowchart", diagram_bytes.getvalue(), "A simple flowchart diagram"))
    
    # 3. Mathematical Equation Image
    math_img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(math_img)
    
    # Draw mathematical content
    try:
        font = ImageFont.load_default()
        draw.text((50, 50), "E = mc²", fill='black', font=font)
        draw.text((50, 80), "F = ma", fill='black', font=font)
        draw.text((50, 110), "∫ f(x)dx = F(x) + C", fill='black', font=font)
        draw.text((50, 140), "∑(i=1 to n) xi = x1 + x2 + ... + xn", fill='black', font=font)
    except:
        pass
    
    math_bytes = io.BytesIO()
    math_img.save(math_bytes, format='PNG')
    images.append(("Mathematical Equations", math_bytes.getvalue(), "Mathematical formulas and equations"))
    
    # 4. Table-like Image
    table_img = Image.new('RGB', (400, 250), color='white')
    draw = ImageDraw.Draw(table_img)
    
    # Draw table structure
    # Headers
    draw.rectangle([50, 50, 350, 80], outline='black', width=2)
    draw.line([(150, 50), (150, 200)], fill='black', width=1)
    draw.line([(250, 50), (250, 200)], fill='black', width=1)
    
    # Rows
    for i in range(4):
        y = 80 + i * 30
        draw.line([(50, y), (350, y)], fill='black', width=1)
    
    # Add table content
    try:
        font = ImageFont.load_default()
        draw.text((75, 60), "Name", fill='black', font=font)
        draw.text((175, 60), "Age", fill='black', font=font)
        draw.text((275, 60), "Score", fill='black', font=font)
        
        data = [("John", "25", "85"), ("Jane", "30", "92"), ("Bob", "28", "78")]
        for i, (name, age, score) in enumerate(data):
            y = 90 + i * 30
            draw.text((75, y), name, fill='black', font=font)
            draw.text((175, y), age, fill='black', font=font)
            draw.text((275, y), score, fill='black', font=font)
    except:
        pass
    
    table_bytes = io.BytesIO()
    table_img.save(table_bytes, format='PNG')
    images.append(("Data Table", table_bytes.getvalue(), "A table with student data"))
    
    # 5. Mixed Content Image
    mixed_img = Image.new('RGB', (500, 400), color='white')
    draw = ImageDraw.Draw(mixed_img)
    
    # Add various elements
    draw.rectangle([50, 50, 200, 150], outline='blue', width=2)
    draw.ellipse([250, 50, 400, 150], outline='red', width=2)
    draw.line([(50, 200), (450, 200)], fill='green', width=3)
    
    try:
        font = ImageFont.load_default()
        draw.text((60, 100), "Rectangle", fill='blue', font=font)
        draw.text((300, 100), "Circle", fill='red', font=font)
        draw.text((200, 220), "Line", fill='green', font=font)
        draw.text((50, 250), "Mixed geometric shapes", fill='black', font=font)
        draw.text((50, 280), "α + β = γ", fill='black', font=font)
    except:
        pass
    
    mixed_bytes = io.BytesIO()
    mixed_img.save(mixed_bytes, format='PNG')
    images.append(("Mixed Content", mixed_bytes.getvalue(), "Image with mixed geometric shapes and text"))
    
    return images

async def test_multimodal_processing():
    """Test the multi-modal processing functionality"""
    print("=== Multi-Modal Document Processing Demo ===\n")
    
    # Initialize database
    await init_db()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Create sample documents
        user, documents = await create_sample_documents(db)
        
        # Initialize multi-modal processor
        processor = MultiModalProcessor(db)
        
        print("1. Processing documents for multi-modal content...")
        
        all_elements = []
        for doc, description in documents:
            print(f"\nProcessing: {doc.name}")
            print(f"Expected content: {description}")
            
            try:
                elements = await processor.process_document(
                    document_id=doc.id,
                    file_path=doc.file_path,
                    extract_images=True,
                    extract_tables=True,
                    extract_equations=True,
                    analyze_layout=True
                )
                
                print(f"✓ Extracted {len(elements)} multi-modal elements")
                
                for element in elements:
                    print(f"  - {element.content_type.value}: {element.description}")
                    print(f"    Confidence: {element.confidence_score:.3f}")
                    print(f"    Text: {element.extracted_text[:100]}...")
                
                all_elements.extend(elements)
                
            except Exception as e:
                print(f"✗ Error processing {doc.name}: {str(e)}")
        
        print(f"\n2. Total multi-modal elements extracted: {len(all_elements)}")
        
        # Analyze content types
        content_type_counts = {}
        for element in all_elements:
            content_type = element.content_type.value
            content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1
        
        print("\nContent type distribution:")
        for content_type, count in content_type_counts.items():
            print(f"  - {content_type}: {count}")
        
        # Test retrieval functionality
        print("\n3. Testing multi-modal content retrieval...")
        
        if documents:
            doc_id = documents[0][0].id
            retrieved_elements = await processor.get_multimodal_content(doc_id)
            print(f"✓ Retrieved {len(retrieved_elements)} elements for document {doc_id}")
        
        # Test search functionality
        print("\n4. Testing multi-modal content search...")
        
        search_queries = ["chart", "equation", "table", "diagram"]
        for query in search_queries:
            results = await processor.search_multimodal_content(query, min_confidence=0.3)
            print(f"✓ Search '{query}': {len(results)} results")
        
        # Test image analysis directly
        print("\n5. Testing direct image analysis...")
        
        if documents:
            doc, description = documents[0]
            with open(doc.file_path, 'rb') as f:
                image_data = f.read()
            
            analysis_result = await processor._analyze_image(image_data)
            print(f"✓ Image analysis result:")
            print(f"  Description: {analysis_result.description}")
            print(f"  Content type: {analysis_result.content_type.value}")
            print(f"  Confidence: {analysis_result.confidence:.3f}")
            print(f"  Objects detected: {len(analysis_result.objects_detected)}")
            print(f"  Text extracted: {analysis_result.text_extracted[:100]}...")
        
        # Test mathematical content processing
        print("\n6. Testing mathematical content processing...")
        
        math_samples = [
            "$E = mc^2$",
            "$$\\int_{0}^{\\infty} e^{-x} dx = 1$$",
            "α + β = γ",
            "∑(i=1 to n) xi"
        ]
        
        for math_content in math_samples:
            try:
                math_result = await processor._process_mathematical_content(math_content)
                print(f"✓ Math content: {math_content}")
                print(f"  Description: {math_result.description}")
                print(f"  Variables: {math_result.variables}")
                print(f"  Confidence: {math_result.confidence:.3f}")
            except Exception as e:
                print(f"✗ Error processing math content: {str(e)}")
        
        # Performance statistics
        print("\n7. Performance Statistics:")
        
        total_confidence = sum(e.confidence_score for e in all_elements)
        avg_confidence = total_confidence / len(all_elements) if all_elements else 0
        
        processing_methods = {}
        for element in all_elements:
            method = element.processing_method.value
            processing_methods[method] = processing_methods.get(method, 0) + 1
        
        print(f"  - Average confidence: {avg_confidence:.3f}")
        print(f"  - Processing methods used:")
        for method, count in processing_methods.items():
            print(f"    • {method}: {count}")
        
        # Cleanup
        print("\n8. Cleaning up...")
        processor.cleanup()
        
        # Clean up temporary files
        for doc, _ in documents:
            try:
                os.unlink(doc.file_path)
            except:
                pass
        
        print("\n=== Multi-Modal Processing Demo Completed Successfully! ===")
        
        # Summary
        print(f"\n📊 Demo Summary:")
        print(f"✅ Processed {len(documents)} sample documents")
        print(f"✅ Extracted {len(all_elements)} multi-modal elements")
        print(f"✅ Identified {len(content_type_counts)} different content types")
        print(f"✅ Average confidence score: {avg_confidence:.3f}")
        print(f"✅ Used {len(processing_methods)} different processing methods")
        print(f"✅ Successfully tested image analysis, search, and retrieval")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_multimodal_processing())