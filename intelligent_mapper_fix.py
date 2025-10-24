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

