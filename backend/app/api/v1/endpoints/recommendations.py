"""API endpoints for Career Role Recommendations."""

from typing import Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.extractor import extractor, ExtractedSkill
from app.core.recommendation_engine import (
    recommendation_engine,
    CareerRecommendationResponse,
    RoleRecommendationItem,
    AdjacentRolePathway,
)

router = APIRouter()


class RoleRecommendationRequest(BaseModel):
    """Payload for POST /api/v1/recommendations/roles."""
    candidate_skills: Optional[List[Union[ExtractedSkill, Dict, str]]] = Field(
        default_factory=list,
        description="Candidate skills as ExtractedSkill objects, dicts, or canonical skill names/IDs."
    )
    resume_text: Optional[str] = Field(
        None,
        description="Raw resume text. If candidate_skills is empty, skills are extracted automatically."
    )
    candidate_experience_years: Optional[float] = Field(
        None,
        description="Years of professional experience"
    )
    candidate_experience: Optional[Union[float, int, Dict, str]] = Field(
        None,
        description="Experience details (number of years, dict, or description)"
    )
    candidate_education: Optional[Union[Dict, str]] = Field(
        None,
        description="Education details (degree, level, or institution)"
    )
    current_role: Optional[str] = Field(
        None,
        description="Current role slug or title (e.g. 'software_engineer') to anchor adjacent career transitions"
    )


@router.post(
    "/roles",
    response_model=CareerRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend Top 5 suitable career roles and adjacent progression paths",
    description=(
        "Evaluates candidate against all canonical career roles using candidate skill vector, "
        "role skill vector, skill coverage, semantic similarity, and experience compatibility. "
        "Returns top 5 roles with matched skills, missing skills, explainable reasons, and next skills to learn. "
        "Also computes multi-step adjacent-role recommendations (e.g. Software Engineer -> Backend Developer -> ML Engineer) "
        "strictly when verified skill evidence supports the transition."
    )
)
async def recommend_career_roles(request: RoleRecommendationRequest) -> CareerRecommendationResponse:
    # 1. Resolve candidate skills
    active_skills: List[Union[ExtractedSkill, Dict, str]] = list(request.candidate_skills or [])
    if not active_skills and request.resume_text and request.resume_text.strip():
        report = extractor.extract_from_text(request.resume_text, source="resume")
        active_skills = report.skills

    # 2. Resolve experience
    exp_years = request.candidate_experience_years
    if exp_years is None and request.candidate_experience is not None:
        if isinstance(request.candidate_experience, (int, float)):
            exp_years = float(request.candidate_experience)
        elif isinstance(request.candidate_experience, dict):
            exp_years = float(request.candidate_experience.get("years", 0))

    # 3. Compute Top 5 Role Recommendations and Adjacent Pathways
    recommendation_result = recommendation_engine.recommend_roles(
        candidate_skills=active_skills,
        candidate_experience_years=exp_years,
        candidate_education=request.candidate_education,
        current_role=request.current_role,
    )

    return recommendation_result


from app.core.roadmap_generator import (
    roadmap_generator,
    LearningRoadmapResponse,
    LearningRoadmapItem,
)


class RoadmapRequest(BaseModel):
    """Payload for POST /api/v1/recommendations/roadmap."""
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
        description="Target career role slug (e.g. 'data_scientist', 'backend_engineer') or title."
    )
    missing_skills: Optional[List[Union[Dict, str]]] = Field(
        None,
        description="Explicit list of missing skills."
    )
    partial_skills: Optional[List[Union[Dict, str]]] = Field(
        None,
        description="Explicit list of partial skills."
    )
    candidate_experience_years: Optional[float] = Field(
        None,
        description="Candidate years of experience"
    )


@router.post(
    "/roadmap",
    response_model=LearningRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate prioritized, dependency-aware learning roadmap",
    description=(
        "Translates candidate profile, target role, missing skills, and partial skills into a "
        "dependency-aware, prioritized learning plan. Each roadmap milestone specifies the skill, "
        "priority, reason, prerequisites, recommended sequence, estimated learning stage, and "
        "verified learning resources from the local seeded dataset."
    )
)
async def generate_learning_roadmap(request: RoadmapRequest) -> LearningRoadmapResponse:
    # 1. Resolve candidate skills
    active_skills: List[Union[ExtractedSkill, Dict, str]] = list(request.candidate_skills or [])
    if not active_skills and request.resume_text and request.resume_text.strip():
        report = extractor.extract_from_text(request.resume_text, source="resume")
        active_skills = report.skills

    # 2. Generate roadmap
    result = roadmap_generator.generate_roadmap(
        candidate_skills=active_skills,
        target_role=request.target_role,
        missing_skills=request.missing_skills,
        partial_skills=request.partial_skills,
        candidate_experience_years=request.candidate_experience_years,
    )

    return result

