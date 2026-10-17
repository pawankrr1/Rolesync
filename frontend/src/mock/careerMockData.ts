/**
 * ==============================================================================
 * VISUAL DEVELOPMENT MOCK DATA - ISOLATED FROM PRODUCTION API SERVICES
 * Used exclusively for rendering shells, testing layouts, and UI development.
 * ==============================================================================
 */

import {
  CandidateAnalysisSummary,
  RecruiterApplicantItem,
  MarketInsightMetric,
  SkillItem,
} from "../lib/types";

export const mockWorkflowSteps = [
  {
    step: 1,
    title: "Ingest",
    subtitle: "Raw Text & Stream Parsing",
    desc: "Accepts PDFs, DOCX, and text formats with in-memory stream decoding.",
  },
  {
    step: 2,
    title: "Extract",
    subtitle: "Contextual Evidence Capture",
    desc: "Extracts canonical technical skills with sentence-level citation snippets.",
  },
  {
    step: 3,
    title: "Normalize",
    subtitle: "Canonical Ontology & Aliases",
    desc: "Maps abbreviations and variations to a single canonical taxonomy.",
  },
  {
    step: 4,
    title: "Match",
    subtitle: "Weighted Mathematical Scoring",
    desc: "Evaluates required, preferred, semantic overlap, and depth signals.",
  },
  {
    step: 5,
    title: "Gap",
    subtitle: "Prerequisite DAG Prioritization",
    desc: "Ranks missing skills by unblocking power, foundations, and urgency.",
  },
  {
    step: 6,
    title: "Recommend",
    subtitle: "Roadmaps & Career Bridges",
    desc: "Provides curated learning resources, project challenges, and lateral pivots.",
  },
];

export const mockCandidateProfile: {
  name: string;
  title: string;
  email: string;
  experienceYears: number;
  extractedSkills: SkillItem[];
} = {
  name: "Pawan Kumar",
  title: "Fullstack / AI Developer",
  email: "pawan.kumar@moveoncoders.dev",
  experienceYears: 3,
  extractedSkills: [
    {
      id: "python",
      name: "Python",
      category: "Programming",
      confidence: 0.99,
      frequency: 5,
      status: "strong_match",
      evidence: [
        "Architected scalable backend microservices using Python and FastAPI.",
        "Built predictive machine learning models in Python for dataset evaluation.",
      ],
    },
    {
      id: "sql",
      name: "SQL",
      category: "Programming",
      confidence: 0.96,
      frequency: 3,
      status: "strong_match",
      evidence: ["Designed complex analytical SQL queries and database schemas."],
    },
    {
      id: "fastapi",
      name: "FastAPI",
      category: "Web Development",
      confidence: 0.98,
      frequency: 4,
      status: "strong_match",
      evidence: ["Implemented RESTful APIs and asynchronous endpoints with FastAPI."],
    },
    {
      id: "docker",
      name: "Docker & Containerization",
      category: "Cloud & Infrastructure",
      confidence: 0.94,
      frequency: 2,
      status: "strong_match",
      evidence: ["Containerized distributed applications using multi-stage Dockerfiles."],
    },
    {
      id: "machine_learning",
      name: "Machine Learning",
      category: "Data Science & AI",
      confidence: 0.92,
      frequency: 3,
      status: "strong_match",
      evidence: ["Trained supervised classifiers and evaluated F1 performance."],
    },
    {
      id: "react",
      name: "React.js",
      category: "Web Development",
      confidence: 0.95,
      frequency: 4,
      status: "strong_match",
      evidence: ["Built interactive web dashboards and reactive state workflows with React."],
    },
    {
      id: "git",
      name: "Git & Version Control",
      category: "DevOps & SRE",
      confidence: 0.95,
      frequency: 2,
      status: "strong_match",
      evidence: ["Managed team version control, PR branching, and automated CI."],
    },
    {
      id: "deep_learning",
      name: "Deep Learning",
      category: "Data Science & AI",
      confidence: 0.70,
      frequency: 1,
      status: "partial_match",
      evidence: ["Explored preliminary neural network architectures and PyTorch blitz."],
      notes: "Adjacent foundational exposure detected.",
    },
  ],
};

export const mockAnalysisResult: CandidateAnalysisSummary = {
  candidateName: "Pawan Kumar",
  targetRole: "Data Scientist",
  overallScore: 78.5,
  scoreGrade: "High Alignment",
  totalSkillsDetected: 14,
  requiredCoveragePct: 83.3,
  narrative:
    "Overall match score of 78.5% for Data Scientist is derived from transparent, measurable signals rather than arbitrary keyword filtering. Primary required competencies are well-covered (Python, SQL, Machine Learning), while foundational gaps in Statistics & Probability and Pandas represent the immediate priority to reach >90% readiness.",
  factors: [
    {
      name: "Required Skill Coverage",
      rawScore: 83.3,
      weight: 0.6,
      weightedScore: 50.0,
      maxPoints: 60.0,
      explanation:
        "Directly satisfies 5 of 6 required core requirements (Python, SQL, Machine Learning) with 1 partial adjacency.",
    },
    {
      name: "Preferred Skill Coverage",
      rawScore: 75.0,
      weight: 0.1,
      weightedScore: 7.5,
      maxPoints: 10.0,
      explanation:
        "Matched bonus preferred skillsets in Docker and cloud architecture.",
    },
    {
      name: "Semantic Domain Overlap",
      rawScore: 85.0,
      weight: 0.2,
      weightedScore: 17.0,
      maxPoints: 20.0,
      explanation:
        "High taxonomy category overlap spanning AI, Backend, and Database engineering domains.",
    },
    {
      name: "Experience & Evidence Depth",
      rawScore: 80.0,
      weight: 0.1,
      weightedScore: 8.0,
      maxPoints: 10.0,
      explanation:
        "Verified high contextual density with 18 distinct sentence citations across verified projects.",
    },
  ],
  matchedSkills: [
    {
      id: "python",
      name: "Python",
      category: "Programming",
      status: "strong_match",
      evidence: ["Engineered scalable backend microservices using Python."],
    },
    {
      id: "sql",
      name: "SQL",
      category: "Programming",
      status: "strong_match",
      evidence: ["Designed complex analytical SQL queries."],
    },
    {
      id: "machine_learning",
      name: "Machine Learning",
      category: "Data Science & AI",
      status: "strong_match",
      evidence: ["Built predictive models using scikit-learn."],
    },
    {
      id: "docker",
      name: "Docker & Containerization",
      category: "Cloud & Infrastructure",
      status: "strong_match",
      evidence: ["Containerized apps with multi-stage Docker builds."],
    },
  ],
  partialSkills: [
    {
      id: "deep_learning",
      name: "Deep Learning",
      category: "Data Science & AI",
      status: "partial_match",
      notes: "Has machine learning and Python background; lacks production PyTorch/TensorFlow models.",
    },
  ],
  missingSkills: [
    {
      id: "statistics_probability",
      name: "Statistics & Probability",
      category: "Data Science & AI",
      status: "missing",
      notes: "Required for hypothesis testing and A/B experimental design.",
    },
    {
      id: "pandas",
      name: "Pandas",
      category: "Data Science & AI",
      status: "missing",
      notes: "Core data manipulation and transformation library.",
    },
    {
      id: "aws",
      name: "Amazon Web Services (AWS)",
      category: "Cloud & Infrastructure",
      status: "missing",
      notes: "Preferred cloud hosting and model deployment infrastructure.",
    },
  ],
  prioritizedGaps: [
    {
      id: "statistics_probability",
      name: "Statistics & Probability",
      category: "Data Science & AI",
      status: "missing",
      priorityRank: 1,
      priorityTier: "P1 - Foundational (Learn First)",
      priorityScore: 12.5,
      prerequisitesMet: true,
      unmetPrerequisites: [],
      unblocksSkills: ["Machine Learning", "A/B Testing"],
      learningEffortWeeks: "2-3 weeks",
      reasoning:
        "Crucial foundation for hypothesis testing and regression analysis. Unblocks higher-tier modeling tasks.",
    },
    {
      id: "pandas",
      name: "Pandas",
      category: "Data Science & AI",
      status: "missing",
      priorityRank: 2,
      priorityTier: "P1 - Foundational (Learn First)",
      priorityScore: 10.8,
      prerequisitesMet: true,
      unmetPrerequisites: [],
      unblocksSkills: ["Data Analysis", "Feature Engineering"],
      learningEffortWeeks: "1-2 weeks",
      reasoning:
        "Essential dataframe toolkit. You already know Python—fast win to bridge in under 10 days.",
    },
    {
      id: "deep_learning",
      name: "Deep Learning",
      category: "Data Science & AI",
      status: "partial_match",
      priorityRank: 3,
      priorityTier: "P2 - Core Competency",
      priorityScore: 8.4,
      prerequisitesMet: true,
      unmetPrerequisites: [],
      unblocksSkills: ["NLP", "Computer Vision"],
      learningEffortWeeks: "3-4 weeks",
      reasoning:
        "Advanced requirement for complex neural architectures and transformer deployments.",
    },
  ],
  milestones: [
    {
      stepNumber: 1,
      phaseTitle: "Phase 1: Foundational Statistics & Probability",
      skillName: "Statistics & Probability",
      category: "Data Science & AI",
      duration: "2-3 weeks",
      prerequisiteContext: "Unblocks statistical modeling and predictive confidence metrics.",
      resources: [
        {
          title: "Introduction to Probability and Statistics",
          provider: "MIT OpenCourseWare",
          type: "Video Course",
          estimatedHours: 25,
          url: "https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2014/",
          isFree: true,
          rating: 4.9,
        },
        {
          title: "Statistics with Python Specialization",
          provider: "Coursera / Univ. of Michigan",
          type: "Interactive Lab",
          estimatedHours: 20,
          url: "https://www.coursera.org/specializations/statistics-with-python",
          isFree: true,
          rating: 4.8,
        },
      ],
      projectChallenge:
        "Statistical EDA Notebook: Implement hypothesis testing, p-value verification, and bootstrap sampling on real Indian census data.",
      outcomes: [
        "Master distributions, Bayes theorem, and hypothesis validation",
        "Publish verifiable analytical Jupyter Notebook on GitHub",
      ],
    },
    {
      stepNumber: 2,
      phaseTitle: "Phase 2: Data Wrangling with Pandas",
      skillName: "Pandas",
      category: "Data Science & AI",
      duration: "1-2 weeks",
      prerequisiteContext: "Enables robust data cleaning and ETL pipeline development.",
      resources: [
        {
          title: "Data Analysis with Python Certification",
          provider: "freeCodeCamp",
          type: "Interactive Course",
          estimatedHours: 15,
          url: "https://www.freecodecamp.org/learn/data-analysis-with-python/",
          isFree: true,
          rating: 4.8,
        },
      ],
      projectChallenge:
        "Automated Ingestion Pipeline: Ingest messy multi-table CSV datasets, handle missing values, and produce cleaned analytical parquet files.",
      outcomes: [
        "Fluent with groupby, vectorization, and multi-indexing",
        "Satisfy standard data cleaning interview benchmark",
      ],
    },
    {
      stepNumber: 3,
      phaseTitle: "Phase 3: Production Deep Learning",
      skillName: "Deep Learning (PyTorch)",
      category: "Data Science & AI",
      duration: "3-4 weeks",
      prerequisiteContext: "Capstone tier for production neural systems.",
      resources: [
        {
          title: "Deep Learning with PyTorch: 60 Minute Blitz",
          provider: "PyTorch Official Documentation",
          type: "Documentation & Lab",
          estimatedHours: 10,
          url: "https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html",
          isFree: true,
          rating: 4.9,
        },
      ],
      projectChallenge:
        "Neural Classifier Service: Train a PyTorch classification network, package weights, and serve inference through FastAPI with Docker.",
      outcomes: [
        "Implement custom datasets, dataloaders, and validation loops",
        "Deploy containerized inference container with latency logging",
      ],
    },
  ],
  adjacentRoles: [
    {
      id: "backend_engineer",
      title: "Backend Software Engineer",
      category: "Web Development",
      alignmentScore: 84.5,
      scoreGrade: "Exceptional Match",
      overlappingSkills: ["Python", "FastAPI", "SQL", "Docker", "Git"],
      missingBridgeSkills: ["Redis", "System Design"],
      feasibility: "Immediate / High Feasibility",
      rationale:
        "Your verified Python, FastAPI, and Docker evidence gives you an immediate 84.5% qualification. Minimal bridge effort needed.",
    },
    {
      id: "ml_engineer",
      title: "Machine Learning Engineer",
      category: "Data Science & AI",
      alignmentScore: 76.0,
      scoreGrade: "High Alignment",
      overlappingSkills: ["Python", "Machine Learning", "Docker", "FastAPI"],
      missingBridgeSkills: ["PyTorch", "Kubernetes (K8s)"],
      feasibility: "Moderate Bridge Required",
      rationale:
        "Strong intersection between API engineering and ML models. Adding PyTorch will unlock this high-demand role.",
    },
    {
      id: "data_analyst",
      title: "Data Analyst",
      category: "Analytics & BI",
      alignmentScore: 68.0,
      scoreGrade: "Moderate Potential",
      overlappingSkills: ["SQL", "Python", "Data Analysis"],
      missingBridgeSkills: ["Power BI", "Advanced Excel"],
      feasibility: "Moderate Bridge Required",
      rationale:
        "Strong foundation in data queries. Adding BI visualization tools creates an alternate career track.",
    },
  ],
};

export const mockRecruiterApplicants: RecruiterApplicantItem[] = [
  {
    id: "app-1",
    name: "Pawan Kumar",
    filename: "pawan_kumar_resume.pdf",
    score: 88.5,
    grade: "Exceptional Match",
    requiredCoverage: 92,
    matchedCount: 8,
    missingKeySkills: ["Kubernetes"],
    topSkills: ["Python", "FastAPI", "PostgreSQL", "Docker", "Machine Learning"],
    experienceYears: 3,
    status: "Shortlisted",
  },
  {
    id: "app-2",
    name: "Aarav Sharma",
    filename: "aarav_backend_cv.docx",
    score: 81.0,
    grade: "High Alignment",
    requiredCoverage: 83,
    matchedCount: 6,
    missingKeySkills: ["FastAPI", "Redis"],
    topSkills: ["Python", "Django", "SQL", "Docker", "Git"],
    experienceYears: 4,
    status: "Reviewed",
  },
  {
    id: "app-3",
    name: "Sneha Patel",
    filename: "sneha_data_cv.pdf",
    score: 65.5,
    grade: "Moderate Potential",
    requiredCoverage: 60,
    matchedCount: 4,
    missingKeySkills: ["FastAPI", "Docker", "System Design"],
    topSkills: ["Python", "Pandas", "SQL", "Data Analysis"],
    experienceYears: 2,
    status: "Under Review",
  },
  {
    id: "app-4",
    name: "Rohan Verma",
    filename: "rohan_junior_dev.pdf",
    score: 48.0,
    grade: "Needs Upskilling",
    requiredCoverage: 42,
    matchedCount: 3,
    missingKeySkills: ["FastAPI", "PostgreSQL", "Docker", "Linux"],
    topSkills: ["Python", "HTML5", "CSS3"],
    experienceYears: 1,
    status: "Reviewed",
  },
];

export const mockMarketInsights: MarketInsightMetric[] = [
  {
    title: "National Talent-Job Disconnect",
    value: "340 : 1",
    trend: "+14% YoY",
    isPositive: false,
    description: "Applicant-to-vacancy ratio reported by NITI Aayog across public & entry-level roles.",
  },
  {
    title: "Highest In-Demand Tech Skill",
    value: "Python & Cloud",
    trend: "87% Role Demand",
    isPositive: true,
    description: "Appears across 87% of all active tech and AI job requisitions in India.",
  },
  {
    title: "Common Curriculum Gap",
    value: "Docker & CI/CD",
    trend: "72% Missing Signal",
    isPositive: false,
    description: "72% of college graduates lack containerization exposure required on Day 1.",
  },
  {
    title: "Fastest Transition Path",
    value: "Backend → ML Eng",
    trend: "3-4 Weeks Avg Bridge",
    isPositive: true,
    description: "Developers with API and Python experience transition with lowest skill distance.",
  },
];
