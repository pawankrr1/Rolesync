"""Document Ingestion API Endpoints."""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.services.document_parser import (
    parse_document,
    DocumentParseResponse,
    DocumentParsingError,
    EmptyFileError,
    FileSizeExceededError,
    UnsupportedFormatError,
    EncryptedDocumentError,
    CorruptedDocumentError,
    MAX_FILE_SIZE_BYTES,
)
from app.core.rate_limiter import rate_limit
from app.core.logging_security import get_security_logger

logger = get_security_logger("document_parser_api")
router = APIRouter()


@router.post(
    "/parse",
    response_model=DocumentParseResponse,
    summary="Ingest and extract text from resume document",
    description="Parses PDF, DOCX, or TXT documents in-memory and returns cleaned text with page count and metadata.",
    dependencies=[Depends(rate_limit(max_requests=25, window_seconds=60, endpoint_tag="doc_parse"))],
    responses={
        200: {
            "description": "Document parsed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "document_type": "pdf",
                        "text": "Jane Doe\nSenior Python Backend Developer...",
                        "page_count": 2,
                        "metadata": {
                            "filename": "resume.pdf",
                            "file_size_bytes": 48210,
                            "character_count": 2400,
                            "word_count": 350,
                            "content_type": "application/pdf"
                        }
                    }
                }
            }
        },
        400: {"description": "Empty file or unsupported format"},
        413: {"description": "File size exceeds allowed limit (10MB)"},
        422: {"description": "Corrupted or password-protected document"},
        429: {"description": "Rate limit exceeded"},
    }
)
async def parse_document_endpoint(
    file: UploadFile = File(..., description="Document file to parse (PDF, DOCX, TXT)")
) -> DocumentParseResponse:
    """Parses an uploaded document stream and returns extracted text and metadata.
    
    Security controls:
    - Zero permanent disk storage (stream processed in-memory).
    - Hard limit on file stream read to prevent memory exhaustion DoS.
    - Path traversal & filename sanitization.
    - Magic bytes format verification.
    - Rate-limited per client IP.
    """
    filename = file.filename or "uploaded_document"
    content_type = file.content_type

    # 1. Read file stream in chunks with hard cutoff at MAX_FILE_SIZE_BYTES
    chunk_size = 64 * 1024  # 64 KB chunks
    total_bytes = bytearray()
    
    try:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_bytes.extend(chunk)
            if len(total_bytes) > MAX_FILE_SIZE_BYTES:
                raise FileSizeExceededError(len(total_bytes), MAX_FILE_SIZE_BYTES)
    except FileSizeExceededError as e:
        raise HTTPException(status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413), detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file stream."
        )

    file_bytes = bytes(total_bytes)

    # 2. Parse document with security validation pipeline
    try:
        result = parse_document(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
        )
        logger.info(
            "Document parsed successfully",
            extra={
                "filename": result.metadata.get("filename"),
                "file_size": result.metadata.get("file_size_bytes"),
                "page_count": result.page_count,
            }
        )
        return result
    except EmptyFileError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except UnsupportedFormatError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except FileSizeExceededError as e:
        raise HTTPException(status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413), detail=e.message)
    except EncryptedDocumentError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except CorruptedDocumentError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DocumentParsingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        # Prevent stack trace leakage in API responses
        logger.error(f"Unexpected parsing error for {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while parsing the document. Please ensure the file is valid and retry."
        )
