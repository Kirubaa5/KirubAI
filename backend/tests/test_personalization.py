import pytest
from datetime import datetime, timezone, timedelta
from models.vocabulary import Vocabulary, WordDetails
from models.practice import PracticeSession, PracticeAttempt, ReviewRecord, ConversationSession
from models.user import User
from utils.security import hash_password
from services.personalization_service import calculate_adaptive_difficulty


# ============================================================
# Unit Tests for Adaptive Difficulty Calculation
# ============================================================

def test_calculate_adaptive_difficulty_low_mastery():
    """Verify low mastery and low accuracy map to A1/A2 and lower score."""
    score, cefr = calculate_adaptive_difficulty(average_mastery=0.1, accuracy_rate=0.4)
    assert score < 3.0
    assert cefr in ("A1", "A2")


def test_calculate_adaptive_difficulty_intermediate():
    """Verify intermediate mastery and standard accuracy map to B1/B2."""
    score, cefr = calculate_adaptive_difficulty(average_mastery=0.5, accuracy_rate=0.75)
    assert 4.0 <= score <= 7.0
    assert cefr in ("B1", "B2")


def test_calculate_adaptive_difficulty_advanced():
    """Verify high mastery and high accuracy map to C1/C2."""
    score, cefr = calculate_adaptive_difficulty(average_mastery=0.95, accuracy_rate=0.98)
    assert score >= 7.5
    assert cefr in ("C1", "C2")


def test_calculate_adaptive_difficulty_bounds():
    """Verify score is clamped to [1.0, 10.0]."""
    score_min, cefr_min = calculate_adaptive_difficulty(average_mastery=0.0, accuracy_rate=0.0)
    assert score_min >= 1.0
    assert cefr_min == "A1"

    score_max, cefr_max = calculate_adaptive_difficulty(average_mastery=1.0, accuracy_rate=1.0, word_difficulty=10.0)
    assert score_max <= 10.0
    assert cefr_max in ("C1", "C2")


# ============================================================
# API Endpoint Integration Tests
# ============================================================

def test_get_personalization_profile_empty_state(client, auth_headers):
    """Test getting profile for a user with zero vocabulary."""
    response = client.get("/api/v1/personalization/profile", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_vocabulary"] == 0
    assert data["active_vocabulary"] == 0
    assert data["mastered_count"] == 0
    assert data["struggling_count"] == 0
    assert data["average_mastery"] == 0.0
    assert data["weak_words"] == []
    assert data["strong_words"] == []
    assert "Vocabulary Expansion" in data["recommended_focus"]


def test_get_personalization_profile_with_learning_data(client, auth_headers, db_session, test_user):
    """Test learning profile accurately calculates distribution, weak/strong words, and metrics."""
    # Seed mixed vocabulary
    v_struggling = Vocabulary(
        user_id=test_user.id,
        word="hesitate",
        status="struggling",
        mastery_score=0.15,
        practice_count=3,
        successful_usage_count=1,
        failed_recall_count=2,
    )
    v_mastered = Vocabulary(
        user_id=test_user.id,
        word="confident",
        status="mastered",
        mastery_score=0.92,
        practice_count=6,
        successful_usage_count=6,
        failed_recall_count=0,
    )
    v_learned = Vocabulary(
        user_id=test_user.id,
        word="resilient",
        status="learned",
        mastery_score=0.25,
        practice_count=0,
        successful_usage_count=0,
    )
    db_session.add_all([v_struggling, v_mastered, v_learned])
    db_session.commit()

    # Seed Practice Attempts
    session = PracticeSession(
        user_id=test_user.id,
        vocabulary_id=v_struggling.id,
        session_type="scenario",
        status="completed",
    )
    db_session.add(session)
    db_session.flush()

    attempt1 = PracticeAttempt(
        session_id=session.id,
        vocabulary_id=v_struggling.id,
        scenario_text="Workplace",
        user_response="I hesitate",
        vocabulary_usage_score=9.0,
        grammar_score=8.0,
        context_score=8.5,
        naturalness_score=8.0,
        overall_score=8.4,
        feedback="Good",
        is_successful=True,
    )
    attempt2 = PracticeAttempt(
        session_id=session.id,
        vocabulary_id=v_struggling.id,
        scenario_text="Travel",
        user_response="bad answer",
        vocabulary_usage_score=2.0,
        grammar_score=4.0,
        context_score=3.0,
        naturalness_score=3.0,
        overall_score=3.0,
        feedback="Poor",
        is_successful=False,
    )
    db_session.add_all([attempt1, attempt2])

    # Seed Review Records
    review = ReviewRecord(
        user_id=test_user.id,
        vocabulary_id=v_mastered.id,
        review_type="recall",
        recall_successful=True,
        previous_interval_days=14,
        new_interval_days=30,
        previous_status="reinforced",
        new_status="mastered",
    )
    db_session.add(review)

    # Seed Conversation
    convo = ConversationSession(
        user_id=test_user.id,
        topic="Technology",
        status="ended",
    )
    db_session.add(convo)
    db_session.commit()

    response = client.get("/api/v1/personalization/profile", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_vocabulary"] == 3
    assert data["mastered_count"] == 1
    assert data["struggling_count"] == 1
    assert data["mastery_distribution"]["struggling"] == 1
    assert data["mastery_distribution"]["mastered"] == 1
    assert data["mastery_distribution"]["learned"] == 1

    # Check weak & strong detection
    weak_words = [w["word"] for w in data["weak_words"]]
    strong_words = [w["word"] for w in data["strong_words"]]
    assert "hesitate" in weak_words
    assert "confident" in strong_words

    # Check performance metrics
    assert data["total_practice_attempts"] == 2
    assert data["practice_success_rate"] == 0.5
    assert data["total_reviews_completed"] == 1
    assert data["recall_accuracy_rate"] == 1.0
    assert data["total_conversations_completed"] == 1
    assert data["adaptive_difficulty_score"] > 0
    assert len(data["adaptive_cefr_level"]) == 2


def test_get_personalization_recommendations_prioritization(client, auth_headers, db_session, test_user):
    """Test recommendations prioritize due reviews first, struggling words second, and learned third."""
    now = datetime.now(timezone.utc)

    # Word 1: Due review (High priority)
    v_due = Vocabulary(
        user_id=test_user.id,
        word="due_word",
        status="recalled",
        mastery_score=0.6,
        next_review_at=now - timedelta(hours=2),
    )
    # Word 2: Struggling (High priority)
    v_struggling = Vocabulary(
        user_id=test_user.id,
        word="struggling_word",
        status="struggling",
        mastery_score=0.2,
        failed_recall_count=2,
        next_review_at=now + timedelta(days=5),
    )
    # Word 3: Learned (Medium priority)
    v_learned = Vocabulary(
        user_id=test_user.id,
        word="learned_word",
        status="learned",
        mastery_score=0.1,
        next_review_at=now + timedelta(days=1),
    )
    # Word 4: Reinforced ready for conversation (Medium priority)
    v_reinforced = Vocabulary(
        user_id=test_user.id,
        word="reinforced_word",
        status="reinforced",
        mastery_score=0.75,
        next_review_at=now + timedelta(days=7),
    )
    db_session.add_all([v_due, v_struggling, v_learned, v_reinforced])
    db_session.commit()

    response = client.get("/api/v1/personalization/recommendations?limit=4", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    recs = data["recommendations"]
    assert len(recs) == 4

    # 1st must be due review
    assert recs[0]["word"] == "due_word"
    assert recs[0]["activity_type"] == "review"
    assert recs[0]["priority"] == "high"

    # 2nd must be struggling word practice
    assert recs[1]["word"] == "struggling_word"
    assert recs[1]["activity_type"] == "practice"
    assert recs[1]["priority"] == "high"

    # 3rd must be learned word practice
    assert recs[2]["word"] == "learned_word"
    assert recs[2]["activity_type"] == "practice"
    assert recs[2]["priority"] == "medium"

    # 4th must be reinforced word conversation
    assert recs[3]["word"] == "reinforced_word"
    assert recs[3]["activity_type"] == "conversation"
    assert recs[3]["priority"] == "medium"


def test_generate_personalized_scenario(client, auth_headers, db_session, test_user):
    """Test generating a personalized practice scenario matching domain and learner level."""
    vocab = Vocabulary(
        user_id=test_user.id,
        word="negotiate",
        status="learned",
        mastery_score=0.3,
    )
    db_session.add(vocab)
    db_session.commit()

    response = client.post(
        "/api/v1/personalization/scenarios/generate",
        json={
            "word": "negotiate",
            "domain": "Workplace & Business",
            "weak_area_context": "Struggles with polite counter-offers",
            "target_cefr_level": "B2",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["word"] == "negotiate"
    assert len(data["situation"]) > 0
    assert len(data["prompt"]) > 0
    assert data["cefr_level"] == "B2"
    assert "Workplace" in data["domain"] or "Business" in data["domain"]


def test_personalization_user_isolation(client, auth_headers, db_session, test_user):
    """Test user isolation: other user's weak words and reviews do not leak into current user's profile."""
    other_user = User(
        email="other_learner@example.com",
        hashed_password=hash_password("password123"),
        full_name="Other Learner",
    )
    db_session.add(other_user)
    db_session.commit()

    # Add struggling word for other user
    other_vocab = Vocabulary(
        user_id=other_user.id,
        word="secret_other_word",
        status="struggling",
        mastery_score=0.1,
    )
    db_session.add(other_vocab)
    db_session.commit()

    # Current test_user profile should NOT contain other_vocab
    response = client.get("/api/v1/personalization/profile", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_vocabulary"] == 0
    assert all(w["word"] != "secret_other_word" for w in data["weak_words"])

    # Recommendations should NOT contain other_vocab
    recs_resp = client.get("/api/v1/personalization/recommendations", headers=auth_headers)
    assert recs_resp.status_code == 200
    recs_data = recs_resp.json()
    assert all(r["word"] != "secret_other_word" for r in recs_data["recommendations"])


def test_personalization_unauthorized_access_rejected(client):
    """Test unauthenticated requests return 401 Unauthorized."""
    assert client.get("/api/v1/personalization/profile").status_code == 401
    assert client.get("/api/v1/personalization/recommendations").status_code == 401
    assert client.post("/api/v1/personalization/scenarios/generate", json={"word": "test"}).status_code == 401
