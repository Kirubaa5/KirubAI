from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from models.vocabulary import Vocabulary
from models.practice import PracticeSession, PracticeAttempt
from models.user import User
from ai.provider import LLMProvider
from ai.schemas import ScenarioAI, EvaluationAI
from ai.prompts.scenario import build_scenario_prompt, SCENARIO_SYSTEM_PROMPT
from ai.prompts.evaluation import build_evaluation_prompt, EVALUATION_SYSTEM_PROMPT
from services.learning_service import get_llm_provider


def calculate_overall_score(
    vocabulary_usage: float,
    grammar: float,
    context: float,
    naturalness: float,
) -> float:
    """Calculate deterministic weighted overall score."""
    weighted = (
        vocabulary_usage * 0.30
        + grammar * 0.20
        + context * 0.25
        + naturalness * 0.25
    )
    return round(weighted, 1)


def is_attempt_successful(
    overall_score: float,
    vocab_usage_score: float,
    vocab_used_correctly: bool = True,
) -> bool:
    """A practice attempt is successful if overall_score >= 6.0 and vocab_usage >= 5.0."""
    return overall_score >= 6.0 and vocab_usage_score >= 5.0 and vocab_used_correctly


class PracticeService:
    @staticmethod
    async def start_session(
        db: Session,
        user: User,
        vocabulary_id: str,
        session_type: str = "scenario",
        llm: Optional[LLMProvider] = None,
    ) -> Tuple[PracticeSession, ScenarioAI]:
        """Start a new practice session and generate the first scenario."""
        vocab = db.query(Vocabulary).filter(
            Vocabulary.id == vocabulary_id,
            Vocabulary.user_id == user.id,
        ).first()

        if not vocab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary word not found",
            )

        provider = llm or get_llm_provider()

        meaning = vocab.details.simple_meaning if vocab.details else None
        cefr = vocab.details.cefr_level if vocab.details else None

        scenario: ScenarioAI = await provider.generate_structured(
            prompt=build_scenario_prompt(
                word=vocab.word,
                word_meaning=meaning,
                cefr_level=cefr,
            ),
            response_schema=ScenarioAI,
            system_prompt=SCENARIO_SYSTEM_PROMPT,
            temperature=0.7,
        )

        practice_session = PracticeSession(
            user_id=user.id,
            vocabulary_id=vocab.id,
            session_type=session_type,
            status="active",
            total_attempts=0,
            successful_attempts=0,
            average_score=None,
        )
        db.add(practice_session)
        db.commit()
        db.refresh(practice_session)

        return practice_session, scenario

    @staticmethod
    async def generate_scenario(
        db: Session,
        user: User,
        session_id: str,
        llm: Optional[LLMProvider] = None,
    ) -> ScenarioAI:
        """Generate a new scenario for an ongoing practice session."""
        session = db.query(PracticeSession).filter(
            PracticeSession.id == session_id,
            PracticeSession.user_id == user.id,
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice session not found",
            )

        vocab = session.vocabulary
        meaning = vocab.details.simple_meaning if vocab.details else None
        cefr = vocab.details.cefr_level if vocab.details else None

        provider = llm or get_llm_provider()

        scenario: ScenarioAI = await provider.generate_structured(
            prompt=build_scenario_prompt(
                word=vocab.word,
                word_meaning=meaning,
                cefr_level=cefr,
            ),
            response_schema=ScenarioAI,
            system_prompt=SCENARIO_SYSTEM_PROMPT,
            temperature=0.7,
        )

        return scenario

    @staticmethod
    async def submit_attempt(
        db: Session,
        user: User,
        session_id: str,
        scenario_text: str,
        user_response: str,
        llm: Optional[LLMProvider] = None,
    ) -> Tuple[PracticeAttempt, str]:
        """Submit and evaluate a user response for a scenario in a practice session."""
        session = db.query(PracticeSession).filter(
            PracticeSession.id == session_id,
            PracticeSession.user_id == user.id,
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice session not found",
            )

        if session.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot submit to a completed practice session",
            )

        vocab = session.vocabulary
        provider = llm or get_llm_provider()

        # Generate structured evaluation via AI provider
        eval_ai: EvaluationAI = await provider.generate_structured(
            prompt=build_evaluation_prompt(
                word=vocab.word,
                scenario_text=scenario_text,
                user_response=user_response,
            ),
            response_schema=EvaluationAI,
            system_prompt=EVALUATION_SYSTEM_PROMPT,
            temperature=0.3,
        )

        # Enforce application-level deterministic scoring logic
        overall_score = calculate_overall_score(
            vocabulary_usage=eval_ai.vocabulary_usage_score,
            grammar=eval_ai.grammar_score,
            context=eval_ai.context_score,
            naturalness=eval_ai.naturalness_score,
        )

        successful = is_attempt_successful(
            overall_score=overall_score,
            vocab_usage_score=eval_ai.vocabulary_usage_score,
            vocab_used_correctly=eval_ai.vocabulary_used_correctly,
        )

        # Create practice attempt
        attempt = PracticeAttempt(
            session_id=session.id,
            vocabulary_id=vocab.id,
            scenario_text=scenario_text,
            user_response=user_response,
            vocabulary_usage_score=eval_ai.vocabulary_usage_score,
            grammar_score=eval_ai.grammar_score,
            context_score=eval_ai.context_score,
            naturalness_score=eval_ai.naturalness_score,
            overall_score=overall_score,
            feedback=eval_ai.feedback,
            improved_version=eval_ai.improved_version,
            is_successful=successful,
        )
        db.add(attempt)

        # Update session metrics
        session.total_attempts += 1
        if successful:
            session.successful_attempts += 1

        # Update session average score
        all_attempts_scores = [a.overall_score for a in session.attempts] + [overall_score]
        session.average_score = round(sum(all_attempts_scores) / len(all_attempts_scores), 2)

        # Update vocabulary metrics and state machine
        vocab.practice_count += 1
        vocab.last_practiced_at = datetime.now(timezone.utc)

        if successful:
            vocab.successful_usage_count += 1
            if vocab.status in ("new", "learned", "struggling"):
                vocab.status = "practiced"

            practice_rate = vocab.successful_usage_count / max(vocab.practice_count, 1)
            vocab.mastery_score = min(1.0, round(0.25 * practice_rate + 0.15, 2))
            user.xp += 15
            user.level = max(1, (user.xp // 100) + 1)
            if vocab.next_review_at is None:
                vocab.next_review_at = datetime.now(timezone.utc) + timedelta(days=vocab.review_interval_days or 1)
        else:
            user.xp += 5
            user.level = max(1, (user.xp // 100) + 1)

        db.commit()
        db.refresh(attempt)
        db.refresh(session)
        db.refresh(vocab)

        return attempt, vocab.word

    @staticmethod
    def get_session(
        db: Session,
        user: User,
        session_id: str,
    ) -> PracticeSession:
        """Get practice session details with attempts."""
        session = db.query(PracticeSession).filter(
            PracticeSession.id == session_id,
            PracticeSession.user_id == user.id,
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice session not found",
            )

        return session

    @staticmethod
    def list_sessions(
        db: Session,
        user: User,
        vocabulary_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[PracticeSession], int]:
        """List practice sessions for the user with optional vocabulary filter."""
        query = db.query(PracticeSession).filter(PracticeSession.user_id == user.id)

        if vocabulary_id:
            query = query.filter(PracticeSession.vocabulary_id == vocabulary_id)

        total = query.count()
        sessions = (
            query.order_by(desc(PracticeSession.started_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return sessions, total

    @staticmethod
    def complete_session(
        db: Session,
        user: User,
        session_id: str,
    ) -> PracticeSession:
        """Mark a practice session as completed."""
        session = db.query(PracticeSession).filter(
            PracticeSession.id == session_id,
            PracticeSession.user_id == user.id,
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice session not found",
            )

        if session.status != "completed":
            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(session)

        return session
