from datetime import datetime, timezone, timedelta, date
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models.vocabulary import Vocabulary, WordDetails
from models.practice import PracticeSession, PracticeAttempt, ReviewRecord, ConversationSession
from models.user import User
from schemas.progress import (
    VocabularyBreakdownItem,
    MasteryBracketItem,
    VocabularyBreakdownResponse,
    DailyProgressItem,
    WeeklyProgressResponse,
    MonthlyTrendItem,
    MonthlyProgressResponse,
    ProgressOverviewResponse,
)
from services.dashboard_service import calculate_user_streak


class ProgressService:
    @staticmethod
    def get_overview(db: Session, user: User) -> ProgressOverviewResponse:
        """
        Overall learning progress analytics scoped to the authenticated user.
        """
        # 1. Vocabulary metrics
        vocabularies = (
            db.query(Vocabulary)
            .filter(Vocabulary.user_id == user.id)
            .all()
        )
        total_vocab = len(vocabularies)
        active_vocab = sum(
            1 for v in vocabularies if v.status in ("learned", "practiced", "recalled", "reinforced")
        )
        mastered_count = sum(1 for v in vocabularies if v.status == "mastered")
        struggling_count = sum(1 for v in vocabularies if v.status == "struggling")
        total_mastery = sum(v.mastery_score or 0.0 for v in vocabularies)
        avg_mastery = round(total_mastery / total_vocab, 3) if total_vocab > 0 else 0.0

        # 2. Practice attempts
        attempts = (
            db.query(PracticeAttempt)
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(PracticeSession.user_id == user.id)
            .all()
        )
        total_attempts = len(attempts)
        successful_attempts = sum(1 for a in attempts if a.is_successful)
        practice_accuracy = (
            round(successful_attempts / total_attempts, 3) if total_attempts > 0 else 0.0
        )
        avg_practice_score = (
            round(sum(a.overall_score for a in attempts) / total_attempts, 2)
            if total_attempts > 0
            else 0.0
        )

        # 3. Review records
        reviews = (
            db.query(ReviewRecord)
            .filter(ReviewRecord.user_id == user.id)
            .all()
        )
        total_reviews = len(reviews)
        successful_reviews = sum(1 for r in reviews if r.recall_successful)
        recall_accuracy = (
            round(successful_reviews / total_reviews, 3) if total_reviews > 0 else 0.0
        )

        # 4. Conversation sessions
        conversations = (
            db.query(ConversationSession)
            .filter(ConversationSession.user_id == user.id)
            .all()
        )
        total_conversations = len(conversations)
        vocab_used_in_convos = sum(c.vocabulary_usage_count or 0 for c in conversations)

        # 5. Streak & level
        current_streak = calculate_user_streak(db=db, user=user)
        longest_streak = max(user.longest_streak or 0, current_streak)

        return ProgressOverviewResponse(
            total_vocabulary=total_vocab,
            active_vocabulary=active_vocab,
            mastered_count=mastered_count,
            struggling_count=struggling_count,
            average_mastery=avg_mastery,
            total_practice_attempts=total_attempts,
            practice_accuracy=practice_accuracy,
            average_practice_score=avg_practice_score,
            total_reviews_completed=total_reviews,
            recall_accuracy_rate=recall_accuracy,
            total_conversations=total_conversations,
            vocabulary_used_in_conversations=vocab_used_in_convos,
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_xp=user.xp or 0,
            level=user.level or 1,
            daily_goal=user.daily_goal or 5,
        )

    @staticmethod
    def get_weekly(db: Session, user: User) -> WeeklyProgressResponse:
        """
        7-day learning activity, accuracy, and trends.
        """
        now = datetime.now(timezone.utc)
        today = now.date()

        # Fetch all user data in last 7 days window
        window_start = datetime.combine(today - timedelta(days=6), datetime.min.time(), tzinfo=timezone.utc)

        attempts = (
            db.query(PracticeAttempt)
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(
                PracticeSession.user_id == user.id,
                PracticeAttempt.created_at >= window_start,
            )
            .all()
        )

        reviews = (
            db.query(ReviewRecord)
            .filter(
                ReviewRecord.user_id == user.id,
                ReviewRecord.reviewed_at >= window_start,
            )
            .all()
        )

        conversations = (
            db.query(ConversationSession)
            .filter(
                ConversationSession.user_id == user.id,
                ConversationSession.started_at >= window_start,
            )
            .all()
        )

        vocabs = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.user_id == user.id,
                Vocabulary.created_at >= window_start,
            )
            .all()
        )

        # Build 7 daily data points
        daily_items: List[DailyProgressItem] = []
        total_p = 0
        total_r = 0
        total_c = 0
        total_w = 0
        total_xp = 0
        successful_actions = 0
        total_actions = 0
        active_days_count = 0

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for day_offset in range(6, -1, -1):
            target_date = today - timedelta(days=day_offset)
            date_str = target_date.strftime("%Y-%m-%d")
            day_name = day_names[target_date.weekday()]

            # Filter records matching target_date
            day_attempts = [
                a for a in attempts
                if a.created_at and (a.created_at.date() if isinstance(a.created_at, datetime) else a.created_at) == target_date
            ]
            day_reviews = [
                r for r in reviews
                if r.reviewed_at and (r.reviewed_at.date() if isinstance(r.reviewed_at, datetime) else r.reviewed_at) == target_date
            ]
            day_convos = [
                c for c in conversations
                if c.started_at and (c.started_at.date() if isinstance(c.started_at, datetime) else c.started_at) == target_date
            ]
            day_vocabs = [
                v for v in vocabs
                if v.created_at and (v.created_at.date() if isinstance(v.created_at, datetime) else v.created_at) == target_date
            ]

            p_count = len(day_attempts)
            r_count = len(day_reviews)
            c_count = len(day_convos)
            w_count = len(day_vocabs)

            p_success = sum(1 for a in day_attempts if a.is_successful)
            r_success = sum(1 for r in day_reviews if r.recall_successful)
            mastered_count = sum(1 for r in day_reviews if r.new_status == "mastered")

            action_total = p_count + r_count
            action_success = p_success + r_success
            accuracy = round(action_success / action_total, 2) if action_total > 0 else 0.0

            # XP calculation: 10 per successful review, 3 per failed review, 10 per practice attempt, 15 per conversation
            xp = (
                (r_success * 10)
                + ((r_count - r_success) * 3)
                + (p_count * 10)
                + (c_count * 15)
            )

            if (p_count + r_count + c_count + w_count) > 0:
                active_days_count += 1

            total_p += p_count
            total_r += r_count
            total_c += c_count
            total_w += w_count
            total_xp += xp
            successful_actions += action_success
            total_actions += action_total

            daily_items.append(
                DailyProgressItem(
                    date=date_str,
                    day_name=day_name,
                    practices_count=p_count,
                    reviews_count=r_count,
                    conversations_count=c_count,
                    words_added=w_count,
                    words_mastered=mastered_count,
                    accuracy_rate=accuracy,
                    xp_earned=xp,
                )
            )

        avg_acc = (
            round(successful_actions / total_actions, 2) if total_actions > 0 else 0.0
        )

        return WeeklyProgressResponse(
            daily_progress=daily_items,
            total_practices=total_p,
            total_reviews=total_r,
            total_conversations=total_c,
            total_words_added=total_w,
            total_xp_earned=total_xp,
            average_accuracy_rate=avg_acc,
            active_days=active_days_count,
        )

    @staticmethod
    def get_monthly(db: Session, user: User) -> MonthlyProgressResponse:
        """
        Monthly learning trends over the last 30 days.
        """
        now = datetime.now(timezone.utc)
        today = now.date()
        window_start = datetime.combine(today - timedelta(days=29), datetime.min.time(), tzinfo=timezone.utc)

        attempts = (
            db.query(PracticeAttempt)
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(
                PracticeSession.user_id == user.id,
                PracticeAttempt.created_at >= window_start,
            )
            .all()
        )

        reviews = (
            db.query(ReviewRecord)
            .filter(
                ReviewRecord.user_id == user.id,
                ReviewRecord.reviewed_at >= window_start,
            )
            .all()
        )

        conversations = (
            db.query(ConversationSession)
            .filter(
                ConversationSession.user_id == user.id,
                ConversationSession.started_at >= window_start,
            )
            .all()
        )

        vocabs_in_window = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.user_id == user.id,
                Vocabulary.created_at >= window_start,
            )
            .all()
        )

        all_user_vocabs = (
            db.query(Vocabulary)
            .filter(Vocabulary.user_id == user.id)
            .all()
        )
        words_learned_count = sum(
            1 for v in all_user_vocabs if v.status in ("learned", "practiced", "recalled", "reinforced", "mastered")
        )

        trends: List[MonthlyTrendItem] = []
        total_activities = 0
        total_success = 0
        total_actions = 0
        active_days = 0

        for day_offset in range(29, -1, -1):
            target_date = today - timedelta(days=day_offset)
            date_str = target_date.strftime("%Y-%m-%d")
            day_label = target_date.strftime("%b %d")

            day_attempts = [
                a for a in attempts
                if a.created_at and (a.created_at.date() if isinstance(a.created_at, datetime) else a.created_at) == target_date
            ]
            day_reviews = [
                r for r in reviews
                if r.reviewed_at and (r.reviewed_at.date() if isinstance(r.reviewed_at, datetime) else r.reviewed_at) == target_date
            ]
            day_convos = [
                c for c in conversations
                if c.started_at and (c.started_at.date() if isinstance(c.started_at, datetime) else c.started_at) == target_date
            ]
            day_vocabs = [
                v for v in vocabs_in_window
                if v.created_at and (v.created_at.date() if isinstance(v.created_at, datetime) else v.created_at) == target_date
            ]

            p_count = len(day_attempts)
            r_count = len(day_reviews)
            c_count = len(day_convos)
            w_count = len(day_vocabs)
            act_count = p_count + r_count + c_count + w_count

            p_success = sum(1 for a in day_attempts if a.is_successful)
            r_success = sum(1 for r in day_reviews if r.recall_successful)

            action_total = p_count + r_count
            action_success = p_success + r_success
            accuracy = round(action_success / action_total, 2) if action_total > 0 else 0.0

            xp = (
                (r_success * 10)
                + ((r_count - r_success) * 3)
                + (p_count * 10)
                + (c_count * 15)
            )

            if act_count > 0:
                active_days += 1

            total_activities += act_count
            total_success += action_success
            total_actions += action_total

            trends.append(
                MonthlyTrendItem(
                    date=date_str,
                    day_or_week=day_label,
                    activities_count=act_count,
                    words_acquired=w_count,
                    accuracy_rate=accuracy,
                    xp_earned=xp,
                )
            )

        avg_acc = (
            round(total_success / total_actions, 2) if total_actions > 0 else 0.0
        )
        total_monthly_reviews = len(reviews)
        successful_monthly_reviews = sum(1 for r in reviews if r.recall_successful)
        retention_rate = (
            round(successful_monthly_reviews / total_monthly_reviews, 2)
            if total_monthly_reviews > 0
            else 0.0
        )

        return MonthlyProgressResponse(
            trends=trends,
            total_activities=total_activities,
            words_learned=words_learned_count,
            average_accuracy_rate=avg_acc,
            active_days=active_days,
            retention_rate=retention_rate,
        )

    @staticmethod
    def get_vocabulary_breakdown(db: Session, user: User) -> VocabularyBreakdownResponse:
        """
        Complete breakdown of vocabulary across statuses, mastery brackets, and CEFR levels.
        """
        vocabs = (
            db.query(Vocabulary)
            .filter(Vocabulary.user_id == user.id)
            .all()
        )
        total_words = len(vocabs)

        # 1. By status
        statuses = ["new", "learned", "practiced", "recalled", "reinforced", "mastered", "struggling"]
        by_status: List[VocabularyBreakdownItem] = []
        for s in statuses:
            count = sum(1 for v in vocabs if v.status == s)
            pct = round((count / total_words) * 100, 1) if total_words > 0 else 0.0
            by_status.append(
                VocabularyBreakdownItem(
                    status=s,
                    count=count,
                    percentage=pct,
                )
            )

        # 2. By mastery bracket
        brackets = [
            ("0-20%", lambda s: 0.0 <= s <= 0.20),
            ("21-40%", lambda s: 0.20 < s <= 0.40),
            ("41-60%", lambda s: 0.40 < s <= 0.60),
            ("61-80%", lambda s: 0.60 < s <= 0.80),
            ("81-100%", lambda s: 0.80 < s <= 1.00),
        ]
        by_bracket: List[MasteryBracketItem] = []
        for label, cond in brackets:
            b_count = sum(1 for v in vocabs if cond(v.mastery_score or 0.0))
            b_pct = round((b_count / total_words) * 100, 1) if total_words > 0 else 0.0
            by_bracket.append(
                MasteryBracketItem(
                    bracket=label,
                    count=b_count,
                    percentage=b_pct,
                )
            )

        # 3. By CEFR level
        cefr_counts: Dict[str, int] = {
            "A1": 0,
            "A2": 0,
            "B1": 0,
            "B2": 0,
            "C1": 0,
            "C2": 0,
            "Unassigned": 0,
        }

        for v in vocabs:
            if v.details and v.details.cefr_level:
                lvl = v.details.cefr_level.upper()
                if lvl in cefr_counts:
                    cefr_counts[lvl] += 1
                else:
                    cefr_counts["Unassigned"] += 1
            else:
                cefr_counts["Unassigned"] += 1

        return VocabularyBreakdownResponse(
            total_words=total_words,
            by_status=by_status,
            by_mastery_bracket=by_bracket,
            by_cefr_level=cefr_counts,
        )
