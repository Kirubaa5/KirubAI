from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.user import User
from ai.provider import LLMProvider
from ai.mock_provider import MockLLMProvider
from ai.openai_provider import OpenAIProvider
from ai.schemas import WordExplanationAI, ExampleSetAI
from ai.prompts.explanation import build_explanation_prompt, EXPLANATION_SYSTEM_PROMPT
from ai.prompts.examples import build_examples_prompt, EXAMPLES_SYSTEM_PROMPT
from config import settings


def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    return MockLLMProvider()


class LearningService:
    @staticmethod
    async def get_or_generate_learning_content(
        db: Session,
        user: User,
        vocab_id: str,
        llm: LLMProvider | None = None,
    ) -> Vocabulary:
        """Fetch cached word details & examples or generate them via AI Provider."""
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

        # Generate WordDetails if not cached
        if not vocab.details:
            explanation_data: WordExplanationAI = await provider.generate_structured(
                prompt=build_explanation_prompt(vocab.word),
                response_schema=WordExplanationAI,
                system_prompt=EXPLANATION_SYSTEM_PROMPT,
                temperature=0.3,
            )

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

        # Generate Examples if not cached
        if not vocab.examples or len(vocab.examples) == 0:
            examples_data: ExampleSetAI = await provider.generate_structured(
                prompt=build_examples_prompt(vocab.word),
                response_schema=ExampleSetAI,
                system_prompt=EXAMPLES_SYSTEM_PROMPT,
                temperature=0.7,
            )

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
