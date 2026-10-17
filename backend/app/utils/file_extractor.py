"""Safe multi-format document parser supporting PDF, DOCX, and TXT files."""

from app.services.document_parser import (
    parse_document,
    DocumentParsingError,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
)


class FileExtractionError(Exception):
    """Exception raised for file extraction errors."""
    pass


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """Extract clean text content from uploaded file bytes."""
    try:
        parsed = parse_document(file_bytes, filename)
        return parsed.text
    except DocumentParsingError as e:
        raise FileExtractionError(e.message) from e
    except Exception as e:
        raise FileExtractionError(f"Failed to parse {filename}: {str(e)}") from e
