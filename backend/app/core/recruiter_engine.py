"""Recruiter Screening & Candidate Ranking Intelligence Engine.

Orchestrates multi-candidate evaluation against job requirements:
1. Ingests or parses Job Description (text or document)
2. Extracts and normalizes required and preferred skills
3. Evaluates candidate profiles against job requisitions using deterministic 4-factor scoring:
   - Required Skill Coverage (60%)
   - Semantic Domain Overlap (20%)
   - Experience & Depth Alignment (10%)
   - Preferred Skill Coverage (10%)
4. Ranks candidates descending by explainable match score
5. Extracts and verifies authentic resume evidence citations (or explicit fallback note)
6. Computes deterministic Hiring Risk indicators (Low, Medium, High)
7. Identifies Adjacent Talent / Near-matches with skill bridge explanations
8. Provides side-by-side Candidate Comparison with grounded recommendations
9. Computes Applicant Pool Skill Coverage & Common Shortages
10. Enforces ethical compliance:
    - Never claims a candidate is objectively the "best"
    - Emphasizes measured skill alignment within this dataset
    - Grounded decision support disclaimer
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field

from app.core.taxonomy import taxonomy
from app.core.extractor import extractor, ExtractedSkill
from app.core.role_engine import role_engine, CareerRoleProfile, RoleSkillRequirement
from app.core.matching_engine import (
    matching_engine,
    MatchWeights,
    ExplainableMatchResult,
    SkillExplanation,
    normalize_candidate_skills,
)
from app.utils.text_cleaner import extract_sentences


DISCLAIMER_TEXT = (
    "RoleSync Career Intelligence provides decision support based on the available candidate profile and dataset. "
    "It does not guarantee employment, hiring outcomes, or career success. "
    "This system is an explainable decision support tool designed to assist recruiters by analyzing explicit skill alignment "
    "from verified resume text. It is decision support, not an automated hiring decision. "
    "A high score represents the highest measured skill alignment within this dataset."
)

TOP_CANDIDATE_STATEMENT = "Highest measured skill alignment in this dataset."

RESPONSIBLE_MATCHING_TEXT = (
    "RoleSync is designed to prioritize job-relevant evidence. Candidate rankings focus strictly on "
    "verified skill competencies, experience alignment, and job-specific requirements. "
    "RoleSync does not use demographic attributes (such as gender, age, religion, caste, photographs, or personal PII) "
    "in any scoring algorithm."
)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class CandidateInputPayload(BaseModel):
    """Candidate representation for batch evaluation."""
    id: Optional[str] = None
    name: str = "Candidate"
    email: Optional[str] = None
    filename: Optional[str] = "resume.pdf"
    current_title: Optional[str] = None
    location: Optional[str] = None
    resume_text: Optional[str] = None
    candidate_skills: Optional[List[Union[ExtractedSkill, Dict[str, Any], str]]] = Field(default_factory=list)
    experience_years: Optional[float] = 2.0
    education: Optional[Union[Dict[str, Any], str]] = None
    is_demo: bool = False


class SkillEvidenceItem(BaseModel):
    skill: str
    status: str  # 'strong', 'partial', 'missing'
    evidence: str
    has_direct_quote: bool = True


class HiringRiskAssessment(BaseModel):
    level: str  # "LOW RISK", "MEDIUM RISK", "HIGH RISK"
    badge_variant: str  # "success", "warning", "error"
    indicators: List[str]
    rationale: str


class AdjacentTalentInfo(BaseModel):
    is_adjacent: bool = False
    source_role: Optional[str] = None
    near_match_label: Optional[str] = None
    bridge_skills: List[str] = Field(default_factory=list)
    rationale: Optional[str] = None


class CandidateDetailedExplanation(BaseModel):
    """Detailed explanation formatted for recruiter inspection modal."""
    match_score_display: str
    matched: List[str]
    partial: List[str]
    missing: List[str]
    matched_details: List[SkillExplanation] = Field(default_factory=list)
    partial_details: List[SkillExplanation] = Field(default_factory=list)
    missing_details: List[SkillExplanation] = Field(default_factory=list)
    why_match: List[str] = Field(default_factory=list)
    why_not_match: List[str] = Field(default_factory=list)
    top_strengths: List[str] = Field(default_factory=list)
    top_gaps: List[str] = Field(default_factory=list)
    factor_breakdown: Dict[str, float] = Field(default_factory=dict)
    evidence_list: List[SkillEvidenceItem] = Field(default_factory=list)


class RankedCandidateItem(BaseModel):
    """Ranked candidate entry displayed on recruiter leaderboard."""
    rank: int
    candidate_id: str
    name: str
    email: Optional[str] = None
    current_title: Optional[str] = None
    filename: str
    match_score: float
    score_grade: str
    required_skill_coverage_ratio: str  # e.g. "5/5"
    required_skills_count: int
    matched_required_count: int
    preferred_skill_coverage_ratio: str  # e.g. "2/3"
    strong_skills: List[str]
    partial_skills: List[str]
    missing_skills: List[str]
    experience_years: float
    experience_display: str
    experience_fit_label: str  # "Strong", "Good", "Moderate", "Limited"
    top_skill_gap: str
    recommendation_status: str  # "Recommended", "Review", "Consider Bridge"
    hiring_risk: HiringRiskAssessment
    adjacent_talent: AdjacentTalentInfo
    reason: str
    alignment_statement: str
    detailed_explanation: CandidateDetailedExplanation
    resume_text: Optional[str] = None


class RecruiterRankResponse(BaseModel):
    """Response containing ranked candidates, extracted role requirements, and ethical disclaimers."""
    job_title: str
    required_skills: List[str]
    preferred_skills: List[str]
    total_candidates_evaluated: int
    ranked_candidates: List[RankedCandidateItem]
    top_candidate_statement: str = TOP_CANDIDATE_STATEMENT
    disclaimer: str = DISCLAIMER_TEXT
    responsible_matching: str = RESPONSIBLE_MATCHING_TEXT


class CandidateComparisonItem(BaseModel):
    candidate_id: str
    name: str
    current_title: Optional[str] = None
    match_score: float
    required_coverage_ratio: str
    preferred_coverage_ratio: str
    experience_fit: str
    skill_gap_tier: str  # "Low", "Medium", "High"
    top_gaps: List[str]
    hiring_risk_level: str
    recommendation: str
    key_evidence: List[str] = Field(default_factory=list)


class CandidateComparisonResponse(BaseModel):
    job_title: str
    required_skills: List[str]
    preferred_skills: List[str]
    candidates: List[CandidateComparisonItem]
    recommended_candidate_id: str
    recommended_candidate_name: str
    recommendation_reason: str
    disclaimer: str = DISCLAIMER_TEXT


class ApplicantSkillCoverageItem(BaseModel):
    skill: str
    is_required: bool
    applicant_count: int
    total_applicants: int
    coverage_percentage: float


class RecruiterInsightsResponse(BaseModel):
    job_title: str
    total_applicants_evaluated: int
    skill_coverage: List[ApplicantSkillCoverageItem]
    most_common_gap_skill: Optional[str] = None
    most_common_gap_percentage: Optional[float] = None
    shortage_insight_narrative: str
    market_trend_linkage: Optional[str] = None
    is_sample_dataset: bool = True
    disclaimer: str = DISCLAIMER_TEXT


# ---------------------------------------------------------------------------
# Recruiter Engine Implementation
# ---------------------------------------------------------------------------

class RecruiterEngine:
    """Core multi-candidate ranking intelligence engine."""

    def __init__(self):
        self.extractor = extractor
        self.taxonomy = taxonomy
        self.role_engine = role_engine
        self.matching_engine = matching_engine

    def extract_job_skills(
        self,
        job_description_text: str,
        role_title: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Extracts and normalizes required and preferred skills from a raw job description."""
        report = self.extractor.extract_from_text(job_description_text, source="job_description")

        req_skills: List[str] = []
        pref_skills: List[str] = []

        text_lower = job_description_text.lower()
        preferred_markers = [
            "preferred", "plus", "bonus", "nice to have", "good to have",
            "desired", "optional", "beneficial", "advantageous"
        ]

        seen_canonical = set()

        for skill in report.skills:
            name = skill.canonical_name
            if name.lower() in seen_canonical:
                continue
            seen_canonical.add(name.lower())

            # Check if skill context is close to preferred markers
            is_pref = any(
                marker in text_lower and marker in skill.evidence.lower()
                for marker in preferred_markers
            )
            if is_pref:
                pref_skills.append(name)
            else:
                req_skills.append(name)

        # Fallback balancing if no skills separated
        if not req_skills and report.skills:
            for i, s in enumerate(report.skills):
                if i < 5:
                    req_skills.append(s.canonical_name)
                else:
                    pref_skills.append(s.canonical_name)

        # Remove duplicates while preserving order
        def _unique(lst):
            seen = set()
            res = []
            for item in lst:
                if item.lower() not in seen:
                    seen.add(item.lower())
                    res.append(item)
            return res

        return {
            "required_skills": _unique(req_skills),
            "preferred_skills": _unique(pref_skills),
        }

    def _extract_evidence_for_skill(
        self,
        skill_name: str,
        resume_text: Optional[str],
        extracted_skills: Optional[List[ExtractedSkill]] = None
    ) -> tuple:
        """Finds genuine sentence evidence from candidate resume text.
        
        Strict rule: Never fabricate quotes. If not found in text, return
        explicit uncaptured evidence note.
        """
        if not resume_text or not resume_text.strip():
            return (
                "Skill detected from resume profile, but supporting text evidence was not captured.",
                False
            )

        # Check extracted skills first
        if extracted_skills:
            for s in extracted_skills:
                if s.canonical_name.lower() == skill_name.lower() or s.name.lower() == skill_name.lower():
                    if s.evidence and len(s.evidence.strip()) > 10:
                        return (s.evidence.strip(), True)
                    if s.evidence_snippets:
                        return (s.evidence_snippets[0].strip(), True)

        # Search resume sentences
        sentences = extract_sentences(resume_text)
        skill_tokens = [t.lower() for t in re.split(r"[\s_]+", skill_name) if len(t) > 2]
        if not skill_tokens:
            skill_tokens = [skill_name.lower()]

        for sent in sentences:
            sent_lower = sent.lower()
            if any(re.search(r"\b" + re.escape(tok) + r"\b", sent_lower) for tok in skill_tokens):
                # Clean and return sentence
                clean_sent = re.sub(r"^[•\*\-\s]+", "", sent).strip()
                if len(clean_sent) > 15:
                    return (clean_sent, True)

        return (
            "Skill detected from resume, but supporting evidence was not captured.",
            False
        )

    def _compute_hiring_risk(
        self,
        required_coverage: float,
        experience_alignment: float,
        missing_required_count: int,
        total_required_count: int,
        top_gap: str,
    ) -> HiringRiskAssessment:
        """Deterministic, documented hiring risk calculation."""
        req_ratio = (
            (total_required_count - missing_required_count) / total_required_count
            if total_required_count > 0 else 1.0
        )

        if req_ratio >= 0.80 and experience_alignment >= 65.0:
            return HiringRiskAssessment(
                level="LOW RISK",
                badge_variant="success",
                indicators=[
                    f"{total_required_count - missing_required_count}/{total_required_count} required skills",
                    "Strong experience alignment",
                    "Minimal skill gap",
                ],
                rationale="Comprehensive coverage of core required competencies with strong domain experience fit."
            )
        elif req_ratio >= 0.50 or missing_required_count <= 2:
            gap_note = f"{top_gap} gap" if top_gap != "None" else "Partial gap"
            return HiringRiskAssessment(
                level="MEDIUM RISK",
                badge_variant="warning",
                indicators=[
                    f"{total_required_count - missing_required_count}/{total_required_count} required skills",
                    "Partial experience alignment",
                    gap_note,
                ],
                rationale=f"Candidate satisfies foundational competencies; targeted onboarding will bridge {top_gap}."
            )
        else:
            return HiringRiskAssessment(
                level="HIGH RISK",
                badge_variant="error",
                indicators=[
                    f"{total_required_count - missing_required_count}/{total_required_count} required skills",
                    "Multiple core gaps",
                    "Limited relevant experience",
                ],
                rationale="Multiple core requirements are missing with substantial domain and experience gaps."
            )

    def _detect_adjacent_talent(
        self,
        candidate_title: Optional[str],
        strong_skills: List[str],
        missing_skills: List[str],
        target_role_title: str,
        match_score: float
    ) -> AdjacentTalentInfo:
        """Identifies candidates from adjacent career disciplines with transferable skills."""
        title_lower = (candidate_title or "").lower()
        target_lower = target_role_title.lower()

        # Known strategic career adjacent transitions
        adjacent_pairs = [
            ("data analyst", "data scientist", "Machine Learning", "Already matches core analytical and statistical skills, requiring a focused bridge in Machine Learning."),
            ("data analyst", "machine learning", "Machine Learning & Python Pipelines", "Solid quantitative foundation; requires a bridge in production ML algorithms."),
            ("backend", "machine learning", "Production ML Frameworks", "Strong software engineering and API foundation; requires an ML modeling bridge."),
            ("frontend", "fullstack", "Node.js & Database Architecture", "Excellent UI engineering; bridgeable transition into backend services."),
            ("devops", "cloud", "Multi-region Infrastructure", "Container and CI/CD mastery; ready for deeper cloud architecture transition."),
            ("software engineer", "backend", "Distributed Data Stores", "Solid algorithmic foundations; ready for specialized backend architecture."),
        ]

        for src, tgt, bridge_topic, narrative in adjacent_pairs:
            if src in title_lower and (tgt in target_lower or src != target_lower):
                if match_score >= 65.0:
                    return AdjacentTalentInfo(
                        is_adjacent=True,
                        source_role=candidate_title or src.title(),
                        near_match_label="Near Match",
                        bridge_skills=missing_skills[:2] if missing_skills else [bridge_topic],
                        rationale=narrative
                    )

        # General adjacent detection based on skill overlap
        if 65.0 <= match_score < 85.0 and len(strong_skills) >= 3 and 1 <= len(missing_skills) <= 2:
            return AdjacentTalentInfo(
                is_adjacent=True,
                source_role=candidate_title or "Adjacent Background",
                near_match_label="Near Match",
                bridge_skills=missing_skills[:2],
                rationale=f"Matches {len(strong_skills)} core skills; requires a small bridge in {', '.join(missing_skills[:2])}."
            )

        return AdjacentTalentInfo(is_adjacent=False)

    def rank_candidates(
        self,
        candidates: List[CandidateInputPayload],
        job_description_text: Optional[str] = None,
        job_title: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        target_experience_years: Optional[float] = 3.0,
        weights: Optional[MatchWeights] = None,
    ) -> RecruiterRankResponse:
        """Ranks candidates against job requirements with explainable scoring."""
        title = job_title or "Target Job Specification"

        # 1. Resolve role requirements
        active_req_skills: List[str] = list(required_skills or [])
        active_pref_skills: List[str] = list(preferred_skills or [])

        if job_description_text and job_description_text.strip():
            extracted_jd = self.extract_job_skills(job_description_text, role_title=title)
            if not active_req_skills:
                active_req_skills = extracted_jd["required_skills"]
            if not active_pref_skills:
                active_pref_skills = extracted_jd["preferred_skills"]

        if not active_req_skills and not active_pref_skills:
            active_req_skills = ["Python", "SQL", "Machine Learning"]

        evaluated_candidates: List[Dict[str, Any]] = []

        for idx, cand in enumerate(candidates):
            cand_id = cand.id or f"cand_{idx + 1:02d}"
            cand_name = cand.name or f"Candidate {idx + 1}"
            filename = cand.filename or f"resume_{idx + 1}.pdf"
            exp_years = cand.experience_years if cand.experience_years is not None else 2.0

            # Resolve candidate skills
            skills_payload: List[Union[ExtractedSkill, Dict, str]] = list(cand.candidate_skills or [])
            ext_report_skills: List[ExtractedSkill] = []
            if not skills_payload and cand.resume_text and cand.resume_text.strip():
                ext_report = self.extractor.extract_from_text(cand.resume_text, source="resume")
                skills_payload = ext_report.skills
                ext_report_skills = ext_report.skills
            elif cand.resume_text and cand.resume_text.strip():
                ext_report = self.extractor.extract_from_text(cand.resume_text, source="resume")
                ext_report_skills = ext_report.skills

            # Deterministic 4-Factor Matching Engine
            match_res: ExplainableMatchResult = self.matching_engine.calculate_match(
                candidate_skills=skills_payload,
                required_skills=active_req_skills,
                preferred_skills=active_pref_skills,
                target_experience_years=target_experience_years or 3.0,
                candidate_experience=exp_years,
                candidate_education=cand.education,
                custom_weights=weights,
            )

            strong_names = [m.skill for m in match_res.strong_matches]
            partial_names = [p.skill for p in match_res.partial_matches]
            missing_names = [m.skill for m in match_res.missing_skills if m.is_required]
            if not missing_names:
                missing_names = [m.skill for m in match_res.missing_skills]

            # Build genuine evidence list for candidate
            evidence_items: List[SkillEvidenceItem] = []
            for skill_name in strong_names:
                ev_quote, has_quote = self._extract_evidence_for_skill(
                    skill_name, cand.resume_text, ext_report_skills
                )
                evidence_items.append(SkillEvidenceItem(
                    skill=skill_name,
                    status="strong",
                    evidence=ev_quote,
                    has_direct_quote=has_quote,
                ))

            for skill_name in partial_names:
                ev_quote, has_quote = self._extract_evidence_for_skill(
                    skill_name, cand.resume_text, ext_report_skills
                )
                evidence_items.append(SkillEvidenceItem(
                    skill=skill_name,
                    status="partial",
                    evidence=ev_quote,
                    has_direct_quote=has_quote,
                ))

            # Coverage ratios
            total_req = len(active_req_skills)
            matched_req = len([s for s in strong_names if s in active_req_skills])
            req_coverage_ratio = f"{matched_req}/{total_req}"

            total_pref = len(active_pref_skills)
            matched_pref = len([s for s in strong_names if s in active_pref_skills])
            pref_coverage_ratio = f"{matched_pref}/{total_pref}" if total_pref > 0 else "N/A"

            # Experience fit label
            if match_res.experience_alignment >= 85.0:
                exp_fit_label = "Strong"
            elif match_res.experience_alignment >= 65.0:
                exp_fit_label = "Good"
            elif match_res.experience_alignment >= 45.0:
                exp_fit_label = "Moderate"
            else:
                exp_fit_label = "Limited"

            # Top skill gap
            top_gap = missing_names[0] if missing_names else "None"

            # Deterministic Hiring Risk Assessment
            hiring_risk = self._compute_hiring_risk(
                match_res.required_skill_coverage,
                match_res.experience_alignment,
                len(missing_names),
                total_req,
                top_gap
            )

            # Adjacent talent detection
            adjacent_info = self._detect_adjacent_talent(
                cand.current_title,
                strong_names,
                missing_names,
                title,
                match_res.final_match_score
            )

            # Grounded recommendation status
            if match_res.final_match_score >= 85.0 and matched_req == total_req:
                rec_status = "Recommended"
            elif match_res.final_match_score >= 70.0:
                rec_status = "Review"
            elif adjacent_info.is_adjacent:
                rec_status = "Consider Bridge"
            else:
                rec_status = "Review"

            # Detailed Explanation Structure
            score_rounded = round(match_res.final_match_score)
            match_display = f"{score_rounded}% Match"

            # Build grounded why_not_match ("Why this candidate ranks lower")
            why_not_list: List[str] = []
            if missing_names:
                for gap in missing_names[:3]:
                    why_not_list.append(f"Missing verified requirement in {gap}.")
            if partial_names:
                why_not_list.append(f"Partial evidence for {', '.join(partial_names[:2])}.")
            if match_res.experience_alignment < 70.0:
                why_not_list.append(f"Experience ({exp_years:.1f} yrs) below target requisition.")

            detailed_expl = CandidateDetailedExplanation(
                match_score_display=match_display,
                matched=strong_names,
                partial=partial_names,
                missing=missing_names,
                matched_details=match_res.strong_matches,
                partial_details=match_res.partial_matches,
                missing_details=match_res.missing_skills,
                why_match=match_res.why_match,
                why_not_match=why_not_list if why_not_list else ["Full core alignment achieved."],
                top_strengths=match_res.top_strengths,
                top_gaps=match_res.top_gaps,
                factor_breakdown={
                    "required_skill_coverage": match_res.required_skill_coverage,
                    "semantic_similarity": match_res.semantic_similarity,
                    "experience_alignment": match_res.experience_alignment,
                    "preferred_skill_coverage": match_res.preferred_skill_coverage,
                },
                evidence_list=evidence_items,
            )

            # Grounded reason text
            if strong_names and not missing_names:
                reason_str = f"Demonstrates comprehensive coverage across core requirements ({', '.join(strong_names[:3])})."
            elif strong_names:
                reason_str = (
                    f"Strong alignment in {', '.join(strong_names[:3])}; "
                    f"upskilling needed in {missing_names[0] if missing_names else 'supplementary tools'}."
                )
            else:
                reason_str = "Significant skill gaps detected against core job requirements."

            evaluated_candidates.append({
                "candidate_id": cand_id,
                "name": cand_name,
                "email": cand.email,
                "current_title": cand.current_title,
                "filename": filename,
                "match_score": match_res.final_match_score,
                "score_grade": match_res.score_grade,
                "required_skill_coverage_ratio": req_coverage_ratio,
                "required_skills_count": total_req,
                "matched_required_count": matched_req,
                "preferred_skill_coverage_ratio": pref_coverage_ratio,
                "strong_skills": strong_names,
                "partial_skills": partial_names,
                "missing_skills": missing_names,
                "experience_years": exp_years,
                "experience_display": f"{exp_years:.1f} yrs",
                "experience_fit_label": exp_fit_label,
                "top_skill_gap": top_gap,
                "recommendation_status": rec_status,
                "hiring_risk": hiring_risk,
                "adjacent_talent": adjacent_info,
                "reason": reason_str,
                "detailed_explanation": detailed_expl,
                "resume_text": cand.resume_text,
            })

        # 3. Sort candidates descending by match_score
        evaluated_candidates.sort(key=lambda c: c["match_score"], reverse=True)

        # 4. Assign ranks and ethical statements
        ranked_list: List[RankedCandidateItem] = []
        for i, c in enumerate(evaluated_candidates):
            rank_num = i + 1
            if rank_num == 1:
                statement = TOP_CANDIDATE_STATEMENT
            else:
                statement = f"Ranked #{rank_num} based on measured skill overlap in this dataset."

            ranked_list.append(
                RankedCandidateItem(
                    rank=rank_num,
                    candidate_id=c["candidate_id"],
                    name=c["name"],
                    email=c["email"],
                    current_title=c["current_title"],
                    filename=c["filename"],
                    match_score=round(c["match_score"], 1),
                    score_grade=c["score_grade"],
                    required_skill_coverage_ratio=c["required_skill_coverage_ratio"],
                    required_skills_count=c["required_skills_count"],
                    matched_required_count=c["matched_required_count"],
                    preferred_skill_coverage_ratio=c["preferred_skill_coverage_ratio"],
                    strong_skills=c["strong_skills"],
                    partial_skills=c["partial_skills"],
                    missing_skills=c["missing_skills"],
                    experience_years=c["experience_years"],
                    experience_display=c["experience_display"],
                    experience_fit_label=c["experience_fit_label"],
                    top_skill_gap=c["top_skill_gap"],
                    recommendation_status=c["recommendation_status"],
                    hiring_risk=c["hiring_risk"],
                    adjacent_talent=c["adjacent_talent"],
                    reason=c["reason"],
                    alignment_statement=statement,
                    detailed_explanation=c["detailed_explanation"],
                    resume_text=c["resume_text"],
                )
            )

        return RecruiterRankResponse(
            job_title=title,
            required_skills=active_req_skills,
            preferred_skills=active_pref_skills,
            total_candidates_evaluated=len(ranked_list),
            ranked_candidates=ranked_list,
            top_candidate_statement=TOP_CANDIDATE_STATEMENT,
            disclaimer=DISCLAIMER_TEXT,
            responsible_matching=RESPONSIBLE_MATCHING_TEXT,
        )

    def compare_candidates(
        self,
        ranked_items: List[RankedCandidateItem],
        job_title: str,
        required_skills: List[str],
        preferred_skills: List[str],
    ) -> CandidateComparisonResponse:
        """Compares candidates side-by-side with a deterministic, mathematically justified recommendation."""
        if not ranked_items:
            raise ValueError("No candidates provided for comparison.")

        comparison_items: List[CandidateComparisonItem] = []
        for c in ranked_items:
            # Skill gap tier
            missing_count = len(c.missing_skills)
            if missing_count == 0:
                gap_tier = "Low"
            elif missing_count <= 2:
                gap_tier = "Medium"
            else:
                gap_tier = "High"

            key_evidence_snippets = [
                e.evidence for e in c.detailed_explanation.evidence_list if e.has_direct_quote
            ][:3]

            comparison_items.append(CandidateComparisonItem(
                candidate_id=c.candidate_id,
                name=c.name,
                current_title=c.current_title,
                match_score=c.match_score,
                required_coverage_ratio=c.required_skill_coverage_ratio,
                preferred_coverage_ratio=c.preferred_skill_coverage_ratio,
                experience_fit=c.experience_fit_label,
                skill_gap_tier=gap_tier,
                top_gaps=c.missing_skills[:3],
                hiring_risk_level=c.hiring_risk.level,
                recommendation=c.recommendation_status,
                key_evidence=key_evidence_snippets,
            ))

        # Deterministic Recommendation:
        # 1. Candidate with highest required skill coverage
        # 2. Tie-break: lowest missing required skills
        # 3. Tie-break: highest overall match score
        best = max(
            ranked_items,
            key=lambda x: (x.matched_required_count, -len(x.missing_skills), x.match_score)
        )

        reason = (
            f"Highest required-skill coverage ({best.required_skill_coverage_ratio}) "
            f"with the smallest identified skill gap among evaluated profiles."
        )

        return CandidateComparisonResponse(
            job_title=job_title,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            candidates=comparison_items,
            recommended_candidate_id=best.candidate_id,
            recommended_candidate_name=best.name,
            recommendation_reason=reason,
            disclaimer=DISCLAIMER_TEXT,
        )

    def compute_applicant_insights(
        self,
        ranked_items: List[RankedCandidateItem],
        job_title: str,
        required_skills: List[str],
        preferred_skills: List[str],
    ) -> RecruiterInsightsResponse:
        """Computes skill coverage across the applicant pool and identifies common shortages."""
        total = len(ranked_items)
        if total == 0:
            return RecruiterInsightsResponse(
                job_title=job_title,
                total_applicants_evaluated=0,
                skill_coverage=[],
                shortage_insight_narrative="No applicants evaluated yet.",
                is_sample_dataset=True,
                disclaimer=DISCLAIMER_TEXT,
            )

        all_target_skills = [
            (s, True) for s in required_skills
        ] + [
            (s, False) for s in preferred_skills
        ]

        coverage_items: List[ApplicantSkillCoverageItem] = []
        gaps_count: Dict[str, int] = {}

        for skill_name, is_req in all_target_skills:
            # Count candidates possessing skill
            has_count = 0
            for cand in ranked_items:
                if any(s.lower() == skill_name.lower() for s in cand.strong_skills + cand.partial_skills):
                    has_count += 1
                else:
                    gaps_count[skill_name] = gaps_count.get(skill_name, 0) + 1

            pct = round((has_count / total) * 100.0, 1)
            coverage_items.append(ApplicantSkillCoverageItem(
                skill=skill_name,
                is_required=is_req,
                applicant_count=has_count,
                total_applicants=total,
                coverage_percentage=pct,
            ))

        # Sort coverage items descending
        coverage_items.sort(key=lambda x: x.coverage_percentage, reverse=True)

        # Most common gap
        most_common_gap = None
        gap_pct = None
        if gaps_count:
            top_gap_tuple = max(gaps_count.items(), key=lambda x: x[1])
            most_common_gap = top_gap_tuple[0]
            gap_candidates = top_gap_tuple[1]
            gap_pct = round((gap_candidates / total) * 100.0, 1)

        if most_common_gap and gap_pct:
            narrative = (
                f"{most_common_gap} is the most common skill gap across this applicant pool, "
                f"absent in {gap_pct}% of evaluated candidate profiles."
            )
            linkage = f"Industry demand for {most_common_gap} is prominent across recent market requisitions. Consider prioritizing {most_common_gap} in targeted candidate onboarding or upskilling."
        else:
            narrative = "High competency coverage observed across all required skills in this applicant pool."
            linkage = "Applicant capabilities are well-aligned with canonical market benchmarks."

        return RecruiterInsightsResponse(
            job_title=job_title,
            total_applicants_evaluated=total,
            skill_coverage=coverage_items,
            most_common_gap_skill=most_common_gap,
            most_common_gap_percentage=gap_pct,
            shortage_insight_narrative=narrative,
            market_trend_linkage=linkage,
            is_sample_dataset=True,
            disclaimer=DISCLAIMER_TEXT,
        )


recruiter_engine = RecruiterEngine()
