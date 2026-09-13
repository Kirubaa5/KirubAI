from datetime import datetime, timezone, timedelta, date
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.practice import PracticeSession, PracticeAttempt, ReviewRecord, ConversationSession
from models.user import User
from schemas.dashboard import (
    WordOfTheDay,
    DashboardToday,
    DashboardStats,
    DashboardRecentActivityItem,
    DashboardSummaryResponse,
)

CURATED_WORDS_OF_THE_DAY = [
    {
        "word": "resilient",
        "meaning": "Able to withstand or recover quickly from difficult conditions; adaptable and strong.",
        "cefr_level": "B2",
        "part_of_speech": "adjective",
        "example_sentence": "She remained resilient throughout the rigorous project challenges.",
    },
    {
        "word": "articulate",
        "meaning": "Having or showing the ability to speak fluently, clearly, and coherently.",
        "cefr_level": "B2",
        "part_of_speech": "adjective",
        "example_sentence": "He gave an articulate explanation of the engineering roadmap.",
    },
    {
        "word": "pragmatic",
        "meaning": "Dealing with things sensibly and realistically based on practical considerations.",
        "cefr_level": "C1",
        "part_of_speech": "adjective",
        "example_sentence": "We adopted a pragmatic approach to resolve the technical constraints.",
    },
    {
        "word": "meticulous",
        "meaning": "Showing great attention to detail; very careful and precise.",
        "cefr_level": "C1",
        "part_of_speech": "adjective",
        "example_sentence": "The team conducted a meticulous code review before shipping the release.",
    },
    {
        "word": "elucidate",
        "meaning": "To make something clear and easy to understand; to explain in depth.",
        "cefr_level": "C1",
        "part_of_speech": "verb",
        "example_sentence": "The architect elucidated the system architecture with clear diagrams.",
    },
    {
        "word": "ubiquitous",
        "meaning": "Present, appearing, or found everywhere at the same time.",
        "cefr_level": "C1",
        "part_of_speech": "adjective",
        "example_sentence": "Cloud services have become ubiquitous across modern technology companies.",
    },
    {
        "word": "candid",
        "meaning": "Truthful, straightforward, and sincere in expression; frank.",
        "cefr_level": "B2",
        "part_of_speech": "adjective",
        "example_sentence": "They held a candid discussion to address the project blockers.",
    },
]


def to_utc_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    return None


def calculate_user_streak(db: Session, user: User) -> int:
    """
    Deterministic streak calculation based on user activity timestamps and user model data.
    """
    now = datetime.now(timezone.utc)
    today = now.date()
    yesterday = today - timedelta(days=1)

    # Gather distinct dates of activity for the user
    active_dates: Set[date] = set()

    # 1. Practice attempts
    attempts = (
        db.query(PracticeAttempt.created_at)
        .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
        .filter(PracticeSession.user_id == user.id)
        .all()
    )
    for (created_at,) in attempts:
        if created_at:
            active_dates.add(created_at.date() if isinstance(created_at, datetime) else created_at)

    # 2. Review records
    reviews = (
        db.query(ReviewRecord.reviewed_at)
        .filter(ReviewRecord.user_id == user.id)
        .all()
    )
    for (reviewed_at,) in reviews:
        if reviewed_at:
            active_dates.add(reviewed_at.date() if isinstance(reviewed_at, datetime) else reviewed_at)

    # 3. Conversations
    conversations = (
        db.query(ConversationSession.started_at)
        .filter(ConversationSession.user_id == user.id)
        .all()
    )
    for (started_at,) in conversations:
        if started_at:
            active_dates.add(started_at.date() if isinstance(started_at, datetime) else started_at)

    # 4. Vocabulary added
    vocabs = (
        db.query(Vocabulary.created_at)
        .filter(Vocabulary.user_id == user.id)
        .all()
    )
    for (created_at,) in vocabs:
        if created_at:
            active_dates.add(created_at.date() if isinstance(created_at, datetime) else created_at)

    # If no activity dates found, return user.current_streak or 0
    if not active_dates:
        return user.current_streak or 0

    # If neither today nor yesterday has activity, streak is broken
    if today not in active_dates and yesterday not in active_dates:
        # Check if user.last_active_date bridges it
        if user.last_active_date and (today - user.last_active_date).days <= 1:
            return user.current_streak
        return 0

    # Calculate consecutive days backward
    start_date = today if today in active_dates else yesterday
    current_consecutive = 0
    check_date = start_date

    while check_date in active_dates:
        current_consecutive += 1
        check_date -= timedelta(days=1)

    return max(current_consecutive, user.current_streak or 0)


class DashboardService:
    @staticmethod
    def get_dashboard_summary(db: Session, user: User) -> DashboardSummaryResponse:
        """
        Generate deterministic dashboard summary scoped to the authenticated user.
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. Vocabulary metrics
        all_vocabs = (
            db.query(Vocabulary)
            .filter(Vocabulary.user_id == user.id)
            .all()
        )
        total_words = len(all_vocabs)
        mastered_words = sum(1 for v in all_vocabs if v.status == "mastered")
        active_words = sum(
            1 for v in all_vocabs if v.status in ("learned", "practiced", "recalled", "reinforced")
        )
        struggling_words = sum(1 for v in all_vocabs if v.status == "struggling")

        # 2. Reviews due
        reviews_due_count = sum(
            1
            for v in all_vocabs
            if v.status in ("learned", "practiced", "recalled", "reinforced", "mastered", "struggling")
            and (v.next_review_at is None or to_utc_datetime(v.next_review_at) <= now)
        )

        # 3. Words to practice
        words_to_practice_count = sum(
            1 for v in all_vocabs if v.status in ("new", "learned", "struggling")
        )

        # 4. Daily goal progress (practices + reviews + conversations + new words added today)
        practice_attempts_today = (
            db.query(func.count(PracticeAttempt.id))
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(
                PracticeSession.user_id == user.id,
                PracticeAttempt.created_at >= today_start,
            )
            .scalar()
            or 0
        )

        reviews_today = (
            db.query(func.count(ReviewRecord.id))
            .filter(
                ReviewRecord.user_id == user.id,
                ReviewRecord.reviewed_at >= today_start,
            )
            .scalar()
            or 0
        )

        conversations_today = (
            db.query(func.count(ConversationSession.id))
            .filter(
                ConversationSession.user_id == user.id,
                ConversationSession.started_at >= today_start,
            )
            .scalar()
            or 0
        )

        words_added_today = sum(
            1 for v in all_vocabs if v.created_at and to_utc_datetime(v.created_at) >= today_start
        )

        daily_goal_progress = (
            practice_attempts_today
            + reviews_today
            + conversations_today
            + words_added_today
        )

        # 5. Deterministic Word of the Day
        word_of_the_day: Optional[WordOfTheDay] = None
        date_hash = int(now.strftime("%Y%m%d"))

        if all_vocabs:
            # Prioritize struggling words, then new/learned, then all
            candidates = [v for v in all_vocabs if v.status == "struggling"]
            if not candidates:
                candidates = [v for v in all_vocabs if v.status in ("new", "learned")]
            if not candidates:
                candidates = all_vocabs

            selected_vocab = candidates[date_hash % len(candidates)]
            meaning = (
                selected_vocab.details.simple_meaning
                if selected_vocab.details
                else f"Vocabulary word: '{selected_vocab.word}'"
            )
            cefr = (
                selected_vocab.details.cefr_level
                if selected_vocab.details
                else None
            )
            pos = (
                selected_vocab.details.part_of_speech
                if selected_vocab.details
                else None
            )
            ex_sentence = (
                selected_vocab.examples[0].example_text
                if selected_vocab.examples
                else None
            )

            word_of_the_day = WordOfTheDay(
                word=selected_vocab.word,
                meaning=meaning,
                cefr_level=cefr,
                part_of_speech=pos,
                example_sentence=ex_sentence,
            )
        else:
            # Curated fallback for users who haven't added words yet
            curated = CURATED_WORDS_OF_THE_DAY[date_hash % len(CURATED_WORDS_OF_THE_DAY)]
            word_of_the_day = WordOfTheDay(
                word=curated["word"],
                meaning=curated["meaning"],
                cefr_level=curated["cefr_level"],
                part_of_speech=curated["part_of_speech"],
                example_sentence=curated["example_sentence"],
            )

        # 6. Streak calculation
        current_streak = calculate_user_streak(db=db, user=user)

        # 7. Recent activity timeline
        recent_activity: List[DashboardRecentActivityItem] = []

        # Practice attempts
        recent_attempts = (
            db.query(PracticeAttempt, Vocabulary.word)
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .join(Vocabulary, PracticeAttempt.vocabulary_id == Vocabulary.id)
            .filter(PracticeSession.user_id == user.id)
            .order_by(desc(PracticeAttempt.created_at))
            .limit(10)
            .all()
        )
        for attempt, vocab_word in recent_attempts:
            recent_activity.append(
                DashboardRecentActivityItem(
                    type="practice",
                    word=vocab_word,
                    score=attempt.overall_score,
                    result="success" if attempt.is_successful else "needs_work",
                    at=attempt.created_at,
                    detail=f"Scenario practice scored {attempt.overall_score}/10",
                )
            )

        # Review records
        recent_reviews = (
            db.query(ReviewRecord, Vocabulary.word)
            .join(Vocabulary, ReviewRecord.vocabulary_id == Vocabulary.id)
            .filter(ReviewRecord.user_id == user.id)
            .order_by(desc(ReviewRecord.reviewed_at))
            .limit(10)
            .all()
        )
        for review, vocab_word in recent_reviews:
            recent_activity.append(
                DashboardRecentActivityItem(
                    type="review",
                    word=vocab_word,
                    score=review.score,
                    result="success" if review.recall_successful else "needs_work",
                    at=review.reviewed_at,
                    detail=f"Spaced repetition recall ({'Passed' if review.recall_successful else 'Failed'})",
                )
            )

        # Conversations
        recent_convos = (
            db.query(ConversationSession)
            .filter(ConversationSession.user_id == user.id)
            .order_by(desc(ConversationSession.started_at))
            .limit(10)
            .all()
        )
        for convo in recent_convos:
            recent_activity.append(
                DashboardRecentActivityItem(
                    type="conversation",
                    word=convo.topic or "English Conversation",
                    score=None,
                    result="completed" if convo.status == "ended" else "active",
                    at=convo.started_at,
                    detail=f"AI chat session ({convo.vocabulary_usage_count} vocabulary used)",
                )
            )

        # Vocabulary additions
        recent_vocab_additions = (
            db.query(Vocabulary)
            .filter(Vocabulary.user_id == user.id)
            .order_by(desc(Vocabulary.created_at))
            .limit(10)
            .all()
        )
        for v in recent_vocab_additions:
            recent_activity.append(
                DashboardRecentActivityItem(
                    type="vocabulary",
                    word=v.word,
                    score=None,
                    result=v.status,
                    at=v.created_at,
                    detail=f"Added '{v.word}' to vocabulary",
                )
            )

        # Sort all activities by timestamp descending and take top 10
        recent_activity.sort(key=lambda a: to_utc_datetime(a.at) or now, reverse=True)
        recent_activity = recent_activity[:10]

        return DashboardSummaryResponse(
            today=DashboardToday(
                reviews_due=reviews_due_count,
                words_to_practice=words_to_practice_count,
                daily_goal_progress=daily_goal_progress,
                daily_goal_target=user.daily_goal or 5,
                word_of_the_day=word_of_the_day,
            ),
            stats=DashboardStats(
                total_words=total_words,
                mastered_words=mastered_words,
                active_words=active_words,
                struggling_words=struggling_words,
                current_streak=current_streak,
                total_xp=user.xp or 0,
                level=user.level or 1,
            ),
            recent_activity=recent_activity,
        )
