"""API endpoints for Skill Extraction."""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.extractor import extractor, ExtractedSkill, ExtractionReport

router = APIRouter()


class SkillExtractRequest(BaseModel):
    text: Optional[str] = Field(None, description="General text (resume or job description)")
    resume_text: Optional[str] = Field(None, description="Resume text")
    job_description_text: Optional[str] = Field(None, description="Job description text")
    source: Optional[str] = Field(None, description="Source tag: 'resume' or 'job_description'")


class SkillExtractResponse(BaseModel):
    skills: List[ExtractedSkill] = Field(..., description="Extracted skills with evidence and canonical taxonomy")
    total_skills_detected: int = Field(0, description="Total unique canonical skills detected")
    categories_found: List[str] = Field(default_factory=list, description="Unique taxonomy categories")
    extraction_layers_used: List[str] = Field(default_factory=list, description="Layers activated during extraction")


@router.post(
    "/extract",
    response_model=SkillExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract skills from resume and/or job description text",
    description=(
        "Extracts technical and professional skills using a hybrid 4-layer architecture. "
        "Every returned skill is grounded in direct sentence evidence with calibrated confidence."
    )
)
async def extract_skills(request: SkillExtractRequest) -> SkillExtractResponse:
    all_skills: List[ExtractedSkill] = []
    layers_used: List[str] = []

    # Case 1: Separate resume_text and/or job_description_text
    has_separate_inputs = bool(request.resume_text or request.job_description_text)

    if request.resume_text and request.resume_text.strip():
        report = extractor.extract_from_text(request.resume_text, source="resume")
        all_skills.extend(report.skills)
        layers_used = report.extraction_layers_used

    if request.job_description_text and request.job_description_text.strip():
        report = extractor.extract_from_text(request.job_description_text, source="job_description")
        all_skills.extend(report.skills)
        layers_used = report.extraction_layers_used

    # Case 2: General text input
    if not has_separate_inputs and request.text and request.text.strip():
        source_tag = request.source if request.source else "resume"
        report = extractor.extract_from_text(request.text, source=source_tag)
        all_skills.extend(report.skills)
        layers_used = report.extraction_layers_used

    # Deduplicate if same canonical_id and source appear
    unique_skills_dict: Dict[str, ExtractedSkill] = {}
    for s in all_skills:
        key = f"{s.canonical_id}_{s.source}"
        if key not in unique_skills_dict:
            unique_skills_dict[key] = s
        else:
            existing = unique_skills_dict[key]
            existing.frequency += s.frequency
            existing.confidence = max(existing.confidence, s.confidence)

    final_skills = list(unique_skills_dict.values())
    final_skills.sort(key=lambda s: (s.source, s.category, s.canonical_name))

    categories = sorted(list({s.category for s in final_skills}))

    return SkillExtractResponse(
        skills=final_skills,
        total_skills_detected=len(final_skills),
        categories_found=categories,
        extraction_layers_used=layers_used or [
            "Layer 1: Deterministic Dictionary",
            "Layer 2: Context Patterns & Disambiguation"
        ]
    )
