from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

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
from schemas.adaptive import (
    AdaptivePlanResponse,
    LearnerProfileSummary,
    AdaptiveRecommendationItem,
    DiagnosticFocusSummary,
    DiagnosticErrorSummary,
    DailyPlanSyncSummary,
)
from services.personalization_service import calculate_adaptive_difficulty
from services.dashboard_service import calculate_user_streak, to_utc_datetime


class AdaptiveLearningService:
    @staticmethod
    def get_adaptive_plan(db: Session, user: User) -> AdaptivePlanResponse:
        """
        Generate a comprehensive, deterministic adaptive learning plan for the authenticated user:
        - Analyzes due reviews, struggling words, mastery distribution, recent practice/review accuracy
        - Aggregates diagnostic errors across single-word practice, multi-word synthesis, and conversations
        - Computes dynamic adaptive CEFR level & difficulty score
        - Formulates prioritized recommendations with clear pedagogical learning objectives
        - Seamlessly synchronizes with the Daily Learning system
        - Strictly isolated by user_id and handles new/empty accounts safely
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        iso_now = now.isoformat()

        # 1. Fetch User Vocabulary (Strict User Isolation)
        all_vocabs = (
            db.query(Vocabulary)
            .filter(Vocabulary.user_id == user.id)
            .order_by(desc(Vocabulary.created_at))
            .all()
        )

        total_words = len(all_vocabs)
        counts = {
            "new": 0,
            "learned": 0,
            "practiced": 0,
            "recalled": 0,
            "reinforced": 0,
            "mastered": 0,
            "struggling": 0,
        }
        total_mastery_sum = 0.0

        for v in all_vocabs:
            st = v.status if v.status in counts else "new"
            counts[st] += 1
            total_mastery_sum += (v.mastery_score or 0.0)

        active_count = sum(
            counts[k]
            for k in ["learned", "practiced", "recalled", "reinforced", "struggling"]
        )
        avg_mastery = round(total_mastery_sum / total_words, 3) if total_words > 0 else 0.0

        # Partition Vocabulary by State
        due_reviews = [
            v for v in all_vocabs
            if v.status in ("learned", "practiced", "recalled", "reinforced", "mastered", "struggling")
            and (v.next_review_at is None or to_utc_datetime(v.next_review_at) <= now)
        ]
        # Sort due reviews: highest failed recalls first, then nearest review date
        due_reviews.sort(
            key=lambda w: (
                w.failed_recall_count,
                - (to_utc_datetime(w.next_review_at).timestamp() if w.next_review_at else 0),
            ),
            reverse=True,
        )

        struggling_words = [v for v in all_vocabs if v.status == "struggling" or v.failed_recall_count >= 2]
        struggling_words.sort(
            key=lambda w: (w.status == "struggling", w.failed_recall_count, -(w.mastery_score or 0.0)),
            reverse=True,
        )

        learned_words = [v for v in all_vocabs if v.status == "learned"]
        new_words = [v for v in all_vocabs if v.status == "new"]
        eligible_for_multi_word = [v for v in all_vocabs if v.status in ("practiced", "recalled", "reinforced")]
        ready_for_convo = [
            v for v in all_vocabs
            if v.status in ("reinforced", "recalled") or (v.mastery_score or 0.0) >= 0.6
        ]
        ready_for_convo.sort(key=lambda w: (w.mastery_score or 0.0), reverse=True)

        # 2. Performance Metrics & Diagnostic Error Aggregation
        # Recent single-word practice attempts
        recent_practice_attempts = (
            db.query(PracticeAttempt)
            .join(Vocabulary, PracticeAttempt.vocabulary_id == Vocabulary.id)
            .filter(Vocabulary.user_id == user.id)
            .order_by(desc(PracticeAttempt.created_at))
            .limit(50)
            .all()
        )

        practice_total = len(recent_practice_attempts)
        practice_successful = sum(1 for a in recent_practice_attempts if a.is_successful)
        practice_success_rate = (
            round(practice_successful / practice_total, 2)
            if practice_total > 0
            else 0.70
        )

        # Recent spaced reviews
        recent_reviews = (
            db.query(ReviewRecord)
            .filter(ReviewRecord.user_id == user.id)
            .order_by(desc(ReviewRecord.reviewed_at))
            .limit(50)
            .all()
        )

        reviews_total = len(recent_reviews)
        reviews_successful = sum(1 for r in recent_reviews if r.recall_successful)
        recall_accuracy_rate = (
            round(reviews_successful / reviews_total, 2)
            if reviews_total > 0
            else 0.70
        )

        # Recent multi-word attempts
        recent_multi_attempts = (
            db.query(MultiWordPracticeAttempt)
            .join(MultiWordPracticeSession, MultiWordPracticeAttempt.session_id == MultiWordPracticeSession.id)
            .filter(MultiWordPracticeSession.user_id == user.id)
            .order_by(desc(MultiWordPracticeAttempt.created_at))
            .limit(20)
            .all()
        )

        # Recent conversation sessions
        recent_conversations = (
            db.query(ConversationSession)
            .filter(ConversationSession.user_id == user.id, ConversationSession.status == "ended")
            .order_by(desc(ConversationSession.started_at))
            .limit(10)
            .all()
        )

        # Blended recent accuracy
        if practice_total > 0 and reviews_total > 0:
            recent_accuracy = round((practice_success_rate * 0.5) + (recall_accuracy_rate * 0.5), 2)
        elif practice_total > 0:
            recent_accuracy = practice_success_rate
        elif reviews_total > 0:
            recent_accuracy = recall_accuracy_rate
        else:
            recent_accuracy = 0.70

        # Adaptive Difficulty & CEFR Calculation
        diff_score, cefr = calculate_adaptive_difficulty(
            average_mastery=avg_mastery,
            accuracy_rate=recent_accuracy,
        )

        # 3. Aggregate Diagnostic Errors (Grammar, Collocations, Semantics, Tone, Spelling)
        error_counts: Dict[str, int] = {}
        error_samples: Dict[str, List[str]] = {}

        def process_errors(err_list: Any):
            if not err_list or not isinstance(err_list, list):
                return
            for item in err_list:
                if isinstance(item, dict):
                    etype = str(item.get("error_type", "grammar")).lower().strip()
                    orig = str(item.get("original_text", "")).strip()
                elif hasattr(item, "error_type"):
                    etype = str(item.error_type).lower().strip()
                    orig = str(getattr(item, "original_text", "")).strip()
                else:
                    continue

                if etype:
                    error_counts[etype] = error_counts.get(etype, 0) + 1
                    if orig and orig not in error_samples.get(etype, []):
                        error_samples.setdefault(etype, []).append(orig)

        for attempt in recent_practice_attempts:
            process_errors(attempt.errors)

        for mattempt in recent_multi_attempts:
            process_errors(mattempt.errors)

        for conv in recent_conversations:
            if isinstance(conv.evaluation, dict):
                process_errors(conv.evaluation.get("errors", []))

        total_diagnostic_errors = sum(error_counts.values())

        error_descriptions = {
            "grammar": "Sentence construction, tense consistency, and subject-verb agreements.",
            "collocation": "Preposition pairings, natural word combinations, and idioms.",
            "semantic": "Contextual nuance, accurate connotations, and word meaning precision.",
            "tone": "Formality level, register appropriateness, and style alignment.",
            "spelling": "Orthography, word morphology, and spelling accuracy.",
        }

        top_error_summaries: List[DiagnosticErrorSummary] = []
        for etype, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            top_error_summaries.append(
                DiagnosticErrorSummary(
                    error_type=etype,
                    count=count,
                    description=error_descriptions.get(
                        etype,
                        f"Linguistic precision and accuracy issues related to {etype}.",
                    ),
                    sample_phrases=error_samples.get(etype, [])[:3],
                )
            )

        # Primary Weakness and Pedagogical Strategy
        if top_error_summaries and top_error_summaries[0].count >= 2:
            primary_weakness = f"{top_error_summaries[0].error_type.capitalize()} precision & patterns"
            recommended_strategy = (
                f"Prioritize contextual application that reinforces correct {top_error_summaries[0].error_type} rules."
            )
        elif counts["struggling"] > 0:
            primary_weakness = "Active recall retention under scenario pressure"
            recommended_strategy = "Apply struggling words in high-context scenarios to bridge passive recognition into active output."
        elif len(due_reviews) > 0:
            primary_weakness = "Scheduled memory decay curve"
            recommended_strategy = "Complete due spaced repetition reviews promptly to secure long-term consolidation."
        elif total_words == 0:
            primary_weakness = None
            recommended_strategy = "Add your initial target vocabulary to establish your baseline learning profile."
        else:
            primary_weakness = None
            recommended_strategy = "Synthesize vocabulary across multi-word scenarios and open conversational dialogue."

        diagnostic_focus = DiagnosticFocusSummary(
            primary_weakness=primary_weakness,
            recommended_strategy=recommended_strategy,
            recent_error_count=total_diagnostic_errors,
            top_error_types=top_error_summaries,
        )

        # 4. Generate Deterministic Prioritized Recommendations
        recommendations: List[AdaptiveRecommendationItem] = []
        rec_counter = 1

        # Recommendation Tier 1: Due Spaced Reviews (Pedagogical Top Priority for Retention)
        if due_reviews:
            review_words = [v.word for v in due_reviews[:4]]
            review_ids = [v.id for v in due_reviews[:4]]
            due_c = len(due_reviews)
            recommendations.append(
                AdaptiveRecommendationItem(
                    id=f"rec_due_reviews_{rec_counter}",
                    activity_type="review",
                    title=f"Due Spaced Reviews ({due_c} word{'s' if due_c > 1 else ''})",
                    reason=f"You have {due_c} spaced repetition review{'s' if due_c > 1 else ''} due today according to the forgetting curve.",
                    learning_objective="Prevent forgetting curve decay through active retrieval and contextual recall.",
                    target_words=review_words,
                    target_vocabulary_ids=review_ids,
                    difficulty=diff_score,
                    cefr_level=cefr,
                    priority="urgent",
                    action_url="/reviews",
                    action_label="Start Spaced Reviews",
                )
            )
            rec_counter += 1

        # Recommendation Tier 2: Struggling Words Targeted Remediation
        if struggling_words:
            top_st = struggling_words[0]
            st_words = [w.word for w in struggling_words[:3]]
            st_ids = [w.id for w in struggling_words[:3]]
            fail_c = top_st.failed_recall_count
            recommendations.append(
                AdaptiveRecommendationItem(
                    id=f"rec_struggling_{rec_counter}",
                    activity_type="practice",
                    title=f"Struggling Word Remediation: '{top_st.word}'",
                    reason=f"Word '{top_st.word}' has {fail_c} failed recall{'s' if fail_c != 1 else ''}. Targeted scenario practice will restore confidence.",
                    learning_objective=f"Apply '{top_st.word}' in a structured real-world scenario to overcome hesitation and elevate mastery.",
                    target_words=st_words,
                    target_vocabulary_ids=st_ids,
                    difficulty=max(1.0, round(diff_score - 0.8, 1)),
                    cefr_level=cefr,
                    priority="high",
                    action_url=f"/practice/{top_st.id}",
                    action_label=f"Practice '{top_st.word}'",
                )
            )
            rec_counter += 1

        # Recommendation Tier 3: Diagnostic Error Remediation (if recurring errors detected)
        if top_error_summaries and top_error_summaries[0].count >= 2:
            top_err = top_error_summaries[0]
            recommendations.append(
                AdaptiveRecommendationItem(
                    id=f"rec_diagnostic_{rec_counter}",
                    activity_type="error_remediation",
                    title=f"Linguistic Accuracy: {top_err.error_type.capitalize()} Polish",
                    reason=f"Identified {top_err.count} recent {top_err.error_type} error(s) during your practice sessions.",
                    learning_objective=f"Review rules and study authentic usage patterns to eliminate {top_err.error_type} inconsistencies.",
                    target_words=[top_st.word] if struggling_words else [v.word for v in all_vocabs[:2]],
                    target_vocabulary_ids=[top_st.id] if struggling_words else [v.id for v in all_vocabs[:2]],
                    difficulty=diff_score,
                    cefr_level=cefr,
                    priority="medium",
                    action_url="/knowledge",
                    action_label="Review Grammar & Usage",
                )
            )
            rec_counter += 1

        # Recommendation Tier 4: Multi-Word Practice (Use My Vocabulary)
        if len(eligible_for_multi_word) >= 3:
            multi_sample = eligible_for_multi_word[:3]
            recommendations.append(
                AdaptiveRecommendationItem(
                    id=f"rec_multi_word_{rec_counter}",
                    activity_type="multi_word",
                    title="Multi-Word Vocabulary Synthesis",
                    reason=f"You have {len(eligible_for_multi_word)} active words ready to be synthesized into a single contextual narrative.",
                    learning_objective="Synthesize multiple target words simultaneously within one realistic communication scenario.",
                    target_words=[w.word for w in multi_sample],
                    target_vocabulary_ids=[w.id for w in multi_sample],
                    difficulty=min(10.0, round(diff_score + 0.5, 1)),
                    cefr_level=cefr,
                    priority="medium",
                    action_url="/practice/multi-word",
                    action_label="Synthesize Vocabulary",
                )
            )
            rec_counter += 1

        # Recommendation Tier 5: Conversational Fluency Practice
        if ready_for_convo:
            convo_words = [w.word for w in ready_for_convo[:3]]
            convo_ids = [w.id for w in ready_for_convo[:3]]
            recommendations.append(
                AdaptiveRecommendationItem(
                    id=f"rec_conversation_{rec_counter}",
                    activity_type="conversation",
                    title="Conversational Fluency Coach",
                    reason="Your reinforced vocabulary is primed for spontaneous dialogue in AI text conversation.",
                    learning_objective="Deploy active vocabulary naturally in a multi-turn conversation to advance toward full Mastery.",
                    target_words=convo_words,
                    target_vocabulary_ids=convo_ids,
                    difficulty=min(10.0, round(diff_score + 0.5, 1)),
                    cefr_level=cefr,
                    priority="medium",
                    action_url="/conversations",
                    action_label="Start AI Conversation",
                )
            )
            rec_counter += 1

        # Recommendation Tier 6: Newly Learned Words Needing First Practice Attempt
        if learned_words:
            top_learned = learned_words[0]
            recommendations.append(
                AdaptiveRecommendationItem(
                    id=f"rec_learned_practice_{rec_counter}",
                    activity_type="practice",
                    title=f"First Scenario Practice: '{top_learned.word}'",
                    reason=f"'{top_learned.word}' has been understood and is ready for its inaugural scenario practice attempt.",
                    learning_objective=f"Produce an original sentence using '{top_learned.word}' to establish active retrieval.",
                    target_words=[top_learned.word],
                    target_vocabulary_ids=[top_learned.id],
                    difficulty=diff_score,
                    cefr_level=cefr,
                    priority="normal",
                    action_url=f"/practice/{top_learned.id}",
                    action_label=f"Practice '{top_learned.word}'",
                )
            )
            rec_counter += 1

        # Recommendation Tier 7: New Word Learning
        if new_words:
            top_new = new_words[0]
            recommendations.append(
                AdaptiveRecommendationItem(
                    id=f"rec_new_word_{rec_counter}",
                    activity_type="learn",
                    title=f"Explore New Vocabulary: '{top_new.word}'",
                    reason=f"'{top_new.word}' is queued in your vocabulary bank and waiting for definition & 10 conversational examples.",
                    learning_objective=f"Understand contextual nuances, collocations, and varied scenarios for '{top_new.word}'.",
                    target_words=[w.word for w in new_words[:3]],
                    target_vocabulary_ids=[w.id for w in new_words[:3]],
                    difficulty=diff_score,
                    cefr_level=cefr,
                    priority="normal",
                    action_url=f"/vocabulary/{top_new.id}/learn",
                    action_label=f"Learn '{top_new.word}'",
                )
            )
            rec_counter += 1

        # Fallback for New or Empty Users (total_words == 0)
        if total_words == 0:
            recommendations.append(
                AdaptiveRecommendationItem(
                    id="rec_empty_welcome",
                    activity_type="learn",
                    title="Add Your First Vocabulary Words",
                    reason="Your vocabulary bank is currently empty. Adding words unlocks personalized scenario practice and spaced repetition.",
                    learning_objective="Select 3-5 target English words to begin your active vocabulary journey.",
                    target_words=["hesitate", "resilient", "eloquent"],
                    target_vocabulary_ids=[],
                    difficulty=2.5,
                    cefr_level="A2",
                    priority="high",
                    action_url="/vocabulary",
                    action_label="Explore & Add Words",
                )
            )
            recommendations.append(
                AdaptiveRecommendationItem(
                    id="rec_empty_knowledge",
                    activity_type="learn",
                    title="Browse Grammar & Usage Guidelines",
                    reason="Explore curated grammar rules, common learner pitfalls, and natural collocations.",
                    learning_objective="Build foundational awareness of English sentence structure and collocations.",
                    target_words=[],
                    target_vocabulary_ids=[],
                    difficulty=3.0,
                    cefr_level="B1",
                    priority="normal",
                    action_url="/knowledge",
                    action_label="Open Knowledge Base",
                )
            )

        # Primary Recommendation is the first (highest-priority) item
        primary_rec = recommendations[0]

        # 5. Daily Plan Sync Metrics
        reviews_done_today = (
            db.query(func.count(ReviewRecord.id))
            .filter(ReviewRecord.user_id == user.id, ReviewRecord.reviewed_at >= today_start)
            .scalar() or 0
        )
        practice_attempts_today = (
            db.query(func.count(PracticeAttempt.id))
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(PracticeSession.user_id == user.id, PracticeAttempt.created_at >= today_start)
            .scalar() or 0
        )
        multi_word_today = (
            db.query(func.count(MultiWordPracticeAttempt.id))
            .join(MultiWordPracticeSession, MultiWordPracticeAttempt.session_id == MultiWordPracticeSession.id)
            .filter(MultiWordPracticeSession.user_id == user.id, MultiWordPracticeAttempt.created_at >= today_start)
            .scalar() or 0
        )
        conversations_today = (
            db.query(func.count(ConversationSession.id))
            .filter(ConversationSession.user_id == user.id, ConversationSession.started_at >= today_start)
            .scalar() or 0
        )
        words_added_today = sum(
            1 for v in all_vocabs if v.created_at and to_utc_datetime(v.created_at) >= today_start
        )

        daily_goal_progress = (
            practice_attempts_today
            + reviews_done_today
            + conversations_today
            + words_added_today
            + multi_word_today
        )
        daily_goal_target = user.daily_goal or 5
        is_goal_completed = daily_goal_progress >= daily_goal_target
        current_streak = calculate_user_streak(db=db, user=user)

        daily_plan_sync = DailyPlanSyncSummary(
            daily_goal_progress=daily_goal_progress,
            daily_goal_target=daily_goal_target,
            is_goal_completed=is_goal_completed,
            current_streak=current_streak,
        )

        # 6. Build Learner Profile Summary
        learner_profile = LearnerProfileSummary(
            cefr_level=cefr,
            difficulty_score=diff_score,
            average_mastery=avg_mastery,
            total_vocabulary=total_words,
            active_vocabulary=active_count,
            mastered_count=counts["mastered"],
            struggling_count=counts["struggling"],
            recent_accuracy_rate=recent_accuracy,
            practice_success_rate=practice_success_rate,
            recall_accuracy_rate=recall_accuracy_rate,
        )

        return AdaptivePlanResponse(
            generated_at=iso_now,
            learner_profile=learner_profile,
            primary_recommendation=primary_rec,
            recommendations=recommendations,
            diagnostic_focus=diagnostic_focus,
            daily_plan_sync=daily_plan_sync,
        )
