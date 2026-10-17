"""API endpoints for Skill Gap Analysis Engine."""

from typing import Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.extractor import extractor, ExtractedSkill
from app.core.role_engine import role_engine, CareerRoleProfile
from app.core.gap_analyzer import (
    gap_analyzer,
    GapAnalysisReport,
    SkillGapItem,
)

router = APIRouter()


class GapAnalyzeRequest(BaseModel):
    """Payload for POST /api/v1/gap/analyze."""
    candidate_skills: Optional[List[Union[ExtractedSkill, Dict, str]]] = Field(
        default_factory=list,
        description="Candidate skills as ExtractedSkill objects, dicts, or canonical skill names/IDs."
    )
    resume_text: Optional[str] = Field(
        None,
        description="Raw resume text. If candidate_skills is empty, skills are extracted automatically."
    )
    target_role: Optional[str] = Field(
        None,
        description="Target role slug (e.g. 'backend_engineer', 'data_scientist') or title."
    )
    job_description_text: Optional[str] = Field(
        None,
        description="Raw job description text. If target_role is absent, ingested as custom role profile."
    )
    required_skills: Optional[List[Union[Dict, str]]] = Field(
        None,
        description="Explicit required skills (strings or dicts) overriding target_role defaults."
    )
    preferred_skills: Optional[List[Union[Dict, str]]] = Field(
        None,
        description="Explicit preferred skills (strings or dicts) overriding target_role defaults."
    )


@router.post(
    "/analyze",
    response_model=GapAnalysisReport,
    status_code=status.HTTP_200_OK,
    summary="Analyze candidate skill gaps against target role or job requirements",
    description=(
        "Computes exact skill gaps: Required skills minus Candidate skills, improved using "
        "skill importance and partial taxonomy similarity. Classifies skills into STRONG, "
        "PARTIAL, and MISSING. For each gap, calculates 5-factor priority (role importance, "
        "dataset demand in jobs.json, candidate skill similarity, learning dependency, and gap magnitude). "
        "Returns gap_score, strong_skills, partial_skills, missing_skills, and priority_order."
    )
)
async def analyze_gaps(request: GapAnalyzeRequest) -> GapAnalysisReport:
    # 1. Resolve candidate skills
    active_skills: List[Union[ExtractedSkill, Dict, str]] = list(request.candidate_skills or [])
    if not active_skills and request.resume_text and request.resume_text.strip():
        report = extractor.extract_from_text(request.resume_text, source="resume")
        active_skills = report.skills

    # 2. Resolve target role / job profile
    role_arg: Optional[Union[CareerRoleProfile, str]] = None
    if request.target_role:
        role_arg = request.target_role
    elif request.job_description_text and request.job_description_text.strip():
        role_arg = role_engine.ingest_custom_job_description(request.job_description_text)
    elif request.required_skills:
        role_arg = None  # Explicit requirements will be used
    else:
        # Default fallback to backend_engineer if nothing specified
        role_arg = "backend_engineer"

    # 3. Execute Explainable Gap Analysis
    report = gap_analyzer.analyze_gaps(
        candidate_skills=active_skills,
        target_role=role_arg,
        required_skills=request.required_skills,
        preferred_skills=request.preferred_skills,
    )

    return report
