# Financial Statement Generator v1.0

A desktop application that automates the generation of financial statements by using AI to intelligently map data from Excel/PDF sources to a PDF template.

## Features

- **Automated Data Mapping**: AI-powered semantic matching between template labels and data accounts
- **PDF Template Support**: Use any multi-page financial statement as a formatting template
- **Multiple Data Sources**: Support for Excel (.xlsx) and PDF data files
- **Pixel-Perfect Output**: Preserves original formatting, fonts, colors, and logos
- **No Manual Mapping**: Intelligent LLM handles terminology variations automatically
- **User-Friendly UI**: Three-step workflow with progress tracking
- **Secure**: All processing in-memory, API key managed securely

## System Requirements

- Windows 10 or Windows 11
- Internet connection (for OpenRouter API)
- 2GB RAM minimum
- 500MB free disk space

## Installation

### Option 1: Use Standalone Executable (Recommended)

1. Download `FinancialStatementGenerator.exe` from the releases
2. Run the `.exe` - no installation needed
3. Application opens in your web browser automatically

### Option 2: Run from Source

1. Install Python 3.10 or higher
2. Clone/download this repository
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

### 1. Get an OpenRouter API Key

1. Visit [openrouter.ai](https://openrouter.ai)
2. Sign up for a free account
3. Navigate to API Keys section
4. Copy your API key

### 2. Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

3. (Optional) Adjust other settings:
   ```
   LOG_LEVEL=INFO
   MAX_FILE_SIZE_MB=100
   API_TIMEOUT_SECONDS=60
   ```

## Usage

### Running from Source

```bash
python -m streamlit run src/app.py
```

This opens the application in your default web browser at `http://localhost:8501`

### Using the Application

#### Step 1: Upload Template
1. Select your previous-year financial statement PDF
2. Application analyzes all text labels and their positions
3. Click "Proceed to Step 2"

#### Step 2: Upload Data
1. Choose data source format (Excel or PDF)
2. Upload your current financial data file
3. Review extracted data preview
4. Click "Proceed to Step 3"

#### Step 3: Generate
1. Click "🚀 Generate PDF"
2. Watch progress bar as application:
   - Analyzes template (extracts coordinates)
   - Extracts current data
   - Maps template labels to data accounts using AI
   - Generates final PDF with overlaid values
3. Download the generated PDF when complete

## Data File Format

### Excel Format (.xlsx)
- Column A: Account names (e.g., "Revenue", "Total Expenses")
- Column B: Numerical values
- First row can be headers or data

Example:
```
Account Name           | Value
Total Revenue         | 1000000
Operating Expenses    | 500000
Net Income           | 500000
```

### PDF Format
- Must contain readable text with account names and values
- Values should be numbers (with or without commas)
- Application attempts to extract tabular data

## Troubleshooting

### "API Key Not Configured"
- Ensure `.env` file exists in project root
- Verify `OPENROUTER_API_KEY` is set to valid key
- Restart application after changing `.env`

### "Invalid File Format"
- Use PDF files for templates (no images or scans)
- Use .xlsx files for Excel data (not .xls)
- Ensure files are not corrupted (try opening in reader first)

### "API Request Timed Out"
- Check internet connection
- Try again (temporary API issue)
- Increase `API_TIMEOUT_SECONDS` in `.env` if persistent

### "No Data Points Extracted"
- Verify data file has readable text (not images/scans)
- Check that account names are clearly visible
- Ensure numerical values are in expected columns

### PDF Appears Blank
- Template PDF may have unusual format
- Try analyzing a different financial statement
- Check that template PDF opens correctly in PDF reader

## Building Executable

To create a standalone `.exe` for Windows distribution:

```bash
python build.py
```

This creates `dist/FinancialStatementGenerator.exe` containing all dependencies.

**Build Requirements:**
- PyInstaller installed: `pip install PyInstaller`
- All dependencies in requirements.txt
- Windows 10/11 machine for testing

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed information about:
- Module descriptions
- Processing pipeline
- Data flow
- Security features
- Performance considerations

## API Usage & Costs

The application uses OpenRouter API for:
1. **Template Analysis** (Optional - can use local PDF extraction)
2. **Semantic Mapping** - LLM to match labels to accounts

### Cost Estimation
- Typical small statement: < $0.10
- Typical large statement: < $1.00
- Varies based on document complexity and model selection

See [OpenRouter Pricing](https://openrouter.ai/docs/pricing) for current rates.

## Privacy & Security

- **No data stored**: All processing in-memory
- **No disk persistence**: Files deleted after session
- **Secure API key**: Stored locally, never exposed
- **Privacy notice**: Users informed about API usage
- **Error logging**: Logs don't contain sensitive data

## Performance

| Task | Time |
|------|------|
| Application startup | < 10 seconds |
| Template analysis (12 pages) | ~10-20 seconds |
| Data extraction | ~2-5 seconds |
| Semantic mapping | ~15-30 seconds |
| PDF generation (12 pages) | ~5-10 seconds |
| **Total process** | **< 3 minutes** |

Times vary based on:
- Number of PDF pages
- Data file complexity
- API response times
- System specifications

## Development

### Project Structure
```
├── src/                    # Application source code
│   ├── app.py             # Streamlit UI
│   └── core/              # Core processing modules
├── config/                # Configuration management
├── utils/                 # Utilities (logging, validation)
├── build.py              # Build script
└── requirements.txt      # Dependencies
```

### Key Dependencies
- **Streamlit**: Web UI framework
- **PyMuPDF (fitz)**: PDF processing
- **pandas**: Data handling
- **openpyxl**: Excel parsing
- **requests**: API calls
- **python-dotenv**: Environment management

### Development Workflow
1. Make changes to source code
2. Test locally: `python -m streamlit run src/app.py`
3. Test on Windows for compatibility
4. Commit changes with descriptive messages
5. Build executable when ready to release

## Known Limitations

1. **Template Format**: Works best with text-based PDFs, not scanned images
2. **Data Extraction**: Requires clear, structured data format
3. **Terminology Handling**: AI mapping works for common variations only
4. **API Dependency**: Requires internet connection and active API key
5. **15-Page Limit**: Designed for 10-15 page statements (can be extended)

## Future Enhancements

- [x] Core PDF template analysis
- [x] Excel/PDF data extraction
- [x] Semantic mapping with LLM
- [x] PDF generation with overlay
- [x] Streamlit UI
- [ ] Template caching for faster re-use
- [ ] Advanced variance analysis
- [ ] Multi-currency support
- [ ] Direct accounting software integrations
- [ ] Batch processing

## Support & Contributing

For issues, questions, or contributions:
1. Check [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
2. Review error messages and logs for troubleshooting
3. Ensure all dependencies are installed correctly

## License

This project is provided as-is for use in automating financial statement generation.

## Disclaimer

This application processes financial data securely and sends it to the OpenRouter API for AI analysis. Users should review OpenRouter's privacy policy and ensure compliance with their organization's data handling policies before use.

---

**Version**: 1.0  
**Last Updated**: 2024
