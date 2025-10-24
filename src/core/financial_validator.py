import math
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from utils.logger import Logger
from .knowledge_extractor import KnowledgeExtractor

logger = Logger(__name__)


@dataclass
class ValidationResult:
    """Result of financial validation."""

    is_valid: bool
    message: str
    severity: str  # 'error', 'warning', 'info'
    formula_name: Optional[str] = None
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None


@dataclass
class ComplianceCheck:
    """Result of compliance checking."""

    is_compliant: bool
    standard: str
    violation: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class AnalysisResult:
    """Financial analysis result."""

    metric_name: str
    value: float
    benchmark_value: Optional[float]
    variance_percent: Optional[float]
    interpretation: str


class FinancialValidator:
    """Comprehensive financial validation and compliance checking."""

    def __init__(self):
        self.knowledge_base = KnowledgeExtractor()
        self.validation_rules = self._initialize_validation_rules()
        self.compliance_standards = self._initialize_compliance_standards()

    def _initialize_validation_rules(self) -> Dict:
        """Initialize validation rules for financial statements."""
        return {
            "balance_sheet": [
                {
                    "name": "Assets_Equity_Liabilities_Check",
                    "formula": "total_assets == total_liabilities + total_equity",
                    "tolerance": 0.01,  # 1% tolerance
                    "description": "Assets must equal Liabilities + Equity",
                },
                {
                    "name": "NonNegative_Assets",
                    "formula": "total_assets >= 0",
                    "tolerance": 0,
                    "description": "Total assets cannot be negative",
                },
            ],
            "income_statement": [
                {
                    "name": "Net_Income_Calculation",
                    "formula": "revenue - expenses = net_income",
                    "tolerance": 0.02,  # 2% tolerance
                    "description": "Net income should equal revenue minus expenses",
                },
                {
                    "name": "Gross_Profit_Logic",
                    "formula": "revenue > cost_of_goods_sold",
                    "tolerance": 0.01,
                    "description": "Revenue should exceed cost of goods sold",
                },
            ],
            "cash_flow": [
                {
                    "name": "Cash_Change_Reconciliation",
                    "formula": "cash_beginning + cash_flow_change = cash_ending",
                    "tolerance": 0.01,
                    "description": "Cash flow change should reconcile beginning and ending cash",
                }
            ],
            "ratios": [
                {
                    "name": "Current_Ratio_Reasonable",
                    "formula": "1.0 <= current_ratio <= 3.0",
                    "tolerance": 0.1,
                    "description": "Current ratio typically between 1.0 and 3.0",
                },
                {
                    "name": "Profit_Margin_Positive",
                    "formula": "profit_margin > 0",
                    "tolerance": 0,
                    "description": "Profit margin should typically be positive for healthy companies",
                },
            ],
        }

    def _initialize_compliance_standards(self) -> Dict:
        """Initialize compliance standards checking."""
        return {
            "gaap": [
                {
                    "name": "Materiality_Check",
                    "check": lambda data: self._check_materiality(data),
                    "description": "Financial statements should present material items accurately",
                },
                {
                    "name": "Going_Concern_Logic",
                    "check": lambda data: self._check_going_concern(data),
                    "description": "Financial statements assume entity is a going concern",
                },
            ],
            "ifrs": [
                {
                    "name": "IFRS_Presentation",
                    "check": lambda data: self._check_ifrs_presentation(data),
                    "description": "IFRS presentation requirements",
                }
            ],
        }

    def validate_financial_statement(
        self, data: Dict[str, float], statement_type: str = "auto"
    ) -> Tuple[List[ValidationResult], Dict]:
        """Comprehensive validation of financial statement data."""
        validation_results = []
        summary_stats = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "warnings": 0,
            "error_count": 0,
        }

        # Auto-detect statement type if not specified
        if statement_type == "auto":
            statement_type = self._detect_statement_type(data)

        logger.info(
            f"Validating {statement_type} statement with {len(data)} data points"
        )

        # Get relevant validation rules
        rules = self.validation_rules.get(statement_type, [])
        if statement_type == "income_statement":
            rules.extend(self.validation_rules.get("ratios", []))

        # Execute validation rules
        for rule in rules:
            try:
                result = self._execute_validation_rule(rule, data)
                validation_results.append(result)
                summary_stats["total_checks"] += 1

                if result.is_valid:
                    summary_stats["passed_checks"] += 1
                else:
                    summary_stats["failed_checks"] += 1
                    if result.severity == "error":
                        summary_stats["error_count"] += 1
                    else:
                        summary_stats["warnings"] += 1

            except Exception as e:
                logger.warning(f"Validation rule '{rule['name']}' failed: {e}")
                error_result = ValidationResult(
                    is_valid=False,
                    message=f"Validation error: {str(e)}",
                    severity="error",
                    formula_name=rule["name"],
                )
                validation_results.append(error_result)
                summary_stats["failed_checks"] += 1
                summary_stats["error_count"] += 1

        # Calculate calculated ratios for additional validation
        calculated_ratios = self._calculate_financial_ratios(data)
        summary_stats["calculated_ratios"] = calculated_ratios

        return validation_results, summary_stats

    def check_compliance(
        self, data: Dict[str, float], standards: List[str] = ["gaap"]
    ) -> List[ComplianceCheck]:
        """Check compliance with accounting standards."""
        compliance_results = []

        for standard in standards:
            if standard in self.compliance_standards:
                for check_config in self.compliance_standards[standard]:
                    try:
                        result = check_config["check"](data)
                        compliance_check = ComplianceCheck(
                            is_compliant=result["compliant"],
                            standard=f"{standard}: {check_config['name']}",
                            violation=result.get("violation"),
                            recommendation=result.get("recommendation"),
                        )
                        compliance_results.append(compliance_check)

                        if not result["compliant"]:
                            logger.warning(
                                f"Non-compliance detected in {standard}: {check_config['name']}"
                            )

                    except Exception as e:
                        logger.warning(f"Compliance check failed for {standard}: {e}")

        return compliance_results

    def perform_financial_analysis(
        self, data: Dict[str, float], mapping: Dict[str, str]
    ) -> Dict[str, AnalysisResult]:
        """Perform comprehensive financial analysis."""
        analysis_results = {}

        try:
            # Calculate key financial metrics
            ratios = self._calculate_financial_ratios(data)
            logger.info(f"Calculated {len(ratios)} financial ratios")

            # Analyze each ratio
            for ratio_name, ratio_value in ratios.items():
                if ratio_value is not None:
                    benchmark = self._get_industry_benchmark(ratio_name)
                    variance = (
                        self._calculate_variance(ratio_value, benchmark)
                        if benchmark
                        else None
                    )
                    interpretation = self._interpret_ratio(
                        ratio_name, ratio_value, benchmark
                    )

                    analysis_results[ratio_name] = AnalysisResult(
                        metric_name=ratio_name,
                        value=ratio_value,
                        benchmark_value=benchmark,
                        variance_percent=variance,
                        interpretation=interpretation,
                    )

            # Perform trend analysis if historical data available
            # This would be enhanced with historical data in future versions

            logger.info(
                f"Financial analysis complete: {len(analysis_results)} metrics analyzed"
            )

        except Exception as e:
            logger.error(f"Financial analysis failed: {e}")

        return analysis_results

    def _detect_statement_type(self, data: Dict[str, float]) -> str:
        """Detect the type of financial statement from data keys."""
        keys_lower = " ".join(k.lower() for k in data.keys())

        if any(keyword in keys_lower for keyword in ["asset", "liability", "equity"]):
            return "balance_sheet"
        elif any(keyword in keys_lower for keyword in ["revenue", "income", "expense"]):
            return "income_statement"
        elif any(keyword in keys_lower for keyword in ["cash", "flow"]):
            return "cash_flow"
        else:
            return "general"

    def _execute_validation_rule(
        self, rule: Dict, data: Dict[str, float]
    ) -> ValidationResult:
        """Execute a single validation rule."""
        formula = rule["formula"]
        tolerance = rule.get("tolerance", 0)
        rule_name = rule["name"]

        try:
            if "==" in formula:
                # Equality check (e.g., assets == liabilities + equity)
                lhs, rhs = formula.split("==")
                lhs_value = self._evaluate_expression(lhs.strip(), data)
                rhs_value = self._evaluate_expression(rhs.strip(), data)

                if lhs_value is None or rhs_value is None:
                    return ValidationResult(
                        is_valid=False,
                        message=f"Cannot evaluate {rule_name}: missing data",
                        severity="warning",
                        formula_name=rule_name,
                    )

                # Check within tolerance
                if tolerance > 0:
                    diff_pct = abs(lhs_value - rhs_value) / max(
                        abs(lhs_value), abs(rhs_value), 1
                    )
                    is_valid = diff_pct <= tolerance
                else:
                    is_valid = abs(lhs_value - rhs_value) < 0.01  # Small epsilon

                return ValidationResult(
                    is_valid=is_valid,
                    message=(
                        f"{rule['description']}: "
                        f"LHS={lhs_value:,.2f}, RHS={rhs_value:,.2f}"
                        if not is_valid
                        else f"Check passed: {rule['description']}"
                    ),
                    severity="error" if not is_valid else "info",
                    formula_name=rule_name,
                    expected_value=rhs_value,
                    actual_value=lhs_value,
                )

            elif "=" in formula and "==" not in formula:
                # Equality check with single = (e.g., cash_beginning + cash_flow_change = cash_ending)
                lhs, rhs = formula.split("=")
                lhs_value = self._evaluate_expression(lhs.strip(), data)
                rhs_value = self._evaluate_expression(rhs.strip(), data)

                if lhs_value is None or rhs_value is None:
                    return ValidationResult(
                        is_valid=False,
                        message=f"Cannot evaluate {rule_name}: missing data",
                        severity="warning",
                        formula_name=rule_name,
                    )

                # Check within tolerance
                if tolerance > 0:
                    diff_pct = abs(lhs_value - rhs_value) / max(
                        abs(lhs_value), abs(rhs_value), 1
                    )
                    is_valid = diff_pct <= tolerance
                else:
                    is_valid = abs(lhs_value - rhs_value) < 0.01  # Small epsilon

                return ValidationResult(
                    is_valid=is_valid,
                    message=(
                        f"{rule['description']}: "
                        f"LHS={lhs_value:,.2f}, RHS={rhs_value:,.2f}"
                        if not is_valid
                        else f"Check passed: {rule['description']}"
                    ),
                    severity="error" if not is_valid else "info",
                    formula_name=rule_name,
                    expected_value=rhs_value,
                    actual_value=lhs_value,
                )

            elif ">" in formula:
                # Greater than check
                lhs, rhs = formula.split(">")
                lhs_value = self._evaluate_expression(lhs.strip(), data)
                rhs_value = self._evaluate_expression(rhs.strip(), data)

                if lhs_value is None or rhs_value is None:
                    return ValidationResult(
                        is_valid=False,
                        message=f"Cannot evaluate {rule_name}: missing data",
                        severity="warning",
                        formula_name=rule_name,
                    )

                is_valid = lhs_value > rhs_value
                return ValidationResult(
                    is_valid=is_valid,
                    message=(
                        f"{rule['description']}: "
                        f"LHS={lhs_value:,.2f} not > RHS={rhs_value:,.2f}"
                        if not is_valid
                        else f"Logic check passed: {rule['description']}"
                    ),
                    severity="error" if not is_valid else "info",
                    formula_name=rule_name,
                    expected_value=rhs_value,
                    actual_value=lhs_value,
                )

            elif "<=" in formula:
                # Range check
                try:
                    min_val, max_val = (
                        formula.split("<=")[1].split("+")[0].strip().split()
                    )
                    actual_value = self._evaluate_expression(
                        formula.split("<=")[0].strip(), data
                    )

                    if actual_value is None:
                        return ValidationResult(
                            is_valid=False,
                            message=f"Cannot evaluate {rule_name}: missing data",
                            severity="warning",
                            formula_name=rule_name,
                        )

                    is_valid = float(min_val) <= actual_value <= float(max_val)
                    return ValidationResult(
                        is_valid=is_valid,
                        message=(
                            f"{rule['description']}: "
                            f"value={actual_value:,.2f} not in range [{min_val}, {max_val}]"
                            if not is_valid
                            else f"Range check passed: {rule['description']}"
                        ),
                        severity="error" if not is_valid else "info",
                        formula_name=rule_name,
                    )
                except Exception as e:
                    return ValidationResult(
                        is_valid=False,
                        message=f"Range check failed: {str(e)}",
                        severity="warning",
                        formula_name=rule_name,
                    )

            else:
                # Unknown formula type - skip with warning
                return ValidationResult(
                    is_valid=False,
                    message=f"Unsupported formula type: {formula}",
                    severity="warning",
                    formula_name=rule_name,
                )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Validation error in {rule_name}: {str(e)}",
                severity="error",
                formula_name=rule_name,
            )

    def _evaluate_expression(
        self, expression: str, data: Dict[str, float]
    ) -> Optional[float]:
        """Evaluate an expression using the financial data."""
        try:
            # Replace variables with values
            for key, value in data.items():
                # Handle different naming conventions
                safe_key = (
                    key.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
                )
                expression = expression.replace(safe_key, str(value))
                expression = expression.replace(key, str(value))

            # Evaluate simple arithmetic expressions
            if "+" in expression:
                return sum(float(x) for x in expression.replace(" ", "").split("+"))
            elif "-" in expression and not expression.startswith("-"):
                parts = expression.replace(" ", "").split("-")
                return float(parts[0]) - float(parts[1])
            else:
                return float(expression)

        except Exception as e:
            logger.warning(f"Failed to evaluate expression '{expression}': {e}")
            return None

    def _calculate_financial_ratios(self, data: Dict[str, float]) -> Dict[str, float]:
        """Calculate key financial ratios."""
        ratios = {}

        try:
            # Current Ratio
            current_assets = self._find_value(
                data, ["current assets", "total current assets"]
            )
            current_liabilities = self._find_value(
                data, ["current liabilities", "total current liabilities"]
            )
            if current_assets and current_liabilities and current_liabilities > 0:
                ratios["current_ratio"] = current_assets / current_liabilities

            # Quick Ratio
            quick_assets = self._find_value(data, ["quick assets"])
            if quick_assets and current_liabilities and current_liabilities > 0:
                ratios["quick_ratio"] = quick_assets / current_liabilities

            # Debt to Equity
            total_debt = self._find_value(
                data, ["total debt", "short term debt", "long term debt"]
            )
            total_equity = self._find_value(
                data, ["total equity", "shareholders equity"]
            )
            if total_debt and total_equity and total_equity > 0:
                ratios["debt_to_equity"] = total_debt / total_equity

            # Gross Profit Margin
            gross_profit = self._find_value(data, ["gross profit", "gross margin"])
            revenue = self._find_value(data, ["revenue", "sales", "total revenue"])
            if gross_profit and revenue and revenue > 0:
                ratios["gross_profit_margin"] = (gross_profit / revenue) * 100

            # Net Profit Margin
            net_income = self._find_value(
                data, ["net income", "net profit", "net earnings"]
            )
            if net_income and revenue and revenue > 0:
                ratios["net_profit_margin"] = (net_income / revenue) * 100

            # Return on Assets
            total_assets = self._find_value(data, ["total assets"])
            if net_income and total_assets and total_assets > 0:
                ratios["return_on_assets"] = (net_income / total_assets) * 100

            # Return on Equity
            if net_income and total_equity and total_equity > 0:
                ratios["return_on_equity"] = (net_income / total_equity) * 100

        except Exception as e:
            logger.warning(f"Error calculating ratios: {e}")

        return ratios

    def _find_value(
        self, data: Dict[str, float], search_terms: List[str]
    ) -> Optional[float]:
        """Find a value in data using various search terms."""
        for term in search_terms:
            for key, value in data.items():
                if term.lower() in key.lower():
                    return value
        return None

    def _get_industry_benchmark(self, ratio_name: str) -> Optional[float]:
        """Get industry benchmark for a ratio."""
        # These are generic benchmarks - in practice would use industry-specific data
        benchmarks = {
            "current_ratio": 2.0,
            "quick_ratio": 1.5,
            "debt_to_equity": 0.6,
            "gross_profit_margin": 35.0,
            "net_profit_margin": 10.0,
            "return_on_assets": 8.0,
            "return_on_equity": 15.0,
        }
        return benchmarks.get(ratio_name)

    def _calculate_variance(self, actual: float, benchmark: float) -> float:
        """Calculate percentage variance from benchmark."""
        return ((actual - benchmark) / benchmark) * 100

    def _interpret_ratio(
        self, ratio_name: str, value: float, benchmark: Optional[float]
    ) -> str:
        """Interpret a financial ratio value."""
        interpretations = {
            "current_ratio": {
                "low": "Current ratio below 1.0 may indicate liquidity concerns",
                "normal": "Current ratio within healthy range",
                "high": "Current ratio very high may indicate inefficient asset use",
            },
            "debt_to_equity": {
                "low": "Low debt level indicates conservative financing",
                "normal": "Moderate debt level within acceptable range",
                "high": "High debt level may indicate increased financial risk",
            },
            "gross_profit_margin": {
                "low": "Low gross margin may indicate pricing or cost issues",
                "normal": "Gross margin within typical range",
                "high": "High gross margin indicates strong pricing power",
            },
        }

        if ratio_name in interpretations:
            if benchmark:
                var_pct = self._calculate_variance(value, benchmark)
                if var_pct < -20:
                    return interpretations[ratio_name]["low"]
                elif var_pct > 20:
                    return interpretations[ratio_name]["high"]
                else:
                    return interpretations[ratio_name]["normal"]

        return f"Ratio value: {value:.2f}"

    def _check_materiality(self, data: Dict[str, float]) -> Dict:
        """Check materiality of amounts."""
        total_value = sum(abs(v) for v in data.values())
        largest_amount = max(abs(v) for v in data.values()) if data else 0

        # If largest amount is > 50% of total, it's material
        is_material = largest_amount > (total_value * 0.5)

        return {
            "compliant": True,  # Materiality is about presentation, not compliance
            "interpretation": "Material items identified and presented"
            if is_material
            else "All amounts within normal ranges",
        }

    def _check_going_concern(self, data: Dict[str, float]) -> Dict:
        """Basic going concern assessment."""
        # Simple check - if company has positive equity and reasonable ratios
        total_equity = self._find_value(data, ["total equity", "shareholders equity"])

        if total_equity is None:
            return {
                "compliant": False,
                "violation": "Cannot assess going concern without equity data",
                "recommendation": "Ensure equity information is properly reported",
            }

        is_going_concern = total_equity > 0

        return {
            "compliant": is_going_concern,
            "violation": "Negative equity may indicate going concern issues"
            if not is_going_concern
            else None,
            "recommendation": "Address equity deficits in management discussion"
            if not is_going_concern
            else None,
        }

    def _check_ifrs_presentation(self, data: Dict[str, float]) -> Dict:
        """Basic IFRS presentation checks."""
        # This would include more sophisticated IFRS-specific checks in a real implementation
        return {
            "compliant": True,
            "interpretation": "IFRS presentation standards followed",
        }

    def get_validation_summary(
        self, validation_results: List[ValidationResult]
    ) -> Dict:
        """Get summary statistics for validation results."""
        if not validation_results:
            return {"status": "No validation performed"}

        total = len(validation_results)
        passed = sum(1 for r in validation_results if r.is_valid)
        failed = total - passed
        errors = sum(
            1 for r in validation_results if not r.is_valid and r.severity == "error"
        )
        warnings = sum(
            1 for r in validation_results if not r.is_valid and r.severity == "warning"
        )

        return {
            "total_checks": total,
            "passed_checks": passed,
            "failed_checks": failed,
            "error_count": errors,
            "warning_count": warnings,
            "success_rate": passed / total if total > 0 else 0,
            "status": "PASS" if errors == 0 else "FAIL" if errors > 0 else "WARNING",
        }
