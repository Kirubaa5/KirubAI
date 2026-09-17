import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from fastapi import HTTPException, status

from models.vocabulary import Vocabulary, WordDetails
from models.practice import (
    PracticeSession,
    PracticeAttempt,
    ReviewRecord,
    ConversationSession,
    MultiWordPracticeSession,
    MultiWordPracticeAttempt,
)
from models.user import User
from schemas.daily import (
    DailyTaskItem,
    DailyPlanResponse,
    MultiWordTargetWordSchema,
    MultiWordEligibleResponse,
)
from schemas.practice import ScenarioSchema, PracticeScoresSchema
from services.dashboard_service import (
    calculate_user_streak,
    to_utc_datetime,
    CURATED_WORDS_OF_THE_DAY,
)
from schemas.dashboard import WordOfTheDay
from services.practice_service import calculate_overall_score
from services.learning_service import get_llm_provider
from services.gamification_service import GamificationService
from ai.provider import LLMProvider
from ai.schemas import MultiWordScenarioAI, MultiWordEvaluationAI
from ai.prompts.scenario import (
    build_multi_word_scenario_prompt,
    MULTI_WORD_SCENARIO_SYSTEM_PROMPT,
)
from ai.prompts.evaluation import (
    build_multi_word_evaluation_prompt,
    MULTI_WORD_EVALUATION_SYSTEM_PROMPT,
)


class DailyLearningService:
    @staticmethod
    def get_daily_plan(db: Session, user: User) -> DailyPlanResponse:
        """
        Generate prioritized daily learning plan for the authenticated user:
        Priority 1: Due Reviews (retention)
        Priority 2: Struggling Words Practice (targeted improvement)
        Priority 3: New Word Learning (up to user daily goal)
        Priority 4: Reinforcement / "Use My Vocabulary" multi-word practice
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_date_str = now.strftime("%Y-%m-%d")

        # 1. Fetch user's vocabulary
        all_vocabs = db.query(Vocabulary).filter(Vocabulary.user_id == user.id).all()

        # Priority 1: Due reviews
        due_reviews = [
            v for v in all_vocabs
            if v.status in ("learned", "practiced", "recalled", "reinforced", "mastered", "struggling")
            and (v.next_review_at is None or to_utc_datetime(v.next_review_at) <= now)
        ]
        due_reviews_count = len(due_reviews)

        # Reviews completed today
        reviews_done_today = (
            db.query(func.count(ReviewRecord.id))
            .filter(ReviewRecord.user_id == user.id, ReviewRecord.reviewed_at >= today_start)
            .scalar() or 0
        )

        # Priority 2: Struggling words
        struggling_words = [v for v in all_vocabs if v.status == "struggling"]
        struggling_count = len(struggling_words)

        # Priority 3: New words
        new_words = [v for v in all_vocabs if v.status == "new"]
        new_words_count = len(new_words)

        # Priority 4: Eligible words for Use My Vocabulary
        eligible_for_multi_word = [
            v for v in all_vocabs
            if v.status in ("practiced", "recalled", "reinforced")
        ]
        eligible_multi_count = len(eligible_for_multi_word)

        # Multi-word attempts completed today
        multi_word_today = (
            db.query(func.count(MultiWordPracticeAttempt.id))
            .join(MultiWordPracticeSession, MultiWordPracticeAttempt.session_id == MultiWordPracticeSession.id)
            .filter(MultiWordPracticeSession.user_id == user.id, MultiWordPracticeAttempt.created_at >= today_start)
            .scalar() or 0
        )

        # General practice attempts today
        practice_attempts_today = (
            db.query(func.count(PracticeAttempt.id))
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(PracticeSession.user_id == user.id, PracticeAttempt.created_at >= today_start)
            .scalar() or 0
        )

        # Conversations today
        conversations_today = (
            db.query(func.count(ConversationSession.id))
            .filter(ConversationSession.user_id == user.id, ConversationSession.started_at >= today_start)
            .scalar() or 0
        )

        # Words added today
        words_added_today = sum(
            1 for v in all_vocabs if v.created_at and to_utc_datetime(v.created_at) >= today_start
        )

        # Daily goal metrics
        daily_goal_progress = (
            practice_attempts_today
            + reviews_done_today
            + conversations_today
            + words_added_today
            + multi_word_today
        )
        daily_goal_target = user.daily_goal or 5
        is_goal_completed = daily_goal_progress >= daily_goal_target

        # Streak
        current_streak = calculate_user_streak(db=db, user=user)

        # Deterministic Word of the Day
        word_of_the_day: Optional[WordOfTheDay] = None
        date_hash = int(now.strftime("%Y%m%d"))

        if all_vocabs:
            candidates = struggling_words if struggling_words else [v for v in all_vocabs if v.status in ("new", "learned")]
            if not candidates:
                candidates = all_vocabs
            selected_vocab = candidates[date_hash % len(candidates)]
            meaning = selected_vocab.details.simple_meaning if selected_vocab.details else f"Vocabulary word: '{selected_vocab.word}'"
            cefr = selected_vocab.details.cefr_level if selected_vocab.details else None
            pos = selected_vocab.details.part_of_speech if selected_vocab.details else None
            ex = selected_vocab.examples[0].example_text if selected_vocab.examples else None

            word_of_the_day = WordOfTheDay(
                word=selected_vocab.word,
                meaning=meaning,
                cefr_level=cefr,
                part_of_speech=pos,
                example_sentence=ex,
            )
        else:
            curated = CURATED_WORDS_OF_THE_DAY[date_hash % len(CURATED_WORDS_OF_THE_DAY)]
            word_of_the_day = WordOfTheDay(
                word=curated["word"],
                meaning=curated["meaning"],
                cefr_level=curated["cefr_level"],
                part_of_speech=curated["part_of_speech"],
                example_sentence=curated["example_sentence"],
            )

        # Construct Prioritized Tasks
        tasks: List[DailyTaskItem] = []

        # Task 1: Due Reviews
        task_1_status = "completed" if due_reviews_count == 0 else "pending"
        task_1_items = [
            {
                "id": v.id,
                "word": v.word,
                "status": v.status,
                "mastery_score": v.mastery_score,
                "review_interval_days": v.review_interval_days,
            }
            for v in due_reviews[:5]
        ]
        tasks.append(
            DailyTaskItem(
                id="task_reviews_due",
                priority=1,
                task_type="reviews_due",
                title="Due Spaced Reviews",
                description="Active recall reviews scheduled for today to maintain long-term memory retention.",
                status=task_1_status,
                item_count=due_reviews_count,
                action_label="Start Reviews" if due_reviews_count > 0 else "Reviews Up to Date",
                action_url="/reviews",
                items=task_1_items if task_1_items else None,
            )
        )

        # Task 2: Struggling Words Practice
        task_2_status = "completed" if struggling_count == 0 else "pending"
        task_2_items = [
            {
                "id": v.id,
                "word": v.word,
                "status": v.status,
                "mastery_score": v.mastery_score,
                "practice_count": v.practice_count,
            }
            for v in struggling_words[:5]
        ]
        tasks.append(
            DailyTaskItem(
                id="task_struggling_practice",
                priority=2,
                task_type="struggling_practice",
                title="Struggling Words Targeted Practice",
                description="Targeted scenario practice for words with lower recall success to overcome hesitation.",
                status=task_2_status,
                item_count=struggling_count,
                action_label="Practice Struggling Words" if struggling_count > 0 else "No Struggling Words",
                action_url="/practice",
                items=task_2_items if task_2_items else None,
            )
        )

        # Task 3: New Word Learning
        task_3_status = "completed" if (new_words_count == 0 and words_added_today >= 1) or is_goal_completed else "pending"
        task_3_items = [
            {
                "id": v.id,
                "word": v.word,
                "status": v.status,
                "mastery_score": v.mastery_score,
            }
            for v in new_words[:5]
        ]
        tasks.append(
            DailyTaskItem(
                id="task_learn_new",
                priority=3,
                task_type="learn_new",
                title="Learn New Vocabulary",
                description="Expand your active vocabulary pool by understanding definitions, collocations, and 10 conversational examples.",
                status=task_3_status,
                item_count=new_words_count,
                action_label="Learn Words" if new_words_count > 0 else "Explore Vocabulary",
                action_url="/vocabulary",
                items=task_3_items if task_3_items else None,
            )
        )

        # Task 4: Use My Vocabulary (Multi-Word Synthesis)
        if eligible_multi_count < 3:
            task_4_status = "locked"
            task_4_desc = f"Unlock multi-word practice by completing practice on at least 3 vocabulary words (Currently: {eligible_multi_count}/3 eligible)."
            task_4_btn = "Practice Words to Unlock"
        elif multi_word_today > 0:
            task_4_status = "completed"
            task_4_desc = f"Completed {multi_word_today} multi-word synthesis challenge(s) today. Keep practicing to reinforce active usage!"
            task_4_btn = "Practice Again"
        else:
            task_4_status = "ready"
            task_4_desc = f"Synthesize {eligible_multi_count} active vocabulary words into one realistic communication scenario."
            task_4_btn = "Start Multi-Word Practice"

        task_4_items = [
            {
                "id": v.id,
                "word": v.word,
                "status": v.status,
                "mastery_score": v.mastery_score,
            }
            for v in eligible_for_multi_word[:5]
        ]
        tasks.append(
            DailyTaskItem(
                id="task_use_my_vocabulary",
                priority=4,
                task_type="use_my_vocabulary",
                title="Use My Vocabulary (Multi-Word Synthesis)",
                description=task_4_desc,
                status=task_4_status,
                item_count=eligible_multi_count,
                action_label=task_4_btn,
                action_url="/practice/multi-word",
                items=task_4_items if task_4_items else None,
            )
        )

        # Calculate completion metrics
        completed_count = sum(1 for t in tasks if t.status == "completed")
        total_tasks = len(tasks)
        completion_pct = round((completed_count / total_tasks) * 100, 1) if total_tasks > 0 else 0.0

        return DailyPlanResponse(
            date=today_date_str,
            daily_goal_target=daily_goal_target,
            daily_goal_progress=daily_goal_progress,
            is_goal_completed=is_goal_completed,
            current_streak=current_streak,
            word_of_the_day=word_of_the_day,
            tasks=tasks,
            completed_tasks_count=completed_count,
            total_tasks_count=total_tasks,
            completion_percentage=completion_pct,
        )

    # =========================================================================
    # Use My Vocabulary (Multi-Word Practice Engine)
    # =========================================================================

    @staticmethod
    def get_eligible_vocabulary(db: Session, user: User) -> MultiWordEligibleResponse:
        """
        Fetch vocabulary words eligible for multi-word practice.
        Eligible statuses: 'practiced', 'recalled', 'reinforced'.
        """
        all_vocabs = (
            db.query(Vocabulary)
            .filter(Vocabulary.user_id == user.id)
            .all()
        )

        eligible_vocabs = [
            v for v in all_vocabs
            if v.status in ("practiced", "recalled", "reinforced")
        ]

        items = [
            MultiWordTargetWordSchema(
                id=v.id,
                word=v.word,
                meaning=v.details.simple_meaning if v.details else None,
                cefr_level=v.details.cefr_level if v.details else None,
                status=v.status,
            )
            for v in eligible_vocabs
        ]

        eligible_count = len(items)
        is_eligible = eligible_count >= 3

        return MultiWordEligibleResponse(
            eligible_count=eligible_count,
            total_words=len(all_vocabs),
            min_required=3,
            is_eligible=is_eligible,
            items=items,
        )

    @staticmethod
    async def start_multi_word_session(
        db: Session,
        user: User,
        vocabulary_ids: Optional[List[str]] = None,
        llm: Optional[LLMProvider] = None,
    ) -> Tuple[MultiWordPracticeSession, MultiWordScenarioAI, List[Vocabulary]]:
        """
        Start a new multi-word practice session ("Use My Vocabulary"):
        1. Select 3-5 eligible vocabulary words.
        2. Generate cohesive realistic AI scenario requiring natural use of those words.
        3. Persist session.
        """
        selected_vocabs: List[Vocabulary] = []

        if vocabulary_ids and len(vocabulary_ids) > 0:
            # Validate user-provided vocabulary IDs
            vocabs = (
                db.query(Vocabulary)
                .filter(Vocabulary.user_id == user.id, Vocabulary.id.in_(vocabulary_ids))
                .all()
            )
            if len(vocabs) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please provide at least 2 valid vocabulary words for multi-word practice.",
                )
            selected_vocabs = vocabs[:5]
        else:
            # Auto-select 3-5 eligible words (practiced, recalled, reinforced)
            all_eligible = (
                db.query(Vocabulary)
                .filter(
                    Vocabulary.user_id == user.id,
                    Vocabulary.status.in_(["practiced", "recalled", "reinforced"]),
                )
                .order_by(Vocabulary.last_practiced_at.asc().nulls_first())
                .all()
            )

            if len(all_eligible) < 3:
                # Fallback check if user has other active words (learned, struggling, mastered)
                fallback_active = (
                    db.query(Vocabulary)
                    .filter(
                        Vocabulary.user_id == user.id,
                        Vocabulary.status.in_(["learned", "struggling", "mastered"]),
                    )
                    .order_by(Vocabulary.last_practiced_at.asc().nulls_first())
                    .all()
                )
                combined = all_eligible + fallback_active
                if len(combined) < 2:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="At least 3 practiced, recalled, or reinforced vocabulary words are required for 'Use My Vocabulary'. Practice individual words first to unlock multi-word synthesis.",
                    )
                selected_vocabs = combined[: min(5, max(3, len(combined)))]
            else:
                selected_vocabs = all_eligible[: min(5, max(3, len(all_eligible)))]

        target_words_list = [v.word for v in selected_vocabs]
        target_ids_list = [v.id for v in selected_vocabs]

        word_details_list = [
            {
                "word": v.word,
                "meaning": v.details.simple_meaning if v.details else "",
                "cefr_level": v.details.cefr_level if v.details else "B1",
            }
            for v in selected_vocabs
        ]

        provider = llm or get_llm_provider()

        prompt_str = build_multi_word_scenario_prompt(
            words=target_words_list,
            word_details=word_details_list,
            learner_level=user.english_level or "intermediate",
        )

        scenario_ai: MultiWordScenarioAI = await provider.generate_structured(
            prompt=prompt_str,
            response_schema=MultiWordScenarioAI,
            system_prompt=MULTI_WORD_SCENARIO_SYSTEM_PROMPT,
            temperature=0.7,
        )

        session = MultiWordPracticeSession(
            user_id=user.id,
            target_words=target_words_list,
            target_vocabulary_ids=target_ids_list,
            situation=scenario_ai.situation,
            prompt=scenario_ai.prompt,
            context_hint=scenario_ai.context_hint,
            status="active",
            total_attempts=0,
            successful_attempts=0,
            average_score=None,
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return session, scenario_ai, selected_vocabs

    @staticmethod
    async def submit_multi_word_attempt(
        db: Session,
        user: User,
        session_id: str,
        user_response: str,
        llm: Optional[LLMProvider] = None,
    ) -> Tuple[MultiWordPracticeAttempt, MultiWordPracticeSession, int]:
        """
        Submit a written response to a multi-word scenario:
        1. Evaluate overall response & each target word individually.
        2. Enforce deterministic scoring.
        3. Update vocabulary mastery & practice metrics for all target words.
        4. Award XP (+20 XP for success, +5 XP for attempt) and record daily gamification activity.
        5. Persist attempt and return result.
        """
        session = (
            db.query(MultiWordPracticeSession)
            .filter(
                MultiWordPracticeSession.id == session_id,
                MultiWordPracticeSession.user_id == user.id,
            )
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Multi-word practice session not found",
            )

        if session.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot submit to a completed practice session",
            )

        provider = llm or get_llm_provider()

        eval_prompt = build_multi_word_evaluation_prompt(
            target_words=session.target_words,
            scenario_text=f"{session.situation}\nTask: {session.prompt}",
            user_response=user_response,
        )

        eval_ai: MultiWordEvaluationAI = await provider.generate_structured(
            prompt=eval_prompt,
            response_schema=MultiWordEvaluationAI,
            system_prompt=MULTI_WORD_EVALUATION_SYSTEM_PROMPT,
            temperature=0.3,
        )

        # Enforce deterministic scoring formula
        overall_score = calculate_overall_score(
            vocabulary_usage=eval_ai.vocabulary_usage_score,
            grammar=eval_ai.grammar_score,
            context=eval_ai.context_score,
            naturalness=eval_ai.naturalness_score,
        )

        # Check used words
        used_word_evals = [we for we in eval_ai.word_evaluations if we.used and we.used_correctly]
        total_targets = len(session.target_words)
        is_successful = (
            overall_score >= 6.0
            and eval_ai.vocabulary_usage_score >= 5.0
            and len(used_word_evals) >= max(1, total_targets // 2)
        )

        # Serialize word evaluations to JSON dicts
        word_evals_json = [
            {
                "word": we.word,
                "used": we.used,
                "used_correctly": we.used_correctly,
                "used_naturally": we.used_naturally,
                "score": we.score,
                "feedback": we.feedback,
            }
            for we in eval_ai.word_evaluations
        ]

        # Serialize diagnostic errors to JSON dicts
        errors_data = [
            e.model_dump() if hasattr(e, "model_dump") else (e if isinstance(e, dict) else dict(e))
            for e in (eval_ai.errors or [])
        ]

        attempt = MultiWordPracticeAttempt(
            session_id=session.id,
            user_response=user_response,
            vocabulary_usage_score=eval_ai.vocabulary_usage_score,
            grammar_score=eval_ai.grammar_score,
            context_score=eval_ai.context_score,
            naturalness_score=eval_ai.naturalness_score,
            overall_score=overall_score,
            word_evaluations=word_evals_json,
            feedback=eval_ai.feedback,
            improved_version=eval_ai.improved_version,
            is_successful=is_successful,
            errors=errors_data,
            cefr_level=eval_ai.cefr_level or "B1",
            actionable_tips=eval_ai.actionable_tips or [],
        )
        db.add(attempt)

        # Update session metrics
        session.total_attempts += 1
        if is_successful:
            session.successful_attempts += 1

        all_scores = [a.overall_score for a in session.attempts] + [overall_score]
        session.average_score = round(sum(all_scores) / len(all_scores), 2)

        # Update vocabulary metrics for all target words
        now = datetime.now(timezone.utc)
        target_vocabs = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.user_id == user.id,
                Vocabulary.id.in_(session.target_vocabulary_ids),
            )
            .all()
        )

        used_words_set = {
            we.word.lower() for we in eval_ai.word_evaluations if we.used and we.used_correctly
        }

        for vocab in target_vocabs:
            vocab.practice_count += 1
            vocab.last_practiced_at = now
            if vocab.word.lower() in used_words_set:
                vocab.successful_usage_count += 1
                # Mastery reward (+0.08 for multi-word synthesis)
                vocab.mastery_score = min(1.0, round(vocab.mastery_score + 0.08, 2))
                # State progression
                if vocab.status == "practiced" and vocab.successful_usage_count >= 2:
                    vocab.status = "recalled"
                elif vocab.status == "recalled" and vocab.successful_usage_count >= 4:
                    vocab.status = "reinforced"

        # Award XP
        xp_earned = 20 if is_successful else 5
        user.xp = (user.xp or 0) + xp_earned

        # Record activity in gamification system (streaks, daily goal bonus, level, achievements)
        GamificationService.record_activity(db, user)

        db.commit()
        db.refresh(attempt)
        db.refresh(session)

        return attempt, session, xp_earned

    @staticmethod
    def get_multi_word_session(
        db: Session,
        user: User,
        session_id: str,
    ) -> MultiWordPracticeSession:
        """Fetch multi-word session details with attempts."""
        session = (
            db.query(MultiWordPracticeSession)
            .filter(
                MultiWordPracticeSession.id == session_id,
                MultiWordPracticeSession.user_id == user.id,
            )
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Multi-word practice session not found",
            )
        return session

    @staticmethod
    def list_multi_word_sessions(
        db: Session,
        user: User,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[MultiWordPracticeSession], int]:
        """List multi-word practice sessions for the user."""
        query = db.query(MultiWordPracticeSession).filter(MultiWordPracticeSession.user_id == user.id)
        total = query.count()
        sessions = (
            query.order_by(desc(MultiWordPracticeSession.started_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return sessions, total
