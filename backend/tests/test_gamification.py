import uuid
from datetime import datetime, timezone, timedelta
from fastapi import status

from models.user import User
from models.vocabulary import Vocabulary
from models.practice import PracticeSession, PracticeAttempt, ReviewRecord, ConversationSession
from models.achievement import UserAchievement
from services.gamification_service import GamificationService, calculate_level_info, get_level_title
from utils.security import hash_password, create_access_token


def test_level_formula_progression():
    """Verify deterministic level calculation across various XP values."""
    # Level 1 (0-99 XP)
    l1_0 = calculate_level_info(0)
    assert l1_0["level"] == 1
    assert l1_0["title"] == "Novice Explorer"
    assert l1_0["current_level_xp"] == 0
    assert l1_0["next_level_xp"] == 100
    assert l1_0["xp_within_level"] == 0
    assert l1_0["progress_percentage"] == 0.0

    l1_50 = calculate_level_info(50)
    assert l1_50["level"] == 1
    assert l1_50["xp_within_level"] == 50
    assert l1_50["progress_percentage"] == 50.0

    # Level 2 (100-199 XP)
    l2 = calculate_level_info(100)
    assert l2["level"] == 2
    assert l2["title"] == "Curious Learner"
    assert l2["current_level_xp"] == 100
    assert l2["next_level_xp"] == 200
    assert l2["xp_within_level"] == 0
    assert l2["progress_percentage"] == 0.0

    l2_75 = calculate_level_info(175)
    assert l2_75["level"] == 2
    assert l2_75["xp_within_level"] == 75
    assert l2_75["progress_percentage"] == 75.0

    # Level 3 (200-299 XP)
    l3 = calculate_level_info(240)
    assert l3["level"] == 3
    assert l3["title"] == "Word Builder"
    assert l3["xp_within_level"] == 40
    assert l3["progress_percentage"] == 40.0

    # Higher levels
    l10 = calculate_level_info(950)
    assert l10["level"] == 10
    assert l10["title"] == "Polyglot Champion"


def test_award_xp_service(db_session, test_user):
    """Test award_xp correctly increases XP and adjusts level."""
    assert test_user.xp == 0
    assert test_user.level == 1

    GamificationService.award_xp(db_session, test_user, 150)
    assert test_user.xp == 150
    assert test_user.level == 2

    GamificationService.award_xp(db_session, test_user, 100)
    assert test_user.xp == 250
    assert test_user.level == 3


def test_achievement_unlock_vocabulary(db_session, test_user):
    """Test vocabulary count achievement unlocks (first_word, word_collector, lexicon_master)."""
    # 0 words -> no achievements
    unlocked = GamificationService.evaluate_achievements(db_session, test_user)
    assert len(unlocked) == 0

    # Add 1 word
    v1 = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        word="eloquent",
        status="learned",
    )
    db_session.add(v1)
    db_session.commit()

    unlocked = GamificationService.evaluate_achievements(db_session, test_user)
    assert len(unlocked) == 1
    assert unlocked[0].achievement_key == "first_word"

    # Repeated evaluation is idempotent
    unlocked_repeat = GamificationService.evaluate_achievements(db_session, test_user)
    assert len(unlocked_repeat) == 0

    # Add 9 more words to reach 10 words
    for i in range(2, 11):
        v = Vocabulary(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            word=f"word{i}",
            status="learned",
        )
        db_session.add(v)
    db_session.commit()

    unlocked_10 = GamificationService.evaluate_achievements(db_session, test_user)
    assert len(unlocked_10) == 1
    assert unlocked_10[0].achievement_key == "word_collector"


def test_achievement_unlock_practice_and_reviews(db_session, test_user):
    """Test practice and review achievement unlocks."""
    # Create practice session and attempts
    ps = PracticeSession(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        vocabulary_id=str(uuid.uuid4()),
        session_type="scenario",
        status="completed",
    )
    db_session.add(ps)
    db_session.commit()

    attempt = PracticeAttempt(
        id=str(uuid.uuid4()),
        session_id=ps.id,
        vocabulary_id=str(uuid.uuid4()),
        scenario_text="Scenario test",
        user_response="Response test",
        vocabulary_usage_score=8.0,
        grammar_score=8.0,
        context_score=8.0,
        naturalness_score=8.0,
        overall_score=8.0,
        feedback="Great response",
        is_successful=True,
    )
    db_session.add(attempt)

    # Add 1 review record
    rr = ReviewRecord(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        vocabulary_id=str(uuid.uuid4()),
        review_type="recall",
        recall_successful=True,
        response_text="answer",
        score=10.0,
        feedback="Perfect recall",
        previous_interval_days=1,
        new_interval_days=3,
        previous_status="learned",
        new_status="practiced",
    )
    db_session.add(rr)
    db_session.commit()

    unlocked = GamificationService.evaluate_achievements(db_session, test_user)
    keys = {u.achievement_key for u in unlocked}
    assert "first_step" in keys
    assert "active_recall" in keys


def test_achievement_unlock_conversation_and_mastery(db_session, test_user):
    """Test conversation and mastery achievements."""
    # Add conversation session
    cs = ConversationSession(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        topic="Technology",
        status="ended",
    )
    db_session.add(cs)

    # Add mastered vocabulary
    v_mastered = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        word="resilient",
        status="mastered",
        mastery_score=1.0,
    )
    db_session.add(v_mastered)
    db_session.commit()

    unlocked = GamificationService.evaluate_achievements(db_session, test_user)
    keys = {u.achievement_key for u in unlocked}
    assert "chat_starter" in keys
    assert "first_mastery" in keys
    assert "first_word" in keys


def test_achievement_unlock_streak(db_session, test_user):
    """Test streak achievements (streak_starter, consistency_king)."""
    test_user.current_streak = 3
    test_user.longest_streak = 3
    db_session.commit()

    unlocked = GamificationService.evaluate_achievements(db_session, test_user)
    keys = {u.achievement_key for u in unlocked}
    assert "streak_starter" in keys
    assert "consistency_king" not in keys

    test_user.current_streak = 7
    test_user.longest_streak = 7
    db_session.commit()

    unlocked_7 = GamificationService.evaluate_achievements(db_session, test_user)
    keys_7 = {u.achievement_key for u in unlocked_7}
    assert "consistency_king" in keys_7


def test_api_gamification_overview(client, auth_headers, db_session, test_user):
    """Test GET /api/v1/gamification/overview."""
    test_user.xp = 180
    test_user.level = 2
    test_user.current_streak = 4
    test_user.longest_streak = 5
    test_user.daily_goal = 5

    # Add a vocabulary word to trigger first_word unlock
    v = Vocabulary(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        word="pragmatic",
        status="learned",
    )
    db_session.add(v)
    db_session.commit()

    response = client.get("/api/v1/gamification/overview", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["level"] == 2
    assert data["level_title"] == "Curious Learner"
    assert data["total_xp"] == 180
    assert data["current_level_xp"] == 100
    assert data["next_level_xp"] == 200
    assert data["xp_within_level"] == 80
    assert data["level_progress_percentage"] == 80.0
    assert data["current_streak"] == 4
    assert data["longest_streak"] == 5
    assert data["daily_goal"] == 5
    assert data["unlocked_achievements_count"] >= 1
    assert data["total_achievements_count"] == 16
    assert len(data["recent_achievements"]) >= 1
    assert len(data["next_achievements"]) >= 1


def test_api_gamification_achievements(client, auth_headers, db_session, test_user):
    """Test GET /api/v1/gamification/achievements returns full catalogue with progress."""
    response = client.get("/api/v1/gamification/achievements", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total"] == 16
    assert data["unlocked_count"] == 0
    assert data["completion_percentage"] == 0.0
    assert len(data["items"]) == 16

    # Verify categories
    categories = {item["category"] for item in data["items"]}
    assert "vocabulary" in categories
    assert "practice" in categories
    assert "reviews" in categories
    assert "conversations" in categories
    assert "streaks" in categories


def test_api_gamification_levels(client, auth_headers, test_user):
    """Test GET /api/v1/gamification/levels returns roadmap milestones."""
    response = client.get("/api/v1/gamification/levels", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["current_level"] == 1
    assert data["current_xp"] == 0
    assert data["level_title"] == "Novice Explorer"
    assert len(data["levels"]) >= 10

    first_lvl = data["levels"][0]
    assert first_lvl["level"] == 1
    assert first_lvl["title"] == "Novice Explorer"
    assert first_lvl["is_unlocked"] is True
    assert first_lvl["is_current"] is True

    second_lvl = data["levels"][1]
    assert second_lvl["level"] == 2
    assert second_lvl["is_unlocked"] is False
    assert second_lvl["is_current"] is False


def test_user_isolation(client, auth_headers, db_session, test_user):
    """Test gamification data is strictly isolated between users."""
    # Create another user
    other_user = User(
        email="other@example.com",
        full_name="Other User",
        hashed_password=hash_password("pass123"),
        xp=500,
        level=6,
        current_streak=10,
    )
    db_session.add(other_user)
    db_session.commit()

    ua_other = UserAchievement(
        id=str(uuid.uuid4()),
        user_id=other_user.id,
        achievement_key="lexicon_master",
    )
    db_session.add(ua_other)
    db_session.commit()

    # Query as test_user
    res = client.get("/api/v1/gamification/overview", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_xp"] == test_user.xp
    assert data["level"] == test_user.level
    assert data["current_streak"] == test_user.current_streak

    # Query achievements as test_user -> should not have other_user's unlocked achievement
    res_ach = client.get("/api/v1/gamification/achievements", headers=auth_headers)
    ach_data = res_ach.json()
    lexicon_item = next(item for item in ach_data["items"] if item["key"] == "lexicon_master")
    assert lexicon_item["is_unlocked"] is False


def test_unauthorized_access(client):
    """Test unauthenticated requests are rejected."""
    r1 = client.get("/api/v1/gamification/overview")
    assert r1.status_code == status.HTTP_401_UNAUTHORIZED

    r2 = client.get("/api/v1/gamification/achievements")
    assert r2.status_code == status.HTTP_401_UNAUTHORIZED

    r3 = client.get("/api/v1/gamification/levels")
    assert r3.status_code == status.HTTP_401_UNAUTHORIZED


def test_regression_duplicate_vocabulary_does_not_repeat_xp(client, auth_headers, db_session, test_user):
    """Regression test proving duplicate vocabulary creation/learning does not repeatedly award XP."""
    initial_xp = test_user.xp or 0

    # 1. Add word via API
    res1 = client.post("/api/v1/vocabulary", json={"word": "innovative"}, headers=auth_headers)
    assert res1.status_code == status.HTTP_201_CREATED
    vocab_id = res1.json()["id"]

    # 2. Attempting to add same word again returns 409 Conflict
    res_dup = client.post("/api/v1/vocabulary", json={"word": "innovative"}, headers=auth_headers)
    assert res_dup.status_code == status.HTTP_409_CONFLICT

    # 3. Mark word learned -> awards 10 XP
    res_learn = client.post(f"/api/v1/vocabulary/{vocab_id}/mark-learned", headers=auth_headers)
    assert res_learn.status_code == status.HTTP_200_OK

    db_session.refresh(test_user)
    assert test_user.xp == initial_xp + 10

    # 4. Repeated mark_word_learned on already learned word does NOT award extra XP
    res_learn_again = client.post(f"/api/v1/vocabulary/{vocab_id}/mark-learned", headers=auth_headers)
    assert res_learn_again.status_code == status.HTTP_200_OK

    db_session.refresh(test_user)
    assert test_user.xp == initial_xp + 10  # XP remains unchanged
