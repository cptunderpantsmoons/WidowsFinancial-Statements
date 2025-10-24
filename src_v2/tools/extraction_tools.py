"""
Advanced Extraction Tools for Financial Statements
Properly extracts tables, text, and notes from PDF and Excel files
"""

import pandas as pd
import pdfplumber
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import re
import io
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """Advanced PDF extraction using pdfplumber for accurate table detection."""

    def __init__(self):
        self.extracted_data = {}

    def extract_all_tables(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extract all tables from PDF with proper structure recognition.
        Returns structured data with page numbers and table positions.
        """
        results = {"tables": [], "text_blocks": [], "metadata": {}, "notes": []}

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                results["metadata"] = {
                    "total_pages": len(pdf.pages),
                    "title": self._extract_title(pdf.pages[0])
                    if len(pdf.pages) > 0
                    else None,
                }

                for page_num, page in enumerate(pdf.pages, start=1):
                    logger.info(f"Processing page {page_num}/{len(pdf.pages)}")

                    # Extract tables
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table and len(table) > 0:
                            cleaned_table = self._clean_table(table)
                            if cleaned_table:
                                results["tables"].append(
                                    {
                                        "page": page_num,
                                        "table_index": table_idx,
                                        "data": cleaned_table,
                                        "type": self._identify_table_type(
                                            cleaned_table
                                        ),
                                    }
                                )

                    # Extract text blocks (for notes and narrative content)
                    text = page.extract_text()
                    if text:
                        text_blocks = self._extract_text_blocks(text, page_num)
                        results["text_blocks"].extend(text_blocks)

                        # Extract notes specifically
                        notes = self._extract_notes(text, page_num)
                        results["notes"].extend(notes)

                logger.info(
                    f"Extracted {len(results['tables'])} tables and {len(results['notes'])} notes"
                )

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise

        return results

    def _extract_title(self, first_page) -> Optional[str]:
        """Extract document title from first page."""
        text = first_page.extract_text()
        if not text:
            return None

        lines = text.split("\n")
        # Usually title is in first few lines
        for line in lines[:5]:
            if len(line) > 10 and not line.startswith("Page"):
                return line.strip()
        return None

    def _clean_table(self, table: List[List]) -> Optional[pd.DataFrame]:
        """
        Clean and structure table data.
        Handles merged cells, empty rows, and formatting issues.
        """
        if not table or len(table) < 2:
            return None

        # Remove completely empty rows
        cleaned_rows = []
        for row in table:
            if any(cell and str(cell).strip() for cell in row):
                cleaned_rows.append(row)

        if len(cleaned_rows) < 2:
            return None

        # Try to identify header row
        header_row = 0
        for idx, row in enumerate(cleaned_rows[:3]):
            if self._looks_like_header(row):
                header_row = idx
                break

        # Create DataFrame
        try:
            df = pd.DataFrame(
                cleaned_rows[header_row + 1 :], columns=cleaned_rows[header_row]
            )

            # Clean column names
            df.columns = [
                str(col).strip() if col else f"Column_{i}"
                for i, col in enumerate(df.columns)
            ]

            # Remove rows where all values are None or empty
            df = df.dropna(how="all")

            return df if len(df) > 0 else None

        except Exception as e:
            logger.warning(f"Failed to create DataFrame from table: {e}")
            return None

    def _looks_like_header(self, row: List) -> bool:
        """Determine if a row looks like a header row."""
        if not row:
            return False

        # Headers typically have text in multiple cells
        non_empty = sum(1 for cell in row if cell and str(cell).strip())

        # Check for common header keywords
        header_keywords = [
            "account",
            "amount",
            "balance",
            "description",
            "particulars",
            "note",
            "year",
            "2024",
            "2025",
        ]
        row_text = " ".join(str(cell).lower() for cell in row if cell)
        has_keywords = any(keyword in row_text for keyword in header_keywords)

        return non_empty >= 2 or has_keywords

    def _identify_table_type(self, df: pd.DataFrame) -> str:
        """Identify the type of financial table."""
        if df is None or df.empty:
            return "unknown"

        # Convert all columns to string for searching
        all_text = " ".join(
            [str(col).lower() for col in df.columns]
            + [str(val).lower() for val in df.values.flatten()]
        )

        if any(
            keyword in all_text
            for keyword in ["revenue", "expense", "income", "profit", "loss"]
        ):
            return "income_statement"
        elif any(keyword in all_text for keyword in ["asset", "liability", "equity"]):
            return "balance_sheet"
        elif any(
            keyword in all_text
            for keyword in ["cash flow", "operating activities", "investing activities"]
        ):
            return "cash_flow"
        elif "note" in all_text:
            return "notes"
        else:
            return "other"

    def _extract_text_blocks(self, text: str, page_num: int) -> List[Dict]:
        """Extract structured text blocks from page text."""
        blocks = []

        # Split into paragraphs
        paragraphs = text.split("\n\n")

        for para_idx, para in enumerate(paragraphs):
            if para.strip():
                blocks.append(
                    {
                        "page": page_num,
                        "index": para_idx,
                        "content": para.strip(),
                        "type": self._classify_text_block(para),
                    }
                )

        return blocks

    def _classify_text_block(self, text: str) -> str:
        """Classify type of text block."""
        text_lower = text.lower()

        if text.startswith("Note") or "note to the financial" in text_lower:
            return "note"
        elif any(
            keyword in text_lower for keyword in ["policy", "accounting", "method"]
        ):
            return "accounting_policy"
        elif "director" in text_lower or "signed" in text_lower:
            return "signature"
        else:
            return "general"

    def _extract_notes(self, text: str, page_num: int) -> List[Dict]:
        """Extract notes to financial statements."""
        notes = []

        # Pattern for notes (e.g., "Note 1:", "1.", "Note 1 -")
        note_pattern = r"(?:Note\s+)?(\d+)[\.:]\s*([^\n]+)"

        matches = re.finditer(note_pattern, text, re.IGNORECASE)

        for match in matches:
            note_num = match.group(1)
            note_title = match.group(2).strip()

            # Try to get note content (next paragraph)
            start_pos = match.end()
            end_pos = text.find("\n\n", start_pos)
            if end_pos == -1:
                end_pos = len(text)

            note_content = text[start_pos:end_pos].strip()

            notes.append(
                {
                    "page": page_num,
                    "note_number": note_num,
                    "title": note_title,
                    "content": note_content,
                }
            )

        return notes


class ExcelExtractor:
    """Advanced Excel extraction handling multi-sheet, multi-column formats."""

    def __init__(self):
        self.data = {}

    def extract_all_sheets(self, excel_bytes: bytes) -> Dict[str, Any]:
        """
        Extract all sheets from Excel file with intelligent parsing.
        Returns structured data for each sheet.
        """
        results = {"sheets": {}, "metadata": {}, "financial_data": {}}

        try:
            # Read all sheets
            excel_file = io.BytesIO(excel_bytes)
            all_sheets = pd.read_excel(excel_file, sheet_name=None, header=None)

            results["metadata"] = {
                "sheet_names": list(all_sheets.keys()),
                "total_sheets": len(all_sheets),
            }

            for sheet_name, df in all_sheets.items():
                logger.info(f"Processing sheet: {sheet_name}")

                # Skip very small sheets (metadata only)
                if len(df) < 3:
                    continue

                # Parse the sheet
                parsed_data = self._parse_financial_sheet(df, sheet_name)

                if parsed_data:
                    results["sheets"][sheet_name] = parsed_data

                    # Extract financial line items
                    financial_items = self._extract_financial_items(parsed_data)
                    if financial_items:
                        results["financial_data"][sheet_name] = financial_items

            logger.info(f"Extracted data from {len(results['sheets'])} sheets")

        except Exception as e:
            logger.error(f"Excel extraction failed: {e}")
            raise

        return results

    def _parse_financial_sheet(
        self, df: pd.DataFrame, sheet_name: str
    ) -> Optional[Dict]:
        """Parse a financial sheet with intelligent header detection."""

        # Find header row
        header_row_idx = self._find_header_row(df)

        if header_row_idx is None:
            logger.warning(f"No header found in sheet {sheet_name}")
            return None

        try:
            # Set header and clean data
            new_df = df.iloc[header_row_idx:].copy()
            new_df.columns = new_df.iloc[0]
            new_df = new_df[1:].reset_index(drop=True)

            # Clean column names
            new_df.columns = [self._clean_column_name(col) for col in new_df.columns]

            # Identify year columns
            year_columns = self._identify_year_columns(new_df.columns)

            # Identify description/account column
            desc_column = self._identify_description_column(new_df.columns)

            return {
                "dataframe": new_df,
                "header_row": header_row_idx,
                "year_columns": year_columns,
                "description_column": desc_column,
                "row_count": len(new_df),
            }

        except Exception as e:
            logger.warning(f"Failed to parse sheet {sheet_name}: {e}")
            return None

    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """Find the row that contains column headers."""

        for idx in range(min(10, len(df))):
            row = df.iloc[idx]

            # Check for header keywords
            row_text = " ".join([str(val).lower() for val in row if pd.notna(val)])

            header_keywords = [
                "particular",
                "account",
                "description",
                "note",
                "year",
                "2024",
                "2025",
                "amount",
                "balance",
            ]

            if any(keyword in row_text for keyword in header_keywords):
                # Check if multiple cells have content (typical for headers)
                non_empty = sum(1 for val in row if pd.notna(val) and str(val).strip())
                if non_empty >= 2:
                    return idx

        return None

    def _clean_column_name(self, col) -> str:
        """Clean column name."""
        if pd.isna(col):
            return "Unnamed"

        col_str = str(col).strip()

        # Handle year columns (2024.0 -> 2024)
        if "." in col_str and col_str.replace(".", "").replace("-", "").isdigit():
            return col_str.split(".")[0]

        return col_str

    def _identify_year_columns(self, columns: List[str]) -> List[str]:
        """Identify columns that contain year data (2024, 2025, etc.)."""
        year_cols = []

        for col in columns:
            col_str = str(col)
            # Check if column name is a year (4 digits between 2000-2100)
            if re.match(r"^(20\d{2})$", col_str):
                year_cols.append(col)

        return sorted(year_cols, reverse=True)  # Most recent first

    def _identify_description_column(self, columns: List[str]) -> Optional[str]:
        """Identify the column containing account descriptions."""

        desc_keywords = ["particular", "account", "description", "name", "item"]

        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in desc_keywords):
                return col

        # Default to first column if no match
        return columns[0] if len(columns) > 0 else None

    def _extract_financial_items(self, parsed_data: Dict) -> Dict[str, float]:
        """Extract financial line items with values."""

        df = parsed_data["dataframe"]
        year_cols = parsed_data["year_columns"]
        desc_col = parsed_data["description_column"]

        if not year_cols or not desc_col:
            return {}

        # Use most recent year
        value_col = year_cols[0]

        financial_items = {}

        for idx, row in df.iterrows():
            account = row.get(desc_col)
            value = row.get(value_col)

            # Skip if no account name
            if pd.isna(account) or not str(account).strip():
                continue

            # Skip header-like rows
            account_str = str(account).strip()
            if account_str.lower() in [
                "particular",
                "particulars",
                "account",
                "description",
            ]:
                continue

            # Convert value to float
            try:
                if pd.notna(value):
                    # Clean value (remove commas, spaces)
                    value_str = str(value).replace(",", "").replace(" ", "").strip()

                    # Handle negative values in parentheses
                    if value_str.startswith("(") and value_str.endswith(")"):
                        value_str = "-" + value_str[1:-1]

                    value_float = float(value_str)

                    # Store non-zero values
                    if value_float != 0:
                        financial_items[account_str] = value_float

            except (ValueError, TypeError):
                continue

        logger.info(f"Extracted {len(financial_items)} financial line items")

        return financial_items


class FinancialDataExtractor:
    """High-level extractor coordinating PDF and Excel extraction."""

    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.excel_extractor = ExcelExtractor()

    def extract_from_template(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Extract comprehensive data from 2024 PDF template."""
        logger.info("Extracting data from PDF template...")

        return self.pdf_extractor.extract_all_tables(pdf_bytes)

    def extract_from_data_file(self, excel_bytes: bytes) -> Dict[str, Any]:
        """Extract comprehensive data from 2025 Excel file."""
        logger.info("Extracting data from Excel file...")

        return self.excel_extractor.extract_all_sheets(excel_bytes)

    def merge_and_structure(
        self, template_data: Dict, current_data: Dict
    ) -> Dict[str, Any]:
        """
        Merge data from both sources into a structured format.
        Creates a unified view of the financial data.
        """
        merged = {
            "template": {
                "structure": template_data.get("tables", []),
                "notes": template_data.get("notes", []),
                "metadata": template_data.get("metadata", {}),
            },
            "current_data": {
                "sheets": current_data.get("sheets", {}),
                "financial_items": current_data.get("financial_data", {}),
                "metadata": current_data.get("metadata", {}),
            },
            "mapping": {},
            "validation": {},
        }

        # Create initial mapping suggestions
        merged["mapping"] = self._suggest_mappings(template_data, current_data)

        return merged

    def _suggest_mappings(
        self, template_data: Dict, current_data: Dict
    ) -> Dict[str, Any]:
        """Suggest mappings between template structure and current data."""

        mappings = {
            "income_statement": {},
            "balance_sheet": {},
            "cash_flow": {},
            "notes": {},
        }

        # Extract template line items
        template_items = []
        for table in template_data.get("tables", []):
            if table["type"] in mappings:
                df = table["data"]
                if df is not None and not df.empty:
                    # Get first column as line items
                    first_col = df.columns[0]
                    template_items.extend(df[first_col].dropna().tolist())

        # Extract current data items
        current_items = {}
        for sheet_name, items in current_data.get("financial_data", {}).items():
            current_items.update(items)

        # Simple fuzzy matching (will be enhanced by AI agent)
        for template_item in template_items:
            template_lower = str(template_item).lower().strip()

            for current_account, value in current_items.items():
                current_lower = current_account.lower().strip()

                # Exact match
                if template_lower == current_lower:
                    mappings["income_statement"][template_item] = {
                        "account": current_account,
                        "value": value,
                        "confidence": 1.0,
                    }
                # Partial match
                elif template_lower in current_lower or current_lower in template_lower:
                    if template_item not in mappings["income_statement"]:
                        mappings["income_statement"][template_item] = {
                            "account": current_account,
                            "value": value,
                            "confidence": 0.7,
                        }

        return mappings


# Utility functions
def extract_year_from_text(text: str) -> Optional[int]:
    """Extract year from text (e.g., '2024', 'FY2025')."""
    pattern = r"(?:FY)?(\d{4})"
    match = re.search(pattern, text)
    return int(match.group(1)) if match else None


def normalize_account_name(name: str) -> str:
    """Normalize account name for better matching."""
    # Remove account codes (e.g., "40050 - Trade Sales" -> "Trade Sales")
    name = re.sub(r"^\d+\s*-\s*", "", name)

    # Remove extra whitespace
    name = " ".join(name.split())

    # Remove IC_ prefix (internal company prefix)
    name = name.replace("IC_", "")

    return name.strip()
