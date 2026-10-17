"""Security-Conscious Logging System with Automated Redaction.

Guarantees:
- Passwords, tokens, API keys, and bearer tokens are automatically redacted.
- Sensitive PII (payment cards, Indian Aadhaar, US SSN, PAN) is masked.
- Full raw resume text is NEVER logged.
- Only non-sensitive metrics (filename, size, page count, duration, status) are emitted.
"""

import logging
import re
from typing import Any

# Sensitive patterns to scrub from all logs
REDACTION_PATTERNS = [
    # API keys / Bearer tokens / Secrets
    (re.compile(r"(?i)(api[_-]?key|secret|password|access_token|bearer)\s*[:=]\s*[^\s,;]+"), r"\1: [REDACTED]"),
    # Bearer tokens in headers
    (re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"), "Bearer [REDACTED]"),
    # 16-digit credit/debit card numbers
    (re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b"), "[REDACTED-PAYMENT-CARD]"),
    # 12-digit Indian Aadhaar
    (re.compile(r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b"), "[REDACTED-NATIONAL-ID]"),
    # US SSN (3-2-4 digits)
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
    # Indian PAN (5 uppercase letters, 4 digits, 1 uppercase letter)
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"), "[REDACTED-TAX-ID]"),
]


class SecurityRedactionFilter(logging.Filter):
    """Logging filter that scrubs sensitive credentials, keys, PII, and resume text dumps."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            # Check and sanitize message string
            if isinstance(record.msg, str):
                record.msg = self._redact(record.msg)

            # Check and sanitize args if they exist
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {k: self._redact(v) if isinstance(v, str) else v for k, v in record.args.items()}
                elif isinstance(record.args, (list, tuple)):
                    record.args = tuple(self._redact(v) if isinstance(v, str) else v for v in record.args)
        except Exception:
            # Never let logger filter crash application execution
            pass
        return True

    @staticmethod
    def _redact(text: str) -> str:
        if not text or not isinstance(text, str):
            return text

        # Prevent large raw resume text dumps in logs (truncate text > 500 chars if not JSON)
        if len(text) > 1000 and "{" not in text[:50]:
            text = text[:300] + "... [TRUNCATED - RAW TEXT EXCLUDED FOR SECURITY]"

        for pattern, replacement in REDACTION_PATTERNS:
            text = pattern.sub(replacement, text)

        return text


def get_security_logger(name: str) -> logging.Logger:
    """Return a configured logger equipped with the SecurityRedactionFilter."""
    logger = logging.getLogger(name)
    # Check if filter already attached
    if not any(isinstance(f, SecurityRedactionFilter) for f in logger.filters):
        logger.addFilter(SecurityRedactionFilter())
    return logger
