import pytest
from datetime import datetime, timezone, timedelta
from models.vocabulary import Vocabulary, WordDetails
from models.practice import PracticeSession, PracticeAttempt, ReviewRecord, ConversationSession
from models.user import User
from utils.security import hash_password


def test_get_progress_overview_empty_state(client, auth_headers):
    """Test progress overview for a user with no learning history."""
    response = client.get("/api/v1/progress/overview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_vocabulary"] == 0
    assert data["active_vocabulary"] == 0
    assert data["mastered_count"] == 0
    assert data["struggling_count"] == 0
    assert data["average_mastery"] == 0.0
    assert data["total_practice_attempts"] == 0
    assert data["practice_accuracy"] == 0.0
    assert data["average_practice_score"] == 0.0
    assert data["total_reviews_completed"] == 0
    assert data["recall_accuracy_rate"] == 0.0
    assert data["total_conversations"] == 0
    assert data["vocabulary_used_in_conversations"] == 0
    assert data["current_streak"] == 0
    assert data["total_xp"] == 0


def test_get_progress_overview_with_data(client, auth_headers, db_session, test_user):
    """Test progress overview with vocabulary, practice, reviews, and conversations."""
    now = datetime.now(timezone.utc)

    # 1. Add vocabulary
    v1 = Vocabulary(
        user_id=test_user.id,
        word="hesitate",
        status="struggling",
        mastery_score=0.2,
    )
    v2 = Vocabulary(
        user_id=test_user.id,
        word="confident",
        status="mastered",
        mastery_score=1.0,
    )
    v3 = Vocabulary(
        user_id=test_user.id,
        word="articulate",
        status="practiced",
        mastery_score=0.6,
    )
    db_session.add_all([v1, v2, v3])
    db_session.flush()

    # 2. Add practice session & attempts
    session = PracticeSession(
        user_id=test_user.id,
        vocabulary_id=v1.id,
        session_type="scenario",
        status="completed",
    )
    db_session.add(session)
    db_session.flush()

    a1 = PracticeAttempt(
        session_id=session.id,
        vocabulary_id=v1.id,
        scenario_text="Scenario 1",
        user_response="Response 1",
        vocabulary_usage_score=9.0,
        grammar_score=9.0,
        context_score=9.0,
        naturalness_score=9.0,
        overall_score=9.0,
        feedback="Great",
        is_successful=True,
    )
    a2 = PracticeAttempt(
        session_id=session.id,
        vocabulary_id=v1.id,
        scenario_text="Scenario 2",
        user_response="Response 2",
        vocabulary_usage_score=4.0,
        grammar_score=5.0,
        context_score=5.0,
        naturalness_score=4.0,
        overall_score=4.5,
        feedback="Needs work",
        is_successful=False,
    )
    db_session.add_all([a1, a2])

    # 3. Add review records
    r1 = ReviewRecord(
        user_id=test_user.id,
        vocabulary_id=v2.id,
        review_type="recall",
        recall_successful=True,
        score=10.0,
        previous_interval_days=7,
        new_interval_days=14,
        previous_status="reinforced",
        new_status="mastered",
    )
    db_session.add(r1)

    # 4. Add conversation
    c1 = ConversationSession(
        user_id=test_user.id,
        topic="Job Interview",
        vocabulary_usage_count=3,
        status="ended",
    )
    db_session.add(c1)

    db_session.commit()

    response = client.get("/api/v1/progress/overview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_vocabulary"] == 3
    assert data["mastered_count"] == 1
    assert data["struggling_count"] == 1
    assert data["active_vocabulary"] == 1  # 'practiced'
    assert data["average_mastery"] == 0.6  # (0.2 + 1.0 + 0.6) / 3 = 0.6
    assert data["total_practice_attempts"] == 2
    assert data["practice_accuracy"] == 0.5  # 1 of 2 successful
    assert data["average_practice_score"] == 6.75  # (9.0 + 4.5) / 2 = 6.75
    assert data["total_reviews_completed"] == 1
    assert data["recall_accuracy_rate"] == 1.0
    assert data["total_conversations"] == 1
    assert data["vocabulary_used_in_conversations"] == 3


def test_get_weekly_progress(client, auth_headers, db_session, test_user):
    """Test 7-day weekly progress breakdown."""
    now = datetime.now(timezone.utc)

    # Add practice today
    v = Vocabulary(
        user_id=test_user.id,
        word="resilient",
        status="learned",
        created_at=now,
    )
    db_session.add(v)
    db_session.flush()

    session = PracticeSession(
        user_id=test_user.id,
        vocabulary_id=v.id,
        session_type="scenario",
        status="completed",
    )
    db_session.add(session)
    db_session.flush()

    attempt = PracticeAttempt(
        session_id=session.id,
        vocabulary_id=v.id,
        scenario_text="Scenario text",
        user_response="Response text",
        vocabulary_usage_score=8.0,
        grammar_score=8.0,
        context_score=8.0,
        naturalness_score=8.0,
        overall_score=8.0,
        feedback="Good",
        is_successful=True,
        created_at=now,
    )
    db_session.add(attempt)
    db_session.commit()

    response = client.get("/api/v1/progress/weekly", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["daily_progress"]) == 7
    assert data["total_practices"] >= 1
    assert data["total_words_added"] >= 1
    assert data["active_days"] >= 1
    assert data["average_accuracy_rate"] > 0


def test_get_monthly_progress(client, auth_headers, db_session, test_user):
    """Test monthly trends over 30 days."""
    now = datetime.now(timezone.utc)

    v = Vocabulary(
        user_id=test_user.id,
        word="meticulous",
        status="mastered",
        created_at=now - timedelta(days=2),
    )
    db_session.add(v)
    db_session.flush()

    review = ReviewRecord(
        user_id=test_user.id,
        vocabulary_id=v.id,
        review_type="recall",
        recall_successful=True,
        score=10.0,
        previous_interval_days=1,
        new_interval_days=3,
        previous_status="practiced",
        new_status="mastered",
        reviewed_at=now - timedelta(days=2),
    )
    db_session.add(review)
    db_session.commit()

    response = client.get("/api/v1/progress/monthly", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["trends"]) == 30
    assert data["words_learned"] >= 1
    assert data["active_days"] >= 1
    assert data["retention_rate"] == 1.0


def test_get_vocabulary_breakdown(client, auth_headers, db_session, test_user):
    """Test vocabulary status, mastery bracket, and CEFR breakdown."""
    # Seed words across statuses
    v1 = Vocabulary(
        user_id=test_user.id,
        word="new_word",
        status="new",
        mastery_score=0.1,
    )
    v2 = Vocabulary(
        user_id=test_user.id,
        word="mastered_word",
        status="mastered",
        mastery_score=0.95,
    )
    db_session.add_all([v1, v2])
    db_session.flush()

    details = WordDetails(
        vocabulary_id=v2.id,
        simple_meaning="A mastered word.",
        cefr_level="C1",
    )
    db_session.add(details)
    db_session.commit()

    response = client.get("/api/v1/progress/vocabulary-breakdown", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_words"] == 2

    # Check status breakdown
    status_map = {item["status"]: item["count"] for item in data["by_status"]}
    assert status_map["new"] == 1
    assert status_map["mastered"] == 1
    assert status_map["struggling"] == 0

    # Check brackets
    bracket_map = {item["bracket"]: item["count"] for item in data["by_mastery_bracket"]}
    assert bracket_map["0-20%"] == 1
    assert bracket_map["81-100%"] == 1

    # Check CEFR
    assert data["by_cefr_level"]["C1"] == 1
    assert data["by_cefr_level"]["Unassigned"] == 1


def test_progress_user_isolation(client, auth_headers, db_session, test_user):
    """Test user isolation across all progress endpoints."""
    other_user = User(
        email="other_progress_user@example.com",
        hashed_password=hash_password("password123"),
        full_name="Other Progress User",
    )
    db_session.add(other_user)
    db_session.commit()

    other_v = Vocabulary(
        user_id=other_user.id,
        word="private_word",
        status="mastered",
        mastery_score=0.9,
    )
    db_session.add(other_v)
    db_session.commit()

    # Query overview as test_user
    res_overview = client.get("/api/v1/progress/overview", headers=auth_headers)
    assert res_overview.status_code == 200
    assert res_overview.json()["total_vocabulary"] == 0

    # Query breakdown as test_user
    res_breakdown = client.get("/api/v1/progress/vocabulary-breakdown", headers=auth_headers)
    assert res_breakdown.status_code == 200
    assert res_breakdown.json()["total_words"] == 0


def test_progress_unauthorized(client):
    """Test progress endpoints require authentication."""
    endpoints = [
        "/api/v1/progress/overview",
        "/api/v1/progress/weekly",
        "/api/v1/progress/monthly",
        "/api/v1/progress/vocabulary-breakdown",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 401
