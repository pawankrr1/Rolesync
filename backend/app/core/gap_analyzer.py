"""Skill Gap Analysis and Priority Ordering Engine.

Implements the explainable Skill Gap Analysis Engine:
Core logic:
  Required skills minus Candidate skills,
  improved using skill importance and partial similarity.

Classifies skills into:
  - STRONG (directly verified in candidate profile)
  - PARTIAL (candidate has adjacent competency in taxonomy graph)
  - MISSING (completely unfulfilled gap)

For each missing / partial skill, calculates:
  - priority ("HIGH", "MEDIUM", "LOW")
  - importance ("CRITICAL", "HIGH", "MEDIUM", "LOW" + numerical score)
  - reason (explainable rationale grounded in dataset evidence)
  - recommended next action (actionable next step with curated courses from dataset)

Priority formula incorporates 5 explicit dimensions:
  1. Role importance (required vs preferred, requirement weight)
  2. Skill demand in available dataset (exact frequency across data/jobs.json)
  3. Similarity to candidate's existing skills (taxonomy adjacency quick-win bridge)
  4. Learning dependency (prerequisites satisfied vs unmet, unblocking other requirements)
  5. Current gap magnitude (MISSING = full gap, PARTIAL = quick-win bridge)

Strict constraints:
  - Do not claim external market statistics unless the dataset actually contains the evidence.
  - Use only available data.
"""

from collections import Counter
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

from app.core.taxonomy import taxonomy, SkillDefinition
from app.core.extractor import ExtractedSkill
from app.core.role_engine import role_engine, CareerRoleProfile, RoleSkillRequirement
from app.core.matching_engine import (
    matching_engine,
    ExplainableMatchResult,
    SkillMatchDetail,
    normalize_candidate_skills,
)


def _resolve_data_file(filename: str) -> Optional[Path]:
    """Finds seed dataset JSON files within repository paths."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "data" / filename,
        Path(__file__).resolve().parent.parent.parent.parent / "data" / filename,
        Path.cwd() / "data" / filename,
        Path("/Users/pawankumar/Documents/New_assignmnet/Bharat 2.0/data") / filename,
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _load_dataset_job_demands() -> Tuple[Dict[str, int], int]:
    """Computes exact skill demand counts across the available jobs dataset (jobs.json)."""
    job_file = _resolve_data_file("jobs.json")
    if not job_file:
        return {}, 0

    try:
        with open(job_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        
        counts: Counter = Counter()
        for job in jobs:
            skills = job.get("skills", [])
            for s in skills:
                # Normalize skill id
                s_id = s.strip().lower()
                counts[s_id] += 1
        return dict(counts), len(jobs)
    except Exception:
        return {}, 0


def _load_dataset_courses() -> Dict[str, List[Dict[str, Any]]]:
    """Loads curated course catalog grouped by canonical skill_id."""
    course_file = _resolve_data_file("courses.json")
    if not course_file:
        return {}

    try:
        with open(course_file, "r", encoding="utf-8") as f:
            courses = json.load(f)
        
        by_skill: Dict[str, List[Dict[str, Any]]] = {}
        for c in courses:
            sid = c.get("skill_id", "").strip().lower()
            if sid:
                by_skill.setdefault(sid, []).append(c)
        return by_skill
    except Exception:
        return {}


class SkillGapItem(BaseModel):
    """Detailed explainable gap object for a single skill."""
    skill: str  # Canonical display name (e.g. "Docker & Containerization")
    skill_id: str
    canonical_name: str
    category: str
    classification: str  # "STRONG", "PARTIAL", "MISSING"
    priority: str  # "HIGH", "MEDIUM", "LOW"
    importance: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    importance_score: float
    reason: str  # Grounded explainable reason
    recommended_next_action: str  # Grounded actionable step
    recommended_action: Optional[str] = None  # Alias for recommended_next_action
    similarity_to_candidate: float = 0.0
    adjacent_skills_found: List[str] = Field(default_factory=list)
    dataset_demand_count: int = 0
    dataset_demand_percentage: float = 0.0
    prerequisites_met: bool = True
    unmet_prerequisites: List[str] = Field(default_factory=list)
    unblocks_skills: List[str] = Field(default_factory=list)
    priority_rank: int = 0
    priority_tier: str = "P2 - Core Competency"
    priority_score: float = 0.0
    learning_effort_weeks: str = "2-3 weeks"
    is_required: bool = True
    gap_status: str = "missing"  # "missing", "partial_match", "strong_match"
    reasoning: str = ""  # Alias for reason
    why_missing: str = Field("", description="Explicit answer to 'WHY IS THIS MISSING?'")


# For backward compatibility with roadmap_generator and existing modules
class PrioritizedSkillGap(SkillGapItem):
    pass


class GapAnalysisReport(BaseModel):
    """Standard explainable output for skill gap analysis."""
    gap_score: float  # 0.0 (no gap) to 100.0 (complete gap)
    strong_skills: List[SkillGapItem] = Field(default_factory=list)
    partial_skills: List[SkillGapItem] = Field(default_factory=list)
    missing_skills: List[SkillGapItem] = Field(default_factory=list)
    priority_order: List[SkillGapItem] = Field(default_factory=list)

    # Additional contextual & backward compatibility fields
    target_role_title: str = "Target Role"
    total_required_skills: int = 0
    strong_match_count: int = 0
    partial_match_count: int = 0
    missing_count: int = 0
    readiness_percentage: float = 0.0
    prioritized_gaps: List[SkillGapItem] = Field(default_factory=list)
    strong_matches: List[SkillMatchDetail] = Field(default_factory=list)
    summary_message: str = ""
    system_disclaimer: str = (
        "Career Intelligence provides decision support based on the available profile and dataset. "
        "It does not guarantee employment, hiring outcomes or career success."
    )


class SkillGapAnalyzer:
    """Core Skill Gap Analysis Engine."""

    def __init__(self):
        self.taxonomy = taxonomy
        self.demand_counts, self.total_jobs = _load_dataset_job_demands()
        self.courses_by_skill = _load_dataset_courses()

    def analyze_gaps(
        self,
        candidate_skills: List[Union[ExtractedSkill, Dict, str]],
        target_role: Optional[Union[CareerRoleProfile, str]] = None,
        match_result: Optional[ExplainableMatchResult] = None,
        required_skills: Optional[List[Union[RoleSkillRequirement, Dict, str]]] = None,
        preferred_skills: Optional[List[Union[RoleSkillRequirement, Dict, str]]] = None,
    ) -> GapAnalysisReport:
        """Performs rigorous gap analysis: Required minus Candidate, improved with taxonomy & demand."""
        # 1. Run matching engine if match_result not provided
        if match_result is None:
            match_result = matching_engine.calculate_match(
                candidate_skills=candidate_skills,
                target_role=target_role,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
            )

        # 2. Resolve Role Profile & Title
        role_profile: Optional[CareerRoleProfile] = None
        if isinstance(target_role, str):
            role_profile = role_engine.get_role(target_role)
        elif isinstance(target_role, CareerRoleProfile):
            role_profile = target_role
        
        role_title = role_profile.title if role_profile else "Target Role Specification"

        # 3. Candidate skill IDs for fast set operations
        norm_candidate_skills: List[ExtractedSkill] = normalize_candidate_skills(candidate_skills)
        cand_skill_ids: Set[str] = {s.canonical_id for s in norm_candidate_skills}

        # 4. Classify skills into STRONG, PARTIAL, MISSING
        strong_skills: List[SkillGapItem] = []
        partial_skills: List[SkillGapItem] = []
        missing_skills: List[SkillGapItem] = []

        # Process Strong Matches (Required + Preferred)
        all_strong_details = match_result.matched_required + match_result.matched_preferred
        for m in all_strong_details:
            demand_cnt = self.demand_counts.get(m.skill_id, 0)
            demand_pct = round((demand_cnt / max(1, self.total_jobs)) * 100.0, 1) if self.total_jobs > 0 else 0.0

            item = SkillGapItem(
                skill=m.canonical_name,
                skill_id=m.skill_id,
                canonical_name=m.canonical_name,
                category=m.category,
                classification="STRONG",
                priority="NONE",
                importance="CRITICAL" if m.is_required else "MEDIUM",
                importance_score=1.4 if m.is_required else 1.0,
                reason=f"Candidate possesses verified competency in {m.canonical_name}.",
                reasoning=f"Candidate possesses verified competency in {m.canonical_name}.",
                recommended_next_action=f"Apply {m.canonical_name} in advanced system architecture and production delivery.",
                recommended_action=f"Apply {m.canonical_name} in advanced system architecture and production delivery.",
                similarity_to_candidate=1.0,
                adjacent_skills_found=[],
                dataset_demand_count=demand_cnt,
                dataset_demand_percentage=demand_pct,
                prerequisites_met=True,
                unmet_prerequisites=[],
                unblocks_skills=[],
                priority_rank=0,
                priority_tier="Satisfied",
                priority_score=0.0,
                learning_effort_weeks="0 weeks",
                is_required=m.is_required,
                gap_status="strong_match",
                why_missing=f"Competency satisfied for {role_title}. Verified in candidate profile text.",
            )
            strong_skills.append(item)

        # 5. Build Dependency Graph among missing/partial competencies
        gaps_raw: List[SkillMatchDetail] = (
            match_result.partial_skills + match_result.missing_required + match_result.missing_preferred
        )
        gap_skill_ids: Set[str] = {g.skill_id for g in gaps_raw}

        unblocks_map: Dict[str, List[str]] = {gid: [] for gid in gap_skill_ids}
        for gid in gap_skill_ids:
            s_def = self.taxonomy.get_skill(gid)
            if s_def:
                for prereq in s_def.prerequisites:
                    if prereq in unblocks_map:
                        unblocks_map[prereq].append(s_def.name)

        # 6. Evaluate each Gap against the 5 Priority Dimensions
        for g_detail in gaps_raw:
            s_def = self.taxonomy.get_skill(g_detail.skill_id)
            is_partial = (g_detail.status == "partial_match")
            classification = "PARTIAL" if is_partial else "MISSING"

            # -------------------------------------------------------------
            # Factor 1: Role Importance
            # -------------------------------------------------------------
            if g_detail.is_required:
                base_score = 5.0
                importance_label = "CRITICAL" if s_def and s_def.importance_weight >= 1.2 else "HIGH"
                importance_num = round((s_def.importance_weight if s_def else 1.2) * 1.2, 2)
            else:
                base_score = 2.5
                importance_label = "MEDIUM"
                importance_num = round((s_def.importance_weight if s_def else 1.0) * 0.8, 2)

            # -------------------------------------------------------------
            # Factor 2: Skill Demand in Available Dataset (jobs.json)
            # -------------------------------------------------------------
            demand_cnt = self.demand_counts.get(g_detail.skill_id, 0)
            demand_pct = round((demand_cnt / max(1, self.total_jobs)) * 100.0, 1) if self.total_jobs > 0 else 0.0

            if demand_pct >= 25.0:
                demand_bonus = 3.5
                demand_phrase = f"appears frequently across similar jobs ({demand_cnt} of {self.total_jobs} jobs in available dataset)"
            elif demand_pct >= 12.0:
                demand_bonus = 2.0
                demand_phrase = f"in moderate demand across jobs ({demand_cnt} of {self.total_jobs} jobs in available dataset)"
            elif demand_pct > 0.0:
                demand_bonus = 1.0
                demand_phrase = f"appears in {demand_cnt} of {self.total_jobs} jobs ({demand_pct}%) in available dataset"
            else:
                demand_bonus = 0.5
                demand_phrase = "specialized competency for target role in available dataset"

            # -------------------------------------------------------------
            # Factor 3: Similarity to Candidate's Existing Skills (Adjacency)
            # -------------------------------------------------------------
            adj_list = s_def.adjacent_skills if s_def else []
            adj_possessed = [
                self.taxonomy.get_skill(adj).name
                for adj in adj_list
                if adj in cand_skill_ids and self.taxonomy.get_skill(adj)
            ]

            if is_partial or adj_possessed:
                similarity_score = round(min(1.0, len(adj_possessed) * 0.35 + 0.35), 2)
                similarity_bonus = 2.5
                similarity_phrase = f"Candidate already possesses adjacent competency in {', '.join(adj_possessed)} (quick-win skill bridge)."
            else:
                similarity_score = 0.0
                similarity_bonus = 0.0
                similarity_phrase = ""

            # -------------------------------------------------------------
            # Factor 4: Learning Dependency (Prerequisites & Unblocking)
            # -------------------------------------------------------------
            prereqs = s_def.prerequisites if s_def else []
            unmet_prereqs = [
                self.taxonomy.get_skill(p).name
                for p in prereqs
                if p not in cand_skill_ids and self.taxonomy.get_skill(p)
            ]
            prereqs_met = (len(unmet_prereqs) == 0)
            unblocks = unblocks_map.get(g_detail.skill_id, [])

            unblocks_bonus = len(unblocks) * 3.5
            prereq_score = 2.5 if prereqs_met else (-1.5 * len(unmet_prereqs))

            # -------------------------------------------------------------
            # Factor 5: Current Gap Magnitude
            # -------------------------------------------------------------
            if is_partial:
                gap_bonus = 2.0  # High ROI: closing an adjacent gap is faster
                gap_status_val = "partial_match"
            else:
                gap_bonus = 1.5  # Full gap to close
                gap_status_val = "missing"

            # Combined Priority Calculation
            raw_priority = (
                base_score
                + demand_bonus
                + similarity_bonus
                + unblocks_bonus
                + prereq_score
                + gap_bonus
            )
            if s_def and s_def.importance_weight:
                raw_priority *= s_def.importance_weight
            priority_score = round(max(1.0, raw_priority), 2)

            # Categorize Priority: HIGH, MEDIUM, LOW
            if priority_score >= 11.5:
                priority_label = "HIGH"
                priority_tier_val = "P1 - Foundational (Learn First)"
            elif priority_score >= 7.0:
                priority_label = "MEDIUM"
                priority_tier_val = "P2 - Core Competency"
            else:
                priority_label = "LOW"
                priority_tier_val = "P3 - Advanced / Capstone"

            # Synthesize Explainable Reason
            role_part = f"Required by target role ({role_title})" if g_detail.is_required else f"Preferred differentiator for {role_title}"
            reason_clauses = [f"{role_part} and {demand_phrase}."]
            if unblocks:
                reason_clauses.append(f"Foundational dependency unblocking: {', '.join(unblocks)}.")
            if prereqs_met:
                reason_clauses.append("All prerequisites satisfied; ready to learn immediately.")
            else:
                reason_clauses.append(f"Depends on unmet prerequisite(s): {', '.join(unmet_prereqs)}.")
            if similarity_phrase:
                reason_clauses.append(similarity_phrase)
            
            full_reason = " ".join(reason_clauses)

            # Grounded Actionable Recommendation from dataset
            courses = self.courses_by_skill.get(g_detail.skill_id, [])
            if courses:
                best_course = sorted(
                    courses,
                    key=lambda c: (c.get("is_free", False), c.get("rating", 4.5)),
                    reverse=True
                )[0]
                rec_action = (
                    f"Complete '{best_course.get('title')}' ({best_course.get('provider')}) "
                    f"and build an end-to-end portfolio challenge."
                )
                effort = f"{max(1, best_course.get('estimated_hours', 20) // 10)}-3 weeks"
            elif adj_possessed:
                rec_action = (
                    f"Bridge adjacent knowledge in {adj_possessed[0]} to master {g_detail.canonical_name} "
                    f"via documentation and hands-on implementation."
                )
                effort = "1-2 weeks"
            else:
                rec_action = (
                    f"Study official technical documentation for {g_detail.canonical_name} "
                    f"and implement a prototype application demonstrating core competency."
                )
                effort = "3-4 weeks"

            gap_item = SkillGapItem(
                skill=g_detail.canonical_name,
                skill_id=g_detail.skill_id,
                canonical_name=g_detail.canonical_name,
                category=g_detail.category,
                classification=classification,
                priority=priority_label,
                importance=importance_label,
                importance_score=importance_num,
                reason=full_reason,
                reasoning=full_reason,
                recommended_next_action=rec_action,
                recommended_action=rec_action,
                similarity_to_candidate=similarity_score,
                adjacent_skills_found=adj_possessed,
                dataset_demand_count=demand_cnt,
                dataset_demand_percentage=demand_pct,
                prerequisites_met=prereqs_met,
                unmet_prerequisites=unmet_prereqs,
                unblocks_skills=unblocks,
                priority_rank=0,
                priority_tier=priority_tier_val,
                priority_score=priority_score,
                learning_effort_weeks=effort,
                is_required=g_detail.is_required,
                gap_status=gap_status_val,
                why_missing=(
                    f"Partially unmet for {role_title}. Candidate demonstrates adjacent foundational competency in "
                    f"{', '.join(adj_possessed) if adj_possessed else 'related area'}, but direct production experience "
                    f"in {g_detail.canonical_name} was not identified in the profile."
                    if is_partial
                    else
                    f"Required benchmark skill for {role_title}. No direct keyword mentions, equivalent aliases, "
                    f"or foundational prerequisites were detected in the evaluated candidate profile."
                ),
            )

            if is_partial:
                partial_skills.append(gap_item)
            else:
                missing_skills.append(gap_item)

        # 7. Priority Order: Sort all gaps by priority score descending
        all_gaps = partial_skills + missing_skills
        all_gaps.sort(key=lambda x: x.priority_score, reverse=True)
        for i, item in enumerate(all_gaps):
            item.priority_rank = i + 1

        # 8. Compute Gap Score
        total_req_count = (
            len(match_result.matched_required)
            + len(match_result.partial_skills)
            + len(match_result.missing_required)
        )
        if total_req_count == 0:
            gap_score = 0.0
        else:
            missing_req_ids = {m.skill_id for m in match_result.missing_required}
            partial_req_ids = {p.skill_id for p in match_result.partial_skills if p.is_required}
            req_gaps_weight = sum(1.0 for _ in missing_req_ids) + sum(0.45 for _ in partial_req_ids)
            gap_score = round((req_gaps_weight / max(1, total_req_count)) * 100.0, 1)
            gap_score = max(0.0, min(100.0, gap_score))

        readiness_pct = round(max(0.0, 100.0 - gap_score), 1)

        high_priority_gaps = [g.skill for g in all_gaps if g.priority == "HIGH"]
        summary = (
            f"Evaluated {total_req_count} core requirements for {role_title}. "
            f"Overall gap score is {gap_score}% ({len(strong_skills)} strong, {len(partial_skills)} partial, {len(missing_skills)} missing). "
            f"Immediate focus should be placed on {min(3, len(high_priority_gaps))} HIGH priority skills: {', '.join(high_priority_gaps[:3])}."
        )

        return GapAnalysisReport(
            gap_score=gap_score,
            strong_skills=strong_skills,
            partial_skills=partial_skills,
            missing_skills=missing_skills,
            priority_order=all_gaps,
            target_role_title=role_title,
            total_required_skills=total_req_count,
            strong_match_count=len(strong_skills),
            partial_match_count=len(partial_skills),
            missing_count=len(missing_skills),
            readiness_percentage=readiness_pct,
            prioritized_gaps=all_gaps,
            strong_matches=match_result.matched_required,
            summary_message=summary,
        )


gap_analyzer = SkillGapAnalyzer()
