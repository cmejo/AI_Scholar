"""
Tests for Multi-Modal Document Processor
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from PIL import Image
import io

from sqlalchemy.orm import Session
from services.multimodal_processor import (
    MultiModalProcessor, ContentType, ProcessingMethod,
    MultiModalElement, ImageAnalysisResult, TableExtractionResult,
    MathematicalContent
)
from core.database import Document, DocumentChunk

@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock(spec=Session)

@pytest.fixture
def multimodal_processor(mock_db):
    """Create MultiModalProcessor instance with mocked dependencies"""
    with patch('services.multimodal_processor.tempfile.mkdtemp', return_value='/tmp/test'):
        processor = MultiModalProcessor(mock_db)
        # Mock the model initialization to avoid loading actual models
        processor.blip_processor = Mock()
        processor.blip_model = Mock()
        processor.detr_processor = Mock()
        processor.detr_model = Mock()
        processor.layout_processor = Mock()
        processor.layout_model = Mock()
        processor.easyocr_reader = Mock()
        return processor

@pytest.fixture
def sample_image():
    """Create a sample image for testing"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()

@pytest.fixture
def sample_document():
    """Sample document for testing"""
    return Document(
        id="test-doc-1",
        user_id="test-user",
        name="Test Document",
        file_path="/path/to/test.pdf",
        content_type="application/pdf",
        size=1024,
        status="completed"
    )

class TestMultiModalProcessor:
    """Test cases for MultiModalProcessor"""

    def test_initialization(self, mock_db):
        """Test processor initialization"""
        with patch('services.multimodal_processor.tempfile.mkdtemp', return_value='/tmp/test'):
            processor = MultiModalProcessor(mock_db)
            assert processor.db == mock_db
            assert processor.temp_dir == '/tmp/test'

    @pytest.mark.asyncio
    async def test_analyze_image_success(self, multimodal_processor, sample_image):
        """Test successful image analysis"""
        # Mock BLIP model response
        multimodal_processor.blip_processor.return_value = {"input_ids": Mock()}
        multimodal_processor.blip_model.generate.return_value = [Mock()]
        multimodal_processor.blip_processor.decode.return_value = "A red square image"
        
        # Mock DETR model response
        multimodal_processor.detr_processor.return_value = {"pixel_values": Mock()}
        multimodal_processor.detr_model.return_value = Mock()
        multimodal_processor.detr_processor.post_process_object_detection.return_value = [{
            "scores": [0.9],
            "labels": [1],
            "boxes": [[10, 10, 90, 90]]
        }]
        multimodal_processor.detr_model.config.id2label = {1: "square"}
        
        # Mock OCR response
        multimodal_processor.easyocr_reader.readtext.return_value = [
            ([(0, 0), (100, 0), (100, 100), (0, 100)], "TEST TEXT", 0.9)
        ]
        
        result = await multimodal_processor._analyze_image(sample_image)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.description == "A red square image"
        assert "TEST TEXT" in result.text_extracted
        assert len(result.objects_detected) > 0
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_analyze_image_error_handling(self, multimodal_processor):
        """Test image analysis error handling"""
        # Test with invalid image data
        invalid_data = b"not an image"
        
        result = await multimodal_processor._analyze_image(invalid_data)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.description == "Error analyzing image"
        assert result.confidence == 0.0
        assert "error" in result.metadata

    def test_classify_image_content(self, multimodal_processor):
        """Test image content classification"""
        # Test chart classification
        content_type = multimodal_processor._classify_image_content(
            "A bar chart showing data",
            [],
            ""
        )
        assert content_type == ContentType.CHART
        
        # Test diagram classification
        content_type = multimodal_processor._classify_image_content(
            "A flowchart diagram",
            [],
            ""
        )
        assert content_type == ContentType.DIAGRAM
        
        # Test equation classification
        content_type = multimodal_processor._classify_image_content(
            "",
            [],
            "E = mc²"
        )
        assert content_type == ContentType.EQUATION
        
        # Test default classification
        content_type = multimodal_processor._classify_image_content(
            "A regular photo",
            [],
            ""
        )
        assert content_type == ContentType.IMAGE

    def test_calculate_image_confidence(self, multimodal_processor):
        """Test image confidence calculation"""
        # Test with good data
        confidence = multimodal_processor._calculate_image_confidence(
            "A detailed description of the image",
            [{"confidence": 0.9}, {"confidence": 0.8}],
            "Some extracted text"
        )
        assert confidence > 0.8
        
        # Test with minimal data
        confidence = multimodal_processor._calculate_image_confidence(
            "",
            [],
            ""
        )
        assert confidence == 0.0

    def test_table_to_text(self, multimodal_processor):
        """Test table to text conversion"""
        table_result = TableExtractionResult(
            data=[["John", "25"], ["Jane", "30"]],
            headers=["Name", "Age"],
            caption="Employee Data",
            confidence=0.9,
            format="csv",
            metadata={}
        )
        
        text = multimodal_processor._table_to_text(table_result)
        
        assert "Caption: Employee Data" in text
        assert "Headers: Name, Age" in text
        assert "Data: 2 rows" in text
        assert "John, 25" in text

    @pytest.mark.asyncio
    async def test_process_mathematical_content(self, multimodal_processor):
        """Test mathematical content processing"""
        # Test LaTeX equation
        latex_content = "$E = mc^2$"
        
        with patch('services.multimodal_processor.latex_to_mathml') as mock_latex:
            mock_latex.return_value = "<math>E = mc^2</math>"
            
            with patch('services.multimodal_processor.sympy.sympify') as mock_sympy:
                mock_expr = Mock()
                mock_expr.free_symbols = [Mock()]
                mock_expr.free_symbols[0].__str__ = lambda: "E"
                mock_expr.__str__ = lambda: "E = m*c**2"
                mock_sympy.return_value = mock_expr
                
                result = await multimodal_processor._process_mathematical_content(latex_content)
                
                assert isinstance(result, MathematicalContent)
                assert result.latex == "E = mc^2"
                assert result.mathml == "<math>E = mc^2</math>"
                assert result.confidence > 0

    def test_generate_math_description(self, multimodal_processor):
        """Test mathematical description generation"""
        description = multimodal_processor._generate_math_description(
            "E = mc^2",
            ["E", "m", "c"],
            ["E = m*c**2"]
        )
        
        assert "Variables: E, m, c" in description
        assert "Equations: 1 mathematical expression(s)" in description
        assert "LaTeX: E = mc^2" in description

    def test_calculate_math_confidence(self, multimodal_processor):
        """Test mathematical confidence calculation"""
        # Test with good mathematical content
        confidence = multimodal_processor._calculate_math_confidence(
            "E = mc^2",
            ["E", "m", "c"],
            ["E = m*c**2"]
        )
        assert confidence == 1.0
        
        # Test with minimal content
        confidence = multimodal_processor._calculate_math_confidence(
            "",
            [],
            []
        )
        assert confidence == 0.3

    @pytest.mark.asyncio
    async def test_store_multimodal_elements(self, multimodal_processor, mock_db):
        """Test storing multi-modal elements in database"""
        elements = [
            MultiModalElement(
                id="element-1",
                content_type=ContentType.IMAGE,
                processing_method=ProcessingMethod.VISION_TRANSFORMER,
                raw_data=b"image data",
                extracted_text="Test image",
                description="A test image",
                confidence_score=0.8,
                bounding_box=None,
                metadata={"test": "data"},
                page_number=1,
                document_id="doc-1"
            )
        ]
        
        await multimodal_processor._store_multimodal_elements(elements)
        
        # Verify database operations
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_multimodal_content(self, multimodal_processor, mock_db):
        """Test retrieving multi-modal content"""
        # Mock database query
        mock_chunk = Mock()
        mock_chunk.id = "element-1"
        mock_chunk.document_id = "doc-1"
        mock_chunk.content = "Test content"
        mock_chunk.page_number = 1
        mock_chunk.chunk_metadata = '{"is_multimodal": true, "content_type": "image", "processing_method": "vision_transformer", "description": "Test", "confidence_score": 0.8, "metadata": {}}'
        
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_chunk]
        
        elements = await multimodal_processor.get_multimodal_content("doc-1")
        
        assert len(elements) == 1
        assert elements[0].id == "element-1"
        assert elements[0].content_type == ContentType.IMAGE

    @pytest.mark.asyncio
    async def test_search_multimodal_content(self, multimodal_processor, mock_db):
        """Test searching multi-modal content"""
        # Mock database query
        mock_chunk = Mock()
        mock_chunk.id = "element-1"
        mock_chunk.document_id = "doc-1"
        mock_chunk.content = "Test image content"
        mock_chunk.page_number = 1
        mock_chunk.chunk_metadata = '{"is_multimodal": true, "content_type": "image", "processing_method": "vision_transformer", "description": "Test", "confidence_score": 0.8, "metadata": {}}'
        
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_chunk]
        
        elements = await multimodal_processor.search_multimodal_content("test")
        
        assert len(elements) == 1
        assert elements[0].id == "element-1"

    @pytest.mark.asyncio
    async def test_process_image_file(self, multimodal_processor, sample_image):
        """Test processing standalone image file"""
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(sample_image)
            tmp_file_path = tmp_file.name
        
        try:
            # Mock image analysis
            with patch.object(multimodal_processor, '_analyze_image') as mock_analyze:
                mock_analyze.return_value = ImageAnalysisResult(
                    description="Test image",
                    objects_detected=[],
                    text_extracted="",
                    content_type=ContentType.IMAGE,
                    confidence=0.8,
                    metadata={}
                )
                
                elements = await multimodal_processor._process_image_file("doc-1", tmp_file_path)
                
                assert len(elements) == 1
                assert elements[0].content_type == ContentType.IMAGE
                assert elements[0].document_id == "doc-1"
        
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)

    @pytest.mark.asyncio
    async def test_process_document_unsupported_format(self, multimodal_processor):
        """Test processing unsupported document format"""
        elements = await multimodal_processor.process_document(
            document_id="doc-1",
            file_path="/path/to/unsupported.xyz",
            extract_images=True,
            extract_tables=True,
            extract_equations=True,
            analyze_layout=True
        )
        
        # Should return empty list for unsupported format
        assert len(elements) == 0

    def test_cleanup(self, multimodal_processor):
        """Test cleanup of temporary resources"""
        with patch('os.path.exists', return_value=True):
            with patch('shutil.rmtree') as mock_rmtree:
                multimodal_processor.cleanup()
                mock_rmtree.assert_called_once_with(multimodal_processor.temp_dir)

    @pytest.mark.asyncio
    async def test_error_handling_in_process_document(self, multimodal_processor):
        """Test error handling in document processing"""
        with patch('services.multimodal_processor.fitz.open', side_effect=Exception("PDF error")):
            with pytest.raises(Exception):
                await multimodal_processor.process_document(
                    document_id="doc-1",
                    file_path="/path/to/test.pdf"
                )

    def test_content_type_enum(self):
        """Test ContentType enum values"""
        assert ContentType.IMAGE == "image"
        assert ContentType.CHART == "chart"
        assert ContentType.DIAGRAM == "diagram"
        assert ContentType.TABLE == "table"
        assert ContentType.EQUATION == "equation"

    def test_processing_method_enum(self):
        """Test ProcessingMethod enum values"""
        assert ProcessingMethod.OCR == "ocr"
        assert ProcessingMethod.VISION_TRANSFORMER == "vision_transformer"
        assert ProcessingMethod.OBJECT_DETECTION == "object_detection"
        assert ProcessingMethod.LAYOUT_ANALYSIS == "layout_analysis"
        assert ProcessingMethod.TABLE_EXTRACTION == "table_extraction"
        assert ProcessingMethod.MATHEMATICAL_PARSING == "mathematical_parsing"

    def test_multimodal_element_dataclass(self):
        """Test MultiModalElement dataclass"""
        element = MultiModalElement(
            id="test-id",
            content_type=ContentType.IMAGE,
            processing_method=ProcessingMethod.VISION_TRANSFORMER,
            raw_data=b"test data",
            extracted_text="test text",
            description="test description",
            confidence_score=0.8,
            bounding_box=(0, 0, 100, 100),
            metadata={"test": "value"},
            page_number=1,
            document_id="doc-1"
        )
        
        assert element.id == "test-id"
        assert element.content_type == ContentType.IMAGE
        assert element.confidence_score == 0.8
        assert element.bounding_box == (0, 0, 100, 100)

    def test_image_analysis_result_dataclass(self):
        """Test ImageAnalysisResult dataclass"""
        result = ImageAnalysisResult(
            description="test description",
            objects_detected=[{"label": "test", "confidence": 0.9}],
            text_extracted="test text",
            content_type=ContentType.IMAGE,
            confidence=0.8,
            metadata={"test": "value"}
        )
        
        assert result.description == "test description"
        assert len(result.objects_detected) == 1
        assert result.confidence == 0.8

    def test_table_extraction_result_dataclass(self):
        """Test TableExtractionResult dataclass"""
        result = TableExtractionResult(
            data=[["A", "B"], ["1", "2"]],
            headers=["Col1", "Col2"],
            caption="Test Table",
            confidence=0.9,
            format="csv",
            metadata={"test": "value"}
        )
        
        assert len(result.data) == 2
        assert len(result.headers) == 2
        assert result.confidence == 0.9

    def test_mathematical_content_dataclass(self):
        """Test MathematicalContent dataclass"""
        content = MathematicalContent(
            latex="E = mc^2",
            mathml="<math>E = mc^2</math>",
            description="Einstein's equation",
            variables=["E", "m", "c"],
            equations=["E = m*c**2"],
            confidence=0.9
        )
        
        assert content.latex == "E = mc^2"
        assert len(content.variables) == 3
        assert content.confidence == 0.9

if __name__ == "__main__":
    pytest.main([__file__])