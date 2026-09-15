from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.user import User
from ai.provider import LLMProvider
from ai.mock_provider import MockLLMProvider, MOCK_VOCABULARY_DB
from ai.openai_provider import OpenAIProvider
from ai.schemas import WordExplanationAI, ExampleSetAI
from ai.prompts.explanation import build_explanation_prompt, EXPLANATION_SYSTEM_PROMPT
from ai.prompts.examples import build_examples_prompt, EXAMPLES_SYSTEM_PROMPT
from config import settings


def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    return MockLLMProvider()


def is_details_stale(word: str, details: WordDetails | None) -> bool:
    """Determine if cached WordDetails contain obsolete, generic, or low-quality fallback data."""
    if not details:
        return True

    clean = word.strip().lower()

    # 1. If word is in curated mock dictionary, verify cached data matches curated definitions
    if clean in MOCK_VOCABULARY_DB:
        curated = MOCK_VOCABULARY_DB[clean]
        if details.simple_meaning != curated.get("simple_meaning"):
            return True
        if details.part_of_speech != curated.get("part_of_speech"):
            return True
        if details.pronunciation_text != curated.get("pronunciation_text"):
            return True

    # 2. Check for legacy generic fallback markers
    sm = (details.simple_meaning or "").lower()
    if "general meaning, usage, and definition" in sm:
        return True
    if details.part_of_speech == "word":
        return True
    if details.pronunciation_text == f"/{clean}/":
        return True

    # 3. Check for placeholder synonyms
    if details.synonyms:
        for syn in details.synonyms:
            syn_str = str(syn).lower()
            if "term related to" in syn_str or "concept of" in syn_str:
                return True

    # 4. Check for placeholder collocations
    if details.collocations:
        for col in details.collocations:
            col_str = str(col).lower()
            if "in context" in col_str or "use '" in col_str:
                return True

    # 5. Check for bad template word forms (e.g. 'vividlytion', 'hassletion')
    if details.word_forms:
        wf_str = str(details.word_forms).lower()
        if f"{clean}tion" in wf_str and clean not in ("hesitate", "attract", "direct", "react", "instruct", "connect"):
            return True

    return False


def is_examples_stale(word: str, examples: List[VocabularyExample] | None) -> bool:
    """Determine if cached examples contain obsolete, generic, or low-quality fallback data."""
    if not examples or len(examples) == 0:
        return True

    clean = word.strip().lower()

    # 1. If in curated mock dictionary, check if examples match curated list
    if clean in MOCK_VOCABULARY_DB and "examples" in MOCK_VOCABULARY_DB[clean]:
        curated_exs = MOCK_VOCABULARY_DB[clean]["examples"]
        if len(examples) != len(curated_exs):
            return True
        if len(examples) > 0 and examples[0].example_text != curated_exs[0][1]:
            return True

    # 2. Check for legacy boilerplate example phrases
    legacy_markers = [
        "applied to our current workflow",
        "used the word",
        "importance of understanding",
        "was impressed when the candidate used",
        "highlighted",
        "family discussion centered around the idea of",
        "no confusion about",
        "people in different regions interpret",
        "make sure to clarify her perspective on",
        "into daily conversations helps build confidence in english",
    ]
    for ex in examples:
        text_lower = ex.example_text.lower()
        if any(marker in text_lower for marker in legacy_markers):
            return True

    return False


class LearningService:
    @staticmethod
    async def get_or_generate_learning_content(
        db: Session,
        user: User,
        vocab_id: str,
        llm: LLMProvider | None = None,
    ) -> Vocabulary:
        """Fetch cached word details & examples or generate/upgrade them via AI Provider."""
        vocab = db.query(Vocabulary).filter(
            Vocabulary.id == vocab_id,
            Vocabulary.user_id == user.id,
        ).first()

        if not vocab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary word not found",
            )

        provider = llm or get_llm_provider()

        # Generate or upgrade WordDetails if not cached or if stale
        if is_details_stale(vocab.word, vocab.details):
            explanation_data: WordExplanationAI = await provider.generate_structured(
                prompt=build_explanation_prompt(vocab.word),
                response_schema=WordExplanationAI,
                system_prompt=EXPLANATION_SYSTEM_PROMPT,
                temperature=0.3,
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
            db.commit()

        # Generate or upgrade Examples if not cached or if stale
        if is_examples_stale(vocab.word, vocab.examples):
            examples_data: ExampleSetAI = await provider.generate_structured(
                prompt=build_examples_prompt(vocab.word),
                response_schema=ExampleSetAI,
                system_prompt=EXAMPLES_SYSTEM_PROMPT,
                temperature=0.7,
            )

            # Remove stale examples if any exist
            if vocab.examples:
                for old_ex in list(vocab.examples):
                    db.delete(old_ex)
                db.flush()

            for idx, ex in enumerate(examples_data.examples):
                example_obj = VocabularyExample(
                    vocabulary_id=vocab.id,
                    example_text=ex.example_text,
                    context_label=ex.context_label,
                    order_index=idx,
                )
                db.add(example_obj)
            db.commit()

        db.refresh(vocab)
        return vocab

    @staticmethod
    def mark_word_learned(db: Session, user: User, vocab_id: str) -> Vocabulary:
        """Transition vocabulary status from 'new' to 'learned'."""
        vocab = db.query(Vocabulary).filter(
            Vocabulary.id == vocab_id,
            Vocabulary.user_id == user.id,
        ).first()

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
            db.commit()
            db.refresh(vocab)

        return vocab
