"""Internal Automated Tests for UAT Evaluation Logic (UAT-EVAL-01 through UAT-EVAL-07)."""

import pytest
from app.services.uat_evaluator import UATEvaluator


def test_uat_eval_01_valid_resume_analysis():
    """UAT-EVAL-01: Valid resume analysis -> PASS."""
    res = UATEvaluator.evaluate_uat_01(
        file_accepted=True,
        parsing_succeeded=True,
        extracted_text="Jane Doe\nExperienced Python and SQL backend engineer with 4 years building scalable services.",
        skill_extraction_succeeded=True,
        extracted_skills=["Python", "SQL", "FastAPI"],
        results_displayed=True,
        filename="Jane_Resume.pdf",
        duration_seconds=2.1,
    )
    assert res.status == "PASS"
    assert res.failure_reason is None
    assert "Extracted 3 competencies" in res.actual_result
    assert len(res.passed_conditions) == 6
    assert len(res.failed_conditions) == 0


def test_uat_eval_02_resume_upload_succeeds_parsing_fails():
    """UAT-EVAL-02: Resume upload succeeds but parsing fails -> FAIL."""
    res = UATEvaluator.evaluate_uat_01(
        file_accepted=True,
        parsing_succeeded=False,
        extracted_text=None,
        skill_extraction_succeeded=False,
        extracted_skills=[],
        results_displayed=False,
        filename="corrupted.pdf",
    )
    assert res.status == "FAIL"
    assert res.failure_reason == "Resume uploaded successfully, but parsing did not complete."
    assert "Resume parsing did not complete" in res.failed_conditions


def test_uat_eval_03_resume_parsing_succeeds_skill_extraction_fails():
    """UAT-EVAL-03: Resume parsing succeeds but skill extraction fails -> FAIL."""
    res = UATEvaluator.evaluate_uat_01(
        file_accepted=True,
        parsing_succeeded=True,
        extracted_text="Some valid extracted resume text about software engineering and mathematics.",
        skill_extraction_succeeded=False,
        extracted_skills=None,
        results_displayed=False,
    )
    assert res.status == "FAIL"
    assert res.failure_reason == "Resume parsed successfully, but skill extraction returned no valid result."
    assert "Skill extraction process failed" in res.failed_conditions


def test_uat_eval_04_valid_match_result():
    """UAT-EVAL-04: Valid match result -> PASS."""
    res = UATEvaluator.evaluate_uat_02(
        candidate_profile_exists=True,
        target_role_exists=True,
        matching_completed=True,
        match_result_returned=True,
        match_score=82.5,
        skill_alignment_exists=True,
        skill_gap_result_exists=True,
        results_displayed=True,
        target_role_title="Data Scientist",
    )
    assert res.status == "PASS"
    assert res.failure_reason is None
    assert "Calculated match score: 82/100" in res.actual_result
    assert len(res.failed_conditions) == 0


def test_uat_eval_05_invalid_match_score():
    """UAT-EVAL-05: Invalid match score -> FAIL."""
    # Negative score
    res_neg = UATEvaluator.evaluate_uat_02(
        candidate_profile_exists=True,
        target_role_exists=True,
        matching_completed=True,
        match_result_returned=True,
        match_score=-15.0,
        skill_alignment_exists=True,
        skill_gap_result_exists=True,
    )
    assert res_neg.status == "FAIL"
    assert res_neg.failure_reason == "Match analysis did not return a valid score."

    # None score
    res_none = UATEvaluator.evaluate_uat_02(
        candidate_profile_exists=True,
        target_role_exists=True,
        matching_completed=True,
        match_result_returned=True,
        match_score=None,
        skill_alignment_exists=True,
        skill_gap_result_exists=True,
    )
    assert res_none.status == "FAIL"
    assert res_none.failure_reason == "Match analysis did not return a valid score."


def test_uat_eval_06_valid_recruiter_shortlist():
    """UAT-EVAL-06: Valid recruiter shortlist -> PASS."""
    res = UATEvaluator.evaluate_uat_03(
        recruiter_authorized=True,
        job_exists=True,
        candidates_available=True,
        candidate_matching_completed=True,
        candidate_ranking_returned=True,
        candidate_score_valid=True,
        candidate_detail_accessible=True,
        shortlist_action_succeeded=True,
        shortlist_persisted=True,
        candidate_name="Aarav Sharma",
        job_title="Senior Python Backend Engineer",
    )
    assert res.status == "PASS"
    assert res.failure_reason is None
    assert "Shortlisted candidate 'Aarav Sharma'" in res.actual_result


def test_uat_eval_07_shortlist_failure():
    """UAT-EVAL-07: Shortlist failure -> FAIL."""
    res = UATEvaluator.evaluate_uat_03(
        recruiter_authorized=True,
        job_exists=True,
        candidates_available=True,
        candidate_matching_completed=True,
        candidate_ranking_returned=True,
        candidate_score_valid=True,
        candidate_detail_accessible=True,
        shortlist_action_succeeded=False,
        shortlist_persisted=False,
        candidate_name="Candidate",
    )
    assert res.status == "FAIL"
    assert res.failure_reason == "Candidate matching completed, but shortlist action failed."
