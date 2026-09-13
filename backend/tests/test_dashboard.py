import uuid
import pytest
from datetime import datetime, timezone, timedelta
from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.practice import PracticeSession, PracticeAttempt, ReviewRecord, ConversationSession
from models.user import User
from utils.security import hash_password


def test_get_dashboard_empty_state(client, auth_headers):
    """Test dashboard endpoint for a new user with no vocabulary or activity."""
    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Today stats
    assert data["today"]["reviews_due"] == 0
    assert data["today"]["words_to_practice"] == 0
    assert data["today"]["daily_goal_progress"] == 0
    assert data["today"]["daily_goal_target"] == 5
    assert data["today"]["word_of_the_day"] is not None
    assert len(data["today"]["word_of_the_day"]["word"]) > 0
    assert len(data["today"]["word_of_the_day"]["meaning"]) > 0

    # User stats
    assert data["stats"]["total_words"] == 0
    assert data["stats"]["mastered_words"] == 0
    assert data["stats"]["active_words"] == 0
    assert data["stats"]["struggling_words"] == 0
    assert data["stats"]["current_streak"] == 0
    assert data["stats"]["total_xp"] == 0
    assert data["stats"]["level"] == 1

    # Recent activity
    assert data["recent_activity"] == []


def test_get_dashboard_with_learning_data(client, auth_headers, db_session, test_user):
    """Test dashboard returns accurate aggregated metrics and recent activity."""
    now = datetime.now(timezone.utc)

    # 1. Add vocabulary
    v_struggling = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        word="hesitate",
        status="struggling",
        mastery_score=0.15,
        next_review_at=now - timedelta(hours=1),  # Due for review
    )
    db_session.add(v_struggling)
    db_session.flush()

    v_details = WordDetails(
        vocabulary_id=v_struggling.id,
        simple_meaning="To pause before taking action.",
        part_of_speech="verb",
        cefr_level="B1",
    )
    db_session.add(v_details)

    v_example = VocabularyExample(
        vocabulary_id=v_struggling.id,
        example_text="I hesitate when speaking in front of large crowds.",
        context_label="Speech",
        order_index=0,
    )
    db_session.add(v_example)

    v_mastered = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        word="confident",
        status="mastered",
        mastery_score=0.95,
        next_review_at=now + timedelta(days=14),
    )
    db_session.add(v_mastered)

    v_new = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        word="resilient",
        status="new",
        mastery_score=0.0,
    )
    db_session.add(v_new)

    v_learned = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        word="pragmatic",
        status="learned",
        mastery_score=0.3,
        next_review_at=now + timedelta(days=2),
    )
    db_session.add(v_learned)
    db_session.flush()

    # 2. Add practice session & attempt today
    session = PracticeSession(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        vocabulary_id=v_struggling.id,
        session_type="scenario",
        status="completed",
        total_attempts=1,
        successful_attempts=1,
    )
    db_session.add(session)
    db_session.flush()

    attempt = PracticeAttempt(
        session_id=session.id,
        vocabulary_id=v_struggling.id,
        scenario_text="You are asked to join a team project.",
        user_response="I hesitated before answering.",
        vocabulary_usage_score=9.0,
        grammar_score=8.5,
        context_score=9.0,
        naturalness_score=8.0,
        overall_score=8.6,
        feedback="Good usage.",
        is_successful=True,
        created_at=now,
    )
    db_session.add(attempt)

    # 3. Add review record today
    review = ReviewRecord(
        user_id=test_user.id,
        vocabulary_id=v_mastered.id,
        review_type="recall",
        recall_successful=True,
        score=10.0,
        previous_interval_days=7,
        new_interval_days=14,
        previous_status="reinforced",
        new_status="mastered",
        reviewed_at=now,
    )
    db_session.add(review)

    # 4. Add conversation session today
    convo = ConversationSession(
        user_id=test_user.id,
        topic="Technology & Future",
        vocabulary_usage_count=2,
        status="ended",
        started_at=now,
    )
    db_session.add(convo)

    db_session.commit()

    # Call dashboard API
    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["today"]["reviews_due"] == 1
    # Words to practice (new, learned, struggling): hesitate, resilient, pragmatic = 3
    assert data["today"]["words_to_practice"] == 3
    # Daily goal progress: 1 practice + 1 review + 1 conversation + 4 vocabs added today = 7
    assert data["today"]["daily_goal_progress"] >= 3
    assert data["today"]["word_of_the_day"]["word"] in ["hesitate", "confident", "resilient", "pragmatic"]

    assert data["stats"]["total_words"] == 4
    assert data["stats"]["mastered_words"] == 1
    assert data["stats"]["struggling_words"] == 1
    assert data["stats"]["active_words"] == 1  # 'learned' is in active statuses

    # Check recent activity items
    assert len(data["recent_activity"]) >= 3
    activity_types = [a["type"] for a in data["recent_activity"]]
    assert "practice" in activity_types
    assert "review" in activity_types
    assert "conversation" in activity_types


def test_dashboard_streak_consecutive_days(client, auth_headers, db_session, test_user):
    """Test dashboard calculates current streak from consecutive active days."""
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)

    # Activity today
    v_today = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        word="word1",
        status="new",
        created_at=now,
    )
    db_session.add(v_today)

    # Activity yesterday
    v_yesterday = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        word="word2",
        status="new",
        created_at=yesterday,
    )
    db_session.add(v_yesterday)
    db_session.commit()

    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["current_streak"] >= 2


def test_dashboard_user_isolation(client, auth_headers, db_session, test_user):
    """Test user isolation: User A never sees User B's dashboard metrics or activity."""
    other_user = User(
        id=str(uuid.uuid4()),
        email="other_dashboard_user@example.com",
        hashed_password=hash_password("password123"),
        full_name="Other User",
    )
    db_session.add(other_user)
    db_session.flush()

    # Add private data for other_user
    other_vocab = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=other_user.id,
        word="secret_word",
        status="mastered",
        mastery_score=1.0,
    )
    db_session.add(other_vocab)
    db_session.flush()

    other_review = ReviewRecord(
        user_id=other_user.id,
        vocabulary_id=other_vocab.id,
        review_type="recall",
        recall_successful=True,
        score=10.0,
        previous_interval_days=1,
        new_interval_days=3,
        previous_status="new",
        new_status="mastered",
    )
    db_session.add(other_review)
    db_session.commit()

    # Query dashboard as test_user
    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # test_user has 0 words and 0 reviews
    assert data["stats"]["total_words"] == 0
    assert data["stats"]["mastered_words"] == 0
    assert data["recent_activity"] == []


def test_dashboard_unauthorized(client):
    """Test dashboard endpoint requires authentication."""
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 401
