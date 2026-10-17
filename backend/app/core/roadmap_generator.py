"""Learning Roadmap Engine and Prioritized Sequencing System.

Translates candidate profile, target role, missing skills, and partial skills into
a dependency-aware, prioritized learning plan.

Each roadmap item includes:
  - skill: Canonical skill name
  - priority: "HIGH", "MEDIUM", "LOW"
  - reason: Grounded justification (e.g. "Required for target role.")
  - prerequisites: Explicit prerequisite list (e.g. ["Machine Learning"])
  - recommended_sequence: 1, 2, 3... (ordered by prerequisite graph & priority)
  - estimated_learning_stage: Foundational, Core, or Advanced Capstone
  - available_learning_resources: Curated courses from the local seeded dataset (data/courses.json).

Strict Constraints:
  - Do not invent course URLs.
  - Use only seeded resources unless a verified external course API is available.
  - If external data is unavailable, show: "Demo learning resource" instead of fabricating a real course.
"""

from collections import Counter
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

from app.core.taxonomy import taxonomy, SkillDefinition
from app.core.extractor import ExtractedSkill
from app.core.role_engine import role_engine, CareerRoleProfile, RoleSkillRequirement
from app.core.matching_engine import matching_engine, normalize_candidate_skills
from app.core.gap_analyzer import (
    gap_analyzer,
    GapAnalysisReport,
    SkillGapItem,
    PrioritizedSkillGap,
)


def _resolve_courses_file() -> Optional[Path]:
    """Finds courses.json seed dataset within repository paths."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "data" / "courses.json",
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "courses.json",
        Path.cwd() / "data" / "courses.json",
        Path("/Users/pawankumar/Documents/New_assignmnet/Bharat 2.0/data/courses.json"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _load_courses_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """Loads seeded courses grouped by canonical skill_id."""
    cf = _resolve_courses_file()
    if not cf:
        return {}

    try:
        with open(cf, "r", encoding="utf-8") as f:
            courses = json.load(f)
        
        catalog: Dict[str, List[Dict[str, Any]]] = {}
        for c in courses:
            sid = c.get("skill_id", "").strip().lower()
            if sid:
                catalog.setdefault(sid, []).append(c)
        return catalog
    except Exception:
        return {}


# In-memory cached course catalog
SEEDED_COURSES = _load_courses_catalog()


class CourseResourceItem(BaseModel):
    """Educational course resource adhering strictly to verified/seeded constraints."""
    title: str
    provider: str
    type: str = "Online Course"
    url: Optional[str] = None
    estimated_hours: int = 20
    is_free: bool = True
    rating: float = 4.8


# Backward compatibility alias
CuratedCourseResource = CourseResourceItem


class LearningRoadmapItem(BaseModel):
    """A prioritized milestone in the learning roadmap."""
    skill: str  # Canonical display name (e.g. "Statistics" or "Deep Learning")
    skill_id: str
    priority: str  # "HIGH", "MEDIUM", "LOW"
    reason: str  # e.g. "Required for target role."
    why_recommended: str = Field("", description="Explicit answer to 'WHY WAS THIS RECOMMENDED?'")
    prerequisites: List[str] = Field(default_factory=list)  # e.g. ["Machine Learning"]
    prerequisite: Optional[str] = None  # Singular alias
    recommended_sequence: int  # 1, 2, 3...
    estimated_learning_stage: str  # "Stage 1: Foundational Prerequisites", "Stage 2: Core Competencies", etc.
    estimated_duration_weeks: str = "2-3 weeks"
    available_learning_resources: List[CourseResourceItem] = Field(default_factory=list)
    hands_on_project: str = ""
    learning_outcomes: List[str] = Field(default_factory=list)

    # Backward compatibility fields for existing code & RoadmapMilestone
    step_number: Optional[int] = None
    stage_phase: Optional[str] = None
    skill_name: Optional[str] = None
    category: Optional[str] = None
    estimated_duration: Optional[str] = None
    prerequisite_context: Optional[str] = None
    curated_resources: Optional[List[CourseResourceItem]] = None


# Backward compatibility alias
RoadmapMilestone = LearningRoadmapItem


class LearningRoadmapResponse(BaseModel):
    """Complete response returned by learning roadmap engine."""
    target_role: str
    target_role_id: str
    total_estimated_weeks: int
    total_milestones: int
    readiness_before: float
    projected_readiness_after: float
    pedagogical_strategy: str
    roadmap: List[LearningRoadmapItem]  # The prioritized learning plan
    prioritized_learning_plan: List[LearningRoadmapItem] = Field(default_factory=list)
    milestones: List[LearningRoadmapItem] = Field(default_factory=list)  # Backward compatibility
    system_disclaimer: str = (
        "Career Intelligence provides decision support based on the available profile and dataset. "
        "It does not guarantee employment, hiring outcomes or career success."
    )


# Backward compatibility alias
LearningRoadmap = LearningRoadmapResponse


class AdjacentCareerRole(BaseModel):
    """Preserved for backward compatibility."""
    role_id: str
    role_title: str
    category: str
    alignment_score: float
    score_grade: str
    overlapping_skills: List[str]
    missing_bridge_skills: List[str]
    transition_feasibility: str
    why_recommended: str


def get_available_learning_resources(skill_id: str, skill_name: str) -> List[CourseResourceItem]:
    """Retrieves seeded resources for a skill.
    
    Strict Rule: Do not invent course URLs. If unseeded, return 'Demo learning resource'.
    """
    raw_courses = SEEDED_COURSES.get(skill_id, [])

    if raw_courses:
        resources = []
        for c in raw_courses:
            resources.append(
                CourseResourceItem(
                    title=c.get("title", f"{skill_name} Fundamentals"),
                    provider=c.get("provider", "Curated Seeded Platform"),
                    type=c.get("course_type", "Interactive Course"),
                    url=c.get("url"),  # Preserves exact seeded URL
                    estimated_hours=int(c.get("estimated_hours", 20)),
                    is_free=bool(c.get("is_free", True)),
                    rating=float(c.get("rating", 4.8)),
                )
            )
        return resources

    # Fallback constraint: If external data is unavailable, show 'Demo learning resource'
    # Do NOT invent course URLs
    return [
        CourseResourceItem(
            title=f"Demo learning resource: {skill_name} Guided Tutorial",
            provider="Demo learning resource",
            type="Demo learning resource",
            url=None,  # No fabricated URL
            estimated_hours=15,
            is_free=True,
            rating=4.5,
        )
    ]


class RoadmapGenerator:
    """Core Dependency-Aware Learning Roadmap Sequencing Engine."""

    def __init__(self):
        self.taxonomy = taxonomy
        self.role_engine = role_engine
        self.matching_engine = matching_engine
        self.gap_analyzer = gap_analyzer

    def generate_roadmap(
        self,
        candidate_skills: Optional[List[Union[ExtractedSkill, Dict, str]]] = None,
        target_role: Optional[Union[CareerRoleProfile, str]] = None,
        missing_skills: Optional[List[Union[Dict, str]]] = None,
        partial_skills: Optional[List[Union[Dict, str]]] = None,
        candidate_experience_years: Optional[float] = None,
        gap_report: Optional[GapAnalysisReport] = None,
    ) -> LearningRoadmapResponse:
        """Constructs an explainable, dependency-aware prioritized learning plan."""
        # 1. Resolve Target Role
        role_profile: Optional[CareerRoleProfile] = None
        if isinstance(target_role, str):
            role_profile = self.role_engine.get_role(target_role)
        elif isinstance(target_role, CareerRoleProfile):
            role_profile = target_role
        elif gap_report and gap_report.target_role_title:
            role_profile = self.role_engine.get_role(gap_report.target_role_title.lower().replace(" ", "_"))

        if not role_profile:
            # Fallback to backend_engineer
            role_profile = self.role_engine.get_role("backend_engineer") or self.role_engine.get_all_roles()[0]

        target_title = role_profile.title if role_profile else "Target Role Specification"
        target_id = role_profile.id if role_profile else "custom_role"

        # 2. Resolve Candidate Verified Skills
        norm_candidate_skills: List[ExtractedSkill] = (
            normalize_candidate_skills(candidate_skills) if candidate_skills else []
        )
        cand_skill_ids: Set[str] = {s.canonical_id for s in norm_candidate_skills}

        # 3. Resolve Gaps (Missing & Partial)
        # If gap_report not provided, compute through gap_analyzer
        if gap_report is None:
            gap_report = self.gap_analyzer.analyze_gaps(
                candidate_skills=norm_candidate_skills,
                target_role=role_profile,
            )

        # Build list of gaps to sequence
        # If user explicitly provided missing_skills or partial_skills, respect them
        gaps_to_plan: List[SkillGapItem] = []

        if missing_skills is not None or partial_skills is not None:
            explicit_missing = list(missing_skills or [])
            explicit_partial = list(partial_skills or [])

            # Convert explicit names to SkillGapItem
            for item in explicit_partial:
                name = item if isinstance(item, str) else item.get("skill", item.get("name", ""))
                sid = self.taxonomy.get_canonical_id(name) or name.lower().replace(" ", "_")
                s_def = self.taxonomy.get_skill(sid)
                c_name = s_def.name if s_def else name
                gaps_to_plan.append(
                    SkillGapItem(
                        skill=c_name,
                        skill_id=sid,
                        canonical_name=c_name,
                        category=s_def.category if s_def else "General",
                        classification="PARTIAL",
                        priority="HIGH",
                        importance="HIGH",
                        importance_score=1.3,
                        reason=f"Partial competency detected for {target_title}; targeted bridging recommended.",
                        reasoning=f"Partial competency detected for {target_title}; targeted bridging recommended.",
                        recommended_next_action=f"Deepen mastery of {c_name} with hands-on practice.",
                        is_required=True,
                        gap_status="partial_match",
                    )
                )

            for item in explicit_missing:
                name = item if isinstance(item, str) else item.get("skill", item.get("name", ""))
                sid = self.taxonomy.get_canonical_id(name) or name.lower().replace(" ", "_")
                s_def = self.taxonomy.get_skill(sid)
                c_name = s_def.name if s_def else name

                # User priority override if provided as dict
                user_prio = item.get("priority") if isinstance(item, dict) else None
                user_reason = item.get("reason") if isinstance(item, dict) else None

                # Check if it is a required skill for the role
                is_req = any(r.skill_id == sid for r in role_profile.required_skills)

                if user_prio:
                    priority_val = user_prio.upper()
                elif is_req or sid in ("statistics_probability", "statistics", "deep_learning", "machine_learning", "python", "sql", "docker"):
                    priority_val = "HIGH"
                else:
                    priority_val = "MEDIUM"

                reason_val = user_reason or (f"Required for target role." if (is_req or priority_val == "HIGH") else f"Preferred differentiator for target role.")

                gaps_to_plan.append(
                    SkillGapItem(
                        skill=c_name,
                        skill_id=sid,
                        canonical_name=c_name,
                        category=s_def.category if s_def else "General",
                        classification="MISSING",
                        priority=priority_val,
                        importance="CRITICAL" if priority_val == "HIGH" else "MEDIUM",
                        importance_score=1.4 if priority_val == "HIGH" else 1.0,
                        reason=reason_val,
                        reasoning=reason_val,
                        recommended_next_action=f"Master foundational concepts of {c_name}.",
                        is_required=is_req or (priority_val == "HIGH"),
                        gap_status="missing",
                    )
                )
        else:
            # Use prioritized gaps from gap_report
            gaps_to_plan = list(gap_report.priority_order)

        # 4. Pedagogical Sequencing Algorithm (Dependency-Aware Topological Progression)
        # We sequence skills such that:
        # - Skills with no unmet prerequisites are scheduled first (Foundational Stage)
        # - Dependent skills are unlocked after their prerequisites are completed
        # - High-priority core requirements are prioritized within each dependency stage
        plan_items: List[LearningRoadmapItem] = []

        unlocked_skills: Set[str] = set(cand_skill_ids)
        remaining_gaps = list(gaps_to_plan)

        sequence_counter = 1
        total_weeks = 0

        # Safety loop counter to prevent infinite iteration
        max_iterations = len(remaining_gaps) + 5

        while remaining_gaps and max_iterations > 0:
            max_iterations -= 1

            # Find all candidates whose prerequisites are completely satisfied
            eligible_indices = []
            for idx, gap in enumerate(remaining_gaps):
                s_def = self.taxonomy.get_skill(gap.skill_id)
                prereqs = s_def.prerequisites if s_def else []
                # Check if all prerequisites are either possessed or already completed in earlier steps
                unmet = [p for p in prereqs if p not in unlocked_skills]
                if not unmet:
                    eligible_indices.append(idx)

            # If no gap has all prerequisites met (e.g. mutual dependency or external missing),
            # pick the gap with the fewest unmet prerequisites
            if not eligible_indices:
                fewest_idx = min(
                    range(len(remaining_gaps)),
                    key=lambda i: len([
                        p for p in (self.taxonomy.get_skill(remaining_gaps[i].skill_id).prerequisites if self.taxonomy.get_skill(remaining_gaps[i].skill_id) else [])
                        if p not in unlocked_skills
                    ])
                )
                eligible_indices = [fewest_idx]

            # Among eligible candidates, pick the one with highest priority score / role importance
            best_idx = max(
                eligible_indices,
                key=lambda i: (
                    1 if remaining_gaps[i].priority == "HIGH" else (0.5 if remaining_gaps[i].priority == "MEDIUM" else 0.2),
                    remaining_gaps[i].is_required,
                    remaining_gaps[i].priority_score,
                )
            )

            chosen_gap = remaining_gaps.pop(best_idx)
            s_def = self.taxonomy.get_skill(chosen_gap.skill_id)

            # Prerequisite context names
            raw_prereqs = s_def.prerequisites if s_def else []
            prereq_names = [
                self.taxonomy.get_skill(p).name
                for p in raw_prereqs
                if self.taxonomy.get_skill(p)
            ]
            singular_prereq = prereq_names[0] if prereq_names else None

            # Determine Learning Stage
            if sequence_counter <= 2 or not prereq_names:
                stage = "Stage 1: Foundational Prerequisites"
            elif sequence_counter <= 4 or chosen_gap.is_required:
                stage = "Stage 2: Core Competencies"
            else:
                stage = "Stage 3: Advanced Specialization & Capstone"

            # Learning duration
            weeks = 3 if "3" in chosen_gap.learning_effort_weeks else 2
            total_weeks += weeks

            # Course resources from seeded dataset
            resources = get_available_learning_resources(chosen_gap.skill_id, chosen_gap.canonical_name)

            # Clean reason string
            if chosen_gap.is_required:
                reason_phrase = f"Required for target role."
            else:
                reason_phrase = f"High-value preferred differentiator for target role."

            # Project challenge
            project = (
                f"Build a showcase portfolio project applying {chosen_gap.canonical_name}: "
                f"Implement a working prototype demonstrating production-ready competencies."
            )
            if chosen_gap.skill_id in ("statistics_probability", "statistics"):
                project = "Statistical EDA Notebook: Run hypothesis testing, p-value calculations, and A/B test simulations."
            elif chosen_gap.skill_id == "machine_learning":
                project = "Predictive Modeling Project: Train and evaluate scikit-learn models on Kaggle tabular data with cross-validation."
            elif chosen_gap.skill_id == "deep_learning":
                project = "Neural Network Classifier: Implement and train a PyTorch neural network with custom loss curves and validation metrics."
            elif chosen_gap.skill_id == "docker":
                project = "Containerized Microservice: Write a multi-stage Dockerfile and docker-compose.yml with automated healthchecks."

            outcomes = [
                f"Master core syntax and paradigms of {chosen_gap.canonical_name}",
                f"Build verifiable portfolio code in a public GitHub repository",
                f"Satisfy hiring requirement for {target_title}",
            ]

            why_rec = (
                f"Recommended as Milestone {sequence_counter} in {stage} because mastering {chosen_gap.canonical_name} "
                f"directly fulfills a priority gap for {target_title} and unblocks {len(chosen_gap.unblocks_skills)} dependent competencies."
            )

            milestone = LearningRoadmapItem(
                skill=chosen_gap.canonical_name,
                skill_id=chosen_gap.skill_id,
                priority=chosen_gap.priority,
                reason=reason_phrase,
                why_recommended=why_rec,
                prerequisites=prereq_names,
                prerequisite=singular_prereq,
                recommended_sequence=sequence_counter,
                estimated_learning_stage=stage,
                estimated_duration_weeks=f"{weeks} weeks",
                available_learning_resources=resources,
                hands_on_project=project,
                learning_outcomes=outcomes,
                # Backward compatibility
                step_number=sequence_counter,
                stage_phase=stage,
                skill_name=chosen_gap.canonical_name,
                category=chosen_gap.category,
                estimated_duration=f"{weeks} weeks",
                prerequisite_context=chosen_gap.reasoning or reason_phrase,
                curated_resources=resources,
            )

            plan_items.append(milestone)
            unlocked_skills.add(chosen_gap.skill_id)
            sequence_counter += 1

        strategy = (
            f"Pedagogical Sequence: Ordered strictly by prerequisite hierarchy first, ensuring fundamental math and tools "
            f"are mastered before dependent frameworks, culminating in production-ready projects."
        )

        readiness_before = gap_report.readiness_percentage if gap_report else 30.0
        readiness_after = min(100.0, round(readiness_before + (len(plan_items) * 12.5), 1))

        return LearningRoadmapResponse(
            target_role=target_title,
            target_role_id=target_id,
            total_estimated_weeks=total_weeks,
            total_milestones=len(plan_items),
            readiness_before=readiness_before,
            projected_readiness_after=readiness_after,
            pedagogical_strategy=strategy,
            roadmap=plan_items,
            prioritized_learning_plan=plan_items,
            milestones=plan_items,
        )

    def recommend_adjacent_roles(
        self,
        candidate_skills: List[ExtractedSkill],
        current_target_role_id: Optional[str] = None
    ) -> List[AdjacentCareerRole]:
        """Preserved for backward compatibility with existing tests."""
        from app.core.recommendation_engine import recommendation_engine
        res = recommendation_engine.recommend_roles(
            candidate_skills=candidate_skills,
            current_role=current_target_role_id
        )
        adjacent = []
        for r in res.recommended_roles:
            if current_target_role_id and r.role_id == current_target_role_id:
                continue
            adjacent.append(
                AdjacentCareerRole(
                    role_id=r.role_id,
                    role_title=r.role,
                    category=r.category,
                    alignment_score=r.match_score,
                    score_grade="High Alignment" if r.match_score >= 65.0 else "Needs Upskilling",
                    overlapping_skills=r.matched_skills[:5],
                    missing_bridge_skills=r.missing_skills[:4],
                    transition_feasibility="Immediate / High Feasibility" if r.match_score >= 70.0 else "Moderate Bridge Required",
                    why_recommended=r.reason,
                )
            )
        return adjacent


roadmap_generator = RoadmapGenerator()
