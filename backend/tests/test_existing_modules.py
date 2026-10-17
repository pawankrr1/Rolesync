"""Regression verification: Ensure existing core logic and utilities remain intact."""

from app.core.taxonomy import taxonomy
from app.core.normalizer import normalizer
from app.core.extractor import extractor
from app.core.role_engine import role_engine
from app.core.matching_engine import matching_engine
from app.core.gap_analyzer import gap_analyzer
from app.core.roadmap_generator import roadmap_generator
from app.utils.text_cleaner import clean_text, extract_sentences


def test_taxonomy_intact():
    skills = taxonomy.get_all_skills()
    assert len(skills) >= 20
    assert taxonomy.get_skill("python") is not None
    assert taxonomy.get_canonical_id("py") == "python"


def test_normalizer_intact():
    norm = normalizer.normalize("Python 3")
    assert norm is not None
    assert norm.canonical_id == "python"


def test_extractor_intact():
    report = extractor.extract_from_text("Software Engineer experienced in Python, Docker, and SQL.")
    extracted_names = [s.canonical_name for s in report.skills]
    assert "Python" in extracted_names
    assert "SQL" in extracted_names
    assert "Docker & Containerization" in extracted_names


def test_matching_and_gaps_intact():
    report = extractor.extract_from_text("Python, SQL, and Docker specialist.")
    role = role_engine.get_role("backend_engineer")
    assert role is not None
    match = matching_engine.calculate_match(report.skills, role)
    assert 0.0 <= match.overall_match_score <= 100.0
    gaps = gap_analyzer.analyze_gaps(report.skills, role, match)
    assert len(gaps.prioritized_gaps) > 0


def test_text_cleaner_intact():
    cleaned = clean_text("  Bullet \u2022 Item 1 \n\n Item 2  ")
    assert "•" in cleaned
    sentences = extract_sentences(cleaned)
    assert len(sentences) >= 1
