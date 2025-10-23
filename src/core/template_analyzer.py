import io
import base64
import json
from typing import Dict, List, Tuple
import fitz
from utils.logger import Logger
from config.settings import VISION_MODEL, OPENROUTER_BASE_URL, OPENROUTER_API_KEY, API_TIMEOUT_SECONDS
import requests

logger = Logger(__name__)

class TemplateAnalyzer:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.vision_model = VISION_MODEL
        self.coordinate_map = {}
    
    def analyze_template(self, pdf_bytes: bytes, progress_callback=None) -> Dict:
        """Extract labels and coordinates from template PDF."""
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(pdf_document)
            
            logger.info(f"Analyzing template: {total_pages} pages")
            
            for page_num in range(total_pages):
                if progress_callback:
                    progress_callback(page_num + 1, total_pages)
                
                page = pdf_document[page_num]
                page_data = self._extract_page_data(page, page_num)
                self.coordinate_map[page_num] = page_data
            
            pdf_document.close()
            logger.info("Template analysis completed")
            return self.coordinate_map
        
        except Exception as e:
            logger.error(f"Template analysis failed: {str(e)}")
            raise
    
    def _extract_page_data(self, page, page_num: int) -> List[Dict]:
        """Extract text and coordinates from a single page."""
        try:
            page_data = []
            
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                rect = span["bbox"]
                                x, y = rect[0], rect[1]
                                
                                page_data.append({
                                    "text": text,
                                    "x": x,
                                    "y": y,
                                    "font_size": span.get("size", 12),
                                    "font_name": span.get("font", "unknown"),
                                    "flags": span.get("flags", 0)
                                })
            
            logger.debug(f"Page {page_num}: extracted {len(page_data)} text elements")
            return page_data
        
        except Exception as e:
            logger.error(f"Failed to extract page {page_num} data: {str(e)}")
            return []
    
    def _get_page_image(self, page) -> str:
        """Convert PDF page to base64 image for Vision API."""
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes(output="png")
            return base64.b64encode(img_data).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to convert page to image: {str(e)}")
            raise
    
    def get_coordinate_map(self) -> Dict:
        """Return the extracted coordinate map."""
        return self.coordinate_map
