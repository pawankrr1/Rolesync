"""
Unit and Integration Tests for Career Intelligence Explainability Audit.

Ensures that every match score, missing skill, and recommendation provides
grounded explainability answering:
1. WHY? (e.g. "Your score is 78% because 7 of 9 high-priority skills were matched or partially matched.")
2. WHY IS THIS MISSING?
3. WHY WAS THIS RECOMMENDED?
4. Confidence indicators and low-confidence disclaimer:
   "Possible skill detected — review recommended."
5. Mandated system disclaimer:
   "Career Intelligence provides decision support based on the available profile and dataset. It does not guarantee employment, hiring outcomes or career success."
"""

import re
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.matching_engine import matching_engine, SYSTEM_DISCLAIMER
from app.core.role_engine import role_engine
from app.core.gap_analyzer import SkillGapAnalyzer
from app.core.recommendation_engine import CareerRecommendationEngine
from app.core.roadmap_generator import RoadmapGenerator
from app.core.extractor import SkillExtractor, ExtractedSkill


MANDATED_SYSTEM_DISCLAIMER = (
    "Career Intelligence provides decision support based on the available profile and dataset. "
    "It does not guarantee employment, hiring outcomes or career success."
)

LOW_CONFIDENCE_NOTE = "Possible skill detected — review recommended."


@pytest.fixture
def client():
    return TestClient(app)


class TestMatchScoreExplainability:
    """Tests ensuring every match score explains WHY."""

    def test_why_score_format(self):
        target_role = role_engine.get_role("data_scientist")
        result = matching_engine.calculate_match(
            candidate_skills=["Python", "SQL", "Machine Learning"],
            target_role=target_role,
            candidate_experience_years=3.0,
        )

        assert result.why_score is not None
        assert isinstance(result.why_score, str)
        assert len(result.why_score) > 0

        # Must follow the required pattern:
        # "Your score is X% because Y of Z high-priority skills were matched or partially matched."
        pattern = r"^Your score is \d+% because \d+ of \d+ high-priority skills were matched or partially matched\."
        assert re.match(pattern, result.why_score), (
            f"why_score does not match expected format: {result.why_score}"
        )

    def test_why_score_zero_match(self):
        target_role = role_engine.get_role("data_scientist")
        result = matching_engine.calculate_match(
            candidate_skills=["Baking", "Cooking"],
            target_role=target_role,
        )

        assert result.why_score is not None
        assert "0 of" in result.why_score
        assert "high-priority skills were matched or partially matched." in result.why_score

    def test_system_disclaimer_present_in_match_result(self):
        target_role = role_engine.get_role("data_scientist")
        result = matching_engine.calculate_match(
            candidate_skills=["Python", "SQL"],
            target_role=target_role,
        )

        assert result.system_disclaimer == MANDATED_SYSTEM_DISCLAIMER


class TestMissingSkillsExplainability:
    """Tests ensuring every missing skill explains WHY IS THIS MISSING."""

    def test_matching_engine_missing_skills_have_why_missing(self):
        target_role = role_engine.get_role("data_scientist")
        result = matching_engine.calculate_match(
            candidate_skills=["Python"],
            target_role=target_role,
        )

        assert len(result.missing_skills) > 0
        for item in result.missing_skills:
            assert hasattr(item, "why_missing")
            assert item.why_missing is not None
            assert len(item.why_missing.strip()) > 0
            assert "benchmark" in item.why_missing.lower() or "detected" in item.why_missing.lower()

    def test_gap_analyzer_missing_skills_have_why_missing(self):
        analyzer = SkillGapAnalyzer()
        report = analyzer.analyze_gaps(
            candidate_skills=["Python", "FastAPI"],
            target_role="data_scientist",
        )

        assert len(report.missing_skills) > 0
        for gap in report.missing_skills:
            assert gap.why_missing is not None
            assert len(gap.why_missing.strip()) > 0
            assert "benchmark" in gap.why_missing.lower() or "not detected" in gap.why_missing.lower()

        # Also verify priority_order items
        for gap in report.priority_order:
            if gap.classification == "MISSING":
                assert gap.why_missing is not None
                assert len(gap.why_missing.strip()) > 0

    def test_gap_analyzer_system_disclaimer(self):
        analyzer = SkillGapAnalyzer()
        report = analyzer.analyze_gaps(
            candidate_skills=["Python"],
            target_role="data_scientist",
        )
        assert report.system_disclaimer == MANDATED_SYSTEM_DISCLAIMER


class TestRecommendationExplainability:
    """Tests ensuring every recommendation explains WHY WAS THIS RECOMMENDED."""

    def test_role_recommendation_why_recommended(self):
        engine = CareerRecommendationEngine()
        result = engine.recommend_roles(
            candidate_skills=["Python", "SQL", "Machine Learning"],
            candidate_experience_years=2.0,
        )

        assert len(result.recommended_roles) > 0
        for role in result.recommended_roles:
            assert role.why_recommended is not None
            assert len(role.why_recommended.strip()) > 0
            assert "recommended" in role.why_recommended.lower()

        for adj in result.adjacent_transitions:
            assert len(adj.supporting_evidence.strip()) > 0

        assert result.system_disclaimer == MANDATED_SYSTEM_DISCLAIMER

    def test_roadmap_milestones_why_recommended(self):
        generator = RoadmapGenerator()
        result = generator.generate_roadmap(
            candidate_skills=["Python"],
            target_role="data_scientist",
        )

        assert len(result.roadmap) > 0
        for milestone in result.roadmap:
            assert milestone.why_recommended is not None
            assert len(milestone.why_recommended.strip()) > 0
            assert "recommended" in milestone.why_recommended.lower()

        assert result.system_disclaimer == MANDATED_SYSTEM_DISCLAIMER


class TestSkillExtractionConfidenceAndGuardrails:
    """Tests confidence indicators and low-confidence warnings."""

    def test_high_confidence_skill_extraction(self):
        extractor = SkillExtractor()
        text = "Expert software engineer with 5 years experience in Python and PostgreSQL."
        report = extractor.extract_from_text(text, source="resume")

        skills = {s.canonical_name: s for s in report.skills}
        assert "Python" in skills
        assert skills["Python"].confidence_level in ["High", "Medium"]
        assert skills["Python"].confidence_note is None

    def test_low_confidence_skill_note(self):
        # Create an ExtractedSkill with confidence below 0.60
        skill = ExtractedSkill(
            name="Rust",
            canonical_name="Rust",
            canonical_id="rust",
            category="Programming",
            confidence=0.45,
            evidence="Candidate briefly mentioned Rust.",
            source="resume",
        )
        assert skill.confidence_level == "Low"
        assert skill.confidence_note == LOW_CONFIDENCE_NOTE

    def test_extraction_report_system_disclaimer(self):
        extractor = SkillExtractor()
        report = extractor.extract_from_text("Experienced in Docker and Kubernetes.", source="resume")
        assert report.system_disclaimer == MANDATED_SYSTEM_DISCLAIMER


class TestApiExplainabilityAudit:
    """Audits all FastAPI responses to ensure explainability fields are present."""

    def test_api_matching_explainability(self, client):
        response = client.post(
            "/api/v1/matching/analyze",
            json={
                "candidate_skills": ["Python", "SQL"],
                "target_role": "data_scientist",
                "candidate_experience_years": 2.0,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # 1. Matches WHY score
        assert "why_score" in data
        assert "Your score is" in data["why_score"]
        assert "high-priority skills were matched or partially matched." in data["why_score"]

        # 2. System Disclaimer
        assert data.get("system_disclaimer") == MANDATED_SYSTEM_DISCLAIMER

        # 3. Missing skills answer WHY IS THIS MISSING
        assert "missing_skills" in data
        for missing in data["missing_skills"]:
            assert "why_missing" in missing
            assert len(missing["why_missing"]) > 0

    def test_api_gap_explainability(self, client):
        response = client.post(
            "/api/v1/gap/analyze",
            json={
                "candidate_skills": ["Python"],
                "target_role": "data_scientist",
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data.get("system_disclaimer") == MANDATED_SYSTEM_DISCLAIMER
        assert "missing_skills" in data
        for missing in data["missing_skills"]:
            assert "why_missing" in missing
            assert len(missing["why_missing"]) > 0

    def test_api_recommendations_roles_explainability(self, client):
        response = client.post(
            "/api/v1/recommendations/roles",
            json={
                "candidate_skills": ["Python", "Machine Learning"],
                "top_n": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data.get("system_disclaimer") == MANDATED_SYSTEM_DISCLAIMER
        assert "recommended_roles" in data
        for role in data["recommended_roles"]:
            assert "why_recommended" in role
            assert len(role["why_recommended"]) > 0

    def test_api_recommendations_roadmap_explainability(self, client):
        response = client.post(
            "/api/v1/recommendations/roadmap",
            json={
                "candidate_skills": ["Python"],
                "target_role": "data_scientist",
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data.get("system_disclaimer") == MANDATED_SYSTEM_DISCLAIMER
        assert "roadmap" in data
        for milestone in data["roadmap"]:
            assert "why_recommended" in milestone
            assert len(milestone["why_recommended"]) > 0
