from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status

from models.vocabulary import Vocabulary, WordDetails
from models.practice import PracticeAttempt, ReviewRecord, ConversationSession
from models.user import User
from ai.provider import LLMProvider
from ai.schemas import PersonalizedScenarioAI
from ai.prompts.personalization import (
    PERSONALIZED_SCENARIO_SYSTEM_PROMPT,
    build_personalized_scenario_prompt,
)
from schemas.personalization import (
    WordSummaryItem,
    MasteryDistribution,
    LearningProfileResponse,
    RecommendationItem,
    PersonalizedRecommendationsResponse,
    GeneratePersonalizedScenarioRequest,
    PersonalizedScenarioResponse,
)
from services.learning_service import get_llm_provider


def calculate_adaptive_difficulty(
    average_mastery: float,
    accuracy_rate: float,
    word_difficulty: Optional[float] = None,
) -> Tuple[float, str]:
    """
    Deterministic adaptive difficulty & CEFR level calculation.

    Difficulty score: 1.0 (very basic) to 10.0 (highly advanced).
    CEFR mapping:
      1.0 - 2.5: A1
      2.6 - 4.0: A2
      4.1 - 6.0: B1
      6.1 - 7.5: B2
      7.6 - 9.0: C1
      9.1 - 10.0: C2
    """
    # Baseline difficulty from mastery (0.0 to 1.0 -> 2.0 to 8.0)
    base_score = 2.5 + (average_mastery * 5.0)

    # Accuracy adjustment (+/- 1.5 based on accuracy vs standard 0.70 benchmark)
    accuracy_adj = (accuracy_rate - 0.70) * 3.0
    calculated_score = base_score + accuracy_adj

    if word_difficulty is not None:
        # Weighted blend with specific word difficulty if available
        calculated_score = (calculated_score * 0.6) + (word_difficulty * 0.4)

    # Clamp between 1.0 and 10.0
    final_score = round(max(1.0, min(10.0, calculated_score)), 1)

    # Determine CEFR level
    if final_score <= 2.5:
        cefr = "A1"
    elif final_score <= 4.0:
        cefr = "A2"
    elif final_score <= 6.0:
        cefr = "B1"
    elif final_score <= 7.5:
        cefr = "B2"
    elif final_score <= 9.0:
        cefr = "C1"
    else:
        cefr = "C2"

    return final_score, cefr


class PersonalizationService:
    @staticmethod
    def get_learning_profile(db: Session, user: User) -> LearningProfileResponse:
        """
        Analyze user's learning data to build a comprehensive learning profile:
        - Mastery distribution
        - Weak and strong vocabulary detection
        - Practice and recall accuracy metrics
        - Adaptive difficulty & CEFR level
        - Deterministic recommended focus area
        """
        # Fetch all user vocabulary
        vocabularies = (
            db.query(Vocabulary)
            .filter(Vocabulary.user_id == user.id)
            .order_by(desc(Vocabulary.created_at))
            .all()
        )

        total_words = len(vocabularies)

        # 1. Mastery Distribution
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

        for v in vocabularies:
            status_key = v.status if v.status in counts else "new"
            counts[status_key] += 1
            total_mastery_sum += (v.mastery_score or 0.0)

        distribution = MasteryDistribution(
            new=counts["new"],
            learned=counts["learned"],
            practiced=counts["practiced"],
            recalled=counts["recalled"],
            reinforced=counts["reinforced"],
            mastered=counts["mastered"],
            struggling=counts["struggling"],
            total=total_words,
        )

        active_count = sum(
            counts[k]
            for k in ["learned", "practiced", "recalled", "reinforced", "struggling"]
        )
        avg_mastery = round(total_mastery_sum / total_words, 3) if total_words > 0 else 0.0

        # 2. Identify Weak Vocabulary
        # Words struggling, with failed recalls, low practice ratio, or low mastery
        weak_list: List[Vocabulary] = []
        for v in vocabularies:
            is_weak = False
            if v.status == "struggling":
                is_weak = True
            elif v.failed_recall_count > 0:
                is_weak = True
            elif v.practice_count >= 2 and (v.successful_usage_count / v.practice_count) < 0.5:
                is_weak = True
            elif v.status not in ("new", "mastered", "reinforced") and v.mastery_score < 0.35:
                is_weak = True

            if is_weak:
                weak_list.append(v)

        # Sort weak words: struggling first, then highest failed recalls, then lowest mastery
        weak_list.sort(
            key=lambda w: (
                w.status == "struggling",
                w.failed_recall_count,
                -w.mastery_score,
            ),
            reverse=True,
        )
        weak_items = [WordSummaryItem.model_validate(w) for w in weak_list[:10]]

        # 3. Identify Strong Vocabulary
        strong_list = [
            v for v in vocabularies
            if v.status in ("mastered", "reinforced") or v.mastery_score >= 0.7
        ]
        strong_list.sort(key=lambda w: (w.mastery_score, w.successful_usage_count), reverse=True)
        strong_items = [WordSummaryItem.model_validate(w) for w in strong_list[:10]]

        # 4. Learning Performance Metrics
        # Practice Attempts
        practice_attempts_count = (
            db.query(PracticeAttempt)
            .join(Vocabulary, PracticeAttempt.vocabulary_id == Vocabulary.id)
            .filter(Vocabulary.user_id == user.id)
            .count()
        )
        successful_practice_count = (
            db.query(PracticeAttempt)
            .join(Vocabulary, PracticeAttempt.vocabulary_id == Vocabulary.id)
            .filter(
                Vocabulary.user_id == user.id,
                PracticeAttempt.is_successful == True,
            )
            .count()
        )
        practice_success_rate = (
            round(successful_practice_count / practice_attempts_count, 2)
            if practice_attempts_count > 0
            else 0.0
        )

        # Review Records
        reviews_count = (
            db.query(ReviewRecord)
            .filter(ReviewRecord.user_id == user.id)
            .count()
        )
        successful_recalls_count = (
            db.query(ReviewRecord)
            .filter(
                ReviewRecord.user_id == user.id,
                ReviewRecord.recall_successful == True,
            )
            .count()
        )
        recall_accuracy_rate = (
            round(successful_recalls_count / reviews_count, 2)
            if reviews_count > 0
            else 0.0
        )

        # Conversations
        conversations_count = (
            db.query(ConversationSession)
            .filter(
                ConversationSession.user_id == user.id,
                ConversationSession.status == "ended",
            )
            .count()
        )

        # 5. Adaptive Difficulty & CEFR
        overall_accuracy = (
            (practice_success_rate * 0.5) + (recall_accuracy_rate * 0.5)
            if (practice_attempts_count > 0 and reviews_count > 0)
            else practice_success_rate or recall_accuracy_rate or 0.70
        )
        adaptive_difficulty, adaptive_cefr = calculate_adaptive_difficulty(
            average_mastery=avg_mastery,
            accuracy_rate=overall_accuracy,
        )

        # 6. Recommended Focus
        now = datetime.now(timezone.utc)
        due_reviews_count = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.user_id == user.id,
                Vocabulary.next_review_at <= now,
            )
            .count()
        )

        if due_reviews_count > 0:
            recommended_focus = f"Spaced Repetition: You have {due_reviews_count} review{'s' if due_reviews_count > 1 else ''} due today to prevent memory decay."
        elif counts["struggling"] > 0:
            recommended_focus = f"Targeted Reinforcement: Focus on mastering your {counts['struggling']} struggling word{'s' if counts['struggling'] > 1 else ''}."
        elif counts["learned"] > 0:
            recommended_focus = f"Active Practice: Put your {counts['learned']} newly learned word{'s' if counts['learned'] > 1 else ''} into real-life practice scenarios."
        elif counts["reinforced"] > 0 or counts["recalled"] > 0:
            recommended_focus = "Conversational Fluency: Test your reinforced vocabulary in interactive AI conversations to achieve mastery."
        elif total_words == 0:
            recommended_focus = "Vocabulary Expansion: Add your first target words to kickstart your personalized learning loop."
        else:
            recommended_focus = "Continuous Growth: Add new vocabulary words to expand your active English expression."

        return LearningProfileResponse(
            total_vocabulary=total_words,
            active_vocabulary=active_count,
            mastered_count=counts["mastered"],
            struggling_count=counts["struggling"],
            average_mastery=avg_mastery,
            mastery_distribution=distribution,
            weak_words=weak_items,
            strong_words=strong_items,
            total_practice_attempts=practice_attempts_count,
            practice_success_rate=practice_success_rate,
            total_reviews_completed=reviews_count,
            recall_accuracy_rate=recall_accuracy_rate,
            total_conversations_completed=conversations_count,
            adaptive_cefr_level=adaptive_cefr,
            adaptive_difficulty_score=adaptive_difficulty,
            recommended_focus=recommended_focus,
        )

    @staticmethod
    def get_recommendations(
        db: Session,
        user: User,
        limit: int = 5,
    ) -> PersonalizedRecommendationsResponse:
        """
        Generate deterministic, prioritized study recommendations based on user's current learning state:
        1. Due reviews (High Priority - prevents forgetting curve)
        2. Struggling words (High Priority - targeted practice needed)
        3. Learned words needing initial practice (Medium Priority - active recall ramp)
        4. Recalled/Reinforced words needing conversation (Medium Priority - pathway to Mastery)
        5. New words needing initial learning (Low Priority)
        """
        now = datetime.now(timezone.utc)
        profile = PersonalizationService.get_learning_profile(db, user)
        adaptive_diff = profile.adaptive_difficulty_score
        adaptive_cefr = profile.adaptive_cefr_level

        recommendations: List[RecommendationItem] = []
        selected_vocab_ids = set()

        # 1. Due reviews (High Priority)
        due_vocabs = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.user_id == user.id,
                Vocabulary.next_review_at <= now,
            )
            .order_by(Vocabulary.next_review_at.asc())
            .limit(limit)
            .all()
        )
        for v in due_vocabs:
            if len(recommendations) >= limit:
                break
            recommendations.append(
                RecommendationItem(
                    vocabulary_id=v.id,
                    word=v.word,
                    activity_type="review",
                    priority="high",
                    reason="Scheduled review is due today according to spaced repetition.",
                    recommended_difficulty=adaptive_diff,
                    cefr_level=adaptive_cefr,
                )
            )
            selected_vocab_ids.add(v.id)

        # 2. Struggling words (High Priority)
        if len(recommendations) < limit:
            struggling_vocabs = (
                db.query(Vocabulary)
                .filter(
                    Vocabulary.user_id == user.id,
                    Vocabulary.status == "struggling",
                    Vocabulary.id.notin_(selected_vocab_ids) if selected_vocab_ids else True,
                )
                .order_by(desc(Vocabulary.failed_recall_count), Vocabulary.mastery_score.asc())
                .limit(limit - len(recommendations))
                .all()
            )
            for v in struggling_vocabs:
                if len(recommendations) >= limit:
                    break
                recommendations.append(
                    RecommendationItem(
                        vocabulary_id=v.id,
                        word=v.word,
                        activity_type="practice",
                        priority="high",
                        reason="Word is marked as struggling. Targeted scenario practice will strengthen retention.",
                        recommended_difficulty=max(1.0, round(adaptive_diff - 1.0, 1)),
                        cefr_level=adaptive_cefr,
                    )
                )
                selected_vocab_ids.add(v.id)

        # 3. Learned words needing practice (Medium Priority)
        if len(recommendations) < limit:
            learned_vocabs = (
                db.query(Vocabulary)
                .filter(
                    Vocabulary.user_id == user.id,
                    Vocabulary.status == "learned",
                    Vocabulary.id.notin_(selected_vocab_ids) if selected_vocab_ids else True,
                )
                .order_by(Vocabulary.created_at.desc())
                .limit(limit - len(recommendations))
                .all()
            )
            for v in learned_vocabs:
                if len(recommendations) >= limit:
                    break
                recommendations.append(
                    RecommendationItem(
                        vocabulary_id=v.id,
                        word=v.word,
                        activity_type="practice",
                        priority="medium",
                        reason="Newly learned word ready for first scenario practice attempt.",
                        recommended_difficulty=adaptive_diff,
                        cefr_level=adaptive_cefr,
                    )
                )
                selected_vocab_ids.add(v.id)

        # 4. Reinforced / Recalled words ready for Conversation (Medium Priority)
        if len(recommendations) < limit:
            ready_for_convo = (
                db.query(Vocabulary)
                .filter(
                    Vocabulary.user_id == user.id,
                    Vocabulary.status.in_(["reinforced", "recalled"]),
                    Vocabulary.id.notin_(selected_vocab_ids) if selected_vocab_ids else True,
                )
                .order_by(desc(Vocabulary.mastery_score))
                .limit(limit - len(recommendations))
                .all()
            )
            for v in ready_for_convo:
                if len(recommendations) >= limit:
                    break
                recommendations.append(
                    RecommendationItem(
                        vocabulary_id=v.id,
                        word=v.word,
                        activity_type="conversation",
                        priority="medium",
                        reason="Use in natural AI conversation to advance towards full mastery.",
                        recommended_difficulty=min(10.0, round(adaptive_diff + 0.5, 1)),
                        cefr_level=adaptive_cefr,
                    )
                )
                selected_vocab_ids.add(v.id)

        # 5. New words needing initial learning (Low Priority)
        if len(recommendations) < limit:
            new_vocabs = (
                db.query(Vocabulary)
                .filter(
                    Vocabulary.user_id == user.id,
                    Vocabulary.status == "new",
                    Vocabulary.id.notin_(selected_vocab_ids) if selected_vocab_ids else True,
                )
                .order_by(Vocabulary.created_at.desc())
                .limit(limit - len(recommendations))
                .all()
            )
            for v in new_vocabs:
                if len(recommendations) >= limit:
                    break
                recommendations.append(
                    RecommendationItem(
                        vocabulary_id=v.id,
                        word=v.word,
                        activity_type="learn",
                        priority="low",
                        reason="Explore word explanation and conversational examples to begin learning.",
                        recommended_difficulty=adaptive_diff,
                        cefr_level=adaptive_cefr,
                    )
                )
                selected_vocab_ids.add(v.id)

        return PersonalizedRecommendationsResponse(
            recommendations=recommendations,
            total_due_reviews=len(due_vocabs),
            total_struggling_words=profile.struggling_count,
            recommended_daily_focus=profile.recommended_focus,
            learner_level=f"{profile.adaptive_cefr_level} (Difficulty {profile.adaptive_difficulty_score}/10)",
        )

    @staticmethod
    async def generate_personalized_scenario(
        db: Session,
        user: User,
        request: GeneratePersonalizedScenarioRequest,
        llm: Optional[LLMProvider] = None,
    ) -> PersonalizedScenarioResponse:
        """
        Generate an adaptive practice scenario personalized to the user's level and requested domain/interests.
        """
        target_word = request.word.strip()
        if not target_word:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target word cannot be empty",
            )

        # Lookup word in user's vocabulary if exists
        vocab = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.user_id == user.id,
                func.lower(Vocabulary.word) == target_word.lower(),
            )
            .first()
        )

        word_meaning = None
        word_diff = None
        if vocab and vocab.details:
            word_meaning = vocab.details.simple_meaning
            word_diff = vocab.details.difficulty_score

        profile = PersonalizationService.get_learning_profile(db, user)
        diff_score, cefr = calculate_adaptive_difficulty(
            average_mastery=profile.average_mastery,
            accuracy_rate=(profile.practice_success_rate + profile.recall_accuracy_rate) / 2 or 0.70,
            word_difficulty=word_diff,
        )

        if request.target_cefr_level:
            cefr = request.target_cefr_level.upper()

        domain = request.domain or "Workplace"
        prompt_str = build_personalized_scenario_prompt(
            word=target_word,
            domain=domain,
            cefr_level=cefr,
            difficulty_score=diff_score,
            word_meaning=word_meaning,
            weak_area_context=request.weak_area_context,
        )

        provider = llm or get_llm_provider()
        try:
            scenario_ai: PersonalizedScenarioAI = await provider.generate_structured(
                prompt=prompt_str,
                response_schema=PersonalizedScenarioAI,
                system_prompt=PERSONALIZED_SCENARIO_SYSTEM_PROMPT,
                temperature=0.7,
            )
            situation = scenario_ai.situation
            prompt_text = scenario_ai.prompt
            context_hint = scenario_ai.context_hint
            domain_result = scenario_ai.domain or domain
            cefr_result = scenario_ai.cefr_level or cefr
        except Exception:
            # Fallback deterministic scenario
            situation = f"You are in a {domain.lower()} setting and need to communicate your thoughts clearly using the word '{target_word}'."
            prompt_text = f"Respond in this context and naturally use '{target_word}'."
            context_hint = "Focus on natural phrasing and clear tone."
            domain_result = domain
            cefr_result = cefr

        return PersonalizedScenarioResponse(
            vocabulary_id=vocab.id if vocab else None,
            word=target_word,
            situation=situation,
            prompt=prompt_text,
            context_hint=context_hint,
            domain=domain_result,
            cefr_level=cefr_result,
            difficulty_score=diff_score,
        )
