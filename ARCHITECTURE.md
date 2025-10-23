# Financial Statement Generator - Architecture Documentation

## Project Overview

The Financial Statement Generator is a desktop application that automates the generation of current-year financial statements by using a previous-year PDF statement as a visual template and overlaying current financial data from an Excel or PDF file.

## Directory Structure

```
financial-statement-generator/
├── src/
│   ├── main.py                      # Entry point for the application
│   ├── app.py                       # Streamlit web UI application
│   └── core/
│       ├── __init__.py
│       ├── template_analyzer.py     # PDF template extraction and analysis
│       ├── data_handler.py          # Data extraction from Excel/PDF
│       ├── ai_processor.py          # OpenRouter API integration for semantic mapping
│       └── pdf_handler.py           # PDF generation with overlay
├── config/
│   ├── __init__.py
│   └── settings.py                  # Configuration and environment variables
├── utils/
│   ├── __init__.py
│   ├── logger.py                    # Logging utility
│   └── validators.py                # File validation
├── build.py                         # PyInstaller build script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore rules
└── ARCHITECTURE.md                  # This file
```

## Module Descriptions

### Core Processing Modules

#### 1. **template_analyzer.py** - `TemplateAnalyzer`
Extracts text labels and their precise coordinates from the template PDF.

**Key Methods:**
- `analyze_template(pdf_bytes, progress_callback)` - Main analysis method
- `_extract_page_data(page, page_num)` - Extracts text and coordinates from single page
- `get_coordinate_map()` - Returns the extracted coordinate mapping

**Output:** Dictionary mapping page numbers to lists of text elements with coordinates
```python
{
    0: [
        {"text": "Revenue", "x": 100, "y": 200, "font_size": 12, ...},
        ...
    ],
    ...
}
```

#### 2. **data_handler.py** - `DataHandler`
Extracts financial data from Excel or PDF files.

**Key Methods:**
- `extract_from_excel(file_bytes)` - Parse Excel files
- `extract_from_pdf(file_bytes)` - Parse PDF files
- `normalize_account_name(name)` - Normalize names for matching
- `format_number(value)` - Format with commas (e.g., 1,234,567)

**Output:** Dictionary of account names and their values
```python
{
    "Revenue": 1000000,
    "Operating Expenses": 500000,
    ...
}
```

#### 3. **ai_processor.py** - `AIProcessor`
Uses OpenRouter API to create semantic mapping between template labels and data accounts.

**Key Methods:**
- `create_semantic_mapping(template_labels, data_accounts)` - Main mapping method
- `_build_mapping_prompt(...)` - Constructs LLM prompt
- `_call_api(prompt)` - Calls OpenRouter API
- `_parse_mapping_response(response)` - Parses JSON response

**Process:**
1. Builds a prompt with template labels and data accounts
2. Sends to LLM (default: meta-llama/llama-2-70b-chat)
3. LLM matches labels to accounts handling terminology variations
4. Parses JSON response into mapping dictionary

**Output:** Dictionary mapping template labels to data account names
```python
{
    "Total Revenue": "Revenue",
    "Net Earnings": "Net Income",
    ...
}
```

#### 4. **pdf_handler.py** - `PDFHandler`
Generates the final PDF by overlaying financial data on the template.

**Key Methods:**
- `__init__(template_bytes)` - Initialize with template PDF
- `generate_output_pdf(...)` - Main PDF generation method
- `_overlay_text(page, x, y, text, font_size)` - Overlay text on page

**Process:**
1. Loads template PDF
2. For each page and element:
   - Checks if element text is in semantic mapping
   - Gets corresponding value from data accounts
   - Formats the number
   - Overlays text at exact coordinates
3. Returns final PDF as bytes

## Processing Flow

```
User Input (Streamlit)
    ↓
[Step 1] Upload Template PDF
    ↓
TemplateAnalyzer.analyze_template()
    → Extract all text labels and coordinates from each page
    ↓
[Step 2] Upload Data File (Excel/PDF)
    ↓
DataHandler.extract_from_excel() OR DataHandler.extract_from_pdf()
    → Extract account names and values
    ↓
[Step 3] Generate
    ↓
AIProcessor.create_semantic_mapping()
    → Use LLM to match template labels to data accounts
    ↓
PDFHandler.generate_output_pdf()
    → Overlay values on template at correct coordinates
    ↓
Download Generated PDF
```

## UI/UX - Three-Step Workflow

### Step 1: Upload Template
- User uploads a PDF of their previous financial statement
- File is validated (type, size, format)
- Metadata displayed (filename, size)
- Proceed button to Step 2

### Step 2: Upload Data
- Toggle between Excel and PDF data sources
- Upload corresponding file
- Preview first 10 data points
- Back/Proceed buttons

### Step 3: Generate
- "Generate PDF" button triggers processing
- Progress bar shows current step
- Status text: "Analyzing Template: Page 5 of 12..."
- Upon success: Download button for final PDF
- Error messages displayed if any step fails

## Security Features

### API Key Management
- OpenRouter API key stored in `.env` file
- Never hardcoded in source code
- Validated at application startup
- Secure error messages (no key exposure)

### Data Privacy
- All file processing done in-memory
- No files written to disk (except logs)
- Session data cleared after completion
- Privacy notice displayed to users about API usage

### File Validation
- Type checking (PDF, XLSX only)
- Size validation (max 100MB configurable)
- Format validation (PDF header check, ZIP signature for Excel)
- Corrupted file detection

## Configuration

All settings stored in `config/settings.py`:
- API endpoints and models
- File size limits
- Processing timeouts
- Log levels
- Error messages

Environment variables loaded from `.env`:
```
OPENROUTER_API_KEY=<your_key>
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=100
API_TIMEOUT_SECONDS=60
```

## Error Handling

### Graceful Degradation
- Invalid file format → User-friendly error message
- API timeout → Retry with timeout notification
- Missing data field → Mapping shows null, user can adjust
- Corrupted files → Validation catches before processing

### Logging
- All operations logged to console and file
- No sensitive data in logs
- Log files in `logs/` directory with timestamp
- Configurable log levels

## Performance Considerations

### Optimizations
1. **Caching**: Template analysis results cached for re-use
2. **Batch Processing**: API calls grouped where possible
3. **Memory Efficiency**: Byte streams used for PDFs (not full loads)
4. **Progressive UI**: Status updates every 0.5 seconds

### Performance Targets
- UI startup: < 10 seconds
- Template analysis: Proportional to page count
- Semantic mapping: < 30 seconds (API dependent)
- PDF generation: < 1 minute for 15 pages
- Total process: < 3 minutes

## Testing Strategy

Before releasing, test:
1. **Unit Tests**: Individual module functionality
2. **Integration Tests**: Full processing pipeline
3. **UI Tests**: User workflow and error handling
4. **Compatibility Tests**: Windows 10/11 VMs
5. **Performance Tests**: Large PDFs and data sets

## Future Enhancements

1. **Caching Framework**: Cache template analysis for multiple runs
2. **Advanced AI**: Variance analysis and commentary generation
3. **Template Library**: Save and manage multiple templates
4. **Multi-Currency**: Handle different currency formats
5. **Direct Integrations**: Connect to QuickBooks, Xero, etc.

## Building for Distribution

```bash
python build.py
```

This creates a single `.exe` file in `dist/` with all dependencies bundled:
- All Python packages included
- Streamlit assets embedded
- No separate Python installation required
- Icon and metadata included
