import os
from config.settings import MAX_FILE_SIZE_MB, ALLOWED_FILE_EXTENSIONS, ERRORS

class FileValidator:
    @staticmethod
    def validate_file(file_bytes: bytes, filename: str) -> tuple[bool, str]:
        """Validate uploaded file type, extension, and size."""
        
        if not filename:
            return False, ERRORS["invalid_file_type"]
        
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_FILE_EXTENSIONS:
            return False, ERRORS["invalid_file_type"]
        
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return False, ERRORS["file_too_large"]
        
        if file_ext == ".pdf":
            if not FileValidator._validate_pdf(file_bytes):
                return False, "Invalid or corrupted PDF file."
        
        if file_ext in {".xlsx", ".xls"}:
            if not FileValidator._validate_excel(file_bytes):
                return False, "Invalid or corrupted Excel file."
        
        return True, ""
    
    @staticmethod
    def _validate_pdf(file_bytes: bytes) -> bool:
        """Check if file has valid PDF header."""
        return file_bytes.startswith(b"%PDF")
    
    @staticmethod
    def _validate_excel(file_bytes: bytes) -> bool:
        """Check if file has valid Excel signature."""
        return file_bytes.startswith(b"PK")
