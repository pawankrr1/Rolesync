"""Security Audit and Vulnerability Regression Test Suite.

Validates defensive security controls across:
- File upload validation (size limits, MIME types, magic bytes)
- Path traversal & malicious filename sanitization
- Zero permanent resume disk storage
- SQL injection immunity
- XSS & Protocol Injection prevention
- CORS configuration security
- Secret management & logging redaction (passwords, tokens, API keys)
- PII and high-risk credential masking (Cards, Aadhaar, SSN, PAN, secrets)
- Rate limiting protection (429 Too Many Requests)
- API error leakage prevention
"""

import io
import os
import logging
import pytest
import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.services.document_parser import (
    parse_document,
    sanitize_filename,
    validate_magic_bytes,
    sanitize_sensitive_information,
    MAX_FILE_SIZE_BYTES,
    EmptyFileError,
    FileSizeExceededError,
    UnsupportedFormatError,
    CorruptedDocumentError,
)
from app.core.rate_limiter import rate_limiter
from app.core.logging_security import SecurityRedactionFilter, get_security_logger
from app.db.repositories.user_repo import UserRepository
from app.db.session import SessionLocal


@pytest.fixture
def client() -> TestClient:
    rate_limiter.reset()
    return TestClient(app)


def make_valid_pdf_bytes(content: str = "Pawan Kumar - Senior Systems Engineer") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), content)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


# ==============================================================================
# 1. FILE UPLOAD SECURITY (Size Limits, Empty Files, Formats)
# ==============================================================================

class TestFileUploadSecurity:
    """Verifies strict upload validation, file size limits, and format controls."""

    def test_file_upload_size_limit_rejection(self, client: TestClient):
        """Oversized files (> 10MB) must be rejected with HTTP 413 without memory exhaustion."""
        oversized = b"A" * (MAX_FILE_SIZE_BYTES + 2048)
        files = {"file": ("big_resume.pdf", oversized, "application/pdf")}
        response = client.post("/api/v1/documents/parse", files=files)
        assert response.status_code == 413
        assert "exceeds" in response.json()["detail"].lower()

    def test_empty_file_upload_rejection(self, client: TestClient):
        """0-byte files must be rejected with HTTP 400 Bad Request."""
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        response = client.post("/api/v1/documents/parse", files=files)
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_unsupported_file_extension_rejection(self, client: TestClient):
        """Executable, script, or binary extensions must be rejected with HTTP 400."""
        dangerous_extensions = [
            ("script.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh"),
            ("exploit.exe", b"MZ\x90\x00\x03fake-executable", "application/octet-stream"),
            ("payload.php", b"<?php phpinfo(); ?>", "application/x-httpd-php"),
            ("app.py", b"import os; os.system('ls')", "text/x-python"),
            ("index.html", b"<script>alert(1)</script>", "text/html"),
        ]
        for fname, content, mime in dangerous_extensions:
            files = {"file": (fname, content, mime)}
            response = client.post("/api/v1/documents/parse", files=files)
            assert response.status_code == 400, f"Expected 400 for {fname}, got {response.status_code}"
            assert "unsupported" in response.json()["detail"].lower()


# ==============================================================================
# 2. PATH TRAVERSAL & MALICIOUS FILENAMES
# ==============================================================================

class TestPathTraversalAndFilenameSanitization:
    """Verifies that malicious filenames and path traversal payloads are neutralized."""

    def test_path_traversal_payloads_sanitized(self):
        """Path traversal sequences (../../etc/passwd) must be stripped to clean basenames."""
        traversal_attempts = [
            ("../../../../etc/passwd.pdf", "passwd.pdf"),
            ("..\\..\\windows\\system32\\config.pdf", "config.pdf"),
            ("/var/log/private/secret.docx", "secret.docx"),
            ("..//..//..//root//resume.txt", "resume.txt"),
        ]
        for input_name, expected_base in traversal_attempts:
            sanitized = sanitize_filename(input_name)
            assert "/" not in sanitized
            assert "\\" not in sanitized
            assert ".." not in sanitized
            assert sanitized == expected_base

    def test_malicious_characters_sanitized(self):
        """Null bytes, control characters, and injection tokens must be replaced or stripped."""
        dirty_names = [
            ("evil\x00resume.pdf", "evilresume.pdf"),
            ("<script>alert(1)</script>.pdf", "_script_alert_1___script_.pdf"),
            (".bashrc", "document.txt"),  # hidden file disallowed
            ("a" * 150 + ".pdf", 100),   # max length enforcement
        ]
        for dirty, expected in dirty_names[:3]:
            res = sanitize_filename(dirty)
            assert "\x00" not in res
            assert "<" not in res
            assert ">" not in res

        # Length test
        long_sanitized = sanitize_filename(dirty_names[3][0])
        assert len(long_sanitized) <= 100
        assert long_sanitized.endswith(".pdf")

    def test_endpoint_path_traversal_reflection_safe(self, client: TestClient):
        """Endpoint metadata must return sanitized filename, never raw path traversal."""
        pdf_bytes = make_valid_pdf_bytes()
        files = {"file": ("../../../../etc/shadow.pdf", pdf_bytes, "application/pdf")}
        response = client.post("/api/v1/documents/parse", files=files)
        assert response.status_code == 200
        metadata = response.json()["metadata"]
        assert metadata["filename"] == "shadow.pdf"
        assert ".." not in metadata["filename"]


# ==============================================================================
# 3. MAGIC BYTES & DISGUISED BINARY VALIDATION
# ==============================================================================

class TestMagicBytesAndFileSignatures:
    """Verifies file content signatures match claimed extensions."""

    def test_disguised_executable_rejected(self):
        """Windows PE executable (MZ header) disguised as .pdf must be rejected."""
        fake_pdf = b"MZ\x90\x00\x03\x00\x00\x00" + b"A" * 100
        with pytest.raises(UnsupportedFormatError) as exc_info:
            validate_magic_bytes(fake_pdf, ".pdf")
        assert "executable" in str(exc_info.value).lower()

    def test_disguised_elf_executable_rejected(self):
        """Linux ELF executable (\x7fELF) disguised as .docx must be rejected."""
        fake_docx = b"\x7fELF\x02\x01\x01\x00" + b"B" * 100
        with pytest.raises(UnsupportedFormatError) as exc_info:
            validate_magic_bytes(fake_docx, ".docx")
        assert "executable" in str(exc_info.value).lower()

    def test_plain_text_disguised_as_pdf_rejected(self):
        """Plain text without %PDF- header must be rejected for .pdf extension."""
        text_disguised_as_pdf = b"This is just raw text with no PDF header."
        with pytest.raises(CorruptedDocumentError) as exc_info:
            validate_magic_bytes(text_disguised_as_pdf, ".pdf")
        assert "pdf format signature" in str(exc_info.value).lower()

    def test_non_zip_disguised_as_docx_rejected(self):
        """Files without PK zip header must be rejected for .docx extension."""
        garbage_docx = b"NOT_A_ZIP_CONTAINER" + b"X" * 50
        with pytest.raises(CorruptedDocumentError) as exc_info:
            validate_magic_bytes(garbage_docx, ".docx")
        assert "docx format signature" in str(exc_info.value).lower()


# ==============================================================================
# 4. ZERO PERMANENT DISK STORAGE
# ==============================================================================

class TestZeroPermanentStorage:
    """Guarantees uploaded resumes are processed purely in-memory and never saved to disk."""

    def test_no_disk_files_created_during_parsing(self, client: TestClient):
        cwd_files_before = set(os.listdir("."))
        pdf_bytes = make_valid_pdf_bytes("Sensitive Candidate Resume - Not For Storage")
        files = {"file": ("transient_test.pdf", pdf_bytes, "application/pdf")}

        response = client.post("/api/v1/documents/parse", files=files)
        assert response.status_code == 200

        cwd_files_after = set(os.listdir("."))
        # No new files must exist in current working directory
        new_files = cwd_files_after - cwd_files_before
        # Exclude expected test/runtime artifacts like __pycache__ or .pytest_cache
        relevant_new_files = [f for f in new_files if "transient" in f or f.endswith(".pdf")]
        assert len(relevant_new_files) == 0, f"Temporary resume leaked to disk: {relevant_new_files}"


# ==============================================================================
# 5. PII & SENSITIVE DATA MASKING
# ==============================================================================

class TestPiiAndSensitiveDataMasking:
    """Verifies automated masking of credentials, tax IDs, SSNs, and payment cards."""

    def test_payment_card_masked(self):
        raw = "Contact details: credit card 4111-2222-3333-4444 for billing."
        sanitized = sanitize_sensitive_information(raw)
        assert "[REDACTED-PAYMENT-CARD]" in sanitized
        assert "4111-2222-3333-4444" not in sanitized

    def test_national_aadhaar_id_masked(self):
        raw = "Resident ID / Aadhaar: 5432 9876 1234 on record."
        sanitized = sanitize_sensitive_information(raw)
        assert "[REDACTED-NATIONAL-ID]" in sanitized
        assert "5432 9876 1234" not in sanitized

    def test_us_ssn_masked(self):
        raw = "Candidate Social Security Number: 123-45-6789."
        sanitized = sanitize_sensitive_information(raw)
        assert "[REDACTED-SSN]" in sanitized
        assert "123-45-6789" not in sanitized

    def test_indian_pan_card_masked(self):
        raw = "Tax identification PAN: ABCDE1234F registered."
        sanitized = sanitize_sensitive_information(raw)
        assert "[REDACTED-TAX-ID]" in sanitized
        assert "ABCDE1234F" not in sanitized

    def test_passwords_and_api_keys_masked(self):
        raw = "Deployment configuration: api_key=sk-live-992837482910 password=SuperSecretPassword123"
        sanitized = sanitize_sensitive_information(raw)
        assert "[REDACTED-SECRET]" in sanitized
        assert "sk-live-992837482910" not in sanitized
        assert "SuperSecretPassword123" not in sanitized


# ==============================================================================
# 6. SQL INJECTION IMMUNITY
# ==============================================================================

class TestSqlInjectionResistance:
    """Verifies that all database repositories utilize parameterized queries immune to SQLi."""

    def test_user_repository_sql_injection_payloads(self):
        db = SessionLocal()
        try:
            sqli_payloads = [
                "' OR '1'='1' --",
                "admin' --",
                "' UNION SELECT id, email, hashed_password FROM users --",
                "'; DROP TABLE users; --",
                "' OR 1=1; --",
            ]
            for payload in sqli_payloads:
                # Must query safely without throwing syntax errors or returning unauthenticated records
                user = UserRepository.get_user_by_email(db, payload)
                assert user is None

                auth = UserRepository.authenticate_user(db, payload, "password")
                assert auth is None
        finally:
            db.close()


# ==============================================================================
# 7. LOGGING REDACTION (No Passwords, Keys, or Full Resumes in Logs)
# ==============================================================================

class TestLoggingSecurityAndRedaction:
    """Verifies that loggers never leak full resumes, passwords, or credentials."""

    def test_security_filter_redacts_credentials(self):
        filter_obj = SecurityRedactionFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="User login attempted with password=MySecretPassword and api_key=sk-1234567890abcdef",
            args=(),
            exc_info=None,
        )
        filter_obj.filter(record)
        assert "MySecretPassword" not in record.msg
        assert "sk-1234567890abcdef" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_security_filter_truncates_large_raw_resume_dumps(self):
        filter_obj = SecurityRedactionFilter()
        large_raw_resume = "Candidate Resume Dump: " + "Python Developer with 5 years experience. " * 50
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg=large_raw_resume,
            args=(),
            exc_info=None,
        )
        filter_obj.filter(record)
        assert "[TRUNCATED - RAW TEXT EXCLUDED FOR SECURITY]" in record.msg
        assert len(record.msg) < 500


# ==============================================================================
# 8. CORS & HTTP SECURITY HEADERS
# ==============================================================================

class TestCorsAndSecurityHeaders:
    """Verifies HTTP security headers and safe CORS credential handling."""

    def test_security_headers_present_on_responses(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        headers = response.headers

        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in headers.get("Permissions-Policy", "")

    def test_cors_configuration_safe(self, client: TestClient):
        """When origins are explicitly configured, credentials can be allowed."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        # Wildcard origin with credentials is forbidden by CORS spec
        allow_origin = response.headers.get("access-control-allow-origin")
        allow_creds = response.headers.get("access-control-allow-credentials")
        if allow_origin == "*":
            assert allow_creds != "true", "Wildcard origin cannot be combined with allow-credentials=true"


# ==============================================================================
# 9. RATE LIMITING PROTECTION
# ==============================================================================

class TestRateLimiter:
    """Verifies in-memory rate limiting triggers HTTP 429 when limits are exceeded."""

    def test_rate_limiter_triggers_429(self, client: TestClient):
        rate_limiter.reset()
        pdf_bytes = make_valid_pdf_bytes("Rate limiting candidate profile")

        # Exceed rate limit for document parse (limit is 25 per minute)
        status_codes = []
        for i in range(30):
            files = {"file": (f"test_{i}.pdf", pdf_bytes, "application/pdf")}
            res = client.post("/api/v1/documents/parse", files=files)
            status_codes.append(res.status_code)

        assert 429 in status_codes
        # Verify 429 response contains Retry-After header
        assert any(
            client.post("/api/v1/documents/parse", files={"file": ("t.pdf", pdf_bytes, "application/pdf")}).headers.get("Retry-After")
            for _ in range(1)
        )
        rate_limiter.reset()


# ==============================================================================
# 10. API ERROR LEAKAGE
# ==============================================================================

class TestApiErrorLeakage:
    """Verifies that internal exceptions do not leak stack traces or server paths to callers."""

    def test_corrupted_document_message_sanitized(self, client: TestClient):
        """Corrupted documents return structured, user-friendly errors without internal tracebacks."""
        corrupted = b"%PDF-1.4 garbage corrupted byte stream"
        files = {"file": ("corrupted.pdf", corrupted, "application/pdf")}
        response = client.post("/api/v1/documents/parse", files=files)
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "Traceback" not in detail
        assert "/Users/" not in detail
        assert "corrupted" in detail.lower()
