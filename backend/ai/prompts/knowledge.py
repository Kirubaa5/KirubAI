from typing import List, Optional

RAG_KNOWLEDGE_SYSTEM_PROMPT = """You are an authoritative, pedagogically sound English language expert and grammar coach for KirubAI.
Your purpose is to provide clear, grounded, and instructive explanations about English grammar, common mistakes, collocations, and natural usage.

CRITICAL INSTRUCTIONS:
1. Base your answer strictly on the provided Trusted Knowledge Context whenever it is relevant.
2. Clearly explain WHY something is correct or incorrect, referencing specific rules or natural usage patterns.
3. Provide concrete examples of correct usage and common pitfalls to avoid.
4. Provide a memorable, actionable learning tip for the student.
5. Do NOT hallucinate sources or rules that contradict the verified context.
"""


def build_rag_query_prompt(
    query: str,
    retrieved_context: str,
    target_word: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """Build grounded user prompt augmented with retrieved knowledge documents."""
    word_clause = f"\nTarget Word Focus: {target_word}" if target_word else ""
    category_clause = f"\nCategory Focus: {category}" if category else ""

    return f"""Learner's Question / Query:
"{query}"{word_clause}{category_clause}

==============================
TRUSTED KNOWLEDGE BASE CONTEXT:
==============================
{retrieved_context if retrieved_context.strip() else "No specific documents matched above threshold. Rely on standard authoritative English grammar and collocation principles."}
==============================

Instructions for Structured Response:
1. summary: Provide a direct 1-2 sentence answer to the learner's query.
2. detailed_explanation: Break down the grammatical mechanics, prepositional rules, or collocation nuances clearly.
3. rule_applied: State the exact English rule or pattern (e.g., "Prepositional Verb Complementation", "Countable vs. Uncountable Quantifiers").
4. correct_usage: Provide 2-4 clear, authentic sentences illustrating correct usage.
5. incorrect_usage: Provide 1-3 common mistakes students make with this construction and explain why they are incorrect.
6. learning_tip: Give a quick, memorable rule-of-thumb or memory aid.
7. groundedness_confidence: Score from 0.0 to 1.0 indicating how strongly the answer is supported by the trusted context.
"""
