from typing import Optional

REVIEW_EVALUATION_SYSTEM_PROMPT = """You are an encouraging, expert English language tutor evaluating an active recall or usage review attempt.
Evaluate whether the learner accurately remembered, spelled, or appropriately used the target English vocabulary word.
Return your evaluation strictly conforming to the requested JSON schema."""


def build_review_evaluation_prompt(
    target_word: str,
    definition: Optional[str],
    user_response: str,
    review_type: str = "recall",
) -> str:
    """Build the prompt for evaluating a user's active recall / review response."""
    return f"""Evaluate the learner's response for the target English word.

Target Word: "{target_word}"
Word Definition / Hint: "{definition or 'N/A'}"
Review Type: "{review_type}"

Learner's response:
"{user_response}"

Instructions:
1. Determine if the learner recalled the target word "{target_word}" (or an acceptable valid grammatical inflection/spelling variant).
2. If the learner typed the word accurately, set is_correct to true, score to 9.0-10.0, and provide positive feedback confirming the word.
3. If the learner wrote a sentence correctly incorporating the target word, evaluate the usage and set is_correct to true with score 8.5-10.0.
4. If the learner gave an incorrect word, misunderstood the concept, or did not recall the word, set is_correct to false, score to 1.0-5.0, and provide encouraging feedback revealing the correct word.
5. Keep feedback concise (1-2 sentences) and helpful for English vocabulary retention.
"""
