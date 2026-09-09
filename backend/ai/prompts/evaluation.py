EVALUATION_SYSTEM_PROMPT = """You are an expert linguistic evaluator and English coach.
Your job is to evaluate a learner's response to a real-life English communication scenario.
Evaluate with high accuracy, objectivity, and encouraging, constructive feedback.
Focus on:
1. Did the user use the target vocabulary word correctly in meaning, form, and syntax?
2. Is the grammar accurate?
3. Does the response fit the scenario context and tone?
4. How natural and native-like is the phrasing?"""


def build_evaluation_prompt(
    word: str,
    scenario_text: str,
    user_response: str,
) -> str:
    return f"""Evaluate the learner's response for the target English word "{word}".

Scenario:
{scenario_text}

Learner's response:
"{user_response}"

Evaluate the following metrics:
1. vocabulary_usage_score (0.0 to 10.0): Did the user correctly and appropriately use "{word}" or one of its valid grammatical forms? (If the word was not used at all or used completely incorrectly, score must be <= 3.0).
2. grammar_score (0.0 to 10.0): Grammatical correctness, syntax, tense, and sentence structure.
3. context_score (0.0 to 10.0): How well the response answers the scenario prompt and matches the required situation and tone.
4. naturalness_score (0.0 to 10.0): How authentic, idiomatic, and native-like the phrasing sounds.
5. overall_score (0.0 to 10.0): Weighted overall assessment.
6. feedback: 2-3 sentences of constructive feedback highlighting strengths and specific areas to improve.
7. improved_version: A natural, native-speaker phrasing of what the learner intended to convey using "{word}".
8. vocabulary_used_correctly: Boolean indicating whether "{word}" was used with accurate meaning and correct grammatical form.
"""
