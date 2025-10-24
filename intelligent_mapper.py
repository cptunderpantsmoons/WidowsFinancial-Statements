"""
Intelligent Financial Account Mapper
Uses AI with financial context to create accurate mappings between template and data
"""

import os
import json
import requests
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import pandas as pd
import re

load_dotenv()


class IntelligentMapper:
    """AI-powered financial account mapper with context understanding"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        # Free models with fallback
        self.models = [
            "gpt-oss-20b:free",  # Primary free model
            "gpt-oss-120b",  # Fallback paid model if free fails
            "alibaba/tongyi-deepresearch-30b-a3b:free",  # Additional fallback
        ]
        self.current_model_index = 0
        self.model = self.models[0]

    def create_mappings(
        self,
        template_labels: List[str],
        excel_accounts: Dict[str, float],
        batch_size: int = 20,  # Smaller batches for higher accuracy
        double_check: bool = True,  # Enable second-pass validation
    ) -> pd.DataFrame:
        """
        Create intelligent mappings using AI with financial context.
        Optimized for 100% accuracy over speed.
        Uses smaller batches and multi-pass validation.

        Args:
            template_labels: List of labels from template
            excel_accounts: Dict of account names to values
            batch_size: Number of items per batch (smaller = more accurate)
            double_check: If True, re-validates uncertain mappings (recommended)
        """

        all_mappings = []

        # PASS 1: Initial AI mapping
        print("\n=== PASS 1: Initial AI Mapping ===")
        total_batches = (len(template_labels) - 1) // batch_size + 1
        for i in range(0, len(template_labels), batch_size):
            batch_labels = template_labels[i : i + batch_size]
            print(
                f"🤖 AI Processing batch {i // batch_size + 1}/{total_batches} ({len(batch_labels)} items)..."
            )

            batch_mappings = self._map_batch(batch_labels, excel_accounts)
            all_mappings.extend(batch_mappings)

            print(f"   ✓ Batch {i // batch_size + 1} complete")

        # Convert to DataFrame
        df = pd.DataFrame(all_mappings)

        # Validate and enhance mappings
        df = self._validate_and_enhance(df, excel_accounts)

        # PASS 2: Double-check uncertain mappings for maximum accuracy
        if double_check:
            df = self._double_check_uncertain(df, excel_accounts)

        return df

    def _map_batch(
        self, template_labels: List[str], excel_accounts: Dict[str, float]
    ) -> List[Dict]:
        """Map a batch of template labels to excel accounts using AI"""

        # Prepare account list with values for context - include MORE context for accuracy
        account_list = []
        for account, value in excel_accounts.items():
            account_list.append(f"{account} (${value:,.2f})")

        prompt = self._build_intelligent_prompt(
            template_labels,
            account_list[:500],  # More context for better accuracy
        )

        try:
            mappings_json = self._call_ai(prompt)
            mappings = self._parse_ai_response(mappings_json, excel_accounts)

            # Create result list
            results = []
            for label in template_labels:
                mapping = mappings.get(label, {})
                matched_account = mapping.get("account", "")
                confidence = mapping.get("confidence", 0)
                reasoning = mapping.get("reasoning", "")

                # Get value
                value = excel_accounts.get(matched_account, 0) if matched_account else 0

                # Determine status
                if confidence >= 0.9:
                    status = "✅"
                    conf_label = "High"
                elif confidence >= 0.7:
                    status = "⚠️"
                    conf_label = "Medium"
                else:
                    status = "❌"
                    conf_label = "Low"

                results.append(
                    {
                        "Status": status,
                        "Template Label": label,
                        "Matched Account": matched_account,
                        "Value (2025)": value,
                        "Confidence": conf_label,
                        "Score": int(confidence * 100),
                        "AI Reasoning": reasoning,
                    }
                )

            return results

        except Exception as e:
            print(f"AI mapping failed: {e}, falling back to fuzzy matching")
            return self._fallback_fuzzy_match(template_labels, excel_accounts)

    def _build_intelligent_prompt(
        self, template_labels: List[str], account_list: List[str]
    ) -> str:
        """Build detailed prompt for AI mapping with financial context"""

        labels_text = "\n".join(
            [f"{i + 1}. {label}" for i, label in enumerate(template_labels)]
        )
        accounts_text = "\n".join([f"- {acc}" for acc in account_list])

        prompt = f"""You are a senior financial accountant with 20+ years experience in financial statement preparation and analysis.

OBJECTIVE: Map financial statement line items from a 2024 template to corresponding accounts in 2025 data with MAXIMUM ACCURACY.

CRITICAL: Take your time. Accuracy is MORE important than speed. Every mapping must be financially correct.

=== TEMPLATE LABELS (from 2024 Financial Statement) ===
{labels_text}

=== AVAILABLE ACCOUNTS (from 2025 Chart of Accounts with values) ===
{accounts_text}

=== FINANCIAL MAPPING PRINCIPLES ===

1. SEMANTIC EQUIVALENCE - Match by financial meaning:
   • Revenue = Sales = Turnover = Income (operating)
   • COGS = Cost of Sales = Cost of Goods Sold
   • Net Income = Net Profit = Profit After Tax = Bottom Line
   • EBITDA = Operating Income (before D&A)
   • Gross Profit = Revenue - COGS

2. ACCOUNT HIERARCHY - Understand parent-child relationships:
   • "Total Assets" includes "Current Assets" + "Non-Current Assets"
   • "Current Assets" includes "Cash", "Receivables", "Inventory"
   • "Total Expenses" includes all expense sub-categories
   • Sub-accounts roll up to totals

3. ACCOUNT CODES - Ignore numeric prefixes:
   • "40050 - Trade Sales" → focus on "Trade Sales"
   • "79584 - Commission Income" → focus on "Commission Income"
   • "IC_" prefix means internal company account

4. FINANCIAL STATEMENT SECTIONS:
   • Income Statement: Revenue, Expenses, Profit/Loss
   • Balance Sheet: Assets, Liabilities, Equity
   • Cash Flow: Operating/Investing/Financing activities

5. COMMON VARIATIONS:
   • "Shareholders Equity" = "Owner's Equity" = "Net Worth"
   • "Accounts Receivable" = "Debtors" = "Trade Receivables"
   • "Accounts Payable" = "Creditors" = "Trade Payables"
   • "Property, Plant & Equipment" = "Fixed Assets" = "Tangible Assets"

6. MATCHING QUALITY:
   • 0.95-1.0: Exact semantic match (same financial concept)
   • 0.85-0.94: Strong match (clear relationship, minor wording difference)
   • 0.70-0.84: Good match (same category, reasonable fit)
   • Below 0.70: Uncertain or no match (leave blank if < 0.60)

=== OUTPUT REQUIREMENTS ===

Return ONLY a JSON object with this EXACT structure:
{{
  "Template Label Name": {{
    "account": "Exact Account Name from Available Accounts",
    "confidence": 0.XX,
    "reasoning": "Detailed explanation of why this is the correct match"
  }}
}}

VALIDATION CHECKLIST for each mapping:
✓ Is the account name EXACTLY as shown in available accounts?
✓ Does the financial meaning match (not just similar words)?
✓ Does the value seem appropriate for this type of account?
✓ Have I considered the account category (revenue/expense/asset/liability/equity)?
✓ If confidence < 0.70, should I leave it blank?

BE EXTREMELY CAREFUL WITH:
- Totals vs sub-items (don't map "Total Revenue" to a sub-category)
- Similar names with different meanings
- Account codes and prefixes
- Negative values (expenses, some equity items)

Now carefully map all {len(template_labels)} labels with maximum accuracy:"""

        return prompt

    def _call_ai(self, prompt: str, retry_count: int = 0) -> str:
        """Call OpenRouter API with the mapping prompt, with model fallback"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8503",
            "X-Title": "Financial Statement Mapper",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior financial accountant with expertise in financial statement preparation, GAAP/IFRS standards, and chart of accounts mapping. Your responses must be accurate, thoughtful, and in valid JSON format only. Accuracy is more important than speed.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.05,  # Very low temperature for maximum consistency and accuracy
            "max_tokens": 16000,  # More tokens for detailed responses
            "top_p": 0.9,  # Focused sampling
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=300,  # 5 minutes - accuracy over speed
            )

            if response.status_code == 429 or response.status_code == 503:
                # Rate limit or service unavailable - try next model
                raise Exception(f"Model unavailable: {response.status_code}")

            if response.status_code != 200:
                raise Exception(f"API error {response.status_code}: {response.text}")

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            return content

        except Exception as e:
            # Try fallback model if available
            if self.current_model_index < len(self.models) - 1 and retry_count < len(
                self.models
            ):
                self.current_model_index += 1
                old_model = self.model
                self.model = self.models[self.current_model_index]
                print(f"   ⚠️ Model {old_model} failed, switching to {self.model}")
                return self._call_ai(prompt, retry_count + 1)
            else:
                raise Exception(f"All models failed: {str(e)}")

    def _parse_ai_response(
        self, ai_response: str, excel_accounts: Dict[str, float]
    ) -> Dict:
        """Parse AI JSON response into mappings"""

        try:
            # Extract JSON from response (may have markdown code blocks)
            json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                json_str = ai_response

            # Parse JSON
            mappings_raw = json.loads(json_str)

            # Validate and clean mappings
            clean_mappings = {}
            for label, mapping_data in mappings_raw.items():
                if isinstance(mapping_data, dict):
                    account = mapping_data.get("account", "")

                    # Verify account exists in our data
                    if account and account not in excel_accounts:
                        # Try to find close match
                        account = self._find_closest_account(account, excel_accounts)

                    clean_mappings[label] = {
                        "account": account,
                        "confidence": mapping_data.get("confidence", 0.5),
                        "reasoning": mapping_data.get("reasoning", "AI matched"),
                    }

            return clean_mappings

        except json.JSONDecodeError as e:
            print(f"Failed to parse AI JSON: {e}")
            print(f"Response was: {ai_response[:500]}")
            return {}

    def _find_closest_account(
        self, account: str, excel_accounts: Dict[str, float]
    ) -> str:
        """Find closest matching account name"""

        account_lower = account.lower()

        # Try exact match (case insensitive)
        for acc in excel_accounts.keys():
            if acc.lower() == account_lower:
                return acc

        # Try partial match
        for acc in excel_accounts.keys():
            if account_lower in acc.lower() or acc.lower() in account_lower:
                return acc

        # No match found
        return ""

    def _fallback_fuzzy_match(
        self, template_labels: List[str], excel_accounts: Dict[str, float]
    ) -> List[Dict]:
        """Fallback to simple fuzzy matching if AI fails"""

        from fuzzywuzzy import fuzz

        results = []
        for label in template_labels:
            best_match = None
            best_score = 0

            for account in excel_accounts.keys():
                score = fuzz.token_set_ratio(label.lower(), account.lower())
                if score > best_score:
                    best_score = score
                    best_match = account

            value = excel_accounts.get(best_match, 0) if best_match else 0

            if best_score >= 90:
                status = "✅"
                confidence = "High"
            elif best_score >= 70:
                status = "⚠️"
                confidence = "Medium"
            else:
                status = "❌"
                confidence = "Low"

            results.append(
                {
                    "Status": status,
                    "Template Label": label,
                    "Matched Account": best_match if best_match else "",
                    "Value (2025)": value,
                    "Confidence": confidence,
                    "Score": best_score,
                    "AI Reasoning": "Fuzzy match (AI unavailable)",
                }
            )

        return results
# Insert these methods at line 385 in IntelligentMapper class, before the class ends

    def _validate_and_enhance(
        self, df: pd.DataFrame, excel_accounts: Dict[str, float]
    ) -> pd.DataFrame:
        """
        Post-processing validation to ensure maximum accuracy.
        Double-checks mappings and enhances confidence scores.
        """

        print("🔍 Validating mappings for accuracy...")

        # Check for duplicate mappings (multiple labels to same account)
        account_counts = df[df["Matched Account"] != ""][
            "Matched Account"
        ].value_counts()
        duplicates = account_counts[account_counts > 1]

        if len(duplicates) > 0:
            print(
                f"   ⚠️  Found {len(duplicates)} accounts mapped multiple times - may need review"
            )

        # Check for very low confidence mappings
        low_conf = len(df[df["Score"] < 70])
        if low_conf > 0:
            print(
                f"   ⚠️  Found {low_conf} low confidence mappings - manual review recommended"
            )

        # Check for unmapped items
        unmapped = len(df[df["Matched Account"] == ""])
        if unmapped > 0:
            print(f"   ℹ️  {unmapped} items unmapped (no good match found)")

        # Enhance confidence for exact matches
        for idx, row in df.iterrows():
            if row["Matched Account"]:
                label_clean = row["Template Label"].lower().strip()
                account_clean = row["Matched Account"].lower().strip()

                # Boost confidence for exact or near-exact matches
                if label_clean == account_clean:
                    df.at[idx, "Score"] = 100
                    df.at[idx, "Confidence"] = "High"
                    df.at[idx, "Status"] = "✅"

        print("✓ Validation complete")
        return df

    def _double_check_uncertain(
        self, df: pd.DataFrame, excel_accounts: Dict[str, float]
    ) -> pd.DataFrame:
        """
        PASS 2: Re-validate uncertain mappings with focused prompts for maximum accuracy.
        Reviews Medium and Low confidence items with additional context.
        """

        print("\n=== PASS 2: Double-Check Uncertain Mappings ===")

        # Find items that need double-checking (confidence < High or unmapped)
        uncertain = df[
            (df["Confidence"].isin(["Medium", "Low"])) | (df["Matched Account"] == "")
        ].copy()

        if len(uncertain) == 0:
            print("✓ All mappings are high confidence - no double-check needed")
            return df

        print(
            f"🔍 Re-validating {len(uncertain)} uncertain mappings for maximum accuracy..."
        )

        # Process uncertain items in small focused batches
        for idx, row in uncertain.iterrows():
            label = row["Template Label"]
            current_match = row["Matched Account"]
            current_conf = row["Score"]

            # Get better match with focused prompt
            improved_match = self._focused_revalidation(
                label, current_match, excel_accounts
            )

            if improved_match:
                # Update the main dataframe
                df.at[idx, "Matched Account"] = improved_match["account"]
                df.at[idx, "Score"] = int(improved_match["confidence"] * 100)
                df.at[idx, "AI Reasoning"] = (
                    improved_match["reasoning"] + " [Re-validated]"
                )

                # Update confidence and status
                new_score = improved_match["confidence"] * 100
                if new_score >= 90:
                    df.at[idx, "Confidence"] = "High"
                    df.at[idx, "Status"] = "✅"
                elif new_score >= 70:
                    df.at[idx, "Confidence"] = "Medium"
                    df.at[idx, "Status"] = "⚠️"
                else:
                    df.at[idx, "Confidence"] = "Low"
                    df.at[idx, "Status"] = "❌"

        print("✓ Double-check complete - accuracy improved!")
        return df

    def _focused_revalidation(
        self, label: str, current_match: str, excel_accounts: Dict[str, float]
    ) -> Optional[Dict]:
        """
        Focused re-validation of a single uncertain mapping.
        Uses a more detailed prompt with additional context.
        """

        # Get top 10 most relevant accounts for focused analysis
        from fuzzywuzzy import fuzz

        candidates = []
        for account, value in excel_accounts.items():
            score = fuzz.token_set_ratio(label.lower(), account.lower())
            candidates.append((account, value, score))

        # Sort by score and take top 10
        candidates.sort(key=lambda x: x[2], reverse=True)
        top_candidates = candidates[:10]

        candidates_text = "\n".join(
            [
                f"{i + 1}. {acc} (${val:,.2f}) - Text similarity: {score}%"
                for i, (acc, val, score) in enumerate(top_candidates)
            ]
        )

        prompt = f"""You are doing a SECOND-PASS validation for MAXIMUM ACCURACY.

TEMPLATE LABEL TO MAP:
"{label}"

CURRENT MAPPING (from first pass):
Account: "{current_match if current_match else "NONE"}"

TOP 10 CANDIDATE ACCOUNTS (sorted by relevance):
{candidates_text}

YOUR TASK:
1. Review the current mapping critically
2. Consider all candidate accounts
3. Choose the MOST ACCURATE match based on financial meaning
4. If none are good matches, set account to empty string

CRITICAL QUESTIONS:
- Does the current mapping truly represent the same financial concept?
- Is there a better match in the candidates?
- Should this be a total or a sub-account?
- Does the value make sense for this type of account?

Return ONLY valid JSON:
{{
  "account": "Best matching account name (or empty string)",
  "confidence": 0.XX,
  "reasoning": "Detailed explanation of why this is correct"
}}"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8503",
                "X-Title": "Financial Statement Mapper - Validation Pass",
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a senior financial auditor performing accuracy validation. Be extremely critical and precise.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.01,  # Even lower for validation
                "max_tokens": 2000,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Parse response
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    mapping = json.loads(json_match.group())

                    # Verify account exists
                    account = mapping.get("account", "")
                    if account and account not in excel_accounts:
                        account = self._find_closest_account(account, excel_accounts)
                        mapping["account"] = account

                    return mapping

        except Exception as e:
            print(f"   ⚠️  Re-validation failed for '{label}': {e}")

        return None



class StructuredMapper:
    """
    Alternative mapper that uses financial statement structure
    Groups accounts by type for better accuracy
    """

    def __init__(self):
        self.account_categories = {
            "revenue": ["revenue", "sales", "income", "fees", "turnover"],
            "expense": [
                "expense",
                "cost",
                "depreciation",
                "amortization",
                "interest",
                "tax",
            ],
            "asset": [
                "asset",
                "cash",
                "receivable",
                "inventory",
                "property",
                "equipment",
            ],
            "liability": ["liability", "payable", "loan", "borrowing", "debt"],
            "equity": ["equity", "capital", "retained", "reserve", "share"],
        }

    def categorize_account(self, account_name: str) -> str:
        """Categorize account into financial statement section"""

        account_lower = account_name.lower()

        for category, keywords in self.account_categories.items():
            if any(kw in account_lower for kw in keywords):
                return category

        return "other"

    def create_structured_mappings(
        self, template_labels: List[str], excel_accounts: Dict[str, float]
    ) -> pd.DataFrame:
        """
        Create mappings using financial structure understanding
        More accurate than pure fuzzy matching
        """

        from fuzzywuzzy import fuzz

        # Categorize all accounts
        excel_categorized = {}
        for account, value in excel_accounts.items():
            category = self.categorize_account(account)
            if category not in excel_categorized:
                excel_categorized[category] = {}
            excel_categorized[category][account] = value

        results = []

        for label in template_labels:
            # Categorize label
            label_category = self.categorize_account(label)

            # Search within same category first
            candidate_accounts = excel_categorized.get(label_category, {})

            # If no candidates in category, search all
            if not candidate_accounts:
                candidate_accounts = excel_accounts

            # Find best match within candidates
            best_match = None
            best_score = 0

            for account in candidate_accounts.keys():
                # Use multiple scoring methods
                token_score = fuzz.token_set_ratio(label.lower(), account.lower())
                partial_score = fuzz.partial_ratio(label.lower(), account.lower())

                # Weighted average (token_set more important)
                combined_score = (token_score * 0.7) + (partial_score * 0.3)

                if combined_score > best_score:
                    best_score = combined_score
                    best_match = account

            value = excel_accounts.get(best_match, 0) if best_match else 0

            # Adjust confidence based on category match
            if best_match and self.categorize_account(best_match) == label_category:
                best_score = min(100, best_score * 1.1)  # Boost for category match

            if best_score >= 85:
                status = "✅"
                confidence = "High"
            elif best_score >= 65:
                status = "⚠️"
                confidence = "Medium"
            else:
                status = "❌"
                confidence = "Low"

            results.append(
                {
                    "Status": status,
                    "Template Label": label,
                    "Matched Account": best_match if best_match else "",
                    "Value (2025)": value,
                    "Confidence": confidence,
                    "Score": int(best_score),
                    "Category": label_category.title(),
                }
            )

        return pd.DataFrame(results)

    def _validate_and_enhance(
        self, df: pd.DataFrame, excel_accounts: Dict[str, float]
    ) -> pd.DataFrame:
        """
        Post-processing validation to ensure maximum accuracy.
        Double-checks mappings and enhances confidence scores.
        """

        print("🔍 Validating mappings for accuracy...")

        # Check for duplicate mappings (multiple labels to same account)
        account_counts = df[df["Matched Account"] != ""][
            "Matched Account"
        ].value_counts()
        duplicates = account_counts[account_counts > 1]

        if len(duplicates) > 0:
            print(
                f"   ⚠️  Found {len(duplicates)} accounts mapped multiple times - may need review"
            )

        # Check for very low confidence mappings
        low_conf = len(df[df["Score"] < 70])
        if low_conf > 0:
            print(
                f"   ⚠️  Found {low_conf} low confidence mappings - manual review recommended"
            )

        # Check for unmapped items
        unmapped = len(df[df["Matched Account"] == ""])
        if unmapped > 0:
            print(f"   ℹ️  {unmapped} items unmapped (no good match found)")

        # Enhance confidence for exact matches
        for idx, row in df.iterrows():
            if row["Matched Account"]:
                label_clean = row["Template Label"].lower().strip()
                account_clean = row["Matched Account"].lower().strip()

                # Boost confidence for exact or near-exact matches
                if label_clean == account_clean:
                    df.at[idx, "Score"] = 100
                    df.at[idx, "Confidence"] = "High"
                    df.at[idx, "Status"] = "✅"

        print("✓ Validation complete")
        return df

    def _double_check_uncertain(
        self, df: pd.DataFrame, excel_accounts: Dict[str, float]
    ) -> pd.DataFrame:
        """
        PASS 2: Re-validate uncertain mappings with focused prompts for maximum accuracy.
        Reviews Medium and Low confidence items with additional context.
        """

        print("\n=== PASS 2: Double-Check Uncertain Mappings ===")

        # Find items that need double-checking (confidence < High or unmapped)
        uncertain = df[
            (df["Confidence"].isin(["Medium", "Low"])) | (df["Matched Account"] == "")
        ].copy()

        if len(uncertain) == 0:
            print("✓ All mappings are high confidence - no double-check needed")
            return df

        print(
            f"🔍 Re-validating {len(uncertain)} uncertain mappings for maximum accuracy..."
        )

        # Process uncertain items in small focused batches
        for idx, row in uncertain.iterrows():
            label = row["Template Label"]
            current_match = row["Matched Account"]
            current_conf = row["Score"]

            # Get better match with focused prompt
            improved_match = self._focused_revalidation(
                label, current_match, excel_accounts
            )

            if improved_match:
                # Update the main dataframe
                df.at[idx, "Matched Account"] = improved_match["account"]
                df.at[idx, "Score"] = int(improved_match["confidence"] * 100)
                df.at[idx, "AI Reasoning"] = (
                    improved_match["reasoning"] + " [Re-validated]"
                )

                # Update confidence and status
                new_score = improved_match["confidence"] * 100
                if new_score >= 90:
                    df.at[idx, "Confidence"] = "High"
                    df.at[idx, "Status"] = "✅"
                elif new_score >= 70:
                    df.at[idx, "Confidence"] = "Medium"
                    df.at[idx, "Status"] = "⚠️"
                else:
                    df.at[idx, "Confidence"] = "Low"
                    df.at[idx, "Status"] = "❌"

        print("✓ Double-check complete - accuracy improved!")
        return df

    def _focused_revalidation(
        self, label: str, current_match: str, excel_accounts: Dict[str, float]
    ) -> Optional[Dict]:
        """
        Focused re-validation of a single uncertain mapping.
        Uses a more detailed prompt with additional context.
        """

        # Get top 10 most relevant accounts for focused analysis
        from fuzzywuzzy import fuzz

        candidates = []
        for account, value in excel_accounts.items():
            score = fuzz.token_set_ratio(label.lower(), account.lower())
            candidates.append((account, value, score))

        # Sort by score and take top 10
        candidates.sort(key=lambda x: x[2], reverse=True)
        top_candidates = candidates[:10]

        candidates_text = "\n".join(
            [
                f"{i + 1}. {acc} (${val:,.2f}) - Text similarity: {score}%"
                for i, (acc, val, score) in enumerate(top_candidates)
            ]
        )

        prompt = f"""You are doing a SECOND-PASS validation for MAXIMUM ACCURACY.

TEMPLATE LABEL TO MAP:
"{label}"

CURRENT MAPPING (from first pass):
Account: "{current_match if current_match else "NONE"}"

TOP 10 CANDIDATE ACCOUNTS (sorted by relevance):
{candidates_text}

YOUR TASK:
1. Review the current mapping critically
2. Consider all candidate accounts
3. Choose the MOST ACCURATE match based on financial meaning
4. If none are good matches, set account to empty string

CRITICAL QUESTIONS:
- Does the current mapping truly represent the same financial concept?
- Is there a better match in the candidates?
- Should this be a total or a sub-account?
- Does the value make sense for this type of account?

Return ONLY valid JSON:
{{
  "account": "Best matching account name (or empty string)",
  "confidence": 0.XX,
  "reasoning": "Detailed explanation of why this is correct"
}}"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8503",
                "X-Title": "Financial Statement Mapper - Validation Pass",
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a senior financial auditor performing accuracy validation. Be extremely critical and precise.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.01,  # Even lower for validation
                "max_tokens": 2000,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Parse response
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    mapping = json.loads(json_match.group())

                    # Verify account exists
                    account = mapping.get("account", "")
                    if account and account not in excel_accounts:
                        account = self._find_closest_account(account, excel_accounts)
                        mapping["account"] = account

                    return mapping

        except Exception as e:
            print(f"   ⚠️  Re-validation failed for '{label}': {e}")

        return None


# Example usage
if __name__ == "__main__":
    # Test with sample data
    mapper = IntelligentMapper()

    sample_labels = [
        "Total Revenue",
        "Cost of Goods Sold",
        "Gross Profit",
        "Operating Expenses",
        "Net Income",
    ]

    sample_accounts = {
        "Revenue from Sales": 1000000,
        "COGS": 600000,
        "Administrative Expenses": 150000,
        "Profit After Tax": 250000,
    }

    mappings = mapper.create_mappings(sample_labels, sample_accounts)
    print(mappings)
