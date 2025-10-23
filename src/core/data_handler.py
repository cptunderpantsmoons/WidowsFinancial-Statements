import io
import fitz
import pandas as pd
from typing import Dict, List, Tuple
from openpyxl import load_workbook
from utils.logger import Logger

logger = Logger(__name__)

class DataHandler:
    
    @staticmethod
    def extract_from_excel(file_bytes: bytes) -> Dict[str, float]:
        """Extract account names and values from Excel file."""
        try:
            excel_file = io.BytesIO(file_bytes)
            
            workbook = load_workbook(excel_file)
            sheet = workbook.active
            
            data_map = {}
            for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row):
                if len(row) >= 2:
                    account_name = row[0].value
                    value = row[1].value
                    
                    if account_name and isinstance(value, (int, float)):
                        account_name_str = str(account_name).strip()
                        data_map[account_name_str] = float(value)
            
            logger.info(f"Extracted {len(data_map)} data points from Excel")
            return data_map
        
        except Exception as e:
            logger.error(f"Failed to extract Excel data: {str(e)}")
            raise
    
    @staticmethod
    def extract_from_pdf(file_bytes: bytes) -> Dict[str, float]:
        """Extract account names and values from PDF table/text."""
        try:
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            data_map = {}
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text()
                
                lines = text.split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            value = float(parts[-1].replace(',', ''))
                            account_name = ' '.join(parts[:-1]).strip()
                            if account_name:
                                data_map[account_name] = value
                        except ValueError:
                            continue
            
            pdf_document.close()
            logger.info(f"Extracted {len(data_map)} data points from PDF")
            return data_map
        
        except Exception as e:
            logger.error(f"Failed to extract PDF data: {str(e)}")
            raise
    
    @staticmethod
    def normalize_account_name(name: str) -> str:
        """Normalize account name for matching."""
        return name.lower().strip()
    
    @staticmethod
    def format_number(value: float) -> str:
        """Format number with commas and appropriate decimals."""
        if isinstance(value, float) and value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}".rstrip('0').rstrip('.')
