# IMMEDIATE ACTION PLAN - Working System NOW

## Reality Check

The current system is fundamentally broken. Instead of trying to build a massive agent-based system, let's build a **simple working system TODAY** that actually produces 2025 financial statements.

## Simplified Approach (Working in 2-3 hours)

### Step 1: Better Data Extraction (30 minutes)
**Goal**: Extract ALL data from your Excel file properly

**Simple Solution**:
```python
# Read Income Statement sheet with proper headers
df_income = pd.read_excel(file, sheet_name='Income Statement', header=1)
# Get 2025 column
accounts_2025 = dict(zip(df_income['Particulars'], df_income[2025.0]))

# Read Balance Sheet
df_balance = pd.read_excel(file, sheet_name='Balance Sheet', header=3)
# Merge all accounts
all_accounts = {**accounts_2025, **dict(zip(df_balance['Particulars'], df_balance[2025.0]))}
```

**Result**: Get 500+ accounts with values instead of 4

---

### Step 2: Simple Mapping (30 minutes)
**Goal**: Match 2024 labels to 2025 accounts

**Simple Solution**:
- Don't use AI for matching (it's failing)
- Use fuzzy string matching (fuzzywuzzy library)
- Let USER edit mappings in a table before generation

```python
from fuzzywuzzy import fuzz

def smart_match(template_label, accounts_dict):
    best_match = None
    best_score = 0
    
    for account_name in accounts_dict.keys():
        score = fuzz.token_set_ratio(template_label.lower(), account_name.lower())
        if score > best_score:
            best_score = score
            best_match = account_name
    
    return best_match if best_score > 70 else None
```

---

### Step 3: Interactive Preview (45 minutes)
**Goal**: Show user what will be generated, let them fix it

**Simple Solution using Streamlit AgGrid**:

```python
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# Create editable table
mapping_df = pd.DataFrame({
    '2024 Label': template_labels,
    '2025 Account': matched_accounts,
    '2025 Value': values,
    'Confidence': confidence_scores
})

# Make it editable
gb = GridOptionsBuilder.from_dataframe(mapping_df)
gb.configure_column("2025 Account", editable=True)
gb.configure_column("2025 Value", editable=True)

grid_response = AgGrid(
    mapping_df,
    gridOptions=gb.build(),
    editable=True,
    height=600
)

# Get edited data
edited_df = grid_response['data']
```

---

### Step 4: Generate NEW PDF (45 minutes)
**Goal**: Create proper 2025 statements, not overlay on template

**Simple Solution using ReportLab**:

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_income_statement(data, output_file):
    doc = SimpleDocTemplate(output_file, pagesize=A4)
    story = []
    
    # Title
    styles = getSampleStyleSheet()
    title = Paragraph("Income Statement - Year Ended 2025", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Create table
    table_data = [['Account', '2025', '2024']]
    for account, value in data.items():
        table_data.append([account, f"${value:,.2f}", ""])
    
    t = Table(table_data)
    t.setStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    
    story.append(t)
    doc.build(story)
```

---

## New Streamlit App Structure

```python
import streamlit as st

st.title("Financial Statement Generator v2")

# Step 1: Upload files
st.header("Step 1: Upload Files")
template_pdf = st.file_uploader("Upload 2024 Template (PDF)", type=['pdf'])
data_excel = st.file_uploader("Upload 2025 Data (Excel)", type=['xlsx'])

if template_pdf and data_excel:
    
    # Step 2: Extract & Show Data
    st.header("Step 2: Data Extraction")
    
    with st.spinner("Extracting data..."):
        # Extract from Excel (properly this time)
        accounts_2025 = extract_all_sheets_properly(data_excel)
        st.success(f"✅ Extracted {len(accounts_2025)} accounts from Excel")
        
        # Extract from PDF
        template_labels = extract_pdf_labels(template_pdf)
        st.success(f"✅ Found {len(template_labels)} labels in template")
    
    # Step 3: Smart Mapping
    st.header("Step 3: Review & Edit Mappings")
    
    # Create initial mappings
    mappings = {}
    for label in template_labels:
        matched = fuzzy_match(label, accounts_2025)
        mappings[label] = {
            'account': matched,
            'value': accounts_2025.get(matched, 0),
            'confidence': calculate_confidence(label, matched)
        }
    
    # Show editable table
    mapping_df = create_mapping_dataframe(mappings)
    edited_mappings = show_editable_grid(mapping_df)
    
    # Show statistics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Mappings", len(edited_mappings))
    col2.metric("High Confidence", sum(1 for m in mappings.values() if m['confidence'] > 0.8))
    col3.metric("Needs Review", sum(1 for m in mappings.values() if m['confidence'] < 0.7))
    
    # Step 4: Generate
    st.header("Step 4: Generate Financial Statements")
    
    if st.button("🚀 Generate PDF", type="primary"):
        with st.spinner("Generating professional PDF..."):
            
            # Generate each statement
            pdf_bytes = generate_financial_statements(
                income_statement=filter_income_items(edited_mappings),
                balance_sheet=filter_balance_items(edited_mappings),
                notes=extract_notes(template_pdf)
            )
            
            st.success("✅ PDF Generated!")
            st.download_button(
                "📥 Download 2025 Financial Statements",
                pdf_bytes,
                "Financial_Statements_2025.pdf",
                "application/pdf"
            )
```

---

## What This Gives You (TODAY)

1. ✅ **Proper Data Extraction**: All 500+ accounts from Excel
2. ✅ **Visual Mapping Review**: See what matched, edit what didn't
3. ✅ **Editable Preview**: Fix any issues before generation
4. ✅ **Professional PDF**: Clean, new statements (not overlay garbage)
5. ✅ **Fast & Simple**: No complex AI agents, just working code

---

## Installation (5 minutes)

```bash
pip install streamlit pandas openpyxl pdfplumber reportlab fuzzywuzzy python-levenshtein streamlit-aggrid
```

---

## Next Steps

1. **Install dependencies** (above)
2. **Create `app_v2.py`** with the simplified structure
3. **Test with your Paniri files**
4. **Get it working first**
5. **Then add fancy features** (chat, AI agents, etc.)

---

## Why This Will Work

- ✅ No complex AI that fails
- ✅ User can see and fix everything
- ✅ Simple fuzzy matching (proven to work)
- ✅ Generates NEW PDF (not broken overlay)
- ✅ Can be built in 2-3 hours
- ✅ Actually produces 2025 statements

---

## After This Works

Once we have a working base system, we can add:
- Chat interface for corrections
- AI agent for better matching
- Mathematical validation
- Multi-year comparison
- Notes generation
- Formulas and calculations

**But first, let's get something that WORKS.**

---

## Decision Point

Do you want me to:

**Option A**: Build this simplified working version NOW (2-3 hours)
**Option B**: Continue with complex agent-based system (2-3 days)

I strongly recommend **Option A** - get something working, then iterate.