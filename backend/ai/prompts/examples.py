EXAMPLES_SYSTEM_PROMPT = """You are an English linguistic expert. Generate realistic, authentic conversational examples of English words across varied real-life situations. Avoid unnatural textbook sentences. Make every example sound like natural English spoken by native speakers."""


def build_examples_prompt(word: str) -> str:
    return f"""Generate exactly 10 realistic, diverse conversational examples for the target English word "{word}".
Each example must come from a DISTINCT real-life context:
1. Workplace (team collaboration / projects)
2. Friends (casual conversation / plans)
3. Meeting (business / formal discussion)
4. Interview (job interview / professional response)
5. College (academic life / campus discussions)
6. Family (home / personal relationships)
7. Shopping (stores / making purchasing choices)
8. Travel (navigating / vacation situations)
9. Phone call (customer service / quick conversations)
10. Daily life (general everyday situations)

Each example must have:
- context_label: Name of the situation (e.g., "Workplace", "Friends")
- example_text: A natural, realistic sentence using "{word}".
"""
