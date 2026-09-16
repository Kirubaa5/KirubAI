import math
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas.practice import (
    PracticeStartRequest,
    PracticeStartResponse,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
    PracticeAttemptResponse,
    PracticeSessionResponse,
    PracticeSessionListResponse,
    PracticeScoresSchema,
    ScenarioSchema,
)
from schemas.daily import (
    MultiWordStartRequest,
    MultiWordStartResponse,
    MultiWordSubmitRequest,
    MultiWordAttemptResponse,
    MultiWordSessionResponse,
    MultiWordSessionListResponse,
    MultiWordEligibleResponse,
    MultiWordTargetWordSchema,
    WordEvaluationDetailSchema,
)
from services.practice_service import PracticeService
from services.daily_service import DailyLearningService
from middleware.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/practice", tags=["practice"])


def format_attempt_response(attempt, target_word: str) -> PracticeAttemptResponse:
    return PracticeAttemptResponse(
        id=attempt.id,
        session_id=attempt.session_id,
        vocabulary_id=attempt.vocabulary_id,
        target_word=target_word,
        scenario_text=attempt.scenario_text,
        user_response=attempt.user_response,
        scores=PracticeScoresSchema(
            vocabulary_usage=attempt.vocabulary_usage_score,
            grammar=attempt.grammar_score,
            context=attempt.context_score,
            naturalness=attempt.naturalness_score,
            overall=attempt.overall_score,
        ),
        feedback=attempt.feedback,
        improved_version=attempt.improved_version,
        is_successful=attempt.is_successful,
        created_at=attempt.created_at,
    )


def format_session_response(session) -> PracticeSessionResponse:
    word = session.vocabulary.word if session.vocabulary else None
    formatted_attempts = [
        format_attempt_response(att, word or "")
        for att in session.attempts
    ]
    return PracticeSessionResponse(
        id=session.id,
        user_id=session.user_id,
        vocabulary_id=session.vocabulary_id,
        target_word=word,
        session_type=session.session_type,
        status=session.status,
        total_attempts=session.total_attempts,
        successful_attempts=session.successful_attempts,
        average_score=session.average_score,
        started_at=session.started_at,
        completed_at=session.completed_at,
        attempts=formatted_attempts,
    )


def format_multi_word_attempt_response(attempt, xp_earned: int = 0) -> MultiWordAttemptResponse:
    return MultiWordAttemptResponse(
        id=attempt.id,
        session_id=attempt.session_id,
        user_response=attempt.user_response,
        scores=PracticeScoresSchema(
            vocabulary_usage=attempt.vocabulary_usage_score,
            grammar=attempt.grammar_score,
            context=attempt.context_score,
            naturalness=attempt.naturalness_score,
            overall=attempt.overall_score,
        ),
        word_evaluations=[
            WordEvaluationDetailSchema(
                word=we.get("word", ""),
                used=we.get("used", False),
                used_correctly=we.get("used_correctly", False),
                used_naturally=we.get("used_naturally", False),
                score=we.get("score"),
                feedback=we.get("feedback", ""),
            )
            for we in (attempt.word_evaluations or [])
        ],
        feedback=attempt.feedback,
        improved_version=attempt.improved_version,
        is_successful=attempt.is_successful,
        xp_earned=xp_earned if xp_earned > 0 else (20 if attempt.is_successful else 5),
        created_at=attempt.created_at,
    )


def format_multi_word_session_response(session) -> MultiWordSessionResponse:
    formatted_attempts = [
        format_multi_word_attempt_response(att)
        for att in session.attempts
    ]
    return MultiWordSessionResponse(
        id=session.id,
        user_id=session.user_id,
        target_words=session.target_words or [],
        target_vocabulary_ids=session.target_vocabulary_ids or [],
        scenario_text=session.situation,
        scenario_prompt=session.prompt,
        context_hint=session.context_hint,
        status=session.status,
        total_attempts=session.total_attempts,
        successful_attempts=session.successful_attempts,
        average_score=session.average_score,
        started_at=session.started_at,
        completed_at=session.completed_at,
        attempts=formatted_attempts,
    )


# =============================================================================
# Use My Vocabulary (Multi-Word Practice) Routes
# =============================================================================

@router.get("/multi-word/eligible", response_model=MultiWordEligibleResponse)
def get_eligible_multi_word_vocabulary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch user's vocabulary words that are eligible for multi-word practice."""
    return DailyLearningService.get_eligible_vocabulary(db=db, user=current_user)


@router.get("/multi-word/sessions", response_model=MultiWordSessionListResponse)
def list_multi_word_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List multi-word practice sessions for the current user."""
    sessions, total = DailyLearningService.list_multi_word_sessions(
        db=db,
        user=current_user,
        page=page,
        per_page=per_page,
    )
    pages = math.ceil(total / per_page) if total > 0 else 1
    return MultiWordSessionListResponse(
        items=[format_multi_word_session_response(s) for s in sessions],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.post("/multi-word", response_model=MultiWordStartResponse, status_code=status.HTTP_201_CREATED)
async def start_multi_word_practice(
    data: Optional[MultiWordStartRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a multi-word synthesis practice session ("Use My Vocabulary").
    Selects 3-5 eligible vocabulary words and generates a cohesive scenario.
    """
    vocab_ids = data.vocabulary_ids if data else None
    session, scenario, selected_vocabs = await DailyLearningService.start_multi_word_session(
        db=db,
        user=current_user,
        vocabulary_ids=vocab_ids,
    )
    return MultiWordStartResponse(
        session_id=session.id,
        target_words=[
            MultiWordTargetWordSchema(
                id=v.id,
                word=v.word,
                meaning=v.details.simple_meaning if v.details else None,
                cefr_level=v.details.cefr_level if v.details else None,
                status=v.status,
            )
            for v in selected_vocabs
        ],
        scenario=ScenarioSchema(
            situation=scenario.situation,
            prompt=scenario.prompt,
            context_hint=scenario.context_hint,
        ),
        created_at=session.started_at,
    )


@router.get("/multi-word/{session_id}", response_model=MultiWordSessionResponse)
def get_multi_word_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific multi-word practice session and its attempts."""
    session = DailyLearningService.get_multi_word_session(
        db=db,
        user=current_user,
        session_id=session_id,
    )
    return format_multi_word_session_response(session)


@router.post("/multi-word/{session_id}/submit", response_model=MultiWordAttemptResponse)
async def submit_multi_word_attempt(
    session_id: str,
    data: MultiWordSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a user's response to a multi-word practice scenario.
    Evaluates each target word individually and provides comprehensive feedback.
    """
    attempt, session, xp_earned = await DailyLearningService.submit_multi_word_attempt(
        db=db,
        user=current_user,
        session_id=session_id,
        user_response=data.response,
    )
    return format_multi_word_attempt_response(attempt, xp_earned=xp_earned)



@router.post("/start", response_model=PracticeStartResponse, status_code=status.HTTP_201_CREATED)
async def start_practice_session(
    data: PracticeStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a new practice session for a vocabulary word and generate a scenario."""
    session, scenario = await PracticeService.start_session(
        db=db,
        user=current_user,
        vocabulary_id=data.vocabulary_id,
        session_type=data.session_type or "scenario",
    )
    return PracticeStartResponse(
        session_id=session.id,
        vocabulary_id=session.vocabulary_id,
        target_word=session.vocabulary.word,
        scenario=ScenarioSchema(
            situation=scenario.situation,
            prompt=scenario.prompt,
            context_hint=scenario.context_hint,
        ),
    )


@router.post("/{session_id}/scenario", response_model=ScenarioSchema)
async def generate_new_scenario(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a new scenario for an ongoing practice session."""
    scenario = await PracticeService.generate_scenario(
        db=db,
        user=current_user,
        session_id=session_id,
    )
    return ScenarioSchema(
        situation=scenario.situation,
        prompt=scenario.prompt,
        context_hint=scenario.context_hint,
    )


@router.post("/{session_id}/submit", response_model=PracticeSubmitResponse)
async def submit_practice_attempt(
    session_id: str,
    data: PracticeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a response to a scenario, evaluate via AI, and persist attempt."""
    attempt, target_word = await PracticeService.submit_attempt(
        db=db,
        user=current_user,
        session_id=session_id,
        scenario_text=data.scenario_text,
        user_response=data.response,
    )

    formatted_attempt = format_attempt_response(attempt, target_word)

    return PracticeSubmitResponse(
        attempt_id=attempt.id,
        session_id=attempt.session_id,
        vocabulary_id=attempt.vocabulary_id,
        target_word=target_word,
        scenario_text=attempt.scenario_text,
        user_response=attempt.user_response,
        scores=formatted_attempt.scores,
        feedback=attempt.feedback,
        improved_version=attempt.improved_version,
        is_successful=attempt.is_successful,
        can_continue=True,
        next_scenario=None,
    )


@router.get("/sessions", response_model=PracticeSessionListResponse)
def list_practice_sessions(
    vocabulary_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List practice sessions for the current user."""
    sessions, total = PracticeService.list_sessions(
        db=db,
        user=current_user,
        vocabulary_id=vocabulary_id,
        page=page,
        per_page=per_page,
    )
    pages = math.ceil(total / per_page) if total > 0 else 1
    return PracticeSessionListResponse(
        items=[format_session_response(s) for s in sessions],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{session_id}", response_model=PracticeSessionResponse)
def get_practice_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific practice session and its attempts."""
    session = PracticeService.get_session(
        db=db,
        user=current_user,
        session_id=session_id,
    )
    return format_session_response(session)


@router.post("/{session_id}/complete", response_model=PracticeSessionResponse)
def complete_practice_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a practice session as completed."""
    session = PracticeService.complete_session(
        db=db,
        user=current_user,
        session_id=session_id,
    )
    return format_session_response(session)
