"""Career Intelligence Skill Normalization Engine.

Maps raw, variant, misspelled, punctuated, and abbreviated skill terms to canonical taxonomy skills using:
1. Exact matching (canonical IDs & canonical names)
2. Alias & synonym resolution
3. Case normalization (UPPERCASE, lowercase, TitleCase, mixed-case)
4. Punctuation normalization (hyphens, underscores, slashes, periods, dots)
5. Abbreviation handling (domain abbreviations: JS, TS, ML, DL, NLP, AWS, GCP, etc.)
6. High-confidence fuzzy matching (RapidFuzz with short-token guard and strict threshold)
7. Deterministic semantic token overlap & phrase containment matching

Preserves unknown terms as unresolved with confidence=0.0 and is_resolved=False.
Does not silently map ambiguous low-confidence terms.
Works 100% offline without external network or LLM dependencies.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field
from rapidfuzz import fuzz, process

from app.core.taxonomy import taxonomy, SkillDefinition


class NormalizationResult(BaseModel):
    """Structured result of a skill normalization operation."""
    raw_term: str
    is_resolved: bool = Field(True, description="Whether the term mapped to a canonical skill")
    canonical_id: Optional[str] = Field(None, description="Standardized slug ID (e.g. 'machine_learning')")
    canonical_name: Optional[str] = Field(None, description="Human-readable canonical name (e.g. 'Machine Learning')")
    category: Optional[str] = Field(None, description="Standardized category domain")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Match confidence score between 0.0 and 1.0")
    match_method: str = Field("exact", description="Method used: exact, alias, abbreviation, case_normalized, punctuation_normalized, fuzzy, semantic, unresolved")
    related_skills: List[str] = Field(default_factory=list, description="IDs of adjacent/related skills")
    description: Optional[str] = Field(None, description="Skill summary definition")
    importance: float = Field(1.0, description="Importance weighting metadata")

    def __bool__(self) -> bool:
        """Allow natural boolean checks: if result: ..."""
        return self.is_resolved


# High-confidence domain abbreviation mappings
ABBREVIATIONS: Dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine_learning",
    "dl": "deep_learning",
    "nlp": "nlp",
    "aws": "aws",
    "gcp": "gcp",
    "postgres": "postgresql",
    "psql": "postgresql",
    "pgsql": "postgresql",
    "pytorch": "pytorch",
    "torch": "pytorch",
    "tf": "tensorflow",
    "k8s": "kubernetes",
    "dsa": "data_structures_algorithms",
    "eda": "data_analysis",
    "bi": "power_bi",
    "pbi": "power_bi",
    "iac": "terraform",
    "llm": "llms",
    "llms": "llms",
    "genai": "llms",
    "cv": "computer_vision",
    "owasp": "application_security",
    "iam": "iam_auth",
    "ci/cd": "devops_cicd",
    "cicd": "devops_cicd",
    "py": "python",
}


class SkillNormalizer:
    """Deterministic Multi-Stage Skill Normalizer."""

    def __init__(self, fuzzy_threshold: float = 82.0):
        self.taxonomy = taxonomy
        self.fuzzy_threshold = fuzzy_threshold
        self.abbreviations = ABBREVIATIONS
        self.alias_map: Dict[str, str] = self.taxonomy.get_alias_map()
        self.search_choices: List[str] = list(self.alias_map.keys())
        # Fast O(1) case-normalized lookup
        self._name_to_skill: Dict[str, SkillDefinition] = {
            s.name.lower(): s for s in self.taxonomy._skills.values()
        }
        # Precomputed token sets for semantic overlap matching (avoids repeated regex in loop)
        self._skill_tokens: List[Tuple[SkillDefinition, Set[str]]] = [
            (s, set(re.findall(r"[a-z0-9]+", s.name.lower())))
            for s in self.taxonomy._skills.values()
            if s.name
        ]
        # In-memory normalization cache for high-throughput reuse
        self._cache: Dict[str, NormalizationResult] = {}

    def _clean_punctuation(self, term: str) -> str:
        """Remove punctuation like hyphens, underscores, slashes while preserving spaces."""
        cleaned = re.sub(r"[\-_\/]+", " ", term.lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _strip_web_dots(self, term: str) -> str:
        """Normalize terms ending in or containing dots like React.js, Node.js."""
        cleaned = term.lower().strip()
        # "react.js" -> "react", "node.js" -> "node"
        if cleaned.endswith(".js"):
            cleaned = cleaned[:-3].strip()
        cleaned = re.sub(r"[,\-_/.]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _create_resolved(
        self,
        raw_term: str,
        skill: SkillDefinition,
        confidence: float,
        method: str
    ) -> NormalizationResult:
        """Helper to build a resolved NormalizationResult."""
        res = NormalizationResult(
            raw_term=raw_term,
            is_resolved=True,
            canonical_id=skill.id,
            canonical_name=skill.name,
            category=skill.category,
            confidence=round(confidence, 2),
            match_method=method,
            related_skills=skill.related_skills or skill.adjacent_skills,
            description=skill.description,
            importance=skill.importance_weight,
        )
        if len(self._cache) < 8192:
            self._cache[raw_term] = res
        return res

    def _create_unresolved(self, raw_term: str) -> NormalizationResult:
        """Helper to build an unresolved NormalizationResult."""
        res = NormalizationResult(
            raw_term=raw_term,
            is_resolved=False,
            canonical_id=None,
            canonical_name=None,
            category=None,
            confidence=0.0,
            match_method="unresolved",
            related_skills=[],
            description=None,
            importance=0.0,
        )
        if len(self._cache) < 8192:
            self._cache[raw_term] = res
        return res

    def normalize(self, raw_term: str) -> NormalizationResult:
        """Normalizes a raw or variant skill string into a canonical skill representation.
        
        Execution pipeline:
        1. Exact canonical ID or Canonical Name matching (case-insensitive)
        2. Abbreviation handling (e.g. JS, TS, ML, DL, NLP, AWS, GCP, Postgres)
        3. Alias & synonym matching
        4. Case normalization
        5. Punctuation & delimiter normalization (hyphens, underscores, slashes, .js)
        6. RapidFuzz similarity matching with strict short-word guard
        7. Semantic token overlap & containment matching
        8. Unresolved preservation
        """
        if not raw_term or not raw_term.strip():
            return self._create_unresolved(raw_term or "")

        # Fast cache lookup for repeated terms
        if raw_term in self._cache:
            return self._cache[raw_term]

        term = raw_term.strip()
        term_lower = term.lower()

        # ----------------------------------------------------------------------
        # 1. Exact canonical ID or Canonical Name match
        # ----------------------------------------------------------------------
        # Exact canonical ID check
        skill = self.taxonomy.get_skill(term_lower)
        if skill and (term_lower == skill.id or term_lower == skill.name.lower()):
            return self._create_resolved(raw_term, skill, 1.0, "exact")

        # ----------------------------------------------------------------------
        # 2. Abbreviation handling
        # ----------------------------------------------------------------------
        # Cleaned abbreviation lookup (strip punctuation)
        clean_abbr = re.sub(r"[.\-_/]", "", term_lower).strip()
        if term_lower in self.abbreviations:
            target_id = self.abbreviations[term_lower]
            skill = self.taxonomy.get_skill(target_id)
            if skill:
                return self._create_resolved(raw_term, skill, 1.0, "abbreviation")
        elif clean_abbr in self.abbreviations:
            target_id = self.abbreviations[clean_abbr]
            skill = self.taxonomy.get_skill(target_id)
            if skill:
                return self._create_resolved(raw_term, skill, 1.0, "abbreviation")

        # ----------------------------------------------------------------------
        # 3. Alias dictionary match
        # ----------------------------------------------------------------------
        if term_lower in self.alias_map:
            canon_id = self.alias_map[term_lower]
            skill = self.taxonomy.get_skill(canon_id)
            if skill:
                is_exact_name = term_lower == skill.name.lower() or term_lower == skill.id
                return self._create_resolved(
                    raw_term,
                    skill,
                    1.0,
                    "exact" if is_exact_name else "alias"
                )

        # ----------------------------------------------------------------------
        # 4. Case normalization check (O(1) dictionary lookup)
        # ----------------------------------------------------------------------
        if term_lower in self._name_to_skill:
            return self._create_resolved(raw_term, self._name_to_skill[term_lower], 1.0, "case_normalized")

        # ----------------------------------------------------------------------
        # 5. Punctuation & Delimiter Normalization
        # ----------------------------------------------------------------------
        # Try replacing hyphens/underscores/slashes with space
        cleaned_punct = self._clean_punctuation(term)
        if cleaned_punct in self.alias_map:
            canon_id = self.alias_map[cleaned_punct]
            skill = self.taxonomy.get_skill(canon_id)
            if skill:
                return self._create_resolved(raw_term, skill, 0.98, "punctuation_normalized")

        # Try stripped dots/web extensions (e.g., "react.js" -> "react")
        stripped_dots = self._strip_web_dots(term)
        if stripped_dots in self.alias_map:
            canon_id = self.alias_map[stripped_dots]
            skill = self.taxonomy.get_skill(canon_id)
            if skill:
                return self._create_resolved(raw_term, skill, 0.98, "punctuation_normalized")

        # ----------------------------------------------------------------------
        # 6. Fuzzy matching with strict guards
        # ----------------------------------------------------------------------
        # Short token guard: never fuzzy match tokens <= 2 chars (e.g. 'c', 'r', 'go', 'js')
        if len(term_lower) >= 3:
            best_match = process.extractOne(
                term_lower,
                self.search_choices,
                scorer=fuzz.ratio,
                score_cutoff=self.fuzzy_threshold,
            )
            if best_match:
                matched_key, score, _ = best_match
                # Extra guard: Do not match if the length difference is too extreme
                if abs(len(matched_key) - len(term_lower)) <= 4:
                    canon_id = self.alias_map[matched_key]
                    skill = self.taxonomy.get_skill(canon_id)
                    if skill:
                        conf = min(0.95, round(float(score) / 100.0, 2))
                        return self._create_resolved(
                            raw_term,
                            skill,
                            conf,
                            f"fuzzy_{int(score)}%"
                        )

            # Try token_sort_ratio for reordered words (e.g. "learning machine")
            if " " in term_lower or "-" in term_lower:
                sort_match = process.extractOne(
                    term_lower,
                    self.search_choices,
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=86.0,
                )
                if sort_match:
                    matched_key, score, _ = sort_match
                    canon_id = self.alias_map[matched_key]
                    skill = self.taxonomy.get_skill(canon_id)
                    if skill:
                        conf = min(0.92, round(float(score) / 100.0, 2))
                        return self._create_resolved(
                            raw_term,
                            skill,
                            conf,
                            f"fuzzy_sort_{int(score)}%"
                        )

        # ----------------------------------------------------------------------
        # 7. Semantic token overlap & phrase containment matching
        # ----------------------------------------------------------------------
        # For multi-word descriptive phrases (e.g. "Amazon Web Services Cloud Infrastructure")
        input_tokens = set(re.findall(r"[a-z0-9]+", term_lower))
        if len(input_tokens) >= 2:
            best_semantic_skill: Optional[SkillDefinition] = None
            best_semantic_overlap = 0.0

            for s_def, name_tokens in self._skill_tokens:
                if not name_tokens:
                    continue

                # If all canonical name tokens are contained in the input
                if name_tokens.issubset(input_tokens):
                    coverage = len(name_tokens) / len(input_tokens)
                    score = 0.75 + (0.20 * coverage)
                    if score > best_semantic_overlap:
                        best_semantic_overlap = score
                        best_semantic_skill = s_def

            if best_semantic_skill and best_semantic_overlap >= 0.80:
                return self._create_resolved(
                    raw_term,
                    best_semantic_skill,
                    round(best_semantic_overlap, 2),
                    "semantic"
                )

        # ----------------------------------------------------------------------
        # 8. Unresolved preservation (low confidence / unknown skills)
        # ----------------------------------------------------------------------
        return self._create_unresolved(raw_term)


# Global singleton instance
normalizer = SkillNormalizer()
