import json
import requests
from typing import Dict, List, Tuple
from utils.logger import Logger
from config.settings import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    TEXT_MODEL,
    API_TIMEOUT_SECONDS,
    ERRORS,
)

logger = Logger(__name__)


class AIProcessor:
    def __init__(self):
        if not OPENROUTER_API_KEY:
            logger.error("OpenRouter API key not configured")
            raise ValueError(ERRORS["api_key_missing"])

        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.model = TEXT_MODEL

    def create_semantic_mapping(
        self, template_labels: List[str], data_accounts: Dict[str, float]
    ) -> Dict[str, str]:
        """Use LLM to map template labels to data accounts."""
        try:
            prompt = self._build_mapping_prompt(template_labels, data_accounts)

            response = self._call_api(prompt)

            mapping = self._parse_mapping_response(response)
            logger.info(f"Created semantic mapping for {len(mapping)} fields")
            return mapping

        except Exception as e:
            logger.error(f"Semantic mapping failed: {str(e)}")
            raise

    def _build_mapping_prompt(
        self, template_labels: List[str], data_accounts: Dict[str, float]
    ) -> str:
        """Build LLM prompt for semantic mapping."""

        accounts_list = "\n".join([f"- {account}" for account in data_accounts.keys()])
        labels_list = "\n".join([f"- {label}" for label in template_labels])

        prompt = f"""You are a financial document expert. Match the following template labels with the best corresponding data account.

Template Labels (from PDF):
{labels_list}

Available Data Accounts (from Excel/PDF):
{accounts_list}

Task: Create a JSON mapping where each template label maps to the best matching account name.
Handle terminology variations (e.g., "Revenue" → "Total Revenues", "Net Earnings" → "Net Income").
If no good match exists, return null for that label.

Return ONLY valid JSON in this format:
{{"template_label_1": "matching_account_1", "template_label_2": "matching_account_2"}}

Do not include any other text."""

        return prompt

    def _call_api(self, prompt: str) -> str:
        """Call OpenRouter API with the prompt."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=API_TIMEOUT_SECONDS,
            )

            if response.status_code != 200:
                logger.error(f"API error {response.status_code}: {response.text}")
                raise Exception(ERRORS["api_failure"])

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.Timeout:
            timeout_msg = (
                f"API timeout after {API_TIMEOUT_SECONDS} seconds"
                if API_TIMEOUT_SECONDS
                else "API request timed out"
            )
            logger.error(timeout_msg)
            raise Exception(timeout_msg)
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            raise

    def _parse_mapping_response(self, response: str) -> Dict[str, str]:
        """Parse LLM response into mapping dictionary."""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_str = response[json_start:json_end]
            mapping = json.loads(json_str)

            return {k: v for k, v in mapping.items() if v is not None}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {str(e)}")
            raise
