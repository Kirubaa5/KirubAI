from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional


class WordExplanationAI(BaseModel):
    """Structured AI output for word explanation."""
    simple_meaning: str = Field(..., description="Clear and simple definition understandable by B1 English learners")
    contextual_meaning: str = Field(..., description="Detailed explanation of how and when to naturally use the word")
    part_of_speech: str = Field(..., description="e.g. verb, noun, adjective, adverb")
    pronunciation_text: str = Field(..., description="Phonetic text representation, e.g. HEZ-ih-tayt")
    synonyms: List[str] = Field(default_factory=list, description="3-5 closely related synonyms")
    antonyms: List[str] = Field(default_factory=list, description="2-4 opposite meaning words")
    word_forms: Dict[str, str] = Field(
        default_factory=dict,
        description="Grammatical forms, e.g. {'verb': 'hesitate', 'noun': 'hesitation', 'adjective': 'hesitant'}"
    )
    collocations: List[str] = Field(
        default_factory=list,
        description="Common word pairings, e.g. ['hesitate to ask', 'don\'t hesitate', 'hesitate for a moment']"
    )
    cefr_level: str = Field(..., description="CEFR difficulty level: A1, A2, B1, B2, C1, or C2")
    difficulty_score: float = Field(..., description="Difficulty score from 1.0 (very basic) to 10.0 (highly advanced)")

    model_config = ConfigDict(from_attributes=True)


class ConversationalExampleAI(BaseModel):
    context_label: str = Field(..., description="Situation type (e.g., Workplace, Friends, Interview, Family, College)")
    example_text: str = Field(..., description="Natural, realistic English sentence using the target word")

    model_config = ConfigDict(from_attributes=True)


class ExampleSetAI(BaseModel):
    """Set of 10 conversational examples."""
    examples: List[ConversationalExampleAI] = Field(..., description="10 conversational examples across varied scenarios")

    model_config = ConfigDict(from_attributes=True)


class ScenarioAI(BaseModel):
    """Generated practice scenario."""
    situation: str = Field(..., description="Detailed description of a realistic life situation")
    prompt: str = Field(..., description="Instruction on how the user should respond using the target word")
    context_hint: Optional[str] = Field(None, description="Subtle hint about nuance or context")

    model_config = ConfigDict(from_attributes=True)


class EvaluationAI(BaseModel):
    """AI evaluation of user's practice attempt."""
    vocabulary_usage_score: float = Field(..., ge=0.0, le=10.0, description="How well the target word was used (0-10)")
    grammar_score: float = Field(..., ge=0.0, le=10.0, description="Grammar and syntax accuracy (0-10)")
    context_score: float = Field(..., ge=0.0, le=10.0, description="Suitability to the given scenario (0-10)")
    naturalness_score: float = Field(..., ge=0.0, le=10.0, description="How natural and native-like the response is (0-10)")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Weighted aggregate score (0-10)")
    feedback: str = Field(..., description="Constructive, encouraging feedback on strengths and improvement areas")
    improved_version: str = Field(..., description="A more natural, native-like alternative phrasing")
    vocabulary_used_correctly: bool = Field(..., description="Whether the target word was used with correct meaning and form")

    model_config = ConfigDict(from_attributes=True)


class ReviewEvaluationAI(BaseModel):
    """AI evaluation of user's active recall / review response."""
    is_correct: bool = Field(..., description="Whether the user correctly recalled or used the target word")
    score: float = Field(..., ge=0.0, le=10.0, description="Score from 0.0 to 10.0")
    feedback: str = Field(..., description="Encouraging and constructive feedback on the recall attempt")
    recalled_word: Optional[str] = Field(None, description="The target word or form identified from the response")

    model_config = ConfigDict(from_attributes=True)

