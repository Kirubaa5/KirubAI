import pytest
from datetime import datetime, timezone, timedelta
from models.vocabulary import Vocabulary, WordDetails
from models.practice import ConversationSession, ConversationMessage, ReviewRecord
from models.user import User
from utils.security import hash_password
from services.conversation_service import detect_vocabulary


# ============================================================
# Unit Tests for Vocabulary Detection
# ============================================================

def test_detect_vocabulary_exact_and_case_insensitive():
    """Verify exact and case-insensitive word matching."""
    target_words = ["hesitate", "confident", "improve"]
    text = "I used to HESITATE a lot, but now I am very confident."
    detected = detect_vocabulary(text, target_words)
    assert detected == ["hesitate", "confident"]
    assert "improve" not in detected


def test_detect_vocabulary_inflections_and_stems():
    """Verify detection of various grammatical inflections (-ed, -ing, -s, -tion, -ly)."""
    target_words = ["hesitate", "confident", "improve", "resilient"]
    text = "She hesitated for a second, but spoke confidently about her improvements."
    detected = detect_vocabulary(text, target_words)
    assert "hesitate" in detected
    assert "confident" in detected
    assert "improve" in detected
    assert "resilient" not in detected


def test_detect_vocabulary_no_false_positives():
    """Verify word boundaries prevent matching substrings inside unrelated words."""
    target_words = ["fit", "con"]
    text = "The benefit of the conference was great."
    detected = detect_vocabulary(text, target_words)
    # 'benefit' has 'fit', 'conference' has 'con', but word boundary should prevent match
    assert detected == []


# ============================================================
# API Endpoint Integration Tests
# ============================================================

def test_start_conversation_with_active_vocabulary(client, auth_headers, db_session, test_user):
    """Test starting a conversation session automatically selects active vocabulary."""
    # Seed user vocabulary
    vocab1 = Vocabulary(user_id=test_user.id, word="hesitate", status="practiced", mastery_score=0.4)
    vocab2 = Vocabulary(user_id=test_user.id, word="confident", status="recalled", mastery_score=0.6)
    vocab3 = Vocabulary(user_id=test_user.id, word="improve", status="reinforced", mastery_score=0.7)
    db_session.add_all([vocab1, vocab2, vocab3])
    db_session.commit()

    response = client.post(
        "/api/v1/conversations/start",
        json={"topic": "career planning", "use_vocabulary": True},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()

    assert "session_id" in data
    assert data["topic"] == "career planning"
    assert len(data["initial_message"]) > 0
    assert "hesitate" in data["target_vocabulary"]
    assert "confident" in data["target_vocabulary"]
    assert "improve" in data["target_vocabulary"]

    # Verify session persisted in DB
    session = db_session.query(ConversationSession).filter(ConversationSession.id == data["session_id"]).first()
    assert session is not None
    assert session.user_id == test_user.id
    assert session.status == "active"
    assert session.message_count == 1

    # Verify initial opening message persisted
    messages = db_session.query(ConversationMessage).filter(ConversationMessage.session_id == session.id).all()
    assert len(messages) == 1
    assert messages[0].role == "assistant"
    assert messages[0].order_index == 1


def test_start_conversation_fallback_when_no_vocabulary(client, auth_headers, db_session, test_user):
    """Test starting a conversation provides default target words when user has no vocabulary."""
    response = client.post(
        "/api/v1/conversations/start",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["target_vocabulary"]) > 0
    assert len(data["initial_message"]) > 0


def test_send_message_multi_turn_and_vocabulary_detection(client, auth_headers, db_session, test_user):
    """Test sending user messages detects vocabulary, updates cumulative list, and returns AI reply."""
    # Start conversation
    start_resp = client.post(
        "/api/v1/conversations/start",
        json={"topic": "job interview", "target_words": ["hesitate", "confident", "improve"]},
        headers=auth_headers,
    )
    session_id = start_resp.json()["session_id"]

    # Send first message containing 'hesitate'
    msg_resp1 = client.post(
        f"/api/v1/conversations/{session_id}/message",
        json={"content": "I usually hesitate when answering questions about my weaknesses."},
        headers=auth_headers,
    )
    assert msg_resp1.status_code == 200
    m1_data = msg_resp1.json()

    assert "message_id" in m1_data
    assert len(m1_data["response"]) > 0
    assert m1_data["vocabulary_detected"] == ["hesitate"]
    assert m1_data["vocabulary_used"] == ["hesitate"]

    # Send second message containing 'confident' and 'improve'
    msg_resp2 = client.post(
        f"/api/v1/conversations/{session_id}/message",
        json={"content": "However, I feel confident that I can improve quickly with practice."},
        headers=auth_headers,
    )
    assert msg_resp2.status_code == 200
    m2_data = msg_resp2.json()

    assert "confident" in m2_data["vocabulary_detected"]
    assert "improve" in m2_data["vocabulary_detected"]
    assert "hesitate" in m2_data["vocabulary_used"]
    assert "confident" in m2_data["vocabulary_used"]
    assert "improve" in m2_data["vocabulary_used"]

    # Verify message persistence and order indices
    messages = (
        db_session.query(ConversationMessage)
        .filter(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.order_index.asc())
        .all()
    )
    # Order: 1=assistant (init), 2=user, 3=assistant, 4=user, 5=assistant
    assert len(messages) == 5
    assert [m.role for m in messages] == ["assistant", "user", "assistant", "user", "assistant"]
    assert [m.order_index for m in messages] == [1, 2, 3, 4, 5]


def test_end_conversation_evaluation_xp_and_mastery_integration(client, auth_headers, db_session, test_user):
    """Test ending a conversation generates evaluation, awards 20 XP, and updates mastery logic."""
    initial_xp = test_user.xp

    # Setup vocabulary in database
    vocab = Vocabulary(
        user_id=test_user.id,
        word="hesitate",
        status="learned",
        mastery_score=0.2,
        practice_count=1,
        successful_usage_count=0,
    )
    db_session.add(vocab)
    db_session.commit()

    # Start session with 'hesitate' and 'confident'
    start_resp = client.post(
        "/api/v1/conversations/start",
        json={"topic": "public speaking", "target_words": ["hesitate", "confident"]},
        headers=auth_headers,
    )
    session_id = start_resp.json()["session_id"]

    # Send message using 'hesitate'
    client.post(
        f"/api/v1/conversations/{session_id}/message",
        json={"content": "I always hesitate before giving a speech."},
        headers=auth_headers,
    )

    # End conversation
    end_resp = client.post(
        f"/api/v1/conversations/{session_id}/end",
        headers=auth_headers,
    )
    assert end_resp.status_code == 200
    end_data = end_resp.json()

    assert end_data["session_id"] == session_id
    assert end_data["status"] == "ended"
    assert end_data["xp_earned"] == 20

    evaluation = end_data["evaluation"]
    assert "hesitate" in evaluation["vocabulary_used"]
    assert "confident" in evaluation["vocabulary_missed"]
    assert evaluation["overall_fluency"] > 0
    assert len(evaluation["feedback"]) > 0
    assert "hesitate" in evaluation["usage_quality"]

    # Verify User XP was incremented by 20
    db_session.refresh(test_user)
    assert test_user.xp == initial_xp + 20

    # Verify Vocabulary status and mastery updated via Phase 5 domain logic
    db_session.refresh(vocab)
    assert vocab.successful_usage_count == 1
    assert vocab.status == "practiced"  # Transitioned from 'learned' to 'practiced'
    assert vocab.mastery_score > 0.2


def test_conversation_reinforced_to_mastered_transition(client, auth_headers, db_session, test_user):
    """Test transition from REINFORCED to MASTERED when 3+ successful reviews and conversation usage occur."""
    vocab = Vocabulary(
        user_id=test_user.id,
        word="resilient",
        status="reinforced",
        mastery_score=0.75,
        practice_count=5,
        successful_usage_count=5,
        created_at=datetime.now(timezone.utc) - timedelta(days=35),
    )
    db_session.add(vocab)
    db_session.commit()

    # Add 4 successful review records for this word (satisfying 3+ reviews)
    for _ in range(4):
        rec = ReviewRecord(
            user_id=test_user.id,
            vocabulary_id=vocab.id,
            review_type="recall",
            recall_successful=True,
            previous_interval_days=7,
            new_interval_days=14,
            previous_status="reinforced",
            new_status="reinforced",
        )
        db_session.add(rec)
    db_session.commit()

    # Start and conduct conversation using 'resilient'
    start_resp = client.post(
        "/api/v1/conversations/start",
        json={"topic": "mental strength", "target_words": ["resilient"]},
        headers=auth_headers,
    )
    session_id = start_resp.json()["session_id"]

    client.post(
        f"/api/v1/conversations/{session_id}/message",
        json={"content": "Staying resilient helped me overcome many difficulties."},
        headers=auth_headers,
    )

    # End conversation
    end_resp = client.post(f"/api/v1/conversations/{session_id}/end", headers=auth_headers)
    assert end_resp.status_code == 200

    db_session.refresh(vocab)
    assert vocab.status == "mastered"
    assert vocab.mastery_score >= 0.8


def test_get_conversation_detail(client, auth_headers, db_session, test_user):
    """Test retrieving conversation detail with messages and evaluation."""
    start_resp = client.post(
        "/api/v1/conversations/start",
        json={"topic": "music and arts", "target_words": ["creative", "inspire"]},
        headers=auth_headers,
    )
    session_id = start_resp.json()["session_id"]

    client.post(
        f"/api/v1/conversations/{session_id}/message",
        json={"content": "Listening to classical music is very creative and inspiring."},
        headers=auth_headers,
    )
    client.post(f"/api/v1/conversations/{session_id}/end", headers=auth_headers)

    # Get conversation detail
    detail_resp = client.get(f"/api/v1/conversations/{session_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()

    assert detail["id"] == session_id
    assert detail["user_id"] == test_user.id
    assert detail["topic"] == "music and arts"
    assert detail["status"] == "ended"
    assert len(detail["messages"]) >= 3
    assert detail["evaluation"] is not None


def test_list_conversations_pagination(client, auth_headers, db_session, test_user):
    """Test listing conversations with pagination."""
    for i in range(3):
        client.post(
            "/api/v1/conversations/start",
            json={"topic": f"Topic {i+1}"},
            headers=auth_headers,
        )

    list_resp = client.get("/api/v1/conversations?page=1&per_page=2", headers=auth_headers)
    assert list_resp.status_code == 200
    data = list_resp.json()

    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["pages"] == 2


def test_conversation_user_isolation(client, auth_headers, db_session, test_user):
    """Test strict isolation preventing users from accessing or modifying other users' conversations."""
    other_user = User(
        email="other@example.com",
        hashed_password=hash_password("password123"),
        full_name="Other User",
    )
    db_session.add(other_user)
    db_session.commit()

    # Create session for other_user
    other_session = ConversationSession(
        user_id=other_user.id,
        topic="Private Topic",
        status="active",
    )
    db_session.add(other_session)
    db_session.commit()

    # test_user cannot get other_user's session -> 404
    get_resp = client.get(f"/api/v1/conversations/{other_session.id}", headers=auth_headers)
    assert get_resp.status_code == 404

    # test_user cannot send message to other_user's session -> 404
    msg_resp = client.post(
        f"/api/v1/conversations/{other_session.id}/message",
        json={"content": "Hello"},
        headers=auth_headers,
    )
    assert msg_resp.status_code == 404

    # test_user cannot end other_user's session -> 404
    end_resp = client.post(f"/api/v1/conversations/{other_session.id}/end", headers=auth_headers)
    assert end_resp.status_code == 404


def test_cannot_send_message_to_ended_session(client, auth_headers):
    """Test that sending a message to an already completed conversation returns 400 Bad Request."""
    start_resp = client.post("/api/v1/conversations/start", json={}, headers=auth_headers)
    session_id = start_resp.json()["session_id"]

    # End session
    client.post(f"/api/v1/conversations/{session_id}/end", headers=auth_headers)

    # Attempt to send message
    msg_resp = client.post(
        f"/api/v1/conversations/{session_id}/message",
        json={"content": "Are you still there?"},
        headers=auth_headers,
    )
    assert msg_resp.status_code == 400
    assert "already ended" in msg_resp.json()["detail"].lower()


def test_unauthorized_access_rejected(client):
    """Test unauthenticated requests are rejected with 401."""
    assert client.post("/api/v1/conversations/start").status_code == 401
    assert client.get("/api/v1/conversations").status_code == 401
    assert client.get("/api/v1/conversations/123").status_code == 401
    assert client.post("/api/v1/conversations/123/message", json={"content": "hi"}).status_code == 401
    assert client.post("/api/v1/conversations/123/end").status_code == 401
