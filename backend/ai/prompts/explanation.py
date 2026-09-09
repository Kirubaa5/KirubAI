EXPLANATION_SYSTEM_PROMPT = """You are a world-class English language teacher and linguistic expert specializing in helping intermediate learners convert passive vocabulary into active, natural communication.
Provide clear, structured explanations with high practical utility."""


def build_explanation_prompt(word: str) -> str:
    return f"""Explain the English word "{word}" for an intermediate English learner (CEFR B1/B2 level).
Provide:
1. simple_meaning: Clear and concise definition.
2. contextual_meaning: Nuances and real-world natural usage.
3. part_of_speech: Grammatical category (verb, noun, adjective, adverb, etc.).
4. pronunciation_text: Easy phonetic representation (e.g., HEZ-ih-tayt).
5. synonyms: 3-5 accurate synonyms.
6. antonyms: 2-4 antonyms.
7. word_forms: Dictionary of standard grammatical variations (noun, verb, adjective, adverb).
8. collocations: 4 common English collocations or phrases.
9. cefr_level: Estimated CEFR level (A1, A2, B1, B2, C1, C2).
10. difficulty_score: Number between 1.0 (very basic) and 10.0 (advanced).
"""
