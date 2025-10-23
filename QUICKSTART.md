# Quick Start Guide - Financial Statement Generator

Get up and running in 5 minutes!

## Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Run the Application

```bash
python -m streamlit run src/app.py
```

The application opens automatically in your browser at `http://localhost:8501`

## Step 3: Configure OpenRouter API Key

On first run, you'll see a setup screen asking for your API key:

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up for a free account
3. Navigate to API Keys section
4. Copy your API key
5. Paste it into the application's setup screen
6. Click "Save API Key"

Done! The application saves your key and starts automatically.

## Step 4: Generate Your First Statement

### Upload Template (Step 1)
- Click "Choose a PDF file"
- Select a financial statement from a previous period
- Click "Proceed to Step 2"

### Upload Data (Step 2)
- Choose Excel (.xlsx) or PDF format
- Click "Choose a file"
- Select your current financial data
- Click "Proceed to Step 3"

### Generate (Step 3)
- Click "🚀 Generate PDF"
- Watch the progress bar
- Download the generated PDF when complete

## Troubleshooting

**Can't run the application?**
- Ensure Python 3.10+ is installed: `python --version`
- Reinstall dependencies: `pip install -r requirements.txt --upgrade`
- Check that you're in the project directory

**Setup screen appears every time?**
- Check that `.env` file exists in the project root
- Verify `OPENROUTER_API_KEY=` line has a value (not empty)

**PDF generation fails?**
- Ensure template PDF opens correctly in a PDF reader
- Check data file format matches expected structure
- Verify internet connection (API calls require it)

**Need to change API key later?**
- Click the **⚙️ Settings** button in the top-right corner
- Enter new API key and save

## Next Steps

- See [README.md](README.md) for comprehensive documentation
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for development info

## API Key Security

Your OpenRouter API key is:
- Stored locally in the `.env` file
- Never transmitted except to OpenRouter for processing
- Never logged or exposed in error messages
- Encrypted per OpenRouter's security standards

## Support

For issues or questions, refer to the full [README.md](README.md) troubleshooting section.

---

**Happy automating!** 🚀
