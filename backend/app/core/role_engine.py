"""Job and Career Role Intelligence Layer.

Defines standardized career role profiles, skill weightings, and converts
custom job descriptions into normalized role skill profiles.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.taxonomy import taxonomy
from app.core.extractor import extractor


class RoleSkillRequirement(BaseModel):
    skill_id: str
    canonical_name: str
    category: str
    weight: float = 1.0  # Importance factor (1.0 - 2.0)
    is_required: bool = True
    level: str = "intermediate"  # beginner, intermediate, advanced


class CareerRoleProfile(BaseModel):
    id: str
    title: str
    category: str
    summary: str
    typical_experience_years: int = 2
    required_skills: List[RoleSkillRequirement]
    preferred_skills: List[RoleSkillRequirement]
    market_demand_index: float = 8.5  # 1.0 - 10.0 scale


# Curated Career Roles Repository
PREDEFINED_ROLES: Dict[str, CareerRoleProfile] = {
    "data_scientist": CareerRoleProfile(
        id="data_scientist",
        title="Data Scientist",
        category="Data Science & AI",
        summary="Designs machine learning models, statistical experiments, and extracts predictive insights from complex datasets.",
        typical_experience_years=3,
        market_demand_index=9.2,
        required_skills=[
            RoleSkillRequirement(skill_id="python", canonical_name="Python", category="Programming", weight=1.5, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="sql", canonical_name="SQL", category="Programming", weight=1.3, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="statistics_probability", canonical_name="Statistics & Probability", category="Data Science & AI", weight=1.4, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="machine_learning", canonical_name="Machine Learning", category="Data Science & AI", weight=1.5, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="pandas", canonical_name="Pandas", category="Data Science & AI", weight=1.2, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="scikit_learn", canonical_name="Scikit-Learn", category="Data Science & AI", weight=1.3, is_required=True, level="intermediate"),
        ],
        preferred_skills=[
            RoleSkillRequirement(skill_id="deep_learning", canonical_name="Deep Learning", category="Data Science & AI", weight=1.2, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="nlp", canonical_name="Natural Language Processing (NLP)", category="Data Science & AI", weight=1.1, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="docker", canonical_name="Docker & Containerization", category="Cloud & Infrastructure", weight=1.0, is_required=False, level="beginner"),
            RoleSkillRequirement(skill_id="aws", canonical_name="Amazon Web Services (AWS)", category="Cloud & Infrastructure", weight=1.1, is_required=False, level="beginner"),
            RoleSkillRequirement(skill_id="data_visualization", canonical_name="Data Visualization", category="Analytics & BI", weight=1.0, is_required=False, level="intermediate"),
        ]
    ),
    "ml_engineer": CareerRoleProfile(
        id="ml_engineer",
        title="Machine Learning Engineer",
        category="Data Science & AI",
        summary="Engineers, scales, and deploys production-grade machine learning and deep learning systems and pipelines.",
        typical_experience_years=3,
        market_demand_index=9.5,
        required_skills=[
            RoleSkillRequirement(skill_id="python", canonical_name="Python", category="Programming", weight=1.5, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="machine_learning", canonical_name="Machine Learning", category="Data Science & AI", weight=1.5, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="pytorch", canonical_name="PyTorch", category="Data Science & AI", weight=1.4, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="docker", canonical_name="Docker & Containerization", category="Cloud & Infrastructure", weight=1.3, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="fastapi", canonical_name="FastAPI", category="Web Development", weight=1.2, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="git", canonical_name="Git & Version Control", category="DevOps & SRE", weight=1.1, is_required=True, level="intermediate"),
        ],
        preferred_skills=[
            RoleSkillRequirement(skill_id="kubernetes", canonical_name="Kubernetes (K8s)", category="Cloud & Infrastructure", weight=1.2, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="llms", canonical_name="Large Language Models (LLMs) & GenAI", category="Data Science & AI", weight=1.3, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="aws", canonical_name="Amazon Web Services (AWS)", category="Cloud & Infrastructure", weight=1.2, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="devops_cicd", canonical_name="CI/CD Pipelines", category="DevOps & SRE", weight=1.0, is_required=False, level="beginner"),
        ]
    ),
    "data_analyst": CareerRoleProfile(
        id="data_analyst",
        title="Data Analyst",
        category="Analytics & BI",
        summary="Translates data into business insights, designs dashboards, and supports decision-making processes.",
        typical_experience_years=2,
        market_demand_index=8.8,
        required_skills=[
            RoleSkillRequirement(skill_id="sql", canonical_name="SQL", category="Programming", weight=1.5, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="excel", canonical_name="Advanced Excel", category="Analytics & BI", weight=1.3, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="data_analysis", canonical_name="Data Analysis", category="Analytics & BI", weight=1.4, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="power_bi", canonical_name="Power BI", category="Analytics & BI", weight=1.3, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="data_visualization", canonical_name="Data Visualization", category="Analytics & BI", weight=1.2, is_required=True, level="intermediate"),
        ],
        preferred_skills=[
            RoleSkillRequirement(skill_id="python", canonical_name="Python", category="Programming", weight=1.2, is_required=False, level="beginner"),
            RoleSkillRequirement(skill_id="tableau", canonical_name="Tableau", category="Analytics & BI", weight=1.1, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="statistics_probability", canonical_name="Statistics & Probability", category="Data Science & AI", weight=1.1, is_required=False, level="beginner"),
        ]
    ),
    "fullstack_developer": CareerRoleProfile(
        id="fullstack_developer",
        title="Full Stack Software Engineer",
        category="Web Development",
        summary="Builds end-to-end web applications, encompassing user interfaces, RESTful APIs, and database persistence.",
        typical_experience_years=3,
        market_demand_index=9.1,
        required_skills=[
            RoleSkillRequirement(skill_id="javascript", canonical_name="JavaScript", category="Programming", weight=1.4, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="typescript", canonical_name="TypeScript", category="Programming", weight=1.3, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="react", canonical_name="React.js", category="Web Development", weight=1.4, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="node_js", canonical_name="Node.js", category="Web Development", weight=1.3, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="postgresql", canonical_name="PostgreSQL", category="Databases & Storage", weight=1.2, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="git", canonical_name="Git & Version Control", category="DevOps & SRE", weight=1.1, is_required=True, level="intermediate"),
        ],
        preferred_skills=[
            RoleSkillRequirement(skill_id="next_js", canonical_name="Next.js", category="Web Development", weight=1.2, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="docker", canonical_name="Docker & Containerization", category="Cloud & Infrastructure", weight=1.1, is_required=False, level="beginner"),
            RoleSkillRequirement(skill_id="tailwind_css", canonical_name="Tailwind CSS", category="Web Development", weight=1.0, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="redis", canonical_name="Redis", category="Databases & Storage", weight=1.0, is_required=False, level="beginner"),
        ]
    ),
    "backend_engineer": CareerRoleProfile(
        id="backend_engineer",
        title="Backend Software Engineer",
        category="Web Development",
        summary="Engineers scalable server-side systems, RESTful microservices, and reliable database architectures.",
        typical_experience_years=3,
        market_demand_index=9.0,
        required_skills=[
            RoleSkillRequirement(skill_id="python", canonical_name="Python", category="Programming", weight=1.4, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="sql", canonical_name="SQL", category="Programming", weight=1.3, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="fastapi", canonical_name="FastAPI", category="Web Development", weight=1.3, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="postgresql", canonical_name="PostgreSQL", category="Databases & Storage", weight=1.3, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="docker", canonical_name="Docker & Containerization", category="Cloud & Infrastructure", weight=1.2, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="git", canonical_name="Git & Version Control", category="DevOps & SRE", weight=1.1, is_required=True, level="intermediate"),
        ],
        preferred_skills=[
            RoleSkillRequirement(skill_id="redis", canonical_name="Redis", category="Databases & Storage", weight=1.2, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="kafka", canonical_name="Apache Kafka", category="Databases & Storage", weight=1.1, is_required=False, level="beginner"),
            RoleSkillRequirement(skill_id="aws", canonical_name="Amazon Web Services (AWS)", category="Cloud & Infrastructure", weight=1.2, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="system_design", canonical_name="System Design & Architecture", category="Core Engineering", weight=1.3, is_required=False, level="intermediate"),
        ]
    ),
    "cloud_devops_engineer": CareerRoleProfile(
        id="cloud_devops_engineer",
        title="Cloud & DevOps Engineer",
        category="DevOps & SRE",
        summary="Automates cloud infrastructure, manages Kubernetes clusters, and guarantees high availability and CI/CD.",
        typical_experience_years=3,
        market_demand_index=9.3,
        required_skills=[
            RoleSkillRequirement(skill_id="linux", canonical_name="Linux System Administration", category="DevOps & SRE", weight=1.4, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="docker", canonical_name="Docker & Containerization", category="Cloud & Infrastructure", weight=1.4, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="kubernetes", canonical_name="Kubernetes (K8s)", category="Cloud & Infrastructure", weight=1.4, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="aws", canonical_name="Amazon Web Services (AWS)", category="Cloud & Infrastructure", weight=1.4, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="devops_cicd", canonical_name="CI/CD Pipelines", category="DevOps & SRE", weight=1.3, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="git", canonical_name="Git & Version Control", category="DevOps & SRE", weight=1.1, is_required=True, level="intermediate"),
        ],
        preferred_skills=[
            RoleSkillRequirement(skill_id="terraform", canonical_name="Terraform (IaC)", category="Cloud & Infrastructure", weight=1.3, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="bash_shell", canonical_name="Bash & Shell Scripting", category="Programming", weight=1.1, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="monitoring", canonical_name="Monitoring & Observability", category="DevOps & SRE", weight=1.2, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="python", canonical_name="Python", category="Programming", weight=1.1, is_required=False, level="intermediate"),
        ]
    ),
    "cybersecurity_analyst": CareerRoleProfile(
        id="cybersecurity_analyst",
        title="Cybersecurity Analyst",
        category="Cybersecurity",
        summary="Protects organizational infrastructure, assesses vulnerabilities, and audits security compliance.",
        typical_experience_years=2,
        market_demand_index=8.9,
        required_skills=[
            RoleSkillRequirement(skill_id="network_security", canonical_name="Network & Cloud Security", category="Cybersecurity", weight=1.5, is_required=True, level="advanced"),
            RoleSkillRequirement(skill_id="linux", canonical_name="Linux System Administration", category="DevOps & SRE", weight=1.3, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="iam_auth", canonical_name="IAM & Authentication (OAuth/JWT)", category="Cybersecurity", weight=1.3, is_required=True, level="intermediate"),
            RoleSkillRequirement(skill_id="penetration_testing", canonical_name="Penetration Testing & Vulnerability Assessment", category="Cybersecurity", weight=1.4, is_required=True, level="intermediate"),
        ],
        preferred_skills=[
            RoleSkillRequirement(skill_id="python", canonical_name="Python", category="Programming", weight=1.2, is_required=False, level="intermediate"),
            RoleSkillRequirement(skill_id="aws", canonical_name="Amazon Web Services (AWS)", category="Cloud & Infrastructure", weight=1.1, is_required=False, level="beginner"),
            RoleSkillRequirement(skill_id="monitoring", canonical_name="Monitoring & Observability", category="DevOps & SRE", weight=1.1, is_required=False, level="intermediate"),
        ]
    )
}


import json
from pathlib import Path

def _resolve_roles_file() -> Optional[Path]:
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "data" / "roles.json",
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "roles.json",
        Path.cwd() / "data" / "roles.json",
        Path("/Users/pawankumar/Documents/New_assignmnet/Bharat 2.0/data/roles.json"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


class RoleEngine:
    def __init__(self):
        self.predefined_roles = dict(PREDEFINED_ROLES)
        self._load_seed_roles()

    def _load_seed_roles(self):
        """Loads canonical roles from data/roles.json to provide comprehensive career paths."""
        rf = _resolve_roles_file()
        if not rf:
            return
        try:
            with open(rf, "r", encoding="utf-8") as f:
                data = json.load(f)
            for r in data:
                r_id = r.get("id")
                if not r_id:
                    continue
                # Map role if not already in predefined or add as complementary
                reqs = []
                for s in r.get("required_skills", []):
                    s_id = s.get("skill_id")
                    s_def = taxonomy.get_skill(s_id)
                    name = s_def.name if s_def else s_id.replace("_", " ").title()
                    cat = s_def.category if s_def else "General"
                    reqs.append(RoleSkillRequirement(
                        skill_id=s_id,
                        canonical_name=name,
                        category=cat,
                        weight=float(s.get("importance", 1.2)),
                        is_required=True,
                        level=s.get("required_level", "intermediate")
                    ))
                prefs = []
                for s in r.get("preferred_skills", []):
                    s_id = s.get("skill_id")
                    s_def = taxonomy.get_skill(s_id)
                    name = s_def.name if s_def else s_id.replace("_", " ").title()
                    cat = s_def.category if s_def else "General"
                    prefs.append(RoleSkillRequirement(
                        skill_id=s_id,
                        canonical_name=name,
                        category=cat,
                        weight=float(s.get("importance", 1.0)),
                        is_required=False,
                        level=s.get("required_level", "beginner")
                    ))

                if r_id not in self.predefined_roles:
                    self.predefined_roles[r_id] = CareerRoleProfile(
                        id=r_id,
                        title=r.get("title", r_id.replace("_", " ").title()),
                        category=r.get("category", "General"),
                        summary=r.get("description", ""),
                        typical_experience_years=int(r.get("typical_experience_years", 2)),
                        market_demand_index=float(r.get("market_demand_index", 8.5)),
                        required_skills=reqs,
                        preferred_skills=prefs
                    )
            # Aliases for cross-referencing
            if "backend_engineer" in self.predefined_roles and "backend_developer" not in self.predefined_roles:
                self.predefined_roles["backend_developer"] = self.predefined_roles["backend_engineer"]
            elif "backend_developer" in self.predefined_roles and "backend_engineer" not in self.predefined_roles:
                self.predefined_roles["backend_engineer"] = self.predefined_roles["backend_developer"]

            if "cloud_devops_engineer" in self.predefined_roles and "devops_engineer" not in self.predefined_roles:
                self.predefined_roles["devops_engineer"] = self.predefined_roles["cloud_devops_engineer"]
        except Exception:
            pass

    def get_role(self, role_id: str) -> Optional[CareerRoleProfile]:
        return self.predefined_roles.get(role_id)

    def get_all_roles(self) -> List[CareerRoleProfile]:
        # Return unique profiles by ID
        seen = set()
        unique = []
        for r in self.predefined_roles.values():
            if r.id not in seen:
                seen.add(r.id)
                unique.append(r)
        return unique

    def parse_job_description_to_role(self, title: str, jd_text: str) -> CareerRoleProfile:
        """Converts an arbitrary pasted Job Description into a standardized role profile."""
        report = extractor.extract_from_text(jd_text, source="job_description")
        
        # Sort extracted skills by frequency & confidence
        sorted_skills = sorted(report.skills, key=lambda s: (s.frequency, s.confidence), reverse=True)
        
        required: List[RoleSkillRequirement] = []
        preferred: List[RoleSkillRequirement] = []

        # High frequency / high prominence skills become required, remainder preferred
        cutoff = max(3, len(sorted_skills) // 2)
        for i, s in enumerate(sorted_skills):
            req = RoleSkillRequirement(
                skill_id=s.canonical_id,
                canonical_name=s.canonical_name,
                category=s.category,
                weight=1.3 if i < cutoff else 1.0,
                is_required=(i < cutoff),
                level="intermediate"
            )
            if i < cutoff:
                required.append(req)
            else:
                preferred.append(req)

        # Fallback if JD text had very sparse recognizable skills
        if not required:
            # Default to Python, Git if nothing found
            required.append(RoleSkillRequirement(
                skill_id="python", canonical_name="Python", category="Programming", weight=1.0, is_required=True
            ))

        return CareerRoleProfile(
            id="custom_role_" + str(abs(hash(title + jd_text[:50])) % 100000),
            title=title or "Custom Job Specification",
            category="Custom Ingestion",
            summary=jd_text[:200] + ("..." if len(jd_text) > 200 else ""),
            typical_experience_years=2,
            market_demand_index=8.0,
            required_skills=required,
            preferred_skills=preferred
        )

    def ingest_custom_job_description(self, jd_text: str, title: str = "Custom Role") -> CareerRoleProfile:
        """Parses and ingests arbitrary job description or role text into a CareerRoleProfile."""
        return self.parse_job_description_to_role(title=title, jd_text=jd_text)


role_engine = RoleEngine()
