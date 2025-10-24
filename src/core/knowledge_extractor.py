import pandas as pd
import json
import re
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from utils.logger import Logger

logger = Logger(__name__)


class KnowledgeExtractor:
    """Extracts and integrates financial knowledge from various knowledge bases."""

    def __init__(self, knowledge_base_path: str = "Finance Knowledge"):
        self.knowledge_path = Path(knowledge_base_path)
        self.xbrl_terms = {}
        self.financial_formulas = {}
        self.benchmarks = {}
        self.account_synonyms = {}
        self._load_knowledge_bases()

    def _load_knowledge_bases(self):
        """Load all knowledge base files."""
        try:
            self._load_xbrl_terminology()
            self._load_financial_formulas()
            self._load_benchmarks()
            self._build_synonym_mapping()
            logger.info("Knowledge bases loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load knowledge bases: {e}")

    def _load_xbrl_terminology(self):
        """Load XBRL standardized financial terminology."""
        try:
            file_path = self.knowledge_path / "xbrl-terminology.xlsx"
            df = pd.read_excel(file_path)

            for _, row in df.iterrows():
                term = str(row["Term"]).strip().lower()
                explanation = str(row["Explanation"]).strip()

                self.xbrl_terms[term] = {
                    "definition": explanation,
                    "category": self._categorize_term(term),
                    "synonyms": self._extract_synonyms_from_explanation(explanation),
                }

            logger.info(f"Loaded {len(self.xbrl_terms)} XBRL terms")
        except Exception as e:
            logger.error(f"Failed to load XBRL terminology: {e}")

    def _load_financial_formulas(self):
        """Load financial formulas with explanations."""
        try:
            file_path = (
                self.knowledge_path
                / "formulas_with_explanations_with_questions_with_gt.xlsx"
            )
            df = pd.read_excel(file_path)

            for _, row in df.iterrows():
                formula_name = str(row["Formula Name"]).strip()
                formula = str(row["Formula"]).strip()
                explanation = str(row["Explanation"]).strip()

                self.financial_formulas[formula_name] = {
                    "formula": formula,
                    "explanation": explanation,
                    "components": self._extract_formula_components(formula),
                    "category": self._categorize_formula(formula_name),
                }

            logger.info(f"Loaded {len(self.financial_formulas)} financial formulas")
        except Exception as e:
            logger.error(f"Failed to load financial formulas: {e}")

    def _load_benchmarks(self):
        """Load financial benchmarking data."""
        try:
            file_path = self.knowledge_path / "financebench.xlsx"
            df = pd.read_excel(file_path)

            # Group by question type and extract common patterns
            for _, row in df.iterrows():
                q_type = str(row["question_type"]).strip()
                question = str(row["question"]).strip()
                answer = str(row["answer"]).strip()

                if q_type not in self.benchmarks:
                    self.benchmarks[q_type] = []

                self.benchmarks[q_type].append(
                    {
                        "question": question,
                        "answer": answer,
                        "patterns": self._extract_financial_patterns(question, answer),
                    }
                )

            logger.info(
                f"Loaded benchmark data for {len(self.benchmarks)} question types"
            )
        except Exception as e:
            logger.error(f"Failed to load benchmark data: {e}")

    def _categorize_term(self, term: str) -> str:
        """Categorize XBRL terms into financial statement categories."""
        if any(keyword in term.lower() for keyword in ["asset", "liability", "equity"]):
            return "balance_sheet"
        elif any(
            keyword in term.lower()
            for keyword in ["revenue", "expense", "income", "profit"]
        ):
            return "income_statement"
        elif any(keyword in term.lower() for keyword in ["cash", "flow"]):
            return "cash_flow"
        else:
            return "general"

    def _categorize_formula(self, formula_name: str) -> str:
        """Categorize formulas by type."""
        if any(
            keyword in formula_name.lower() for keyword in ["ratio", "margin", "return"]
        ):
            return "ratio"
        elif any(
            keyword in formula_name.lower() for keyword in ["npv", "irr", "pv", "fv"]
        ):
            return "valuation"
        elif any(keyword in formula_name.lower() for keyword in ["debt", "equity"]):
            return "leverage"
        else:
            return "general"

    def _extract_synonyms_from_explanation(self, explanation: str) -> List[str]:
        """Extract potential synonyms from explanation text."""
        synonyms = []
        # Look for common patterns like "also known as", "refers to", etc.
        patterns = [
            r"(?:also known as|refers to|sometimes called)\s+([^,.]+)",
            r"([^ ]+)\s+(?:means|represents|indicates)",
            r"term\s+([^ ]+)\s+(?:is|represents)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            synonyms.extend(matches)

        return [s.strip().lower() for s in synonyms if len(s.strip()) > 2]

    def _extract_formula_components(self, formula: str) -> List[str]:
        """Extract variable names from formula."""
        # Look for variable patterns like R_t, PV, FV, etc.
        components = re.findall(r"\b[A-Za-z][A-Za-z0-9_]*\b", formula)
        return list(set(components))

    def _extract_financial_patterns(self, question: str, answer: str) -> Dict:
        """Extract financial patterns from Q&A pairs."""
        patterns = {
            "amount_patterns": [],
            "ratio_patterns": [],
            "percentage_patterns": [],
            "term_associations": {},
        }

        # Extract monetary amounts
        amount_pattern = r"\$?\s*[\d,]+\.?\d*\s*(?:million|billion|thousand)?"
        patterns["amount_patterns"] = re.findall(amount_pattern, answer, re.IGNORECASE)

        # Extract percentages
        percentage_pattern = r"\d+\.?\d*%?"
        patterns["percentage_patterns"] = re.findall(
            percentage_pattern, answer, re.IGNORECASE
        )

        # Extract financial terms from question
        financial_terms = re.findall(
            r"\b(?:revenue|income|profit|loss|expense|asset|liability|equity|cash|debt|capital|margin|ratio)\b",
            question,
            re.IGNORECASE,
        )
        patterns["term_associations"] = {
            term.lower(): answer for term in financial_terms
        }

        return patterns

    def _build_synonym_mapping(self):
        """Build comprehensive synonym mapping from all sources."""
        # Base XBRL terms
        for term, info in self.xbrl_terms.items():
            self.account_synonyms[term] = term
            for synonym in info.get("synonyms", []):
                self.account_synonyms[synonym] = term

        # Add common financial term variations
        common_mappings = {
            "revenue": ["total revenue", "sales", "turnover", "gross revenue"],
            "net income": ["net profit", "net earnings", "bottom line"],
            "assets": ["total assets", "gross assets"],
            "liabilities": ["total liabilities"],
            "equity": ["shareholders equity", "owner equity", "net worth"],
            "cash": ["cash and equivalents", "cash on hand"],
            "expenses": ["total expenses", "operating expenses"],
            "operating income": ["ebit", "operating profit"],
            "gross profit": ["gross margin", "gross earnings"],
        }

        for canonical, variations in common_mappings.items():
            for variation in variations:
                self.account_synonyms[variation.lower()] = canonical.lower()

        logger.info(f"Built synonym mapping with {len(self.account_synonyms)} terms")

    def get_term_definition(self, term: str) -> Optional[str]:
        """Get definition for a financial term."""
        term_normalized = term.lower().strip()
        return self.xbrl_terms.get(term_normalized, {}).get("definition")

    def get_synonyms(self, term: str) -> List[str]:
        """Get all synonyms for a term."""
        synonyms = []
        term_normalized = term.lower().strip()

        for canonical_term, info in self.xbrl_terms.items():
            if canonical_term == term_normalized:
                synonyms.extend(info.get("synonyms", []))
            elif term_normalized in info.get("synonyms", []):
                synonyms.append(canonical_term)
                synonyms.extend(
                    [s for s in info.get("synonyms", []) if s != term_normalized]
                )

        return list(set(synonyms))

    def normalize_account_name(self, account_name: str) -> str:
        """Normalize account name to standard terminology."""
        normalized = account_name.lower().strip()

        # Direct synonym mapping
        if normalized in self.account_synonyms:
            return self.account_synonyms[normalized]

        # Partial matching for longer phrases
        for term, canonical in self.account_synonyms.items():
            if term in normalized or normalized in term:
                return canonical

        return normalized

    def get_formulas_for_category(self, category: str) -> Dict:
        """Get all formulas for a specific category."""
        return {
            name: info
            for name, info in self.financial_formulas.items()
            if info.get("category") == category
        }

    def validate_formula_consistency(self, data: Dict[str, float]) -> Dict[str, bool]:
        """Validate data against known financial formulas and relationships."""
        validation_results = {}

        for formula_name, info in self.financial_formulas.items():
            try:
                components = info["components"]
                if self._has_required_data(components, data):
                    validation_results[formula_name] = self._check_formula_validity(
                        info["formula"], components, data
                    )
            except Exception as e:
                logger.warning(f"Could not validate {formula_name}: {e}")
                validation_results[formula_name] = False

        return validation_results

    def _has_required_data(self, components: List[str], data: Dict[str, float]) -> bool:
        """Check if required components exist in data."""
        normalized_components = [c.lower().replace("_", " ") for c in components]
        normalized_data_keys = [k.lower() for k in data.keys()]

        has_all = all(
            comp in " ".join(normalized_data_keys) for comp in normalized_components
        )
        logger.debug(f"Components check: {normalized_components} -> {has_all}")
        return has_all

    def _check_formula_validity(
        self, formula: str, components: List[str], data: Dict[str, float]
    ) -> bool:
        """Check if data satisfies formula constraints."""
        # This is a simplified validity check
        # In practice, you'd implement actual formula evaluation

        # Check if all required components have reasonable values
        for component in components:
            found = False
            for account_name, value in data.items():
                if component.lower() in account_name.lower():
                    if value < 0:  # Basic sanity check
                        return False
                    found = True
                    break
            if not found:
                return False

        return True

    def get_benchmark_context(self, metric_type: str) -> List[Dict]:
        """Get benchmark context for a specific metric type."""
        return self.benchmarks.get(metric_type, [])

    def suggest_mapping_for_label(
        self, label: str, data_accounts: List[str]
    ) -> List[str]:
        """Suggest mapping for a single label based on knowledge base."""
        normalized_label = self.normalize_account_name(label)
        suggestions = []

        # Direct synonym matches
        for account in data_accounts:
            normalized_account = self.normalize_account_name(account)
            if normalized_label == normalized_account:
                suggestions.append(account)
                continue

            # Partial matches for longer phrases
            if any(
                word in normalized_account.split() for word in normalized_label.split()
            ):
                suggestions.append(account)

        # XBRL term matches
        for term, info in self.xbrl_terms.items():
            if term in normalized_label.lower():
                for account in data_accounts:
                    if term in account.lower() and account not in suggestions:
                        suggestions.append(account)

        # Remove duplicates and limit to top 3 suggestions
        return list(dict.fromkeys(suggestions))[:3]

    def suggest_mappings(
        self, template_labels: List[str], data_accounts: List[str]
    ) -> Dict[str, List[str]]:
        """Suggest mappings based on knowledge base (without LLM)."""
        suggestions = {}

        for label in template_labels:
            suggestions[label] = self.suggest_mapping_for_label(label, data_accounts)

        return suggestions
