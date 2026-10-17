"""Document Ingestion & Multi-Format Text Extraction Service.

Supported formats:
- PDF (via PyMuPDF / fitz)
- DOCX (via python-docx)
- TXT (UTF-8 with encoding fallbacks)

Features:
- Stream-based in-memory processing (zero permanent disk storage)
- File validation (empty files, unsupported extensions, size limits)
- Error handling for corrupted and password-protected files
- Text cleaning and sensitive information masking
- Structured parsing response
"""

import io
import os
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import fitz  # PyMuPDF
import docx

from app.utils.text_cleaner import clean_text


MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/msword",
    "application/octet-stream",
}


def sanitize_filename(filename: Optional[str]) -> str:
    """Sanitize uploaded filename to prevent directory traversal and injection.
    
    - Extracts pure basename
    - Strips directory traversal tokens (../, ..\\, etc.)
    - Removes null bytes and control characters
    - Restricts characters to safe alphanumeric, underscores, hyphens, and single extension dot
    - Disallows hidden files (starting with dot)
    - Enforces maximum length limit of 100 characters
    """
    if not filename:
        return "document.txt"
    
    # Strip null bytes and control characters
    cleaned = filename.replace("\x00", "").strip()
    
    # Normalize Windows backslashes to forward slashes before extracting basename
    cleaned = cleaned.replace("\\", "/")
    
    # Extract basename to eliminate path traversal sequences
    cleaned = os.path.basename(cleaned)
    cleaned = re.sub(r"[\/\\]+", "", cleaned)
    cleaned = re.sub(r"\.\.+", "", cleaned)  # eliminate multiple dots (e.g. ../ or ..)
    
    # Remove leading dots to prevent hidden file names
    cleaned = cleaned.lstrip(".")
    
    # Replace unsafe characters with underscore (allow alphanumeric, underscore, dash, dot)
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", cleaned)
    
    # Enforce maximum length
    if len(cleaned) > 100:
        base, ext = os.path.splitext(cleaned)
        cleaned = base[:100 - len(ext)] + ext
        
    if not cleaned or cleaned.startswith("."):
        return "document.txt"
        
    return cleaned


def validate_magic_bytes(file_bytes: bytes, ext: str) -> None:
    """Verify file magic bytes against the claimed file extension.
    Prevents execution of malicious binaries disguised as documents.
    """
    if not file_bytes:
        raise EmptyFileError("Uploaded file is empty (0 bytes).")
        
    # Check for known dangerous binary executable headers
    # Windows PE (MZ), Linux ELF (\x7fELF), Mach-O binary signatures
    DANGEROUS_SIGNATURES = [
        b"MZ",  # Windows PE exe/dll
        b"\x7fELF",  # Linux ELF executable
        b"\xfe\xed\xfa\xce",  # Mach-O 32-bit
        b"\xfe\xed\xfa\xcf",  # Mach-O 64-bit
        b"\xce\xfa\xed\xfe",  # Mach-O reverse
        b"\xcf\xfa\xed\xfe",  # Mach-O reverse 64-bit
    ]
    for sig in DANGEROUS_SIGNATURES:
        if file_bytes.startswith(sig):
            raise UnsupportedFormatError(f"Executable binary content detected. Binary programs are strictly prohibited.")

    if ext == ".pdf":
        # PDF must begin with %PDF- (or within first 1024 bytes)
        header = file_bytes[:1024]
        if b"%PDF-" not in header:
            raise CorruptedDocumentError("Corrupted or invalid PDF format signature (%PDF- missing).")
            
    elif ext == ".docx":
        # DOCX is a ZIP container and must start with PK\x03\x04
        if not file_bytes.startswith(b"PK\x03\x04"):
            raise CorruptedDocumentError("Corrupted or invalid DOCX format signature (PK zip header missing).")
            
    elif ext == ".txt":
        # TXT must be valid text, not binary data
        # Check that null bytes are not pervasive (binary file heuristic)
        sample = file_bytes[:4096]
        if b"\x00" in sample:
            raise CorruptedDocumentError("Corrupted text file containing binary or null byte data.")


class DocumentParsingError(Exception):
    """Base exception for document parsing failures."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EmptyFileError(DocumentParsingError):
    def __init__(self, message: str = "Uploaded file is empty."):
        super().__init__(message, status_code=400)


class UnsupportedFormatError(DocumentParsingError):
    def __init__(self, extension: str):
        allowed = ", ".join(ext.upper().lstrip(".") for ext in sorted(ALLOWED_EXTENSIONS))
        message = f"Unsupported file format '{extension}'. Supported formats: {allowed}."
        super().__init__(message, status_code=400)


class FileSizeExceededError(DocumentParsingError):
    def __init__(self, size_bytes: int, max_bytes: int = MAX_FILE_SIZE_BYTES):
        max_mb = max_bytes // (1024 * 1024)
        actual_mb = round(size_bytes / (1024 * 1024), 2)
        message = f"File size ({actual_mb}MB) exceeds the maximum allowed limit of {max_mb}MB."
        super().__init__(message, status_code=413)


class EncryptedDocumentError(DocumentParsingError):
    def __init__(self, message: str = "Document is password-protected and cannot be parsed."):
        super().__init__(message, status_code=422)


class CorruptedDocumentError(DocumentParsingError):
    def __init__(self, message: str = "Document is corrupted or cannot be parsed."):
        super().__init__(message, status_code=422)


class DocumentParseResponse(BaseModel):
    document_type: str = Field(..., description="Document type slug: 'pdf', 'docx', or 'txt'")
    text: str = Field(..., description="Cleaned, extracted text content")
    page_count: int = Field(1, description="Page count (or estimated page count)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata metrics")


def sanitize_sensitive_information(text: str) -> str:
    """Mask high-risk sensitive patterns (payment cards, national IDs, SSNs, credentials)
    while preserving candidate contact info and technical competencies."""
    if not text:
        return ""
    
    # 1. 16-digit credit/debit card pattern
    card_pattern = r"\b(?:\d{4}[\s\-]?){3}\d{4}\b"
    text = re.sub(card_pattern, "[REDACTED-PAYMENT-CARD]", text)

    # 2. Indian Aadhaar 12-digit pattern
    aadhaar_pattern = r"\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b"
    text = re.sub(aadhaar_pattern, "[REDACTED-NATIONAL-ID]", text)

    # 3. US Social Security Number (SSN): 3-2-4 digits
    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
    text = re.sub(ssn_pattern, "[REDACTED-SSN]", text)

    # 4. Indian PAN card format (5 uppercase letters, 4 digits, 1 letter)
    pan_pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    text = re.sub(pan_pattern, "[REDACTED-TAX-ID]", text)

    # 5. API keys and passwords in plaintext
    secret_pattern = r"(?i)\b(api_key|secret|password|access_token|bearer)\s*[:=]\s*[^\s,;]+"
    text = re.sub(secret_pattern, r"\1: [REDACTED-SECRET]", text)

    return text


def parse_pdf(file_bytes: bytes, filename: str) -> tuple[str, int]:
    """Extract text and page count from PDF bytes using PyMuPDF."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise CorruptedDocumentError(f"Corrupted or invalid PDF structure: {str(e)}")

    try:
        # Check password encryption
        if doc.needs_pass or doc.is_encrypted:
            raise EncryptedDocumentError("PDF is password-protected and cannot be parsed.")

        page_count = len(doc)
        if page_count == 0:
            raise CorruptedDocumentError("PDF contains no pages.")

        extracted_parts = []
        for page_idx in range(page_count):
            page = doc[page_idx]
            extracted_parts.append(page.get_text())

        raw_text = "\n".join(extracted_parts)
        return raw_text, page_count
    finally:
        doc.close()


def parse_docx(file_bytes: bytes, filename: str) -> tuple[str, int]:
    """Extract text and estimated page count from DOCX bytes using python-docx."""
    try:
        doc_stream = io.BytesIO(file_bytes)
        document = docx.Document(doc_stream)
    except Exception as e:
        raise CorruptedDocumentError(f"Corrupted or invalid DOCX archive: {str(e)}")

    extracted_parts = []
    total_elements = 0

    # Extract paragraphs
    for p in document.paragraphs:
        total_elements += 1
        if p.text and p.text.strip():
            extracted_parts.append(p.text.strip())

    # Extract tables
    for table in document.tables:
        for row in table.rows:
            total_elements += 1
            row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_cells:
                extracted_parts.append(" | ".join(row_cells))

    raw_text = "\n".join(extracted_parts)
    # Estimate pages (standard resume is ~30-40 lines/elements per page)
    estimated_pages = max(1, round(total_elements / 35))
    return raw_text, estimated_pages


def parse_txt(file_bytes: bytes, filename: str) -> tuple[str, int]:
    """Decode text from plain text bytes."""
    # Attempt UTF-8 with fallback to Latin-1
    try:
        raw_text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            raw_text = file_bytes.decode("latin-1")
        except Exception as e:
            raise CorruptedDocumentError(f"Unable to decode text document: {str(e)}")

    lines = raw_text.splitlines()
    estimated_pages = max(1, round(len(lines) / 45))
    return raw_text, estimated_pages


def parse_document(
    file_bytes: bytes,
    filename: str,
    content_type: Optional[str] = None
) -> DocumentParseResponse:
    """Master document parsing function.
    
    Security & Validation Pipeline:
    1. Zero permanent disk storage — processed purely in-memory.
    2. File size validation (rejects files > 10MB).
    3. Empty file detection.
    4. Path traversal & filename injection sanitization.
    5. Allowed extension check (.pdf, .docx, .txt).
    6. MIME type validation against allowed list.
    7. Magic bytes / file signature validation (prevents disguised executable injection).
    8. Text extraction via PyMuPDF/python-docx with encryption detection.
    9. Sensitive information masking (Cards, Aadhaar, PAN, SSN, API keys, passwords).
    """
    # 1. Empty file validation
    if not file_bytes or len(file_bytes) == 0:
        raise EmptyFileError("Uploaded file is empty (0 bytes).")

    # 2. File size validation
    size_bytes = len(file_bytes)
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise FileSizeExceededError(size_bytes, MAX_FILE_SIZE_BYTES)

    # 3. Path traversal & malicious filename sanitization
    clean_filename = sanitize_filename(filename)
    ext = "." + clean_filename.rsplit(".", 1)[-1].lower() if "." in clean_filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFormatError(ext)

    # 4. MIME type validation if content_type header provided
    if content_type:
        clean_mime = content_type.split(";")[0].strip().lower()
        if clean_mime not in ALLOWED_MIME_TYPES:
            raise UnsupportedFormatError(f"MIME type '{clean_mime}' is not permitted")

    # 5. Magic bytes & file signature validation
    validate_magic_bytes(file_bytes, ext)

    # 6. Text extraction based on format
    doc_type = ext.lstrip(".")
    if ext == ".pdf":
        raw_text, page_count = parse_pdf(file_bytes, clean_filename)
    elif ext == ".docx":
        raw_text, page_count = parse_docx(file_bytes, clean_filename)
    elif ext == ".txt":
        raw_text, page_count = parse_txt(file_bytes, clean_filename)
    else:
        raise UnsupportedFormatError(ext)

    # 7. Text cleaning & normalization
    cleaned_text = clean_text(raw_text)

    # 8. Sensitive information masking (PII, cards, national IDs, credentials)
    sanitized_text = sanitize_sensitive_information(cleaned_text)

    # 9. Metadata computation
    word_count = len(sanitized_text.split()) if sanitized_text else 0
    char_count = len(sanitized_text)

    metadata = {
        "filename": clean_filename,
        "file_size_bytes": size_bytes,
        "character_count": char_count,
        "word_count": word_count,
        "content_type": content_type or f"application/{doc_type}",
    }

    return DocumentParseResponse(
        document_type=doc_type,
        text=sanitized_text,
        page_count=page_count,
        metadata=metadata,
    )
