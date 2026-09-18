import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import status

from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.user import User
from models.practice import (
    PracticeSession,
    PracticeAttempt,
    ReviewRecord,
    ConversationSession,
    ConversationMessage,
    MultiWordPracticeSession,
    MultiWordPracticeAttempt,
)
from utils.security import create_access_token, hash_password


def create_mock_vocab(
    db,
    user_id: str,
    word: str,
    vocab_status: str = "new",
    mastery: float = 0.0,
    failed_recalls: int = 0,
    due: bool = False,
    practice_count: int = 0,
    successful_usage: int = 0,
):
    vocab = Vocabulary(
        user_id=user_id,
        word=word,
        status=vocab_status,
        mastery_score=mastery,
        failed_recall_count=failed_recalls,
        practice_count=practice_count,
        successful_usage_count=successful_usage,
        next_review_at=(
            datetime.now(timezone.utc) - timedelta(hours=2)
            if due
            else datetime.now(timezone.utc) + timedelta(days=3)
        ),
    )
    db.add(vocab)
    db.commit()
    db.refresh(vocab)

    details = WordDetails(
        vocabulary_id=vocab.id,
        simple_meaning=f"Clear definition of {word}",
        part_of_speech="verb",
        pronunciation_text=f"/{word}/",
        cefr_level="B1",
        difficulty_score=4.5,
        synonyms=[],
        antonyms=[],
        word_forms={},
        collocations=[],
    )
    db.add(details)
    db.commit()
    db.refresh(vocab)
    return vocab


def test_adaptive_plan_empty_user(client, auth_headers, test_user):
    """Test adaptive plan response for a brand new user with no vocabulary or history."""
    response = client.get("/api/v1/adaptive/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "generated_at" in data
    assert "learner_profile" in data
    assert "primary_recommendation" in data
    assert "recommendations" in data
    assert "diagnostic_focus" in data
    assert "daily_plan_sync" in data

    profile = data["learner_profile"]
    assert profile["total_vocabulary"] == 0
    assert profile["active_vocabulary"] == 0
    assert profile["mastered_count"] == 0
    assert profile["struggling_count"] == 0
    assert profile["average_mastery"] == 0.0
    assert profile["cefr_level"] in ["A1", "A2", "B1"]

    primary = data["primary_recommendation"]
    assert primary["activity_type"] == "learn"
    assert "First Vocabulary" in primary["title"] or "Add" in primary["title"]
    assert primary["action_url"] == "/vocabulary"
    assert len(primary["learning_objective"]) > 0
    assert len(primary["reason"]) > 0

    assert len(data["recommendations"]) >= 1

    diagnostic = data["diagnostic_focus"]
    assert diagnostic["recent_error_count"] == 0
    assert diagnostic["primary_weakness"] is None

    sync = data["daily_plan_sync"]
    assert sync["daily_goal_progress"] == 0
    assert sync["daily_goal_target"] == 5
    assert sync["is_goal_completed"] is False


def test_adaptive_plan_due_reviews_prioritization(client, auth_headers, test_user, db_session):
    """Test that when due reviews exist, they become the highest priority primary recommendation."""
    v1 = create_mock_vocab(db_session, test_user.id, "hesitate", "practiced", 0.4, due=True)
    v2 = create_mock_vocab(db_session, test_user.id, "vividly", "recalled", 0.6, due=True)
    create_mock_vocab(db_session, test_user.id, "resilient", "new", 0.0, due=False)

    response = client.get("/api/v1/adaptive/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    primary = data["primary_recommendation"]
    assert primary["activity_type"] == "review"
    assert primary["priority"] == "urgent"
    assert primary["action_url"] == "/reviews"
    assert "hesitate" in primary["target_words"] or "vividly" in primary["target_words"]
    assert "forgetting curve" in primary["reason"].lower() or "due" in primary["reason"].lower()
    assert len(primary["learning_objective"]) > 0

    profile = data["learner_profile"]
    assert profile["total_vocabulary"] == 3
    assert profile["active_vocabulary"] == 2


def test_adaptive_plan_struggling_words_prioritization(client, auth_headers, test_user, db_session):
    """Test that when no reviews are due but struggling words exist, struggling remediation is prioritized."""
    v1 = create_mock_vocab(
        db_session,
        test_user.id,
        "reluctant",
        vocab_status="struggling",
        mastery=0.2,
        failed_recalls=3,
        due=False,
    )
    v2 = create_mock_vocab(db_session, test_user.id, "coherent", "learned", 0.1, due=False)

    response = client.get("/api/v1/adaptive/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    primary = data["primary_recommendation"]
    assert primary["activity_type"] == "practice"
    assert primary["priority"] == "high"
    assert "reluctant" in primary["target_words"]
    assert primary["action_url"] == f"/practice/{v1.id}"
    assert "failed recall" in primary["reason"].lower() or "struggling" in primary["reason"].lower()

    profile = data["learner_profile"]
    assert profile["struggling_count"] == 1


def test_adaptive_plan_new_words_prioritization(client, auth_headers, test_user, db_session):
    """Test that when only new words exist, new word learning is prioritized."""
    v1 = create_mock_vocab(db_session, test_user.id, "meticulous", vocab_status="new", due=False)
    v2 = create_mock_vocab(db_session, test_user.id, "pragmatic", vocab_status="new", due=False)

    response = client.get("/api/v1/adaptive/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    primary = data["primary_recommendation"]
    assert primary["activity_type"] == "learn"
    assert "meticulous" in primary["target_words"] or "pragmatic" in primary["target_words"]
    assert primary["action_url"].startswith("/vocabulary/")
    assert len(primary["learning_objective"]) > 0


def test_adaptive_plan_multi_word_recommendation(client, auth_headers, test_user, db_session):
    """Test multi-word synthesis recommendation when 3+ words are eligible."""
    create_mock_vocab(db_session, test_user.id, "word1", "practiced", 0.5, due=False)
    create_mock_vocab(db_session, test_user.id, "word2", "recalled", 0.6, due=False)
    create_mock_vocab(db_session, test_user.id, "word3", "reinforced", 0.7, due=False)

    response = client.get("/api/v1/adaptive/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    rec_types = [r["activity_type"] for r in data["recommendations"]]
    assert "multi_word" in rec_types

    multi_rec = next(r for r in data["recommendations"] if r["activity_type"] == "multi_word")
    assert len(multi_rec["target_words"]) == 3
    assert multi_rec["action_url"] == "/practice/multi-word"
    assert "synthesis" in multi_rec["learning_objective"].lower() or "synthesize" in multi_rec["learning_objective"].lower()


def test_adaptive_plan_conversation_recommendation(client, auth_headers, test_user, db_session):
    """Test conversation recommendation when reinforced words exist."""
    create_mock_vocab(db_session, test_user.id, "articulate", "reinforced", 0.8, due=False)
    create_mock_vocab(db_session, test_user.id, "lucid", "recalled", 0.75, due=False)

    response = client.get("/api/v1/adaptive/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    rec_types = [r["activity_type"] for r in data["recommendations"]]
    assert "conversation" in rec_types

    convo_rec = next(r for r in data["recommendations"] if r["activity_type"] == "conversation")
    assert convo_rec["action_url"] == "/conversations"
    assert "articulate" in convo_rec["target_words"] or "lucid" in convo_rec["target_words"]


def test_adaptive_plan_performance_based_adaptation(client, auth_headers, test_user, db_session):
    """Test that adaptive difficulty score and CEFR level adjust based on user performance & mastery."""
    # Case 1: Advanced mastery with perfect scores
    for i in range(5):
        v = create_mock_vocab(
            db_session,
            test_user.id,
            f"advword{i}",
            vocab_status="mastered",
            mastery=0.9,
            due=False,
            practice_count=5,
            successful_usage=5,
        )
        sess = PracticeSession(
            user_id=test_user.id,
            vocabulary_id=v.id,
            session_type="scenario",
            status="completed",
            total_attempts=1,
            successful_attempts=1,
            average_score=9.5,
        )
        db_session.add(sess)
        db_session.commit()

        attempt = PracticeAttempt(
            session_id=sess.id,
            vocabulary_id=v.id,
            scenario_text="Advanced discussion scenario.",
            user_response=f"I used advword{i} impeccably in this discourse.",
            vocabulary_usage_score=9.5,
            grammar_score=9.5,
            context_score=9.5,
            naturalness_score=9.5,
            overall_score=9.5,
            feedback="Masterful usage.",
            is_successful=True,
            errors=[],
            cefr_level="C1",
        )
        db_session.add(attempt)

        rec = ReviewRecord(
            user_id=test_user.id,
            vocabulary_id=v.id,
            review_type="recall",
            recall_successful=True,
            score=10.0,
            feedback="Flawless recall.",
            previous_interval_days=14,
            new_interval_days=30,
            previous_status="reinforced",
            new_status="mastered",
        )
        db_session.add(rec)
        db_session.commit()

    response = client.get("/api/v1/adaptive/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    profile = data["learner_profile"]
    assert profile["average_mastery"] >= 0.8
    assert profile["practice_success_rate"] == 1.0
    assert profile["recall_accuracy_rate"] == 1.0
    assert profile["difficulty_score"] >= 7.0
    assert profile["cefr_level"] in ["C1", "C2", "B2"]


def test_adaptive_plan_diagnostic_errors_aggregation_and_remediation(client, auth_headers, test_user, db_session):
    """Test that diagnostic errors from practice attempts and conversations are collected and analyzed."""
    v = create_mock_vocab(db_session, test_user.id, "hesitate", "practiced", 0.4, due=False)

    sess = PracticeSession(
        user_id=test_user.id,
        vocabulary_id=v.id,
        session_type="scenario",
        status="completed",
        total_attempts=2,
        successful_attempts=0,
    )
    db_session.add(sess)
    db_session.commit()

    errors_sample = [
        {
            "error_type": "collocation",
            "original_text": "hesitate of doing",
            "explanation": "Use 'hesitate to do' instead of 'hesitate of'.",
            "suggested_correction": "hesitate to do",
            "severity": "medium",
        },
        {
            "error_type": "collocation",
            "original_text": "make hesitation",
            "explanation": "Natural phrasing is 'have hesitation' or use the verb directly.",
            "suggested_correction": "have hesitation",
            "severity": "medium",
        },
        {
            "error_type": "grammar",
            "original_text": "he hesitate yesterday",
            "explanation": "Past tense required: 'hesitated'.",
            "suggested_correction": "he hesitated yesterday",
            "severity": "high",
        },
    ]

    attempt = PracticeAttempt(
        session_id=sess.id,
        vocabulary_id=v.id,
        scenario_text="Workplace meeting.",
        user_response="He hesitate yesterday and make hesitation of doing it.",
        vocabulary_usage_score=4.0,
        grammar_score=5.0,
        context_score=6.0,
        naturalness_score=4.0,
        overall_score=4.8,
        feedback="Work on preposition collocations and past tense.",
        is_successful=False,
        errors=errors_sample,
        cefr_level="B1",
    )
    db_session.add(attempt)
    db_session.commit()

    response = client.get("/api/v1/adaptive/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    diagnostic = data["diagnostic_focus"]
    assert diagnostic["recent_error_count"] == 3
    assert len(diagnostic["top_error_types"]) >= 2

    top_err = diagnostic["top_error_types"][0]
    assert top_err["error_type"] == "collocation"
    assert top_err["count"] == 2
    assert "Collocation" in diagnostic["primary_weakness"]

    rec_types = [r["activity_type"] for r in data["recommendations"]]
    assert "error_remediation" in rec_types


def test_adaptive_plan_determinism(client, auth_headers, test_user, db_session):
    """Test that two calls in succession on unchanged state produce deterministic output."""
    create_mock_vocab(db_session, test_user.id, "stable1", "practiced", 0.5, due=True)
    create_mock_vocab(db_session, test_user.id, "stable2", "learned", 0.2, due=False)

    res1 = client.get("/api/v1/adaptive/plan", headers=auth_headers).json()
    res2 = client.get("/api/v1/adaptive/plan", headers=auth_headers).json()

    assert res1["primary_recommendation"]["activity_type"] == res2["primary_recommendation"]["activity_type"]
    assert res1["primary_recommendation"]["target_words"] == res2["primary_recommendation"]["target_words"]
    assert res1["learner_profile"]["difficulty_score"] == res2["learner_profile"]["difficulty_score"]
    assert res1["learner_profile"]["cefr_level"] == res2["learner_profile"]["cefr_level"]
    assert len(res1["recommendations"]) == len(res2["recommendations"])


def test_adaptive_plan_user_isolation(client, auth_headers, test_user, db_session):
    """Test strict user isolation: User A's data does not appear in User B's adaptive plan."""
    other_user = User(
        email="other_adaptive_user@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Other User",
        daily_goal=10,
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    # Add words to other user only
    create_mock_vocab(db_session, other_user.id, "secretword", "struggling", 0.1, due=True)

    # Query with test_user (who has no words)
    response = client.get("/api/v1/adaptive/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["learner_profile"]["total_vocabulary"] == 0
    assert "secretword" not in data["primary_recommendation"]["target_words"]
    for rec in data["recommendations"]:
        assert "secretword" not in rec["target_words"]

    # Now authenticate as other_user
    other_token = create_access_token({"sub": other_user.id})
    other_headers = {"Authorization": f"Bearer {other_token}"}
    other_res = client.get("/api/v1/adaptive/plan", headers=other_headers)
    assert other_res.status_code == status.HTTP_200_OK

    other_data = other_res.json()
    assert other_data["learner_profile"]["total_vocabulary"] == 1
    assert "secretword" in other_data["primary_recommendation"]["target_words"]


def test_adaptive_plan_unauthorized(client):
    """Test that unauthorized requests are rejected."""
    response = client.get("/api/v1/adaptive/plan")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
