"""Text preprocessing and sentence-level evidence splitting."""

import re
from typing import List


def clean_text(text: str) -> str:
    """Sanitize and normalize raw text while preserving linguistic boundaries."""
    if not text:
        return ""
    
    # Replace non-breaking spaces and special unicode dashes/quotes
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2022", " • ").replace("\u25cf", " • ").replace("\u25e6", " • ")
    
    # Normalize multiple newlines and spaces
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    
    return text.strip()


def extract_sentences(text: str) -> List[str]:
    """Split text into distinct sentences / bullet lines for evidence extraction."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    
    raw_segments = []
    # Split on newlines, bullet points, or sentence end punctuations
    lines = cleaned.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Split on bullet points if line has multiple
        bullets = re.split(r"\s*[•\*\-]\s+", line)
        for b in bullets:
            b = b.strip()
            if not b:
                continue
            # Further split by sentence-ending punctuation followed by space
            sentence_splits = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", b)
            for s in sentence_splits:
                s = s.strip()
                if len(s) >= 4:
                    raw_segments.append(s)
                    
    return raw_segments
