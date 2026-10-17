"""ATS Resume Analysis and Readiness Scoring Service.

Provides deterministic, explainable, and transparent evaluation of resume ATS-readiness.
Evaluates:
- Parseability & Structure
- Content Completeness
- Skills Presentation (no keyword stuffing bonus)
- Experience & Impact
- Formatting Signals
- Job Skill / Keyword Alignment (when job description provided)

Zero LLM score fabrication. 100% deterministic rules grounded in extracted text and taxonomy.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

from app.core.extractor import extractor, ExtractedSkill
from app.core.normalizer import normalizer
from app.utils.text_cleaner import clean_text, extract_sentences


# ---------------------------------------------------------------------------
# Transparent Weight Configurations (Centrally Stored)
# ---------------------------------------------------------------------------

GENERAL_WEIGHTS = {
    "parseability": 25.0,
    "content": 20.0,
    "skills": 20.0,
    "impact": 20.0,
    "formatting": 15.0,
}

JOB_SPECIFIC_WEIGHTS = {
    "parseability": 20.0,
    "content": 15.0,
    "job_alignment": 30.0,
    "impact": 20.0,
    "formatting": 15.0,
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ATSCategoryScore(BaseModel):
    category_id: str
    name: str
    score: float
    max_score: float
    percentage: float
    status: str  # "Strong", "Good", "Needs Improvement", "Needs Attention"


class ATSChecklistItem(BaseModel):
    label: str
    status: str  # "pass", "warning", "fail"
    detail: str


class ATSRecommendation(BaseModel):
    priority: str  # "HIGH", "MEDIUM", "LOW"
    title: str
    description: str
    category: str


class ATSMatchedSkill(BaseModel):
    name: str
    canonical_name: str
    category: str
    evidence: Optional[str] = None


class ATSMissingSkill(BaseModel):
    name: str
    canonical_name: str
    category: str


class ATSAnalysisResponse(BaseModel):
    overall_score: int
    rating: str  # "Excellent", "Strong", "Good", "Needs Improvement", "Needs Attention"
    check_type: str  # "general" or "job_specific"
    target_job_title: Optional[str] = None
    category_scores: List[ATSCategoryScore]
    whats_working: List[str]
    needs_attention: List[str]
    resume_health: Dict[str, Any]
    matched_skills: List[ATSMatchedSkill]
    missing_skills: List[ATSMissingSkill]
    recommendations: List[ATSRecommendation]
    checklist: List[ATSChecklistItem]
    job_alignment_percentage: Optional[float] = None
    total_jd_skills: int = 0
    matched_jd_skills_count: int = 0
    parse_confidence: str  # "High", "Medium", "Low"
    word_count: int
    character_count: int
    page_count: int
    disclaimer: str = (
        "This score estimates how well your resume follows common ATS-friendly practices and, "
        "when a job description is provided, how well its content aligns with that role. "
        "Actual employer systems may evaluate resumes differently."
    )


# ---------------------------------------------------------------------------
# Section Recognition Patterns (Accepts all standard synonyms)
# ---------------------------------------------------------------------------

SECTION_PATTERNS = {
    "contact": [
        r"\b(contact|email|phone|address|linkedin|github)\b",
    ],
    "experience": [
        r"\b(experience|work\s+experience|professional\s+experience|employment\s+history|work\s+history|career\s+history|professional\s+background)\b",
    ],
    "education": [
        r"\b(education|academic\s+background|academic\s+history|qualifications|degrees|educational\s+qualifications)\b",
    ],
    "skills": [
        r"\b(skills|technical\s+skills|core\s+competencies|technologies|proficiencies|key\s+skills|tools\s+(&|and)\s+technologies)\b",
    ],
    "projects": [
        r"\b(projects|personal\s+projects|academic\s+projects|key\s+projects|portfolio|initiatives)\b",
    ],
    "summary": [
        r"\b(summary|professional\s+summary|profile|about\s+me|career\s+objective|objective|executive\s+summary)\b",
    ],
    "certifications": [
        r"\b(certifications|certificates|licenses|credentials|accreditations)\b",
    ],
}

ACTION_VERBS = {
    "built", "developed", "designed", "implemented", "created", "engineered",
    "architected", "optimized", "reduced", "increased", "spearheaded", "orchestrated",
    "automated", "led", "managed", "deployed", "analyzed", "established",
    "improved", "streamlined", "accelerated", "delivered", "executed", "initiated",
    "transformed", "scaled", "maintained", "integrated", "produced", "authored",
    "formulated", "coordinated", "resolved", "trained", "supervised", "directed"
}

METRIC_PATTERNS = [
    r"\b\d+%",                          # e.g. 25%
    r"\b\d+\s*(?:percent|percentage)\b", # e.g. 15 percent
    r"\b\$\s*\d+(?:[\.,]\d+)?\s*[kKmMbB]?\b", # e.g. $50k, $1.2M
    r"\b\d+(?:[\.,]\d+)?\s*(?:k|m|million|billion|thousand)\b", # e.g. 50k, 2 million
    r"\b\d+\+?\s*(?:users|clients|records|requests|transactions|queries|servers|endpoints|engineers|members|students)\b",
    r"\b(?:reduced|increased|improved|decreased|cut|boosted)\s+by\s+\d+",
    r"\b\d+x\b",                         # e.g. 3x
]


# ---------------------------------------------------------------------------
# Scoring Service
# ---------------------------------------------------------------------------

class ATSService:
    @staticmethod
    def analyze(
        resume_text: str,
        filename: Optional[str] = None,
        file_size_bytes: int = 0,
        page_count: int = 1,
        check_type: str = "general",
        job_description_text: Optional[str] = None,
        target_job_title: Optional[str] = None,
    ) -> ATSAnalysisResponse:
        cleaned_text = clean_text(resume_text or "")
        words = re.findall(r"\b[A-Za-z0-9_\-\.\#\+]+\b", cleaned_text)
        word_count = len(words)
        char_count = len(cleaned_text)

        # 1. Parse Confidence
        if word_count < 50:
            parse_confidence = "Low"
        elif word_count < 150:
            parse_confidence = "Medium"
        else:
            parse_confidence = "High"

        # 2. Extract Sentences / Bullets
        sentences = extract_sentences(cleaned_text)

        # 3. Detect Sections
        detected_sections = ATSService._detect_sections(cleaned_text)

        # 4. Detect Contact Elements
        contact_info = ATSService._detect_contact(cleaned_text)

        # 5. Extract Resume Skills using existing hybrid extractor
        skill_report = extractor.extract_from_text(cleaned_text, source="resume")
        resume_skills = skill_report.skills

        # 6. Analyze Action Verbs & Quantified Metrics in Bullets
        bullet_analysis = ATSService._analyze_experience_bullets(sentences)

        # 7. Evaluate Formatting Signals
        formatting_analysis = ATSService._analyze_formatting(
            filename=filename,
            word_count=word_count,
            char_count=char_count,
            page_count=page_count,
            cleaned_text=cleaned_text,
        )

        # 8. If Job-Specific, Extract & Compare JD Skills
        is_job_specific = check_type == "job_specific" and bool(job_description_text and job_description_text.strip())
        jd_alignment_result = None
        if is_job_specific:
            jd_alignment_result = ATSService._analyze_jd_alignment(
                resume_skills=resume_skills,
                job_description_text=job_description_text,
            )

        # 9. Compute Category Scores (Deterministic Formulas)
        category_scores, overall_score = ATSService._compute_scores(
            is_job_specific=is_job_specific,
            word_count=word_count,
            detected_sections=detected_sections,
            contact_info=contact_info,
            resume_skills=resume_skills,
            bullet_analysis=bullet_analysis,
            formatting_analysis=formatting_analysis,
            jd_alignment_result=jd_alignment_result,
        )

        # 10. Determine Rating Tier
        rating = ATSService._get_rating_label(overall_score)

        # 11. Generate What's Working and Needs Attention
        whats_working, needs_attention = ATSService._generate_explanations(
            is_job_specific=is_job_specific,
            detected_sections=detected_sections,
            contact_info=contact_info,
            resume_skills=resume_skills,
            bullet_analysis=bullet_analysis,
            formatting_analysis=formatting_analysis,
            jd_alignment_result=jd_alignment_result,
        )

        # 12. Generate Actionable Recommendations (Prioritized, max 3-5 items)
        recommendations = ATSService._generate_recommendations(
            is_job_specific=is_job_specific,
            detected_sections=detected_sections,
            contact_info=contact_info,
            resume_skills=resume_skills,
            bullet_analysis=bullet_analysis,
            formatting_analysis=formatting_analysis,
            jd_alignment_result=jd_alignment_result,
        )

        # 13. Generate ATS Readiness Checklist
        checklist = ATSService._generate_checklist(
            is_job_specific=is_job_specific,
            detected_sections=detected_sections,
            contact_info=contact_info,
            bullet_analysis=bullet_analysis,
            formatting_analysis=formatting_analysis,
            jd_alignment_result=jd_alignment_result,
        )

        # 14. Build Matched & Missing Skills for Output
        matched_skills: List[ATSMatchedSkill] = []
        missing_skills: List[ATSMissingSkill] = []
        job_alignment_pct: Optional[float] = None
        total_jd_skills = 0
        matched_jd_count = 0

        if is_job_specific and jd_alignment_result:
            matched_skills = jd_alignment_result["matched_skills"]
            missing_skills = jd_alignment_result["missing_skills"]
            job_alignment_pct = jd_alignment_result["alignment_percentage"]
            total_jd_skills = jd_alignment_result["total_jd_skills"]
            matched_jd_count = jd_alignment_result["matched_count"]
        else:
            # For general check, show top detected skills with verified evidence
            for s in resume_skills[:12]:
                matched_skills.append(
                    ATSMatchedSkill(
                        name=s.name,
                        canonical_name=s.canonical_name,
                        category=s.category,
                        evidence=s.evidence if s.evidence else None,
                    )
                )

        # 15. Resume Health Overview
        resume_health = {
            "parseability": ATSService._tier_from_pct(
                next(c.percentage for c in category_scores if c.category_id == "parseability")
            ),
            "content": ATSService._tier_from_pct(
                next(c.percentage for c in category_scores if c.category_id == "content")
            ),
            "skills": ATSService._tier_from_pct(
                next(c.percentage for c in category_scores if c.category_id in ("skills", "job_alignment"))
            ),
            "impact": ATSService._tier_from_pct(
                next(c.percentage for c in category_scores if c.category_id == "impact")
            ),
            "formatting": ATSService._tier_from_pct(
                next(c.percentage for c in category_scores if c.category_id == "formatting")
            ),
        }
        if is_job_specific and job_alignment_pct is not None:
            resume_health["job_alignment"] = round(job_alignment_pct, 1)

        return ATSAnalysisResponse(
            overall_score=overall_score,
            rating=rating,
            check_type="job_specific" if is_job_specific else "general",
            target_job_title=target_job_title,
            category_scores=category_scores,
            whats_working=whats_working,
            needs_attention=needs_attention,
            resume_health=resume_health,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            recommendations=recommendations,
            checklist=checklist,
            job_alignment_percentage=job_alignment_pct,
            total_jd_skills=total_jd_skills,
            matched_jd_skills_count=matched_jd_count,
            parse_confidence=parse_confidence,
            word_count=word_count,
            character_count=char_count,
            page_count=page_count,
        )

    # -----------------------------------------------------------------------
    # Helper Inspection Methods
    # -----------------------------------------------------------------------

    @staticmethod
    def _detect_sections(text: str) -> Dict[str, bool]:
        lower_text = text.lower()
        results = {}
        for section, patterns in SECTION_PATTERNS.items():
            found = False
            for p in patterns:
                if re.search(p, lower_text):
                    found = True
                    break
            results[section] = found
        return results

    @staticmethod
    def _detect_contact(text: str) -> Dict[str, bool]:
        has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text))
        has_phone = bool(
            re.search(
                r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}",
                text,
            )
        )
        has_links = bool(
            re.search(r"\b(linkedin\.com|github\.com|http[s]?://)\b", text, re.IGNORECASE)
        )
        return {
            "email": has_email,
            "phone": has_phone,
            "links": has_links,
            "has_basic_contact": (has_email or has_phone),
        }

    @staticmethod
    def _analyze_experience_bullets(sentences: List[str]) -> Dict[str, Any]:
        total_bullets = len(sentences)
        action_verb_count = 0
        metric_count = 0

        for s in sentences:
            s_clean = s.strip()
            first_words = re.findall(r"^[A-Za-z]+", s_clean)
            if first_words and first_words[0].lower() in ACTION_VERBS:
                action_verb_count += 1
            else:
                # Also check within the first 3 tokens
                tokens = [t.lower() for t in re.findall(r"\b[A-Za-z]+\b", s_clean)[:3]]
                if any(t in ACTION_VERBS for t in tokens):
                    action_verb_count += 1

            # Check metrics
            for mp in METRIC_PATTERNS:
                if re.search(mp, s_clean, re.IGNORECASE):
                    metric_count += 1
                    break

        return {
            "total_sentences": total_bullets,
            "action_verb_count": action_verb_count,
            "metric_count": metric_count,
            "action_verb_ratio": (action_verb_count / max(total_bullets, 1)),
            "metric_ratio": (metric_count / max(total_bullets, 1)),
        }

    @staticmethod
    def _analyze_formatting(
        filename: Optional[str],
        word_count: int,
        char_count: int,
        page_count: int,
        cleaned_text: str,
    ) -> Dict[str, Any]:
        ext = ""
        if filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        valid_ext = ext in (".pdf", ".docx", ".txt", "")

        # Non-printable character ratio (checks for decoding artifacts)
        printable_chars = sum(1 for c in cleaned_text if c.isprintable() or c in "\n\t")
        cleanliness_ratio = printable_chars / max(char_count, 1)

        # Word count appropriateness
        word_count_status = "optimal"
        if word_count < 150:
            word_count_status = "too_short"
        elif word_count > 2500:
            word_count_status = "too_long"

        # Page count sanity
        reasonable_pages = (1 <= page_count <= 3)

        return {
            "valid_extension": valid_ext,
            "cleanliness_ratio": cleanliness_ratio,
            "word_count_status": word_count_status,
            "reasonable_pages": reasonable_pages,
            "text_extractable": word_count >= 50,
        }

    @staticmethod
    def _analyze_jd_alignment(
        resume_skills: List[ExtractedSkill],
        job_description_text: str,
    ) -> Dict[str, Any]:
        # Extract skills from JD using the exact same engine
        jd_report = extractor.extract_from_text(job_description_text, source="job_description")
        jd_skills = jd_report.skills

        # Build candidate canonical set
        resume_canonicals = {s.canonical_id: s for s in resume_skills}

        matched_skills: List[ATSMatchedSkill] = []
        missing_skills: List[ATSMissingSkill] = []

        seen_jd_canonicals = set()
        for jds in jd_skills:
            cid = jds.canonical_id
            if cid in seen_jd_canonicals:
                continue
            seen_jd_canonicals.add(cid)

            if cid in resume_canonicals:
                matched_item = resume_canonicals[cid]
                matched_skills.append(
                    ATSMatchedSkill(
                        name=matched_item.name,
                        canonical_name=matched_item.canonical_name,
                        category=matched_item.category,
                        evidence=matched_item.evidence if matched_item.evidence else None,
                    )
                )
            else:
                missing_skills.append(
                    ATSMissingSkill(
                        name=jds.name,
                        canonical_name=jds.canonical_name,
                        category=jds.category,
                    )
                )

        total_jd = len(seen_jd_canonicals)
        matched_count = len(matched_skills)
        alignment_pct = (matched_count / total_jd * 100.0) if total_jd > 0 else 100.0

        return {
            "total_jd_skills": total_jd,
            "matched_count": matched_count,
            "alignment_percentage": alignment_pct,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        }

    # -----------------------------------------------------------------------
    # Deterministic Scoring Mathematics
    # -----------------------------------------------------------------------

    @staticmethod
    def _compute_scores(
        is_job_specific: bool,
        word_count: int,
        detected_sections: Dict[str, bool],
        contact_info: Dict[str, bool],
        resume_skills: List[ExtractedSkill],
        bullet_analysis: Dict[str, Any],
        formatting_analysis: Dict[str, Any],
        jd_alignment_result: Optional[Dict[str, Any]],
    ) -> Tuple[List[ATSCategoryScore], int]:
        category_scores: List[ATSCategoryScore] = []

        # ===================================================================
        # Category A: Parseability & Structure
        # Max: 25 pts (General) or 20 pts (Job-Specific)
        # ===================================================================
        max_parse = 20.0 if is_job_specific else 25.0
        p_raw = 0.0

        # 1. Text extracted reliably (7 pts / 6 pts)
        if word_count >= 150:
            p_raw += 7.0 if not is_job_specific else 6.0
        elif word_count >= 50:
            p_raw += 4.0 if not is_job_specific else 3.5

        # 2. Key sections detectable (Education, Experience/Projects, Skills)
        # Experience or Projects recognized
        if detected_sections.get("experience") or detected_sections.get("projects"):
            p_raw += 6.0 if not is_job_specific else 5.0
        # Education recognized
        if detected_sections.get("education"):
            p_raw += 5.0 if not is_job_specific else 4.0
        # Skills section recognized
        if detected_sections.get("skills"):
            p_raw += 4.0 if not is_job_specific else 3.0
        # Contact recognizable
        if contact_info.get("has_basic_contact"):
            p_raw += 3.0 if not is_job_specific else 2.0

        parse_score = min(p_raw, max_parse)
        category_scores.append(
            ATSCategoryScore(
                category_id="parseability",
                name="Parseability & Structure",
                score=round(parse_score, 1),
                max_score=max_parse,
                percentage=round((parse_score / max_parse) * 100.0, 1),
                status=ATSService._tier_from_pct((parse_score / max_parse) * 100.0),
            )
        )

        # ===================================================================
        # Category B: Content Completeness
        # Max: 20 pts (General) or 15 pts (Job-Specific)
        # ===================================================================
        max_content = 15.0 if is_job_specific else 20.0
        c_raw = 0.0

        # Contact details (email, phone, links)
        if contact_info.get("email"):
            c_raw += 3.0 if not is_job_specific else 2.5
        if contact_info.get("phone"):
            c_raw += 2.0 if not is_job_specific else 1.5
        if contact_info.get("links"):
            c_raw += 2.0 if not is_job_specific else 1.5

        # Education
        if detected_sections.get("education"):
            c_raw += 4.0 if not is_job_specific else 3.0

        # Experience or Projects (freshers with projects treated equally)
        if detected_sections.get("experience") and detected_sections.get("projects"):
            c_raw += 5.0 if not is_job_specific else 4.0
        elif detected_sections.get("experience") or detected_sections.get("projects"):
            c_raw += 4.0 if not is_job_specific else 3.0

        # Optional summary or certifications give positive bump
        if detected_sections.get("summary"):
            c_raw += 2.0 if not is_job_specific else 1.5
        if detected_sections.get("certifications"):
            c_raw += 2.0 if not is_job_specific else 1.0

        content_score = min(c_raw, max_content)
        category_scores.append(
            ATSCategoryScore(
                category_id="content",
                name="Content Completeness",
                score=round(content_score, 1),
                max_score=max_content,
                percentage=round((content_score / max_content) * 100.0, 1),
                status=ATSService._tier_from_pct((content_score / max_content) * 100.0),
            )
        )

        # ===================================================================
        # Category C: Skills Presentation (General: 20 pts)
        # OR Job Skill / Keyword Alignment (Job-Specific: 30 pts)
        # ===================================================================
        if not is_job_specific:
            max_skills = 20.0
            s_raw = 0.0

            # Number of unique normalized skills detected (breadth without stuffing)
            unique_skill_count = len({s.canonical_id for s in resume_skills})
            if unique_skill_count >= 10:
                s_raw += 8.0
            elif unique_skill_count >= 6:
                s_raw += 6.0
            elif unique_skill_count >= 3:
                s_raw += 4.0
            elif unique_skill_count >= 1:
                s_raw += 2.0

            # Categories represented (diversity of competencies)
            categories = {s.category for s in resume_skills}
            if len(categories) >= 4:
                s_raw += 6.0
            elif len(categories) >= 2:
                s_raw += 4.0
            elif len(categories) >= 1:
                s_raw += 2.0

            # Evidence grounding: skills backed by real sentences (not just raw list)
            skills_with_evidence = sum(1 for s in resume_skills if s.evidence)
            evidence_ratio = (skills_with_evidence / max(len(resume_skills), 1))
            if evidence_ratio >= 0.6:
                s_raw += 6.0
            elif evidence_ratio >= 0.3:
                s_raw += 4.0
            else:
                s_raw += 2.0

            skills_score = min(s_raw, max_skills)
            category_scores.append(
                ATSCategoryScore(
                    category_id="skills",
                    name="Skills Presentation",
                    score=round(skills_score, 1),
                    max_score=max_skills,
                    percentage=round((skills_score / max_skills) * 100.0, 1),
                    status=ATSService._tier_from_pct((skills_score / max_skills) * 100.0),
                )
            )
        else:
            # Job-Specific: 30 points based on canonical skill coverage
            max_alignment = 30.0
            alignment_pct = jd_alignment_result["alignment_percentage"] if jd_alignment_result else 100.0
            # Scale alignment percentage to 30 points
            alignment_score = min((alignment_pct / 100.0) * max_alignment, max_alignment)
            category_scores.append(
                ATSCategoryScore(
                    category_id="job_alignment",
                    name="Job Skill & Keyword Alignment",
                    score=round(alignment_score, 1),
                    max_score=max_alignment,
                    percentage=round(alignment_pct, 1),
                    status=ATSService._tier_from_pct(alignment_pct),
                )
            )

        # ===================================================================
        # Category D: Experience & Impact
        # Max: 20 pts (both modes)
        # ===================================================================
        max_impact = 20.0
        i_raw = 0.0

        action_count = bullet_analysis["action_verb_count"]
        metric_count = bullet_analysis["metric_count"]

        # Action-oriented statements
        if action_count >= 8:
            i_raw += 10.0
        elif action_count >= 5:
            i_raw += 8.0
        elif action_count >= 3:
            i_raw += 6.0
        elif action_count >= 1:
            i_raw += 4.0

        # Quantified impact / metrics where genuinely present
        if metric_count >= 4:
            i_raw += 10.0
        elif metric_count >= 2:
            i_raw += 7.0
        elif metric_count >= 1:
            i_raw += 5.0
        else:
            i_raw += 2.0  # Do not harshly penalize if absent

        impact_score = min(i_raw, max_impact)
        category_scores.append(
            ATSCategoryScore(
                category_id="impact",
                name="Experience & Impact",
                score=round(impact_score, 1),
                max_score=max_impact,
                percentage=round((impact_score / max_impact) * 100.0, 1),
                status=ATSService._tier_from_pct((impact_score / max_impact) * 100.0),
            )
        )

        # ===================================================================
        # Category E: ATS-Friendly Formatting Signals
        # Max: 15 pts (both modes)
        # ===================================================================
        max_formatting = 15.0
        f_raw = 0.0

        if formatting_analysis["valid_extension"]:
            f_raw += 4.0
        if formatting_analysis["cleanliness_ratio"] >= 0.95:
            f_raw += 4.0
        elif formatting_analysis["cleanliness_ratio"] >= 0.85:
            f_raw += 2.5

        if formatting_analysis["word_count_status"] == "optimal":
            f_raw += 4.0
        elif formatting_analysis["word_count_status"] in ("too_short", "too_long"):
            f_raw += 2.0

        if formatting_analysis["reasonable_pages"]:
            f_raw += 3.0

        formatting_score = min(f_raw, max_formatting)
        category_scores.append(
            ATSCategoryScore(
                category_id="formatting",
                name="ATS-Friendly Formatting Signals",
                score=round(formatting_score, 1),
                max_score=max_formatting,
                percentage=round((formatting_score / max_formatting) * 100.0, 1),
                status=ATSService._tier_from_pct((formatting_score / max_formatting) * 100.0),
            )
        )

        # Sum total
        raw_total = sum(c.score for c in category_scores)
        overall_score = max(10, min(100, int(round(raw_total))))

        return category_scores, overall_score

    # -----------------------------------------------------------------------
    # Explanation & Recommendation Generators
    # -----------------------------------------------------------------------

    @staticmethod
    def _get_rating_label(score: int) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 80:
            return "Strong"
        if score >= 70:
            return "Good"
        if score >= 60:
            return "Needs Improvement"
        return "Needs Attention"

    @staticmethod
    def _tier_from_pct(pct: float) -> str:
        if pct >= 85:
            return "Strong"
        if pct >= 70:
            return "Good"
        return "Needs Improvement"

    @staticmethod
    def _generate_explanations(
        is_job_specific: bool,
        detected_sections: Dict[str, bool],
        contact_info: Dict[str, bool],
        resume_skills: List[ExtractedSkill],
        bullet_analysis: Dict[str, Any],
        formatting_analysis: Dict[str, Any],
        jd_alignment_result: Optional[Dict[str, Any]],
    ) -> Tuple[List[str], List[str]]:
        whats_working: List[str] = []
        needs_attention: List[str] = []

        # Working points
        if formatting_analysis.get("text_extractable"):
            whats_working.append("Resume text parsed cleanly into structured text layer.")

        if detected_sections.get("skills"):
            whats_working.append("Dedicated skills section reliably recognized.")

        if contact_info.get("email") and contact_info.get("phone"):
            whats_working.append("Standard contact channels (email & phone) clearly detected.")

        if bullet_analysis.get("action_verb_count", 0) >= 3:
            whats_working.append(
                f"{bullet_analysis['action_verb_count']} experience bullets lead with decisive action verbs."
            )

        if is_job_specific and jd_alignment_result:
            matched_count = jd_alignment_result["matched_count"]
            total_jd = jd_alignment_result["total_jd_skills"]
            pct = round(jd_alignment_result["alignment_percentage"])
            whats_working.append(
                f"{matched_count} of {total_jd} target role skills ({pct}%) directly matched."
            )
        elif len(resume_skills) >= 5:
            top_names = ", ".join(s.canonical_name for s in resume_skills[:3])
            whats_working.append(f"Strong foundation of recognized core skills ({top_names}).")

        # Attention points
        if is_job_specific and jd_alignment_result:
            missing_skills = jd_alignment_result["missing_skills"]
            if missing_skills:
                missing_names = ", ".join(m.name for m in missing_skills[:2])
                needs_attention.append(
                    f"{missing_names} demanded by target role but not detected in resume text."
                )

        if bullet_analysis.get("metric_count", 0) == 0:
            needs_attention.append(
                "Limited quantified impact or outcomes detected across project statements."
            )

        if not contact_info.get("links"):
            needs_attention.append("No professional portfolio or GitHub/LinkedIn links identified.")

        if not (detected_sections.get("experience") or detected_sections.get("projects")):
            needs_attention.append("Experience and projects headings could not be distinctly separated.")

        if formatting_analysis.get("word_count_status") == "too_short":
            needs_attention.append("Resume contains under 150 words; consider adding detailed project scope.")

        return whats_working[:4], needs_attention[:3]

    @staticmethod
    def _generate_recommendations(
        is_job_specific: bool,
        detected_sections: Dict[str, bool],
        contact_info: Dict[str, bool],
        resume_skills: List[ExtractedSkill],
        bullet_analysis: Dict[str, Any],
        formatting_analysis: Dict[str, Any],
        jd_alignment_result: Optional[Dict[str, Any]],
    ) -> List[ATSRecommendation]:
        recs: List[ATSRecommendation] = []

        # 1. High Priority: Missing Required Skills (if job-specific)
        if is_job_specific and jd_alignment_result:
            missing = jd_alignment_result["missing_skills"]
            if missing:
                top_missing = missing[0].name
                recs.append(
                    ATSRecommendation(
                        priority="HIGH",
                        title=f"Address missing target competency ({top_missing})",
                        description=(
                            f"The target role specifies {top_missing}, but it was not detected in your resume. "
                            "Only add this skill if you genuinely possess real-world or academic experience with it."
                        ),
                        category="Job Alignment",
                    )
                )

        # 2. High / Medium Priority: Quantified Impact
        if bullet_analysis.get("metric_count", 0) < 2:
            recs.append(
                ATSRecommendation(
                    priority="HIGH" if bullet_analysis.get("metric_count", 0) == 0 else "MEDIUM",
                    title="Incorporate measurable outcomes in project descriptions",
                    description=(
                        "Strengthen project bullets by pairing responsibilities with measurable scope. "
                        "Example structure: 'Developed [feature] using [technologies], achieving [specific measurable result]'."
                    ),
                    category="Experience & Impact",
                )
            )

        # 3. Medium Priority: Skill Evidence Context
        low_evidence = [s.name for s in resume_skills if not s.evidence]
        if low_evidence:
            sample_skills = ", ".join(low_evidence[:2])
            recs.append(
                ATSRecommendation(
                    priority="MEDIUM",
                    title=f"Provide contextual evidence for listed competencies ({sample_skills})",
                    description=(
                        f"Skills such as {sample_skills} appear in a list but lack supporting context in your "
                        "experience or project descriptions. Reference tools inside active project statements."
                    ),
                    category="Skills Presentation",
                )
            )

        # 4. Low Priority: Contact / Links
        if not contact_info.get("links"):
            recs.append(
                ATSRecommendation(
                    priority="LOW",
                    title="Include direct links to professional profiles",
                    description=(
                        "Adding standard GitHub, LinkedIn, or portfolio URLs assists recruiters in validating "
                        "your technical background and project repositories."
                    ),
                    category="Completeness",
                )
            )

        return recs[:4]

    @staticmethod
    def _generate_checklist(
        is_job_specific: bool,
        detected_sections: Dict[str, bool],
        contact_info: Dict[str, bool],
        bullet_analysis: Dict[str, Any],
        formatting_analysis: Dict[str, Any],
        jd_alignment_result: Optional[Dict[str, Any]],
    ) -> List[ATSChecklistItem]:
        items: List[ATSChecklistItem] = [
            ATSChecklistItem(
                label="Text extractable without parsing artifacts",
                status="pass" if formatting_analysis.get("text_extractable") else "fail",
                detail="Resume content extracted cleanly into plain text layer.",
            ),
            ATSChecklistItem(
                label="Education section detectable",
                status="pass" if detected_sections.get("education") else "warning",
                detail="Recognized academic qualifications or degree references.",
            ),
            ATSChecklistItem(
                label="Skills section detectable",
                status="pass" if detected_sections.get("skills") else "warning",
                detail="Dedicated technical proficiencies or competencies identified.",
            ),
            ATSChecklistItem(
                label="Experience or projects identifiable",
                status="pass" if (detected_sections.get("experience") or detected_sections.get("projects")) else "fail",
                detail="Professional employment or portfolio initiatives recognized.",
            ),
            ATSChecklistItem(
                label="Action verbs lead project statements",
                status="pass" if bullet_analysis.get("action_verb_count", 0) >= 3 else "warning",
                detail=f"{bullet_analysis.get('action_verb_count', 0)} action verbs detected across sentence starts.",
            ),
            ATSChecklistItem(
                label="Supported ATS document format",
                status="pass" if formatting_analysis.get("valid_extension") else "fail",
                detail="Clean PDF, DOCX, or text formatting.",
            ),
        ]

        if is_job_specific and jd_alignment_result:
            pct = jd_alignment_result.get("alignment_percentage", 0)
            items.insert(
                4,
                ATSChecklistItem(
                    label="Target JD skill coverage",
                    status="pass" if pct >= 75 else ("warning" if pct >= 50 else "fail"),
                    detail=f"{round(pct)}% of target job description requirements matched.",
                )
            )

        return items
