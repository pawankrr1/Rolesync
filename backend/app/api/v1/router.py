"""API v1 master router."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, documents, skills, matching, gap, recommendations, recruiter, insights, ats

api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_v1_router.include_router(skills.router, prefix="/skills", tags=["Skills"])
api_v1_router.include_router(matching.router, prefix="/matching", tags=["Matching"])
api_v1_router.include_router(gap.router, prefix="/gap", tags=["Gap Analysis"])
api_v1_router.include_router(recommendations.router, prefix="/recommendations", tags=["Career Recommendations"])
api_v1_router.include_router(recruiter.router, prefix="/recruiter", tags=["Recruiter Workflow"])
api_v1_router.include_router(insights.router, prefix="/insights", tags=["Market Intelligence"])
api_v1_router.include_router(ats.router, prefix="/ats", tags=["ATS Resume Checker"])


