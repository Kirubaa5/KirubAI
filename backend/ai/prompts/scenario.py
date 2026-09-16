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


MULTI_WORD_SCENARIO_SYSTEM_PROMPT = """You are an expert English language coach and pedagogy specialist.
Your goal is to help language learners synthesize multiple vocabulary words into active, natural communication.
Generate a cohesive, realistic scenario where using ALL of the specified target vocabulary words makes natural conversational sense.
Avoid artificial or forced scenarios; make the narrative engaging, believable, and authentic."""


def build_multi_word_scenario_prompt(
    words: list[str],
    word_details: Optional[list[dict]] = None,
    learner_level: str = "intermediate",
    domain: Optional[str] = None,
) -> str:
    words_formatted = ", ".join(f'"{w}"' for w in words)
    details_str = ""
    if word_details:
        details_str = "\nTarget Words Details:\n" + "\n".join(
            f"- {wd.get('word', '')}: {wd.get('meaning', '')} ({wd.get('cefr_level', 'B1')})"
            for wd in word_details
        )

    domain_hint = f"\nPreferred Domain/Context: {domain}" if domain else ""

    return f"""Create a cohesive, single real-life communication scenario designed for 'Use My Vocabulary' practice.
The learner must write a response that naturally incorporates all of the following target words: {words_formatted}.
Learner Level: {learner_level}{domain_hint}{details_str}

Requirements:
1. situation: A realistic, contextual setting (e.g. workplace project negotiation, resolving a complex travel problem, strategic team planning, advising a friend through a challenging life choice) where using all {len(words)} target words is logical, cohesive, and natural.
2. prompt: Clear instructions prompting the learner to express their perspective or handle the situation, explicitly requesting them to naturally integrate all target words: {words_formatted}.
3. target_words: Exactly the list of target words {words}.
4. context_hint: Helpful advice on tone, register, and how to connect the concepts without sounding forced.

Do NOT provide the solution or write the learner's response.
"""

