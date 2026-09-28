"""
PII Detection and Redaction Service using Microsoft Presidio.

Multiple representation levels:
  - internal_representation: Full data (database layer)
  - llm_representation: Masked for LLM (agent can identify but not see full details)
  - user_visible_representation: Redacted for API responses
  - log_representation: Heavily redacted for security logs

Sensitive fields handled:
  - SSN, Credit Card, Account Number, Phone, Email, DOB, Routing Number
"""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PIIRedactionService:
    """Manages PII visibility across system layers using Presidio."""

    def __init__(self):
        """Initialize Presidio analyzer and anonymizer engines."""
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def analyze(self, text: str) -> list:
        """Detect PII entities in text using Presidio."""
        if not text:
            return []
        try:
            results = self.analyzer.analyze(
                text=text,
                language="en",
                score_threshold=0.5,
            )
            return results
        except Exception as e:
            logger.warning(f"PII analysis error: {e}")
            return []

    def has_sensitive_data(self, text: str) -> bool:
        """Check if text contains detected sensitive data."""
        if not text:
            return False
        results = self.analyze(text)
        return len(results) > 0

    def anonymize_for_logs(self, text: str) -> str:
        """Anonymize text for safe logging."""
        if not text:
            return text
        try:
            results = self.analyzer.analyze(text=text, language="en")
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators={
                    "DEFAULT": OperatorConfig("mask", {"type": "mask", "masking_char": "*"}),
                },
            )
            return anonymized.text
        except Exception as e:
            logger.error(f"Anonymization error: {e}")
            return "[REDACTED]"

    # ========================
    # REPRESENTATION LAYERS
    # ========================

    @staticmethod
    def internal_representation(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal representation: Full unrestricted data for DB/internal services.
        """
        return data.copy()

    def llm_representation(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM-safe representation: Masked but identifiable for agent.

        Agent can:
          - Identify the account (via masked account number)
          - See balance and status (needed for queries)
          - NOT see full sensitive details in plaintext

        Presidio anonymizes sensitive fields automatically.
        """
        account_number = str(account_data.get("account_number", ""))
        account_number_masked = self.anonymize_for_logs(account_number)

        return {
            "account_id": account_data.get("id"),
            "account_number": account_number_masked,
            "balance": float(account_data.get("balance", 0)),
            "status": account_data.get("status"),
            "account_type": account_data.get("account_type"),
        }

    def user_visible_representation(
        self, data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """
        User-visible representation: Redacted for API responses.
        Uses Presidio to anonymize sensitive fields.
        """
        if data_type == "account":
            account_number = str(data.get("account_number", ""))
            account_number_masked = self.anonymize_for_logs(account_number)

            return {
                "account_id": data.get("id"),
                "account_number": account_number_masked,
                "balance": float(data.get("balance", 0)),
                "status": data.get("status"),
                "account_type": data.get("account_type"),
            }

        elif data_type == "user":
            email = str(data.get("email", ""))
            email_masked = self.anonymize_for_logs(email)

            return {
                "id": data.get("id"),
                "email": email_masked,
                "name": data.get("name"),
                "role": data.get("role"),
            }

        elif data_type == "transaction":
            from_account = str(data.get("from_account", ""))
            to_account = str(data.get("to_account", ""))
            from_masked = self.anonymize_for_logs(from_account)
            to_masked = self.anonymize_for_logs(to_account)

            return {
                "id": data.get("id"),
                "amount": float(data.get("amount", 0)),
                "type": data.get("type"),
                "status": data.get("status"),
                "timestamp": data.get("timestamp"),
                "from_account": from_masked,
                "to_account": to_masked,
            }

        return data

    def log_representation(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """
        Log-safe representation: Heavily redacted, only identifiers.
        All sensitive data is anonymized by Presidio.
        """
        if data_type == "account":
            account_number = str(data.get("account_number", ""))
            account_number_masked = self.anonymize_for_logs(account_number)

            return {
                "account_id": data.get("id"),
                "account_number": account_number_masked,
                "balance": "[REDACTED]",
                "status": data.get("status"),
            }

        elif data_type == "user":
            email = str(data.get("email", ""))
            email_masked = self.anonymize_for_logs(email)

            return {
                "user_id": data.get("id"),
                "email": email_masked,
                "role": data.get("role"),
            }

        elif data_type == "transaction":
            return {
                "transaction_id": data.get("id"),
                "amount": "[REDACTED]",
                "type": data.get("type"),
                "status": data.get("status"),
            }

        return data

    def sanitize_agent_message(self, message: str) -> str:
        """
        Redact PII from agent-generated messages before sending to user.
        Uses Presidio for comprehensive detection and anonymization.
        """
        if not message:
            return message

        return self.anonymize_for_logs(message)


# Global instance
_pii_service = None


def get_pii_service() -> PIIRedactionService:
    """Get or create singleton PII service."""
    global _pii_service
    if _pii_service is None:
        _pii_service = PIIRedactionService()
    return _pii_service
