import re
from typing import Optional, List, Tuple
from ai.schemas import WordExplanationAI, ExampleSetAI, ConversationalExampleAI

# Generic definition patterns that indicate low-quality template generation
GENERIC_DEFINITION_PATTERNS = [
    r"characterized by or exhibiting the qualities and nature of",
    r"the state, quality, concept, or condition associated with",
    r"in a manner characterized by",
    r"to demonstrate, carry out, or engage in the action of",
    r"a core english term used to express",
    r"general meaning, usage, and definition",
    r"concept or condition associated with",
    r"qualities and nature of",
]

GENERIC_USAGE_PATTERNS = [
    r"used in professional, academic, and daily communication when expressing ideas involving",
    r"used in everyday or professional communication when expressing concepts related to",
    r"when expressing ideas involving",
    r"expressing concepts related to",
]

GENERIC_COLLOCATION_PATTERNS = [
    r"^highly\s+",
    r"^truly\s+",
    r"\s+approach$",
    r"\s+impact$",
    r"^experience\s+",
    r"^sense of\s+",
    r"^understand\s+",
    r"^use\s+['\"]",
]

GENERIC_EXAMPLE_PATTERNS = [
    r"impacts our project roadmap and key deliverables",
    r"important consideration for the upcoming quarter",
    r"approach .* in collaborative environments",
    r"analyzed the concept of .* through real-world case studies",
    r"conversation about how to handle .* with empathy and patience",
    r"ensure there was no confusion regarding",
    r"different cultures perceive and respond to",
    r"plan to address .* moving forward",
    r"helps develop stronger communication and self-awareness",
    r"applied to our current workflow",
    r"used the word",
    r"into daily conversations helps build confidence in english",
]


def is_circular_or_generic_definition(word: str, definition: Optional[str]) -> bool:
    """Detect if a definition is circular or matches known generic fallback templates."""
    if not definition or len(definition.strip()) < 10:
        return True

    clean_def = definition.strip().lower()
    clean_word = word.strip().lower()

    # Check for known boilerplate templates
    for pattern in GENERIC_DEFINITION_PATTERNS:
        if re.search(pattern, clean_def):
            return True

    # Check for circular definition: e.g. "nature of 'frivolous'" or "concept of 'behavior'"
    circular_patterns = [
        rf"nature of ['\"]?{re.escape(clean_word)}['\"]?",
        rf"associated with ['\"]?{re.escape(clean_word)}['\"]?",
        rf"concept of ['\"]?{re.escape(clean_word)}['\"]?",
        rf"action of ['\"]?{re.escape(clean_word)}['\"]?",
        rf"state of being ['\"]?{re.escape(clean_word)}['\"]?",
    ]
    for cp in circular_patterns:
        if re.search(cp, clean_def):
            return True

    return False


def is_generic_contextual_meaning(word: str, contextual_meaning: Optional[str]) -> bool:
    """Detect if contextual usage description is generic boilerplate."""
    if not contextual_meaning or len(contextual_meaning.strip()) < 10:
        return True

    clean_usage = contextual_meaning.strip().lower()
    clean_word = word.strip().lower()

    for pattern in GENERIC_USAGE_PATTERNS:
        if re.search(pattern, clean_usage):
            return True

    if re.search(rf"ideas involving ['\"]?{re.escape(clean_word)}['\"]?", clean_usage):
        return True

    return False


def has_generic_collocations(word: str, collocations: Optional[List[str]]) -> bool:
    """Detect if collocations are mechanical string-template outputs."""
    if not collocations or len(collocations) == 0:
        return True

    clean_word = word.strip().lower()
    generic_matches = 0

    for col in collocations:
        col_clean = str(col).strip().lower()
        for pattern in GENERIC_COLLOCATION_PATTERNS:
            if re.search(pattern, col_clean):
                generic_matches += 1
                break
        if f"use '{clean_word}'" in col_clean or f"understand '{clean_word}'" in col_clean:
            generic_matches += 1

    return generic_matches >= max(2, len(collocations) // 2)


def has_generic_examples(word: str, examples: Optional[List[ConversationalExampleAI]]) -> bool:
    """Detect if examples are mechanical string-template outputs."""
    if not examples or len(examples) == 0:
        return True

    clean_word = word.strip().lower()
    generic_count = 0

    for ex in examples:
        text = (ex.example_text if hasattr(ex, "example_text") else str(ex)).lower()
        if any(re.search(pat, text) for pat in GENERIC_EXAMPLE_PATTERNS):
            generic_count += 1
        # Check that target word or its root actually appears in the sentence
        stem = clean_word[:-1] if clean_word.endswith("e") or clean_word.endswith("y") else clean_word
        if stem not in text and clean_word not in text:
            generic_count += 1

    return generic_count >= max(2, len(examples) // 3)


def validate_vocabulary_explanation(word: str, explanation: WordExplanationAI) -> Tuple[bool, Optional[str]]:
    """Validate that WordExplanationAI contains genuine, non-generic linguistic data."""
    if is_circular_or_generic_definition(word, explanation.simple_meaning):
        return False, f"Definition for '{word}' is generic or circular."

    if is_generic_contextual_meaning(word, explanation.contextual_meaning):
        return False, f"Contextual meaning for '{word}' is generic boilerplate."

    if explanation.part_of_speech.lower() in ["word", "term", "unknown", ""]:
        return False, f"Invalid part of speech '{explanation.part_of_speech}' for '{word}'."

    if has_generic_collocations(word, explanation.collocations):
        return False, f"Collocations for '{word}' match generic fallback patterns."

    return True, None


def validate_vocabulary_examples(word: str, example_set: ExampleSetAI) -> Tuple[bool, Optional[str]]:
    """Validate that ExampleSetAI contains distinct, natural examples."""
    if not example_set.examples or len(example_set.examples) == 0:
        return False, f"No examples provided for '{word}'."

    if has_generic_examples(word, example_set.examples):
        return False, f"Examples for '{word}' match generic template patterns."

    return True, None
