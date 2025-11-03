"""
Visual content processor for multi-modal learning system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
from PIL import Image
import io
import base64
from datetime import datetime

from .models import (
    VisualElement,
    VisualElementType,
    BoundingBox,
    VisualFeatures,
    QuantitativeData,
    StructuralRelationships
)

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Base image processing utilities."""
    
    @staticmethod
    def load_image_from_bytes(image_data: bytes) -> Image.Image:
        """Load PIL Image from bytes."""
        try:
            return Image.open(io.BytesIO(image_data))
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")
    
    @staticmethod
    def load_image_from_base64(base64_data: str) -> Image.Image:
        """Load PIL Image from base64 string."""
        try:
            image_data = base64.b64decode(base64_data)
            return ImageProcessor.load_image_from_bytes(image_data)
        except Exception as e:
            raise ValueError(f"Failed to load image from base64: {str(e)}")
    
    @staticmethod
    def resize_image(image: Image.Image, max_size: Tuple[int, int] = (1024, 1024)) -> Image.Image:
        """Resize image while maintaining aspect ratio."""
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image
    
    @staticmethod
    def convert_to_rgb(image: Image.Image) -> Image.Image:
        """Convert image to RGB format."""
        if image.mode != 'RGB':
            return image.convert('RGB')
        return image
    
    @staticmethod
    def extract_basic_features(image: Image.Image) -> Dict[str, float]:
        """Extract basic image features."""
        # Convert to numpy array for analysis
        img_array = np.array(image)
        
        # Basic color statistics
        if len(img_array.shape) == 3:  # Color image
            mean_rgb = np.mean(img_array, axis=(0, 1))
            std_rgb = np.std(img_array, axis=(0, 1))
            
            features = {
                "mean_red": float(mean_rgb[0]) / 255.0,
                "mean_green": float(mean_rgb[1]) / 255.0,
                "mean_blue": float(mean_rgb[2]) / 255.0,
                "std_red": float(std_rgb[0]) / 255.0,
                "std_green": float(std_rgb[1]) / 255.0,
                "std_blue": float(std_rgb[2]) / 255.0,
                "brightness": float(np.mean(img_array)) / 255.0,
                "contrast": float(np.std(img_array)) / 255.0
            }
        else:  # Grayscale image
            features = {
                "brightness": float(np.mean(img_array)) / 255.0,
                "contrast": float(np.std(img_array)) / 255.0,
                "mean_red": 0.0,
                "mean_green": 0.0,
                "mean_blue": 0.0,
                "std_red": 0.0,
                "std_green": 0.0,
                "std_blue": 0.0
            }
        
        # Image dimensions
        height, width = img_array.shape[:2]
        features.update({
            "width": float(width),
            "height": float(height),
            "aspect_ratio": float(width) / float(height) if height > 0 else 1.0,
            "area": float(width * height)
        })
        
        return features


class ElementDetector:
    """Detects different types of visual elements in images."""
    
    def __init__(self):
        self.confidence_threshold = 0.5
    
    async def detect_elements(self, image: Image.Image) -> List[VisualElement]:
        """Detect visual elements in an image."""
        elements = []
        
        # Basic element detection based on image characteristics
        basic_features = ImageProcessor.extract_basic_features(image)
        
        # Detect potential charts/graphs based on color patterns
        chart_elements = await self._detect_charts(image, basic_features)
        elements.extend(chart_elements)
        
        # Detect potential diagrams based on structure
        diagram_elements = await self._detect_diagrams(image, basic_features)
        elements.extend(diagram_elements)
        
        # Detect potential equations (placeholder implementation)
        equation_elements = await self._detect_equations(image, basic_features)
        elements.extend(equation_elements)
        
        return elements
    
    async def _detect_charts(self, image: Image.Image, features: Dict[str, float]) -> List[VisualElement]:
        """Detect chart-like elements."""
        elements = []
        
        # Simple heuristic: high contrast images with regular patterns might be charts
        if features["contrast"] > 0.3 and features["aspect_ratio"] > 0.5:
            bbox = BoundingBox(
                x=0.0,
                y=0.0,
                width=features["width"],
                height=features["height"]
            )
            
            confidence = min(0.9, features["contrast"] * 2)  # Simple confidence calculation
            
            element = VisualElement(
                element_id=f"chart_{datetime.now().timestamp()}",
                element_type=VisualElementType.CHART,
                bounding_box=bbox,
                confidence=confidence,
                extracted_data={
                    "detection_method": "contrast_analysis",
                    "features": features
                }
            )
            elements.append(element)
        
        return elements
    
    async def _detect_diagrams(self, image: Image.Image, features: Dict[str, float]) -> List[VisualElement]:
        """Detect diagram-like elements."""
        elements = []
        
        # Simple heuristic: square-ish images with moderate contrast might be diagrams
        aspect_ratio = features["aspect_ratio"]
        if 0.7 <= aspect_ratio <= 1.3 and features["contrast"] > 0.2:
            bbox = BoundingBox(
                x=0.0,
                y=0.0,
                width=features["width"],
                height=features["height"]
            )
            
            confidence = min(0.8, (1.0 - abs(aspect_ratio - 1.0)) * features["contrast"] * 3)
            
            element = VisualElement(
                element_id=f"diagram_{datetime.now().timestamp()}",
                element_type=VisualElementType.DIAGRAM,
                bounding_box=bbox,
                confidence=confidence,
                extracted_data={
                    "detection_method": "aspect_ratio_analysis",
                    "features": features
                }
            )
            elements.append(element)
        
        return elements
    
    async def _detect_equations(self, image: Image.Image, features: Dict[str, float]) -> List[VisualElement]:
        """Detect equation-like elements."""
        elements = []
        
        # Simple heuristic: wide, short images might contain equations
        aspect_ratio = features["aspect_ratio"]
        if aspect_ratio > 2.0 and features["height"] < 100:
            bbox = BoundingBox(
                x=0.0,
                y=0.0,
                width=features["width"],
                height=features["height"]
            )
            
            confidence = min(0.7, (aspect_ratio - 2.0) * 0.2 + 0.3)
            
            element = VisualElement(
                element_id=f"equation_{datetime.now().timestamp()}",
                element_type=VisualElementType.EQUATION,
                bounding_box=bbox,
                confidence=confidence,
                extracted_data={
                    "detection_method": "aspect_ratio_analysis",
                    "features": features
                }
            )
            elements.append(element)
        
        return elements


class FeatureExtractor:
    """Extracts detailed features from visual elements."""
    
    def __init__(self):
        self.feature_dim = 256  # Dimension of visual embeddings
    
    async def extract_visual_features(self, image: Image.Image) -> VisualFeatures:
        """Extract comprehensive visual features from an image."""
        # Basic image processing
        image = ImageProcessor.convert_to_rgb(image)
        image = ImageProcessor.resize_image(image)
        
        # Extract different types of features
        color_features = await self._extract_color_features(image)
        texture_features = await self._extract_texture_features(image)
        shape_features = await self._extract_shape_features(image)
        spatial_features = await self._extract_spatial_features(image)
        content_features = await self._extract_content_features(image)
        
        # Generate visual embeddings (simplified implementation)
        visual_embeddings = await self._generate_embeddings(image)
        
        return VisualFeatures(
            visual_embeddings=visual_embeddings,
            color_features=color_features,
            texture_features=texture_features,
            shape_features=shape_features,
            spatial_features=spatial_features,
            content_features=content_features
        )
    
    async def _extract_color_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract color-based features."""
        img_array = np.array(image)
        
        # Color statistics
        mean_color = np.mean(img_array, axis=(0, 1))
        std_color = np.std(img_array, axis=(0, 1))
        
        # Color distribution
        hist_r, _ = np.histogram(img_array[:, :, 0], bins=32, range=(0, 256))
        hist_g, _ = np.histogram(img_array[:, :, 1], bins=32, range=(0, 256))
        hist_b, _ = np.histogram(img_array[:, :, 2], bins=32, range=(0, 256))
        
        # Normalize histograms
        total_pixels = img_array.shape[0] * img_array.shape[1]
        hist_r = hist_r / total_pixels
        hist_g = hist_g / total_pixels
        hist_b = hist_b / total_pixels
        
        features = {
            "mean_red": float(mean_color[0]) / 255.0,
            "mean_green": float(mean_color[1]) / 255.0,
            "mean_blue": float(mean_color[2]) / 255.0,
            "std_red": float(std_color[0]) / 255.0,
            "std_green": float(std_color[1]) / 255.0,
            "std_blue": float(std_color[2]) / 255.0,
            "brightness": float(np.mean(img_array)) / 255.0,
            "contrast": float(np.std(img_array)) / 255.0,
            "color_diversity": float(np.mean([np.std(hist_r), np.std(hist_g), np.std(hist_b)]))
        }
        
        return features
    
    async def _extract_texture_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract texture-based features."""
        # Convert to grayscale for texture analysis
        gray_image = image.convert('L')
        img_array = np.array(gray_image)
        
        # Simple texture measures
        # Gradient-based texture
        grad_x = np.abs(np.diff(img_array, axis=1))
        grad_y = np.abs(np.diff(img_array, axis=0))
        
        features = {
            "roughness": float(np.mean(grad_x) + np.mean(grad_y)) / 255.0,
            "uniformity": 1.0 - float(np.std(img_array)) / 255.0,
            "entropy": self._calculate_entropy(img_array),
            "edge_density": float(np.sum(grad_x > 30) + np.sum(grad_y > 30)) / img_array.size
        }
        
        return features
    
    async def _extract_shape_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract shape-based features."""
        # Convert to binary image for shape analysis
        gray_image = image.convert('L')
        img_array = np.array(gray_image)
        
        # Simple shape measures
        height, width = img_array.shape
        
        features = {
            "aspect_ratio": float(width) / float(height) if height > 0 else 1.0,
            "compactness": self._calculate_compactness(img_array),
            "circularity": self._calculate_circularity(img_array),
            "rectangularity": self._calculate_rectangularity(img_array)
        }
        
        return features
    
    async def _extract_spatial_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract spatial arrangement features."""
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Spatial distribution of intensity
        center_region = img_array[height//4:3*height//4, width//4:3*width//4]
        edge_regions = [
            img_array[:height//4, :],  # Top
            img_array[3*height//4:, :],  # Bottom
            img_array[:, :width//4],  # Left
            img_array[:, 3*width//4:]  # Right
        ]
        
        center_brightness = np.mean(center_region) / 255.0 if center_region.size > 0 else 0.0
        edge_brightness = np.mean([np.mean(region) for region in edge_regions if region.size > 0]) / 255.0
        
        features = {
            "center_focus": float(center_brightness - edge_brightness + 0.5),  # Normalize to [0,1]
            "symmetry": self._calculate_symmetry(img_array),
            "density": float(np.sum(img_array > 128)) / img_array.size,
            "spatial_variance": float(np.var(np.mean(img_array, axis=0))) / (255.0 ** 2)
        }
        
        return features
    
    async def _extract_content_features(self, image: Image.Image) -> Dict[str, Any]:
        """Extract content-based features."""
        img_array = np.array(image)
        
        # Simple content detection
        features = {
            "has_text": self._detect_text_regions(img_array),
            "has_lines": self._detect_line_structures(img_array),
            "has_shapes": self._detect_geometric_shapes(img_array),
            "complexity": self._calculate_visual_complexity(img_array)
        }
        
        return features
    
    async def _generate_embeddings(self, image: Image.Image) -> np.ndarray:
        """Generate visual embeddings (simplified implementation)."""
        # This is a placeholder implementation
        # In a real system, this would use a pre-trained CNN or vision transformer
        
        img_array = np.array(image)
        
        # Simple feature-based embedding
        basic_features = ImageProcessor.extract_basic_features(image)
        color_features = await self._extract_color_features(image)
        texture_features = await self._extract_texture_features(image)
        
        # Combine features into embedding
        feature_vector = []
        feature_vector.extend(basic_features.values())
        feature_vector.extend(color_features.values())
        feature_vector.extend(texture_features.values())
        
        # Pad or truncate to desired dimension
        if len(feature_vector) < self.feature_dim:
            feature_vector.extend([0.0] * (self.feature_dim - len(feature_vector)))
        else:
            feature_vector = feature_vector[:self.feature_dim]
        
        return np.array(feature_vector, dtype=np.float32)
    
    def _calculate_entropy(self, img_array: np.ndarray) -> float:
        """Calculate image entropy."""
        hist, _ = np.histogram(img_array, bins=256, range=(0, 256))
        hist = hist / np.sum(hist)  # Normalize
        hist = hist[hist > 0]  # Remove zeros
        return float(-np.sum(hist * np.log2(hist)))
    
    def _calculate_compactness(self, img_array: np.ndarray) -> float:
        """Calculate shape compactness."""
        # Simple approximation based on variance
        return 1.0 - float(np.std(img_array)) / 255.0
    
    def _calculate_circularity(self, img_array: np.ndarray) -> float:
        """Calculate shape circularity."""
        height, width = img_array.shape
        aspect_ratio = width / height if height > 0 else 1.0
        return 1.0 - abs(aspect_ratio - 1.0)  # Closer to 1 means more circular
    
    def _calculate_rectangularity(self, img_array: np.ndarray) -> float:
        """Calculate shape rectangularity."""
        # Simple measure based on edge alignment
        grad_x = np.abs(np.diff(img_array, axis=1))
        grad_y = np.abs(np.diff(img_array, axis=0))
        
        horizontal_edges = np.sum(grad_y > 30)
        vertical_edges = np.sum(grad_x > 30)
        total_edges = horizontal_edges + vertical_edges
        
        if total_edges == 0:
            return 0.0
        
        edge_ratio = min(horizontal_edges, vertical_edges) / total_edges
        return float(edge_ratio * 2)  # Normalize to [0,1]
    
    def _calculate_symmetry(self, img_array: np.ndarray) -> float:
        """Calculate image symmetry."""
        height, width = img_array.shape[:2]
        
        # Horizontal symmetry
        left_half = img_array[:, :width//2]
        right_half = img_array[:, width//2:]
        right_half_flipped = np.fliplr(right_half)
        
        # Ensure same dimensions
        min_width = min(left_half.shape[1], right_half_flipped.shape[1])
        left_half = left_half[:, :min_width]
        right_half_flipped = right_half_flipped[:, :min_width]
        
        if left_half.size > 0 and right_half_flipped.size > 0:
            symmetry = 1.0 - float(np.mean(np.abs(left_half - right_half_flipped))) / 255.0
        else:
            symmetry = 0.0
        
        return max(0.0, symmetry)
    
    def _detect_text_regions(self, img_array: np.ndarray) -> bool:
        """Simple text region detection."""
        # Look for horizontal line patterns that might indicate text
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array
        
        # Detect horizontal patterns
        horizontal_grad = np.abs(np.diff(gray, axis=0))
        horizontal_lines = np.sum(horizontal_grad > 20, axis=1)
        
        # Text regions typically have regular horizontal patterns
        regular_patterns = np.sum(horizontal_lines > gray.shape[1] * 0.1)
        return regular_patterns > gray.shape[0] * 0.1
    
    def _detect_line_structures(self, img_array: np.ndarray) -> bool:
        """Simple line structure detection."""
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array
        
        # Detect strong gradients that might indicate lines
        grad_x = np.abs(np.diff(gray, axis=1))
        grad_y = np.abs(np.diff(gray, axis=0))
        
        strong_edges = np.sum((grad_x > 50) | (grad_y > 50))
        return strong_edges > gray.size * 0.05
    
    def _detect_geometric_shapes(self, img_array: np.ndarray) -> bool:
        """Simple geometric shape detection."""
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array
        
        # Look for closed contours (simplified)
        edges = gray > np.mean(gray) + np.std(gray)
        return np.sum(edges) > gray.size * 0.02
    
    def _calculate_visual_complexity(self, img_array: np.ndarray) -> float:
        """Calculate visual complexity score."""
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array
        
        # Complexity based on gradient magnitude
        grad_x = np.abs(np.diff(gray, axis=1))
        grad_y = np.abs(np.diff(gray, axis=0))
        
        total_gradient = np.sum(grad_x) + np.sum(grad_y)
        max_possible_gradient = gray.size * 255
        
        return float(total_gradient) / max_possible_gradient if max_possible_gradient > 0 else 0.0


class VisualContentProcessor:
    """Main visual content processor that coordinates all visual analysis."""
    
    def __init__(self):
        self.element_detector = ElementDetector()
        self.feature_extractor = FeatureExtractor()
        self.processing_cache = {}
    
    async def extract_visual_features(self, image_data: Union[bytes, str]) -> VisualFeatures:
        """Extract visual features from image data."""
        try:
            # Load image
            if isinstance(image_data, str):
                image = ImageProcessor.load_image_from_base64(image_data)
            else:
                image = ImageProcessor.load_image_from_bytes(image_data)
            
            # Extract features
            features = await self.feature_extractor.extract_visual_features(image)
            
            logger.info(f"Extracted visual features with embedding dimension: {features.visual_embeddings.shape}")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting visual features: {str(e)}")
            raise
    
    async def classify_visual_elements(self, image_data: Union[bytes, str]) -> List[VisualElement]:
        """Classify visual elements in image data."""
        try:
            # Load image
            if isinstance(image_data, str):
                image = ImageProcessor.load_image_from_base64(image_data)
            else:
                image = ImageProcessor.load_image_from_bytes(image_data)
            
            # Detect elements
            elements = await self.element_detector.detect_elements(image)
            
            logger.info(f"Detected {len(elements)} visual elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error classifying visual elements: {str(e)}")
            raise
    
    async def extract_quantitative_data(self, chart_image: Union[bytes, str]) -> QuantitativeData:
        """Extract quantitative data from chart images."""
        # This is a placeholder implementation
        # In a real system, this would use specialized chart parsing libraries
        
        try:
            # Load image
            if isinstance(chart_image, str):
                image = ImageProcessor.load_image_from_base64(chart_image)
            else:
                image = ImageProcessor.load_image_from_bytes(chart_image)
            
            # Simple mock data extraction
            # In reality, this would analyze the chart structure and extract actual data
            mock_data = QuantitativeData(
                data_points=[
                    {"x": 1.0, "y": 2.0},
                    {"x": 2.0, "y": 4.0},
                    {"x": 3.0, "y": 3.0}
                ],
                data_series={
                    "series1": [2.0, 4.0, 3.0, 5.0, 1.0]
                },
                axis_labels={
                    "x": ["Jan", "Feb", "Mar", "Apr", "May"],
                    "y": ["Low", "Medium", "High"]
                },
                chart_type="line",
                metadata={
                    "extraction_method": "mock_extraction",
                    "confidence": 0.6,
                    "image_size": image.size
                }
            )
            
            logger.info("Extracted quantitative data from chart")
            return mock_data
            
        except Exception as e:
            logger.error(f"Error extracting quantitative data: {str(e)}")
            raise
    
    async def analyze_diagram_structure(self, diagram_image: Union[bytes, str]) -> StructuralRelationships:
        """Analyze structural relationships in diagrams."""
        # This is a placeholder implementation
        # In a real system, this would use computer vision to detect nodes and edges
        
        try:
            # Load image
            if isinstance(diagram_image, str):
                image = ImageProcessor.load_image_from_base64(diagram_image)
            else:
                image = ImageProcessor.load_image_from_bytes(diagram_image)
            
            # Simple mock structure analysis
            mock_structure = StructuralRelationships(
                nodes=[
                    {"id": "node1", "label": "Start", "x": 100, "y": 50},
                    {"id": "node2", "label": "Process", "x": 200, "y": 150},
                    {"id": "node3", "label": "Decision", "x": 300, "y": 100},
                    {"id": "node4", "label": "End", "x": 400, "y": 200}
                ],
                edges=[
                    {"source": "node1", "target": "node2", "type": "flow"},
                    {"source": "node2", "target": "node3", "type": "flow"},
                    {"source": "node3", "target": "node4", "type": "flow"}
                ],
                hierarchy_levels={
                    "node1": 0,
                    "node2": 1,
                    "node3": 1,
                    "node4": 2
                },
                flow_direction="top-down",
                relationship_types={
                    "flow": "sequential_process"
                },
                metadata={
                    "extraction_method": "mock_analysis",
                    "confidence": 0.7,
                    "image_size": image.size
                }
            )
            
            logger.info("Analyzed diagram structure")
            return mock_structure
            
        except Exception as e:
            logger.error(f"Error analyzing diagram structure: {str(e)}")
            raise
    
    async def process_document_images(self, image_list: List[Union[bytes, str]]) -> Dict[str, Any]:
        """Process multiple images from a document."""
        results = {
            "visual_elements": [],
            "visual_features": [],
            "quantitative_data": [],
            "structural_relationships": [],
            "processing_summary": {}
        }
        
        try:
            for i, image_data in enumerate(image_list):
                logger.info(f"Processing image {i+1}/{len(image_list)}")
                
                # Classify elements
                elements = await self.classify_visual_elements(image_data)
                results["visual_elements"].extend(elements)
                
                # Extract features
                features = await self.extract_visual_features(image_data)
                results["visual_features"].append(features)
                
                # Process specific element types
                for element in elements:
                    if element.element_type == VisualElementType.CHART:
                        try:
                            quant_data = await self.extract_quantitative_data(image_data)
                            results["quantitative_data"].append(quant_data)
                        except Exception as e:
                            logger.warning(f"Failed to extract quantitative data: {str(e)}")
                    
                    elif element.element_type == VisualElementType.DIAGRAM:
                        try:
                            struct_data = await self.analyze_diagram_structure(image_data)
                            results["structural_relationships"].append(struct_data)
                        except Exception as e:
                            logger.warning(f"Failed to analyze diagram structure: {str(e)}")
            
            # Generate processing summary
            results["processing_summary"] = {
                "total_images": len(image_list),
                "total_elements": len(results["visual_elements"]),
                "element_types": {
                    elem_type.value: len([e for e in results["visual_elements"] if e.element_type == elem_type])
                    for elem_type in VisualElementType
                },
                "average_confidence": np.mean([e.confidence for e in results["visual_elements"]]) if results["visual_elements"] else 0.0,
                "processing_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Completed processing {len(image_list)} images")
            return results
            
        except Exception as e:
            logger.error(f"Error processing document images: {str(e)}")
            raise