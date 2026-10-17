import time
from typing import Dict, List, Optional, Union, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.extractor import extractor, ExtractedSkill
from app.core.role_engine import role_engine, CareerRoleProfile, RoleSkillRequirement
from app.core.matching_engine import (
    matching_engine,
    MatchWeights,
    ExplainableMatchResult,
    SkillExplanation
)
from app.core.gap_analyzer import gap_analyzer, GapAnalysisReport
from app.core.roadmap_generator import roadmap_generator, LearningRoadmapResponse
from app.core.recommendation_engine import recommendation_engine, CareerRecommendationResponse

router = APIRouter()


class MatchingAnalyzeRequest(BaseModel):
    # Candidate details
    candidate_skills: Optional[List[Union[ExtractedSkill, Dict, str]]] = Field(
        default_factory=list,
        description="Candidate skills as ExtractedSkill objects, dicts, or skill names/IDs"
    )
    resume_text: Optional[str] = Field(
        None,
        description="Raw resume text. If candidate_skills is empty, skills are extracted automatically."
    )
    candidate_experience_years: Optional[float] = Field(None, description="Years of professional experience")
    candidate_experience: Optional[Union[float, int, Dict, str]] = Field(None, description="Experience details")
    candidate_education: Optional[Union[Dict, str]] = Field(None, description="Education details (e.g. degree or level)")

    # Target role / job details
    target_role: Optional[str] = Field(
        None,
        description="Predefined role slug (e.g. 'backend_engineer', 'data_scientist') or title"
    )
    target_job: Optional[Dict] = Field(None, description="Custom job object with requirements")
    job_description_text: Optional[str] = Field(
        None,
        description="Raw job description text. If target_role is absent, ingested as custom role."
    )
    required_skills: Optional[List[Union[Dict, str]]] = Field(
        None,
        description="Explicit required skills (strings or dicts) overriding target_role defaults"
    )
    preferred_skills: Optional[List[Union[Dict, str]]] = Field(
        None,
        description="Explicit preferred skills (strings or dicts) overriding target_role defaults"
    )
    target_experience_years: Optional[float] = Field(
        None,
        description="Target minimum years of experience required for the role"
    )
    target_education_level: Optional[Union[int, str]] = Field(
        None,
        description="Target minimum education level (e.g. 'bachelor', 'master')"
    )

    # Configurable weights
    weights: Optional[MatchWeights] = Field(
        None,
        description="Configurable scoring weights (default: 60% required, 20% semantic, 10% exp, 10% pref)"
    )


@router.post(
    "/analyze",
    response_model=ExplainableMatchResult,
    status_code=status.HTTP_200_OK,
    summary="Compute mathematically explainable candidate-job match score",
    description=(
        "Evaluates candidate against target role or job description using explicit mathematical features: "
        "Required Skill Coverage (60%), Semantic Similarity (20%), Experience Alignment (10%), and "
        "Preferred Skill Coverage (10%). All scores are deterministic, reproducible, and explainable."
    )
)
async def analyze_match(request: MatchingAnalyzeRequest) -> ExplainableMatchResult:
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
    elif request.target_job:
        title = request.target_job.get("title", "Custom Job")
        reqs = request.target_job.get("required_skills", [])
        prefs = request.target_job.get("preferred_skills", [])
        role_arg = CareerRoleProfile(
            id="custom_target_job",
            title=title,
            category=request.target_job.get("category", "General"),
            summary=request.target_job.get("summary", ""),
            typical_experience_years=int(request.target_job.get("experience_years", 2)),
            required_skills=[],
            preferred_skills=[]
        )
        if not request.required_skills:
            request.required_skills = reqs
        if not request.preferred_skills:
            request.preferred_skills = prefs
    else:
        # Default to backend_engineer if no role or required skills provided
        if not request.required_skills:
            role_arg = "backend_engineer"

    # 3. Calculate match
    result = matching_engine.calculate_match(
        candidate_skills=active_skills,
        target_role=role_arg,
        custom_weights=request.weights,
        candidate_experience_years=request.candidate_experience_years,
        candidate_experience=request.candidate_experience,
        candidate_education=request.candidate_education,
        required_skills=request.required_skills,
        preferred_skills=request.preferred_skills,
        target_experience_years=request.target_experience_years,
        target_education_level=request.target_education_level,
    )

    return result


class CandidatePipelineRequest(BaseModel):
    """Payload for POST /api/v1/matching/candidate-pipeline."""
    candidate_skills: Optional[List[Union[ExtractedSkill, Dict, str]]] = Field(
        default_factory=list,
        description="Candidate skills as ExtractedSkill objects, dicts, or skill names/IDs"
    )
    resume_text: Optional[str] = Field(None, description="Raw resume text")
    target_role: Optional[str] = Field("data_scientist", description="Target role slug")
    candidate_experience_years: Optional[float] = Field(2.5, description="Years of professional experience")
    candidate_name: Optional[str] = Field("Candidate", description="Candidate name")


class CandidatePipelineResponse(BaseModel):
    """Unified candidate analysis payload combining 4 services in a single roundtrip."""
    matching: ExplainableMatchResult
    gap_analysis: GapAnalysisReport
    roadmap: LearningRoadmapResponse
    recommendations: CareerRecommendationResponse
    execution_time_ms: float


@router.post(
    "/candidate-pipeline",
    response_model=CandidatePipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Unified High-Performance Candidate Intelligence Pipeline",
    description=(
        "Executes candidate matching, skill gap analysis, learning roadmap generation, and "
        "career recommendations in a single in-memory pass, eliminating 3 redundant network "
        "requests and duplicate skill vector processing."
    )
)
async def run_candidate_pipeline_endpoint(request: CandidatePipelineRequest) -> CandidatePipelineResponse:
    t0 = time.perf_counter()
    # 1. Resolve skills
    active_skills: List[Union[ExtractedSkill, Dict, str]] = list(request.candidate_skills or [])
    if not active_skills and request.resume_text and request.resume_text.strip():
        report = extractor.extract_from_text(request.resume_text, source="resume")
        active_skills = report.skills

    role_id = request.target_role or "data_scientist"
    exp_years = request.candidate_experience_years if request.candidate_experience_years is not None else 2.5

    # 2. In-memory single-pass computations
    # (a) Matching
    match_result = matching_engine.calculate_match(
        candidate_skills=active_skills,
        target_role=role_id,
        candidate_experience_years=exp_years,
    )

    # (b) Gap Analysis
    gap_report = gap_analyzer.analyze_gaps(
        candidate_skills=active_skills,
        target_role=role_id,
    )

    # (c) Roadmap generation with already computed missing/partial skills
    missing_skill_ids = [m.skill for m in match_result.missing_skills]
    partial_skill_ids = [p.skill for p in match_result.partial_matches]
    roadmap_result = roadmap_generator.generate_roadmap(
        candidate_skills=active_skills,
        target_role=role_id,
        missing_skills=missing_skill_ids,
        partial_skills=partial_skill_ids,
        candidate_experience_years=exp_years,
    )

    # (d) Recommendations
    rec_result = recommendation_engine.recommend_roles(
        candidate_skills=active_skills,
        candidate_experience_years=exp_years,
        current_role=role_id,
    )

    t1 = time.perf_counter()
    return CandidatePipelineResponse(
        matching=match_result,
        gap_analysis=gap_report,
        roadmap=roadmap_result,
        recommendations=rec_result,
        execution_time_ms=round((t1 - t0) * 1000.0, 2)
    )
