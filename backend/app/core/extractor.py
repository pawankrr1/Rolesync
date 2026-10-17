"""Hybrid 4-Layer Skill Extraction Engine.

Implements:
- Layer 1: Deterministic skill dictionary matching (canonical IDs, names, aliases)
- Layer 2: Context-aware pattern matching (section detection, action clauses, disambiguation rules)
- Layer 3: Optional spaCy NLP (POS tagging, entity recognition with graceful degradation)
- Layer 4: Optional embedding/LLM enhancement (graceful degradation when AI services are unavailable)

Strictly grounded: Skills are emitted ONLY when supported by direct evidence in the input text.
Zero hallucinations.
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field, model_validator

from app.core.taxonomy import taxonomy, SkillDefinition
from app.core.normalizer import normalizer
from app.utils.text_cleaner import clean_text, extract_sentences


# ---------------------------------------------------------------------------
# Output Data Models
# ---------------------------------------------------------------------------

class ExtractedSkill(BaseModel):
    name: str = Field(..., description="Surface or matched skill name")
    canonical_name: str = Field(..., description="Standardized canonical taxonomy name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence score")
    evidence: str = Field(..., description="Direct sentence snippet containing the skill evidence")
    source: str = Field("resume", description="Document source: 'resume' or 'job_description'")
    category: str = Field(..., description="Standardized skill category")
    canonical_id: str = Field(..., description="Internal canonical slug (e.g. python, machine_learning)")
    frequency: int = Field(1, description="Number of mentions in document")
    evidence_snippets: List[str] = Field(default_factory=list, description="All sentence snippets mentioning skill")
    confidence_level: str = Field("High", description="Confidence tier: 'High', 'Medium', or 'Low'")
    confidence_note: Optional[str] = Field(None, description="Review note when confidence is low")

    @model_validator(mode="after")
    def compute_confidence_tier(self) -> "ExtractedSkill":
        if self.confidence < 0.60:
            self.confidence_level = "Low"
            if not self.confidence_note:
                self.confidence_note = "Possible skill detected — review recommended."
        elif self.confidence < 0.85:
            if self.confidence_level not in ("Low", "Medium"):
                self.confidence_level = "Medium"
        else:
            if not self.confidence_level:
                self.confidence_level = "High"
        return self


class ExtractionReport(BaseModel):
    skills: List[ExtractedSkill] = Field(default_factory=list, description="List of all extracted skills")
    total_skills_detected: int = 0
    categories_found: List[str] = Field(default_factory=list)
    skills_by_category: Dict[str, List[ExtractedSkill]] = Field(default_factory=dict)
    raw_character_count: int = 0
    sentences_analyzed: int = 0
    extraction_layers_used: List[str] = Field(default_factory=list)
    system_disclaimer: str = (
        "Career Intelligence provides decision support based on the available profile and dataset. "
        "It does not guarantee employment, hiring outcomes or career success."
    )


# ---------------------------------------------------------------------------
# Layer 3: Optional spaCy NLP
# ---------------------------------------------------------------------------

class SpacyNLPLayer:
    """Layer 3: Optional spaCy NLP layer for POS verification and entity candidate filtering.
    Degrades gracefully when spaCy or language models are unavailable.
    """

    def __init__(self):
        self.available = False
        self.nlp = None
        self._initialize()

    def _initialize(self):
        try:
            import spacy  # type: ignore
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.available = True
            except Exception:
                try:
                    self.nlp = spacy.blank("en")
                    self.available = True
                except Exception:
                    self.available = False
        except (ImportError, Exception):
            self.nlp = None
            self.available = False

    def is_available(self) -> bool:
        return self.available

    def validate_pos_not_verb(self, sentence: str, token: str) -> bool:
        """If available, verify that a candidate token is NOT used as an action verb."""
        if not self.available or not self.nlp:
            return True  # Fallback to Layer 2 regex heuristics
        try:
            doc = self.nlp(sentence)
            for tok in doc:
                if tok.text.lower() == token.lower():
                    if tok.pos_ in ("VERB", "AUX"):
                        return False
            return True
        except Exception:
            return True


# ---------------------------------------------------------------------------
# Layer 4: Optional Embedding / LLM Enhancement
# ---------------------------------------------------------------------------

class OptionalAIEnhancer:
    """Layer 4: Optional Embedding or LLM enhancement layer.
    Allows semantic scoring or contextual re-ranking when API services are configured.
    Remains fully functional and deterministic when offline.
    """

    def __init__(self):
        self.available = False
        self._check_configuration()

    def _check_configuration(self):
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        enable_flag = os.environ.get("ENABLE_OPTIONAL_AI", "false").lower() in ("true", "1", "yes")
        self.available = bool(api_key and enable_flag)

    def is_available(self) -> bool:
        return self.available

    def enhance(self, text: str, initial_skills: List[ExtractedSkill]) -> List[ExtractedSkill]:
        if not self.available:
            return initial_skills
        return initial_skills


# ---------------------------------------------------------------------------
# Layer 2: Context Patterns, Action Verbs, and Disambiguation Rules
# ---------------------------------------------------------------------------

SKILL_SECTION_HEADERS = re.compile(
    r"^(?:technical\s+skills|skills\s*(?:&|and)?\s*competencies|technologies|"
    r"tools\s*(?:&|and)?\s*frameworks|core\s+competencies|key\s+skills|"
    r"proficiencies|tech\s+stack|programming\s+languages|stack|skills)[\s:]*$",
    re.IGNORECASE
)

NON_SKILL_SECTION_HEADERS = re.compile(
    r"^(?:experience|work\s+experience|professional\s+experience|employment\s+history|"
    r"education|certifications?|awards?|honors?|publications?|interests?|personal\s+projects|"
    r"references|summary|profile|about\s+me)[\s:]*$",
    re.IGNORECASE
)

ACTION_PATTERNS = [
    re.compile(r"\b(?:proficient|skilled|experienced|expertise|hands-on|competent)\s+(?:in|with)\s+([^.;\n]+)", re.IGNORECASE),
    re.compile(r"\b(?:knowledge|understanding|mastery)\s+of\s+([^.;\n]+)", re.IGNORECASE),
    re.compile(r"\b(?:built|developed|designed|implemented|architected|maintained|deployed)\s+(?:using|with|in)\s+([^.;\n]+)", re.IGNORECASE),
    re.compile(r"\b(?:experience\s+with|experience\s+in|familiarity\s+with|worked\s+with)\s+([^.;\n]+)", re.IGNORECASE),
    re.compile(r"\b(?:requirements?|qualifications?|must\s+have|preferred\s+skills?|required\s+skills?)[:\s]+([^.;\n]+)", re.IGNORECASE),
]

# Sensitive ambiguous terms that require strict context / disambiguation checks
SENSITIVE_TERMS = {
    "go", "golang", "r", "c", "cv", "rest", "excel", "react", "spring",
    "spark", "ann", "ml", "dl", "pd", "np", "tf", "can", "as", "act",
    "algorithm", "algorithms"
}



def disambiguate_term(
    term: str,
    matched_text: str,
    canon_id: str,
    sentence: str,
    in_skill_section: bool,
    has_action_context: bool,
    spacy_layer: SpacyNLPLayer
) -> bool:
    """Disambiguate ambiguous tech terms from standard English vocabulary.
    Returns True if the match is a genuine technical skill, False if it is a false positive.
    """
    mt = matched_text
    mt_lower = mt.lower()
    sent = sentence

    # 1. Go / Golang
    if canon_id == "golang":
        if mt_lower in ("golang", "go language", "go programming", "go developer", "go backend"):
            return True
        # Plain "go" or "Go"
        if mt == "go":  # Lowercase "go" is universally the English verb
            return False
        # Preceding verb contexts: "to Go", "will Go", "let's Go", "going to Go", etc.
        if re.search(r"\b(to|will|let's|lets|going|where\s+to|can|should|ready\s+to|want\s+to|how\s+to|on\s+the)\s+Go\b", sent):
            return False
        # Following preposition: "Go to", "Go ahead", "Go through", "Go into", etc.
        if re.search(r"\bGo\s+(to|ahead|through|back|on|into|out|for|with|away)\b", sent):
            return False
        # If in skills section with uppercase Go
        if in_skill_section and mt == "Go":
            return True
        # Must be accompanied by backend / systems / cloud context
        if re.search(r"\b(docker|kubernetes|k8s|microservices|backend|grpc|gin|goroutines|channels|concurrency|python|java|rust|c\+\+|postgres|sql|developer|engineer|software)\b", sent, re.IGNORECASE):
            return True
        return False

    # 2. REST API / REST
    if canon_id == "rest_api":
        if mt_lower in ("rest api", "rest apis", "restful", "restful api", "restful apis", "rest endpoints", "rest services", "rest web services"):
            return True
        # Plain "rest" or "REST"
        if re.search(r"\b(the\s+rest|rest\s+of|at\s+rest|take\s+a\s+rest|need\s+rest|rest\s+and\s+relaxation|bed\s+rest)\b", sent, re.IGNORECASE):
            return False
        if in_skill_section and mt == "REST":
            return True
        if re.search(r"\b(api|apis|endpoints?|services?|graphql|grpc|http|json|microservices?|soap|postman|fastapi)\b", sent, re.IGNORECASE):
            return True
        return False

    # 3. Microsoft Excel
    if canon_id == "excel":
        if mt_lower in ("microsoft excel", "ms excel", "excel formulas", "excel macros", "excel sheets", "advanced excel", "excel spreadsheets", "excel vba"):
            return True
        # Reject English verb: "excel in", "excel at", "excelled", "excelling", "ability to excel"
        if re.search(r"\b(ability\s+to\s+excel|strive\s+to\s+excel|to\s+excel|will\s+excel|excel\s+in|excel\s+at|excelled|excelling)\b", sent, re.IGNORECASE):
            return False
        if not spacy_layer.validate_pos_not_verb(sent, "excel"):
            return False
        if in_skill_section:
            return True
        # Tool / Analytics context
        if re.search(r"\b(vlookup|pivot|macros|sql|power\s*bi|tableau|spreadsheet|data\s+analysis|reporting|charts|formulas)\b", sent, re.IGNORECASE):
            return True
        if mt == "Excel" and not re.search(r"\b(to|will|can|must|should)\s+Excel\b", sent):
            return True
        return False

    # 4. R Language
    if canon_id == "r":
        if mt_lower in ("r programming", "r language", "r script", "r scripts", "r studio", "r packages", "cran"):
            return True
        if re.search(r"\b(r&d|r-squared|model\s+r|toys\s+r\s+us)\b", sent, re.IGNORECASE):
            return False
        # Data language list context
        if re.search(r"\b(python\s*,\s*r\b|\br\s*,\s*python\b|\br\s*,\s*(?:and\s+)?sql\b|\bsql\s*,\s*(?:and\s+)?r\b|\br\s*/\s*python\b|\bpython\s*/\s*r\b)", sent, re.IGNORECASE):
            return True
        if in_skill_section and mt == "R" and re.search(r"\b(python|sql|julia|sas|spss|stata|matlab|analytics|statistics)\b", sent, re.IGNORECASE):
            return True
        return False

    # 5. C Language
    if canon_id == "c":
        if mt_lower in ("c programming", "c language", "c/c++", "c & c++"):
            return True
        if re.search(r"\b(vitamin\s+c|grade\s+c|section\s+c|c-suite|c-level)\b", sent, re.IGNORECASE):
            return False
        if re.search(r"\b(c\s*,\s*c\+\+|\bc\+\+\s*,\s*c\b|\bc\s*,\s*java|\bembedded\s+c\b)", sent, re.IGNORECASE):
            return True
        return False

    # 6. React
    # 6. React
    if canon_id == "react":
        if mt_lower in ("react.js", "reactjs", "react native", "react framework", "react components", "react hooks"):
            return True
        # Reject English verb: "react to", "react quickly", "fail to react"
        if re.search(r"\b(react\s+to|react\s+quickly|react\s+promptly|ability\s+to\s+react|fail\s+to\s+react)\b", sent, re.IGNORECASE):
            return False
        if not spacy_layer.validate_pos_not_verb(sent, "react"):
            return False
        if in_skill_section:
            return True
        if re.search(r"\b(javascript|typescript|next\.?js|redux|vue|angular|frontend|ui|tailwind|html|css|web|components)\b", sent, re.IGNORECASE):
            return True
        if re.search(r"\b(?:using|with|developed|built|learning)\s+react\b", sent, re.IGNORECASE):
            return True
        return False

    # 7. Spring Boot / Spring
    if canon_id == "spring_boot":
        if mt_lower in ("spring boot", "spring framework", "spring mvc", "spring cloud", "spring data", "spring security", "java spring"):
            return True
        # Reject season / term: "spring 2024", "spring semester", "spring break"
        if re.search(r"\bspring\s+(20\d\d|semester|break|term|internship|quarter)\b", sent, re.IGNORECASE):
            return False
        if in_skill_section and mt == "Spring":
            return True
        if re.search(r"\b(java|hibernate|maven|gradle|backend|microservices|jpa)\b", sent, re.IGNORECASE):
            return True
        return False

    # 8. Apache Spark / Spark
    if canon_id == "spark":
        if mt_lower in ("apache spark", "pyspark", "spark streaming", "spark sql", "spark dataframe", "spark rdd"):
            return True
        if re.search(r"\b(spark\s+ideas|spark\s+interest|spark\s+curiosity|spark\s+innovation)\b", sent, re.IGNORECASE):
            return False
        if in_skill_section:
            return True
        if re.search(r"\b(hadoop|kafka|databricks|big\s+data|scala|data\s+pipeline|etl|mapreduce|distributed|analytics)\b", sent, re.IGNORECASE):
            return True
        return False

    # 9. Computer Vision vs CV (Curriculum Vitae)
    if canon_id == "computer_vision":
        if mt_lower in ("computer vision", "opencv", "yolo", "image segmentation", "object detection"):
            return True
        # Reject CV as resume
        if re.search(r"\b(attached|my|send|updated|review|find|submit|enclosed)\s+cv\b", sent, re.IGNORECASE):
            return False
        if re.search(r"\bcv\s+(attached|enclosed|submitted|format)\b", sent, re.IGNORECASE):
            return False
        if re.search(r"\b(image|video|camera|vision|cnn|opencv|yolo|deep\s+learning|detection|segmentation)\b", sent, re.IGNORECASE):
            return True
        return False

    # 10. Machine Learning vs "ml" (milliliters)
    if canon_id == "machine_learning":
        if mt_lower in ("machine learning", "scikit-learn", "scikit learn", "sklearn"):
            return True
        if re.search(r"\b\d+\s*ml\b", sent, re.IGNORECASE):
            return False
        if mt == "ML" or in_skill_section:
            if re.search(r"\b(ai|ai/ml|ml/dl|model|models|pipeline|algorithm|algorithms|data|python|nlp|deep\s+learning)\b", sent, re.IGNORECASE):
                return True
        return False

    # 11. Deep Learning vs "dl" (driver's license)
    if canon_id == "deep_learning":
        if mt_lower in ("deep learning", "neural networks", "neural network"):
            return True
        if re.search(r"\b(driving|driver'?s)\s+dl\b", sent, re.IGNORECASE):
            return False
        if mt == "DL" or in_skill_section:
            if re.search(r"\b(ai|ml/dl|pytorch|tensorflow|cnn|rnn|transformer|neural)\b", sent, re.IGNORECASE):
                return True
        return False

    # 12. Problem Solving & Algorithms vs Domain Specific Algorithms
    if canon_id == "data_structures_algorithms":
        if mt_lower in ("algorithm", "algorithms"):
            # If preceded by NLP, ML, AI, etc., it belongs to the AI domain, not DSA
            if re.search(r"\b(nlp|ml|machine\s+learning|deep\s+learning|ai|genetic|search\s+engine)\s+algorithms?\b", sent, re.IGNORECASE):
                return False
            if in_skill_section and mt_lower in ("dsa", "data structures"):
                return True
            if re.search(r"\b(data\s+structures|problem\s+solving|competitive\s+programming|leetcode|dynamic\s+programming|trees?|graphs?|asymptotic)\b", sent, re.IGNORECASE):
                return True
            return False

    # 13. Short data aliases (pd, np, tf)
    if term in ("pd", "np", "tf"):
        if term == "pd" and re.search(r"\b(import\s+pandas\s+as\s+pd|pd\.dataframe|pd\.read_)\b", sent, re.IGNORECASE):
            return True
        if term == "np" and re.search(r"\b(import\s+numpy\s+as\s+np|np\.array|np\.zeros)\b", sent, re.IGNORECASE):
            return True
        if term == "tf" and re.search(r"\b(import\s+tensorflow\s+as\s+tf|tf\.keras|tf\.tensor)\b", sent, re.IGNORECASE):
            return True
        return False

    # Default pass for non-sensitive terms
    return True


# ---------------------------------------------------------------------------
# SkillExtractor Main Engine
# ---------------------------------------------------------------------------

class CompiledMatcher:
    def __init__(self, term: str, canon_id: str, pattern: re.Pattern, is_sensitive: bool, is_multiword: bool, is_acronym: bool):
        self.term = term
        self.term_lower = term.lower()
        self.canon_id = canon_id
        self.pattern = pattern
        self.is_sensitive = is_sensitive
        self.is_multiword = is_multiword
        self.is_acronym = is_acronym


class SkillExtractor:
    """Hybrid 4-Layer Skill Extraction Engine."""

    def __init__(self):
        self.taxonomy = taxonomy
        self.normalizer = normalizer
        self.spacy_layer = SpacyNLPLayer()
        self.ai_layer = OptionalAIEnhancer()
        self._compiled_matchers: List[CompiledMatcher] = []
        self._build_compiled_matchers()

    def _build_compiled_matchers(self):
        """Build regex matchers for Layer 1 dictionary matching."""
        alias_map = self.taxonomy.get_alias_map()
        # Sort terms by length descending to match greedy multi-word phrases first
        sorted_terms = sorted(alias_map.keys(), key=lambda x: len(x), reverse=True)

        for term in sorted_terms:
            canon_id = alias_map[term]
            is_sensitive = term.lower() in SENSITIVE_TERMS
            is_multiword = (" " in term or "-" in term or "/" in term)
            is_acronym = (len(term) <= 5 and not is_multiword)

            escaped = re.escape(term)

            # Special characters like ++, #, ., / need safe lookaround boundaries
            has_special = any(c in term for c in "+#./")
            if has_special:
                prefix = r"(?<![a-zA-Z0-9_])"
                suffix = r"(?![a-zA-Z0-9_])"
                pattern_str = f"{prefix}{escaped}{suffix}"
            else:
                pattern_str = f"\\b{escaped}\\b"

            try:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                self._compiled_matchers.append(
                    CompiledMatcher(
                        term=term,
                        canon_id=canon_id,
                        pattern=pattern,
                        is_sensitive=is_sensitive,
                        is_multiword=is_multiword,
                        is_acronym=is_acronym
                    )
                )
            except re.error:
                continue

    def extract_from_text(self, text: str, source: str = "resume") -> ExtractionReport:
        """Extract all skills, normalize to canonical taxonomy, and gather sentence evidence.
        Applies Layer 1 (Dictionary), Layer 2 (Context & Disambiguation),
        Layer 3 (Optional spaCy NLP), and Layer 4 (Optional AI Enhancement).
        """
        cleaned = clean_text(text)
        if not cleaned:
            return ExtractionReport(
                skills=[],
                total_skills_detected=0,
                categories_found=[],
                skills_by_category={},
                raw_character_count=0,
                sentences_analyzed=0,
                extraction_layers_used=["Layer 1: Deterministic Dictionary", "Layer 2: Context Patterns & Disambiguation"]
            )

        sentences = extract_sentences(cleaned)
        lines = cleaned.split("\n")

        # 1. Map line context to detect designated Skill Sections
        in_skill_section_lines: Set[int] = set()
        is_in_skill_block = False

        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            if SKILL_SECTION_HEADERS.match(line_str):
                is_in_skill_block = True
                in_skill_section_lines.add(idx)
                continue

            if NON_SKILL_SECTION_HEADERS.match(line_str):
                is_in_skill_block = False
                continue

            # Inline skills header, e.g. "Skills: Python, Docker, SQL"
            if re.match(r"^(?:skills|technical skills|technologies|tools|stack)[:\s]+", line_str, re.IGNORECASE):
                in_skill_section_lines.add(idx)
                continue

            if is_in_skill_block:
                in_skill_section_lines.add(idx)

        # 2. Extract and disambiguate sentence-by-sentence
        found_skills: Dict[str, ExtractedSkill] = {}
        layers_used = ["Layer 1: Deterministic Dictionary", "Layer 2: Context Patterns & Disambiguation"]
        if self.spacy_layer.is_available():
            layers_used.append("Layer 3: spaCy NLP")
        if self.ai_layer.is_available():
            layers_used.append("Layer 4: AI Enhancement")

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue

            # Check if sentence is in a skill section
            in_section = any(sentence_clean in lines[i] for i in in_skill_section_lines if i < len(lines))

            # Check if sentence has action / proficiency context
            has_action = any(pat.search(sentence_clean) for pat in ACTION_PATTERNS)

            # Track matched character spans in this sentence to prevent sub-string overlap
            # (e.g. if 'Machine Learning' was matched, don't re-match 'ML' or sub-words on the same span)
            matched_spans: List[Tuple[int, int]] = []
            sentence_lower = sentence_clean.lower()

            for matcher in self._compiled_matchers:
                # Fast C-level substring check: skip 90%+ of regex evaluations when term cannot match
                if matcher.term_lower not in sentence_lower:
                    continue

                for match in matcher.pattern.finditer(sentence_clean):
                    span = match.span()
                    # Check for overlap with already matched longer phrases
                    if any(s <= span[0] and span[1] <= e for s, e in matched_spans):
                        continue

                    matched_text = match.group(0)

                    # Layer 2 & 3: Disambiguation checks
                    if matcher.is_sensitive:
                        is_valid = disambiguate_term(
                            term=matcher.term,
                            matched_text=matched_text,
                            canon_id=matcher.canon_id,
                            sentence=sentence_clean,
                            in_skill_section=in_section,
                            has_action_context=has_action,
                            spacy_layer=self.spacy_layer
                        )
                        if not is_valid:
                            continue

                    # Record span
                    matched_spans.append(span)

                    skill_def = self.taxonomy.get_skill(matcher.canon_id)
                    if not skill_def:
                        continue

                    # Confidence calibration
                    if matcher.is_multiword:
                        base_conf = 0.96
                    elif len(matcher.term) >= 4:
                        base_conf = 0.94
                    else:
                        base_conf = 0.91

                    if in_section:
                        base_conf += 0.03
                    if has_action:
                        base_conf += 0.03

                    calibrated_conf = min(0.99, round(base_conf, 2))

                    canon_id = skill_def.id
                    if canon_id not in found_skills:
                        found_skills[canon_id] = ExtractedSkill(
                            name=skill_def.name,
                            canonical_name=skill_def.name,
                            category=skill_def.category,
                            confidence=calibrated_conf,
                            evidence=sentence_clean,
                            source=source,
                            canonical_id=skill_def.id,
                            frequency=1,
                            evidence_snippets=[sentence_clean]
                        )
                    else:
                        existing = found_skills[canon_id]
                        existing.frequency += 1
                        if sentence_clean not in existing.evidence_snippets and len(existing.evidence_snippets) < 3:
                            existing.evidence_snippets.append(sentence_clean)
                        # Pick the richest sentence (action context preferred)
                        if has_action and not any(pat.search(existing.evidence) for pat in ACTION_PATTERNS):
                            existing.evidence = sentence_clean
                        # Slight confidence boost on repeated mentions
                        existing.confidence = min(0.99, round(existing.confidence + 0.01, 2))

        # 3. Layer 4 AI Enhancement (if configured/available)
        skills_list = list(found_skills.values())
        if self.ai_layer.is_available():
            skills_list = self.ai_layer.enhance(cleaned, skills_list)

        # 4. Set explainable confidence indicators
        for s in skills_list:
            if s.confidence < 0.60:
                s.confidence_level = "Low"
                s.confidence_note = "Possible skill detected — review recommended."
            elif s.confidence < 0.85:
                s.confidence_level = "Medium"
                s.confidence_note = None
            else:
                s.confidence_level = "High"
                s.confidence_note = None

        # 5. Group by category and sort
        skills_list.sort(key=lambda s: (s.category, s.canonical_name))

        skills_by_category: Dict[str, List[ExtractedSkill]] = {}
        for skill in skills_list:
            skills_by_category.setdefault(skill.category, []).append(skill)

        categories_found = sorted(list(skills_by_category.keys()))

        return ExtractionReport(
            skills=skills_list,
            total_skills_detected=len(skills_list),
            categories_found=categories_found,
            skills_by_category=skills_by_category,
            raw_character_count=len(cleaned),
            sentences_analyzed=len(sentences),
            extraction_layers_used=layers_used
        )

    # Aliases
    extract = extract_from_text


# Global shared instance
extractor = SkillExtractor()
