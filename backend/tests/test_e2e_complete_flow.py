"""Complete End-to-End Test Suite for Career Intelligence.

Verifies:
1. Candidate Scenario:
   - Profile: B.Tech Computer Science student
   - Skills: Python, SQL, Pandas, Machine Learning, Power BI
   - Target Role: Data Scientist
   - Step 1: Resume uploads
   - Step 2: Text extracted
   - Step 3: Skills detected
   - Step 4: Skills normalized
   - Step 5: Data Scientist role loads
   - Step 6: Match score generated
   - Step 7: Matched skills appear
   - Step 8: Missing skills appear
   - Step 9: Explanation appears
   - Step 10: Skill gaps prioritized
   - Step 11: Learning roadmap generated
   - Step 12: Adjacent roles shown

2. Recruiter Scenario:
   - Step 1: Paste Data Scientist JD
   - Step 2: Ingest 3 demo resumes
   - Step 3: Extract skills
   - Step 4: Calculate scores
   - Step 5: Rank candidates
   - Step 6: Show explanations

3. Failure Scenarios:
   - Invalid PDF
   - Empty resume
   - Unsupported file
   - Missing role
   - Empty skill set
   - Backend error handling & resilience
"""

import io
import pytest
import fitz  # PyMuPDF
from fastapi.testclient import TestClient

from app.main import app
from app.core.role_engine import role_engine

client = TestClient(app)

# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def create_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    data = doc.write()
    doc.close()
    return data


CANDIDATE_RESUME_TEXT = """
Aditya Verma
B.Tech Computer Science and Engineering Student
Email: aditya.cs@example.edu | Bengaluru, India

EDUCATION
Bachelor of Technology (B.Tech) in Computer Science & Engineering
Expected Graduation: 2025 | GPA: 8.8/10

TECHNICAL SKILLS
- Programming & Databases: Python, SQL
- Data Science & Machine Learning: Pandas, Machine Learning
- Analytics & Visualization: Power BI

PROJECTS
1. Predictive Customer Churn Analysis
- Built machine learning classification models in Python using Pandas for exploratory data analysis.
- Executed complex SQL queries to clean and transform 50,000+ customer records.
- Designed interactive business analytics dashboards in Power BI.

2. Student Performance Predictor
- Implemented machine learning regression algorithms in Python.
- Utilized Pandas for feature engineering and statistical data summarization.
"""

DATA_SCIENTIST_JD = """
Senior Data Scientist
We are seeking an experienced Data Scientist to design predictive models and mine insights.
Requirements:
- Strong proficiency in Python, SQL, Statistics & Probability, and Machine Learning.
- Hands-on experience with Pandas and Scikit-Learn.
- Experience with Deep Learning, NLP, and Cloud (AWS) is preferred.
"""


# ===========================================================================
# 1. Candidate End-to-End Workflow Test
# ===========================================================================

class TestCandidateWorkflowE2E:
    """Verifies all 12 steps of the candidate intelligence evaluation."""

    def test_candidate_complete_workflow(self):
        # Step 1: Resume Uploads
        pdf_bytes = create_pdf(CANDIDATE_RESUME_TEXT)
        upload_resp = client.post(
            "/api/v1/documents/parse",
            files={"file": ("aditya_resume.pdf", pdf_bytes, "application/pdf")}
        )
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        doc_data = upload_resp.json()

        # Step 2: Text is Extracted
        extracted_text = doc_data.get("text", "")
        assert len(extracted_text) > 100
        assert "B.Tech Computer Science" in extracted_text
        assert "Python" in extracted_text
        assert "Machine Learning" in extracted_text
        assert doc_data.get("page_count") == 1

        # Step 3: Skills are Detected
        extract_resp = client.post(
            "/api/v1/skills/extract",
            json={"resume_text": extracted_text}
        )
        assert extract_resp.status_code == 200
        skill_data = extract_resp.json()
        detected_skills = skill_data.get("skills", [])
        assert len(detected_skills) >= 5

        detected_names = [s["canonical_name"] for s in detected_skills]
        # Required skills in prompt
        assert "Python" in detected_names
        assert "SQL" in detected_names
        assert "Pandas" in detected_names
        assert "Machine Learning" in detected_names
        assert "Power BI" in detected_names

        # Step 4: Skills are Normalized
        for skill in detected_skills:
            assert skill["canonical_id"] is not None
            assert skill["category"] is not None
            assert 0.0 <= skill["confidence"] <= 1.0
            assert len(skill["evidence"]) > 0

        # Step 5: Data Scientist Role Loads
        role = role_engine.get_role("data_scientist")
        assert role is not None
        assert role.title == "Data Scientist"
        req_skill_names = [r.canonical_name for r in role.required_skills]
        assert "Python" in req_skill_names
        assert "Machine Learning" in req_skill_names

        # Step 6: Match Score is Generated
        match_resp = client.post(
            "/api/v1/matching/analyze",
            json={
                "candidate_skills": detected_skills,
                "target_role": "data_scientist",
                "candidate_experience_years": 1.0
            }
        )
        assert match_resp.status_code == 200
        match_result = match_resp.json()
        score = match_result["final_match_score"]
        assert 0.0 < score <= 100.0
        assert match_result["score_grade"] in [
            "Exceptional Match", "High Alignment", "Moderate Potential", "Needs Upskilling"
        ]

        # Step 7: Matched Skills Appear
        strong_matches = [m["skill"] for m in match_result["strong_matches"]]
        assert "Python" in strong_matches
        assert "SQL" in strong_matches
        assert "Pandas" in strong_matches
        assert "Machine Learning" in strong_matches

        # Step 8: Missing Skills Appear
        missing_skills = [m["skill"] for m in match_result["missing_skills"]]
        assert len(missing_skills) > 0
        # E.g. Scikit-Learn or Statistics & Probability should be missing
        assert any(sk in missing_skills for sk in ["Scikit-Learn", "Statistics & Probability", "Deep Learning"])

        # Step 9: Explanation Appears
        why_score = match_result["why_score"]
        assert "because" in why_score
        assert "high-priority skills were matched" in why_score
        assert "system_disclaimer" in match_result
        assert "decision support" in match_result["system_disclaimer"].lower()

        # Step 10: Skill Gaps are Prioritized
        gap_resp = client.post(
            "/api/v1/gap/analyze",
            json={
                "candidate_skills": detected_skills,
                "target_role": "data_scientist"
            }
        )
        assert gap_resp.status_code == 200
        gap_report = gap_resp.json()
        assert len(gap_report["priority_order"]) > 0
        for gap in gap_report["priority_order"]:
            assert gap["priority"] in ["HIGH", "MEDIUM", "LOW"]
            assert "reason" in gap

        # Step 11: Learning Roadmap is Generated
        roadmap_resp = client.post(
            "/api/v1/recommendations/roadmap",
            json={
                "candidate_skills": detected_skills,
                "target_role": "data_scientist",
                "missing_skills": missing_skills
            }
        )
        assert roadmap_resp.status_code == 200
        roadmap = roadmap_resp.json()["roadmap"]
        assert len(roadmap) > 0
        for milestone in roadmap:
            assert milestone["skill"] is not None
            assert milestone["priority"] in ["HIGH", "MEDIUM", "LOW"]
            assert milestone["recommended_sequence"] >= 1
            assert len(milestone["available_learning_resources"]) > 0

        # Step 12: Adjacent Roles are Shown
        roles_resp = client.post(
            "/api/v1/recommendations/roles",
            json={
                "candidate_skills": detected_skills,
                "current_role": "data_scientist"
            }
        )
        assert roles_resp.status_code == 200
        rec_data = roles_resp.json()
        recommended_titles = [r["role_title"] for r in rec_data["recommended_roles"]]
        assert len(recommended_titles) >= 3
        # Should recommend complementary roles like Data Analyst or ML Engineer
        assert any(
            t in recommended_titles
            for t in ["Data Analyst", "Machine Learning Engineer", "Backend Software Engineer", "Python Developer"]
        )

    def test_candidate_unified_pipeline_endpoint(self):
        """Verifies the unified candidate pipeline returns all 12 components in a single pass."""
        resp = client.post(
            "/api/v1/matching/candidate-pipeline",
            json={
                "candidate_skills": ["Python", "SQL", "Pandas", "Machine Learning", "Power BI"],
                "target_role": "data_scientist",
                "candidate_experience_years": 1.0,
                "candidate_name": "Aditya Verma"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "matching" in data
        assert "gap_analysis" in data
        assert "roadmap" in data
        assert "recommendations" in data
        assert data["execution_time_ms"] > 0.0
        # Verify matched skills
        matched = [m["skill"] for m in data["matching"]["strong_matches"]]
        assert "Python" in matched
        assert "Machine Learning" in matched


# ===========================================================================
# 2. Recruiter Workflow Test
# ===========================================================================

class TestRecruiterWorkflowE2E:
    """Verifies all steps of the recruiter screening & talent ranking workflow."""

    def test_recruiter_complete_workflow(self):
        # Step 1: Paste Data Scientist JD
        parse_jd_resp = client.post(
            "/api/v1/recruiter/parse-jd",
            json={"job_description": DATA_SCIENTIST_JD, "job_title": "Data Scientist"}
        )
        assert parse_jd_resp.status_code == 200
        jd_data = parse_jd_resp.json()
        req_skills = jd_data["required_skills"]
        assert "Python" in req_skills
        assert "Machine Learning" in req_skills

        # Step 2: Upload at least 3 demo resumes
        resumes = [
            {
                "id": "cand_01",
                "name": "Pawan Kumar",
                "skills": ["Python", "SQL", "Machine Learning", "Statistics & Probability", "Pandas", "Scikit-Learn"],
                "exp": 4.0
            },
            {
                "id": "cand_02",
                "name": "Priya Patel",
                "skills": ["Python", "SQL", "Machine Learning", "Pandas"],
                "exp": 2.0
            },
            {
                "id": "cand_03",
                "name": "Aarav Sharma",
                "skills": ["Python", "SQL", "HTML5", "CSS3"],
                "exp": 1.0
            },
            {
                "id": "cand_04",
                "name": "Junior Applicant",
                "skills": ["HTML5"],
                "exp": 0.5
            },
        ]
        assert len(resumes) >= 3

        # Step 3, 4, 5: Extract skills, calculate scores, rank candidates
        candidate_payloads = [
            {
                "id": c["id"],
                "name": c["name"],
                "candidate_skills": c["skills"],
                "experience_years": c["exp"],
                "filename": f"{c['id']}.pdf"
            }
            for c in resumes
        ]

        rank_resp = client.post(
            "/api/v1/recruiter/rank",
            json={
                "job_title": "Data Scientist",
                "job_description": DATA_SCIENTIST_JD,
                "required_skills": req_skills,
                "candidates": candidate_payloads
            }
        )
        assert rank_resp.status_code == 200
        rank_data = rank_resp.json()
        ranked = rank_data["ranked_candidates"]
        assert len(ranked) == len(resumes)

        # Verify ranking order (descending by score)
        scores = [c["match_score"] for c in ranked]
        assert scores == sorted(scores, reverse=True)
        assert ranked[0]["name"] == "Pawan Kumar"
        assert ranked[-1]["name"] == "Junior Applicant"

        # Step 6: Show explanations
        top_cand = ranked[0]
        assert "detailed_explanation" in top_cand
        expl = top_cand["detailed_explanation"]
        assert len(expl["matched"]) > 0
        assert "Python" in expl["matched"]
        assert "reason" in top_cand
        assert "ethical" not in rank_data or "Highest measured skill alignment" in rank_data["top_candidate_statement"]
        assert "decision support" in rank_data["disclaimer"].lower()


# ===========================================================================
# 3. Failure Scenarios Test
# ===========================================================================

class TestFailureScenarios:
    """Verifies graceful rejection, non-crashing behavior, and clear error reporting."""

    def test_invalid_pdf(self):
        """Invalid / corrupted PDF content must return HTTP 422 or sanitized error."""
        corrupted_bytes = b"%PDF-1.4\ncorrupted_binary_garbage_bytes_xyz\x00\xff"
        resp = client.post(
            "/api/v1/documents/parse",
            files={"file": ("corrupted.pdf", corrupted_bytes, "application/pdf")}
        )
        assert resp.status_code in [400, 422]
        detail = resp.json().get("detail", "")
        assert len(detail) > 0
        assert "traceback" not in detail.lower()

    def test_empty_resume(self):
        """0-byte file must be rejected with HTTP 400 Bad Request."""
        empty_bytes = b""
        resp = client.post(
            "/api/v1/documents/parse",
            files={"file": ("empty.pdf", empty_bytes, "application/pdf")}
        )
        assert resp.status_code == 400
        assert "empty" in resp.json().get("detail", "").lower()

    def test_unsupported_file(self):
        """Unsupported extensions (e.g. .exe) must be rejected with HTTP 400."""
        exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
        resp = client.post(
            "/api/v1/documents/parse",
            files={"file": ("malicious.exe", exe_bytes, "application/x-msdownload")}
        )
        assert resp.status_code == 400
        assert "unsupported" in resp.json().get("detail", "").lower()

    def test_missing_role(self):
        """Unknown role slug must not crash the server (returns 200 with fallback/custom profile)."""
        resp = client.post(
            "/api/v1/matching/analyze",
            json={
                "candidate_skills": ["Python", "SQL"],
                "target_role": "unknown_future_role_xyz_999",
                "candidate_experience_years": 2.0
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "final_match_score" in data
        assert "why_score" in data

    def test_empty_skill_set(self):
        """Candidate with no detected skills returns 0 score without exceptions."""
        resp = client.post(
            "/api/v1/matching/analyze",
            json={
                "candidate_skills": [],
                "target_role": "data_scientist",
                "candidate_experience_years": 0.0
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_match_score"] == 0.0
        assert data["score_grade"] == "Needs Upskilling"
        assert len(data["missing_skills"]) > 0
        assert len(data["strong_matches"]) == 0
        assert "0%" in data["why_score"]

    def test_health_check_endpoint(self):
        """Confirms backend service health reporting."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
