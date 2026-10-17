"""ATS Resume Checker API Endpoints."""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field

from app.services.document_parser import (
    parse_document,
    DocumentParsingError,
    EmptyFileError,
    FileSizeExceededError,
    UnsupportedFormatError,
    EncryptedDocumentError,
    CorruptedDocumentError,
    MAX_FILE_SIZE_BYTES,
)
from app.services.ats_service import ATSService, ATSAnalysisResponse
from app.core.logging_security import get_security_logger

logger = get_security_logger("ats_checker_api")
router = APIRouter()


class ATSAnalyzeRequest(BaseModel):
    resume_text: str = Field(..., description="Extracted resume text to evaluate")
    filename: Optional[str] = Field("resume.pdf", description="Original file name")
    file_size_bytes: Optional[int] = Field(0, description="Size in bytes")
    page_count: Optional[int] = Field(1, description="Page count")
    check_type: Optional[str] = Field("general", description="'general' or 'job_specific'")
    job_description_text: Optional[str] = Field(None, description="Pasted Job Description for job-specific ATS check")
    target_job_title: Optional[str] = Field(None, description="Optional target job title")


@router.post(
    "/analyze",
    response_model=ATSAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze resume ATS readiness and calculate deterministic score",
    description="Evaluates parseability, content completeness, skill presentation, experience/impact, formatting signals, and optional JD alignment."
)
async def analyze_ats_endpoint(request: ATSAnalyzeRequest) -> ATSAnalysisResponse:
    if not request.resume_text or not request.resume_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text cannot be empty. Please provide parsed resume content."
        )

    try:
        response = ATSService.analyze(
            resume_text=request.resume_text,
            filename=request.filename,
            file_size_bytes=request.file_size_bytes or 0,
            page_count=request.page_count or 1,
            check_type=request.check_type or "general",
            job_description_text=request.job_description_text,
            target_job_title=request.target_job_title,
        )
        return response
    except Exception as e:
        logger.error(f"Error during ATS analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while evaluating ATS readiness. Please retry."
        )


@router.post(
    "/upload-and-analyze",
    response_model=ATSAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload resume file directly and execute ATS readiness check",
    description="Stream parses document in-memory (zero persistent PII disk storage) and runs deterministic ATS evaluation."
)
async def upload_and_analyze_ats_endpoint(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, TXT)"),
    check_type: str = Form("general", description="'general' or 'job_specific'"),
    job_description_text: Optional[str] = Form(None, description="Optional job description text"),
    target_job_title: Optional[str] = Form(None, description="Optional target job title"),
) -> ATSAnalysisResponse:
    filename = file.filename or "uploaded_resume.pdf"
    content_type = file.content_type

    # 1. Read file stream in chunks
    chunk_size = 64 * 1024
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file stream."
        )

    file_bytes = bytes(total_bytes)

    # 2. Parse document using existing secure document parser
    try:
        parsed_doc = parse_document(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
        )
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
        logger.error(f"Unexpected parsing error for {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while parsing the resume. Ensure it is a valid, unencrypted document."
        )

    # 3. Execute ATS Evaluation
    try:
        response = ATSService.analyze(
            resume_text=parsed_doc.text,
            filename=filename,
            file_size_bytes=len(file_bytes),
            page_count=parsed_doc.page_count,
            check_type=check_type,
            job_description_text=job_description_text,
            target_job_title=target_job_title,
        )
        return response
    except Exception as e:
        logger.error(f"Error during ATS evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete ATS readiness evaluation."
        )
