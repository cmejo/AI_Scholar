#!/usr/bin/env python3
"""
Multi-Modal RAG Enhancement
Supports images, tables, charts, and complex document structures
"""

import cv2
import pytesseract
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

class MultiModalRAG:
    def __init__(self):
        # Initialize vision models
        self.image_captioner = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        
        # Document processors
        self.processors = {
            'image': self._process_image,
            'table': self._process_table,
            'chart': self._process_chart,
            'diagram': self._process_diagram,
            'code': self._process_code_snippet
        }
    
    def _process_image(self, image_path: str) -> dict:
        """Extract information from images using OCR and captioning"""
        image = Image.open(image_path)
        
        # Generate caption
        inputs = self.image_captioner(image, return_tensors="pt")
        out = self.caption_model.generate(**inputs, max_length=50)
        caption = self.image_captioner.decode(out[0], skip_special_tokens=True)
        
        # Extract text using OCR
        ocr_text = pytesseract.image_to_string(image)
        
        return {
            'type': 'image',
            'caption': caption,
            'extracted_text': ocr_text,
            'searchable_content': f"{caption} {ocr_text}",
            'metadata': {
                'size': image.size,
                'format': image.format
            }
        }
    
    def _process_table(self, table_data) -> dict:
        """Process tables and make them searchable"""
        if isinstance(table_data, pd.DataFrame):
            df = table_data
        else:
            df = pd.read_csv(table_data) if isinstance(table_data, str) else pd.DataFrame(table_data)
        
        # Generate table summary
        summary = f"Table with {len(df)} rows and {len(df.columns)} columns. "
        summary += f"Columns: {', '.join(df.columns)}. "
        
        # Add statistical summary for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary += f"Numeric columns: {', '.join(numeric_cols)}. "
        
        # Convert to searchable text
        searchable_text = summary + " " + df.to_string()
        
        return {
            'type': 'table',
            'summary': summary,
            'data': df.to_dict(),
            'searchable_content': searchable_text,
            'metadata': {
                'rows': len(df),
                'columns': list(df.columns),
                'numeric_columns': list(numeric_cols)
            }
        }
    
    def _process_chart(self, chart_path: str) -> dict:
        """Extract information from charts and graphs"""
        image = cv2.imread(chart_path)
        
        # Use OCR to extract text from chart
        text = pytesseract.image_to_string(image)
        
        # Generate chart description using vision model
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        inputs = self.image_captioner(pil_image, return_tensors="pt")
        out = self.caption_model.generate(**inputs, max_length=100)
        description = self.image_captioner.decode(out[0], skip_special_tokens=True)
        
        return {
            'type': 'chart',
            'description': description,
            'extracted_text': text,
            'searchable_content': f"Chart: {description} {text}",
            'metadata': {
                'chart_type': self._detect_chart_type(description),
                'has_legend': 'legend' in text.lower(),
                'has_title': len(text.split('\n')[0]) > 0
            }
        }
    
    def _detect_chart_type(self, description: str) -> str:
        """Detect chart type from description"""
        description_lower = description.lower()
        if 'bar' in description_lower:
            return 'bar_chart'
        elif 'line' in description_lower:
            return 'line_chart'
        elif 'pie' in description_lower:
            return 'pie_chart'
        elif 'scatter' in description_lower:
            return 'scatter_plot'
        else:
            return 'unknown'

# Usage example
def enhance_rag_with_multimodal():
    """Example of how to integrate multi-modal RAG"""
    multimodal_rag = MultiModalRAG()
    
    # Process different content types
    image_content = multimodal_rag._process_image("research_diagram.png")
    table_content = multimodal_rag._process_table("data.csv")
    chart_content = multimodal_rag._process_chart("results_chart.png")
    
    return {
        'enhanced_content': [image_content, table_content, chart_content],
        'searchable_index': [
            content['searchable_content'] 
            for content in [image_content, table_content, chart_content]
        ]
    }