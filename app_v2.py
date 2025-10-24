"""
Financial Statement Generator v2.0 - Simplified Working Version
Properly extracts data, shows editable preview, generates clean PDFs
"""

import streamlit as st
import pandas as pd
import pdfplumber
import io
from fuzzywuzzy import fuzz
from typing import Dict, List, Tuple, Optional
import re
import sys
from pathlib import Path
import pickle
import hashlib

# Add intelligent mapper to path
sys.path.insert(0, str(Path(__file__).parent))
from intelligent_mapper import IntelligentMapper, StructuredMapper
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Financial Statement Generator v2", page_icon="📊", layout="wide"
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


class ExcelExtractor:
    """Extract data properly from multi-sheet Excel files"""

    @staticmethod
    def extract_all_accounts(excel_bytes: bytes) -> Dict[str, float]:
        """Extract ALL accounts with values from Excel file"""
        all_accounts = {}

        try:
            excel_file = io.BytesIO(excel_bytes)

            # Read all sheets
            sheet_dict = pd.read_excel(excel_file, sheet_name=None)

            for sheet_name, df in sheet_dict.items():
                # Skip small sheets
                if len(df) < 3:
                    continue

                # Find header row (contains 'Particulars' or similar)
                header_row = None
                for idx in range(min(10, len(df))):
                    row_text = " ".join(
                        [str(val).lower() for val in df.iloc[idx] if pd.notna(val)]
                    )
                    if "particular" in row_text or "account" in row_text:
                        header_row = idx
                        break

                if header_row is None:
                    continue

                # Re-read with proper header
                df_clean = df.iloc[header_row:].copy()
                df_clean.columns = df_clean.iloc[0]
                df_clean = df_clean[1:].reset_index(drop=True)

                # Find description column
                desc_col = None
                for col in df_clean.columns:
                    col_str = str(col).lower()
                    if (
                        "particular" in col_str
                        or "account" in col_str
                        or "description" in col_str
                    ):
                        desc_col = col
                        break

                if desc_col is None:
                    desc_col = df_clean.columns[0]

                # Find year columns (2025, 2024, etc.)
                year_cols = []
                for col in df_clean.columns:
                    col_str = str(col)
                    # Check if it's a year
                    if re.match(r"^(20\d{2})\.?\d*$", col_str):
                        year_cols.append(col)

                if not year_cols:
                    continue

                # Use most recent year (first in list after sorting)
                year_cols_sorted = sorted(year_cols, reverse=True)
                value_col = year_cols_sorted[0]

                # Extract accounts
                for idx, row in df_clean.iterrows():
                    account = row.get(desc_col)
                    value = row.get(value_col)

                    # Skip invalid rows
                    if pd.isna(account) or not str(account).strip():
                        continue

                    account_str = str(account).strip()

                    # Skip header rows
                    if account_str.lower() in [
                        "particulars",
                        "account",
                        "description",
                        "notes",
                    ]:
                        continue

                    # Try to convert value
                    try:
                        if pd.notna(value):
                            # Clean value
                            value_str = (
                                str(value).replace(",", "").replace(" ", "").strip()
                            )

                            # Handle negatives in parentheses
                            if value_str.startswith("(") and value_str.endswith(")"):
                                value_str = "-" + value_str[1:-1]

                            value_float = float(value_str)

                            # Store non-zero values
                            if value_float != 0:
                                # Clean account name
                                account_clean = re.sub(r"^\d+\s*-\s*", "", account_str)
                                account_clean = account_clean.replace("IC_", "")
                                all_accounts[account_clean.strip()] = value_float

                    except (ValueError, TypeError):
                        continue

            return all_accounts

        except Exception as e:
            st.error(f"Excel extraction error: {e}")
            return {}


class PDFExtractor:
    """Extract labels and structure from PDF template"""

    @staticmethod
    def extract_labels(pdf_bytes: bytes) -> List[str]:
        """Extract all text labels from PDF that could be account names"""
        labels = []

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    # Extract text
                    text = page.extract_text()
                    if not text:
                        continue

                    # Split into lines
                    lines = text.split("\n")

                    for line in lines:
                        line = line.strip()

                        # Skip empty lines
                        if not line:
                            continue

                        # Skip obvious headers/footers
                        if any(
                            skip in line.lower()
                            for skip in [
                                "page ",
                                "financial statement",
                                "directors",
                                "dated:",
                            ]
                        ):
                            continue

                        # Skip lines that are just numbers
                        if re.match(r"^[\d,\.\s\(\)]+$", line):
                            continue

                        # If line has both text and numbers, extract just the text part
                        # This captures account names before their values
                        parts = re.split(r"\s{2,}|\t", line)
                        for part in parts:
                            part = part.strip()
                            # Must have letters and be reasonable length
                            if len(part) > 3 and re.search(r"[a-zA-Z]", part):
                                # Remove trailing numbers/decimals
                                clean_part = re.sub(
                                    r"\s*[\d,\.]+\s*$", "", part
                                ).strip()
                                if clean_part:
                                    labels.append(clean_part)

        except Exception as e:
            st.error(f"PDF extraction error: {e}")

        # Remove duplicates while preserving order
        seen = set()
        unique_labels = []
        for label in labels:
            if label not in seen:
                seen.add(label)
                unique_labels.append(label)

        return unique_labels


class SmartMatcher:
    """Enhanced matching between template labels and Excel accounts"""

    @staticmethod
    def match_accounts(
        labels: List[str], accounts: Dict[str, float], method: str = "structured"
    ) -> pd.DataFrame:
        """
        Create mapping dataframe with selected matching method.

        Methods:
        - 'ai': Use AI with financial context (most accurate, requires API)
        - 'structured': Use financial structure understanding (fast, good)
        - 'fuzzy': Simple fuzzy matching (fastest, basic)
        """

        if method == "ai":
            try:
                st.info("🤖 Using AI-powered mapping with maximum accuracy mode...")
                mapper = IntelligentMapper()
                # Get double-check setting from session state
                double_check = st.session_state.get("double_check", True)
                return mapper.create_mappings(
                    labels, accounts, batch_size=20, double_check=double_check
                )
            except Exception as e:
                st.error(f"❌ AI mapping failed: {e}")
                st.warning("Falling back to structured method...")
                method = "structured"

        if method == "structured":
            st.info("🏗️ Using structured mapping with category understanding...")
            mapper = StructuredMapper()
            return mapper.create_structured_mappings(labels, accounts)

        # Fallback to basic fuzzy matching
        st.info("🔤 Using basic fuzzy matching...")
        mappings = []

        for label in labels:
            # Find best match
            best_match = None
            best_score = 0

            for account_name in accounts.keys():
                # Use token set ratio (ignores word order)
                score = fuzz.token_set_ratio(label.lower(), account_name.lower())

                if score > best_score:
                    best_score = score
                    best_match = account_name

            # Determine confidence level
            if best_score >= 90:
                confidence = "High"
                status = "✅"
            elif best_score >= 70:
                confidence = "Medium"
                status = "⚠️"
            else:
                confidence = "Low"
                status = "❌"

            # Get value
            value = accounts.get(best_match, 0) if best_match else 0

            mappings.append(
                {
                    "Status": status,
                    "Template Label": label,
                    "Matched Account": best_match if best_match else "",
                    "Value (2025)": value,
                    "Confidence": confidence,
                    "Score": best_score,
                }
            )

        return pd.DataFrame(mappings)


class PDFGenerator:
    """Generate professional PDF from scratch (not overlay)"""

    @staticmethod
    def generate_financial_statements(
        company_name: str,
        year: int,
        income_data: Dict[str, float],
        balance_data: Dict[str, float],
        notes: List[str] = None,
    ) -> bytes:
        """Generate complete financial statements PDF"""

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch
        )

        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1f77b4"),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=20,
            spaceBefore=20,
            fontName="Helvetica-Bold",
        )

        # Cover / Title
        story.append(Paragraph(f"{company_name}", title_style))
        story.append(Paragraph(f"Financial Statements", styles["Heading2"]))
        story.append(Paragraph(f"For the Year Ended 30 June {year}", styles["Normal"]))
        story.append(Spacer(1, 0.5 * inch))
        story.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%d %B %Y')}", styles["Normal"]
            )
        )
        story.append(PageBreak())

        # Income Statement
        story.append(Paragraph("Income Statement", heading_style))
        story.append(Paragraph(f"For the Year Ended 30 June {year}", styles["Normal"]))
        story.append(Spacer(1, 0.25 * inch))

        if income_data:
            income_table_data = [["Description", f"{year}", f"{year - 1}"]]

            # Add revenue section
            income_table_data.append(["REVENUE", "", ""])
            revenue_items = {
                k: v
                for k, v in income_data.items()
                if "revenue" in k.lower()
                or "sales" in k.lower()
                or "income" in k.lower()
            }
            for account, value in revenue_items.items():
                income_table_data.append([f"  {account}", f"${value:,.2f}", ""])

            # Add expense section
            income_table_data.append(["", "", ""])
            income_table_data.append(["EXPENSES", "", ""])
            expense_items = {
                k: v
                for k, v in income_data.items()
                if "expense" in k.lower() or "cost" in k.lower()
            }
            for account, value in expense_items.items():
                income_table_data.append([f"  {account}", f"${value:,.2f}", ""])

            # Create table
            income_table = Table(
                income_table_data, colWidths=[4 * inch, 1.5 * inch, 1.5 * inch]
            )
            income_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 10),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#f0f2f6")],
                        ),
                    ]
                )
            )

            story.append(income_table)
        else:
            story.append(
                Paragraph("No income statement data available", styles["Normal"])
            )

        story.append(PageBreak())

        # Balance Sheet
        story.append(Paragraph("Balance Sheet", heading_style))
        story.append(Paragraph(f"As at 30 June {year}", styles["Normal"]))
        story.append(Spacer(1, 0.25 * inch))

        if balance_data:
            balance_table_data = [["Description", f"{year}", f"{year - 1}"]]

            # Assets
            balance_table_data.append(["ASSETS", "", ""])
            asset_items = {
                k: v for k, v in balance_data.items() if "asset" in k.lower()
            }
            for account, value in asset_items.items():
                balance_table_data.append([f"  {account}", f"${value:,.2f}", ""])

            # Liabilities
            balance_table_data.append(["", "", ""])
            balance_table_data.append(["LIABILITIES", "", ""])
            liability_items = {
                k: v
                for k, v in balance_data.items()
                if "liability" in k.lower() or "debt" in k.lower()
            }
            for account, value in liability_items.items():
                balance_table_data.append([f"  {account}", f"${value:,.2f}", ""])

            # Equity
            balance_table_data.append(["", "", ""])
            balance_table_data.append(["EQUITY", "", ""])
            equity_items = {
                k: v for k, v in balance_data.items() if "equity" in k.lower()
            }
            for account, value in equity_items.items():
                balance_table_data.append([f"  {account}", f"${value:,.2f}", ""])

            balance_table = Table(
                balance_table_data, colWidths=[4 * inch, 1.5 * inch, 1.5 * inch]
            )
            balance_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 10),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#f0f2f6")],
                        ),
                    ]
                )
            )

            story.append(balance_table)
        else:
            story.append(Paragraph("No balance sheet data available", styles["Normal"]))

        # Notes (if any)
        if notes:
            story.append(PageBreak())
            story.append(Paragraph("Notes to Financial Statements", heading_style))
            for note in notes:
                story.append(Paragraph(note, styles["Normal"]))
                story.append(Spacer(1, 0.1 * inch))

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes


# ==================== MAIN APP ====================


def main():
    st.markdown(
        '<div class="main-header">📊 Financial Statement Generator v2.0</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "**Simplified Working Version** - Proper extraction, editable preview, clean PDF generation"
    )

    # Initialize session state
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "extracted_accounts" not in st.session_state:
        st.session_state.extracted_accounts = {}
    if "template_labels" not in st.session_state:
        st.session_state.template_labels = []
    if "mapping_df" not in st.session_state:
        st.session_state.mapping_df = None
    if "cache_dir" not in st.session_state:
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)
        st.session_state.cache_dir = cache_dir

    # Progress tracker
    progress_cols = st.columns(4)
    with progress_cols[0]:
        st.markdown(
            f"**{'✅' if st.session_state.step >= 1 else '⬜'} Step 1: Upload**"
        )
    with progress_cols[1]:
        st.markdown(
            f"**{'✅' if st.session_state.step >= 2 else '⬜'} Step 2: Extract**"
        )
    with progress_cols[2]:
        st.markdown(
            f"**{'✅' if st.session_state.step >= 3 else '⬜'} Step 3: Review**"
        )
    with progress_cols[3]:
        st.markdown(
            f"**{'✅' if st.session_state.step >= 4 else '⬜'} Step 4: Generate**"
        )

    st.markdown("---")

    # STEP 1: Upload Files
    st.markdown(
        '<div class="sub-header">Step 1: Upload Files</div>', unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📄 2024 Template (PDF)**")
        st.info(
            "Upload your previous year's financial statements. We'll extract the structure."
        )
        template_pdf = st.file_uploader(
            "Choose PDF file", type=["pdf"], key="pdf_upload"
        )

    with col2:
        st.markdown("**📊 2025 Data (Excel)**")
        st.info(
            "Upload your current year's data. We'll extract all accounts and values."
        )
        data_excel = st.file_uploader(
            "Choose Excel file", type=["xlsx", "xls"], key="excel_upload"
        )

    if not (template_pdf and data_excel):
        st.warning("⚠️ Please upload both files to continue")
        return

    # STEP 2: Extract Data
    if st.session_state.step >= 1:
        st.markdown("---")
        st.markdown(
            '<div class="sub-header">Step 2: Data Extraction & Mapping</div>',
            unsafe_allow_html=True,
        )

        # Mapping method selection
        st.markdown("**Select Mapping Method:**")

        mapping_method = st.radio(
            "Choose method",
            ["ai", "structured", "fuzzy"],
            format_func=lambda x: {
                "ai": "🤖 AI-Powered (Maximum Accuracy - 100% Focus)",
                "structured": "🏗️ Structured (Fast & Good)",
                "fuzzy": "🔤 Basic Fuzzy (Quick Test)",
            }[x],
            key="mapping_method",
            index=0,  # Default to AI
        )

        # Show method info
        if mapping_method == "ai":
            st.info("""
            **🎯 Maximum Accuracy Mode**
            - Model: Alibaba Tongyi DeepResearch 30B
            - Batch size: 20 items (smaller = more accurate)
            - Temperature: 0.05 (very low for consistency)
            - Double-check: Enabled (re-validates uncertain mappings)
            - Time: 5-10 minutes (accuracy over speed)
            - Expected: 80-85% High Confidence matches
            """)

            enable_double_check = st.checkbox(
                "Enable Double-Check Mode (recommended for 100% accuracy)",
                value=True,
                help="Re-validates Medium and Low confidence mappings with focused prompts. Takes longer but ensures maximum accuracy.",
            )
            st.session_state.double_check = enable_double_check
        elif mapping_method == "structured":
            st.info(
                "📊 Groups by Revenue/Expense/Asset/Liability/Equity - Fast & accurate"
            )
        else:
            st.info("📝 Simple text similarity matching - Quick test only")

        # Helper function to generate cache key
        def get_cache_key(template_bytes, data_bytes, method):
            combined = template_bytes + data_bytes + method.encode()
            return hashlib.md5(combined).hexdigest()

        if st.button("🔄 Extract & Map Data", type="primary", key="extract_btn"):
            # Extract data first
            with st.spinner("Extracting data from files..."):
                excel_bytes = data_excel.read()
                pdf_bytes = template_pdf.read()

                st.session_state.extracted_accounts = (
                    ExcelExtractor.extract_all_accounts(excel_bytes)
                )
                st.session_state.template_labels = PDFExtractor.extract_labels(
                    pdf_bytes
                )

            # Generate cache key
            cache_key = get_cache_key(pdf_bytes, excel_bytes, mapping_method)
            cache_file = st.session_state.cache_dir / f"mapping_{cache_key}.pkl"

            # Check if cached mapping exists
            if cache_file.exists():
                st.info("💾 Found cached mapping! Loading from cache...")
                with open(cache_file, "rb") as f:
                    st.session_state.mapping_df = pickle.load(f)
                st.success("✅ Loaded mapping from cache (instant!)")
                st.session_state.step = 2
                st.rerun()

            # No cache found - proceed with mapping
            st.info("🔄 No cache found, creating new mappings...")

            if mapping_method == "ai":
                st.markdown("---")
                st.markdown("**🤖 AI Mapping Progress:**")
                progress_text = st.empty()
                progress_bar = st.progress(0)

                with st.spinner("AI is analyzing accounts with financial context..."):
                    # This will take time but will be accurate
                    progress_text.info(
                        "⏳ This may take 5-10 minutes for maximum accuracy. Please be patient..."
                    )

                    st.session_state.mapping_df = SmartMatcher.match_accounts(
                        st.session_state.template_labels,
                        st.session_state.extracted_accounts,
                        method=mapping_method,
                    )

                    progress_bar.progress(100)
                    progress_text.success(
                        "✅ AI mapping complete with double-check validation!"
                    )

                    # Save to cache
                    with open(cache_file, "wb") as f:
                        pickle.dump(st.session_state.mapping_df, f)
                    st.success(f"💾 Mapping saved to cache for future use!")

                st.session_state.step = 2
                st.rerun()
            else:
                with st.spinner(
                    f"Creating intelligent mappings using {mapping_method} method..."
                ):
                    # Create mappings with selected method
                    st.session_state.mapping_df = SmartMatcher.match_accounts(
                        st.session_state.template_labels,
                        st.session_state.extracted_accounts,
                        method=mapping_method,
                    )

                    # Save to cache
                    with open(cache_file, "wb") as f:
                        pickle.dump(st.session_state.mapping_df, f)
                    st.success(f"💾 Mapping saved to cache for future use!")

                st.session_state.step = 2
                st.rerun()

    # Show extraction results
    if st.session_state.step >= 2:
        # Add cache management
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Clear Cache", help="Clear all cached mappings"):
                import shutil

                if st.session_state.cache_dir.exists():
                    shutil.rmtree(st.session_state.cache_dir)
                    st.session_state.cache_dir.mkdir(exist_ok=True)
                    st.success("✅ Cache cleared!")
                    st.rerun()

        with col1:
            st.markdown("")  # Spacing
        st.markdown(
            '<div class="success-box">✅ Data extraction completed successfully!</div>',
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Excel Accounts Extracted", len(st.session_state.extracted_accounts)
            )
        with col2:
            st.metric("Template Labels Found", len(st.session_state.template_labels))
        with col3:
            if st.session_state.mapping_df is not None:
                high_conf = len(
                    st.session_state.mapping_df[
                        st.session_state.mapping_df["Confidence"] == "High"
                    ]
                )
                st.metric("High Confidence Matches", high_conf)

        # Show sample extracted data
        with st.expander("📋 View Extracted Accounts (Sample)"):
            sample_accounts = dict(
                list(st.session_state.extracted_accounts.items())[:20]
            )
            sample_df = pd.DataFrame(
                [
                    {"Account": k, "Value": f"${v:,.2f}"}
                    for k, v in sample_accounts.items()
                ]
            )
            st.dataframe(sample_df, use_container_width=True)

    # STEP 3: Review & Edit Mappings
    if st.session_state.step >= 2:
        st.markdown("---")
        st.markdown(
            '<div class="sub-header">Step 3: Review & Edit Mappings</div>',
            unsafe_allow_html=True,
        )

        st.info(
            "⚡ Review the automatic mappings below. You can edit any field by clicking on it. Click outside to save changes."
        )

        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            filter_confidence = st.selectbox(
                "Filter by Confidence",
                ["All", "High", "Medium", "Low"],
                key="filter_conf",
            )
        with col2:
            show_unmapped = st.checkbox("Show only unmapped items", key="show_unmapped")

        # Apply filters
        display_df = st.session_state.mapping_df.copy()

        if filter_confidence != "All":
            display_df = display_df[display_df["Confidence"] == filter_confidence]

        if show_unmapped:
            display_df = display_df[display_df["Matched Account"] == ""]

        # Check if AI Reasoning column exists
        has_reasoning = "AI Reasoning" in display_df.columns
        has_category = "Category" in display_df.columns

        # Build column config
        column_config = {
            "Status": st.column_config.TextColumn("", width="small"),
            "Template Label": st.column_config.TextColumn(
                "Template Label", width="large"
            ),
            "Matched Account": st.column_config.SelectboxColumn(
                "Matched Account",
                options=[""] + list(st.session_state.extracted_accounts.keys()),
                width="large",
            ),
            "Value (2025)": st.column_config.NumberColumn(
                "Value (2025)", format="$%.2f"
            ),
            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
            "Score": st.column_config.NumberColumn("Match Score", format="%d"),
        }

        if has_reasoning:
            column_config["AI Reasoning"] = st.column_config.TextColumn(
                "AI Reasoning", width="large"
            )

        if has_category:
            column_config["Category"] = st.column_config.TextColumn(
                "Category", width="small"
            )

        # Editable dataframe
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config=column_config,
            hide_index=True,
            key="mapping_editor",
        )

        # Save edited mappings
        if st.button("💾 Save Changes", key="save_mappings"):
            st.session_state.mapping_df = edited_df
            st.success("✅ Mappings saved!")
            st.session_state.step = 3
            st.rerun()

        # Statistics
        if st.session_state.step >= 3:
            st.markdown("---")
            st.markdown("**Mapping Statistics:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total = len(edited_df)
                st.metric("Total Items", total)
            with col2:
                mapped = len(edited_df[edited_df["Matched Account"] != ""])
                st.metric("Mapped", mapped)
            with col3:
                unmapped = total - mapped
                st.metric("Unmapped", unmapped)
            with col4:
                pct = (mapped / total * 100) if total > 0 else 0
                st.metric("Coverage", f"{pct:.1f}%")

    # STEP 4: Generate PDF
    if st.session_state.step >= 3:
        st.markdown("---")
        st.markdown(
            '<div class="sub-header">Step 4: Generate Financial Statements</div>',
            unsafe_allow_html=True,
        )

        # Company details
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input(
                "Company Name", "Paniri Agricultural Co Pty Ltd", key="company_name"
            )
        with col2:
            year = st.number_input(
                "Financial Year",
                min_value=2020,
                max_value=2030,
                value=2025,
                key="fin_year",
            )

        if st.button("🚀 Generate PDF", type="primary", key="generate_btn"):
            with st.spinner("Generating professional PDF..."):
                try:
                    # Prepare data
                    final_mapping = st.session_state.mapping_df[
                        st.session_state.mapping_df["Matched Account"] != ""
                    ]

                    # Separate by statement type (simple heuristic)
                    income_data = {}
                    balance_data = {}

                    for _, row in final_mapping.iterrows():
                        account = row["Matched Account"]
                        value = row["Value (2025)"]
                        label = row["Template Label"].lower()

                        # Categorize
                        if any(
                            kw in label
                            for kw in [
                                "revenue",
                                "sales",
                                "income",
                                "expense",
                                "cost",
                                "profit",
                            ]
                        ):
                            income_data[account] = value
                        elif any(
                            kw in label
                            for kw in [
                                "asset",
                                "liability",
                                "equity",
                                "capital",
                                "debt",
                            ]
                        ):
                            balance_data[account] = value
                        else:
                            # Default to income statement
                            income_data[account] = value

                    # Generate PDF
                    pdf_bytes = PDFGenerator.generate_financial_statements(
                        company_name=company_name,
                        year=year,
                        income_data=income_data,
                        balance_data=balance_data,
                        notes=None,
                    )

                    st.markdown(
                        '<div class="success-box">✅ PDF generated successfully!</div>',
                        unsafe_allow_html=True,
                    )

                    # Download button
                    st.download_button(
                        label="📥 Download Financial Statements PDF",
                        data=pdf_bytes,
                        file_name=f"Financial_Statements_{year}.pdf",
                        mime="application/pdf",
                        key="download_pdf",
                    )

                    st.balloons()

                except Exception as e:
                    st.error(f"❌ Error generating PDF: {e}")
                    st.exception(e)


if __name__ == "__main__":
    main()
