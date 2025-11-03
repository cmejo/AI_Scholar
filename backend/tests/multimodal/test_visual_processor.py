"""
Unit tests for visual content processor.
"""

import pytest
import numpy as np
import asyncio
from PIL import Image
import io
import base64
from unittest.mock import Mock, patch, AsyncMock

from backend.rl.multimodal.visual_processor import (
    ImageProcessor,
    ElementDetector,
    FeatureExtractor,
    VisualContentProcessor
)
from backend.rl.multimodal.models import (
    VisualElement,
    VisualElementType,
    BoundingBox,
    VisualFeatures,
    QuantitativeData,
    StructuralRelationships
)


class TestImageProcessor:
    """Test cases for ImageProcessor class."""
    
    def create_test_image(self, width=100, height=100, mode='RGB'):
        """Create a test PIL Image."""
        if mode == 'RGB':
            # Create a simple gradient image
            img_array = np.zeros((height, width, 3), dtype=np.uint8)
            for i in range(height):
                for j in range(width):
                    img_array[i, j] = [i % 256, j % 256, (i + j) % 256]
        else:  # Grayscale
            img_array = np.zeros((height, width), dtype=np.uint8)
            for i in range(height):
                for j in range(width):
                    img_array[i, j] = (i + j) % 256
        
        return Image.fromarray(img_array, mode=mode)
    
    def image_to_bytes(self, image):
        """Convert PIL Image to bytes."""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def image_to_base64(self, image):
        """Convert PIL Image to base64 string."""
        image_bytes = self.image_to_bytes(image)
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def test_load_image_from_bytes(self):
        """Test loading image from bytes."""
        test_image = self.create_test_image()
        image_bytes = self.image_to_bytes(test_image)
        
        loaded_image = ImageProcessor.load_image_from_bytes(image_bytes)
        
        assert loaded_image.size == test_image.size
        assert loaded_image.mode == test_image.mode
    
    def test_load_image_from_base64(self):
        """Test loading image from base64 string."""
        test_image = self.create_test_image()
        base64_data = self.image_to_base64(test_image)
        
        loaded_image = ImageProcessor.load_image_from_base64(base64_data)
        
        assert loaded_image.size == test_image.size
        assert loaded_image.mode == test_image.mode
    
    def test_load_image_invalid_data(self):
        """Test error handling for invalid image data."""
        with pytest.raises(ValueError, match="Failed to load image"):
            ImageProcessor.load_image_from_bytes(b"invalid image data")
        
        with pytest.raises(ValueError, match="Failed to load image from base64"):
            ImageProcessor.load_image_from_base64("invalid base64 data")
    
    def test_resize_image(self):
        """Test image resizing."""
        test_image = self.create_test_image(width=2000, height=1500)
        
        resized_image = ImageProcessor.resize_image(test_image, max_size=(1024, 1024))
        
        # Should maintain aspect ratio and fit within max_size
        assert resized_image.width <= 1024
        assert resized_image.height <= 1024
        
        # Check aspect ratio is maintained (approximately)
        original_ratio = test_image.width / test_image.height
        resized_ratio = resized_image.width / resized_image.height
        assert abs(original_ratio - resized_ratio) < 0.01
    
    def test_convert_to_rgb(self):
        """Test RGB conversion."""
        # Test with grayscale image
        gray_image = self.create_test_image(mode='L')
        rgb_image = ImageProcessor.convert_to_rgb(gray_image)
        
        assert rgb_image.mode == 'RGB'
        
        # Test with already RGB image
        rgb_original = self.create_test_image(mode='RGB')
        rgb_converted = ImageProcessor.convert_to_rgb(rgb_original)
        
        assert rgb_converted.mode == 'RGB'
        assert rgb_converted.size == rgb_original.size
    
    def test_extract_basic_features_rgb(self):
        """Test basic feature extraction from RGB image."""
        test_image = self.create_test_image(width=50, height=30)
        
        features = ImageProcessor.extract_basic_features(test_image)
        
        # Check required features are present
        required_features = [
            'mean_red', 'mean_green', 'mean_blue',
            'std_red', 'std_green', 'std_blue',
            'brightness', 'contrast',
            'width', 'height', 'aspect_ratio', 'area'
        ]
        
        for feature in required_features:
            assert feature in features
        
        # Check feature value ranges
        assert 0 <= features['brightness'] <= 1
        assert 0 <= features['contrast'] <= 1
        assert features['width'] == 50
        assert features['height'] == 30
        assert abs(features['aspect_ratio'] - (50/30)) < 0.01
        assert features['area'] == 50 * 30
    
    def test_extract_basic_features_grayscale(self):
        """Test basic feature extraction from grayscale image."""
        test_image = self.create_test_image(width=40, height=60, mode='L')
        
        features = ImageProcessor.extract_basic_features(test_image)
        
        # For grayscale, RGB components should be 0
        assert features['mean_red'] == 0.0
        assert features['mean_green'] == 0.0
        assert features['mean_blue'] == 0.0
        
        # Other features should still be present
        assert 0 <= features['brightness'] <= 1
        assert 0 <= features['contrast'] <= 1
        assert features['width'] == 40
        assert features['height'] == 60


class TestElementDetector:
    """Test cases for ElementDetector class."""
    
    def create_test_image(self, width=100, height=100):
        """Create a test PIL Image."""
        img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        return Image.fromarray(img_array, mode='RGB')
    
    def create_high_contrast_image(self, width=200, height=100):
        """Create a high contrast image that might be detected as a chart."""
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create alternating black and white stripes (high contrast)
        for i in range(height):
            for j in range(width):
                if (i // 10 + j // 10) % 2 == 0:
                    img_array[i, j] = [255, 255, 255]
                else:
                    img_array[i, j] = [0, 0, 0]
        
        return Image.fromarray(img_array, mode='RGB')
    
    def create_square_image(self, size=100):
        """Create a square image that might be detected as a diagram."""
        img_array = np.random.randint(50, 200, (size, size, 3), dtype=np.uint8)
        return Image.fromarray(img_array, mode='RGB')
    
    def create_wide_image(self, width=300, height=50):
        """Create a wide image that might be detected as an equation."""
        img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        return Image.fromarray(img_array, mode='RGB')
    
    @pytest.mark.asyncio
    async def test_detect_elements_basic(self):
        """Test basic element detection."""
        detector = ElementDetector()
        test_image = self.create_test_image()
        
        elements = await detector.detect_elements(test_image)
        
        # Should return a list (might be empty for random image)
        assert isinstance(elements, list)
        
        # All elements should be valid
        for element in elements:
            assert isinstance(element, VisualElement)
            assert element.is_valid()
    
    @pytest.mark.asyncio
    async def test_detect_chart_elements(self):
        """Test detection of chart-like elements."""
        detector = ElementDetector()
        high_contrast_image = self.create_high_contrast_image()
        
        elements = await detector.detect_elements(high_contrast_image)
        
        # Should detect at least one element due to high contrast
        assert len(elements) > 0
        
        # Check if any chart elements were detected
        chart_elements = [e for e in elements if e.element_type == VisualElementType.CHART]
        assert len(chart_elements) > 0
        
        # Verify chart element properties
        chart_element = chart_elements[0]
        assert chart_element.confidence > 0
        assert chart_element.bounding_box.area() > 0
    
    @pytest.mark.asyncio
    async def test_detect_diagram_elements(self):
        """Test detection of diagram-like elements."""
        detector = ElementDetector()
        square_image = self.create_square_image()
        
        elements = await detector.detect_elements(square_image)
        
        # Should return elements
        assert isinstance(elements, list)
        
        # Check for diagram elements (might not always detect due to randomness)
        for element in elements:
            if element.element_type == VisualElementType.DIAGRAM:
                assert element.confidence > 0
                assert element.bounding_box.area() > 0
    
    @pytest.mark.asyncio
    async def test_detect_equation_elements(self):
        """Test detection of equation-like elements."""
        detector = ElementDetector()
        wide_image = self.create_wide_image()
        
        elements = await detector.detect_elements(wide_image)
        
        # Should return elements
        assert isinstance(elements, list)
        
        # Check for equation elements
        equation_elements = [e for e in elements if e.element_type == VisualElementType.EQUATION]
        
        # Wide, short images should be detected as equations
        if equation_elements:
            equation_element = equation_elements[0]
            assert equation_element.confidence > 0
            assert equation_element.bounding_box.width > equation_element.bounding_box.height


class TestFeatureExtractor:
    """Test cases for FeatureExtractor class."""
    
    def create_test_image(self, width=100, height=100):
        """Create a test PIL Image."""
        img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        return Image.fromarray(img_array, mode='RGB')
    
    @pytest.mark.asyncio
    async def test_extract_visual_features(self):
        """Test visual feature extraction."""
        extractor = FeatureExtractor()
        test_image = self.create_test_image()
        
        features = await extractor.extract_visual_features(test_image)
        
        # Check that we get a VisualFeatures object
        assert isinstance(features, VisualFeatures)
        
        # Check embeddings
        assert features.visual_embeddings.size > 0
        assert features.visual_embeddings.shape[0] == extractor.feature_dim
        
        # Check feature dictionaries
        assert isinstance(features.color_features, dict)
        assert isinstance(features.texture_features, dict)
        assert isinstance(features.shape_features, dict)
        assert isinstance(features.spatial_features, dict)
        assert isinstance(features.content_features, dict)
    
    @pytest.mark.asyncio
    async def test_extract_color_features(self):
        """Test color feature extraction."""
        extractor = FeatureExtractor()
        test_image = self.create_test_image()
        
        color_features = await extractor._extract_color_features(test_image)
        
        # Check required color features
        required_features = [
            'mean_red', 'mean_green', 'mean_blue',
            'std_red', 'std_green', 'std_blue',
            'brightness', 'contrast', 'color_diversity'
        ]
        
        for feature in required_features:
            assert feature in color_features
            assert 0 <= color_features[feature] <= 1
    
    @pytest.mark.asyncio
    async def test_extract_texture_features(self):
        """Test texture feature extraction."""
        extractor = FeatureExtractor()
        test_image = self.create_test_image()
        
        texture_features = await extractor._extract_texture_features(test_image)
        
        # Check required texture features
        required_features = ['roughness', 'uniformity', 'entropy', 'edge_density']
        
        for feature in required_features:
            assert feature in texture_features
            assert isinstance(texture_features[feature], float)
    
    @pytest.mark.asyncio
    async def test_extract_shape_features(self):
        """Test shape feature extraction."""
        extractor = FeatureExtractor()
        test_image = self.create_test_image(width=200, height=100)
        
        shape_features = await extractor._extract_shape_features(test_image)
        
        # Check required shape features
        required_features = ['aspect_ratio', 'compactness', 'circularity', 'rectangularity']
        
        for feature in required_features:
            assert feature in shape_features
            assert isinstance(shape_features[feature], float)
        
        # Check aspect ratio calculation
        expected_ratio = 200 / 100
        assert abs(shape_features['aspect_ratio'] - expected_ratio) < 0.01
    
    @pytest.mark.asyncio
    async def test_extract_spatial_features(self):
        """Test spatial feature extraction."""
        extractor = FeatureExtractor()
        test_image = self.create_test_image()
        
        spatial_features = await extractor._extract_spatial_features(test_image)
        
        # Check required spatial features
        required_features = ['center_focus', 'symmetry', 'density', 'spatial_variance']
        
        for feature in required_features:
            assert feature in spatial_features
            assert isinstance(spatial_features[feature], float)
    
    @pytest.mark.asyncio
    async def test_extract_content_features(self):
        """Test content feature extraction."""
        extractor = FeatureExtractor()
        test_image = self.create_test_image()
        
        content_features = await extractor._extract_content_features(test_image)
        
        # Check required content features
        required_features = ['has_text', 'has_lines', 'has_shapes', 'complexity']
        
        for feature in required_features:
            assert feature in content_features
        
        # Check boolean features
        assert isinstance(content_features['has_text'], bool)
        assert isinstance(content_features['has_lines'], bool)
        assert isinstance(content_features['has_shapes'], bool)
        
        # Check complexity score
        assert isinstance(content_features['complexity'], float)
        assert 0 <= content_features['complexity'] <= 1
    
    @pytest.mark.asyncio
    async def test_generate_embeddings(self):
        """Test embedding generation."""
        extractor = FeatureExtractor()
        test_image = self.create_test_image()
        
        embeddings = await extractor._generate_embeddings(test_image)
        
        # Check embedding properties
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == extractor.feature_dim
        assert embeddings.dtype == np.float32
    
    def test_calculate_entropy(self):
        """Test entropy calculation."""
        extractor = FeatureExtractor()
        
        # Test with uniform image (low entropy)
        uniform_array = np.full((100, 100), 128, dtype=np.uint8)
        entropy_uniform = extractor._calculate_entropy(uniform_array)
        
        # Test with random image (high entropy)
        random_array = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        entropy_random = extractor._calculate_entropy(random_array)
        
        # Random image should have higher entropy
        assert entropy_random > entropy_uniform
        assert entropy_uniform >= 0
        assert entropy_random >= 0
    
    def test_calculate_symmetry(self):
        """Test symmetry calculation."""
        extractor = FeatureExtractor()
        
        # Create perfectly symmetric image
        symmetric_array = np.zeros((100, 100, 3), dtype=np.uint8)
        for i in range(100):
            for j in range(50):
                value = (i + j) % 256
                symmetric_array[i, j] = [value, value, value]
                symmetric_array[i, 99-j] = [value, value, value]  # Mirror
        
        symmetry_score = extractor._calculate_symmetry(symmetric_array)
        
        # Should have high symmetry
        assert symmetry_score > 0.5
        assert 0 <= symmetry_score <= 1


class TestVisualContentProcessor:
    """Test cases for VisualContentProcessor class."""
    
    def create_test_image(self, width=100, height=100):
        """Create a test PIL Image."""
        img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        return Image.fromarray(img_array, mode='RGB')
    
    def image_to_bytes(self, image):
        """Convert PIL Image to bytes."""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def image_to_base64(self, image):
        """Convert PIL Image to base64 string."""
        image_bytes = self.image_to_bytes(image)
        return base64.b64encode(image_bytes).decode('utf-8')
    
    @pytest.mark.asyncio
    async def test_extract_visual_features_bytes(self):
        """Test visual feature extraction from bytes."""
        processor = VisualContentProcessor()
        test_image = self.create_test_image()
        image_bytes = self.image_to_bytes(test_image)
        
        features = await processor.extract_visual_features(image_bytes)
        
        assert isinstance(features, VisualFeatures)
        assert features.visual_embeddings.size > 0
    
    @pytest.mark.asyncio
    async def test_extract_visual_features_base64(self):
        """Test visual feature extraction from base64."""
        processor = VisualContentProcessor()
        test_image = self.create_test_image()
        base64_data = self.image_to_base64(test_image)
        
        features = await processor.extract_visual_features(base64_data)
        
        assert isinstance(features, VisualFeatures)
        assert features.visual_embeddings.size > 0
    
    @pytest.mark.asyncio
    async def test_classify_visual_elements_bytes(self):
        """Test visual element classification from bytes."""
        processor = VisualContentProcessor()
        test_image = self.create_test_image()
        image_bytes = self.image_to_bytes(test_image)
        
        elements = await processor.classify_visual_elements(image_bytes)
        
        assert isinstance(elements, list)
        for element in elements:
            assert isinstance(element, VisualElement)
            assert element.is_valid()
    
    @pytest.mark.asyncio
    async def test_classify_visual_elements_base64(self):
        """Test visual element classification from base64."""
        processor = VisualContentProcessor()
        test_image = self.create_test_image()
        base64_data = self.image_to_base64(test_image)
        
        elements = await processor.classify_visual_elements(base64_data)
        
        assert isinstance(elements, list)
        for element in elements:
            assert isinstance(element, VisualElement)
            assert element.is_valid()
    
    @pytest.mark.asyncio
    async def test_extract_quantitative_data(self):
        """Test quantitative data extraction."""
        processor = VisualContentProcessor()
        test_image = self.create_test_image()
        image_bytes = self.image_to_bytes(test_image)
        
        quant_data = await processor.extract_quantitative_data(image_bytes)
        
        assert isinstance(quant_data, QuantitativeData)
        assert quant_data.chart_type
        assert len(quant_data.data_points) > 0 or len(quant_data.data_series) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_diagram_structure(self):
        """Test diagram structure analysis."""
        processor = VisualContentProcessor()
        test_image = self.create_test_image()
        image_bytes = self.image_to_bytes(test_image)
        
        structure = await processor.analyze_diagram_structure(image_bytes)
        
        assert isinstance(structure, StructuralRelationships)
        assert len(structure.nodes) > 0
        assert structure.flow_direction
    
    @pytest.mark.asyncio
    async def test_process_document_images(self):
        """Test processing multiple document images."""
        processor = VisualContentProcessor()
        
        # Create multiple test images
        test_images = [self.create_test_image() for _ in range(3)]
        image_bytes_list = [self.image_to_bytes(img) for img in test_images]
        
        results = await processor.process_document_images(image_bytes_list)
        
        # Check result structure
        assert isinstance(results, dict)
        required_keys = [
            'visual_elements', 'visual_features', 'quantitative_data',
            'structural_relationships', 'processing_summary'
        ]
        
        for key in required_keys:
            assert key in results
        
        # Check processing summary
        summary = results['processing_summary']
        assert summary['total_images'] == 3
        assert 'total_elements' in summary
        assert 'element_types' in summary
        assert 'average_confidence' in summary
        assert 'processing_timestamp' in summary
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_image(self):
        """Test error handling for invalid image data."""
        processor = VisualContentProcessor()
        
        with pytest.raises(ValueError):
            await processor.extract_visual_features(b"invalid image data")
        
        with pytest.raises(ValueError):
            await processor.classify_visual_elements("invalid base64 data")
    
    @pytest.mark.asyncio
    async def test_process_empty_image_list(self):
        """Test processing empty image list."""
        processor = VisualContentProcessor()
        
        results = await processor.process_document_images([])
        
        assert results['processing_summary']['total_images'] == 0
        assert len(results['visual_elements']) == 0
        assert len(results['visual_features']) == 0
    
    @pytest.mark.asyncio
    async def test_process_mixed_image_formats(self):
        """Test processing mixed image formats (bytes and base64)."""
        processor = VisualContentProcessor()
        
        test_image1 = self.create_test_image()
        test_image2 = self.create_test_image()
        
        image_bytes = self.image_to_bytes(test_image1)
        image_base64 = self.image_to_base64(test_image2)
        
        mixed_list = [image_bytes, image_base64]
        
        results = await processor.process_document_images(mixed_list)
        
        assert results['processing_summary']['total_images'] == 2
        assert len(results['visual_features']) == 2


class TestIntegration:
    """Integration tests for visual processing components."""
    
    def create_chart_like_image(self):
        """Create an image that looks like a chart."""
        img_array = np.zeros((200, 400, 3), dtype=np.uint8)
        
        # Create chart-like patterns
        # Background
        img_array[:, :] = [255, 255, 255]
        
        # Draw axes
        img_array[180:185, 50:350] = [0, 0, 0]  # X-axis
        img_array[50:180, 50:55] = [0, 0, 0]    # Y-axis
        
        # Draw some data points
        for i in range(5):
            x = 80 + i * 50
            y = 160 - i * 20
            img_array[y-5:y+5, x-5:x+5] = [255, 0, 0]  # Red dots
        
        return Image.fromarray(img_array, mode='RGB')
    
    def image_to_bytes(self, image):
        """Convert PIL Image to bytes."""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()
    
    @pytest.mark.asyncio
    async def test_end_to_end_chart_processing(self):
        """Test end-to-end processing of a chart-like image."""
        processor = VisualContentProcessor()
        chart_image = self.create_chart_like_image()
        image_bytes = self.image_to_bytes(chart_image)
        
        # Extract features
        features = await processor.extract_visual_features(image_bytes)
        assert isinstance(features, VisualFeatures)
        
        # Classify elements
        elements = await processor.classify_visual_elements(image_bytes)
        assert isinstance(elements, list)
        
        # Check if chart was detected
        chart_elements = [e for e in elements if e.element_type == VisualElementType.CHART]
        
        # Extract quantitative data if chart detected
        if chart_elements:
            quant_data = await processor.extract_quantitative_data(image_bytes)
            assert isinstance(quant_data, QuantitativeData)
    
    @pytest.mark.asyncio
    async def test_processor_consistency(self):
        """Test that processor gives consistent results for same image."""
        processor = VisualContentProcessor()
        test_image = self.create_chart_like_image()
        image_bytes = self.image_to_bytes(test_image)
        
        # Process same image twice
        features1 = await processor.extract_visual_features(image_bytes)
        features2 = await processor.extract_visual_features(image_bytes)
        
        # Results should be identical (or very close due to floating point)
        assert np.allclose(features1.visual_embeddings, features2.visual_embeddings)
        
        elements1 = await processor.classify_visual_elements(image_bytes)
        elements2 = await processor.classify_visual_elements(image_bytes)
        
        # Should detect same number of elements
        assert len(elements1) == len(elements2)
    
    @pytest.mark.asyncio
    async def test_performance_with_large_image(self):
        """Test performance with larger images."""
        processor = VisualContentProcessor()
        
        # Create larger test image
        large_image = Image.new('RGB', (2000, 1500), color='white')
        image_bytes = self.image_to_bytes(large_image)
        
        # Should complete without errors (timing not critical for unit tests)
        features = await processor.extract_visual_features(image_bytes)
        elements = await processor.classify_visual_elements(image_bytes)
        
        assert isinstance(features, VisualFeatures)
        assert isinstance(elements, list)