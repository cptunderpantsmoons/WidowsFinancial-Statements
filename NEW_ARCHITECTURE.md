# Financial Statement Generator v2.0 - Complete Overhaul

## Current Problems

1. **Output is garbage** - Getting back 2024 template instead of proper 2025 statements
2. **No preview/editing** - Can't review or fix issues before PDF generation
3. **No chat interface** - Can't request specific corrections
4. **Mathematical accuracy questionable** - No proper validation
5. **Format preservation doesn't work** - Overlay approach is fundamentally flawed
6. **Using expensive models** - Need to switch to free models

## New Architecture

### Phase 1: Data Extraction & Understanding
**Goal**: Extract ALL data from both 2024 template and 2025 data file

```
Input: 2024 PDF Template + 2025 Excel Data
  ↓
Extract 2024 Financial Data (tables, notes, structure)
Extract 2025 Financial Data (all sheets, all accounts)
  ↓
Output: Structured JSON with both years' data
```

**Tools Needed**:
- Enhanced PDF table extraction (tabula-py or camelot)
- Multi-sheet Excel parser
- Notes extraction from both sources
- Account code mapping

### Phase 2: AI Agent Analysis
**Goal**: Use AI agent with tools to understand and map the data

```
Agent Workflow:
1. Analyze 2024 structure → identify all line items
2. Map 2024 accounts to 2025 accounts
3. Identify missing data
4. Extract notes and create note references
5. Calculate derived values (totals, subtotals)
6. Validate mathematical relationships
```

**AI Model**: gpt-oss-20b (FREE)
**Framework**: LangChain or custom agent with tool calling

**Tools for Agent**:
- `get_account_mapping()` - Map 2024 to 2025 accounts
- `calculate_total()` - Calculate line item totals
- `validate_formula()` - Check mathematical accuracy
- `extract_notes()` - Get relevant notes
- `find_missing_data()` - Identify gaps

### Phase 3: Interactive Preview & Editing
**Goal**: Show user editable preview before PDF generation

```
Streamlit UI with:
├── Income Statement (editable table)
├── Balance Sheet (editable table)
├── Cash Flow Statement (editable table)
├── Notes Section (editable text)
└── Validation Results (errors/warnings)
```

**Features**:
- ✅ Inline editing of all values
- ✅ Real-time formula validation
- ✅ Highlighting of calculated vs input values
- ✅ Color coding (green=good, red=error, yellow=warning)
- ✅ Export to Excel for external editing
- ✅ Import edited Excel back

### Phase 4: Chat Interface for Corrections
**Goal**: Allow natural language requests to fix issues

```
User: "The total assets don't match, please recalculate"
Agent: 
  1. Identifies issue
  2. Recalculates using tools
  3. Updates preview
  4. Shows what changed

User: "Add a note about the depreciation method"
Agent:
  1. Creates new note
  2. Adds reference to relevant line
  3. Updates preview
```

**Chat Features**:
- Natural language understanding
- Multi-turn conversation
- Undo/redo functionality
- Show reasoning for changes
- Request clarification when ambiguous

### Phase 5: Mathematical Validation
**Goal**: 100% accuracy on all calculations

```
Validation Rules:
1. Assets = Liabilities + Equity
2. Revenue - Expenses = Net Income
3. All subtotals match sum of line items
4. Cash flow reconciles
5. Retained earnings rollforward correct
6. All cross-references valid
```

**Approach**:
- Parse formulas from 2024 template
- Apply to 2025 data
- Flag any discrepancies
- Auto-fix when possible
- Request user input when ambiguous

### Phase 6: PDF Generation (From Scratch)
**Goal**: Generate professional PDF, NOT overlay on template

```
Use ReportLab to create:
├── Cover page
├── Income Statement (formatted table)
├── Balance Sheet (formatted table)
├── Cash Flow Statement (formatted table)
├── Statement of Changes in Equity
└── Notes to Financial Statements
```

**Styling**:
- Professional formatting (not copying template)
- Clean tables with proper alignment
- Page numbers and headers
- Company logo/branding
- Consistent fonts and spacing

## Technology Stack

### Core Dependencies
```python
# AI & Agents
langchain==0.1.0
openai==1.0.0  # For OpenRouter API

# Data Processing
pandas==2.1.3
openpyxl==3.1.5
tabula-py==2.9.0  # PDF table extraction
camelot-py[cv]==0.11.0  # Advanced PDF extraction
pdfplumber==0.10.3  # Text extraction

# PDF Generation (NEW)
reportlab==4.0.7  # Professional PDF creation
pypdf==3.17.0  # PDF manipulation

# UI
streamlit==1.28.1
streamlit-aggrid==0.3.4  # Editable tables
streamlit-chat==0.1.1  # Chat interface

# Validation
sympy==1.12  # Symbolic math for formula validation
numexpr==2.8.7  # Safe expression evaluation
```

### File Structure (NEW)
```
src/
├── agents/
│   ├── __init__.py
│   ├── financial_agent.py      # Main orchestration agent
│   ├── extraction_agent.py     # Data extraction specialist
│   ├── mapping_agent.py        # Account mapping specialist
│   ├── calculation_agent.py    # Mathematical calculations
│   └── notes_agent.py          # Notes extraction/generation
├── tools/
│   ├── __init__.py
│   ├── extraction_tools.py     # PDF/Excel extraction
│   ├── calculation_tools.py    # Formula calculations
│   ├── validation_tools.py     # Accuracy checking
│   └── mapping_tools.py        # Account mapping
├── ui/
│   ├── __init__.py
│   ├── preview_editor.py       # Interactive preview
│   ├── chat_interface.py       # Chat UI
│   └── validation_display.py   # Show validation results
├── generators/
│   ├── __init__.py
│   ├── pdf_generator.py        # ReportLab PDF creation
│   ├── income_statement.py     # Income statement generator
│   ├── balance_sheet.py        # Balance sheet generator
│   ├── cash_flow.py            # Cash flow generator
│   └── notes.py                # Notes generator
├── validators/
│   ├── __init__.py
│   ├── mathematical.py         # Formula validation
│   ├── structural.py           # Statement structure
│   └── gaap_compliance.py      # GAAP rules
└── main_app.py                 # New Streamlit app
```

## Implementation Plan

### Step 1: Set up new dependencies
```bash
pip install langchain openai tabula-py camelot-py[cv] pdfplumber reportlab
pip install streamlit-aggrid streamlit-chat sympy numexpr
```

### Step 2: Build extraction agents
- Extract tables from 2024 PDF using camelot/tabula
- Parse all sheets from 2025 Excel
- Create structured JSON for both years

### Step 3: Build mapping agent
- Use gpt-oss-20b with tool calling
- Map 2024 accounts to 2025 accounts
- Handle missing data gracefully

### Step 4: Build calculation agent
- Parse formulas from 2024 statements
- Apply to 2025 data
- Validate all calculations
- Flag errors for review

### Step 5: Build preview UI
- Streamlit-aggrid for editable tables
- Show all three main statements
- Real-time validation
- Export/import capability

### Step 6: Build chat interface
- Streamlit-chat for UI
- Connect to agent workflow
- Allow natural language corrections
- Show reasoning and changes

### Step 7: Build PDF generator
- ReportLab templates for each statement
- Professional formatting
- Company branding
- Generate from structured data (not overlay)

### Step 8: End-to-end testing
- Test with real Paniri data
- Verify mathematical accuracy
- Test chat corrections
- Validate PDF output

## Key Differences from Current Version

| Aspect | Old Approach | New Approach |
|--------|-------------|--------------|
| **Output Method** | Overlay on template | Generate from scratch |
| **Preview** | None | Editable tables |
| **Corrections** | None | Chat interface |
| **Extraction** | Basic pandas | Advanced (camelot/tabula) |
| **AI Model** | Expensive models | Free gpt-oss-20b |
| **Validation** | Limited | 100% mathematical |
| **Architecture** | Monolithic | Agent-based workflow |
| **User Control** | None | Full editing capability |

## Expected Results

### Before (Current State)
- ❌ Gets back 2024 template (garbage)
- ❌ No way to fix issues
- ❌ Can't see what's happening
- ❌ Mathematical errors
- ❌ No notes handling

### After (New System)
- ✅ Proper 2025 financial statements
- ✅ Interactive preview with editing
- ✅ Chat to request changes
- ✅ 100% mathematical accuracy
- ✅ Proper notes extraction/generation
- ✅ Professional PDF output
- ✅ Full transparency in process

## Implementation Timeline

1. **Day 1**: Set up new structure, install dependencies
2. **Day 2**: Build extraction agents (camelot/tabula integration)
3. **Day 3**: Build mapping & calculation agents
4. **Day 4**: Build preview UI with editable tables
5. **Day 5**: Build chat interface
6. **Day 6**: Build PDF generator (ReportLab)
7. **Day 7**: Testing & refinement

## Next Steps

1. Get approval for complete overhaul
2. Install new dependencies
3. Start with extraction agents (most critical)
4. Build incrementally, testing each phase
5. Keep user in the loop with progress

---

**This is a complete rewrite, not a patch. The current system is fundamentally flawed and needs to be rebuilt from the ground up.**