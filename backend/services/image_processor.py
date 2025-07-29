"""
Image processing service for OCR and object detection
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        # Configure Tesseract (adjust path as needed)
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        pass
    
    async def extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            # Load image
            image = Image.open(image_path)
            
            # Preprocess image for better OCR
            image = self._preprocess_image(image)
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config='--psm 6')
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            return ""
    
    async def detect_objects(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect objects in image (simplified implementation)"""
        try:
            # Load image with OpenCV
            image = cv2.imread(image_path)
            
            # Simple contour detection for basic object detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            objects = []
            for i, contour in enumerate(contours):
                if cv2.contourArea(contour) > 1000:  # Filter small objects
                    x, y, w, h = cv2.boundingRect(contour)
                    objects.append({
                        'id': i,
                        'type': 'object',
                        'bbox': [x, y, w, h],
                        'area': cv2.contourArea(contour),
                        'confidence': 0.8  # Mock confidence
                    })
            
            return objects
            
        except Exception as e:
            logger.error(f"Object detection error: {str(e)}")
            return []
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Convert to numpy array for OpenCV processing
        img_array = np.array(image)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(img_array)
        
        # Apply threshold
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL Image
        return Image.fromarray(thresh)
    
    async def extract_tables(self, image_path: str) -> List[Dict[str, Any]]:
        """Extract tables from image (basic implementation)"""
        try:
            # This is a simplified implementation
            # In production, you might use specialized table detection models
            
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect horizontal and vertical lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine lines
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find contours that might be tables
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            tables = []
            for i, contour in enumerate(contours):
                if cv2.contourArea(contour) > 5000:  # Filter small areas
                    x, y, w, h = cv2.boundingRect(contour)
                    tables.append({
                        'id': i,
                        'bbox': [x, y, w, h],
                        'type': 'table',
                        'confidence': 0.7
                    })
            
            return tables
            
        except Exception as e:
            logger.error(f"Table extraction error: {str(e)}")
            return []