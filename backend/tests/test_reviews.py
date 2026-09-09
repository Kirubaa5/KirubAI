import pytest
from datetime import datetime, timezone, timedelta
from services.spaced_repetition import (
    calculate_next_review,
    calculate_mastery,
    determine_status_transition,
    REVIEW_INTERVALS,
)
from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.practice import ReviewRecord


# ============================================================
# Pure Function Domain Tests (Deterministic Spaced Repetition)
# ============================================================

def test_spaced_repetition_intervals_progression():
    """Verify standard progression: 1d -> 3d -> 7d -> 14d -> 30d."""
    # 1 -> 3
    interval, next_dt = calculate_next_review(1, recall_successful=True, consecutive_successes=1)
    assert interval == 3
    assert next_dt > datetime.now(timezone.utc)

    # 3 -> 7
    interval, _ = calculate_next_review(3, recall_successful=True, consecutive_successes=2)
    assert interval == 7

    # 7 -> 14 (with streak bonus >= 3: 14 * 1.2 = 16)
    interval, _ = calculate_next_review(7, recall_successful=True, consecutive_successes=3)
    assert interval == 16  # int(14 * 1.2)

    # 14 -> 30 (with streak bonus >= 3: 30 * 1.2 = 36)
    interval, _ = calculate_next_review(14, recall_successful=True, consecutive_successes=4)
    assert interval == 36  # int(30 * 1.2)

    # 30 -> 1.5x = 45 (streak bonus >= 3: 45 * 1.2 = 54)
    interval, _ = calculate_next_review(30, recall_successful=True, consecutive_successes=5)
    assert interval == 54


def test_spaced_repetition_cap_at_90_days():
    """Verify maximum interval is capped at 90 days."""
    interval, _ = calculate_next_review(80, recall_successful=True, consecutive_successes=5)
    assert interval <= 90


def test_spaced_repetition_failure_reduction():
    """Verify interval reduction on failure."""
    # 1 failure: current // 2
    interval, _ = calculate_next_review(14, recall_successful=False, consecutive_failures=1)
    assert interval == 7

    interval, _ = calculate_next_review(7, recall_successful=False, consecutive_failures=1)
    assert interval == 3

    # 2 consecutive failures: current // 3
    interval, _ = calculate_next_review(14, recall_successful=False, consecutive_failures=2)
    assert interval == 4  # 14 // 3 = 4

    # 3+ consecutive failures: reset to 1
    interval, _ = calculate_next_review(30, recall_successful=False, consecutive_failures=3)
    assert interval == 1

    interval, _ = calculate_next_review(14, recall_successful=False, consecutive_failures=4)
    assert interval == 1


def test_mastery_calculation_bounds():
    """Verify mastery score is bounded [0.0, 1.0] and handles varied metrics."""
    # Zero metrics
    m0 = calculate_mastery(
        practice_count=0,
        successful_practice_count=0,
        consecutive_successful_recalls=0,
        unique_contexts_used=0,
        reviews_completed_on_time=0,
        total_reviews_due=1,
        days_since_added=0,
    )
    assert m0 == 0.0

    # High metrics
    m_max = calculate_mastery(
        practice_count=10,
        successful_practice_count=10,
        consecutive_successful_recalls=5,
        unique_contexts_used=5,
        reviews_completed_on_time=5,
        total_reviews_due=5,
        days_since_added=30,
    )
    assert m_max == 1.0

    # Intermediate metrics
    m_mid = calculate_mastery(
        practice_count=5,
        successful_practice_count=3,
        consecutive_successful_recalls=2,
        unique_contexts_used=2,
        reviews_completed_on_time=2,
        total_reviews_due=2,
        days_since_added=15,
    )
    assert 0.3 <= m_mid <= 0.7


def test_status_transitions():
    """Verify state transitions according to LEARNING_ENGINE.md."""
    # PRACTICED -> RECALLED on first success
    s1 = determine_status_transition("practiced", recall_successful=True, consecutive_successes=1, consecutive_failures=0)
    assert s1 == "recalled"

    # RECALLED -> REINFORCED after 2 consecutive successes
    s2 = determine_status_transition("recalled", recall_successful=True, consecutive_successes=2, consecutive_failures=0)
    assert s2 == "reinforced"

    # REINFORCED -> MASTERED with 3+ successes and high mastery
    s3 = determine_status_transition("reinforced", recall_successful=True, consecutive_successes=3, consecutive_failures=0, mastery_score=0.85)
    assert s3 == "mastered"

    # REINFORCED remains REINFORCED if mastery < 0.8
    s3_low = determine_status_transition("reinforced", recall_successful=True, consecutive_successes=3, consecutive_failures=0, mastery_score=0.6)
    assert s3_low == "reinforced"

    # 2 consecutive failures -> STRUGGLING
    s4 = determine_status_transition("recalled", recall_successful=False, consecutive_successes=0, consecutive_failures=2)
    assert s4 == "struggling"

    # STRUGGLING -> PRACTICED on successful recall
    s5 = determine_status_transition("struggling", recall_successful=True, consecutive_successes=1, consecutive_failures=0)
    assert s5 == "practiced"


# ============================================================
# API Endpoint Integration Tests
# ============================================================

def test_get_due_reviews_empty(client, auth_headers):
    """Test getting due reviews when none exist."""
    response = client.get("/api/v1/reviews/due", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["due_count"] == 0
    assert data["items"] == []


def test_get_due_reviews_with_items(client, auth_headers, db_session, test_user):
    """Test getting due reviews returns only due words belonging to the user."""
    # Add a practiced word due now
    vocab_due = Vocabulary(
        user_id=test_user.id,
        word="hesitate",
        status="practiced",
        mastery_score=0.4,
        next_review_at=datetime.now(timezone.utc) - timedelta(hours=1),
        review_interval_days=1,
    )
    details = WordDetails(
        vocabulary=vocab_due,
        simple_meaning="To pause before doing something because you are uncertain.",
        part_of_speech="verb",
        pronunciation_text="HEZ-ih-tayt",
        synonyms=["pause", "waver"],
        word_forms={"verb": "hesitate", "noun": "hesitation"},
    )
    ex = VocabularyExample(
        vocabulary=vocab_due,
        example_text="I hesitated before opening the envelope.",
        context_label="Workplace",
        order_index=0,
    )
    db_session.add_all([vocab_due, details, ex])

    # Add a word that is NOT due yet (next_review_at in the future)
    vocab_future = Vocabulary(
        user_id=test_user.id,
        word="confident",
        status="practiced",
        mastery_score=0.5,
        next_review_at=datetime.now(timezone.utc) + timedelta(days=3),
        review_interval_days=3,
    )
    db_session.add(vocab_future)
    db_session.commit()

    response = client.get("/api/v1/reviews/due", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["due_count"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["vocabulary_id"] == vocab_due.id
    assert item["word"] == "hesitate"
    assert item["status"] == "practiced"
    assert item["prompt"]["prompt_type"] == "recall"
    assert item["prompt"]["definition"] == "To pause before doing something because you are uncertain."
    assert item["prompt"]["part_of_speech"] == "verb"
    # Cloze sentence should have the word blanked out
    assert "_____" in item["prompt"]["cloze_sentence"]
    assert "hesitated" not in item["prompt"]["cloze_sentence"]


def test_submit_review_success_progression(client, auth_headers, db_session, test_user):
    """Test submitting a successful review answer advances status and interval."""
    vocab = Vocabulary(
        user_id=test_user.id,
        word="diligent",
        status="practiced",
        mastery_score=0.3,
        review_interval_days=1,
        next_review_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    details = WordDetails(
        vocabulary=vocab,
        simple_meaning="Having or showing care and conscientiousness in one's work.",
        part_of_speech="adjective",
        pronunciation_text="DIL-ih-junt",
    )
    db_session.add_all([vocab, details])
    db_session.commit()

    # Submit correct answer
    response = client.post(
        "/api/v1/reviews/submit",
        json={
            "vocabulary_id": vocab.id,
            "review_type": "recall",
            "response_text": "diligent",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()

    assert result["recall_successful"] is True
    assert result["score"] == 10.0
    assert result["previous_status"] == "practiced"
    assert result["new_status"] == "recalled"
    assert result["previous_interval_days"] == 1
    assert result["new_interval_days"] == 3
    assert result["xp_earned"] == 10
    assert result["target_word"] == "diligent"

    # Verify DB persistence
    db_session.refresh(vocab)
    assert vocab.status == "recalled"
    assert vocab.review_interval_days == 3
    assert vocab.last_reviewed_at is not None

    # Check ReviewRecord
    records = db_session.query(ReviewRecord).filter(ReviewRecord.vocabulary_id == vocab.id).all()
    assert len(records) == 1
    assert records[0].recall_successful is True
    assert records[0].new_status == "recalled"
    assert records[0].new_interval_days == 3


def test_submit_review_failure_progression(client, auth_headers, db_session, test_user):
    """Test submitting a failed review answer resets interval and transitions to struggling on repeat failures."""
    vocab = Vocabulary(
        user_id=test_user.id,
        word="resilient",
        status="recalled",
        mastery_score=0.5,
        review_interval_days=7,
        next_review_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    details = WordDetails(
        vocabulary=vocab,
        simple_meaning="Able to withstand or recover quickly from difficult conditions.",
        part_of_speech="adjective",
    )
    db_session.add_all([vocab, details])
    db_session.commit()

    # First failure
    resp1 = client.post(
        "/api/v1/reviews/submit",
        json={
            "vocabulary_id": vocab.id,
            "review_type": "recall",
            "response_text": "incorrect_word",
        },
        headers=auth_headers,
    )
    assert resp1.status_code == 200
    r1 = resp1.json()
    assert r1["recall_successful"] is False
    assert r1["previous_interval_days"] == 7
    assert r1["new_interval_days"] == 3  # 7 // 2 = 3
    assert r1["xp_earned"] == 3

    # Second failure -> should transition to 'struggling'
    resp2 = client.post(
        "/api/v1/reviews/submit",
        json={
            "vocabulary_id": vocab.id,
            "review_type": "recall",
            "response_text": "still_wrong",
        },
        headers=auth_headers,
    )
    assert resp2.status_code == 200
    r2 = resp2.json()
    assert r2["recall_successful"] is False
    assert r2["new_status"] == "struggling"
    assert r2["new_interval_days"] == 1  # 3 // 3 = 1


def test_review_history_endpoint(client, auth_headers, db_session, test_user):
    """Test getting paginated review history."""
    vocab = Vocabulary(
        user_id=test_user.id,
        word="eloquent",
        status="recalled",
    )
    db_session.add(vocab)
    db_session.commit()

    # Create 3 review records
    for i in range(3):
        rec = ReviewRecord(
            user_id=test_user.id,
            vocabulary_id=vocab.id,
            review_type="recall",
            recall_successful=True,
            response_text="eloquent",
            score=10.0,
            feedback="Correct!",
            previous_interval_days=1 if i == 0 else 3,
            new_interval_days=3 if i == 0 else 7,
            previous_status="practiced" if i == 0 else "recalled",
            new_status="recalled" if i == 0 else "reinforced",
        )
        db_session.add(rec)
    db_session.commit()

    response = client.get("/api/v1/reviews/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["target_word"] == "eloquent"


def test_reviews_user_isolation(client, auth_headers, db_session, test_user):
    """Test user cannot access or review words belonging to another user."""
    from models.user import User
    from utils.security import hash_password

    other_user = User(
        email="other_user@example.com",
        hashed_password=hash_password("password123"),
        full_name="Other User",
    )
    db_session.add(other_user)
    db_session.commit()

    other_vocab = Vocabulary(
        user_id=other_user.id,
        word="privilege",
        status="practiced",
        next_review_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(other_vocab)
    db_session.commit()

    # Due reviews should NOT include other_user's word
    due_resp = client.get("/api/v1/reviews/due", headers=auth_headers)
    assert due_resp.status_code == 200
    assert not any(item["vocabulary_id"] == other_vocab.id for item in due_resp.json()["items"])

    # Attempting to submit a review for other_user's word should return 404
    submit_resp = client.post(
        "/api/v1/reviews/submit",
        json={
            "vocabulary_id": other_vocab.id,
            "review_type": "recall",
            "response_text": "privilege",
        },
        headers=auth_headers,
    )
    assert submit_resp.status_code == 404
