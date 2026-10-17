"""Market Intelligence Data Aggregation Service.

Aggregates insights strictly from the seeded / public repository dataset:
- data/jobs.json (50 seeded job requisitions)
- data/roles.json (11 benchmark roles)
- data/skills.json (58 canonical skills)
- data/demo_candidates.json (11 demo candidate profiles)

Rules & Constraints:
1. No live scraping or external web crawling.
2. Strictly descriptive aggregations; no predictive workforce forecasting.
3. Every aggregation includes clear data source context.
4. "Based on the current dataset" is included across all summaries.
"""

import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

DATASET_NOTICE = "Based on the current dataset"
NO_FORECASTING_NOTICE = (
    "Predictive workforce forecasting is not active in this release. "
    "All figures reflect descriptive aggregations of the current seeded repository data."
)


def resolve_data_directory(custom_path: Optional[str] = None) -> Path:
    """Resolves the local data directory containing seeded JSON files."""
    candidates: List[Path] = []
    if custom_path:
        candidates.append(Path(custom_path).resolve())

    current_file = Path(__file__).resolve()
    # backend/app/services -> repo root / data
    candidates.append(current_file.parent.parent.parent.parent / "data")
    # backend/app/services -> backend / data
    candidates.append(current_file.parent.parent.parent / "data")
    candidates.append(Path.cwd() / "data")
    candidates.append(Path("/Users/pawankumar/Documents/New_assignmnet/Bharat 2.0/data"))

    for p in candidates:
        if p.exists() and (p / "jobs.json").is_file():
            return p

    raise FileNotFoundError(
        f"Unable to locate seeded data directory. Evaluated paths: {[str(p) for p in candidates]}"
    )


_DATASET_CACHE: Dict[str, Any] = {}


def load_dataset_json(filename: str, data_dir: Optional[Path] = None) -> Any:
    """Loads a seeded JSON dataset file with in-memory caching."""
    base_dir = data_dir or resolve_data_directory()
    file_path = base_dir / filename
    cache_key = str(file_path.resolve())
    if cache_key in _DATASET_CACHE:
        cached = _DATASET_CACHE[cache_key]
        return list(cached) if isinstance(cached, list) else dict(cached)

    if not file_path.exists():
        raise FileNotFoundError(f"Seeded dataset file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _DATASET_CACHE[cache_key] = data
    return list(data) if isinstance(data, list) else dict(data)


def _build_skill_lookup(skills_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Builds a fast lookup dictionary by skill id."""
    lookup: Dict[str, Dict[str, Any]] = {}
    for s in skills_data:
        sid = s.get("id", "").strip().lower()
        if sid:
            lookup[sid] = {
                "id": sid,
                "name": s.get("name", sid.replace("_", " ").title()),
                "category": s.get("category", "General Technical"),
                "importance_weight": float(s.get("importance_weight", 1.0)),
                "adjacent_skills": s.get("adjacent_skills", []),
            }
    return lookup


# ==============================================================================
# 1. Most Frequently Requested Skills
# ==============================================================================
def get_most_frequently_requested_skills(
    jobs_data: Optional[List[Dict[str, Any]]] = None,
    skills_data: Optional[List[Dict[str, Any]]] = None,
    top_n: Optional[int] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Aggregates the most frequently requested skills across available job requisitions.

    Returns:
        Dict containing ranked skills, occurrence counts, percentage shares,
        and explicit data source context.
    """
    if jobs_data is None:
        jobs_data = load_dataset_json("jobs.json")
    if skills_data is None:
        skills_data = load_dataset_json("skills.json")

    total_jobs = len(jobs_data)
    skill_lookup = _build_skill_lookup(skills_data)

    if total_jobs == 0:
        return {
            "total_jobs_evaluated": 0,
            "skills": [],
            "data_source_context": "Seeded Job Requisitions (data/jobs.json, N=0 postings)",
            "context_note": f"{DATASET_NOTICE}, no job requisitions are currently available.",
        }

    skill_counts = Counter()
    for job in jobs_data:
        for sk in job.get("skills", []):
            clean_sk = sk.strip().lower()
            if clean_sk:
                skill_counts[clean_sk] += 1

    ranked_skills: List[Dict[str, Any]] = []
    for skill_id, count in skill_counts.most_common(top_n):
        skill_meta = skill_lookup.get(skill_id, {})
        freq_pct = round((count / total_jobs) * 100.0, 1)
        ranked_skills.append({
            "skill_id": skill_id,
            "skill_name": skill_meta.get("name", skill_id.replace("_", " ").title()),
            "category": skill_meta.get("category", "General Technical"),
            "job_count": count,
            "frequency_percentage": freq_pct,
            "importance_weight": skill_meta.get("importance_weight", 1.0),
        })

    top_names = [s["skill_name"] for s in ranked_skills[:3]]
    summary_text = (
        f"{DATASET_NOTICE}, the most frequently requested skills are "
        f"{', '.join(top_names)} across {total_jobs} seeded job postings."
    )

    return {
        "total_jobs_evaluated": total_jobs,
        "total_unique_skills_demanded": len(skill_counts),
        "skills": ranked_skills,
        "data_source_context": f"Seeded Job Requisitions (data/jobs.json, N={total_jobs} postings)",
        "context_note": summary_text,
    }


# ==============================================================================
# 2. Skills by Role
# ==============================================================================
def get_skills_by_role(
    role_id: Optional[str] = None,
    roles_data: Optional[List[Dict[str, Any]]] = None,
    skills_data: Optional[List[Dict[str, Any]]] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Aggregates required and preferred skills organized by benchmark career roles.

    Returns:
        Dict containing role skill taxonomies, importance scores, required levels,
        and data source context.
    """
    if roles_data is None:
        roles_data = load_dataset_json("roles.json")
    if skills_data is None:
        skills_data = load_dataset_json("skills.json")

    skill_lookup = _build_skill_lookup(skills_data)

    roles_summary: List[Dict[str, Any]] = []
    for r in roles_data:
        r_id = r.get("id", "").strip().lower()
        if role_id and r_id != role_id.strip().lower():
            continue

        required_list = []
        for req in r.get("required_skills", []):
            sid = req.get("skill_id", "").strip().lower()
            smeta = skill_lookup.get(sid, {})
            required_list.append({
                "skill_id": sid,
                "skill_name": smeta.get("name", sid.replace("_", " ").title()),
                "category": smeta.get("category", "General Technical"),
                "importance": float(req.get("importance", 1.2)),
                "required_level": req.get("required_level", "intermediate"),
                "is_required": True,
            })

        preferred_list = []
        for pref in r.get("preferred_skills", []):
            sid = pref.get("skill_id", "").strip().lower()
            smeta = skill_lookup.get(sid, {})
            preferred_list.append({
                "skill_id": sid,
                "skill_name": smeta.get("name", sid.replace("_", " ").title()),
                "category": smeta.get("category", "General Technical"),
                "importance": float(pref.get("importance", 1.0)),
                "required_level": pref.get("required_level", "beginner"),
                "is_required": False,
            })

        roles_summary.append({
            "role_id": r_id,
            "role_title": r.get("title", r_id.replace("_", " ").title()),
            "category": r.get("category", "Engineering"),
            "description": r.get("description", ""),
            "typical_experience_years": int(r.get("typical_experience_years", 2)),
            "market_demand_index": float(r.get("market_demand_index", 8.0)),
            "required_skills": required_list,
            "preferred_skills": preferred_list,
            "total_skills_count": len(required_list) + len(preferred_list),
            "required_count": len(required_list),
            "preferred_count": len(preferred_list),
        })

    return {
        "total_roles_evaluated": len(roles_summary),
        "roles": roles_summary,
        "data_source_context": f"Benchmark Role Skill Architecture (data/roles.json, N={len(roles_summary)} roles)",
        "context_note": f"{DATASET_NOTICE}, skill specifications mapped across benchmark engineering roles.",
    }


# ==============================================================================
# 3. Skills by Category
# ==============================================================================
def get_skills_by_category(
    skills_data: Optional[List[Dict[str, Any]]] = None,
    jobs_data: Optional[List[Dict[str, Any]]] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Aggregates canonical skills and job requisition demand by technology category.

    Returns:
        Dict containing categories, count of distinct skills, total requisition mentions,
        relative share of total demand, and top skills per category.
    """
    if skills_data is None:
        skills_data = load_dataset_json("skills.json")
    if jobs_data is None:
        jobs_data = load_dataset_json("jobs.json")

    # Aggregate job demand per skill
    job_skill_counts = Counter()
    for job in jobs_data:
        for sk in job.get("skills", []):
            clean_sk = sk.strip().lower()
            if clean_sk:
                job_skill_counts[clean_sk] += 1

    total_demand_occurrences = sum(job_skill_counts.values()) or 1

    # Standardize category names for clean visualization
    category_map: Dict[str, List[Dict[str, Any]]] = {}
    for s in skills_data:
        raw_cat = s.get("category", "General Technical").strip()
        # Normalize minor labeling differences
        if raw_cat in ("AI/ML", "Data Science & AI"):
            cat = "Data Science & AI"
        elif raw_cat in ("Web", "Web Development"):
            cat = "Web Development"
        elif raw_cat in ("Cloud", "DevOps", "DevOps & SRE"):
            cat = "Cloud & DevOps"
        elif raw_cat in ("Data", "Databases"):
            cat = "Databases & Data Platforms"
        elif raw_cat in ("Analytics", "Analytics & BI"):
            cat = "Analytics & BI"
        elif raw_cat in ("Cybersecurity",):
            cat = "Cybersecurity"
        elif raw_cat in ("Programming", "Core Engineering"):
            cat = "Programming & Systems"
        else:
            cat = raw_cat

        if cat not in category_map:
            category_map[cat] = []

        sid = s.get("id", "").strip().lower()
        job_count = job_skill_counts.get(sid, 0)
        category_map[cat].append({
            "skill_id": sid,
            "skill_name": s.get("name", sid.replace("_", " ").title()),
            "job_count": job_count,
            "importance_weight": float(s.get("importance_weight", 1.0)),
        })

    categories_summary: List[Dict[str, Any]] = []
    for cat, skills_in_cat in category_map.items():
        cat_demand = sum(item["job_count"] for item in skills_in_cat)
        pct_share = round((cat_demand / total_demand_occurrences) * 100.0, 1)
        # Top 3 skills in this category by job mentions
        sorted_skills = sorted(skills_in_cat, key=lambda x: x["job_count"], reverse=True)
        categories_summary.append({
            "category": cat,
            "unique_skills_count": len(skills_in_cat),
            "job_demand_occurrences": cat_demand,
            "percentage_of_total_demand": pct_share,
            "top_skills": sorted_skills[:4],
        })

    # Sort descending by total job demand occurrences
    categories_summary.sort(key=lambda x: x["job_demand_occurrences"], reverse=True)

    return {
        "total_categories": len(categories_summary),
        "total_demand_occurrences": total_demand_occurrences,
        "categories": categories_summary,
        "data_source_context": "Canonical Taxonomy & Job Requisitions (data/skills.json & data/jobs.json)",
        "context_note": (
            f"{DATASET_NOTICE}, skill inventory and demand occurrences aggregated across "
            f"{len(categories_summary)} functional domain categories."
        ),
    }


# ==============================================================================
# 4. Role Distribution
# ==============================================================================
def get_role_distribution(
    jobs_data: Optional[List[Dict[str, Any]]] = None,
    roles_data: Optional[List[Dict[str, Any]]] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Analyzes role representation and experience band distribution in the dataset.

    Returns:
        Dict containing job counts per role domain, experience distribution,
        and benchmark role counts.
    """
    if jobs_data is None:
        jobs_data = load_dataset_json("jobs.json")
    if roles_data is None:
        roles_data = load_dataset_json("roles.json")

    total_jobs = len(jobs_data)
    total_roles = len(roles_data)

    # Classify jobs into broad engineering domains based on title and skill cues
    domain_mapping = {
        "Backend & Systems": 0,
        "Data Science & AI": 0,
        "Analytics & BI": 0,
        "Cloud & DevOps": 0,
        "Frontend & Fullstack": 0,
        "Data Engineering": 0,
        "Cybersecurity": 0,
    }

    experience_bands = {
        "Entry-Level (1-2 years)": 0,
        "Mid-Level (3-4 years)": 0,
        "Senior / Lead (5+ years)": 0,
    }

    all_exp_years = []

    for job in jobs_data:
        title = job.get("title", "").lower()
        skills = set(job.get("skills", []))
        exp = int(job.get("experience_years_min", 1))
        all_exp_years.append(exp)

        if exp <= 2:
            experience_bands["Entry-Level (1-2 years)"] += 1
        elif exp <= 4:
            experience_bands["Mid-Level (3-4 years)"] += 1
        else:
            experience_bands["Senior / Lead (5+ years)"] += 1

        if any(w in title for w in ["machine learning", "data science", "ml", "nlp", "computer vision", "ai"]):
            domain_mapping["Data Science & AI"] += 1
        elif any(w in title for w in ["analyst", "analytics", "business intelligence", "power bi", "reporting"]):
            domain_mapping["Analytics & BI"] += 1
        elif any(w in title for w in ["devops", "cloud", "sre", "reliability", "kubernetes", "terraform", "infrastructure"]):
            domain_mapping["Cloud & DevOps"] += 1
        elif any(w in title for w in ["frontend", "full stack", "fullstack", "react", "next.js", "ui/ux"]):
            domain_mapping["Frontend & Fullstack"] += 1
        elif any(w in title for w in ["data platform", "etl", "data pipeline", "kafka", "data engineer"]):
            domain_mapping["Data Engineering"] += 1
        elif any(w in title for w in ["security", "soc", "iam", "cybersecurity"]):
            domain_mapping["Cybersecurity"] += 1
        else:
            domain_mapping["Backend & Systems"] += 1

    domains_list = []
    for domain_name, count in domain_mapping.items():
        pct = round((count / total_jobs) * 100.0, 1) if total_jobs > 0 else 0.0
        domains_list.append({
            "domain": domain_name,
            "job_count": count,
            "percentage": pct,
        })
    domains_list.sort(key=lambda x: x["job_count"], reverse=True)

    exp_list = []
    for band_name, count in experience_bands.items():
        pct = round((count / total_jobs) * 100.0, 1) if total_jobs > 0 else 0.0
        exp_list.append({
            "experience_band": band_name,
            "job_count": count,
            "percentage": pct,
        })

    avg_experience = round(sum(all_exp_years) / len(all_exp_years), 1) if all_exp_years else 0.0

    return {
        "total_jobs": total_jobs,
        "total_benchmark_roles": total_roles,
        "average_minimum_experience_years": avg_experience,
        "domain_distribution": domains_list,
        "experience_band_distribution": exp_list,
        "data_source_context": f"Seeded Job Postings & Benchmark Roles (data/jobs.json & data/roles.json, N={total_jobs} jobs)",
        "context_note": (
            f"{DATASET_NOTICE}, role specializations and experience requirements distribution "
            f"across {total_jobs} seeded job requisitions."
        ),
    }


# ==============================================================================
# 5. Skill-Gap Trends Within the Available Dataset
# ==============================================================================
def get_skill_gap_trends(
    jobs_data: Optional[List[Dict[str, Any]]] = None,
    candidates_data: Optional[List[Dict[str, Any]]] = None,
    skills_data: Optional[List[Dict[str, Any]]] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Analyzes empirical skill-gap trends by comparing job demand vs candidate profile supply.

    Calculates:
        - Job Demand % = (jobs requiring skill / total jobs) * 100
        - Candidate Supply % = (candidates possessing skill / total candidates) * 100
        - Gap Delta % = Job Demand % - Candidate Supply %
        - Gap Status: High Unmet Demand, Moderate Gap, Balanced, High Supply

    Returns:
        Dict containing skill-gap deltas, status classifications, and data source context.
    """
    if jobs_data is None:
        jobs_data = load_dataset_json("jobs.json")
    if candidates_data is None:
        candidates_data = load_dataset_json("demo_candidates.json")
    if skills_data is None:
        skills_data = load_dataset_json("skills.json")

    total_jobs = len(jobs_data)
    total_candidates = len(candidates_data)
    skill_lookup = _build_skill_lookup(skills_data)

    if total_jobs == 0 or total_candidates == 0:
        return {
            "total_jobs": total_jobs,
            "total_candidates": total_candidates,
            "gap_trends": [],
            "data_source_context": "Cross-Analysis of Seeded Jobs vs Demo Candidates (Empty dataset)",
            "context_note": f"{DATASET_NOTICE}, insufficient records to compute gap deltas.",
        }

    # Count skill occurrences in jobs
    job_counts = Counter()
    for job in jobs_data:
        for sk in job.get("skills", []):
            clean_sk = sk.strip().lower()
            if clean_sk:
                job_counts[clean_sk] += 1

    # Count skill occurrences in candidates
    candidate_counts = Counter()
    for cand in candidates_data:
        for sk in cand.get("skills", []):
            clean_sk = sk.strip().lower()
            if clean_sk:
                candidate_counts[clean_sk] += 1

    all_evaluated_skills = set(job_counts.keys()).union(set(candidate_counts.keys()))

    gap_records: List[Dict[str, Any]] = []
    for sid in all_evaluated_skills:
        j_count = job_counts.get(sid, 0)
        c_count = candidate_counts.get(sid, 0)

        # Only evaluate skills that have some presence in either jobs or candidates
        if j_count == 0 and c_count == 0:
            continue

        demand_pct = round((j_count / total_jobs) * 100.0, 1)
        supply_pct = round((c_count / total_candidates) * 100.0, 1)
        delta_pct = round(demand_pct - supply_pct, 1)

        if delta_pct >= 15.0:
            status = "High Unmet Demand"
        elif delta_pct >= 5.0:
            status = "Moderate Gap"
        elif delta_pct >= -10.0:
            status = "Supply-Demand Balanced"
        else:
            status = "High Candidate Supply"

        smeta = skill_lookup.get(sid, {})
        gap_records.append({
            "skill_id": sid,
            "skill_name": smeta.get("name", sid.replace("_", " ").title()),
            "category": smeta.get("category", "General Technical"),
            "job_demand_count": j_count,
            "job_demand_pct": demand_pct,
            "candidate_supply_count": c_count,
            "candidate_supply_pct": supply_pct,
            "gap_delta_pct": delta_pct,
            "gap_status": status,
        })

    # Sort descending by gap delta (highest unmet employer demand first)
    gap_records.sort(key=lambda x: x["gap_delta_pct"], reverse=True)

    high_unmet_skills = [s["skill_name"] for s in gap_records if s["gap_status"] == "High Unmet Demand"]
    summary_text = (
        f"{DATASET_NOTICE}, highest unmet employer demand exists in: "
        f"{', '.join(high_unmet_skills[:4]) if high_unmet_skills else 'None'}."
    )

    return {
        "total_jobs_evaluated": total_jobs,
        "total_candidates_evaluated": total_candidates,
        "total_skills_evaluated": len(gap_records),
        "gap_trends": gap_records,
        "data_source_context": (
            f"Comparative Cross-Analysis: Seeded Jobs (data/jobs.json, N={total_jobs}) vs. "
            f"Demo Candidates (data/demo_candidates.json, N={total_candidates})"
        ),
        "context_note": summary_text,
    }


# ==============================================================================
# 6. Master Aggregator
# ==============================================================================
_MASTER_INTELLIGENCE_CACHE: Dict[Any, Dict[str, Any]] = {}


def get_complete_market_intelligence(
    top_n_skills: Optional[int] = 15,
    role_id: Optional[str] = None,
    data_dir: Optional[str] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Compiles the full lightweight market intelligence payload from seeded datasets with caching."""
    cache_key = (top_n_skills or 15, role_id, str(data_dir) if data_dir else None)
    if db is None and cache_key in _MASTER_INTELLIGENCE_CACHE:
        return _MASTER_INTELLIGENCE_CACHE[cache_key]

    resolved_dir = resolve_data_directory(data_dir)
    jobs_data = load_dataset_json("jobs.json", resolved_dir)
    roles_data = load_dataset_json("roles.json", resolved_dir)
    skills_data = load_dataset_json("skills.json", resolved_dir)
    candidates_data = load_dataset_json("demo_candidates.json", resolved_dir)

    freq_skills = get_most_frequently_requested_skills(
        jobs_data=jobs_data,
        skills_data=skills_data,
        top_n=top_n_skills,
        db=db,
    )

    role_skills = get_skills_by_role(
        role_id=role_id,
        roles_data=roles_data,
        skills_data=skills_data,
        db=db,
    )

    cat_skills = get_skills_by_category(
        skills_data=skills_data,
        jobs_data=jobs_data,
        db=db,
    )

    role_dist = get_role_distribution(
        jobs_data=jobs_data,
        roles_data=roles_data,
        db=db,
    )

    gap_trends = get_skill_gap_trends(
        jobs_data=jobs_data,
        candidates_data=candidates_data,
        skills_data=skills_data,
        db=db,
    )

    result = {
        "metadata": {
            "total_jobs": len(jobs_data),
            "total_roles": len(roles_data),
            "total_skills": len(skills_data),
            "total_candidates": len(candidates_data),
            "dataset_notice": DATASET_NOTICE,
            "disclaimer": (
                "DEMO & SEEDED DATASET ENVIRONMENT: All statistics are derived strictly from "
                "local repository benchmark data. Do not present sample/demo data as live market statistics. "
                "No live web-scraping active."
            ),
            "system_disclaimer": (
                "Career Intelligence provides decision support based on the available profile and dataset. "
                "It does not guarantee employment, hiring outcomes or career success."
            ),
            "predictive_forecasting_active": False,
            "predictive_forecasting_note": NO_FORECASTING_NOTICE,
        },
        "most_frequently_requested_skills": freq_skills,
        "skills_by_role": role_skills,
        "skills_by_category": cat_skills,
        "role_distribution": role_dist,
        "skill_gap_trends": gap_trends,
    }
    if db is None:
        _MASTER_INTELLIGENCE_CACHE[cache_key] = result
    return result
