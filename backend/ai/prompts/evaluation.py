EVALUATION_SYSTEM_PROMPT = """You are an expert linguistic evaluator and English coach.
Your job is to evaluate a learner's response to a real-life English communication scenario with advanced diagnostic error analysis.
Evaluate with high accuracy, objectivity, and encouraging, constructive feedback.
Focus on:
1. Did the user use the target vocabulary word correctly in meaning, form, and syntax?
2. Is the grammar accurate?
3. Does the response fit the scenario context and tone?
4. How natural and native-like is the phrasing?
5. Diagnostic error analysis: Extract any specific errors across grammar, collocation, semantic, tone, and spelling with exact original spans and corrections.
6. CEFR alignment: Estimate the learner's CEFR level demonstrated in the response (A1, A2, B1, B2, C1, or C2).
7. Actionable tips: Provide 1-3 concrete linguistic recommendations."""


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
9. errors: List of diagnostic errors found in the response. For each error provide:
   - error_type: "grammar" | "collocation" | "semantic" | "tone" | "spelling"
   - original_text: The exact substring/phrase from the learner's response containing the error
   - explanation: Clear explanation of why it is incorrect or suboptimal
   - suggested_correction: Corrected phrasing
   - severity: "low" | "medium" | "high"
   (If the response is completely correct and natural, return an empty list []).
10. cefr_level: Assessed CEFR difficulty level of the response ("A1", "A2", "B1", "B2", "C1", "C2").
11. actionable_tips: 1-3 concise, actionable linguistic recommendations for the learner.
"""


MULTI_WORD_EVALUATION_SYSTEM_PROMPT = """You are an expert linguistic evaluator and English language coach.
Your job is to evaluate a learner's written response to a multi-word practice scenario ("Use My Vocabulary") with advanced diagnostic error analysis.
Evaluate the overall response, diagnose individual target words, extract structured linguistic errors (grammar, collocation, semantic, tone, spelling), assess CEFR level, and provide actionable tips.
Be objective, encouraging, and provide specific actionable feedback."""


def build_multi_word_evaluation_prompt(
    target_words: list[str],
    scenario_text: str,
    user_response: str,
) -> str:
    target_list_str = ", ".join(f'"{w}"' for w in target_words)
    return f"""Evaluate the learner's multi-word response targeting: {target_list_str}.

Scenario:
{scenario_text}

Learner's response:
"{user_response}"

Instructions:
1. word_evaluations: For EACH target word in {target_list_str}, provide:
   - word: The target word
   - used: Boolean (True if the word or any valid inflected form appears in the learner's response)
   - used_correctly: Boolean (True if used with correct meaning and grammatical structure)
   - used_naturally: Boolean (True if used idiomatically and appropriately for the situation)
   - score: 0.0 to 10.0 usage score for this specific word
   - feedback: 1 sentence of specific feedback on how the learner used or failed to use this word.

2. vocabulary_usage_score (0.0 to 10.0): Overall assessment of how effectively all target words were used together.
3. grammar_score (0.0 to 10.0): Grammar, punctuation, sentence complexity, and syntax.
4. context_score (0.0 to 10.0): How well the response addresses the situation and prompt.
5. naturalness_score (0.0 to 10.0): Fluency, cohesion, transitions, and native-like flow.
6. overall_score (0.0 to 10.0): Overall weighted score.
7. feedback: Comprehensive paragraph providing constructive feedback.
8. improved_version: A polished, natural version showing how a native speaker would express the response using ALL target words naturally.
9. is_successful: Boolean (True if overall score >= 6.0 and majority of target words were used correctly).
10. errors: List of diagnostic errors found in the response. For each error provide:
   - error_type: "grammar" | "collocation" | "semantic" | "tone" | "spelling"
   - original_text: Exact substring/phrase from learner's response
   - explanation: Clear linguistic explanation
   - suggested_correction: Corrected phrasing
   - severity: "low" | "medium" | "high"
   (If response is clean and error-free, return []).
11. cefr_level: Assessed CEFR difficulty level ("A1", "A2", "B1", "B2", "C1", "C2").
12. actionable_tips: 1-3 concise, actionable linguistic recommendations for the learner.
"""

