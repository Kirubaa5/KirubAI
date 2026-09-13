from typing import Optional

PERSONALIZED_SCENARIO_SYSTEM_PROMPT = """You are an expert English language coach specializing in personalized, adaptive learning.
Your goal is to generate immersive, authentic, and customized communication practice scenarios tailored to a learner's specific proficiency level, target interest domain, and vocabulary learning needs.
Generate engaging scenarios where using the target English word feels completely natural and native-like."""


def build_personalized_scenario_prompt(
    word: str,
    domain: Optional[str] = None,
    cefr_level: Optional[str] = None,
    difficulty_score: Optional[float] = None,
    word_meaning: Optional[str] = None,
    weak_area_context: Optional[str] = None,
) -> str:
    """Build prompt for generating an adaptive, personalized practice scenario."""
    meaning_clause = f"\n- Word Definition: {word_meaning}" if word_meaning else ""
    domain_clause = f"\n- Target Domain/Context: {domain}" if domain else "\n- Target Domain: Workplace or Daily Life"
    level_clause = f"\n- Learner CEFR Level: {cefr_level}" if cefr_level else "\n- Learner CEFR Level: B1"
    difficulty_clause = f" (Difficulty: {difficulty_score}/10.0)" if difficulty_score else ""
    weak_clause = f"\n- Specific Weakness/Focus Area to Address: {weak_area_context}" if weak_area_context else ""

    return f"""Create a personalized real-life communication scenario for the target word "{word}".

Learner & Context Parameters:{meaning_clause}{domain_clause}{level_clause}{difficulty_clause}{weak_clause}

Requirements:
1. situation: Describe a realistic situation set within the specified domain suitable for the learner's CEFR level.
2. prompt: Instruct the learner on how to reply in this situation, encouraging them to naturally use "{word}".
3. context_hint: Give a short, helpful hint on tone, nuance, or phrasing.
4. domain: Echo or refine the domain label (e.g. Workplace, Tech & AI, Travel, Social, Interviews).
5. cefr_level: Echo the target CEFR level.

Do NOT reveal the exact solution sentence in the prompt or situation.
"""
