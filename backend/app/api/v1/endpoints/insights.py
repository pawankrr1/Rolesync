"""API endpoints for Market Intelligence Dashboard.

Delivers descriptive workforce analytics aggregated exclusively from the
repository's seeded benchmark dataset (jobs.json, roles.json, skills.json, demo_candidates.json).

Guarantees:
- Zero live web-scraping.
- Every section contains its explicit data source context.
- Disclaimers state "Based on the current dataset".
- Predictive workforce forecasting is intentionally omitted.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.market_intelligence import (
    get_complete_market_intelligence,
    get_most_frequently_requested_skills,
    get_skills_by_role,
    get_skills_by_category,
    get_role_distribution,
    get_skill_gap_trends,
)

router = APIRouter()


@router.get(
    "/market-intelligence",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get aggregated market intelligence dashboard payload",
    description=(
        "Returns aggregated workforce intelligence across 5 views: "
        "(1) Most frequently requested skills, (2) Skills by role, "
        "(3) Skills by category, (4) Role distribution, (5) Skill-gap trends. "
        "Strictly uses the local seeded repository dataset with explicit data source contexts."
    ),
)
def get_market_intelligence_dashboard(
    top_n_skills: Optional[int] = Query(15, ge=1, le=100, description="Top N frequently requested skills"),
    role_id: Optional[str] = Query(None, description="Optional role filter for role-skills breakdown"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Compiles complete dashboard payload with metadata and source context."""
    return get_complete_market_intelligence(
        top_n_skills=top_n_skills,
        role_id=role_id,
        db=db,
    )


@router.get(
    "/frequently-requested-skills",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get most frequently requested skills in seeded job postings",
)
def get_frequently_demanded_skills(
    top_n: Optional[int] = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns top demanded skills across seeded job postings."""
    return get_most_frequently_requested_skills(top_n=top_n, db=db)


@router.get(
    "/skills-by-role",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get skills broken down by benchmark career role",
)
def get_role_skills_breakdown(
    role_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns required and preferred skills for benchmark roles."""
    return get_skills_by_role(role_id=role_id, db=db)


@router.get(
    "/skills-by-category",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get skills and requisition occurrences grouped by domain category",
)
def get_category_breakdown(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns skill counts and demand occurrences per technology category."""
    return get_skills_by_category(db=db)


@router.get(
    "/role-distribution",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get role and experience distribution in the seeded dataset",
)
def get_role_distribution_breakdown(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns job concentration across domains and experience bands."""
    return get_role_distribution(db=db)


@router.get(
    "/skill-gap-trends",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get skill-gap trends comparing job demand vs candidate profile supply",
)
def get_skill_gaps_breakdown(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns empirical skill-gap deltas across seeded jobs and candidate profiles."""
    return get_skill_gap_trends(db=db)
