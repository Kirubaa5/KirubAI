import re
import math
import random
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status

from models.vocabulary import Vocabulary, WordDetails
from models.practice import ConversationSession, ConversationMessage, ReviewRecord
from models.user import User
from schemas.conversation import (
    ConversationStartRequest,
    ConversationEvaluationSchema,
)
from ai.provider import LLMProvider
from ai.schemas import ConversationEvaluationAI
from ai.prompts.conversation import (
    CONVERSATION_SYSTEM_PROMPT,
    build_conversation_system_prompt,
    build_initial_message_prompt,
    CONVERSATION_EVALUATION_SYSTEM_PROMPT,
    build_conversation_evaluation_prompt,
)
from services.learning_service import get_llm_provider
from services.spaced_repetition import calculate_mastery


DEFAULT_TOPICS = [
    "Career Goals & Professional Ambitions",
    "Travel Adventures & Exploring New Cultures",
    "Technology, AI & Daily Modern Life",
    "Hobbies, Creative Passions & Weekend Plans",
    "Overcoming Challenges & Personal Growth",
    "Healthy Habits, Lifestyle & Wellness",
    "Favorite Books, Movies & Storytelling",
]

DEFAULT_VOCABULARY = ["hesitate", "confident", "improve", "resilient"]


def detect_vocabulary(
    text: str,
    target_words: List[str],
    word_forms_map: Optional[Dict[str, List[str]]] = None,
) -> List[str]:
    """
    Deterministic, application-controlled vocabulary detection.
    Matches target words and their grammatical forms/inflections case-insensitively.
    """
    if not text or not target_words:
        return []

    detected: List[str] = []
    text_clean = text.strip()

    for word in target_words:
        word_clean = word.strip()
        if not word_clean:
            continue

        matched = False
        target_lower = word_clean.lower()

        # Check explicit word forms if provided
        if word_forms_map and word_clean in word_forms_map:
            for form in word_forms_map[word_clean]:
                pattern = r"\b" + re.escape(form.lower()) + r"\b"
                if re.search(pattern, text_clean, re.IGNORECASE):
                    detected.append(word_clean)
                    matched = True
                    break

        if matched:
            continue

        # Exact whole-word match
        exact_pattern = r"\b" + re.escape(target_lower) + r"\b"
        if re.search(exact_pattern, text_clean, re.IGNORECASE):
            detected.append(word_clean)
            continue

        # Stem & morphological inflections
        # E.g., 'hesitate' -> 'hesitates', 'hesitated', 'hesitating', 'hesitation', 'hesitant'
        # E.g., 'improve' -> 'improves', 'improved', 'improving', 'improvement', 'improvements'
        # E.g., 'confident' -> 'confidently', 'confidence', 'confidences'
        if target_lower.endswith("ent") and len(target_lower) > 4:
            base = target_lower[:-3]
            inflection_pattern = (
                r"\b" + re.escape(base) + r"(ent|ently|ence|ences)?\b"
            )
        elif target_lower.endswith("e") and len(target_lower) > 3:
            base = target_lower[:-1]
            inflection_pattern = (
                r"\b" + re.escape(base) + r"(e|es|ed|ing|ation|ations|ant|antly|able|ability|ement|ements|er|ers|ive|ively)?\b"
            )
        elif target_lower.endswith("y") and len(target_lower) > 3:
            base = target_lower[:-1]
            inflection_pattern = (
                r"\b" + re.escape(base) + r"(y|ies|ied|ying|iful|iness|ily)?\b"
            )
        else:
            base = target_lower
            inflection_pattern = (
                r"\b" + re.escape(base) + r"(s|es|ed|ing|er|est|ment|ments|tion|tions|ly|able|ness|ity|ities)?\b"
            )

        if re.search(inflection_pattern, text_clean, re.IGNORECASE):
            detected.append(word_clean)

    # Return unique words preserving original target list order
    return [w for w in target_words if w in detected]


class ConversationService:
    @staticmethod
    def select_target_vocabulary(
        db: Session,
        user: User,
        count: int = 4,
    ) -> List[str]:
        """
        Select 3-5 active vocabulary words for conversation practice.
        Prioritizes practiced, recalled, reinforced, and struggling words.
        """
        active_words = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.user_id == user.id,
                Vocabulary.status.in_([
                    "practiced",
                    "recalled",
                    "reinforced",
                    "struggling",
                    "learned",
                ]),
            )
            .order_by(
                # Prioritize struggling and practiced words
                desc(Vocabulary.status == "struggling"),
                desc(Vocabulary.status == "practiced"),
                Vocabulary.last_practiced_at.asc().nullsfirst(),
            )
            .limit(count)
            .all()
        )

        selected = [v.word for v in active_words]

        # If not enough active words, fill from any user vocabulary
        if len(selected) < count:
            remaining_needed = count - len(selected)
            other_words = (
                db.query(Vocabulary)
                .filter(
                    Vocabulary.user_id == user.id,
                    Vocabulary.word.notin_(selected) if selected else True,
                )
                .limit(remaining_needed)
                .all()
            )
            selected.extend([v.word for v in other_words])

        # If user has no vocabulary at all, use default starter words
        if not selected:
            selected = DEFAULT_VOCABULARY[:count]

        return selected[:count]

    @staticmethod
    async def start_conversation(
        db: Session,
        user: User,
        data: ConversationStartRequest,
        llm: Optional[LLMProvider] = None,
    ) -> Tuple[ConversationSession, str]:
        """
        Start a new conversation session:
        1. Select 3-5 target vocabulary words.
        2. Seed a conversational topic.
        3. Generate initial AI greeting/message.
        4. Persist session and opening message.
        """
        # 1. Determine target vocabulary
        if data.target_words and len(data.target_words) > 0:
            target_words = [w.strip() for w in data.target_words if w.strip()]
        elif data.use_vocabulary:
            target_words = ConversationService.select_target_vocabulary(db, user, count=4)
        else:
            target_words = []

        # 2. Determine topic
        if data.topic and data.topic.strip():
            topic = data.topic.strip()
        else:
            topic = random.choice(DEFAULT_TOPICS)

        # 3. Generate initial AI coach opening message
        provider = llm or get_llm_provider()
        initial_prompt = build_initial_message_prompt(topic, target_words)

        try:
            initial_message = await provider.generate(
                prompt=initial_prompt,
                system_prompt=CONVERSATION_SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=300,
            )
        except Exception:
            # Deterministic fallback
            target_hint = f" (Focus words: {', '.join(target_words)})" if target_words else ""
            initial_message = f"Hello! I'm excited to chat with you today about '{topic}'. To kick off our conversation, what are your initial thoughts or experiences with this?"

        initial_message = initial_message.strip()

        # 4. Create and persist ConversationSession
        session = ConversationSession(
            user_id=user.id,
            topic=topic,
            target_vocabulary=target_words,
            vocabulary_used=[],
            vocabulary_usage_count=0,
            status="active",
            message_count=1,
            started_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.flush()

        # 5. Persist the opening message
        opening_msg = ConversationMessage(
            session_id=session.id,
            role="assistant",
            content=initial_message,
            vocabulary_detected=[],
            order_index=1,
            created_at=datetime.now(timezone.utc),
        )
        db.add(opening_msg)
        db.commit()
        db.refresh(session)

        return session, initial_message

    @staticmethod
    async def send_message(
        db: Session,
        user: User,
        session_id: str,
        content: str,
        llm: Optional[LLMProvider] = None,
    ) -> Tuple[ConversationMessage, str, List[str], List[str]]:
        """
        Send a user message in an active conversation:
        1. Validate session and user ownership.
        2. Detect target vocabulary words used in user message.
        3. Persist user message.
        4. Generate AI assistant reply via conversation history.
        5. Persist assistant reply.
        6. Return user message, assistant reply, detected words, and cumulative used words.
        """
        session = (
            db.query(ConversationSession)
            .filter(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user.id,
            )
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation session not found",
            )

        if session.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation session has already ended",
            )

        target_words: List[str] = session.target_vocabulary or []

        # Collect word forms for target words from DB if available
        word_forms_map: Dict[str, List[str]] = {}
        if target_words:
            details_records = (
                db.query(WordDetails)
                .join(Vocabulary, WordDetails.vocabulary_id == Vocabulary.id)
                .filter(
                    Vocabulary.user_id == user.id,
                    Vocabulary.word.in_(target_words),
                )
                .all()
            )
            for d in details_records:
                if d.word_forms and isinstance(d.word_forms, dict):
                    word_forms_map[d.vocabulary.word] = list(d.word_forms.values())

        # 2. Deterministic vocabulary detection
        detected_in_turn = detect_vocabulary(content, target_words, word_forms_map)

        # 3. Persist user message
        next_order = (session.message_count or 0) + 1
        user_msg = ConversationMessage(
            session_id=session.id,
            role="user",
            content=content.strip(),
            vocabulary_detected=detected_in_turn,
            order_index=next_order,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user_msg)

        # Update cumulative used vocabulary in session
        current_used = set(session.vocabulary_used or [])
        current_used.update(detected_in_turn)
        ordered_used = [w for w in target_words if w in current_used] + [
            w for w in current_used if w not in target_words
        ]
        session.vocabulary_used = ordered_used
        session.vocabulary_usage_count = len(ordered_used)

        # 4. Build message history for LLM (recent context)
        all_messages = (
            db.query(ConversationMessage)
            .filter(ConversationMessage.session_id == session.id)
            .order_by(ConversationMessage.order_index.asc())
            .all()
        )

        history_payload = [
            {"role": m.role, "content": m.content}
            for m in all_messages
        ]
        # Append current user message to history payload
        history_payload.append({"role": "user", "content": content.strip()})

        # Generate assistant reply
        provider = llm or get_llm_provider()
        system_prompt = build_conversation_system_prompt(
            topic=session.topic or "English Conversation",
            target_words=target_words,
        )

        try:
            assistant_reply = await provider.generate_conversation(
                messages=history_payload,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=400,
            )
        except Exception:
            # Deterministic fallback response
            assistant_reply = "That makes a lot of sense! How do you usually handle situations like that?"

        assistant_reply = assistant_reply.strip()

        # 5. Persist assistant reply
        assistant_msg = ConversationMessage(
            session_id=session.id,
            role="assistant",
            content=assistant_reply,
            vocabulary_detected=[],
            order_index=next_order + 1,
            created_at=datetime.now(timezone.utc),
        )
        db.add(assistant_msg)

        session.message_count = next_order + 1
        db.commit()
        db.refresh(user_msg)
        db.refresh(session)

        return user_msg, assistant_reply, detected_in_turn, session.vocabulary_used

    @staticmethod
    async def end_conversation(
        db: Session,
        user: User,
        session_id: str,
        llm: Optional[LLMProvider] = None,
    ) -> Tuple[ConversationSession, int, Dict[str, Any]]:
        """
        End an active conversation session:
        1. Evaluate conversation via structured AI output.
        2. Deterministically verify vocabulary usage and calculate final result.
        3. Award Phase 6 XP (20 XP per session).
        4. Integrate vocabulary usage into Phase 5 spaced repetition mastery logic.
        5. Mark session ended and persist evaluation.
        """
        session = (
            db.query(ConversationSession)
            .filter(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user.id,
            )
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation session not found",
            )

        # If already ended, return existing evaluation idempotently
        if session.status == "ended" and session.evaluation:
            return session, 0, session.evaluation

        # Fetch full conversation history
        messages = (
            db.query(ConversationMessage)
            .filter(ConversationMessage.session_id == session.id)
            .order_by(ConversationMessage.order_index.asc())
            .all()
        )

        transcript_lines = []
        all_detected_set = set()
        for m in messages:
            role_label = "Learner" if m.role == "user" else "Coach"
            transcript_lines.append(f"{role_label}: {m.content}")
            if m.role == "user" and m.vocabulary_detected:
                all_detected_set.update(m.vocabulary_detected)

        transcript = "\n".join(transcript_lines)
        target_words: List[str] = session.target_vocabulary or []

        # 1. AI Evaluation
        provider = llm or get_llm_provider()
        try:
            eval_ai: ConversationEvaluationAI = await provider.generate_structured(
                prompt=build_conversation_evaluation_prompt(
                    topic=session.topic or "English Conversation",
                    target_words=target_words,
                    conversation_transcript=transcript,
                ),
                response_schema=ConversationEvaluationAI,
                system_prompt=CONVERSATION_EVALUATION_SYSTEM_PROMPT,
                temperature=0.3,
            )

            # Reconcile AI evaluation with deterministic application state
            detected_used = list(all_detected_set)
            combined_used = list(dict.fromkeys(eval_ai.vocabulary_used + detected_used))
            final_used = [w for w in target_words if any(w.lower() == u.lower() for u in combined_used)]
            final_missed = [w for w in target_words if w not in final_used]

            usage_quality: Dict[str, float] = {}
            for w in final_used:
                score = eval_ai.usage_quality.get(w)
                if score is not None:
                    usage_quality[w] = round(score, 1)
                else:
                    usage_quality[w] = 8.5

            overall_fluency = round(eval_ai.overall_fluency, 1)
            feedback = eval_ai.feedback

            details = []
            for tw in target_words:
                is_used = tw in final_used
                matching_ai_detail = next(
                    (d for d in eval_ai.vocabulary_details if d.word.lower() == tw.lower()),
                    None,
                )
                details.append({
                    "word": tw,
                    "used": is_used,
                    "quality": usage_quality.get(tw) if is_used else None,
                    "context": matching_ai_detail.context if matching_ai_detail else None,
                })
        except Exception:
            # Deterministic fallback evaluation
            final_used = [w for w in target_words if w in all_detected_set]
            final_missed = [w for w in target_words if w not in all_detected_set]
            usage_quality = {w: 8.5 for w in final_used}
            overall_fluency = 8.0 if final_used else 7.0
            feedback = (
                f"Great job chatting! You actively incorporated {len(final_used)} vocabulary words in context."
                if final_used
                else "Nice conversation practice! In future sessions, try to use more of the suggested target words."
            )
            details = [
                {
                    "word": tw,
                    "used": tw in final_used,
                    "quality": 8.5 if tw in final_used else None,
                    "context": None,
                }
                for tw in target_words
            ]

        eval_dict: Dict[str, Any] = {
            "vocabulary_used": final_used,
            "vocabulary_missed": final_missed,
            "usage_quality": usage_quality,
            "overall_fluency": overall_fluency,
            "feedback": feedback,
            "vocabulary_details": details,
        }

        # 2. Award Phase 6 XP (20 XP per completed conversation session)
        xp_earned = 20
        user.xp += xp_earned
        user.level = max(1, (user.xp // 100) + 1)

        # 3. Integrate vocabulary usage into Phase 5 spaced repetition & mastery domain logic
        for used_word in final_used:
            vocab = (
                db.query(Vocabulary)
                .filter(
                    Vocabulary.user_id == user.id,
                    func.lower(Vocabulary.word) == used_word.lower(),
                )
                .first()
            )
            if vocab:
                vocab.successful_usage_count += 1
                vocab.last_practiced_at = datetime.now(timezone.utc)

                # State transition: NEW, LEARNED, or STRUGGLING advance to PRACTICED on successful usage
                if vocab.status in ("new", "learned", "struggling"):
                    vocab.status = "practiced"

                # Calculate updated mastery using Phase 5 calculation
                created_dt = vocab.created_at or datetime.now(timezone.utc)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                days_since = max(1, (datetime.now(timezone.utc) - created_dt).days)

                past_reviews = (
                    db.query(ReviewRecord)
                    .filter(
                        ReviewRecord.vocabulary_id == vocab.id,
                        ReviewRecord.user_id == user.id,
                    )
                    .order_by(desc(ReviewRecord.reviewed_at))
                    .all()
                )
                consecutive_successes = 0
                for r in past_reviews:
                    if r.recall_successful:
                        consecutive_successes += 1
                    else:
                        break

                successful_reviews_count = sum(1 for r in past_reviews if r.recall_successful)
                practice_total = max(vocab.practice_count, vocab.successful_usage_count, 1)

                new_mastery = calculate_mastery(
                    practice_count=practice_total,
                    successful_practice_count=vocab.successful_usage_count,
                    consecutive_successful_recalls=consecutive_successes,
                    unique_contexts_used=min(5, max(2, len(vocab.practice_attempts or []) + 1)),
                    reviews_completed_on_time=len(past_reviews) + 1,
                    total_reviews_due=max(1, len(past_reviews) + 1),
                    days_since_added=days_since,
                )
                vocab.mastery_score = new_mastery

                # Transition Rule from LEARNING_ENGINE.md:
                # REINFORCED -> MASTERED: User successfully uses word in 3+ reviews AND conversation (with mastery >= 0.8)
                if vocab.status == "reinforced" and successful_reviews_count >= 3 and new_mastery >= 0.8:
                    vocab.status = "mastered"

        # 4. Mark session ended and save
        session.status = "ended"
        session.ended_at = datetime.now(timezone.utc)
        session.evaluation = eval_dict
        session.vocabulary_used = final_used
        session.vocabulary_usage_count = len(final_used)

        db.commit()
        db.refresh(session)
        db.refresh(user)

        return session, xp_earned, eval_dict

    @staticmethod
    def get_session(
        db: Session,
        user: User,
        session_id: str,
    ) -> ConversationSession:
        """Get conversation session with messages and strict user isolation."""
        session = (
            db.query(ConversationSession)
            .filter(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user.id,
            )
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation session not found",
            )

        return session

    @staticmethod
    def list_sessions(
        db: Session,
        user: User,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[ConversationSession], int]:
        """List paginated conversation sessions for authenticated user."""
        query = db.query(ConversationSession).filter(ConversationSession.user_id == user.id)
        total = query.count()
        offset = (page - 1) * per_page
        sessions = (
            query.order_by(desc(ConversationSession.started_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )
        return sessions, total
