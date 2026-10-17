"""Standardized Skill Taxonomy & Classification Foundation.

Implements Stage 2 & 6:
Standardized canonical skills, aliases, categories, prerequisites, and relationships.
Ensures 'Python', 'Python 3', 'py' all map to the canonical entity 'Python'.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    id: str = Field(..., description="Unique slug identifier (e.g. machine_learning)")
    name: str = Field(..., description="Canonical human-readable name (e.g. Machine Learning)")
    category: str = Field(..., description="Standardized category name")
    aliases: List[str] = Field(default_factory=list, description="Synonyms, acronyms, and variations")
    description: str = Field("", description="Skill summary")
    prerequisites: List[str] = Field(default_factory=list, description="IDs of prerequisite skills")
    adjacent_skills: List[str] = Field(default_factory=list, description="IDs of closely related skills")
    related_skills: List[str] = Field(default_factory=list, description="IDs of related skills")
    importance_weight: float = Field(1.0, description="Base weight for gap prioritization")

    def model_post_init(self, __context):
        if not self.related_skills and self.adjacent_skills:
            self.related_skills = list(self.adjacent_skills)
        elif not self.adjacent_skills and self.related_skills:
            self.adjacent_skills = list(self.related_skills)

    @property
    def importance(self) -> float:
        return self.importance_weight


# Standardized Taxonomy Categories
CATEGORIES = [
    "Programming",
    "Data Science & AI",
    "Analytics & BI",
    "Cloud & Infrastructure",
    "Databases & Storage",
    "Web Development",
    "DevOps & SRE",
    "Cybersecurity",
    "Core Engineering"
]

SKILL_CATALOG: Dict[str, SkillDefinition] = {
    # ------------------ Programming ------------------
    "python": SkillDefinition(
        id="python",
        name="Python",
        category="Programming",
        aliases=["python", "python3", "python 3", "py", "cpython"],
        description="High-level, interpreted programming language widely used in AI, data science, and backend development.",
        prerequisites=[],
        adjacent_skills=["sql", "bash_shell", "fastapi", "django"],
        importance_weight=1.2
    ),
    "java": SkillDefinition(
        id="java",
        name="Java",
        category="Programming",
        aliases=["java", "core java", "java 8", "java 11", "java 17", "jdk", "jvm"],
        description="Object-oriented programming language designed for portability and enterprise software.",
        prerequisites=["object_oriented_programming"],
        adjacent_skills=["spring_boot", "kotlin", "sql"],
        importance_weight=1.0
    ),
    "javascript": SkillDefinition(
        id="javascript",
        name="JavaScript",
        category="Programming",
        aliases=["javascript", "js", "ecmascript", "es6", "vanilla js", "modern js"],
        description="Dynamic scripting language essential for modern web applications.",
        prerequisites=[],
        adjacent_skills=["typescript", "react", "node_js", "html5", "css3"],
        importance_weight=1.1
    ),
    "typescript": SkillDefinition(
        id="typescript",
        name="TypeScript",
        category="Programming",
        aliases=["typescript", "ts"],
        description="Statically typed superset of JavaScript enhancing maintainability and code quality.",
        prerequisites=["javascript"],
        adjacent_skills=["react", "next_js", "node_js"],
        importance_weight=1.1
    ),
    "sql": SkillDefinition(
        id="sql",
        name="SQL",
        category="Programming",
        aliases=["sql", "structured query language", "ansi sql", "pl/sql", "t-sql"],
        description="Domain-specific language for managing and querying relational databases.",
        prerequisites=[],
        adjacent_skills=["postgresql", "mysql", "data_analysis"],
        importance_weight=1.2
    ),
    "cpp": SkillDefinition(
        id="cpp",
        name="C++",
        category="Programming",
        aliases=["c++", "cpp", "c plus plus"],
        description="High-performance compiled language used in systems, game engines, and low-latency infrastructure.",
        prerequisites=["object_oriented_programming"],
        adjacent_skills=["c", "data_structures_algorithms"],
        importance_weight=1.0
    ),
    "golang": SkillDefinition(
        id="golang",
        name="Go (Golang)",
        category="Programming",
        aliases=["go", "golang"],
        description="Statically typed, compiled language engineered by Google for concurrent cloud services.",
        prerequisites=[],
        adjacent_skills=["docker", "kubernetes", "microservices"],
        importance_weight=1.0
    ),
    "bash_shell": SkillDefinition(
        id="bash_shell",
        name="Bash & Shell Scripting",
        category="Programming",
        aliases=["bash", "shell", "shell scripting", "sh", "zsh", "cli scripting"],
        description="Unix shell and command language for system automation.",
        prerequisites=["linux"],
        adjacent_skills=["linux", "devops_cicd", "docker"],
        importance_weight=0.9
    ),
    "r": SkillDefinition(
        id="r",
        name="R (Programming Language)",
        category="Programming",
        aliases=["r", "r language", "r programming", "r script", "r studio"],
        description="Programming language and environment for statistical computing and graphics.",
        prerequisites=[],
        adjacent_skills=["python", "statistics_probability", "data_analysis"],
        importance_weight=1.0
    ),

    # ------------------ Data Science & AI ------------------
    "machine_learning": SkillDefinition(
        id="machine_learning",
        name="Machine Learning",
        category="Data Science & AI",
        aliases=["machine learning", "ml", "machine-learning", "supervised learning", "unsupervised learning"],
        description="Algorithms and statistical models that computer systems use to perform tasks without explicit instructions.",
        prerequisites=["python", "statistics_probability", "linear_algebra"],
        adjacent_skills=["scikit_learn", "deep_learning", "data_science", "pandas"],
        importance_weight=1.3
    ),
    "deep_learning": SkillDefinition(
        id="deep_learning",
        name="Deep Learning",
        category="Data Science & AI",
        aliases=["deep learning", "dl", "deep-learning", "neural networks", "artificial neural networks", "ann", "cnn", "rnn"],
        description="Subfield of machine learning based on artificial neural networks with representation learning.",
        prerequisites=["machine_learning", "python"],
        adjacent_skills=["pytorch", "tensorflow", "computer_vision", "nlp"],
        importance_weight=1.2
    ),
    "nlp": SkillDefinition(
        id="nlp",
        name="Natural Language Processing",
        category="Data Science & AI",
        aliases=["natural language processing", "nlp", "natural language processing (nlp)", "text processing", "text mining", "linguistic analysis"],
        description="AI branch focused on enabling computers to understand, interpret, and manipulate human language.",
        prerequisites=["machine_learning", "python"],
        adjacent_skills=["llms", "huggingface", "transformers", "deep_learning"],
        importance_weight=1.2
    ),
    "llms": SkillDefinition(
        id="llms",
        name="Large Language Models (LLMs) & GenAI",
        category="Data Science & AI",
        aliases=["large language models", "llm", "llms", "generative ai", "genai", "prompt engineering", "langchain", "rag", "retrieval augmented generation"],
        description="Advanced neural network architectures trained on massive text corpora for text and content generation.",
        prerequisites=["nlp", "deep_learning"],
        adjacent_skills=["huggingface", "vector_databases", "python"],
        importance_weight=1.2
    ),
    "computer_vision": SkillDefinition(
        id="computer_vision",
        name="Computer Vision",
        category="Data Science & AI",
        aliases=["computer vision", "cv", "image processing", "opencv", "object detection", "yolo"],
        description="Field of AI that trains computers to interpret and understand the visual world.",
        prerequisites=["deep_learning", "python"],
        adjacent_skills=["pytorch", "tensorflow"],
        importance_weight=1.1
    ),
    "scikit_learn": SkillDefinition(
        id="scikit_learn",
        name="Scikit-Learn",
        category="Data Science & AI",
        aliases=["scikit-learn", "scikitlearn", "sklearn"],
        description="Fundamental Python library for classical machine learning and data mining.",
        prerequisites=["python", "statistics_probability"],
        adjacent_skills=["machine_learning", "pandas", "numpy"],
        importance_weight=1.1
    ),
    "pytorch": SkillDefinition(
        id="pytorch",
        name="PyTorch",
        category="Data Science & AI",
        aliases=["pytorch", "torch"],
        description="Leading open-source deep learning framework based on Torch for research and production.",
        prerequisites=["deep_learning", "python"],
        adjacent_skills=["deep_learning", "tensorflow", "huggingface"],
        importance_weight=1.2
    ),
    "tensorflow": SkillDefinition(
        id="tensorflow",
        name="TensorFlow & Keras",
        category="Data Science & AI",
        aliases=["tensorflow", "tf", "keras", "tf.keras"],
        description="End-to-end open source platform for machine learning developed by Google.",
        prerequisites=["deep_learning", "python"],
        adjacent_skills=["deep_learning", "pytorch"],
        importance_weight=1.1
    ),
    "pandas": SkillDefinition(
        id="pandas",
        name="Pandas",
        category="Data Science & AI",
        aliases=["pandas", "pd"],
        description="Python data manipulation and analysis library offering high-performance data structures.",
        prerequisites=["python"],
        adjacent_skills=["numpy", "data_analysis", "data_science"],
        importance_weight=1.1
    ),
    "numpy": SkillDefinition(
        id="numpy",
        name="NumPy",
        category="Data Science & AI",
        aliases=["numpy", "np"],
        description="Fundamental package for scientific computing with multi-dimensional arrays in Python.",
        prerequisites=["python"],
        adjacent_skills=["pandas", "scipy", "scikit_learn"],
        importance_weight=1.0
    ),
    "statistics_probability": SkillDefinition(
        id="statistics_probability",
        name="Statistics & Probability",
        category="Data Science & AI",
        aliases=["statistics", "probability", "statistical modeling", "hypothesis testing", "inferential statistics"],
        description="Mathematical discipline dealing with data collection, analysis, interpretation, and inference.",
        prerequisites=[],
        adjacent_skills=["machine_learning", "data_analysis", "a_b_testing"],
        importance_weight=1.2
    ),

    # ------------------ Analytics & BI ------------------
    "data_analysis": SkillDefinition(
        id="data_analysis",
        name="Data Analysis",
        category="Analytics & BI",
        aliases=["data analysis", "exploratory data analysis", "eda", "data analytics"],
        description="Process of inspecting, cleansing, transforming, and modeling data to discover useful insights.",
        prerequisites=["sql", "excel"],
        adjacent_skills=["pandas", "power_bi", "tableau", "statistics_probability"],
        importance_weight=1.2
    ),
    "power_bi": SkillDefinition(
        id="power_bi",
        name="Power BI",
        category="Analytics & BI",
        aliases=["power bi", "powerbi", "microsoft power bi", "dax", "power query"],
        description="Interactive business analytics service by Microsoft delivering actionable dashboards.",
        prerequisites=["sql", "excel"],
        adjacent_skills=["tableau", "data_visualization", "data_analysis"],
        importance_weight=1.1
    ),
    "tableau": SkillDefinition(
        id="tableau",
        name="Tableau",
        category="Analytics & BI",
        aliases=["tableau", "tableau desktop", "tableau server"],
        description="Visual analytics platform transforming raw data into shareable interactive dashboards.",
        prerequisites=["sql"],
        adjacent_skills=["power_bi", "data_visualization", "data_analysis"],
        importance_weight=1.1
    ),
    "excel": SkillDefinition(
        id="excel",
        name="Advanced Excel",
        category="Analytics & BI",
        aliases=["excel", "microsoft excel", "ms excel", "vlookup", "pivot tables", "excel formulas"],
        description="Spreadsheet tool for calculations, pivot tables, and statistical summaries.",
        prerequisites=[],
        adjacent_skills=["power_bi", "data_analysis"],
        importance_weight=0.9
    ),
    "data_visualization": SkillDefinition(
        id="data_visualization",
        name="Data Visualization",
        category="Analytics & BI",
        aliases=["data visualization", "dataviz", "matplotlib", "seaborn", "plotly", "charting"],
        description="Visual representation of data and information through graphs and charts.",
        prerequisites=["data_analysis"],
        adjacent_skills=["tableau", "power_bi", "pandas"],
        importance_weight=1.0
    ),
    "etl_pipeline": SkillDefinition(
        id="etl_pipeline",
        name="ETL / Data Pipelines",
        category="Analytics & BI",
        aliases=["etl", "elt", "data pipeline", "data pipelines", "airflow", "apache airflow", "dbt"],
        description="Extract, Transform, Load processes for consolidating enterprise data.",
        prerequisites=["sql", "python"],
        adjacent_skills=["data_warehousing", "snowflake", "bigquery"],
        importance_weight=1.1
    ),

    # ------------------ Cloud & Infrastructure ------------------
    "aws": SkillDefinition(
        id="aws",
        name="Amazon Web Services",
        category="Cloud & Infrastructure",
        aliases=["aws", "amazon web services", "amazon web services (aws)", "ec2", "s3", "lambda", "aws cloud"],
        description="Comprehensive cloud computing platform provided by Amazon.",
        prerequisites=["linux"],
        adjacent_skills=["cloud_architecture", "docker", "terraform"],
        importance_weight=1.2
    ),
    "azure": SkillDefinition(
        id="azure",
        name="Microsoft Azure",
        category="Cloud & Infrastructure",
        aliases=["azure", "ms azure", "microsoft azure", "azure cloud"],
        description="Cloud computing service operated by Microsoft for application management.",
        prerequisites=["linux"],
        adjacent_skills=["cloud_architecture", "aws", "docker"],
        importance_weight=1.1
    ),
    "gcp": SkillDefinition(
        id="gcp",
        name="Google Cloud Platform",
        category="Cloud & Infrastructure",
        aliases=["gcp", "google cloud", "google cloud platform", "google cloud platform (gcp)", "bigquery", "gke"],
        description="Suite of cloud computing services running on the same infrastructure Google uses.",
        prerequisites=["linux"],
        adjacent_skills=["cloud_architecture", "kubernetes", "bigquery"],
        importance_weight=1.1
    ),
    "docker": SkillDefinition(
        id="docker",
        name="Docker & Containerization",
        category="Cloud & Infrastructure",
        aliases=["docker", "containers", "containerization", "dockerfile", "docker-compose"],
        description="Platform for developing, shipping, and running applications in lightweight containers.",
        prerequisites=["linux"],
        adjacent_skills=["kubernetes", "devops_cicd", "aws"],
        importance_weight=1.2
    ),
    "kubernetes": SkillDefinition(
        id="kubernetes",
        name="Kubernetes (K8s)",
        category="Cloud & Infrastructure",
        aliases=["kubernetes", "k8s", "k8", "container orchestration", "helm"],
        description="Open-source system for automating deployment, scaling, and management of containerized apps.",
        prerequisites=["docker", "linux"],
        adjacent_skills=["cloud_architecture", "devops_cicd", "aws"],
        importance_weight=1.2
    ),
    "terraform": SkillDefinition(
        id="terraform",
        name="Terraform (IaC)",
        category="Cloud & Infrastructure",
        aliases=["terraform", "iac", "infrastructure as code", "hashicorp terraform"],
        description="Infrastructure as code tool that lets you build, change, and version cloud infrastructure safely.",
        prerequisites=["aws", "linux"],
        adjacent_skills=["cloud_architecture", "devops_cicd"],
        importance_weight=1.1
    ),

    # ------------------ Databases & Storage ------------------
    "postgresql": SkillDefinition(
        id="postgresql",
        name="PostgreSQL",
        category="Databases & Storage",
        aliases=["postgresql", "postgres", "psql"],
        description="Powerful, open-source object-relational database system with strong reliability and SQL compliance.",
        prerequisites=["sql"],
        adjacent_skills=["sql", "database_design", "redis"],
        importance_weight=1.1
    ),
    "mysql": SkillDefinition(
        id="mysql",
        name="MySQL",
        category="Databases & Storage",
        aliases=["mysql", "mariadb"],
        description="Widely deployed open-source relational database management system.",
        prerequisites=["sql"],
        adjacent_skills=["sql", "postgresql"],
        importance_weight=1.0
    ),
    "mongodb": SkillDefinition(
        id="mongodb",
        name="MongoDB",
        category="Databases & Storage",
        aliases=["mongodb", "mongo", "nosql database", "documentdb"],
        description="Leading NoSQL document-oriented database designed for high availability and scalability.",
        prerequisites=[],
        adjacent_skills=["nosql", "node_js", "backend_architecture"],
        importance_weight=1.0
    ),
    "redis": SkillDefinition(
        id="redis",
        name="Redis",
        category="Databases & Storage",
        aliases=["redis", "in-memory cache", "key-value store", "redis cache"],
        description="In-memory data structure store used as a distributed cache, message broker, and database.",
        prerequisites=[],
        adjacent_skills=["postgresql", "system_design", "backend_architecture"],
        importance_weight=1.0
    ),
    "kafka": SkillDefinition(
        id="kafka",
        name="Apache Kafka",
        category="Databases & Storage",
        aliases=["kafka", "apache kafka", "event streaming", "message broker"],
        description="Distributed event store and stream-processing platform for high-throughput pipelines.",
        prerequisites=["java"],
        adjacent_skills=["etl_pipeline", "microservices", "system_design"],
        importance_weight=1.1
    ),

    # ------------------ Web Development ------------------
    "react": SkillDefinition(
        id="react",
        name="React.js",
        category="Web Development",
        aliases=["react", "react.js", "reactjs", "react hooks", "create-react-app"],
        description="Declarative, efficient front-end JavaScript library for building user interfaces.",
        prerequisites=["javascript", "html5", "css3"],
        adjacent_skills=["typescript", "next_js", "tailwind_css", "redux"],
        importance_weight=1.2
    ),
    "next_js": SkillDefinition(
        id="next_js",
        name="Next.js",
        category="Web Development",
        aliases=["next.js", "nextjs", "next js", "react server components"],
        description="Production React framework for server-side rendering, static site generation, and full-stack web apps.",
        prerequisites=["react", "typescript"],
        adjacent_skills=["react", "tailwind_css", "node_js"],
        importance_weight=1.1
    ),
    "node_js": SkillDefinition(
        id="node_js",
        name="Node.js",
        category="Web Development",
        aliases=["node.js", "nodejs", "node", "express", "express.js"],
        description="Cross-platform JavaScript runtime environment for scalable server-side applications.",
        prerequisites=["javascript"],
        adjacent_skills=["typescript", "mongodb", "postgresql", "rest_api"],
        importance_weight=1.1
    ),
    "fastapi": SkillDefinition(
        id="fastapi",
        name="FastAPI",
        category="Web Development",
        aliases=["fastapi", "fast api", "starlette", "pydantic api"],
        description="Modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints.",
        prerequisites=["python"],
        adjacent_skills=["python", "rest_api", "docker", "postgresql"],
        importance_weight=1.1
    ),
    "django": SkillDefinition(
        id="django",
        name="Django",
        category="Web Development",
        aliases=["django", "django rest framework", "drf"],
        description="High-level Python web framework that encourages rapid development and clean design.",
        prerequisites=["python"],
        adjacent_skills=["python", "postgresql", "fastapi"],
        importance_weight=1.0
    ),
    "html5": SkillDefinition(
        id="html5",
        name="HTML5",
        category="Web Development",
        aliases=["html", "html5", "semantic html"],
        description="Standard markup language for documents designed to be displayed in a web browser.",
        prerequisites=[],
        adjacent_skills=["css3", "javascript"],
        importance_weight=0.9
    ),
    "css3": SkillDefinition(
        id="css3",
        name="CSS3 & Responsive Design",
        category="Web Development",
        aliases=["css", "css3", "flexbox", "css grid", "responsive design"],
        description="Style sheet language used for describing the presentation of a document written in HTML.",
        prerequisites=[],
        adjacent_skills=["html5", "tailwind_css"],
        importance_weight=0.9
    ),
    "tailwind_css": SkillDefinition(
        id="tailwind_css",
        name="Tailwind CSS",
        category="Web Development",
        aliases=["tailwind", "tailwindcss", "tailwind css", "utility css"],
        description="Utility-first CSS framework packed with classes that can be composed to build modern designs.",
        prerequisites=["css3"],
        adjacent_skills=["react", "next_js"],
        importance_weight=1.0
    ),
    "rest_api": SkillDefinition(
        id="rest_api",
        name="RESTful APIs",
        category="Web Development",
        aliases=["rest api", "rest", "restful api", "restful apis", "rest apis", "restful web services", "api design"],
        description="Architectural style for designing networked applications using HTTP methods.",
        prerequisites=[],
        adjacent_skills=["fastapi", "node_js", "graphql"],
        importance_weight=1.1
    ),
    "spring_boot": SkillDefinition(
        id="spring_boot",
        name="Spring Boot",
        category="Web Development",
        aliases=["spring boot", "spring framework", "spring", "spring mvc", "java spring"],
        description="Java-based enterprise framework for building microservices and web apps.",
        prerequisites=["java"],
        adjacent_skills=["java", "microservices", "rest_api"],
        importance_weight=1.1
    ),
    "spark": SkillDefinition(
        id="spark",
        name="Apache Spark",
        category="Data Science & AI",
        aliases=["apache spark", "spark", "pyspark", "spark streaming", "spark sql"],
        description="Unified analytics engine for large-scale data processing and distributed computing.",
        prerequisites=["python", "sql"],
        adjacent_skills=["kafka", "python", "data_analysis"],
        importance_weight=1.1
    ),
    "graphql": SkillDefinition(
        id="graphql",
        name="GraphQL",
        category="Web Development",
        aliases=["graphql", "apollo graphql"],
        description="Query language for APIs and runtime for fulfilling those queries with existing data.",
        prerequisites=["rest_api"],
        adjacent_skills=["react", "node_js"],
        importance_weight=1.0
    ),

    # ------------------ DevOps & SRE ------------------
    "git": SkillDefinition(
        id="git",
        name="Git & Version Control",
        category="DevOps & SRE",
        aliases=["git", "github", "gitlab", "version control", "vcs"],
        description="Distributed version control system for tracking changes in source code.",
        prerequisites=[],
        adjacent_skills=["devops_cicd", "linux"],
        importance_weight=1.1
    ),
    "devops_cicd": SkillDefinition(
        id="devops_cicd",
        name="CI/CD Pipelines",
        category="DevOps & SRE",
        aliases=["ci/cd", "continuous integration", "continuous deployment", "github actions", "gitlab ci", "jenkins"],
        description="Practices and tools to automate application build, testing, and deployment cycles.",
        prerequisites=["git", "docker"],
        adjacent_skills=["kubernetes", "docker", "aws"],
        importance_weight=1.1
    ),
    "linux": SkillDefinition(
        id="linux",
        name="Linux System Administration",
        category="DevOps & SRE",
        aliases=["linux", "unix", "ubuntu", "debian", "redhat", "centos", "system administration"],
        description="Open-source Unix-like operating system foundation for server and cloud computing.",
        prerequisites=[],
        adjacent_skills=["bash_shell", "docker", "devops_cicd"],
        importance_weight=1.1
    ),
    "monitoring": SkillDefinition(
        id="monitoring",
        name="Monitoring & Observability",
        category="DevOps & SRE",
        aliases=["monitoring", "observability", "prometheus", "grafana", "datadog", "new relic", "elk stack"],
        description="Practices and tools for tracking system metrics, logging, and health alerts in production.",
        prerequisites=["linux"],
        adjacent_skills=["devops_cicd", "kubernetes"],
        importance_weight=1.0
    ),

    # ------------------ Cybersecurity ------------------
    "network_security": SkillDefinition(
        id="network_security",
        name="Network & Cloud Security",
        category="Cybersecurity",
        aliases=["network security", "firewalls", "vpn", "cybersecurity", "information security", "infosec"],
        description="Practices and technologies designed to protect networks and cloud assets from unauthorized access.",
        prerequisites=["linux"],
        adjacent_skills=["iam_auth", "penetration_testing"],
        importance_weight=1.1
    ),
    "iam_auth": SkillDefinition(
        id="iam_auth",
        name="IAM & Authentication (OAuth/JWT)",
        category="Cybersecurity",
        aliases=["oauth", "jwt", "oauth2", "iam", "identity access management", "saml", "authentication", "authorization"],
        description="Frameworks and protocols for secure user identity verification and access delegation.",
        prerequisites=[],
        adjacent_skills=["rest_api", "network_security"],
        importance_weight=1.0
    ),
    "penetration_testing": SkillDefinition(
        id="penetration_testing",
        name="Penetration Testing & Vulnerability Assessment",
        category="Cybersecurity",
        aliases=["penetration testing", "pen testing", "ethical hacking", "vulnerability assessment", "owasp", "burp suite"],
        description="Authorized simulated cyberattacks against systems to check for exploitable vulnerabilities.",
        prerequisites=["linux", "network_security"],
        adjacent_skills=["network_security"],
        importance_weight=1.1
    ),

    # ------------------ Core Engineering ------------------
    "data_structures_algorithms": SkillDefinition(
        id="data_structures_algorithms",
        name="Data Structures & Algorithms",
        category="Core Engineering",
        aliases=["dsa", "data structures", "algorithms", "problem solving", "algorithmic complexity"],
        description="Fundamental computer science concepts for writing efficient, scalable software.",
        prerequisites=[],
        adjacent_skills=["python", "java", "cpp"],
        importance_weight=1.1
    ),
    "system_design": SkillDefinition(
        id="system_design",
        name="System Design & Architecture",
        category="Core Engineering",
        aliases=["system design", "microservices", "software architecture", "high availability", "scalability"],
        description="Process of defining architecture, modules, interfaces, and data for a system to satisfy requirements.",
        prerequisites=["rest_api", "database_design"],
        adjacent_skills=["cloud_architecture", "microservices", "redis", "kafka"],
        importance_weight=1.2
    ),
}


class SkillTaxonomy:
    """Singleton service to query and normalize skills based on canonical taxonomy."""
    
    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = dict(SKILL_CATALOG)
        self._load_from_json()
        self._alias_map: Dict[str, str] = {}
        self._build_alias_index()

    def _load_from_json(self):
        """Attempts to load and merge canonical skills from skills.json if available."""
        import json
        from pathlib import Path

        candidates = [
            Path(__file__).resolve().parent.parent.parent.parent / "data" / "skills.json",
            Path(__file__).resolve().parent.parent.parent / "data" / "skills.json",
            Path.cwd() / "data" / "skills.json",
        ]
        for p in candidates:
            if p.exists() and p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for item in data:
                        sid = item["id"].strip().lower()
                        self._skills[sid] = SkillDefinition(
                            id=sid,
                            name=item["name"].strip(),
                            category=item["category"].strip(),
                            aliases=item.get("aliases", []),
                            description=item.get("description", ""),
                            prerequisites=item.get("prerequisites", []),
                            adjacent_skills=item.get("adjacent_skills", []),
                            related_skills=item.get("related_skills", item.get("adjacent_skills", [])),
                            importance_weight=float(item.get("importance_weight", 1.0)),
                        )
                    break
                except Exception:
                    pass

    def _build_alias_index(self):
        """Construct normalized alias lookup table."""
        for skill_id, skill in self._skills.items():
            # Add canonical id and canonical name
            self._alias_map[skill_id.lower().strip()] = skill_id
            self._alias_map[skill.name.lower().strip()] = skill_id
            
            # Add all aliases
            for alias in skill.aliases:
                clean_alias = alias.lower().strip()
                if clean_alias:
                    self._alias_map[clean_alias] = skill_id

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self._skills.get(skill_id)

    def get_canonical_id(self, term: str) -> Optional[str]:
        """Look up canonical ID by exact or alias match."""
        if not term:
            return None
        return self._alias_map.get(term.lower().strip())

    def get_all_skills(self) -> List[SkillDefinition]:
        return list(self._skills.values())

    def get_skills_by_category(self, category: str) -> List[SkillDefinition]:
        return [s for s in self._skills.values() if s.category.lower() == category.lower()]

    def get_alias_map(self) -> Dict[str, str]:
        return self._alias_map

    def get_categories(self) -> List[str]:
        return CATEGORIES


# Global instance
taxonomy = SkillTaxonomy()
