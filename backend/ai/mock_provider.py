from typing import TypeVar, Type, List, Dict, Optional
from pydantic import BaseModel
from ai.provider import LLMProvider
from ai.schemas import (
    WordExplanationAI,
    ConversationalExampleAI,
    ExampleSetAI,
    ScenarioAI,
    EvaluationAI,
)

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM provider for tests and offline development."""

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        return "This is a mocked LLM text response."

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> T:
        # Check prompt for word name or fallback
        word = "hesitate"
        if "Explain the English word" in prompt or "word \"" in prompt:
            import re
            match = re.search(r'word\s*["\']?([a-zA-Z\s\-]+)["\']?', prompt)
            if match:
                word = match.group(1).strip()

        if issubclass(response_schema, WordExplanationAI):
            return WordExplanationAI(
                simple_meaning=f"To pause before saying or doing something because you are uncertain or nervous.",
                contextual_meaning=f"Used when someone shows reluctance or pauses to make a thoughtful choice in professional, academic, or social situations.",
                part_of_speech="verb",
                pronunciation_text="HEZ-ih-tayt",
                synonyms=["pause", "waver", "falter", "dither"],
                antonyms=["decide", "commit", "proceed"],
                word_forms={
                    "verb": word,
                    "noun": f"{word}tion",
                    "adjective": f"{word}nt",
                    "adverb": f"{word}ntly",
                },
                collocations=[
                    f"{word} to ask",
                    f"don't {word}",
                    f"{word} for a moment",
                    f"without {word}ing",
                ],
                cefr_level="B1",
                difficulty_score=4.0,
            )

        if issubclass(response_schema, ExampleSetAI):
            return ExampleSetAI(
                examples=[
                    ConversationalExampleAI(
                        context_label="Workplace",
                        example_text=f"Please don't {word} to reach out if you have any questions regarding the project.",
                    ),
                    ConversationalExampleAI(
                        context_label="Friends",
                        example_text=f"I {word}d for a second before telling my friend the truth about what happened.",
                    ),
                    ConversationalExampleAI(
                        context_label="Meeting",
                        example_text=f"The team lead {word}d before approving the final budget proposal.",
                    ),
                    ConversationalExampleAI(
                        context_label="Interview",
                        example_text=f"I {word}d briefly to gather my thoughts before answering the technical question.",
                    ),
                    ConversationalExampleAI(
                        context_label="College",
                        example_text=f"She {word}d to raise her hand in class even though she knew the correct answer.",
                    ),
                    ConversationalExampleAI(
                        context_label="Family",
                        example_text=f"My parents didn't {word} to support my decision to study abroad.",
                    ),
                    ConversationalExampleAI(
                        context_label="Shopping",
                        example_text=f"I {word}d between the two laptops because both had great reviews.",
                    ),
                    ConversationalExampleAI(
                        context_label="Travel",
                        example_text=f"We {word}d at the intersection, unsure of which road would lead to the hotel.",
                    ),
                    ConversationalExampleAI(
                        context_label="Phone call",
                        example_text=f"He {word}d on the phone when I asked if he was free this weekend.",
                    ),
                    ConversationalExampleAI(
                        context_label="Daily life",
                        example_text=f"When an opportunity presents itself, you shouldn't {word} to seize it.",
                    ),
                ]
            )

        if issubclass(response_schema, ScenarioAI):
            return ScenarioAI(
                situation="Your manager asks whether you can take on an urgent new feature deadline for next Friday, but you already have a full backlog.",
                prompt=f"Respond politely and professionally to your manager, naturally expressing your hesitation using the target word '{word}'.",
                context_hint="Be respectful and explain your workload while offering to discuss priorities.",
            )

        if issubclass(response_schema, EvaluationAI):
            return EvaluationAI(
                vocabulary_usage_score=9.0,
                grammar_score=8.5,
                context_score=9.0,
                naturalness_score=8.5,
                overall_score=8.7,
                feedback=f"Excellent usage of the target vocabulary! Your sentence is contextually accurate and fits the professional scenario perfectly.",
                improved_version=f"I'd love to help, but I hesitate to commit right away since my current deliverables are already scheduled for this sprint.",
                vocabulary_used_correctly=True,
            )

        # Fallback to schema default instantiation if available
        raise ValueError(f"Unsupported mock schema: {response_schema}")

    async def generate_conversation(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        return "That sounds like a great perspective! How did you handle that situation next?"
