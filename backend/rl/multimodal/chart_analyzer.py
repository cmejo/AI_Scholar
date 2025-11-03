"""
Advanced chart and graph data extraction for multi-modal learning.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
from PIL import Image, ImageDraw
import cv2
from dataclasses import dataclass
from enum import Enum

from .models import QuantitativeData, BoundingBox

logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Types of charts that can be analyzed."""
    LINE_CHART = "line"
    BAR_CHART = "bar"
    SCATTER_PLOT = "scatter"
    PIE_CHART = "pie"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box"
    AREA_CHART = "area"
    UNKNOWN = "unknown"


@dataclass
class DataPoint:
    """Represents a single data point in a chart."""
    x: float
    y: float
    label: Optional[str] = None
    series: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ChartAxis:
    """Represents a chart axis with its properties."""
    orientation: str  # "horizontal" or "vertical"
    min_value: float
    max_value: float
    labels: List[str]
    tick_positions: List[float]
    title: Optional[str] = None


@dataclass
class ChartRegion:
    """Represents a region of interest in a chart."""
    bounding_box: BoundingBox
    region_type: str  # "plot_area", "legend", "title", "axis_label"
    confidence: float


class ColorAnalyzer:
    """Analyzes colors in chart images."""
    
    @staticmethod
    def extract_dominant_colors(image: np.ndarray, k: int = 5) -> List[Tuple[int, int, int]]:
        """Extract dominant colors using k-means clustering."""
        # Reshape image to be a list of pixels
        pixels = image.reshape(-1, 3)
        
        # Remove white and very light colors (likely background)
        non_white_pixels = pixels[np.sum(pixels, axis=1) < 700]
        
        if len(non_white_pixels) == 0:
            return [(0, 0, 0)]  # Return black if no non-white pixels
        
        # Simple k-means approximation
        # In a real implementation, you'd use sklearn.cluster.KMeans
        unique_colors = []
        for _ in range(min(k, len(non_white_pixels))):
            if len(non_white_pixels) > 0:
                # Find most common color
                unique_pixels, counts = np.unique(non_white_pixels, axis=0, return_counts=True)
                most_common_idx = np.argmax(counts)
                dominant_color = tuple(unique_pixels[most_common_idx])
                unique_colors.append(dominant_color)
                
                # Remove similar colors for next iteration
                distances = np.sum((non_white_pixels - dominant_color) ** 2, axis=1)
                non_white_pixels = non_white_pixels[distances > 1000]  # Threshold for color similarity
        
        return unique_colors
    
    @staticmethod
    def detect_data_series_colors(image: np.ndarray) -> Dict[str, Tuple[int, int, int]]:
        """Detect colors used for different data series."""
        dominant_colors = ColorAnalyzer.extract_dominant_colors(image)
        
        # Assign series names to colors
        series_colors = {}
        for i, color in enumerate(dominant_colors):
            series_colors[f"series_{i+1}"] = color
        
        return series_colors


class EdgeDetector:
    """Detects edges and lines in chart images."""
    
    @staticmethod
    def detect_axes(image: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], List[Tuple[int, int, int, int]]]:
        """Detect horizontal and vertical axes in the chart."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
        
        horizontal_lines = []
        vertical_lines = []
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate angle
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                
                # Classify as horizontal or vertical
                if abs(angle) < 15 or abs(angle) > 165:  # Horizontal
                    horizontal_lines.append((x1, y1, x2, y2))
                elif abs(angle - 90) < 15 or abs(angle + 90) < 15:  # Vertical
                    vertical_lines.append((x1, y1, x2, y2))
        
        return horizontal_lines, vertical_lines
    
    @staticmethod
    def detect_plot_area(image: np.ndarray) -> Optional[BoundingBox]:
        """Detect the main plot area of the chart."""
        horizontal_lines, vertical_lines = EdgeDetector.detect_axes(image)
        
        if not horizontal_lines or not vertical_lines:
            # Fallback: assume plot area is central 70% of image
            height, width = image.shape[:2]
            margin_x = int(width * 0.15)
            margin_y = int(height * 0.15)
            return BoundingBox(
                x=margin_x,
                y=margin_y,
                width=width - 2 * margin_x,
                height=height - 2 * margin_y
            )
        
        # Find bounding box of axes
        all_x = []
        all_y = []
        
        for x1, y1, x2, y2 in horizontal_lines + vertical_lines:
            all_x.extend([x1, x2])
            all_y.extend([y1, y2])
        
        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            
            return BoundingBox(
                x=min_x,
                y=min_y,
                width=max_x - min_x,
                height=max_y - min_y
            )
        
        return None


class DataPointExtractor:
    """Extracts data points from different chart types."""
    
    def __init__(self):
        self.color_analyzer = ColorAnalyzer()
        self.edge_detector = EdgeDetector()
    
    async def extract_line_chart_data(self, image: np.ndarray, plot_area: BoundingBox) -> List[DataPoint]:
        """Extract data points from line charts."""
        data_points = []
        
        # Get the plot area
        plot_img = image[
            int(plot_area.y):int(plot_area.y + plot_area.height),
            int(plot_area.x):int(plot_area.x + plot_area.width)
        ]
        
        # Detect series colors
        series_colors = self.color_analyzer.detect_data_series_colors(plot_img)
        
        # For each series color, trace the line
        for series_name, color in series_colors.items():
            points = await self._trace_line_by_color(plot_img, color, plot_area)
            
            for point in points:
                data_points.append(DataPoint(
                    x=point[0],
                    y=point[1],
                    series=series_name,
                    confidence=0.8
                ))
        
        return data_points
    
    async def extract_bar_chart_data(self, image: np.ndarray, plot_area: BoundingBox) -> List[DataPoint]:
        """Extract data points from bar charts."""
        data_points = []
        
        # Get the plot area
        plot_img = image[
            int(plot_area.y):int(plot_area.y + plot_area.height),
            int(plot_area.x):int(plot_area.x + plot_area.width)
        ]
        
        # Convert to grayscale for bar detection
        if len(plot_img.shape) == 3:
            gray = cv2.cvtColor(plot_img, cv2.COLOR_RGB2GRAY)
        else:
            gray = plot_img
        
        # Detect rectangular regions (bars)
        bars = await self._detect_rectangular_regions(gray)
        
        for i, bar in enumerate(bars):
            # Calculate bar height and position
            bar_height = bar['height']
            bar_center_x = bar['x'] + bar['width'] / 2
            
            # Normalize coordinates to plot area
            normalized_x = bar_center_x / plot_area.width
            normalized_y = bar_height / plot_area.height
            
            data_points.append(DataPoint(
                x=normalized_x,
                y=normalized_y,
                label=f"bar_{i+1}",
                confidence=0.7
            ))
        
        return data_points
    
    async def extract_scatter_plot_data(self, image: np.ndarray, plot_area: BoundingBox) -> List[DataPoint]:
        """Extract data points from scatter plots."""
        data_points = []
        
        # Get the plot area
        plot_img = image[
            int(plot_area.y):int(plot_area.y + plot_area.height),
            int(plot_area.x):int(plot_area.x + plot_area.width)
        ]
        
        # Detect circular/point-like regions
        points = await self._detect_scatter_points(plot_img)
        
        for point in points:
            # Normalize coordinates
            normalized_x = point['x'] / plot_area.width
            normalized_y = (plot_area.height - point['y']) / plot_area.height  # Flip Y
            
            data_points.append(DataPoint(
                x=normalized_x,
                y=normalized_y,
                confidence=point['confidence']
            ))
        
        return data_points
    
    async def extract_pie_chart_data(self, image: np.ndarray, plot_area: BoundingBox) -> List[DataPoint]:
        """Extract data points from pie charts."""
        data_points = []
        
        # Get the plot area
        plot_img = image[
            int(plot_area.y):int(plot_area.y + plot_area.height),
            int(plot_area.x):int(plot_area.x + plot_area.width)
        ]
        
        # Detect pie slices by color regions
        slices = await self._detect_pie_slices(plot_img)
        
        total_area = sum(slice_data['area'] for slice_data in slices)
        
        for i, slice_data in enumerate(slices):
            # Calculate percentage
            percentage = slice_data['area'] / total_area if total_area > 0 else 0
            
            data_points.append(DataPoint(
                x=i,  # Slice index
                y=percentage,
                label=f"slice_{i+1}",
                confidence=slice_data['confidence']
            ))
        
        return data_points
    
    async def _trace_line_by_color(self, image: np.ndarray, target_color: Tuple[int, int, int], plot_area: BoundingBox) -> List[Tuple[float, float]]:
        """Trace a line of specific color in the image."""
        points = []
        
        # Create mask for target color (with some tolerance)
        tolerance = 30
        mask = np.all(np.abs(image - target_color) <= tolerance, axis=2)
        
        # Find connected components
        if len(image.shape) == 3:
            gray_mask = mask.astype(np.uint8) * 255
        else:
            gray_mask = mask
        
        # Find contours
        contours, _ = cv2.findContours(gray_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if len(contour) > 5:  # Minimum points for a line
                # Sample points along the contour
                for point in contour[::max(1, len(contour)//20)]:  # Sample every few points
                    x, y = point[0]
                    # Normalize coordinates
                    norm_x = x / plot_area.width
                    norm_y = (plot_area.height - y) / plot_area.height  # Flip Y
                    points.append((norm_x, norm_y))
        
        return points
    
    async def _detect_rectangular_regions(self, gray_image: np.ndarray) -> List[Dict[str, float]]:
        """Detect rectangular regions (bars) in grayscale image."""
        bars = []
        
        # Apply threshold to create binary image
        _, binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size and aspect ratio (bars should be taller than wide for vertical bars)
            if w > 5 and h > 10 and h > w:  # Vertical bar criteria
                bars.append({
                    'x': float(x),
                    'y': float(y),
                    'width': float(w),
                    'height': float(h),
                    'area': float(w * h)
                })
        
        return bars
    
    async def _detect_scatter_points(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect scatter plot points."""
        points = []
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Use HoughCircles to detect circular points
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=10,
            param1=50,
            param2=15,
            minRadius=2,
            maxRadius=20
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            
            for (x, y, r) in circles:
                points.append({
                    'x': float(x),
                    'y': float(y),
                    'radius': float(r),
                    'confidence': 0.8
                })
        
        return points
    
    async def _detect_pie_slices(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect pie chart slices by color segmentation."""
        slices = []
        
        # Get dominant colors
        dominant_colors = self.color_analyzer.extract_dominant_colors(image)
        
        for i, color in enumerate(dominant_colors):
            # Create mask for this color
            tolerance = 40
            mask = np.all(np.abs(image - color) <= tolerance, axis=2)
            
            # Calculate area of this color region
            area = np.sum(mask)
            
            if area > 100:  # Minimum area threshold
                slices.append({
                    'color': color,
                    'area': float(area),
                    'confidence': 0.7
                })
        
        return slices


class ChartTypeClassifier:
    """Classifies the type of chart in an image."""
    
    def __init__(self):
        self.edge_detector = EdgeDetector()
        self.color_analyzer = ColorAnalyzer()
    
    async def classify_chart_type(self, image: np.ndarray) -> Tuple[ChartType, float]:
        """Classify the type of chart and return confidence score."""
        
        # Extract features for classification
        features = await self._extract_classification_features(image)
        
        # Simple rule-based classification
        # In a real system, this would use machine learning
        
        if features['has_circular_regions'] and features['color_diversity'] > 3:
            return ChartType.PIE_CHART, 0.8
        
        elif features['vertical_bars'] > 2 and features['horizontal_lines'] > 0:
            return ChartType.BAR_CHART, 0.7
        
        elif features['scattered_points'] > 5:
            return ChartType.SCATTER_PLOT, 0.75
        
        elif features['continuous_lines'] > 0 and features['horizontal_lines'] > 0:
            return ChartType.LINE_CHART, 0.8
        
        elif features['histogram_pattern']:
            return ChartType.HISTOGRAM, 0.6
        
        else:
            return ChartType.UNKNOWN, 0.3
    
    async def _extract_classification_features(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract features used for chart type classification."""
        features = {}
        
        # Detect lines and shapes
        horizontal_lines, vertical_lines = self.edge_detector.detect_axes(image)
        
        features['horizontal_lines'] = len(horizontal_lines)
        features['vertical_lines'] = len(vertical_lines)
        
        # Color analysis
        dominant_colors = self.color_analyzer.extract_dominant_colors(image)
        features['color_diversity'] = len(dominant_colors)
        
        # Shape detection
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Detect circles (for pie charts or scatter plots)
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
            param1=50, param2=30, minRadius=10, maxRadius=100
        )
        features['has_circular_regions'] = circles is not None and len(circles[0]) > 0
        
        # Detect rectangular regions (for bar charts)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        vertical_bars = 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > w and h > 20 and w > 5:  # Vertical bar criteria
                vertical_bars += 1
        
        features['vertical_bars'] = vertical_bars
        
        # Detect scattered points
        small_circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1, minDist=5,
            param1=50, param2=15, minRadius=2, maxRadius=10
        )
        features['scattered_points'] = len(small_circles[0]) if small_circles is not None else 0
        
        # Detect continuous lines (for line charts)
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=5)
        
        continuous_lines = 0
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                if length > 50:  # Long lines might be data series
                    continuous_lines += 1
        
        features['continuous_lines'] = continuous_lines
        
        # Simple histogram pattern detection
        # Look for regular vertical patterns
        hist_pattern = False
        if vertical_bars > 3:
            # Check if bars are regularly spaced
            bar_positions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if h > w and h > 20:
                    bar_positions.append(x)
            
            if len(bar_positions) > 2:
                bar_positions.sort()
                spacings = [bar_positions[i+1] - bar_positions[i] for i in range(len(bar_positions)-1)]
                avg_spacing = np.mean(spacings)
                spacing_variance = np.var(spacings)
                
                # Regular spacing indicates histogram
                if spacing_variance < avg_spacing * 0.3:
                    hist_pattern = True
        
        features['histogram_pattern'] = hist_pattern
        
        return features


class ChartAnalyzer:
    """Main chart analyzer that coordinates all chart analysis components."""
    
    def __init__(self):
        self.classifier = ChartTypeClassifier()
        self.extractor = DataPointExtractor()
        self.edge_detector = EdgeDetector()
    
    async def analyze_chart(self, image: Union[np.ndarray, Image.Image]) -> QuantitativeData:
        """Analyze a chart image and extract quantitative data."""
        
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image
        
        try:
            # Classify chart type
            chart_type, type_confidence = await self.classifier.classify_chart_type(image_array)
            
            # Detect plot area
            plot_area = self.edge_detector.detect_plot_area(image_array)
            if plot_area is None:
                # Fallback to full image
                height, width = image_array.shape[:2]
                plot_area = BoundingBox(x=0, y=0, width=width, height=height)
            
            # Extract data points based on chart type
            data_points = []
            
            if chart_type == ChartType.LINE_CHART:
                data_points = await self.extractor.extract_line_chart_data(image_array, plot_area)
            elif chart_type == ChartType.BAR_CHART:
                data_points = await self.extractor.extract_bar_chart_data(image_array, plot_area)
            elif chart_type == ChartType.SCATTER_PLOT:
                data_points = await self.extractor.extract_scatter_plot_data(image_array, plot_area)
            elif chart_type == ChartType.PIE_CHART:
                data_points = await self.extractor.extract_pie_chart_data(image_array, plot_area)
            
            # Convert data points to QuantitativeData format
            quant_data = await self._convert_to_quantitative_data(
                data_points, chart_type, type_confidence, image_array.shape
            )
            
            logger.info(f"Analyzed {chart_type.value} chart with {len(data_points)} data points")
            return quant_data
            
        except Exception as e:
            logger.error(f"Error analyzing chart: {str(e)}")
            # Return minimal data structure
            return QuantitativeData(
                data_points=[],
                data_series={},
                axis_labels={},
                chart_type="unknown",
                metadata={
                    "error": str(e),
                    "analysis_failed": True
                }
            )
    
    async def _convert_to_quantitative_data(
        self, 
        data_points: List[DataPoint], 
        chart_type: ChartType, 
        confidence: float,
        image_shape: Tuple[int, ...]
    ) -> QuantitativeData:
        """Convert extracted data points to QuantitativeData format."""
        
        # Group data points by series
        series_data = {}
        point_data = []
        
        for point in data_points:
            # Add to point data
            point_dict = {"x": point.x, "y": point.y}
            if point.label:
                point_dict["label"] = point.label
            point_data.append(point_dict)
            
            # Group by series
            series_name = point.series or "default"
            if series_name not in series_data:
                series_data[series_name] = []
            series_data[series_name].append(point.y)
        
        # Generate axis labels (simplified)
        x_labels = []
        y_labels = []
        
        if chart_type == ChartType.PIE_CHART:
            x_labels = [f"Slice {i+1}" for i in range(len(data_points))]
            y_labels = ["Percentage"]
        else:
            # Generate generic labels
            if data_points:
                num_points = len(data_points)
                x_labels = [f"Point {i+1}" for i in range(num_points)]
                y_labels = ["Value"]
        
        return QuantitativeData(
            data_points=point_data,
            data_series=series_data,
            axis_labels={"x": x_labels, "y": y_labels},
            chart_type=chart_type.value,
            units={"x": "index", "y": "value"},
            metadata={
                "extraction_method": "advanced_chart_analysis",
                "chart_type_confidence": confidence,
                "image_dimensions": image_shape,
                "num_data_points": len(data_points),
                "num_series": len(series_data),
                "plot_area_detected": True
            }
        )