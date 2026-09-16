import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status

from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.user import User
from models.practice import PracticeSession, PracticeAttempt, MultiWordPracticeSession, MultiWordPracticeAttempt
from utils.security import create_access_token, hash_password


def create_mock_vocabulary(db, user_id: str, word: str, vocab_status: str = "new", mastery: float = 0.0, due: bool = False):
    vocab = Vocabulary(
        user_id=user_id,
        word=word,
        status=vocab_status,
        mastery_score=mastery,
        practice_count=1 if vocab_status in ("practiced", "recalled", "reinforced", "mastered") else 0,
        successful_usage_count=1 if vocab_status in ("practiced", "recalled", "reinforced", "mastered") else 0,
        next_review_at=datetime.now(timezone.utc) - timedelta(hours=2) if due else datetime.now(timezone.utc) + timedelta(days=2),
    )
    db.add(vocab)
    db.commit()
    db.refresh(vocab)

    details = WordDetails(
        vocabulary_id=vocab.id,
        simple_meaning=f"Definition of {word}",
        part_of_speech="verb",
        pronunciation_text=f"/{word}/",
        cefr_level="B1",
        difficulty_score=4.0,
        synonyms=[],
        antonyms=[],
        word_forms={},
        collocations=[],
    )
    db.add(details)

    ex = VocabularyExample(
        vocabulary_id=vocab.id,
        context_label="Workplace",
        example_text=f"Example using {word} in the workplace.",
        order_index=0,
    )
    db.add(ex)
    db.commit()
    db.refresh(vocab)
    return vocab


def test_daily_plan_empty_state(client, auth_headers, test_user):
    response = client.get("/api/v1/daily/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "date" in data
    assert data["daily_goal_target"] == 5
    assert data["daily_goal_progress"] == 0
    assert data["is_goal_completed"] is False
    assert len(data["tasks"]) == 4

    # Verify task ordering
    priorities = [t["priority"] for t in data["tasks"]]
    assert priorities == [1, 2, 3, 4]

    task_types = [t["task_type"] for t in data["tasks"]]
    assert task_types == ["reviews_due", "struggling_practice", "learn_new", "use_my_vocabulary"]

    # In empty state: reviews completed (0 due), struggling completed (0 struggling), learn_new pending (0), multi-word locked
    task_map = {t["task_type"]: t for t in data["tasks"]}
    assert task_map["reviews_due"]["status"] == "completed"
    assert task_map["struggling_practice"]["status"] == "completed"
    assert task_map["use_my_vocabulary"]["status"] == "locked"


def test_daily_plan_prioritization_with_learning_data(client, auth_headers, test_user, db_session):
    # Create 2 due reviews
    create_mock_vocabulary(db_session, test_user.id, "hesitate", "practiced", 0.4, due=True)
    create_mock_vocabulary(db_session, test_user.id, "vividly", "recalled", 0.6, due=True)

    # Create 1 struggling word
    create_mock_vocabulary(db_session, test_user.id, "hassle", "struggling", 0.2, due=False)

    # Create 1 new word
    create_mock_vocabulary(db_session, test_user.id, "persevere", "new", 0.0, due=False)

    response = client.get("/api/v1/daily/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    task_map = {t["task_type"]: t for t in data["tasks"]}

    # Priority 1: Due reviews pending (count: 2)
    assert task_map["reviews_due"]["status"] == "pending"
    assert task_map["reviews_due"]["item_count"] == 2

    # Priority 2: Struggling words pending (count: 1)
    assert task_map["struggling_practice"]["status"] == "pending"
    assert task_map["struggling_practice"]["item_count"] == 1

    # Priority 3: New words pending (count: 1)
    assert task_map["learn_new"]["status"] == "pending"
    assert task_map["learn_new"]["item_count"] == 1

    # Priority 4: Multi-word practice has only 2 practiced/recalled words -> locked (requires 3)
    assert task_map["use_my_vocabulary"]["status"] == "locked"
    assert task_map["use_my_vocabulary"]["item_count"] == 2


def test_daily_plan_unlocks_multi_word_when_eligible(client, auth_headers, test_user, db_session):
    # Add 3 practiced words
    create_mock_vocabulary(db_session, test_user.id, "hesitate", "practiced", 0.4)
    create_mock_vocabulary(db_session, test_user.id, "vividly", "recalled", 0.6)
    create_mock_vocabulary(db_session, test_user.id, "hassle", "reinforced", 0.8)

    response = client.get("/api/v1/daily/plan", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    task_map = {t["task_type"]: t for t in data["tasks"]}

    assert task_map["use_my_vocabulary"]["status"] == "ready"
    assert task_map["use_my_vocabulary"]["item_count"] == 3


def test_multi_word_eligible_vocabulary_endpoint(client, auth_headers, test_user, db_session):
    # When 0 eligible
    res0 = client.get("/api/v1/practice/multi-word/eligible", headers=auth_headers)
    assert res0.status_code == status.HTTP_200_OK
    assert res0.json()["is_eligible"] is False
    assert res0.json()["eligible_count"] == 0

    # Add 2 eligible words
    create_mock_vocabulary(db_session, test_user.id, "hesitate", "practiced")
    create_mock_vocabulary(db_session, test_user.id, "vividly", "recalled")

    res1 = client.get("/api/v1/practice/multi-word/eligible", headers=auth_headers)
    assert res1.status_code == status.HTTP_200_OK
    assert res1.json()["is_eligible"] is False
    assert res1.json()["eligible_count"] == 2

    # Add 3rd eligible word
    create_mock_vocabulary(db_session, test_user.id, "hassle", "reinforced")

    res2 = client.get("/api/v1/practice/multi-word/eligible", headers=auth_headers)
    assert res2.status_code == status.HTTP_200_OK
    assert res2.json()["is_eligible"] is True
    assert res2.json()["eligible_count"] == 3
    assert len(res2.json()["items"]) == 3


def test_start_multi_word_practice_insufficient_words_raises_400(client, auth_headers, test_user, db_session):
    # Only 1 word in total
    create_mock_vocabulary(db_session, test_user.id, "hesitate", "practiced")

    response = client.post("/api/v1/practice/multi-word", json={}, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "At least 3" in response.json()["detail"]


def test_start_multi_word_practice_success(client, auth_headers, test_user, db_session):
    v1 = create_mock_vocabulary(db_session, test_user.id, "hesitate", "practiced")
    v2 = create_mock_vocabulary(db_session, test_user.id, "vividly", "recalled")
    v3 = create_mock_vocabulary(db_session, test_user.id, "hassle", "reinforced")

    response = client.post("/api/v1/practice/multi-word", json={}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert "session_id" in data
    assert len(data["target_words"]) == 3
    words = [tw["word"] for tw in data["target_words"]]
    assert "hesitate" in words
    assert "vividly" in words
    assert "hassle" in words

    assert "situation" in data["scenario"]
    assert "prompt" in data["scenario"]


def test_start_multi_word_practice_with_specific_vocabulary_ids(client, auth_headers, test_user, db_session):
    v1 = create_mock_vocabulary(db_session, test_user.id, "hesitate", "practiced")
    v2 = create_mock_vocabulary(db_session, test_user.id, "vividly", "recalled")
    v3 = create_mock_vocabulary(db_session, test_user.id, "hassle", "reinforced")
    v4 = create_mock_vocabulary(db_session, test_user.id, "persevere", "practiced")

    # Select specific 2-3 IDs
    response = client.post(
        "/api/v1/practice/multi-word",
        json={"vocabulary_ids": [v1.id, v2.id, v4.id]},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    words = [tw["word"] for tw in data["target_words"]]
    assert set(words) == {"hesitate", "vividly", "persevere"}


def test_submit_multi_word_attempt_successful(client, auth_headers, test_user, db_session):
    v1 = create_mock_vocabulary(db_session, test_user.id, "hesitate", "practiced", 0.40)
    v2 = create_mock_vocabulary(db_session, test_user.id, "vividly", "recalled", 0.50)
    v3 = create_mock_vocabulary(db_session, test_user.id, "hassle", "reinforced", 0.60)

    # Start session
    start_res = client.post("/api/v1/practice/multi-word", json={}, headers=auth_headers)
    session_id = start_res.json()["session_id"]

    initial_xp = test_user.xp or 0

    # Submit response containing all target words
    submit_res = client.post(
        f"/api/v1/practice/multi-word/{session_id}/submit",
        json={
            "response": "I would not hesitate to adopt this solution; remembering our past challenges vividly helps us avoid unnecessary hassle for the team."
        },
        headers=auth_headers,
    )
    assert submit_res.status_code == status.HTTP_200_OK
    data = submit_res.json()

    assert data["session_id"] == session_id
    assert data["is_successful"] is True
    assert data["scores"]["overall"] >= 6.0
    assert data["xp_earned"] == 20
    assert len(data["word_evaluations"]) == 3

    # Verify per-word evaluations
    for we in data["word_evaluations"]:
        assert we["used"] is True
        assert we["used_correctly"] is True
        assert we["used_naturally"] is True
        assert we["score"] >= 8.0

    # Verify XP increased by 20 (+ potential daily goal / streak bonus)
    db_session.refresh(test_user)
    assert test_user.xp >= initial_xp + 20

    # Verify vocabulary metrics updated
    db_session.refresh(v1)
    assert v1.successful_usage_count == 2
    assert v1.mastery_score > 0.40


def test_submit_multi_word_attempt_unsuccessful(client, auth_headers, test_user, db_session):
    create_mock_vocabulary(db_session, test_user.id, "hesitate", "practiced")
    create_mock_vocabulary(db_session, test_user.id, "vividly", "recalled")
    create_mock_vocabulary(db_session, test_user.id, "hassle", "reinforced")

    # Start session
    start_res = client.post("/api/v1/practice/multi-word", json={}, headers=auth_headers)
    session_id = start_res.json()["session_id"]

    # Submit response missing all target words
    submit_res = client.post(
        f"/api/v1/practice/multi-word/{session_id}/submit",
        json={"response": "I think we should do something different today."},
        headers=auth_headers,
    )
    assert submit_res.status_code == status.HTTP_200_OK
    data = submit_res.json()

    assert data["is_successful"] is False
    assert data["scores"]["overall"] < 6.0
    assert data["xp_earned"] == 5
    for we in data["word_evaluations"]:
        assert we["used"] is False


def test_get_and_list_multi_word_sessions(client, auth_headers, test_user, db_session):
    create_mock_vocabulary(db_session, test_user.id, "hesitate", "practiced")
    create_mock_vocabulary(db_session, test_user.id, "vividly", "recalled")
    create_mock_vocabulary(db_session, test_user.id, "hassle", "reinforced")

    start_res = client.post("/api/v1/practice/multi-word", json={}, headers=auth_headers)
    session_id = start_res.json()["session_id"]

    # Submit an attempt
    client.post(
        f"/api/v1/practice/multi-word/{session_id}/submit",
        json={"response": "Do not hesitate, remember vividly, avoid hassle."},
        headers=auth_headers,
    )

    # Get session details
    get_res = client.get(f"/api/v1/practice/multi-word/{session_id}", headers=auth_headers)
    assert get_res.status_code == status.HTTP_200_OK
    session_data = get_res.json()
    assert session_data["id"] == session_id
    assert session_data["total_attempts"] == 1
    assert len(session_data["attempts"]) == 1

    # List sessions
    list_res = client.get("/api/v1/practice/multi-word/sessions", headers=auth_headers)
    assert list_res.status_code == status.HTTP_200_OK
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert len(list_data["items"]) >= 1


def test_multi_word_user_isolation(client, db_session):
    user_a = User(
        email="usera_multi@example.com",
        full_name="User A",
        hashed_password=hash_password("pw123"),
    )
    user_b = User(
        email="userb_multi@example.com",
        full_name="User B",
        hashed_password=hash_password("pw123"),
    )
    db_session.add(user_a)
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_a)
    db_session.refresh(user_b)

    create_mock_vocabulary(db_session, user_a.id, "hesitate", "practiced")
    create_mock_vocabulary(db_session, user_a.id, "vividly", "recalled")
    create_mock_vocabulary(db_session, user_a.id, "hassle", "reinforced")

    token_a = create_access_token({"sub": user_a.id, "email": user_a.email})
    token_b = create_access_token({"sub": user_b.id, "email": user_b.email})

    # User A starts session
    res_a = client.post(
        "/api/v1/practice/multi-word",
        json={},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == status.HTTP_201_CREATED
    session_id = res_a.json()["session_id"]

    # User B tries to view or submit to User A's session -> 404
    res_b_get = client.get(
        f"/api/v1/practice/multi-word/{session_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b_get.status_code == status.HTTP_404_NOT_FOUND

    res_b_post = client.post(
        f"/api/v1/practice/multi-word/{session_id}/submit",
        json={"response": "test response"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b_post.status_code == status.HTTP_404_NOT_FOUND


def test_unauthorized_access_rejected(client):
    res1 = client.get("/api/v1/daily/plan")
    assert res1.status_code == status.HTTP_401_UNAUTHORIZED

    res2 = client.get("/api/v1/practice/multi-word/eligible")
    assert res2.status_code == status.HTTP_401_UNAUTHORIZED

    res3 = client.post("/api/v1/practice/multi-word", json={})
    assert res3.status_code == status.HTTP_401_UNAUTHORIZED
