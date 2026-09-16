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


class PersonalizedScenarioAI(BaseModel):
    """Generated personalized practice scenario tailored to domain and learner level."""
    situation: str = Field(..., description="A vivid, personalized scenario matching the learner's requested domain and difficulty")
    prompt: str = Field(..., description="Direct instruction prompting the learner to use the target word naturally")
    context_hint: Optional[str] = Field(None, description="Nuance or stylistic guidance appropriate for this situation")
    domain: str = Field(..., description="The interest domain of the scenario (e.g., Workplace, Travel, Tech, Daily Life)")
    cefr_level: str = Field(..., description="Target CEFR level (A1, A2, B1, B2, C1, C2)")

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


class VocabularyUsageDetailAI(BaseModel):
    """Per-word evaluation within a conversation."""
    word: str = Field(..., description="Target vocabulary word")
    used: bool = Field(..., description="Whether the word was used during the conversation")
    quality: Optional[float] = Field(None, ge=0.0, le=10.0, description="Usage quality score from 0.0 to 10.0 if used")
    context: Optional[str] = Field(None, description="Context excerpt or explanation of how the word was used")

    model_config = ConfigDict(from_attributes=True)


class ConversationEvaluationAI(BaseModel):
    """Structured AI output for end-of-conversation evaluation."""
    vocabulary_details: List[VocabularyUsageDetailAI] = Field(
        default_factory=list,
        description="Detailed evaluation breakdown for each target vocabulary word",
    )
    vocabulary_used: List[str] = Field(
        default_factory=list,
        description="List of target vocabulary words successfully used by the learner",
    )
    vocabulary_missed: List[str] = Field(
        default_factory=list,
        description="List of target vocabulary words not used during the conversation",
    )
    usage_quality: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary mapping each used target word to its quality score (0.0 to 10.0)",
    )
    overall_fluency: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Overall conversational fluency score from 0.0 to 10.0",
    )
    feedback: str = Field(
        ...,
        description="Constructive, encouraging feedback on conversational flow, grammar, and vocabulary usage",
    )

    model_config = ConfigDict(from_attributes=True)


class KnowledgeExplanationAI(BaseModel):
    """Structured AI output for RAG knowledge and grammar explanations."""
    summary: str = Field(..., description="Direct, concise answer to the learner's query or grammar question")
    detailed_explanation: str = Field(..., description="In-depth breakdown of the underlying rule or nuance")
    rule_applied: str = Field(..., description="Name or summary of the specific grammar/usage rule applied")
    correct_usage: List[str] = Field(default_factory=list, description="List of natural, correct English examples")
    incorrect_usage: List[str] = Field(default_factory=list, description="Common learner mistakes or pitfalls to avoid")
    learning_tip: str = Field(..., description="Actionable memory hook or rule of thumb for learner retention")
    groundedness_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score that explanation matches retrieved knowledge (0.0 to 1.0)")

    model_config = ConfigDict(from_attributes=True)


class MultiWordScenarioAI(BaseModel):
    """Generated multi-word practice scenario for 'Use My Vocabulary'."""
    situation: str = Field(..., description="A cohesive, realistic scenario where multiple target words can naturally be used together")
    prompt: str = Field(..., description="Direct instruction prompting the learner to write a response incorporating the target words")
    target_words: List[str] = Field(..., description="The list of target vocabulary words to use in the response")
    context_hint: Optional[str] = Field(None, description="Helpful nuance or stylistic tip for connecting the words naturally")

    model_config = ConfigDict(from_attributes=True)


class TargetWordEvaluationAI(BaseModel):
    """Individual per-word evaluation in a multi-word practice response."""
    word: str = Field(..., description="Target vocabulary word")
    used: bool = Field(..., description="Whether the word (or an inflected grammatical form) was used in the response")
    used_correctly: bool = Field(..., description="Whether the word was used with correct meaning and grammatical form")
    used_naturally: bool = Field(..., description="Whether the word fits naturally and idiomatically into the sentence")
    score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Usage quality score for this word (0.0 to 10.0)")
    feedback: str = Field(..., description="Specific feedback on this word's usage and suggestions for improvement")

    model_config = ConfigDict(from_attributes=True)


class MultiWordEvaluationAI(BaseModel):
    """Structured AI output for multi-word practice evaluation."""
    word_evaluations: List[TargetWordEvaluationAI] = Field(..., description="Detailed individual evaluation for each target word")
    vocabulary_usage_score: float = Field(..., ge=0.0, le=10.0, description="Overall vocabulary usage score across all target words (0-10)")
    grammar_score: float = Field(..., ge=0.0, le=10.0, description="Grammar, punctuation, and syntax accuracy score (0-10)")
    context_score: float = Field(..., ge=0.0, le=10.0, description="Relevance and appropriateness to the given scenario (0-10)")
    naturalness_score: float = Field(..., ge=0.0, le=10.0, description="Overall naturalness, fluency, and idiomatic flow (0-10)")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Weighted aggregate score (0-10)")
    feedback: str = Field(..., description="Comprehensive constructive feedback covering strengths and areas to refine")
    improved_version: str = Field(..., description="A polished, native-like alternative response showing natural usage of all target words")
    is_successful: bool = Field(..., description="Whether the response successfully demonstrated active mastery of the target words")

    model_config = ConfigDict(from_attributes=True)




