import re
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.user import User
from ai.provider import LLMProvider, get_llm_provider
from ai.schemas import WordExplanationAI, ExampleSetAI
from ai.prompts.explanation import build_explanation_prompt, EXPLANATION_SYSTEM_PROMPT
from ai.prompts.examples import build_examples_prompt, EXAMPLES_SYSTEM_PROMPT
from ai.validation import (
    validate_vocabulary_explanation,
    validate_vocabulary_examples,
    is_circular_or_generic_definition,
    is_generic_contextual_meaning,
    has_generic_collocations,
    has_generic_examples,
    GENERIC_EXAMPLE_PATTERNS,
)


def is_details_stale(word: str, details: Optional[WordDetails]) -> bool:
    """Determine if cached WordDetails contain obsolete, generic, or low-quality fallback data."""
    if not details:
        return True

    clean = word.strip().lower()

    # 1. Semantic validation checks on cached DB fields
    if is_circular_or_generic_definition(word, details.simple_meaning):
        return True

    if is_generic_contextual_meaning(word, details.contextual_meaning):
        return True

    if details.part_of_speech in ["word", "term", "unknown", "", None]:
        return True

    if details.pronunciation_text == f"/{clean}/":
        return True

    if has_generic_collocations(word, details.collocations):
        return True

    # 2. Check for placeholder synonyms
    if details.synonyms:
        for syn in details.synonyms:
            syn_str = str(syn).lower()
            if "term related to" in syn_str or "concept of" in syn_str:
                return True

    # 3. Check for bad template word forms (e.g. 'vividlytion', 'hassletion')
    if details.word_forms:
        wf_str = str(details.word_forms).lower()
        if f"{clean}tion" in wf_str and clean not in ("hesitate", "attract", "direct", "react", "instruct", "connect"):
            return True

    return False


def is_examples_stale(word: str, examples: Optional[List[VocabularyExample]]) -> bool:
    """Determine if cached examples contain obsolete, generic, or low-quality fallback data."""
    if not examples or len(examples) == 0:
        return True

    # 1. Check for generic / boilerplate example patterns
    for ex in examples:
        if not ex.example_text:
            return True
        text_lower = ex.example_text.lower()
        if any(re.search(pat, text_lower) for pat in GENERIC_EXAMPLE_PATTERNS):
            return True

    # 2. Check for structural template repetition
    if has_generic_examples(word, examples):
        return True

    return False


class LearningService:
    @staticmethod
    async def get_or_generate_learning_content(
        db: Session,
        user: User,
        vocab_id: str,
        llm: Optional[LLMProvider] = None,
    ) -> Vocabulary:
        """Fetch cached word details & examples or generate/upgrade them via AI Provider."""
        clean_target = vocab_id.strip().lower()
        vocab = (
            db.query(Vocabulary)
            .filter(
                or_(Vocabulary.id == vocab_id, Vocabulary.word == clean_target),
                Vocabulary.user_id == user.id,
            )
            .first()
        )

        if not vocab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary word not found",
            )

        provider = llm or get_llm_provider()
        needs_commit = False

        # Generate or upgrade WordDetails if not cached or if stale
        if is_details_stale(vocab.word, vocab.details):
            try:
                explanation_data: WordExplanationAI = await provider.generate_structured(
                    prompt=build_explanation_prompt(vocab.word),
                    response_schema=WordExplanationAI,
                    system_prompt=EXPLANATION_SYSTEM_PROMPT,
                    temperature=0.3,
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Unable to generate vocabulary details for '{vocab.word}': {str(e)}",
                )

            # Validate generated explanation semantically
            is_valid, err_msg = validate_vocabulary_explanation(vocab.word, explanation_data)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI provider returned invalid vocabulary content: {err_msg}",
                )

            if vocab.details:
                vocab.details.simple_meaning = explanation_data.simple_meaning
                vocab.details.contextual_meaning = explanation_data.contextual_meaning
                vocab.details.part_of_speech = explanation_data.part_of_speech
                vocab.details.pronunciation_text = explanation_data.pronunciation_text
                vocab.details.synonyms = explanation_data.synonyms
                vocab.details.antonyms = explanation_data.antonyms
                vocab.details.word_forms = explanation_data.word_forms
                vocab.details.collocations = explanation_data.collocations
                vocab.details.cefr_level = explanation_data.cefr_level
                vocab.details.difficulty_score = explanation_data.difficulty_score
            else:
                details = WordDetails(
                    vocabulary_id=vocab.id,
                    simple_meaning=explanation_data.simple_meaning,
                    contextual_meaning=explanation_data.contextual_meaning,
                    part_of_speech=explanation_data.part_of_speech,
                    pronunciation_text=explanation_data.pronunciation_text,
                    synonyms=explanation_data.synonyms,
                    antonyms=explanation_data.antonyms,
                    word_forms=explanation_data.word_forms,
                    collocations=explanation_data.collocations,
                    cefr_level=explanation_data.cefr_level,
                    difficulty_score=explanation_data.difficulty_score,
                )
                db.add(details)
            needs_commit = True

        # Generate or upgrade Examples if not cached or if stale
        if is_examples_stale(vocab.word, vocab.examples):
            try:
                examples_data: ExampleSetAI = await provider.generate_structured(
                    prompt=build_examples_prompt(vocab.word),
                    response_schema=ExampleSetAI,
                    system_prompt=EXAMPLES_SYSTEM_PROMPT,
                    temperature=0.7,
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Unable to generate conversational examples for '{vocab.word}': {str(e)}",
                )

            # Validate generated examples semantically
            is_valid_ex, err_msg_ex = validate_vocabulary_examples(vocab.word, examples_data)
            if not is_valid_ex:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI provider returned invalid examples: {err_msg_ex}",
                )

            # Assign directly to the relationship collection for clean cascading replacement
            vocab.examples = [
                VocabularyExample(
                    vocabulary_id=vocab.id,
                    example_text=ex.example_text,
                    context_label=ex.context_label,
                    order_index=idx,
                )
                for idx, ex in enumerate(examples_data.examples)
            ]
            needs_commit = True

        if needs_commit:
            db.commit()
            db.refresh(vocab)

        return vocab

    @staticmethod
    def mark_word_learned(db: Session, user: User, vocab_id: str) -> Vocabulary:
        """Transition vocabulary status from 'new' to 'learned'."""
        clean_target = vocab_id.strip().lower()
        vocab = (
            db.query(Vocabulary)
            .filter(
                or_(Vocabulary.id == vocab_id, Vocabulary.word == clean_target),
                Vocabulary.user_id == user.id,
            )
            .first()
        )

        if not vocab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary word not found",
            )

        if vocab.status == "new":
            vocab.status = "learned"
            # Add small initial mastery for completing learning
            vocab.mastery_score = max(vocab.mastery_score, 0.15)
            # Award XP to user for learning a new word (10 XP)
            user.xp += 10
            from services.gamification_service import GamificationService

            GamificationService.record_activity(db, user)
            db.commit()
            db.refresh(vocab)

        return vocab
