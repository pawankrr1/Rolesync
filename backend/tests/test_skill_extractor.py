"""Comprehensive Unit and Integration Tests for Hybrid 4-Layer Skill Extraction Engine.

Covers:
1. Layer 1: Deterministic dictionary matching (canonical names, aliases, symbols like C++, CI/CD, Node.js).
2. Layer 2: Context-aware patterns, action clauses, and strict disambiguation (go, rest, excel, react, spring, spark, cv, r, c).
3. Layer 3: spaCy NLP optional layer and graceful degradation.
4. Layer 4: Optional embedding/LLM layer and deterministic offline fallback.
5. Evidence grounding & zero hallucination verification.
6. Precision, recall, and false positive benchmarks against annotated evaluation dataset.
7. API endpoint POST /api/v1/skills/extract request/response validation.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.extractor import (
    extractor,
    SkillExtractor,
    ExtractedSkill,
    ExtractionReport,
    SpacyNLPLayer,
    OptionalAIEnhancer
)
from app.core.taxonomy import taxonomy

client = TestClient(app)


# ---------------------------------------------------------------------------
# Layer 1: Deterministic Skill Dictionary Matching Tests
# ---------------------------------------------------------------------------

def test_layer1_exact_and_alias_matching():
    """Verify deterministic matching for canonical names and recognized aliases."""
    text = "Proficient in Python, JavaScript, and PostgreSQL database administration."
    report = extractor.extract_from_text(text, source="resume")
    extracted = {s.canonical_id: s for s in report.skills}

    assert "python" in extracted
    assert extracted["python"].canonical_name == "Python"
    assert extracted["python"].category == "Programming"

    assert "javascript" in extracted
    assert extracted["javascript"].canonical_name == "JavaScript"

    assert "postgresql" in extracted
    assert extracted["postgresql"].canonical_name == "PostgreSQL"


def test_layer1_special_characters_and_symbols():
    """Verify terms with special symbols like ++, #, /, . are correctly captured."""
    text = "Experience with C++, C#, .NET Core, Node.js, and CI/CD pipelines."
    report = extractor.extract_from_text(text, source="resume")
    extracted = {s.canonical_id: s for s in report.skills}

    assert "cpp" in extracted
    assert "node_js" in extracted
    assert "devops_cicd" in extracted


def test_layer1_multiword_greedy_phrasing():
    """Verify multi-word phrases match before individual sub-words."""
    text = "Specialized in Machine Learning, Deep Learning, and Natural Language Processing."
    report = extractor.extract_from_text(text, source="resume")
    extracted_names = [s.canonical_name for s in report.skills]

    assert "Machine Learning" in extracted_names
    assert "Deep Learning" in extracted_names
    assert "Natural Language Processing" in extracted_names


# ---------------------------------------------------------------------------
# Layer 2: Context-Aware Disambiguation & False Positive Suppression Tests
# ---------------------------------------------------------------------------

def test_layer2_disambiguate_go_vs_golang():
    """Reject conversational English verb 'go', accept programming language 'Go' / 'Golang'."""
    # Negative: English verb
    neg_text = "I will go to the office tomorrow to see where we can go next."
    neg_report = extractor.extract_from_text(neg_text)
    assert "golang" not in {s.canonical_id for s in neg_report.skills}

    # Positive: Explicit Golang
    pos_text = "Developed concurrent microservices in Golang with Docker and Kubernetes."
    pos_report = extractor.extract_from_text(pos_text)
    assert "golang" in {s.canonical_id for s in pos_report.skills}

    # Positive: Capitalized Go in tech context
    pos_text2 = "Technical Skills:\nLanguages: Python, Go, Java\nDatabases: PostgreSQL"
    pos_report2 = extractor.extract_from_text(pos_text2)
    assert "golang" in {s.canonical_id for s in pos_report2.skills}


def test_layer2_disambiguate_rest_vs_rest_api():
    """Reject conversational 'rest of', accept technical 'REST APIs'."""
    # Negative: English idiom
    neg_text = "The rest of the team will take a rest during the weekend."
    neg_report = extractor.extract_from_text(neg_text)
    assert "rest_api" not in {s.canonical_id for s in neg_report.skills}

    # Positive: Technical REST APIs
    pos_text = "Designed scalable RESTful APIs and integrated GraphQL endpoints."
    pos_report = extractor.extract_from_text(pos_text)
    assert "rest_api" in {s.canonical_id for s in pos_report.skills}


def test_layer2_disambiguate_excel_verb_vs_microsoft_excel():
    """Reject verb 'excel in', accept 'Microsoft Excel' tool."""
    # Negative: English verb
    neg_text = "Demonstrated strong ability to excel in fast-paced corporate communications."
    neg_report = extractor.extract_from_text(neg_text)
    assert "excel" not in {s.canonical_id for s in neg_report.skills}

    # Positive: Data tool
    pos_text = "Built financial forecasting models using advanced Excel formulas, SQL, and Power BI."
    pos_report = extractor.extract_from_text(pos_text)
    assert "excel" in {s.canonical_id for s in pos_report.skills}


def test_layer2_disambiguate_react_verb_vs_reactjs():
    """Reject verb 'react to', accept 'React' / 'React.js' web library."""
    # Negative: English verb
    neg_text = "Customer support representatives must react quickly to incoming complaints."
    neg_report = extractor.extract_from_text(neg_text)
    assert "react" not in {s.canonical_id for s in neg_report.skills}

    # Positive: Frontend library
    pos_text = "Frontend engineer building single page applications using React and TypeScript."
    pos_report = extractor.extract_from_text(pos_text)
    assert "react" in {s.canonical_id for s in pos_report.skills}


def test_layer2_disambiguate_spring_season_vs_spring_boot():
    """Reject calendar 'spring semester', accept 'Spring Boot' framework."""
    # Negative: Calendar / season
    neg_text = "Graduating in the spring semester of 2024 after spring break."
    neg_report = extractor.extract_from_text(neg_text)
    assert "spring_boot" not in {s.canonical_id for s in neg_report.skills}

    # Positive: Java framework
    pos_text = "Architected enterprise backend services using Java and Spring Boot."
    pos_report = extractor.extract_from_text(pos_text)
    assert "spring_boot" in {s.canonical_id for s in pos_report.skills}


def test_layer2_disambiguate_spark_metaphor_vs_apache_spark():
    """Reject metaphor 'spark curiosity', accept 'Apache Spark' data engine."""
    # Negative: Metaphor
    neg_text = "Our keynote speaker aims to spark curiosity and inspire new ideas."
    neg_report = extractor.extract_from_text(neg_text)
    assert "spark" not in {s.canonical_id for s in neg_report.skills}

    # Positive: Big data engine
    pos_text = "Experience with Apache Spark and Hadoop for distributed ETL pipelines."
    pos_report = extractor.extract_from_text(pos_text)
    assert "spark" in {s.canonical_id for s in pos_report.skills}


def test_layer2_disambiguate_cv_resume_vs_computer_vision():
    """Reject 'my CV / attached CV', accept 'Computer Vision' AI discipline."""
    # Negative: Curriculum Vitae
    neg_text = "Please find attached my updated CV for your review."
    neg_report = extractor.extract_from_text(neg_text)
    assert "computer_vision" not in {s.canonical_id for s in neg_report.skills}

    # Positive: Computer Vision
    pos_text = "Machine Learning researcher with focus on computer vision and YOLO object detection."
    pos_report = extractor.extract_from_text(pos_text)
    assert "computer_vision" in {s.canonical_id for s in pos_report.skills}


def test_layer2_disambiguate_single_letters_and_units():
    """Reject single letters in general prose (C, R) and units (ml), accept tech references."""
    # Negative: Grade C, Vitamin C, R&D, 500 ml
    neg_text = "Scored Grade C in class, took Vitamin C, and measured 500 ml in our R&D lab."
    neg_report = extractor.extract_from_text(neg_text)
    extracted_ids = {s.canonical_id for s in neg_report.skills}
    assert "c" not in extracted_ids
    assert "r" not in extracted_ids
    assert "machine_learning" not in extracted_ids

    # Positive: R in data language context
    pos_text = "Experienced in statistical analysis with Python, R, and SQL."
    pos_report = extractor.extract_from_text(pos_text)
    assert "r" in {s.canonical_id for s in pos_report.skills}


# ---------------------------------------------------------------------------
# Layer 3 & 4: Offline Graceful Degradation & Optional Services Tests
# ---------------------------------------------------------------------------

def test_layer3_spacy_graceful_degradation():
    """Verify Layer 3 handles missing spaCy gracefully without raising errors."""
    spacy_layer = SpacyNLPLayer()
    # Regardless of whether spaCy is installed or not, validate_pos_not_verb must return boolean without throwing
    res = spacy_layer.validate_pos_not_verb("I will excel at coding.", "excel")
    assert isinstance(res, bool)


def test_layer4_optional_ai_graceful_degradation():
    """Verify Layer 4 functions deterministically offline without external API keys."""
    ai_enhancer = OptionalAIEnhancer()
    mock_skill = ExtractedSkill(
        name="Python",
        canonical_name="Python",
        confidence=0.97,
        evidence="Coded in Python",
        source="resume",
        category="Programming",
        canonical_id="python"
    )
    enhanced = ai_enhancer.enhance("Sample text", [mock_skill])
    assert len(enhanced) == 1
    assert enhanced[0].canonical_name == "Python"


def test_extractor_offline_guarantee():
    """Verify complete extraction pipeline runs 100% offline."""
    custom_extractor = SkillExtractor()
    report = custom_extractor.extract_from_text("Senior Docker and Kubernetes Administrator with Terraform experience.")
    extracted = {s.canonical_id for s in report.skills}
    assert "docker" in extracted
    assert "kubernetes" in extracted
    assert "terraform" in extracted
    assert len(report.extraction_layers_used) >= 2


# ---------------------------------------------------------------------------
# Evidence Grounding & Zero Hallucination Tests
# ---------------------------------------------------------------------------

def test_evidence_grounding_and_no_hallucination():
    """Every extracted skill MUST be backed by non-empty evidence directly present in the text."""
    sample_text = (
        "Built automated deployment pipelines using Docker containers.\n"
        "Configured AWS S3 and EC2 instances for cloud storage and compute.\n"
        "Implemented PostgreSQL relational databases with indexing."
    )
    report = extractor.extract_from_text(sample_text, source="resume")
    assert len(report.skills) > 0

    for skill in report.skills:
        # 1. Non-empty string evidence
        assert isinstance(skill.evidence, str)
        assert len(skill.evidence.strip()) > 0
        # 2. Evidence snippet must literally exist in the input document
        assert skill.evidence in sample_text or skill.evidence.strip() in sample_text
        # 3. Confidence must be calibrated between 0.0 and 1.0
        assert 0.0 <= skill.confidence <= 1.0
        # 4. Canonical fields present
        assert skill.canonical_name
        assert skill.category
        assert skill.source == "resume"


def test_empty_and_whitespace_input_returns_no_skills():
    """Empty or whitespace text must return 0 skills with no hallucinations."""
    report = extractor.extract_from_text("   \n\n\t  ")
    assert report.total_skills_detected == 0
    assert len(report.skills) == 0


# ---------------------------------------------------------------------------
# Precision, Recall & False Positive Benchmark Evaluation
# ---------------------------------------------------------------------------

def test_evaluation_benchmark_against_annotated_dataset():
    """Measure precision, recall, and false positives against data/annotated_eval_skills.json."""
    dataset_path = Path(__file__).resolve().parent.parent.parent / "data" / "annotated_eval_skills.json"
    assert dataset_path.exists(), f"Evaluation dataset not found at {dataset_path}"

    with open(dataset_path, "r", encoding="utf-8") as f:
        eval_docs = json.load(f)

    assert len(eval_docs) >= 5, "Evaluation dataset must contain at least 5 annotated documents"

    total_tp = 0
    total_fp = 0
    total_fn = 0
    trap_fp = 0

    for doc in eval_docs:
        text = doc["text"]
        doc_type = doc.get("doc_type", "resume")
        ground_truth = set(doc["annotated_ground_truth_skills"])

        report = extractor.extract_from_text(text, source=doc_type)
        extracted_ids = {s.canonical_id for s in report.skills}

        tp = len(extracted_ids & ground_truth)
        fp = len(extracted_ids - ground_truth)
        fn = len(ground_truth - extracted_ids)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        if len(ground_truth) == 0:
            trap_fp += fp

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0

    print(f"\nEvaluation Benchmark Results:")
    print(f"Total True Positives:  {total_tp}")
    print(f"Total False Positives: {total_fp}")
    print(f"Total False Negatives: {total_fn}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall:    {recall:.2%}")
    print(f"Trap False Positives:  {trap_fp}")

    # Acceptance Criteria
    assert precision >= 0.90, f"Precision {precision:.2%} is below required 90%"
    assert recall >= 0.85, f"Recall {recall:.2%} is below required 85%"
    assert trap_fp == 0, f"Adversarial trap documents produced {trap_fp} false positives"


# ---------------------------------------------------------------------------
# API Endpoint Tests: POST /api/v1/skills/extract
# ---------------------------------------------------------------------------

def test_api_extract_with_resume_text():
    """POST /api/v1/skills/extract with resume_text."""
    payload = {
        "resume_text": "Developed machine learning models using Python and deployed them with Docker."
    }
    response = client.post("/api/v1/skills/extract", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "skills" in data
    skills = data["skills"]
    assert len(skills) > 0

    python_skill = next((s for s in skills if s["canonical_name"] == "Python"), None)
    assert python_skill is not None
    assert python_skill["name"] == "Python"
    assert python_skill["canonical_name"] == "Python"
    assert python_skill["source"] == "resume"
    assert python_skill["category"] == "Programming"
    assert "evidence" in python_skill
    assert "Python" in python_skill["evidence"]
    assert 0.0 <= python_skill["confidence"] <= 1.0


def test_api_extract_with_job_description_text():
    """POST /api/v1/skills/extract with job_description_text."""
    payload = {
        "job_description_text": "Requirements: Must have 3+ years experience with PostgreSQL, FastAPI, and Docker."
    }
    response = client.post("/api/v1/skills/extract", json=payload)
    assert response.status_code == 200

    data = response.json()
    skills = data["skills"]
    assert len(skills) >= 3

    sources = {s["source"] for s in skills}
    assert sources == {"job_description"}

    canonical_names = {s["canonical_name"] for s in skills}
    assert "PostgreSQL" in canonical_names
    assert "FastAPI" in canonical_names
    assert "Docker & Containerization" in canonical_names


def test_api_extract_with_both_resume_and_jd():
    """POST /api/v1/skills/extract with both resume_text and job_description_text."""
    payload = {
        "resume_text": "Experienced Python and Git developer.",
        "job_description_text": "Looking for a Python developer proficient in Kubernetes."
    }
    response = client.post("/api/v1/skills/extract", json=payload)
    assert response.status_code == 200

    data = response.json()
    skills = data["skills"]

    resume_skills = [s for s in skills if s["source"] == "resume"]
    jd_skills = [s for s in skills if s["source"] == "job_description"]

    assert any("Git" in s["canonical_name"] or s["canonical_id"] == "git" for s in resume_skills)
    assert any("Kubernetes" in s["canonical_name"] or s["canonical_id"] == "kubernetes" for s in jd_skills)


def test_api_extract_schema_compatibility():
    """Verify exact JSON output schema matches user specification."""
    payload = {
        "text": "Developed machine learning models using Python"
    }
    response = client.post("/api/v1/skills/extract", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "skills" in data
    assert isinstance(data["skills"], list)

    for skill in data["skills"]:
        assert "name" in skill
        assert "canonical_name" in skill
        assert "confidence" in skill
        assert "evidence" in skill
        assert "source" in skill
        assert "category" in skill
        assert isinstance(skill["confidence"], (int, float))
        assert isinstance(skill["evidence"], str)
