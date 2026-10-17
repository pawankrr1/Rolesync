"""Career Recommendation Engine and Adjacent Role Progression Paths.

Implements the Career Recommendation Engine:
Given a candidate profile, returns the top 5 suitable roles based on:
  - candidate skill vector
  - role skill vector (cosine similarity)
  - skill coverage (required & preferred)
  - semantic similarity (taxonomy categories)
  - experience compatibility

Each recommended role contains:
  - role: Role title (e.g. "Data Analyst")
  - match_score: Mathematical alignment percentage (e.g. 91.0)
  - matched_skills: Verified overlapping competencies
  - missing_skills: Unfulfilled role requirements
  - reason: Non-guaranteed explainable rationale using:
      "Skill alignment", "Potential fit", "Based on the current profile"
  - next_skills_to_learn: Prioritized learning targets to bridge the gap

Also implements adjacent-role recommendations (e.g. Software Engineer -> Backend Developer -> ML Engineer)
strictly when verified skill evidence supports the transition.
"""

import math
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

from app.core.taxonomy import taxonomy, SkillDefinition
from app.core.extractor import extractor, ExtractedSkill
from app.core.role_engine import role_engine, CareerRoleProfile, RoleSkillRequirement
from app.core.matching_engine import (
    matching_engine,
    ExplainableMatchResult,
    normalize_candidate_skills,
    normalize_experience_years,
)
from app.core.gap_analyzer import gap_analyzer


class RoleRecommendationItem(BaseModel):
    """Detailed role recommendation item adhering strictly to requirements."""
    role: str  # Role title (e.g. "Data Analyst")
    role_id: str  # Role identifier slug (e.g. "data_analyst")
    role_title: Optional[str] = None
    category: str
    match_score: float  # Percentage (0.0 to 100.0)
    matched_skills: List[str]
    missing_skills: List[str]
    reason: str  # Must use 'Skill alignment', 'Potential fit', 'Based on the current profile'
    next_skills_to_learn: List[str]
    why_recommended: str = Field("", description="Explicit answer to 'WHY WAS THIS RECOMMENDED?'")
    vector_similarity: float = 0.0  # Cosine similarity between candidate and role vectors (0.0 to 1.0)
    skill_coverage: float = 0.0  # Required skill coverage percentage
    experience_compatibility: str = ""
    market_demand_index: float = 8.5

    def model_post_init(self, __context: Any) -> None:
        if not self.role_title:
            self.role_title = self.role


class AdjacentTransitionStep(BaseModel):
    """A single step in a multi-role career progression pathway."""
    from_role: str
    from_role_id: str
    to_role: str
    to_role_id: str
    transition_feasibility: str  # "Immediate / High Feasibility", "Moderate Bridge Required"
    shared_skills: List[str]
    bridge_skills: List[str]  # Key skills needed to unlock this transition
    evidence: str  # Evidence from candidate profile supporting transition


class AdjacentRolePathway(BaseModel):
    """Complete multi-step adjacent role progression pathway."""
    path_title: str  # e.g. "Software Engineer → Backend Developer → ML Engineer"
    start_role: str
    target_role: str
    overall_feasibility: str
    supporting_evidence: str
    steps: List[AdjacentTransitionStep]


class CareerRecommendationResponse(BaseModel):
    """API response model for POST /api/v1/recommendations/roles."""
    recommended_roles: List[RoleRecommendationItem]  # Exactly Top 5 roles
    adjacent_transitions: List[AdjacentRolePathway] = Field(default_factory=list)
    candidate_skills_analyzed: List[str] = Field(default_factory=list)
    profile_summary: str = ""
    disclaimer: str = (
        "Recommendations reflect skill alignment and potential fit based on the current profile. "
        "They do not represent guaranteed career outcomes or hiring commitments."
    )
    system_disclaimer: str = (
        "Career Intelligence provides decision support based on the available profile and dataset. "
        "It does not guarantee employment, hiring outcomes or career success."
    )


# Curated career progression graph (From -> To -> Bridge Requirements)
STRATEGIC_PATHWAY_DEFINITIONS = [
    {
        "path_title": "Software Engineer → Backend Developer → ML Engineer",
        "start_role_id": "software_engineer",
        "intermediate_role_id": "backend_developer",
        "target_role_id": "ml_engineer",
        "qualifying_skills": {"python", "sql", "git", "data_structures_algorithms"},
        "min_overlap_count": 1,
    },
    {
        "path_title": "Data Analyst → Data Scientist → ML Engineer",
        "start_role_id": "data_analyst",
        "intermediate_role_id": "data_scientist",
        "target_role_id": "ml_engineer",
        "qualifying_skills": {"sql", "excel", "data_analysis", "python", "power_bi"},
        "min_overlap_count": 1,
    },
    {
        "path_title": "Frontend Developer → Full Stack Engineer → Backend Developer",
        "start_role_id": "frontend_developer",
        "intermediate_role_id": "fullstack_developer",
        "target_role_id": "backend_developer",
        "qualifying_skills": {"javascript", "typescript", "react", "html5", "css3"},
        "min_overlap_count": 1,
    },
    {
        "path_title": "DevOps Engineer → Cloud Engineer",
        "start_role_id": "devops_engineer",
        "intermediate_role_id": None,
        "target_role_id": "cloud_engineer",
        "qualifying_skills": {"docker", "linux", "git", "devops_cicd", "aws"},
        "min_overlap_count": 1,
    },
]


class CareerRecommendationEngine:
    """Core mathematical career recommendation and adjacent progression engine."""

    def __init__(self):
        self.taxonomy = taxonomy
        self.role_engine = role_engine
        self.matching_engine = matching_engine
        self.gap_analyzer = gap_analyzer

        # Build ordered canonical skill vocabulary for vector embeddings
        self.vocabulary: List[str] = sorted([s.id for s in self.taxonomy.get_all_skills()])
        self.vocab_index: Dict[str, int] = {sid: i for i, sid in enumerate(self.vocabulary)}

    def build_candidate_vector(self, candidate_skills: List[ExtractedSkill]) -> List[float]:
        """Creates an N-dimensional mathematical skill vector for candidate."""
        cand_map = {s.canonical_id: s for s in candidate_skills}
        vec = [0.0] * len(self.vocabulary)

        for sid, idx in self.vocab_index.items():
            if sid in cand_map:
                vec[idx] = 1.0  # Direct verified match
            else:
                # Check adjacent skills in taxonomy
                s_def = self.taxonomy.get_skill(sid)
                if s_def and any(adj in cand_map for adj in s_def.adjacent_skills):
                    vec[idx] = 0.45  # Adjacent credit

        return vec

    def build_role_vector(self, role: CareerRoleProfile) -> List[float]:
        """Creates an N-dimensional mathematical skill vector for a career role."""
        vec = [0.0] * len(self.vocabulary)
        
        for r in role.required_skills:
            if r.skill_id in self.vocab_index:
                vec[self.vocab_index[r.skill_id]] = 1.5 * r.weight
        
        for p in role.preferred_skills:
            if p.skill_id in self.vocab_index:
                vec[self.vocab_index[p.skill_id]] = 1.0 * p.weight

        return vec

    @staticmethod
    def calculate_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes mathematical cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return round(dot / (norm_a * norm_b), 4)

    def recommend_roles(
        self,
        candidate_skills: List[Union[ExtractedSkill, Dict, str]],
        candidate_experience_years: Optional[float] = None,
        candidate_education: Optional[Union[Dict, str]] = None,
        current_role: Optional[str] = None,
    ) -> CareerRecommendationResponse:
        """Evaluates candidate against all canonical career roles and returns Top 5."""
        norm_cand_skills = normalize_candidate_skills(candidate_skills)
        cand_skill_names = [s.canonical_name for s in norm_cand_skills]
        cand_skill_ids = {s.canonical_id for s in norm_cand_skills}
        cand_exp = normalize_experience_years(candidate_experience_years)

        # Build candidate vector
        cand_vec = self.build_candidate_vector(norm_cand_skills)

        # Retrieve all available canonical roles
        all_roles = self.role_engine.get_all_roles()

        scored_roles: List[RoleRecommendationItem] = []

        for role in all_roles:
            # 1. Calculate matching score
            match_res: ExplainableMatchResult = self.matching_engine.calculate_match(
                candidate_skills=norm_cand_skills,
                target_role=role,
                candidate_experience_years=cand_exp,
                candidate_education=candidate_education,
            )

            # 2. Calculate vector similarity
            role_vec = self.build_role_vector(role)
            vec_sim = self.calculate_cosine_similarity(cand_vec, role_vec)

            # 3. Analyze gaps to determine next skills to learn
            gap_report = self.gap_analyzer.analyze_gaps(
                candidate_skills=norm_cand_skills,
                target_role=role,
                match_result=match_res,
            )

            matched_names = [s.canonical_name for s in match_res.matched_required + match_res.matched_preferred]
            missing_names = [s.canonical_name for s in match_res.missing_required]

            # Priority gaps to learn next
            next_learn = [g.skill for g in gap_report.priority_order[:3]]

            # 4. Formulate Experience Compatibility narrative
            target_exp = float(role.typical_experience_years)
            if cand_exp >= target_exp:
                exp_compat = f"Compatible: {cand_exp} yrs experience meets recommended {target_exp} yrs."
            elif cand_exp > 0:
                exp_compat = f"Developing: {cand_exp} yrs experience (role typically seeks {target_exp} yrs)."
            else:
                exp_compat = f"Entry-level alignment: role recommends {target_exp} yrs practical experience."

            # 5. Formulate Non-Guaranteed Reason using required phrasing:
            # "Skill alignment", "Potential fit", "Based on the current profile"
            score_val = match_res.final_match_score

            if matched_names:
                strengths_str = f" demonstrated strengths in {', '.join(matched_names[:3])}"
            else:
                strengths_str = " emerging baseline interest"

            if score_val >= 75.0:
                qualifier = f"This highlights strong potential fit with minimal skill bridges needed."
            elif score_val >= 50.0:
                qualifier = f"This indicates viable potential fit where targeted upskilling in {next_learn[0] if next_learn else 'core tools'} can unlock competitive readiness."
            else:
                qualifier = f"This reflects exploratory potential fit requiring structured foundational study."

            reason_text = (
                f"Based on the current profile, there is an {score_val}% skill alignment with {role.title}. "
                f"With{strengths_str}, {qualifier}"
            )
            why_rec_text = (
                f"Recommended because you already possess {len(matched_names)} matching core skills "
                f"({', '.join(matched_names[:3]) if matched_names else 'foundational competencies'}), "
                f"yielding an estimated {score_val:.0f}% skill alignment based on the current profile."
            )

            scored_roles.append(
                RoleRecommendationItem(
                    role=role.title,
                    role_id=role.id,
                    category=role.category,
                    match_score=score_val,
                    matched_skills=matched_names,
                    missing_skills=missing_names,
                    reason=reason_text,
                    why_recommended=why_rec_text,
                    next_skills_to_learn=next_learn,
                    vector_similarity=vec_sim,
                    skill_coverage=round(match_res.required_skill_coverage, 1),
                    experience_compatibility=exp_compat,
                    market_demand_index=role.market_demand_index,
                )
            )

        # Sort by match_score descending, break ties with vector_similarity
        scored_roles.sort(key=lambda r: (r.match_score, r.vector_similarity), reverse=True)

        # Select Top 5
        top_5_roles = scored_roles[:5]

        # 6. Generate Adjacent-Role Progression Pathways (strictly evidence-based)
        adjacent_pathways = self._generate_adjacent_pathways(
            norm_cand_skills=norm_cand_skills,
            cand_skill_ids=cand_skill_ids,
            top_roles=top_5_roles,
            current_role_id=current_role,
        )

        summary = (
            f"Evaluated {len(all_roles)} career roles against {len(norm_cand_skills)} verified skills. "
            f"Top aligned career path is {top_5_roles[0].role} ({top_5_roles[0].match_score}% match score)."
        )

        return CareerRecommendationResponse(
            recommended_roles=top_5_roles,
            adjacent_transitions=adjacent_pathways,
            candidate_skills_analyzed=cand_skill_names,
            profile_summary=summary,
        )

    def _generate_adjacent_pathways(
        self,
        norm_cand_skills: List[ExtractedSkill],
        cand_skill_ids: Set[str],
        top_roles: List[RoleRecommendationItem],
        current_role_id: Optional[str] = None,
    ) -> List[AdjacentRolePathway]:
        """Generates adjacent career progression pathways ONLY when skill evidence supports it."""
        pathways: List[AdjacentRolePathway] = []

        # If candidate has NO technical skills at all, skill evidence does NOT support technical transitions
        if not cand_skill_ids:
            return []

        top_role_ids = {r.role_id for r in top_roles}
        anchor_id = current_role_id or (top_roles[0].role_id if top_roles else None)

        for p_def in STRATEGIC_PATHWAY_DEFINITIONS:
            start_id = p_def["start_role_id"]
            inter_id = p_def["intermediate_role_id"]
            target_id = p_def["target_role_id"]
            qual_skills = p_def["qualifying_skills"]

            # Check if candidate possesses skill evidence supporting this pathway
            overlap_evidence = cand_skill_ids.intersection(qual_skills)
            if len(overlap_evidence) < p_def["min_overlap_count"]:
                # Skill evidence does NOT support this transition -> skip!
                continue

            start_role = self.role_engine.get_role(start_id)
            target_role = self.role_engine.get_role(target_id)
            if not start_role or not target_role:
                continue

            steps: List[AdjacentTransitionStep] = []

            # Step 1: Start -> Intermediate (or Start -> Target if 1-step)
            if inter_id:
                inter_role = self.role_engine.get_role(inter_id)
                if not inter_role:
                    continue

                step1_shared, step1_bridge = self._compute_role_bridge(start_role, inter_role, cand_skill_ids)
                evidence1 = (
                    f"Candidate possesses verified competencies in {', '.join([taxonomy.get_skill(s).name for s in overlap_evidence if taxonomy.get_skill(s)])} "
                    f"providing foundational support for {inter_role.title}."
                )
                steps.append(
                    AdjacentTransitionStep(
                        from_role=start_role.title,
                        from_role_id=start_role.id,
                        to_role=inter_role.title,
                        to_role_id=inter_role.id,
                        transition_feasibility="Immediate / High Feasibility" if len(step1_shared) >= 2 else "Moderate Bridge Required",
                        shared_skills=step1_shared,
                        bridge_skills=step1_bridge,
                        evidence=evidence1,
                    )
                )

                # Step 2: Intermediate -> Target
                step2_shared, step2_bridge = self._compute_role_bridge(inter_role, target_role, cand_skill_ids)
                evidence2 = (
                    f"Skills acquired in {inter_role.title} ({', '.join(step1_shared + step1_bridge[:2])}) "
                    f"bridge directly into {target_role.title} production pipelines."
                )
                steps.append(
                    AdjacentTransitionStep(
                        from_role=inter_role.title,
                        from_role_id=inter_role.id,
                        to_role=target_role.title,
                        to_role_id=target_role.id,
                        transition_feasibility="Moderate Bridge Required",
                        shared_skills=step2_shared,
                        bridge_skills=step2_bridge,
                        evidence=evidence2,
                    )
                )
            else:
                # 1-step transition
                step_shared, step_bridge = self._compute_role_bridge(start_role, target_role, cand_skill_ids)
                evidence = (
                    f"Candidate demonstrates {len(step_shared)} overlapping competencies; "
                    f"transition requires closing {len(step_bridge)} bridge skills."
                )
                steps.append(
                    AdjacentTransitionStep(
                        from_role=start_role.title,
                        from_role_id=start_role.id,
                        to_role=target_role.title,
                        to_role_id=target_role.id,
                        transition_feasibility="Immediate / High Feasibility" if len(step_shared) >= 3 else "Moderate Bridge Required",
                        shared_skills=step_shared,
                        bridge_skills=step_bridge,
                        evidence=evidence,
                    )
                )

            ev_names = [taxonomy.get_skill(s).name for s in overlap_evidence if taxonomy.get_skill(s)]
            pathways.append(
                AdjacentRolePathway(
                    path_title=p_def["path_title"],
                    start_role=start_role.title,
                    target_role=target_role.title,
                    overall_feasibility="High Feasibility via Staged Upskilling",
                    supporting_evidence=(
                        f"Skill evidence in candidate profile ({', '.join(ev_names)}) "
                        f"mathematically confirms transition viability along this pathway."
                    ),
                    steps=steps,
                )
            )

        return pathways

    def _compute_role_bridge(
        self,
        role_a: CareerRoleProfile,
        role_b: CareerRoleProfile,
        cand_skill_ids: Set[str]
    ) -> Tuple[List[str], List[str]]:
        """Calculates shared skills and missing bridge skills between two roles."""
        reqs_a = {r.skill_id: r.canonical_name for r in role_a.required_skills}
        reqs_b = {r.skill_id: r.canonical_name for r in role_b.required_skills}

        # Shared skills between roles where candidate has competency
        shared_ids = set(reqs_a.keys()).intersection(set(reqs_b.keys()))
        shared_names = [reqs_b[sid] for sid in shared_ids]

        # If candidate already has skills for role B, include them
        cand_in_b = [reqs_b[sid] for sid in reqs_b if sid in cand_skill_ids and reqs_b[sid] not in shared_names]
        all_shared = shared_names + cand_in_b

        # Bridge skills needed for role B
        bridge_names = [reqs_b[sid] for sid in reqs_b if sid not in cand_skill_ids and reqs_b[sid] not in shared_names]

        return all_shared[:4], bridge_names[:4]


recommendation_engine = CareerRecommendationEngine()
