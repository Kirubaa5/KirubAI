import re
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from fastapi import HTTPException, status

from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.practice import ReviewRecord
from models.user import User
from schemas.review import (
    ReviewPromptSchema,
    DueReviewItemResponse,
    DueReviewsResponse,
    ReviewSubmitRequest,
    ReviewSubmitResponse,
    ReviewRecordResponse,
    ReviewHistoryListResponse,
)
from services.spaced_repetition import (
    calculate_next_review,
    calculate_mastery,
    determine_status_transition,
)
from ai.provider import LLMProvider
from ai.schemas import ReviewEvaluationAI
from ai.prompts.review import build_review_evaluation_prompt, REVIEW_EVALUATION_SYSTEM_PROMPT
from services.learning_service import get_llm_provider


def build_cloze_sentence(word: str, examples: List[VocabularyExample]) -> Tuple[Optional[str], Optional[str]]:
    """Create a cloze sentence with the target word replaced with '_____'."""
    if not examples:
        return None, None

    pattern = re.compile(re.escape(word) + r"[a-zA-Z]*", re.IGNORECASE)

    for ex in examples:
        if pattern.search(ex.example_text):
            cloze = pattern.sub("_____", ex.example_text)
            return cloze, ex.context_label

    # If exact regex didn't match, return the first example with word replaced
    first_ex = examples[0]
    words_in_text = first_ex.example_text.split()
    replaced_words = ["_____" if word.lower() in w.lower() else w for w in words_in_text]
    return " ".join(replaced_words), first_ex.context_label


def generate_recall_prompt(vocab: Vocabulary) -> ReviewPromptSchema:
    """Generate an active recall prompt for a vocabulary word without revealing the answer."""
    details = vocab.details
    definition = details.simple_meaning if details else None
    part_of_speech = details.part_of_speech if details else None

    cloze_sentence, context_label = build_cloze_sentence(vocab.word, vocab.examples or [])

    # Build hint
    first_letter = vocab.word[0].upper() if vocab.word else ""
    letter_count = len(vocab.word) if vocab.word else 0
    hint_parts = [f"Starts with '{first_letter}' ({letter_count} letters)"]
    if details and details.pronunciation_text:
        hint_parts.append(f"Pronunciation: /{details.pronunciation_text}/")

    hint = " • ".join(hint_parts)

    synonyms_hint = details.synonyms[:2] if details and details.synonyms else []

    return ReviewPromptSchema(
        prompt_type="recall",
        definition=definition,
        part_of_speech=part_of_speech,
        cloze_sentence=cloze_sentence,
        hint=hint,
        context_label=context_label,
        synonyms_hint=synonyms_hint,
    )


class ReviewService:
    @staticmethod
    def get_due_reviews(
        db: Session,
        user: User,
        limit: int = 50,
    ) -> DueReviewsResponse:
        """
        Retrieve vocabulary items due for spaced repetition review for the authenticated user.
        Due condition:
          - user_id == user.id
          - status in ('learned', 'practiced', 'recalled', 'reinforced', 'mastered', 'struggling')
          - next_review_at is NULL OR next_review_at <= now()
        """
        now = datetime.now(timezone.utc)

        # Query due vocabulary
        query = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.user_id == user.id,
                Vocabulary.status.in_([
                    "learned",
                    "practiced",
                    "recalled",
                    "reinforced",
                    "mastered",
                    "struggling",
                ]),
                or_(
                    Vocabulary.next_review_at.is_(None),
                    Vocabulary.next_review_at <= now,
                ),
            )
            .order_by(
                # Prioritize struggling words first, then by next_review_at ascending
                desc(Vocabulary.status == "struggling"),
                Vocabulary.next_review_at.asc().nullsfirst(),
            )
        )

        total_due = query.count()
        vocab_items = query.limit(limit).all()

        items: List[DueReviewItemResponse] = []
        for v in vocab_items:
            prompt = generate_recall_prompt(v)
            items.append(
                DueReviewItemResponse(
                    vocabulary_id=v.id,
                    word=v.word,
                    status=v.status,
                    mastery_score=v.mastery_score,
                    last_reviewed_at=v.last_reviewed_at,
                    next_review_at=v.next_review_at,
                    review_interval_days=v.review_interval_days,
                    review_type="recall",
                    prompt=prompt,
                )
            )

        return DueReviewsResponse(
            due_count=total_due,
            items=items,
        )

    @staticmethod
    async def submit_review(
        db: Session,
        user: User,
        data: ReviewSubmitRequest,
        llm: Optional[LLMProvider] = None,
    ) -> ReviewSubmitResponse:
        """
        Submit and evaluate an active recall / review response.
        Updates spaced repetition intervals, mastery scores, status transitions, and persists ReviewRecord.
        """
        vocab = db.query(Vocabulary).filter(
            Vocabulary.id == data.vocabulary_id,
            Vocabulary.user_id == user.id,
        ).first()

        if not vocab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary word not found",
            )

        # Fetch recent review history to calculate consecutive streaks
        past_reviews = (
            db.query(ReviewRecord)
            .filter(
                ReviewRecord.vocabulary_id == vocab.id,
                ReviewRecord.user_id == user.id,
            )
            .order_by(desc(ReviewRecord.reviewed_at))
            .limit(10)
            .all()
        )

        consecutive_successes = 0
        consecutive_failures = 0
        for r in past_reviews:
            if r.recall_successful:
                if consecutive_failures == 0:
                    consecutive_successes += 1
                else:
                    break
            else:
                if consecutive_successes == 0:
                    consecutive_failures += 1
                else:
                    break

        user_input = data.response_text.strip()
        user_input_lower = user_input.lower()
        target_word_lower = vocab.word.lower()

        # Step 1: Deterministic evaluation check
        recall_successful = False
        score = 0.0
        feedback = ""

        # Exact match
        if user_input_lower == target_word_lower:
            recall_successful = True
            score = 10.0
            feedback = f"Excellent! You recalled '{vocab.word}' perfectly."
        # Word forms match
        elif (
            vocab.details
            and vocab.details.word_forms
            and user_input_lower in [v.lower() for v in vocab.details.word_forms.values()]
        ):
            recall_successful = True
            score = 9.5
            feedback = f"Great job! '{user_input}' is a correct grammatical form of '{vocab.word}'."
        # Substring / sentence usage match
        elif target_word_lower in user_input_lower:
            recall_successful = True
            score = 9.0
            feedback = f"Well done! You remembered and used '{vocab.word}' in your response."
        else:
            # Step 2: Use AI to evaluate natural language recall or contextual answer
            provider = llm or get_llm_provider()
            try:
                definition = vocab.details.simple_meaning if vocab.details else None
                eval_ai: ReviewEvaluationAI = await provider.generate_structured(
                    prompt=build_review_evaluation_prompt(
                        target_word=vocab.word,
                        definition=definition,
                        user_response=user_input,
                        review_type=data.review_type or "recall",
                    ),
                    response_schema=ReviewEvaluationAI,
                    system_prompt=REVIEW_EVALUATION_SYSTEM_PROMPT,
                    temperature=0.2,
                )
                recall_successful = eval_ai.is_correct
                score = round(eval_ai.score, 1)
                feedback = eval_ai.feedback
            except Exception:
                # Deterministic fallback if LLM is unavailable
                recall_successful = False
                score = 3.0
                feedback = f"The correct target word was '{vocab.word}'. Review its definition and try again!"

        # Step 3: Application-level state updates and spaced repetition calculations
        if recall_successful:
            new_consecutive_successes = consecutive_successes + 1
            new_consecutive_failures = 0
            xp_earned = 10
        else:
            new_consecutive_successes = 0
            new_consecutive_failures = consecutive_failures + 1
            vocab.failed_recall_count += 1
            xp_earned = 3

        previous_status = vocab.status
        previous_interval_days = vocab.review_interval_days or 1

        # Spaced repetition interval calculation
        new_interval_days, next_review_at = calculate_next_review(
            current_interval_days=previous_interval_days,
            recall_successful=recall_successful,
            consecutive_successes=new_consecutive_successes,
            consecutive_failures=new_consecutive_failures,
        )

        # Mastery calculation
        created_dt = vocab.created_at or datetime.now(timezone.utc)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        days_since_added = max(1, (datetime.now(timezone.utc) - created_dt).days)
        past_reviews_count = len(past_reviews)
        new_mastery = calculate_mastery(
            practice_count=vocab.practice_count,
            successful_practice_count=vocab.successful_usage_count,
            consecutive_successful_recalls=new_consecutive_successes,
            unique_contexts_used=min(5, max(1, len(vocab.practice_attempts or []))),
            reviews_completed_on_time=past_reviews_count + 1,
            total_reviews_due=max(1, past_reviews_count + 1),
            days_since_added=days_since_added,
        )

        # Status transition determination
        new_status = determine_status_transition(
            current_status=previous_status,
            recall_successful=recall_successful,
            consecutive_successes=new_consecutive_successes,
            consecutive_failures=new_consecutive_failures,
            mastery_score=new_mastery,
        )

        # Update vocabulary state
        vocab.status = new_status
        vocab.mastery_score = new_mastery
        vocab.review_interval_days = new_interval_days
        vocab.last_reviewed_at = datetime.now(timezone.utc)
        vocab.next_review_at = next_review_at

        # Update user XP and level
        user.xp += xp_earned
        user.level = max(1, (user.xp // 100) + 1)

        # Persist review record in database
        review_record = ReviewRecord(
            user_id=user.id,
            vocabulary_id=vocab.id,
            review_type=data.review_type or "recall",
            recall_successful=recall_successful,
            response_text=user_input,
            score=score,
            feedback=feedback,
            previous_interval_days=previous_interval_days,
            new_interval_days=new_interval_days,
            previous_status=previous_status,
            new_status=new_status,
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(review_record)
        db.commit()
        db.refresh(vocab)
        db.refresh(user)
        db.refresh(review_record)

        return ReviewSubmitResponse(
            recall_successful=recall_successful,
            score=score,
            feedback=feedback,
            previous_status=previous_status,
            new_status=new_status,
            previous_interval_days=previous_interval_days,
            new_interval_days=new_interval_days,
            next_review_at=next_review_at,
            mastery_score=new_mastery,
            xp_earned=xp_earned,
            target_word=vocab.word,
        )

    @staticmethod
    def get_review_history(
        db: Session,
        user: User,
        vocabulary_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> ReviewHistoryListResponse:
        """Get paginated review records for the authenticated user."""
        query = db.query(ReviewRecord).filter(ReviewRecord.user_id == user.id)

        if vocabulary_id:
            query = query.filter(ReviewRecord.vocabulary_id == vocabulary_id)

        total = query.count()
        pages = math.ceil(total / per_page) if total > 0 else 1
        offset = (page - 1) * per_page
        records = (
            query.order_by(desc(ReviewRecord.reviewed_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )

        items: List[ReviewRecordResponse] = []
        for r in records:
            target_word = r.vocabulary.word if r.vocabulary else None
            items.append(
                ReviewRecordResponse(
                    id=r.id,
                    user_id=r.user_id,
                    vocabulary_id=r.vocabulary_id,
                    target_word=target_word,
                    review_type=r.review_type,
                    recall_successful=r.recall_successful,
                    response_text=r.response_text,
                    score=r.score,
                    feedback=r.feedback,
                    previous_interval_days=r.previous_interval_days,
                    new_interval_days=r.new_interval_days,
                    previous_status=r.previous_status,
                    new_status=r.new_status,
                    reviewed_at=r.reviewed_at,
                )
            )

        return ReviewHistoryListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
