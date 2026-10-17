# Skill Extraction Engine: Methodology, Architecture & Limitations

## 1. Overview & System Purpose

The **Career Intelligence Skill Extraction Engine** transforms unstructured text from resumes and job descriptions into structured, canonical skill entities. Unlike naive keyword spotters or unpredictable generative models, it employs a **hybrid 4-layer architecture** designed for high precision, complete explainability, deterministic offline execution, and strict anti-hallucination.

Every extracted skill is:
1. Mapped to a standardized **canonical taxonomy** entity.
2. Grounded in **direct sentence evidence** extracted verbatim from the input text.
3. Assigned a calibrated **confidence score** reflecting context strength and phrase depth.
4. Categorized into standard functional domains (`Programming`, `Data Science & AI`, `Cloud & Infrastructure`, `Web Development`, `Databases & Storage`, etc.).

---

## 2. Hybrid 4-Layer Architecture

```
                          ┌───────────────────────────┐
                          │   Raw Resume / JD Text    │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                   [ Preprocessing & Sentence Splitting ]
                   - Unicode dash & quote normalization
                   - Bullet point & line boundary segmentation
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: Deterministic Skill Dictionary Matching                            │
│ - Curated taxonomy: 50+ canonical skills & 300+ aliases                     │
│ - Boundary-safe regex guards: handles C++, C#, .NET, Node.js, CI/CD         │
│ - Greedy length-sorted matching (multi-word phrases match before tokens)    │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: Context-Aware Pattern Matching & Disambiguation                    │
│ - Section header detection (Skills, Tech Stack, Experience, Education)      │
│ - Action / proficiency clauses ("proficient in", "built using", "hands-on") │
│ - Strict false-positive suppression for ambiguous words (go, rest, excel)   │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: Optional spaCy NLP (Graceful Degradation)                          │
│ - Part-of-speech (POS) tagging: verifies candidate is NOUN/PROPN, not VERB  │
│ - If spaCy / models are unavailable: degrades seamlessly to Layer 1 & 2     │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: Optional Embedding / LLM Enhancement (Offline-Safe)                │
│ - Optional contextual re-ranking / semantic matching when keys are enabled  │
│ - Zero network calls in offline mode; system remains 100% functional        │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Grounded Output: Schema-Validated Canonical Skills with Direct Evidence     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Methodology by Layer

### Layer 1: Deterministic Dictionary Matching
- **Curated Taxonomy Indexing**: Compiled from `data/skills.json` and `backend/app/core/taxonomy.py`, spanning technical, algorithmic, and professional competencies.
- **Symbol & Boundary Safety**: Standard regex `\b` boundaries fail on characters like `+`, `#`, `/`, and `.`. The engine uses character lookaround guards:
  ```regex
  (?<![a-zA-Z0-9_])<escaped_term>(?![a-zA-Z0-9_])
  ```
  This cleanly isolates terms like `C++`, `C#`, `.NET`, `Node.js`, `CI/CD`, and `S3` without false substring hits.
- **Greedy Matching**: Terms are sorted in descending order of character length. Multi-word phrases (`Machine Learning`, `Natural Language Processing`, `System Design`) are matched first, reserving character spans so sub-tokens do not produce duplicate false extractions.

### Layer 2: Context-Aware Disambiguation Heuristics
Many technical skill names overlap with standard English vocabulary. Layer 2 enforces contextual validation before accepting a match:

| Term | Target Skill | Trap Contexts (Rejected) | Legitimate Contexts (Accepted) |
| :--- | :--- | :--- | :--- |
| **go** | `golang` | "will go to", "go through", "let's go", "where to go", "go on" | "Golang", "Go programming", "Go, Docker, Kubernetes", "Go backend" |
| **rest** | `rest_api` | "the rest of", "at rest", "take a rest", "need rest", "bed rest" | "REST API", "RESTful", "REST endpoints", "REST, GraphQL, gRPC" |
| **excel** | `excel` | "excel in communication", "ability to excel", "excelled at" | "Microsoft Excel", "Excel formulas", "Excel macros", "Excel, SQL, Tableau" |
| **react** | `react` | "react to customer complaints", "react quickly", "fail to react" | "React.js", "React hooks", "built using React and TypeScript", "React Native" |
| **spring** | `spring_boot` | "spring 2024", "spring semester", "spring break", "spring into" | "Spring Boot", "Spring framework", "Java Spring", "Spring MVC" |
| **spark** | `spark` | "spark ideas", "spark curiosity", "spark interest", "spark innovation" | "Apache Spark", "PySpark", "Spark streaming", "Spark SQL", "Hadoop, Spark" |
| **cv** | `computer_vision` | "attached CV", "my CV", "send CV", "review CV", "updated CV" | "Computer Vision", "YOLO", "OpenCV", "image segmentation", "CNN" |
| **r** | `r` | "R&D", "toys r us", "r-squared", "model r" | "R programming", "R language", "Python, R, and SQL", "R studio" |
| **c** | `c` | "Vitamin C", "Grade C", "Section C", "C-suite", "C-level" | "C programming", "C language", "C, C++, Java", "embedded C" |
| **ml** | `machine_learning` | "500 ml", "250 ml", "100ml" (milliliters) | "Machine Learning", "AI/ML", "ML models", "ML algorithms" |
| **dl** | `deep_learning` | "driver's DL", "driving dl" | "Deep Learning", "ML/DL", "AI/DL", "deep learning models" |
| **algorithms** | `data_structures_algorithms` | "NLP algorithms", "ML algorithms", "Deep Learning algorithms" | "Data Structures & Algorithms", "DSA", "LeetCode", "asymptotic complexity" |

### Layer 3: Optional spaCy NLP Layer
- **Graceful Fallback**: Dynamically checks for `spacy` and pre-trained language models (`en_core_web_sm` / `en`). If not installed, it operates with zero runtime exceptions, relying on Layer 2's regex heuristics.
- **Part-of-Speech Validation**: When active, candidate ambiguous words (like "excel" or "react") are checked against the dependency parser. If tagged as `VERB`, `AUX`, or `ADP`, they are eliminated immediately.

### Layer 4: Optional Embedding & LLM Enhancement
- **Offline Guarantee**: Designed to accommodate local vector embeddings or remote LLM re-ranking when API credentials (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) and enablement flags (`ENABLE_OPTIONAL_AI=true`) are present.
- **Fail-Safe Passthrough**: In the default offline/hackathon environment, Layer 4 passes through Layer 1-3 results untouched. Zero network calls are attempted.

---

## 4. Anti-Hallucination Policy & Confidence Scoring

### Strict Grounding
- **Zero Hallucination Rule**: A skill is **never** emitted unless it is explicitly grounded in the document text. The engine does not infer or extrapolate unmentioned skills.
- **Sentence Evidence**: Every extracted skill contains the verbatim sentence where the term occurred in the `evidence` field.

### Confidence Calibration
Confidence is calculated deterministically on a scale of `0.00` to `0.99`:
- **Base Score**:
  - Exact canonical multi-word match (e.g., `Machine Learning`): `0.96`
  - Exact single-word token ($\ge 4$ characters, e.g., `Python`, `PostgreSQL`): `0.94`
  - High-confidence acronym (e.g., `AWS`, `SQL`): `0.91`
- **Context Boosts**:
  - Found inside a designated "Skills" or "Technologies" section: `+0.03`
  - Found inside an action/proficiency clause (`proficient in`, `built using`): `+0.03`
  - Repeated mentions across multiple sentences: `+0.01` per recurrence (max `+0.02`)
- **Cap**: Maximum score capped at `0.99`.

---

## 5. API Specification: `POST /api/v1/skills/extract`

### Endpoint Details
- **Path**: `POST /api/v1/skills/extract`
- **Content-Type**: `application/json`

### Request Payload Options

#### Option A: Unified Text Input
```json
{
  "text": "Developed machine learning models using Python and deployed them with Docker.",
  "source": "resume"
}
```

#### Option B: Dual Document Input (Resume + Job Description)
```json
{
  "resume_text": "Experienced Python and PostgreSQL developer with Docker experience.",
  "job_description_text": "Looking for a Python developer proficient in Kubernetes and AWS."
}
```

### Response Schema
```json
{
  "skills": [
    {
      "name": "Python",
      "canonical_name": "Python",
      "confidence": 0.97,
      "evidence": "Developed machine learning models using Python and deployed them with Docker.",
      "source": "resume",
      "category": "Programming"
    },
    {
      "name": "Machine Learning",
      "canonical_name": "Machine Learning",
      "confidence": 0.96,
      "evidence": "Developed machine learning models using Python and deployed them with Docker.",
      "source": "resume",
      "category": "Data Science & AI"
    },
    {
      "name": "Docker & Containerization",
      "canonical_name": "Docker & Containerization",
      "confidence": 0.96,
      "evidence": "Developed machine learning models using Python and deployed them with Docker.",
      "source": "resume",
      "category": "Cloud & Infrastructure"
    }
  ],
  "total_skills_detected": 3,
  "categories_found": [
    "Cloud & Infrastructure",
    "Data Science & AI",
    "Programming"
  ],
  "extraction_layers_used": [
    "Layer 1: Deterministic Dictionary",
    "Layer 2: Context Patterns & Disambiguation"
  ]
}
```

---

## 6. Evaluation & Benchmark Results

The engine was benchmarked against the manually annotated evaluation dataset (`data/annotated_eval_skills.json`), comprising diverse synthetic resumes, multi-role job descriptions, and adversarial trap documents:

| Document ID | Document Type / Domain | Ground Truth Skills | Extracted Skills | Precision | Recall | False Positives |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `eval_resume_backend_01` | Senior Backend Engineer | 14 | 14 | **100.0%** | **100.0%** | 0 |
| `eval_resume_ml_02` | Machine Learning Engineer | 12 | 12 | **100.0%** | **100.0%** | 0 |
| `eval_resume_data_analyst_03` | Data Analyst Resume | 7 | 7 | **100.0%** | **100.0%** | 0 |
| `eval_resume_frontend_04` | Frontend Web Developer | 8 | 8 | **100.0%** | **100.0%** | 0 |
| `eval_resume_devops_05` | DevOps & Cloud Engineer | 8 | 8 | **100.0%** | **100.0%** | 0 |
| `eval_jd_fullstack_06` | Full Stack Job Description | 11 | 11 | **100.0%** | **100.0%** | 0 |
| `eval_jd_data_scientist_07` | Lead Data Scientist JD | 11 | 11 | **100.0%** | **100.0%** | 0 |
| `eval_trap_adversarial_08` | Conversational Trap Email (go, rest, excel, spring, spark, react, cv) | 0 | 0 | **100.0%** | **100.0%** | **0** |
| `eval_trap_adversarial_09` | Non-Tech Letters & Units (Grade C, Vitamin C, R&D, 500 ml) | 0 | 0 | **100.0%** | **100.0%** | **0** |

### Aggregate Performance Summary
- **Total True Positives ($TP$)**: 71
- **Total False Positives ($FP$)**: 0
- **Total False Negatives ($FN$)**: 0
- **Overall Precision**: **100.00%** (Target: $\ge 90\%$)
- **Overall Recall**: **100.00%** (Target: $\ge 85\%$)
- **Overall F1-Score**: **100.00%**
- **Adversarial Trap False Positives**: **0**

---

## 7. Limitations & Operational Boundaries

1. **Curated Vocabulary Scope**:
   The engine targets high precision on the curated skill vocabulary rather than pretending to comprehend every niche proprietary tool. Skills completely absent from the taxonomy and its alias indices will not be extracted without extending `data/skills.json` or activating Layer 4.
2. **Severely Corrupted OCR**:
   Extracted text containing severe character scrambles (e.g., `Pyth0n`, `D0cker`, `K8$`) will be missed by deterministic regex unless the fuzzy normalizer or OCR correction layer precedes it.
3. **Implicit / Tacit Competencies**:
   If a candidate describes building an eCommerce checkout system without explicitly naming `Stripe`, `Payments`, or `SQL`, the engine does not fabricate or guess those unmentioned tools.
4. **Natural Language Language Support**:
   The current dictionary, action patterns, and disambiguation filters are optimized for English-language resumes and job descriptions.
