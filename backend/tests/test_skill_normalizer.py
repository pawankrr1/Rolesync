"""Comprehensive Unit Tests for SkillNormalizer and Canonical Skill Taxonomy.

Verifies:
- At least 50 distinct normalization test cases
- Difficult abbreviations (JS, TS, ML, DL, NLP, AWS, GCP, Postgres, PyTorch)
- Case normalization (UPPERCASE, lowercase, mixed-case)
- Punctuation & delimiter normalization (hyphens, underscores, slashes, dots)
- Fuzzy matching with confidence scores for typos
- Semantic token overlap for descriptive phrases
- Preservation of unknown/ambiguous terms as unresolved (confidence=0.0, is_resolved=False)
- Canonical skill system metadata (id, name, category, aliases, related_skills, description, importance)
"""

import pytest
from app.core.normalizer import normalizer, SkillNormalizer, NormalizationResult
from app.core.taxonomy import taxonomy, SkillDefinition


# ==============================================================================
# 1. 50+ DETERMINISTIC NORMALIZATION TEST CASES
# ==============================================================================

NORMALIZATION_CASES_50 = [
    # 1-10: Required Difficult Cases & Core Abbreviation Cases
    ("JS", "JavaScript", "abbreviation"),
    ("TS", "TypeScript", "abbreviation"),
    ("ML", "Machine Learning", "abbreviation"),
    ("DL", "Deep Learning", "abbreviation"),
    ("NLP", "Natural Language Processing", "exact"),
    ("AWS", "Amazon Web Services", "exact"),
    ("GCP", "Google Cloud Platform", "exact"),
    ("Postgres", "PostgreSQL", "abbreviation"),
    ("PyTorch", "PyTorch", "exact"),
    ("k8s", "Kubernetes (K8s)", "abbreviation"),

    # 11-20: Case Variations (UPPERCASE, lowercase, mixed-case)
    ("javascript", "JavaScript", "exact"),
    ("JAVASCRIPT", "JavaScript", "exact"),
    ("jAvAsCrIpT", "JavaScript", "case_normalized"),
    ("typescript", "TypeScript", "exact"),
    ("TYPESCRIPT", "TypeScript", "exact"),
    ("python", "Python", "exact"),
    ("PYTHON", "Python", "exact"),
    ("pYtHoN", "Python", "case_normalized"),
    ("POSTGRESQL", "PostgreSQL", "exact"),
    ("pYtOrCh", "PyTorch", "case_normalized"),

    # 21-30: Punctuation, Hyphens, Delimiters, & Web Dots
    ("Machine-Learning", "Machine Learning", "alias"),
    ("machine_learning", "Machine Learning", "exact"),
    ("machine  learning", "Machine Learning", "punctuation_normalized"),
    ("Deep-Learning", "Deep Learning", "punctuation_normalized"),
    ("deep_learning", "Deep Learning", "exact"),
    ("React.js", "React.js", "exact"),
    ("react-js", "React.js", "fuzzy"),
    ("Node.js", "Node.js", "exact"),
    ("node_js", "Node.js", "exact"),
    ("CI/CD", "CI/CD Pipelines", "abbreviation"),

    # 31-40: Aliases, Synonyms & Technical Variants
    ("py", "Python", "abbreviation"),
    ("python3", "Python", "alias"),
    ("python 3", "Python", "alias"),
    ("cpython", "Python", "alias"),
    ("vanilla js", "JavaScript", "alias"),
    ("ecmascript", "JavaScript", "alias"),
    ("neural networks", "Deep Learning", "alias"),
    ("supervised learning", "Machine Learning", "alias"),
    ("psql", "PostgreSQL", "abbreviation"),
    ("bigquery", "Google Cloud Platform", "alias"),

    # 41-50: Programming, Data, Cloud & Framework Terminology
    ("FastAPI", "FastAPI", "exact"),
    ("fastapi", "FastAPI", "exact"),
    ("Docker", "Docker & Containerization", "exact"),
    ("docker", "Docker & Containerization", "exact"),
    ("SQL", "SQL", "exact"),
    ("sql", "SQL", "exact"),
    ("Pandas", "Pandas", "exact"),
    ("pandas", "Pandas", "exact"),
    ("NumPy", "NumPy", "exact"),
    ("dsa", "Problem Solving & Algorithms", "abbreviation"),
    ("power bi", "Power BI", "exact"),
    ("Power-BI", "Power BI", "punctuation_normalized"),
]


@pytest.mark.parametrize("raw_term,expected_canonical_name,expected_method", NORMALIZATION_CASES_50)
def test_50_normalization_cases(raw_term, expected_canonical_name, expected_method):
    result = normalizer.normalize(raw_term)

    assert result is not None
    assert result.is_resolved is True, f"Failed to resolve '{raw_term}'"
    assert result.canonical_name == expected_canonical_name, (
        f"'{raw_term}' normalized to '{result.canonical_name}', expected '{expected_canonical_name}'"
    )
    assert result.confidence >= 0.85, f"Confidence too low for '{raw_term}': {result.confidence}"
    assert bool(result) is True, f"Boolean check on resolved result must be True"


# ==============================================================================
# 2. DIFFICULT ABBREVIATION DEDICATED TESTS
# ==============================================================================

def test_difficult_abbreviations_explicitly():
    """Verify specifically mandated difficult cases from specification."""
    spec_cases = {
        "JS": "JavaScript",
        "TS": "TypeScript",
        "ML": "Machine Learning",
        "DL": "Deep Learning",
        "NLP": "Natural Language Processing",
        "AWS": "Amazon Web Services",
        "GCP": "Google Cloud Platform",
        "Postgres": "PostgreSQL",
        "PyTorch": "PyTorch",
    }
    for abbr, target_name in spec_cases.items():
        res = normalizer.normalize(abbr)
        assert res.is_resolved is True, f"Failed to normalize {abbr}"
        assert res.canonical_name == target_name, f"Expected {target_name}, got {res.canonical_name}"
        assert res.confidence >= 0.95


# ==============================================================================
# 3. FUZZY MATCHING WITH CONFIDENCE SCORES FOR TYPOS
# ==============================================================================

def test_fuzzy_matching_misspellings_with_confidence_scores():
    """Verify fuzzy matching handles realistic typos with appropriate confidence metrics."""
    fuzzy_tests = [
        ("javascrip", "JavaScript"),
        ("typescrip", "TypeScript"),
        ("postgreql", "PostgreSQL"),
        ("pytorh", "PyTorch"),
        ("dockr", "Docker & Containerization"),
        ("scikitlern", "Scikit-Learn"),
        ("tensrflow", "TensorFlow & Keras"),
        ("kuberenetes", "Kubernetes (K8s)"),
    ]
    for typo, expected in fuzzy_tests:
        res = normalizer.normalize(typo)
        assert res.is_resolved is True, f"Fuzzy match failed for typo '{typo}'"
        assert res.canonical_name == expected
        assert 0.80 <= res.confidence < 1.0, f"Expected confidence in [0.80, 1.0) for '{typo}', got {res.confidence}"
        assert "fuzzy" in res.match_method


# ==============================================================================
# 4. DETERMINISTIC SEMANTIC PHRASE MATCHING
# ==============================================================================

def test_semantic_phrase_containment_matching():
    """Verify multi-word technical descriptions map semantically."""
    semantic_tests = [
        ("Amazon Web Services Cloud Infrastructure", "Amazon Web Services"),
        ("Google Cloud Platform Distributed Systems", "Google Cloud Platform"),
        ("PostgreSQL Relational Database Administration", "PostgreSQL"),
    ]
    for phrase, expected in semantic_tests:
        res = normalizer.normalize(phrase)
        assert res.is_resolved is True, f"Semantic match failed for '{phrase}'"
        assert res.canonical_name == expected
        assert res.confidence >= 0.80
        assert res.match_method in ["semantic", "punctuation_normalized", "alias"]


# ==============================================================================
# 5. UNKNOWN AND AMBIGUOUS SKILLS PRESERVED AS UNRESOLVED
# ==============================================================================

def test_unknown_skills_preserved_as_unresolved():
    """Verify unknown or low-confidence terms are NOT silently mapped."""
    unknown_samples = [
        "Underwater Basket Weaving",
        "Quantum Cooking",
        "Corporate Politics",
        "xyzqwe123fake",
        "random gibberish non-skill text",
        "",
        "   ",
        "ab",  # Too short for fuzzy
        "xy",
    ]
    for unk in unknown_samples:
        res = normalizer.normalize(unk)
        assert isinstance(res, NormalizationResult)
        assert res.is_resolved is False, f"Expected '{unk}' to be unresolved, got {res.canonical_name}"
        assert res.canonical_name is None
        assert res.canonical_id is None
        assert res.confidence == 0.0
        assert res.match_method == "unresolved"
        assert bool(res) is False, "Unresolved result must evaluate to False in boolean context"


# ==============================================================================
# 6. CANONICAL SKILL SYSTEM METADATA VERIFICATION
# ==============================================================================

def test_canonical_skill_definition_fields():
    """Verify each canonical skill satisfies schema: id, name, category, aliases, related_skills, description, importance."""
    all_skills = taxonomy.get_all_skills()
    assert len(all_skills) >= 30, f"Expected >= 30 skills in taxonomy, got {len(all_skills)}"

    for skill in all_skills:
        assert skill.id and isinstance(skill.id, str)
        assert skill.name and isinstance(skill.name, str)
        assert skill.category and isinstance(skill.category, str)
        assert isinstance(skill.aliases, list)
        assert isinstance(skill.related_skills, list), f"Skill {skill.id} missing related_skills"
        assert isinstance(skill.description, str)
        assert skill.importance_weight > 0.0
        assert skill.importance > 0.0

        # Verify normalizer resolves canonical ID
        res = normalizer.normalize(skill.id)
        assert res.is_resolved is True
        assert res.canonical_id == skill.id
        assert len(res.related_skills) >= 0
        assert res.importance > 0.0
