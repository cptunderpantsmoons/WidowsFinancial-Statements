import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Vision Model for template analysis (accurate OCR)
VISION_MODEL = "openai/gpt-4-vision-preview"

# Text Model for semantic mapping (reasoning capability)
TEXT_MODEL = "meta-llama/llama-2-70b-chat"

# File Configuration
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
MAX_PDF_PAGES = 15
ALLOWED_FILE_EXTENSIONS = {".pdf", ".xlsx", ".xls"}

# Processing Configuration
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "60"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CACHE_ENABLED = True

# UI Configuration
PROGRESS_UPDATE_INTERVAL = 0.5

# Error Messages
ERRORS = {
    "invalid_file_type": "Invalid file format. Please upload a PDF or Excel file.",
    "file_too_large": f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB.",
    "api_key_missing": "OpenRouter API key not configured. Please set OPENROUTER_API_KEY in .env",
    "api_failure": "API processing failed. Please try again.",
    "no_data_found": "Could not extract data from the uploaded file.",
}
