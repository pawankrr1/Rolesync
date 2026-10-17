"""Explainable Candidate-Job Matching Engine.

Computes a deterministic, mathematically transparent score broken down into explicit features:
- Required Skill Coverage (default: 60%)
- Semantic / Domain Similarity (default: 20%)
- Experience & Depth Alignment (default: 10%)
- Preferred Skill Coverage (default: 10%)

Weights are fully configurable.
Zero opaque AI / LLM percentages: the final score is derived from explicit mathematical features
and is 100% reproducible.
"""

import re
from typing import Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, field_validator

from app.core.taxonomy import taxonomy, SkillDefinition
from app.core.extractor import ExtractedSkill
from app.core.role_engine import CareerRoleProfile, RoleSkillRequirement, role_engine


SYSTEM_DISCLAIMER = (
    "Career Intelligence provides decision support based on the available profile and dataset. "
    "It does not guarantee employment, hiring outcomes or career success."
)


# ---------------------------------------------------------------------------
# Scoring Configuration & Models
# ---------------------------------------------------------------------------

class MatchWeights(BaseModel):
    required_coverage: float = Field(0.60, ge=0.0, le=1.0, description="Weight for required skill coverage")
    semantic_similarity: float = Field(0.20, ge=0.0, le=1.0, description="Weight for semantic/domain similarity")
    experience_alignment: float = Field(0.10, ge=0.0, le=1.0, description="Weight for experience alignment")
    preferred_coverage: float = Field(0.10, ge=0.0, le=1.0, description="Weight for preferred skill coverage")


class SkillExplanation(BaseModel):
    skill: str = Field(..., description="Canonical skill name")
    status: str = Field(..., description="Match status: 'matched', 'partial', 'missing'")
    contribution: float = Field(..., description="Calculated fractional contribution to final match score")
    evidence: str = Field(..., description="Direct citation or rationale")
    category: Optional[str] = Field(None, description="Taxonomy category")
    is_required: bool = Field(True, description="Whether skill was required (True) or preferred (False)")
    why_missing: Optional[str] = Field(None, description="Explanation for why this skill was classified as missing or partial")


class SkillMatchDetail(BaseModel):
    skill_id: str
    canonical_name: str
    category: str
    status: str  # "strong_match", "partial_match", "missing"
    is_required: bool
    confidence: float
    evidence: List[str] = Field(default_factory=list)
    notes: str
    why_missing: Optional[str] = Field(None, description="Explanation for why this skill was classified as missing or partial")

    @field_validator("evidence", mode="before")
    @classmethod
    def _coerce_evidence(cls, v):
        if isinstance(v, str):
            return [v]
        return list(v) if v else []


class ScoreFactorContribution(BaseModel):
    factor_name: str
    raw_score: float  # 0 - 100
    weight: float      # e.g. 0.60
    weighted_score: float  # raw_score * weight
    max_possible_points: float  # 100 * weight
    explanation: str


class ExplainableMatchResult(BaseModel):
    final_match_score: float = Field(..., ge=0.0, le=100.0, description="Overall match score (0-100)")
    overall_match_score: float = Field(..., ge=0.0, le=100.0, description="Alias for final_match_score")
    score_grade: str = Field(..., description="Grade: Exceptional Match, High Alignment, Moderate Potential, Needs Upskilling")
    why_score: str = Field("", description="Primary answer to 'WHY?' this score was achieved")
    system_disclaimer: str = Field(
        SYSTEM_DISCLAIMER,
        description="Mandatory decision support and ethical disclaimer"
    )

    # Explicit component scores (0 - 100)
    required_skill_coverage: float = Field(..., description="Required skill coverage percentage (0-100)")
    preferred_skill_coverage: float = Field(..., description="Preferred skill coverage percentage (0-100)")
    semantic_similarity: float = Field(..., description="Semantic domain similarity percentage (0-100)")
    experience_alignment: float = Field(..., description="Experience alignment percentage (0-100)")

    # Explanation objects as specified
    strong_matches: List[SkillExplanation] = Field(default_factory=list)
    partial_matches: List[SkillExplanation] = Field(default_factory=list)
    missing_skills: List[SkillExplanation] = Field(default_factory=list)
    all_skill_explanations: List[SkillExplanation] = Field(default_factory=list)

    # Explainability narratives
    why_match: List[str] = Field(default_factory=list)
    why_not_match: List[str] = Field(default_factory=list)
    top_strengths: List[str] = Field(default_factory=list)
    top_gaps: List[str] = Field(default_factory=list)

    # Detailed factor breakdown
    factor_breakdown: List[ScoreFactorContribution] = Field(default_factory=list)

    # Backward compatibility with existing modules
    matched_required: List[SkillMatchDetail] = Field(default_factory=list)
    matched_preferred: List[SkillMatchDetail] = Field(default_factory=list)
    partial_skills: List[SkillMatchDetail] = Field(default_factory=list)
    missing_required: List[SkillMatchDetail] = Field(default_factory=list)
    missing_preferred: List[SkillMatchDetail] = Field(default_factory=list)
    all_skill_details: List[SkillMatchDetail] = Field(default_factory=list)
    explainability_narrative: str = ""
    weights_used: MatchWeights


# ---------------------------------------------------------------------------
# Normalization Helpers
# ---------------------------------------------------------------------------

CATEGORY_CANONICAL_MAP = {
    "ai/ml": "data_science_ai",
    "ai": "data_science_ai",
    "data science & ai": "data_science_ai",
    "data science and ai": "data_science_ai",
    "analytics": "analytics_bi",
    "analytics & bi": "analytics_bi",
    "analytics and bi": "analytics_bi",
    "bi": "analytics_bi",
    "cloud": "cloud_infra",
    "cloud & infrastructure": "cloud_infra",
    "cloud and infrastructure": "cloud_infra",
    "databases": "databases_storage",
    "databases & storage": "databases_storage",
    "devops": "devops_sre",
    "devops & sre": "devops_sre",
    "web": "web_development",
    "web development": "web_development",
    "data": "data_science_ai",
    "programming": "programming",
    "cybersecurity": "cybersecurity",
    "professional skills": "professional_skills",
}


def canonicalize_category(cat: str) -> str:
    clean = (cat or "").strip().lower()
    return CATEGORY_CANONICAL_MAP.get(clean, clean)


def normalize_education_tier(edu: Optional[Union[str, Dict]]) -> int:
    """Normalize education to a numeric tier: 0 (none/hs) to 4 (phd)."""
    if not edu:
        return 0
    text = ""
    if isinstance(edu, dict):
        text = f"{edu.get('level', '')} {edu.get('degree', '')} {edu.get('field', '')}".lower()
    else:
        text = str(edu).lower()

    if any(k in text for k in ("phd", "doctorate", "ph.d", "doctoral")):
        return 4
    if any(k in text for k in ("master", "ms", "m.s", "mtech", "m.tech", "mba", "m.sc", "msc", "postgraduate")):
        return 3
    if any(k in text for k in ("bachelor", "bs", "b.s", "btech", "b.tech", "be", "b.e", "b.sc", "bsc", "undergraduate", "degree")):
        return 2
    if any(k in text for k in ("diploma", "associate", "polytechnic")):
        return 1
    return 0


def normalize_experience_years(exp: Optional[Union[float, int, Dict, str]]) -> float:
    """Extract numeric experience years."""
    if exp is None:
        return 0.0
    if isinstance(exp, (int, float)):
        return float(exp)
    if isinstance(exp, dict):
        return float(exp.get("years", exp.get("experience_years", 0.0)))
    if isinstance(exp, str):
        match = re.search(r"(\d+(?:\.\d+)?)", exp)
        if match:
            return float(match.group(1))
    return 0.0


def normalize_candidate_skills(raw_skills: List[Union[ExtractedSkill, Dict, str]]) -> List[ExtractedSkill]:
    """Convert heterogeneous candidate skills (strings, dicts, ExtractedSkill) into standardized ExtractedSkill objects."""
    norm_skills: List[ExtractedSkill] = []
    seen_ids: Set[str] = set()

    for item in raw_skills:
        if isinstance(item, ExtractedSkill):
            if item.canonical_id not in seen_ids:
                norm_skills.append(item)
                seen_ids.add(item.canonical_id)
        elif isinstance(item, dict):
            clean_name = item.get("canonical_name") or item.get("name") or ""
            cid = item.get("canonical_id") or taxonomy.get_canonical_id(clean_name)
            skill_def = taxonomy.get_skill(cid) if cid else None
            cname = skill_def.name if skill_def else (clean_name or "Unknown")
            cat = item.get("category") or (skill_def.category if skill_def else "General")
            conf = float(item.get("confidence", 0.95))
            ev = item.get("evidence", f"{cname} detected in candidate profile")
            src = item.get("source", "resume")
            canon_id = cid or cname.lower().replace(" ", "_")

            if canon_id not in seen_ids:
                norm_skills.append(ExtractedSkill(
                    name=item.get("name", cname),
                    canonical_name=cname,
                    canonical_id=canon_id,
                    category=cat,
                    confidence=conf,
                    evidence=ev,
                    source=src,
                    frequency=int(item.get("frequency", 1)),
                    evidence_snippets=[ev]
                ))
                seen_ids.add(canon_id)
        elif isinstance(item, str):
            clean_term = item.strip()
            if not clean_term:
                continue
            cid = taxonomy.get_canonical_id(clean_term)
            skill_def = taxonomy.get_skill(cid) if cid else None
            cname = skill_def.name if skill_def else clean_term
            cat = skill_def.category if skill_def else "General"
            canon_id = cid or clean_term.lower().replace(" ", "_")

            if canon_id not in seen_ids:
                norm_skills.append(ExtractedSkill(
                    name=clean_term,
                    canonical_name=cname,
                    canonical_id=canon_id,
                    category=cat,
                    confidence=0.95,
                    evidence=f"{cname} verified in candidate skills",
                    source="resume",
                    frequency=1,
                    evidence_snippets=[f"{cname} verified in candidate skills"]
                ))
                seen_ids.add(canon_id)

    return norm_skills


def normalize_skill_requirements(
    raw_reqs: Optional[List[Union[RoleSkillRequirement, Dict, str]]],
    is_required: bool = True
) -> List[RoleSkillRequirement]:
    """Convert heterogeneous requirements into standardized RoleSkillRequirement objects."""
    if not raw_reqs:
        return []
    result: List[RoleSkillRequirement] = []
    seen: Set[str] = set()

    for item in raw_reqs:
        if isinstance(item, RoleSkillRequirement):
            if item.skill_id not in seen:
                result.append(item)
                seen.add(item.skill_id)
        elif isinstance(item, dict):
            s_name = item.get("canonical_name") or item.get("name") or item.get("skill") or ""
            cid = item.get("skill_id") or taxonomy.get_canonical_id(s_name)
            skill_def = taxonomy.get_skill(cid) if cid else None
            cname = skill_def.name if skill_def else s_name
            cat = item.get("category") or (skill_def.category if skill_def else "General")
            wt = float(item.get("weight", 1.0))
            lvl = item.get("level", "intermediate")
            canon_id = cid or s_name.lower().replace(" ", "_")

            if canon_id and canon_id not in seen:
                result.append(RoleSkillRequirement(
                    skill_id=canon_id,
                    canonical_name=cname,
                    category=cat,
                    weight=wt,
                    is_required=is_required,
                    level=lvl
                ))
                seen.add(canon_id)
        elif isinstance(item, str):
            clean_term = item.strip()
            if not clean_term:
                continue
            cid = taxonomy.get_canonical_id(clean_term)
            skill_def = taxonomy.get_skill(cid) if cid else None
            cname = skill_def.name if skill_def else clean_term
            cat = skill_def.category if skill_def else "General"
            canon_id = cid or clean_term.lower().replace(" ", "_")

            if canon_id not in seen:
                result.append(RoleSkillRequirement(
                    skill_id=canon_id,
                    canonical_name=cname,
                    category=cat,
                    weight=1.0,
                    is_required=is_required,
                    level="intermediate"
                ))
                seen.add(canon_id)

    return result


# ---------------------------------------------------------------------------
# Explainable Matching Engine
# ---------------------------------------------------------------------------

class ExplainableMatchingEngine:
    """Core mathematical candidate-job matching engine."""

    def __init__(self, default_weights: Optional[MatchWeights] = None):
        self.weights = default_weights or MatchWeights()
        self.taxonomy = taxonomy

    def calculate_match(
        self,
        candidate_skills: List[Union[ExtractedSkill, Dict, str]],
        target_role: Optional[Union[CareerRoleProfile, str]] = None,
        custom_weights: Optional[MatchWeights] = None,
        candidate_experience_years: Optional[Union[float, int, str]] = None,
        candidate_experience: Optional[Union[float, int, Dict, str]] = None,
        candidate_education: Optional[Union[Dict, str]] = None,
        required_skills: Optional[List[Union[RoleSkillRequirement, Dict, str]]] = None,
        preferred_skills: Optional[List[Union[RoleSkillRequirement, Dict, str]]] = None,
        target_experience_years: Optional[float] = None,
        target_education_level: Optional[Union[int, str]] = None,
    ) -> ExplainableMatchResult:
        # 1. Normalize scoring weights
        raw_w = custom_weights or self.weights
        total_w = raw_w.required_coverage + raw_w.preferred_coverage + raw_w.semantic_similarity + raw_w.experience_alignment
        if abs(total_w - 1.0) > 1e-4 and total_w > 0:
            w = MatchWeights(
                required_coverage=raw_w.required_coverage / total_w,
                preferred_coverage=raw_w.preferred_coverage / total_w,
                semantic_similarity=raw_w.semantic_similarity / total_w,
                experience_alignment=raw_w.experience_alignment / total_w
            )
        else:
            w = raw_w

        # 2. Normalize candidate profile
        norm_candidate_skills: List[ExtractedSkill] = normalize_candidate_skills(candidate_skills)
        cand_map: Dict[str, ExtractedSkill] = {s.canonical_id: s for s in norm_candidate_skills}
        cand_categories: Set[str] = {s.category for s in norm_candidate_skills}

        # Candidate experience (fallback hierarchy)
        exp_years = (
            normalize_experience_years(candidate_experience_years)
            if candidate_experience_years is not None
            else normalize_experience_years(candidate_experience)
        )
        cand_edu_tier = normalize_education_tier(candidate_education)

        # 3. Resolve Target Role & Job Requirements
        role_profile: Optional[CareerRoleProfile] = None
        if isinstance(target_role, str):
            role_profile = role_engine.get_role(target_role)
            if not role_profile:
                # Custom JD text fallback
                role_profile = role_engine.ingest_custom_job_description(target_role)
        elif isinstance(target_role, CareerRoleProfile):
            role_profile = target_role

        # Combine requirements
        role_required: List[RoleSkillRequirement] = []
        role_preferred: List[RoleSkillRequirement] = []

        if role_profile:
            role_required.extend(role_profile.required_skills)
            role_preferred.extend(role_profile.preferred_skills)

        # Explicit overrides take priority / merge
        if required_skills:
            explicit_req = normalize_skill_requirements(required_skills, is_required=True)
            existing_ids = {r.skill_id for r in explicit_req}
            # Add explicit ones, keeping non-overlapping from role profile
            role_required = explicit_req + [r for r in role_required if r.skill_id not in existing_ids]

        if preferred_skills:
            explicit_pref = normalize_skill_requirements(preferred_skills, is_required=False)
            existing_ids = {p.skill_id for p in explicit_pref}
            role_preferred = explicit_pref + [p for p in role_preferred if p.skill_id not in existing_ids]

        # Target experience
        req_exp_years = target_experience_years
        if req_exp_years is None:
            req_exp_years = float(role_profile.typical_experience_years) if role_profile else 2.0

        target_title = role_profile.title if role_profile else "Target Role Specification"

        # ---------------------------------------------------------------------------
        # FEATURE 1: Required Skill Coverage (Default: 60%)
        # ---------------------------------------------------------------------------
        total_req_weight = sum(r.weight for r in role_required) or 1.0
        earned_req_points = 0.0

        strong_explanations: List[SkillExplanation] = []
        partial_explanations: List[SkillExplanation] = []
        missing_explanations: List[SkillExplanation] = []
        all_explanations: List[SkillExplanation] = []

        matched_req_details: List[SkillMatchDetail] = []
        missing_req_details: List[SkillMatchDetail] = []
        partial_details: List[SkillMatchDetail] = []
        all_details: List[SkillMatchDetail] = []

        # If candidate has NO extracted skills at all
        has_skills = len(norm_candidate_skills) > 0

        for req in role_required:
            if has_skills and req.skill_id in cand_map:
                cand_skill = cand_map[req.skill_id]
                earned_req_points += req.weight * 1.0

                # Mathematical fractional contribution to overall score
                skill_contrib = round(w.required_coverage * (req.weight / total_req_weight), 4)

                ev_text = cand_skill.evidence or f"{req.canonical_name} detected in candidate profile."
                exp_obj = SkillExplanation(
                    skill=req.canonical_name,
                    status="matched",
                    contribution=skill_contrib,
                    evidence=ev_text,
                    category=req.category,
                    is_required=True
                )
                strong_explanations.append(exp_obj)
                all_explanations.append(exp_obj)

                detail = SkillMatchDetail(
                    skill_id=req.skill_id,
                    canonical_name=req.canonical_name,
                    category=req.category,
                    status="strong_match",
                    is_required=True,
                    confidence=cand_skill.confidence,
                    evidence=[ev_text],
                    notes=f"Direct match found with {int(cand_skill.confidence * 100)}% confidence."
                )
                matched_req_details.append(detail)
                all_details.append(detail)
            else:
                # Check for adjacent skills in taxonomy (Partial Match)
                skill_def = self.taxonomy.get_skill(req.skill_id)
                adjacent_found = [
                    self.taxonomy.get_skill(adj).name
                    for adj in (skill_def.adjacent_skills if skill_def else [])
                    if has_skills and adj in cand_map
                ]

                if has_skills and adjacent_found:
                    earned_req_points += req.weight * 0.45
                    skill_contrib = round(w.required_coverage * ((req.weight * 0.45) / total_req_weight), 4)

                    ev_text = f"Partial match: Candidate demonstrated adjacent competency in {', '.join(adjacent_found)}."
                    why_miss = (
                        f"Partially unmet for {target_title}. Candidate demonstrated foundational competency in "
                        f"{', '.join(adjacent_found)}, but direct production experience in {req.canonical_name} was not identified in the profile."
                    )
                    exp_obj = SkillExplanation(
                        skill=req.canonical_name,
                        status="partial",
                        contribution=skill_contrib,
                        evidence=ev_text,
                        category=req.category,
                        is_required=True,
                        why_missing=why_miss,
                    )
                    partial_explanations.append(exp_obj)
                    all_explanations.append(exp_obj)

                    detail = SkillMatchDetail(
                        skill_id=req.skill_id,
                        canonical_name=req.canonical_name,
                        category=req.category,
                        status="partial_match",
                        is_required=True,
                        confidence=0.55,
                        evidence=[ev_text],
                        notes=ev_text,
                        why_missing=why_miss,
                    )
                    partial_details.append(detail)
                    all_details.append(detail)
                else:
                    # Missing
                    ev_text = f"Required skill {req.canonical_name} not detected in candidate profile."
                    why_miss = (
                        f"Required benchmark skill for {target_title}. No direct keyword occurrences, equivalent aliases, "
                        f"or foundational prerequisite competencies were detected in the evaluated candidate profile."
                    )
                    exp_obj = SkillExplanation(
                        skill=req.canonical_name,
                        status="missing",
                        contribution=0.0,
                        evidence=ev_text,
                        category=req.category,
                        is_required=True,
                        why_missing=why_miss,
                    )
                    missing_explanations.append(exp_obj)
                    all_explanations.append(exp_obj)

                    detail = SkillMatchDetail(
                        skill_id=req.skill_id,
                        canonical_name=req.canonical_name,
                        category=req.category,
                        status="missing",
                        is_required=True,
                        confidence=0.0,
                        evidence=[],
                        notes=ev_text,
                        why_missing=why_miss,
                    )
                    missing_req_details.append(detail)
                    all_details.append(detail)

        if not has_skills or not role_required:
            raw_req_score = 0.0 if not has_skills else 100.0
        else:
            raw_req_score = min(100.0, (earned_req_points / total_req_weight) * 100.0)

        # ---------------------------------------------------------------------------
        # FEATURE 2: Preferred Skill Coverage (Default: 10%)
        # ---------------------------------------------------------------------------
        matched_pref_details: List[SkillMatchDetail] = []
        missing_pref_details: List[SkillMatchDetail] = []

        if role_preferred:
            total_pref_weight = sum(p.weight for p in role_preferred) or 1.0
            earned_pref_points = 0.0

            for pref in role_preferred:
                if has_skills and pref.skill_id in cand_map:
                    cand_skill = cand_map[pref.skill_id]
                    earned_pref_points += pref.weight * 1.0
                    skill_contrib = round(w.preferred_coverage * (pref.weight / total_pref_weight), 4)

                    ev_text = cand_skill.evidence or f"Bonus preferred skill {pref.canonical_name} detected."
                    exp_obj = SkillExplanation(
                        skill=pref.canonical_name,
                        status="matched",
                        contribution=skill_contrib,
                        evidence=ev_text,
                        category=pref.category,
                        is_required=False
                    )
                    strong_explanations.append(exp_obj)
                    all_explanations.append(exp_obj)

                    detail = SkillMatchDetail(
                        skill_id=pref.skill_id,
                        canonical_name=pref.canonical_name,
                        category=pref.category,
                        status="strong_match",
                        is_required=False,
                        confidence=cand_skill.confidence,
                        evidence=[ev_text],
                        notes=f"Bonus preferred skill matched with {int(cand_skill.confidence * 100)}% confidence."
                    )
                    matched_pref_details.append(detail)
                    all_details.append(detail)
                else:
                    # Check adjacent
                    skill_def = self.taxonomy.get_skill(pref.skill_id)
                    adjacent_found = [
                        self.taxonomy.get_skill(adj).name
                        for adj in (skill_def.adjacent_skills if skill_def else [])
                        if has_skills and adj in cand_map
                    ]

                    if has_skills and adjacent_found:
                        earned_pref_points += pref.weight * 0.45
                        skill_contrib = round(w.preferred_coverage * ((pref.weight * 0.45) / total_pref_weight), 4)
                        ev_text = f"Partial match on preferred skill {pref.canonical_name} via {', '.join(adjacent_found)}."

                        exp_obj = SkillExplanation(
                            skill=pref.canonical_name,
                            status="partial",
                            contribution=skill_contrib,
                            evidence=ev_text,
                            category=pref.category,
                            is_required=False
                        )
                        partial_explanations.append(exp_obj)
                        all_explanations.append(exp_obj)

                        detail = SkillMatchDetail(
                            skill_id=pref.skill_id,
                            canonical_name=pref.canonical_name,
                            category=pref.category,
                            status="partial_match",
                            is_required=False,
                            confidence=0.55,
                            evidence=[ev_text],
                            notes=ev_text
                        )
                        partial_details.append(detail)
                        all_details.append(detail)
                    else:
                        ev_text = f"Optional preferred skill {pref.canonical_name} not detected."
                        why_miss = f"Optional preferred differentiator for {target_title}. Not detected in candidate profile text or verified skills."
                        exp_obj = SkillExplanation(
                            skill=pref.canonical_name,
                            status="missing",
                            contribution=0.0,
                            evidence=ev_text,
                            category=pref.category,
                            is_required=False,
                            why_missing=why_miss,
                        )
                        missing_explanations.append(exp_obj)
                        all_explanations.append(exp_obj)

                        detail = SkillMatchDetail(
                            skill_id=pref.skill_id,
                            canonical_name=pref.canonical_name,
                            category=pref.category,
                            status="missing",
                            is_required=False,
                            confidence=0.0,
                            evidence=[],
                            notes=ev_text,
                            why_missing=why_miss,
                        )
                        missing_pref_details.append(detail)
                        all_details.append(detail)

            if not has_skills:
                raw_pref_score = 0.0
            else:
                raw_pref_score = min(100.0, (earned_pref_points / total_pref_weight) * 100.0)
        else:
            raw_pref_score = 100.0 if has_skills else 0.0

        # ---------------------------------------------------------------------------
        # FEATURE 3: Semantic / Category Taxonomy Similarity (Default: 20%)
        # ---------------------------------------------------------------------------
        role_categories = {canonicalize_category(r.category) for r in (role_required + role_preferred)}
        cand_norm_categories = {canonicalize_category(s.category) for s in norm_candidate_skills}

        if not has_skills:
            raw_semantic_score = 0.0
        elif role_categories:
            overlap = len(cand_norm_categories.intersection(role_categories))
            cat_overlap = overlap / len(role_categories)

            # In-domain skill distribution: candidate skills that belong to the role domain
            in_domain_count = sum(1 for s in norm_candidate_skills if canonicalize_category(s.category) in role_categories)
            domain_ratio = in_domain_count / max(1, len(norm_candidate_skills))

            # Factor skill match ratio
            total_role_skills = len(role_required) + len(role_preferred)
            matched_skills_count = len(matched_req_details) + len(matched_pref_details)
            skill_match_ratio = matched_skills_count / max(1, total_role_skills)

            raw_semantic_score = min(100.0, round((0.40 * skill_match_ratio + 0.35 * cat_overlap + 0.25 * domain_ratio) * 100.0, 1))
        else:
            raw_semantic_score = 75.0

        # ---------------------------------------------------------------------------
        # FEATURE 4: Experience & Education Alignment (Default: 10%)
        # ---------------------------------------------------------------------------
        if not has_skills and exp_years == 0.0 and cand_edu_tier == 0:
            raw_exp_score = 0.0
        else:
            # 1. Experience Years Alignment
            if req_exp_years <= 0.0:
                years_score = 100.0
            else:
                years_score = 100.0 if exp_years >= req_exp_years else min(100.0, (exp_years / req_exp_years) * 100.0)

            # 2. Evidence depth & skill count richness
            evidence_count = sum(len(s.evidence_snippets) if s.evidence_snippets else 1 for s in norm_candidate_skills)
            depth_ratio = min(1.0, (len(norm_candidate_skills) * 0.08) + (evidence_count * 0.04))
            depth_score = round(depth_ratio * 100.0, 1)

            # 3. Education tier (if provided)
            if candidate_education is not None:
                req_edu_tier = normalize_education_tier(target_education_level) or 2  # default bachelor
                edu_score = 100.0 if cand_edu_tier >= req_edu_tier else (cand_edu_tier / req_edu_tier) * 100.0
                raw_exp_score = min(100.0, round(0.60 * years_score + 0.20 * edu_score + 0.20 * depth_score, 1))
            else:
                raw_exp_score = min(100.0, round(0.75 * years_score + 0.25 * depth_score, 1))

        # ---------------------------------------------------------------------------
        # FINAL REPRODUCIBLE MATCH SCORE CALCULATION
        # ---------------------------------------------------------------------------
        weighted_req = raw_req_score * w.required_coverage
        weighted_pref = raw_pref_score * w.preferred_coverage
        weighted_sem = raw_semantic_score * w.semantic_similarity
        weighted_exp = raw_exp_score * w.experience_alignment

        overall_score = round(weighted_req + weighted_pref + weighted_sem + weighted_exp, 1)
        overall_score = max(0.0, min(100.0, overall_score))

        # If zero candidate skills detected, final score must be 0
        if not has_skills:
            overall_score = 0.0
            raw_req_score = 0.0
            raw_pref_score = 0.0
            raw_semantic_score = 0.0
            raw_exp_score = 0.0
            weighted_req = 0.0
            weighted_pref = 0.0
            weighted_sem = 0.0
            weighted_exp = 0.0

        # Score Grade
        if overall_score >= 80.0:
            score_grade = "Exceptional Match"
        elif overall_score >= 65.0:
            score_grade = "High Alignment"
        elif overall_score >= 40.0:
            score_grade = "Moderate Potential"
        else:
            score_grade = "Needs Upskilling"

        # ---------------------------------------------------------------------------
        # NARRATIVES & EXPLANATION GENERATION
        # ---------------------------------------------------------------------------
        why_match: List[str] = []
        why_not_match: List[str] = []

        # Positive reasons
        matched_req_names = [s.canonical_name for s in matched_req_details]
        if matched_req_names:
            why_match.append(f"Strong direct match on core requirements: {', '.join(matched_req_names)}.")

        matched_pref_names = [s.canonical_name for s in matched_pref_details]
        if matched_pref_names:
            why_match.append(f"Bonus preferred skills detected: {', '.join(matched_pref_names)}.")

        if partial_details:
            partial_names = [s.canonical_name for s in partial_details]
            why_match.append(f"Partial match: Demonstrated adjacent competencies providing partial credit in: {', '.join(partial_names)}.")

        if exp_years >= req_exp_years and exp_years > 0:
            why_match.append(f"Experience level ({exp_years} yrs) meets or exceeds target requirement ({req_exp_years} yrs).")

        common_cats = cand_categories.intersection(role_categories)
        if common_cats:
            why_match.append(f"Strong domain category alignment across {', '.join(sorted(list(common_cats)))}.")

        # Negative / Gap reasons
        missing_req_names = [s.canonical_name for s in missing_req_details]
        if missing_req_names:
            why_not_match.append(f"Missing core required skills: {', '.join(missing_req_names)}.")

        missing_pref_names = [s.canonical_name for s in missing_pref_details]
        if missing_pref_names:
            why_not_match.append(f"Missing optional preferred skills: {', '.join(missing_pref_names)}.")

        if exp_years < req_exp_years and has_skills:
            why_not_match.append(f"Experience ({exp_years} yrs) is below recommended requirement ({req_exp_years} yrs).")

        if not has_skills:
            why_not_match.append("No verified skills detected in candidate profile.")

        # Top Strengths & Gaps
        sorted_strengths = sorted(strong_explanations, key=lambda s: s.contribution, reverse=True)
        top_strengths = [s.skill for s in sorted_strengths[:5]]

        sorted_gaps = sorted(
            [e for e in all_explanations if e.status in ("missing", "partial") and e.is_required],
            key=lambda e: (0 if e.status == "missing" else 1),
        )
        top_gaps = [g.skill for g in sorted_gaps[:5]]

        # Factor Breakdown objects
        breakdown = [
            ScoreFactorContribution(
                factor_name="Required Skill Coverage",
                raw_score=round(raw_req_score, 1),
                weight=w.required_coverage,
                weighted_score=round(weighted_req, 1),
                max_possible_points=round(100.0 * w.required_coverage, 1),
                explanation=f"Directly satisfied {len(matched_req_details)} of {len(role_required)} required competencies, with {len(partial_details)} partial matches."
            ),
            ScoreFactorContribution(
                factor_name="Semantic Domain Overlap",
                raw_score=round(raw_semantic_score, 1),
                weight=w.semantic_similarity,
                weighted_score=round(weighted_sem, 1),
                max_possible_points=round(100.0 * w.semantic_similarity, 1),
                explanation=f"Domain overlap in {len(common_cats)} of {len(role_categories)} taxonomy domains required for {target_title}."
            ),
            ScoreFactorContribution(
                factor_name="Experience & Depth Alignment",
                raw_score=round(raw_exp_score, 1),
                weight=w.experience_alignment,
                weighted_score=round(weighted_exp, 1),
                max_possible_points=round(100.0 * w.experience_alignment, 1),
                explanation=f"Evaluated {exp_years} years experience against {req_exp_years} target years with verified evidence depth."
            ),
            ScoreFactorContribution(
                factor_name="Preferred Skill Coverage",
                raw_score=round(raw_pref_score, 1),
                weight=w.preferred_coverage,
                weighted_score=round(weighted_pref, 1),
                max_possible_points=round(100.0 * w.preferred_coverage, 1),
                explanation=f"Fulfilled {len(matched_pref_details)} of {len(role_preferred)} nice-to-have preferred skills."
            ),
        ]

        total_priority = len(role_required)
        matched_priority = len(matched_req_details) + len(partial_details)
        if total_priority > 0:
            why_score = f"Your score is {overall_score:.0f}% because {matched_priority} of {total_priority} high-priority skills were matched or partially matched."
        else:
            why_score = f"Your score is {overall_score:.0f}% based on overall domain compatibility with {target_title}."

        narrative = (
            f"{why_score} Mathematically derived from "
            f"Required Skills ({round(weighted_req, 1)} pts), Semantic Similarity ({round(weighted_sem, 1)} pts), "
            f"Experience Alignment ({round(weighted_exp, 1)} pts), and Preferred Skills ({round(weighted_pref, 1)} pts)."
        )

        return ExplainableMatchResult(
            final_match_score=overall_score,
            overall_match_score=overall_score,
            score_grade=score_grade,
            why_score=why_score,
            system_disclaimer=SYSTEM_DISCLAIMER,
            required_skill_coverage=round(raw_req_score, 1),
            preferred_skill_coverage=round(raw_pref_score, 1),
            semantic_similarity=round(raw_semantic_score, 1),
            experience_alignment=round(raw_exp_score, 1),
            strong_matches=strong_explanations,
            partial_matches=partial_explanations,
            missing_skills=missing_explanations,
            all_skill_explanations=all_explanations,
            why_match=why_match,
            why_not_match=why_not_match,
            top_strengths=top_strengths,
            top_gaps=top_gaps,
            factor_breakdown=breakdown,
            matched_required=matched_req_details,
            matched_preferred=matched_pref_details,
            partial_skills=partial_details,
            missing_required=missing_req_details,
            missing_preferred=missing_pref_details,
            all_skill_details=all_details,
            explainability_narrative=narrative,
            weights_used=w
        )


matching_engine = ExplainableMatchingEngine()
