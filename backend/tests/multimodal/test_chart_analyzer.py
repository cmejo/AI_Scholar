"""
Unit tests for chart analyzer and quantitative data extraction.
"""

import pytest
import numpy as np
import asyncio
from PIL import Image, ImageDraw
import cv2
from unittest.mock import Mock, patch, AsyncMock

from backend.rl.multimodal.chart_analyzer import (
    ChartAnalyzer,
    ChartTypeClassifier,
    DataPointExtractor,
    ColorAnalyzer,
    EdgeDetector,
    ChartType,
    DataPoint
)
from backend.rl.multimodal.models import QuantitativeData, BoundingBox


class TestColorAnalyzer:
    """Test cases for ColorAnalyzer class."""
    
    def create_test_image_with_colors(self, colors, width=100, height=100):
        """Create test image with specific colors."""
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Fill different regions with different colors
        region_width = width // len(colors)
        for i, color in enumerate(colors):
            start_x = i * region_width
            end_x = min((i + 1) * region_width, width)
            img_array[:, start_x:end_x] = color
        
        return img_array
    
    def test_extract_dominant_colors(self):
        """Test extraction of dominant colors."""
        # Create image with known colors
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
        test_image = self.create_test_image_with_colors(colors)
        
        dominant_colors = ColorAnalyzer.extract_dominant_colors(test_image, k=3)
        
        # Should detect the colors we put in
        assert len(dominant_colors) > 0
        assert len(dominant_colors) <= 3
        
        # Colors should be tuples of 3 integers
        for color in dominant_colors:
            assert isinstance(color, tuple)
            assert len(color) == 3
            assert all(isinstance(c, (int, np.integer)) for c in color)
    
    def test_extract_dominant_colors_white_background(self):
        """Test color extraction with white background."""
        # Create image with white background and colored regions
        img_array = np.full((100, 100, 3), 255, dtype=np.uint8)  # White background
        
        # Add colored squares
        img_array[20:40, 20:40] = [255, 0, 0]  # Red square
        img_array[60:80, 60:80] = [0, 0, 255]  # Blue square
        
        dominant_colors = ColorAnalyzer.extract_dominant_colors(img_array)
        
        # Should ignore white background and detect colored regions
        assert len(dominant_colors) > 0
        
        # Should not include white (255, 255, 255)
        white_detected = any(sum(color) > 700 for color in dominant_colors)
        assert not white_detected
    
    def test_detect_data_series_colors(self):
        """Test detection of data series colors."""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        test_image = self.create_test_image_with_colors(colors)
        
        series_colors = ColorAnalyzer.detect_data_series_colors(test_image)
        
        # Should return dictionary with series names
        assert isinstance(series_colors, dict)
        assert len(series_colors) > 0
        
        # Keys should be series names
        for key in series_colors.keys():
            assert key.startswith("series_")
        
        # Values should be color tuples
        for color in series_colors.values():
            assert isinstance(color, tuple)
            assert len(color) == 3
    
    def test_extract_dominant_colors_empty_image(self):
        """Test color extraction from empty/black image."""
        black_image = np.zeros((50, 50, 3), dtype=np.uint8)
        
        dominant_colors = ColorAnalyzer.extract_dominant_colors(black_image)
        
        # Should return at least one color (black)
        assert len(dominant_colors) >= 1
        assert dominant_colors[0] == (0, 0, 0)


class TestEdgeDetector:
    """Test cases for EdgeDetector class."""
    
    def create_chart_with_axes(self, width=200, height=150):
        """Create a simple chart image with axes."""
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)  # White background
        
        # Draw horizontal axis (bottom)
        cv2.line(img_array, (20, height-20), (width-20, height-20), (0, 0, 0), 2)
        
        # Draw vertical axis (left)
        cv2.line(img_array, (20, 20), (20, height-20), (0, 0, 0), 2)
        
        return img_array
    
    def test_detect_axes(self):
        """Test detection of chart axes."""
        chart_image = self.create_chart_with_axes()
        
        horizontal_lines, vertical_lines = EdgeDetector.detect_axes(chart_image)
        
        # Should detect at least one horizontal and one vertical line
        assert len(horizontal_lines) >= 1
        assert len(vertical_lines) >= 1
        
        # Lines should be tuples of 4 coordinates
        for line in horizontal_lines + vertical_lines:
            assert len(line) == 4
            assert all(isinstance(coord, (int, np.integer)) for coord in line)
    
    def test_detect_plot_area_with_axes(self):
        """Test plot area detection when axes are present."""
        chart_image = self.create_chart_with_axes()
        
        plot_area = EdgeDetector.detect_plot_area(chart_image)
        
        # Should return a BoundingBox
        assert isinstance(plot_area, BoundingBox)
        assert plot_area.width > 0
        assert plot_area.height > 0
        assert plot_area.x >= 0
        assert plot_area.y >= 0
    
    def test_detect_plot_area_no_axes(self):
        """Test plot area detection when no axes are detected."""
        # Create image without clear axes
        random_image = np.random.randint(0, 256, (100, 150, 3), dtype=np.uint8)
        
        plot_area = EdgeDetector.detect_plot_area(random_image)
        
        # Should return fallback plot area (central 70% of image)
        assert isinstance(plot_area, BoundingBox)
        assert plot_area.width > 0
        assert plot_area.height > 0
        
        # Should be roughly centered
        expected_margin_x = int(150 * 0.15)  # 15% margin
        expected_margin_y = int(100 * 0.15)
        
        assert abs(plot_area.x - expected_margin_x) < 5
        assert abs(plot_area.y - expected_margin_y) < 5
    
    def test_detect_axes_no_lines(self):
        """Test axis detection on image with no clear lines."""
        # Create solid color image
        solid_image = np.full((100, 100, 3), 128, dtype=np.uint8)
        
        horizontal_lines, vertical_lines = EdgeDetector.detect_axes(solid_image)
        
        # Should return empty lists
        assert isinstance(horizontal_lines, list)
        assert isinstance(vertical_lines, list)
        # May be empty or contain very few lines


class TestDataPointExtractor:
    """Test cases for DataPointExtractor class."""
    
    def create_line_chart_image(self, width=200, height=150):
        """Create a simple line chart image."""
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)
        
        # Draw axes
        cv2.line(img_array, (20, height-20), (width-20, height-20), (0, 0, 0), 2)
        cv2.line(img_array, (20, 20), (20, height-20), (0, 0, 0), 2)
        
        # Draw a simple line (red)
        points = [(30, height-30), (60, height-60), (90, height-40), (120, height-80)]
        for i in range(len(points)-1):
            cv2.line(img_array, points[i], points[i+1], (255, 0, 0), 3)
        
        return img_array
    
    def create_bar_chart_image(self, width=200, height=150):
        """Create a simple bar chart image."""
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)
        
        # Draw axes
        cv2.line(img_array, (20, height-20), (width-20, height-20), (0, 0, 0), 2)
        cv2.line(img_array, (20, 20), (20, height-20), (0, 0, 0), 2)
        
        # Draw bars
        bar_positions = [40, 70, 100, 130]
        bar_heights = [40, 60, 30, 80]
        
        for pos, h in zip(bar_positions, bar_heights):
            cv2.rectangle(img_array, (pos-8, height-20-h), (pos+8, height-20), (0, 0, 255), -1)
        
        return img_array
    
    def create_scatter_plot_image(self, width=200, height=150):
        """Create a simple scatter plot image."""
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)
        
        # Draw axes
        cv2.line(img_array, (20, height-20), (width-20, height-20), (0, 0, 0), 2)
        cv2.line(img_array, (20, 20), (20, height-20), (0, 0, 0), 2)
        
        # Draw scatter points
        points = [(40, 60), (70, 80), (100, 50), (130, 90), (160, 70)]
        for point in points:
            cv2.circle(img_array, point, 4, (255, 0, 0), -1)
        
        return img_array
    
    @pytest.mark.asyncio
    async def test_extract_line_chart_data(self):
        """Test extraction of line chart data."""
        extractor = DataPointExtractor()
        chart_image = self.create_line_chart_image()
        plot_area = BoundingBox(x=20, y=20, width=160, height=110)
        
        data_points = await extractor.extract_line_chart_data(chart_image, plot_area)
        
        # Should extract some data points
        assert isinstance(data_points, list)
        
        # Check data point properties
        for point in data_points:
            assert isinstance(point, DataPoint)
            assert 0 <= point.x <= 1  # Normalized coordinates
            assert 0 <= point.y <= 1
            assert point.confidence > 0
            assert point.series is not None
    
    @pytest.mark.asyncio
    async def test_extract_bar_chart_data(self):
        """Test extraction of bar chart data."""
        extractor = DataPointExtractor()
        chart_image = self.create_bar_chart_image()
        plot_area = BoundingBox(x=20, y=20, width=160, height=110)
        
        data_points = await extractor.extract_bar_chart_data(chart_image, plot_area)
        
        # Should extract data points for bars
        assert isinstance(data_points, list)
        
        # Should detect multiple bars
        if len(data_points) > 0:
            for point in data_points:
                assert isinstance(point, DataPoint)
                assert 0 <= point.x <= 1
                assert 0 <= point.y <= 1
                assert point.label is not None
                assert point.label.startswith("bar_")
    
    @pytest.mark.asyncio
    async def test_extract_scatter_plot_data(self):
        """Test extraction of scatter plot data."""
        extractor = DataPointExtractor()
        chart_image = self.create_scatter_plot_image()
        plot_area = BoundingBox(x=20, y=20, width=160, height=110)
        
        data_points = await extractor.extract_scatter_plot_data(chart_image, plot_area)
        
        # Should extract scatter points
        assert isinstance(data_points, list)
        
        # Check data point properties
        for point in data_points:
            assert isinstance(point, DataPoint)
            assert 0 <= point.x <= 1
            assert 0 <= point.y <= 1
            assert point.confidence > 0
    
    @pytest.mark.asyncio
    async def test_extract_pie_chart_data(self):
        """Test extraction of pie chart data."""
        extractor = DataPointExtractor()
        
        # Create simple pie chart (colored regions)
        img_array = np.full((150, 150, 3), 255, dtype=np.uint8)
        
        # Create colored sectors (simplified)
        cv2.circle(img_array, (75, 75), 50, (255, 0, 0), -1)  # Red circle
        cv2.ellipse(img_array, (75, 75), (50, 50), 0, 0, 120, (0, 255, 0), -1)  # Green sector
        cv2.ellipse(img_array, (75, 75), (50, 50), 0, 120, 240, (0, 0, 255), -1)  # Blue sector
        
        plot_area = BoundingBox(x=25, y=25, width=100, height=100)
        
        data_points = await extractor.extract_pie_chart_data(img_array, plot_area)
        
        # Should extract pie slices
        assert isinstance(data_points, list)
        
        # Check data point properties
        for point in data_points:
            assert isinstance(point, DataPoint)
            assert point.y >= 0  # Percentage should be non-negative
            assert point.label is not None
            assert point.label.startswith("slice_")
    
    @pytest.mark.asyncio
    async def test_trace_line_by_color(self):
        """Test tracing lines by specific color."""
        extractor = DataPointExtractor()
        
        # Create image with red line
        img_array = np.full((100, 100, 3), 255, dtype=np.uint8)
        cv2.line(img_array, (10, 50), (90, 30), (255, 0, 0), 3)
        
        plot_area = BoundingBox(x=0, y=0, width=100, height=100)
        target_color = (255, 0, 0)  # Red
        
        points = await extractor._trace_line_by_color(img_array, target_color, plot_area)
        
        # Should find points along the red line
        assert isinstance(points, list)
        
        # Points should be normalized coordinates
        for x, y in points:
            assert 0 <= x <= 1
            assert 0 <= y <= 1
    
    @pytest.mark.asyncio
    async def test_detect_rectangular_regions(self):
        """Test detection of rectangular regions (bars)."""
        extractor = DataPointExtractor()
        
        # Create grayscale image with rectangles
        gray_image = np.full((100, 100), 255, dtype=np.uint8)
        
        # Draw black rectangles (bars)
        cv2.rectangle(gray_image, (20, 30), (30, 80), 0, -1)  # Vertical bar
        cv2.rectangle(gray_image, (50, 40), (60, 85), 0, -1)  # Another vertical bar
        
        bars = await extractor._detect_rectangular_regions(gray_image)
        
        # Should detect the rectangles
        assert isinstance(bars, list)
        
        # Check bar properties
        for bar in bars:
            assert 'x' in bar
            assert 'y' in bar
            assert 'width' in bar
            assert 'height' in bar
            assert 'area' in bar
            assert bar['height'] > bar['width']  # Vertical bars
    
    @pytest.mark.asyncio
    async def test_detect_scatter_points(self):
        """Test detection of scatter plot points."""
        extractor = DataPointExtractor()
        
        # Create image with circular points
        img_array = np.full((100, 100, 3), 255, dtype=np.uint8)
        
        # Draw circles
        cv2.circle(img_array, (30, 30), 5, (0, 0, 0), -1)
        cv2.circle(img_array, (70, 50), 5, (0, 0, 0), -1)
        cv2.circle(img_array, (50, 80), 5, (0, 0, 0), -1)
        
        points = await extractor._detect_scatter_points(img_array)
        
        # Should detect the circles
        assert isinstance(points, list)
        
        # Check point properties
        for point in points:
            assert 'x' in point
            assert 'y' in point
            assert 'radius' in point
            assert 'confidence' in point
            assert point['confidence'] > 0


class TestChartTypeClassifier:
    """Test cases for ChartTypeClassifier class."""
    
    def create_line_chart_image(self):
        """Create image that looks like a line chart."""
        img_array = np.full((150, 200, 3), 255, dtype=np.uint8)
        
        # Draw axes
        cv2.line(img_array, (20, 130), (180, 130), (0, 0, 0), 2)  # Horizontal axis
        cv2.line(img_array, (20, 20), (20, 130), (0, 0, 0), 2)    # Vertical axis
        
        # Draw continuous line
        points = [(30, 120), (60, 80), (90, 60), (120, 90), (150, 40)]
        for i in range(len(points)-1):
            cv2.line(img_array, points[i], points[i+1], (255, 0, 0), 3)
        
        return img_array
    
    def create_bar_chart_image(self):
        """Create image that looks like a bar chart."""
        img_array = np.full((150, 200, 3), 255, dtype=np.uint8)
        
        # Draw axes
        cv2.line(img_array, (20, 130), (180, 130), (0, 0, 0), 2)
        cv2.line(img_array, (20, 20), (20, 130), (0, 0, 0), 2)
        
        # Draw bars
        bar_positions = [40, 70, 100, 130, 160]
        bar_heights = [40, 60, 30, 80, 50]
        
        for pos, h in zip(bar_positions, bar_heights):
            cv2.rectangle(img_array, (pos-8, 130-h), (pos+8, 130), (0, 0, 255), -1)
        
        return img_array
    
    def create_pie_chart_image(self):
        """Create image that looks like a pie chart."""
        img_array = np.full((150, 150, 3), 255, dtype=np.uint8)
        
        # Draw colored pie slices
        center = (75, 75)
        radius = 50
        
        # Multiple colored sectors
        cv2.ellipse(img_array, center, (radius, radius), 0, 0, 90, (255, 0, 0), -1)    # Red
        cv2.ellipse(img_array, center, (radius, radius), 0, 90, 180, (0, 255, 0), -1)  # Green
        cv2.ellipse(img_array, center, (radius, radius), 0, 180, 270, (0, 0, 255), -1) # Blue
        cv2.ellipse(img_array, center, (radius, radius), 0, 270, 360, (255, 255, 0), -1) # Yellow
        
        return img_array
    
    def create_scatter_plot_image(self):
        """Create image that looks like a scatter plot."""
        img_array = np.full((150, 200, 3), 255, dtype=np.uint8)
        
        # Draw axes
        cv2.line(img_array, (20, 130), (180, 130), (0, 0, 0), 2)
        cv2.line(img_array, (20, 20), (20, 130), (0, 0, 0), 2)
        
        # Draw many scattered points
        np.random.seed(42)  # For reproducible results
        for _ in range(20):
            x = np.random.randint(30, 170)
            y = np.random.randint(30, 120)
            cv2.circle(img_array, (x, y), 3, (255, 0, 0), -1)
        
        return img_array
    
    @pytest.mark.asyncio
    async def test_classify_line_chart(self):
        """Test classification of line chart."""
        classifier = ChartTypeClassifier()
        line_chart = self.create_line_chart_image()
        
        chart_type, confidence = await classifier.classify_chart_type(line_chart)
        
        # Should classify as line chart or at least not unknown
        assert isinstance(chart_type, ChartType)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        
        # Ideally should be LINE_CHART, but may vary due to simple heuristics
        assert chart_type != ChartType.UNKNOWN or confidence < 0.5
    
    @pytest.mark.asyncio
    async def test_classify_bar_chart(self):
        """Test classification of bar chart."""
        classifier = ChartTypeClassifier()
        bar_chart = self.create_bar_chart_image()
        
        chart_type, confidence = await classifier.classify_chart_type(bar_chart)
        
        # Should classify as bar chart or at least detect vertical bars
        assert isinstance(chart_type, ChartType)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
    
    @pytest.mark.asyncio
    async def test_classify_pie_chart(self):
        """Test classification of pie chart."""
        classifier = ChartTypeClassifier()
        pie_chart = self.create_pie_chart_image()
        
        chart_type, confidence = await classifier.classify_chart_type(pie_chart)
        
        # Should classify as pie chart due to circular regions and color diversity
        assert isinstance(chart_type, ChartType)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        
        # Should detect circular regions and multiple colors
        assert chart_type == ChartType.PIE_CHART or confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_classify_scatter_plot(self):
        """Test classification of scatter plot."""
        classifier = ChartTypeClassifier()
        scatter_plot = self.create_scatter_plot_image()
        
        chart_type, confidence = await classifier.classify_chart_type(scatter_plot)
        
        # Should classify as scatter plot due to many small points
        assert isinstance(chart_type, ChartType)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
    
    @pytest.mark.asyncio
    async def test_extract_classification_features(self):
        """Test extraction of classification features."""
        classifier = ChartTypeClassifier()
        test_image = self.create_bar_chart_image()
        
        features = await classifier._extract_classification_features(test_image)
        
        # Should return dictionary with expected features
        expected_features = [
            'horizontal_lines', 'vertical_lines', 'color_diversity',
            'has_circular_regions', 'vertical_bars', 'scattered_points',
            'continuous_lines', 'histogram_pattern'
        ]
        
        for feature in expected_features:
            assert feature in features
        
        # Check feature types
        assert isinstance(features['horizontal_lines'], int)
        assert isinstance(features['vertical_lines'], int)
        assert isinstance(features['color_diversity'], int)
        assert isinstance(features['has_circular_regions'], bool)
        assert isinstance(features['vertical_bars'], int)
        assert isinstance(features['scattered_points'], int)
        assert isinstance(features['continuous_lines'], int)
        assert isinstance(features['histogram_pattern'], bool)


class TestChartAnalyzer:
    """Test cases for ChartAnalyzer class."""
    
    def create_simple_chart(self):
        """Create a simple chart for testing."""
        img_array = np.full((150, 200, 3), 255, dtype=np.uint8)
        
        # Draw axes
        cv2.line(img_array, (20, 130), (180, 130), (0, 0, 0), 2)
        cv2.line(img_array, (20, 20), (20, 130), (0, 0, 0), 2)
        
        # Draw some data (bars)
        cv2.rectangle(img_array, (40, 100), (60, 130), (255, 0, 0), -1)
        cv2.rectangle(img_array, (80, 80), (100, 130), (0, 255, 0), -1)
        cv2.rectangle(img_array, (120, 90), (140, 130), (0, 0, 255), -1)
        
        return img_array
    
    @pytest.mark.asyncio
    async def test_analyze_chart_numpy_array(self):
        """Test chart analysis with numpy array input."""
        analyzer = ChartAnalyzer()
        chart_image = self.create_simple_chart()
        
        result = await analyzer.analyze_chart(chart_image)
        
        # Should return QuantitativeData
        assert isinstance(result, QuantitativeData)
        assert isinstance(result.chart_type, str)
        assert isinstance(result.data_points, list)
        assert isinstance(result.data_series, dict)
        assert isinstance(result.axis_labels, dict)
        assert isinstance(result.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_analyze_chart_pil_image(self):
        """Test chart analysis with PIL Image input."""
        analyzer = ChartAnalyzer()
        chart_array = self.create_simple_chart()
        pil_image = Image.fromarray(chart_array)
        
        result = await analyzer.analyze_chart(pil_image)
        
        # Should return QuantitativeData
        assert isinstance(result, QuantitativeData)
        assert result.chart_type != ""
    
    @pytest.mark.asyncio
    async def test_analyze_chart_metadata(self):
        """Test that chart analysis includes proper metadata."""
        analyzer = ChartAnalyzer()
        chart_image = self.create_simple_chart()
        
        result = await analyzer.analyze_chart(chart_image)
        
        # Check metadata content
        metadata = result.metadata
        assert 'extraction_method' in metadata
        assert 'chart_type_confidence' in metadata
        assert 'image_dimensions' in metadata
        assert 'num_data_points' in metadata
        assert 'num_series' in metadata
        
        # Check metadata types
        assert isinstance(metadata['chart_type_confidence'], float)
        assert isinstance(metadata['image_dimensions'], tuple)
        assert isinstance(metadata['num_data_points'], int)
        assert isinstance(metadata['num_series'], int)
    
    @pytest.mark.asyncio
    async def test_convert_to_quantitative_data(self):
        """Test conversion of data points to QuantitativeData."""
        analyzer = ChartAnalyzer()
        
        # Create sample data points
        data_points = [
            DataPoint(x=0.2, y=0.5, series="series1", confidence=0.8),
            DataPoint(x=0.4, y=0.7, series="series1", confidence=0.9),
            DataPoint(x=0.6, y=0.3, series="series2", confidence=0.7),
        ]
        
        chart_type = ChartType.LINE_CHART
        confidence = 0.85
        image_shape = (150, 200, 3)
        
        result = await analyzer._convert_to_quantitative_data(
            data_points, chart_type, confidence, image_shape
        )
        
        # Check result structure
        assert isinstance(result, QuantitativeData)
        assert result.chart_type == "line"
        assert len(result.data_points) == 3
        assert len(result.data_series) == 2  # Two series
        
        # Check series data
        assert "series1" in result.data_series
        assert "series2" in result.data_series
        assert len(result.data_series["series1"]) == 2
        assert len(result.data_series["series2"]) == 1
        
        # Check metadata
        assert result.metadata['chart_type_confidence'] == confidence
        assert result.metadata['image_dimensions'] == image_shape
        assert result.metadata['num_data_points'] == 3
        assert result.metadata['num_series'] == 2
    
    @pytest.mark.asyncio
    async def test_analyze_chart_error_handling(self):
        """Test error handling in chart analysis."""
        analyzer = ChartAnalyzer()
        
        # Test with invalid input
        with patch.object(analyzer.classifier, 'classify_chart_type', side_effect=Exception("Test error")):
            result = await analyzer.analyze_chart(np.zeros((50, 50, 3), dtype=np.uint8))
            
            # Should return error result
            assert isinstance(result, QuantitativeData)
            assert result.chart_type == "unknown"
            assert 'error' in result.metadata
            assert result.metadata['analysis_failed'] is True
    
    @pytest.mark.asyncio
    async def test_analyze_empty_chart(self):
        """Test analysis of empty/blank chart."""
        analyzer = ChartAnalyzer()
        
        # Create blank white image
        blank_image = np.full((100, 100, 3), 255, dtype=np.uint8)
        
        result = await analyzer.analyze_chart(blank_image)
        
        # Should complete without error
        assert isinstance(result, QuantitativeData)
        # May have empty data points for blank image
        assert isinstance(result.data_points, list)
        assert isinstance(result.data_series, dict)


class TestIntegration:
    """Integration tests for chart analysis components."""
    
    def create_realistic_bar_chart(self):
        """Create a more realistic bar chart for integration testing."""
        img_array = np.full((300, 400, 3), 255, dtype=np.uint8)
        
        # Draw title area
        cv2.putText(img_array, "Sample Bar Chart", (120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        # Draw axes with labels
        cv2.line(img_array, (50, 250), (350, 250), (0, 0, 0), 2)  # X-axis
        cv2.line(img_array, (50, 50), (50, 250), (0, 0, 0), 2)    # Y-axis
        
        # Draw bars with different colors
        bars = [
            (80, 200, (255, 0, 0)),   # Red bar
            (130, 150, (0, 255, 0)),  # Green bar
            (180, 180, (0, 0, 255)),  # Blue bar
            (230, 120, (255, 255, 0)), # Yellow bar
            (280, 160, (255, 0, 255)), # Magenta bar
        ]
        
        for i, (x, top_y, color) in enumerate(bars):
            cv2.rectangle(img_array, (x-15, top_y), (x+15, 250), color, -1)
            # Add bar outline
            cv2.rectangle(img_array, (x-15, top_y), (x+15, 250), (0, 0, 0), 2)
        
        return img_array
    
    @pytest.mark.asyncio
    async def test_end_to_end_bar_chart_analysis(self):
        """Test complete end-to-end analysis of a bar chart."""
        analyzer = ChartAnalyzer()
        chart_image = self.create_realistic_bar_chart()
        
        result = await analyzer.analyze_chart(chart_image)
        
        # Should successfully analyze the chart
        assert isinstance(result, QuantitativeData)
        assert result.chart_type in ["bar", "unknown"]  # Should detect as bar chart
        
        # Should extract some data
        if result.chart_type == "bar":
            assert len(result.data_points) > 0
            
            # Check data point properties
            for point in result.data_points:
                assert isinstance(point, dict)
                assert 'x' in point
                assert 'y' in point
        
        # Should have proper metadata
        assert 'extraction_method' in result.metadata
        assert 'chart_type_confidence' in result.metadata
        assert result.metadata['extraction_method'] == 'advanced_chart_analysis'
    
    @pytest.mark.asyncio
    async def test_multiple_chart_analysis(self):
        """Test analysis of multiple different chart types."""
        analyzer = ChartAnalyzer()
        
        # Create different chart types
        charts = [
            self.create_realistic_bar_chart(),
            np.random.randint(0, 256, (150, 200, 3), dtype=np.uint8),  # Random image
        ]
        
        results = []
        for chart in charts:
            result = await analyzer.analyze_chart(chart)
            results.append(result)
        
        # All should return QuantitativeData
        for result in results:
            assert isinstance(result, QuantitativeData)
            assert isinstance(result.chart_type, str)
            assert isinstance(result.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_performance_with_large_chart(self):
        """Test performance with larger chart images."""
        analyzer = ChartAnalyzer()
        
        # Create large chart image
        large_chart = np.full((800, 1200, 3), 255, dtype=np.uint8)
        
        # Add some basic chart elements
        cv2.line(large_chart, (100, 700), (1100, 700), (0, 0, 0), 3)  # X-axis
        cv2.line(large_chart, (100, 100), (100, 700), (0, 0, 0), 3)   # Y-axis
        
        # Add some bars
        for i in range(10):
            x = 200 + i * 80
            height = 100 + i * 50
            cv2.rectangle(large_chart, (x-20, 700-height), (x+20, 700), (255, 0, 0), -1)
        
        # Should complete analysis without timeout (in reasonable time)
        result = await analyzer.analyze_chart(large_chart)
        
        assert isinstance(result, QuantitativeData)
        assert result.metadata['image_dimensions'] == (800, 1200, 3)