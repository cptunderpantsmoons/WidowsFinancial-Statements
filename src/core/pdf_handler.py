import io
import fitz
from typing import Dict, List, Tuple
from utils.logger import Logger
from .data_handler import DataHandler

logger = Logger(__name__)


class PDFHandler:
    def __init__(self, template_bytes: bytes):
        """Initialize with template PDF."""
        self.template_pdf = fitz.open(stream=template_bytes, filetype="pdf")
        self.total_pages = len(self.template_pdf)
        logger.info(f"PDF Handler initialized with {self.total_pages} pages")

    def generate_output_pdf(
        self,
        coordinate_map: Dict,
        semantic_mapping: Dict[str, str],
        data_accounts: Dict[str, float],
        progress_callback=None,
    ) -> bytes:
        """Generate final PDF with overlaid financial data."""
        try:
            # Create a copy of the template for modification
            output_document = fitz.open(
                stream=self.template_pdf.tobytes(), filetype="pdf"
            )

            for page_num in range(self.total_pages):
                if progress_callback:
                    progress_callback(page_num + 1, self.total_pages)

                page = output_document[page_num]
                page_elements = coordinate_map.get(page_num, [])

                for element in page_elements:
                    text = element.get("text", "").strip()

                    if text in semantic_mapping:
                        account_name = semantic_mapping[text]

                        if account_name in data_accounts:
                            value = data_accounts[account_name]
                            formatted_value = DataHandler.format_number(value)

                            self._overlay_text(
                                page,
                                element["x"],
                                element["y"],
                                formatted_value,
                                element.get("font_size", 12),
                            )

            # Convert document to bytes
            output_bytes = output_document.tobytes()
            output_document.close()

            logger.info("PDF generation completed")
            return output_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise

    def _overlay_text(self, page, x: float, y: float, text: str, font_size: float):
        """Overlay text on PDF page at specified coordinates."""
        try:
            point = fitz.Point(x, y)
            page.insert_text(
                point, text, fontsize=font_size, color=(0, 0, 0), overlay=True
            )
        except Exception as e:
            logger.error(f"Failed to overlay text at ({x}, {y}): {str(e)}")

    def close(self):
        """Close PDF document."""
        if self.template_pdf:
            self.template_pdf.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
