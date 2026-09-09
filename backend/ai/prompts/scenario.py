from typing import Optional

SCENARIO_SYSTEM_PROMPT = """You are an expert English language coach and curriculum designer.
Your goal is to help language learners move passive vocabulary into active conversational fluency.
Generate realistic, immersive, real-life communication scenarios where using the specified target English word is natural and appropriate.
Make the scenarios engaging, relatable, and authentic."""


def build_scenario_prompt(
    word: str,
    word_meaning: Optional[str] = None,
    cefr_level: Optional[str] = None,
) -> str:
    meaning_hint = f" (Meaning: {word_meaning})" if word_meaning else ""
    level_hint = f" aimed at CEFR {cefr_level} learners" if cefr_level else ""

    return f"""Create a realistic real-life communication scenario for the target English word "{word}"{meaning_hint}{level_hint}.

Provide:
1. situation: A vivid, realistic situation (e.g. workplace meeting, conversation with friends, interview, casual dinner, team discussion, travel situation).
2. prompt: A direct instruction telling the user what message they need to convey and encouraging them to naturally use the word "{word}".
3. context_hint: A subtle tip regarding tone, nuance, or politeness suitable for this context.

Do NOT give the exact answer sentence in the prompt or situation.
"""
