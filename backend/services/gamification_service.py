from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.user import User
from models.vocabulary import Vocabulary
from models.practice import PracticeSession, PracticeAttempt, ReviewRecord, ConversationSession
from models.achievement import UserAchievement
from schemas.gamification import (
    AchievementResponse,
    AchievementListResponse,
    LevelRoadmapItem,
    LevelRoadmapResponse,
    GamificationOverviewResponse,
)
from services.dashboard_service import calculate_user_streak


ACHIEVEMENT_CATALOGUE: List[Dict[str, Any]] = [
    # Vocabulary
    {
        "key": "first_word",
        "title": "First Word",
        "description": "Add and learn your first vocabulary word",
        "category": "vocabulary",
        "icon": "BookOpen",
        "target_threshold": 1,
        "metric_type": "vocabulary_count",
    },
    {
        "key": "word_collector",
        "title": "Word Collector",
        "description": "Build your vocabulary with 10 words",
        "category": "vocabulary",
        "icon": "Bookmark",
        "target_threshold": 10,
        "metric_type": "vocabulary_count",
    },
    {
        "key": "lexicon_master",
        "title": "Lexicon Master",
        "description": "Expand your vocabulary to 50 words",
        "category": "vocabulary",
        "icon": "Library",
        "target_threshold": 50,
        "metric_type": "vocabulary_count",
    },
    # Practice
    {
        "key": "first_step",
        "title": "First Step",
        "description": "Complete your first scenario practice attempt",
        "category": "practice",
        "icon": "Target",
        "target_threshold": 1,
        "metric_type": "practice_count",
    },
    {
        "key": "scenario_pro",
        "title": "Scenario Pro",
        "description": "Complete 10 scenario practice attempts",
        "category": "practice",
        "icon": "Zap",
        "target_threshold": 10,
        "metric_type": "practice_count",
    },
    {
        "key": "context_master",
        "title": "Context Master",
        "description": "Complete 25 scenario practice attempts",
        "category": "practice",
        "icon": "Award",
        "target_threshold": 25,
        "metric_type": "practice_count",
    },
    # Reviews
    {
        "key": "active_recall",
        "title": "Active Recall",
        "description": "Complete your first spaced repetition review",
        "category": "reviews",
        "icon": "Brain",
        "target_threshold": 1,
        "metric_type": "review_count",
    },
    {
        "key": "memory_champion",
        "title": "Memory Champion",
        "description": "Complete 10 spaced repetition reviews",
        "category": "reviews",
        "icon": "Sparkles",
        "target_threshold": 10,
        "metric_type": "review_count",
    },
    {
        "key": "spaced_repetition_pro",
        "title": "Spaced Repetition Pro",
        "description": "Complete 30 spaced repetition reviews",
        "category": "reviews",
        "icon": "Repeat",
        "target_threshold": 30,
        "metric_type": "review_count",
    },
    # Conversations
    {
        "key": "chat_starter",
        "title": "Chat Starter",
        "description": "Complete your first AI conversation session",
        "category": "conversations",
        "icon": "MessageSquare",
        "target_threshold": 1,
        "metric_type": "conversation_count",
    },
    {
        "key": "dialogue_star",
        "title": "Dialogue Star",
        "description": "Complete 5 AI conversation sessions",
        "category": "conversations",
        "icon": "MessageCircle",
        "target_threshold": 5,
        "metric_type": "conversation_count",
    },
    {
        "key": "natural_speaker",
        "title": "Natural Speaker",
        "description": "Complete 10 AI conversation sessions",
        "category": "conversations",
        "icon": "Mic",
        "target_threshold": 10,
        "metric_type": "conversation_count",
    },
    # Mastery / Streaks
    {
        "key": "first_mastery",
        "title": "First Mastery",
        "description": "Reach mastered status on your first word",
        "category": "streaks",
        "icon": "Trophy",
        "target_threshold": 1,
        "metric_type": "mastered_count",
    },
    {
        "key": "polymath",
        "title": "Polymath",
        "description": "Master 5 vocabulary words",
        "category": "streaks",
        "icon": "Star",
        "target_threshold": 5,
        "metric_type": "mastered_count",
    },
    {
        "key": "streak_starter",
        "title": "Streak Starter",
        "description": "Maintain a 3-day learning streak",
        "category": "streaks",
        "icon": "Flame",
        "target_threshold": 3,
        "metric_type": "streak_count",
    },
    {
        "key": "consistency_king",
        "title": "Consistency King",
        "description": "Maintain a 7-day learning streak",
        "category": "streaks",
        "icon": "Crown",
        "target_threshold": 7,
        "metric_type": "streak_count",
    },
]

LEVEL_TITLES: List[str] = [
    "Novice Explorer",         # Level 1
    "Curious Learner",         # Level 2
    "Word Builder",            # Level 3
    "Vocabulary Apprentice",   # Level 4
    "Language Practitioner",   # Level 5
    "Context Adventurer",      # Level 6
    "Fluent Thinker",          # Level 7
    "Expression Artisan",      # Level 8
    "Linguistic Master",       # Level 9
    "Polyglot Champion",       # Level 10
    "Eloquent Scholar",        # Level 11
    "Rhetoric Expert",         # Level 12
    "Language Virtuoso",       # Level 13
    "Grandmaster Speaker",     # Level 14
    "KirubAI Legend",          # Level 15+
]


def get_level_title(level: int) -> str:
    """Return deterministic title for a given level."""
    if level < 1:
        return LEVEL_TITLES[0]
    if level <= len(LEVEL_TITLES):
        return LEVEL_TITLES[level - 1]
    return f"KirubAI Legend (Tier {level - len(LEVEL_TITLES) + 1})"


def calculate_level_info(xp: int) -> Dict[str, Any]:
    """
    Deterministic level calculation formula:
    - 100 XP per level
    - Level 1: 0 - 99 XP
    - Level 2: 100 - 199 XP
    - Level L: (L-1)*100 to L*100 - 1 XP
    """
    safe_xp = max(0, xp or 0)
    level = max(1, (safe_xp // 100) + 1)
    current_level_xp = (level - 1) * 100
    next_level_xp = level * 100
    xp_within_level = safe_xp - current_level_xp
    xp_required_for_next_level = 100
    progress_percentage = min(100.0, max(0.0, round((xp_within_level / 100.0) * 100, 1)))

    return {
        "level": level,
        "title": get_level_title(level),
        "total_xp": safe_xp,
        "current_level_xp": current_level_xp,
        "next_level_xp": next_level_xp,
        "xp_within_level": xp_within_level,
        "xp_required_for_next_level": xp_required_for_next_level,
        "progress_percentage": progress_percentage,
    }


class GamificationService:
    @staticmethod
    def calculate_level(xp: int) -> Dict[str, Any]:
        """Expose deterministic level calculation."""
        return calculate_level_info(xp)

    @staticmethod
    def award_xp(db: Session, user: User, amount: int, reason: Optional[str] = None) -> User:
        """
        Deterministically award XP to user and update level.
        """
        if amount <= 0:
            return user

        user.xp = (user.xp or 0) + amount
        level_info = calculate_level_info(user.xp)
        user.level = level_info["level"]

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def evaluate_achievements(db: Session, user: User) -> List[UserAchievement]:
        """
        Deterministically evaluates user eligibility for all catalogue achievements using
        existing database metrics. Unlocking is strictly idempotent.
        """
        # 1. Gather metrics from existing database tables
        vocab_count = db.query(Vocabulary).filter(Vocabulary.user_id == user.id).count()
        mastered_count = db.query(Vocabulary).filter(
            Vocabulary.user_id == user.id,
            Vocabulary.status == "mastered"
        ).count()
        practice_count = (
            db.query(PracticeAttempt)
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(PracticeSession.user_id == user.id)
            .count()
        )
        review_count = db.query(ReviewRecord).filter(ReviewRecord.user_id == user.id).count()
        convo_count = (
            db.query(ConversationSession)
            .filter(ConversationSession.user_id == user.id)
            .count()
        )
        current_streak = calculate_user_streak(db=db, user=user)
        streak_count = max(user.current_streak or 0, user.longest_streak or 0, current_streak)

        metrics_map: Dict[str, int] = {
            "vocabulary_count": vocab_count,
            "mastered_count": mastered_count,
            "practice_count": practice_count,
            "review_count": review_count,
            "conversation_count": convo_count,
            "streak_count": streak_count,
        }

        # 2. Query existing unlocked achievements
        existing_records = (
            db.query(UserAchievement)
            .filter(UserAchievement.user_id == user.id)
            .all()
        )
        unlocked_keys = {ua.achievement_key: ua for ua in existing_records}

        newly_unlocked: List[UserAchievement] = []
        now = datetime.now(timezone.utc)

        for item in ACHIEVEMENT_CATALOGUE:
            metric_val = metrics_map.get(item["metric_type"], 0)
            if metric_val >= item["target_threshold"] and item["key"] not in unlocked_keys:
                ua = UserAchievement(
                    user_id=user.id,
                    achievement_key=item["key"],
                    achieved_at=now,
                )
                db.add(ua)
                newly_unlocked.append(ua)

        if newly_unlocked:
            db.commit()
            for ua in newly_unlocked:
                db.refresh(ua)

        return newly_unlocked

    @staticmethod
    def record_activity(db: Session, user: User) -> Dict[str, Any]:
        """
        Record user learning activity:
        - Maintains daily streaks and awards +5 XP bonus if active on a new consecutive day.
        - Checks daily goal progress and awards +25 XP when goal is reached for the day.
        - Synchronizes level and checks achievement unlocks.
        """
        now = datetime.now(timezone.utc)
        today = now.date()
        yesterday = today - timedelta(days=1)
        bonuses_awarded: Dict[str, int] = {}

        # 1. Streak update & daily streak maintenance bonus (+5 XP)
        if user.last_active_date != today:
            if user.last_active_date == yesterday:
                user.current_streak = (user.current_streak or 0) + 1
                user.longest_streak = max(user.longest_streak or 0, user.current_streak)
                # Award streak maintenance bonus (+5 XP)
                user.xp = (user.xp or 0) + 5
                bonuses_awarded["streak_maintenance_xp"] = 5
            elif user.last_active_date is None or (today - user.last_active_date).days > 1:
                user.current_streak = 1
                user.longest_streak = max(user.longest_streak or 0, 1)

            user.last_active_date = today

        # 2. Daily Goal Check & Bonus (+25 XP)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        p_today = (
            db.query(func.count(PracticeAttempt.id))
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(PracticeSession.user_id == user.id, PracticeAttempt.created_at >= today_start)
            .scalar() or 0
        )
        r_today = (
            db.query(func.count(ReviewRecord.id))
            .filter(ReviewRecord.user_id == user.id, ReviewRecord.reviewed_at >= today_start)
            .scalar() or 0
        )
        c_today = (
            db.query(func.count(ConversationSession.id))
            .filter(ConversationSession.user_id == user.id, ConversationSession.started_at >= today_start)
            .scalar() or 0
        )
        w_today = (
            db.query(func.count(Vocabulary.id))
            .filter(Vocabulary.user_id == user.id, Vocabulary.created_at >= today_start)
            .scalar() or 0
        )
        daily_progress = p_today + r_today + c_today + w_today
        daily_target = user.daily_goal or 5

        # Award daily goal bonus when exactly reaching the goal today
        if daily_progress == daily_target:
            user.xp = (user.xp or 0) + 25
            bonuses_awarded["daily_goal_xp"] = 25

        # 3. Level recalculation
        level_info = calculate_level_info(user.xp or 0)
        user.level = level_info["level"]

        db.commit()
        db.refresh(user)

        # 4. Check achievements
        GamificationService.evaluate_achievements(db, user)

        return bonuses_awarded

    @staticmethod
    def get_achievements(db: Session, user: User) -> AchievementListResponse:
        """
        Get all catalogue achievements merged with user's unlock status and current progress.
        """
        # Sync achievements first
        GamificationService.evaluate_achievements(db, user)

        # Fetch unlocked
        existing_records = (
            db.query(UserAchievement)
            .filter(UserAchievement.user_id == user.id)
            .all()
        )
        unlocked_map = {ua.achievement_key: ua for ua in existing_records}

        # Fetch metrics for progress
        vocab_count = db.query(Vocabulary).filter(Vocabulary.user_id == user.id).count()
        mastered_count = db.query(Vocabulary).filter(
            Vocabulary.user_id == user.id,
            Vocabulary.status == "mastered"
        ).count()
        practice_count = (
            db.query(PracticeAttempt)
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(PracticeSession.user_id == user.id)
            .count()
        )
        review_count = db.query(ReviewRecord).filter(ReviewRecord.user_id == user.id).count()
        convo_count = (
            db.query(ConversationSession)
            .filter(ConversationSession.user_id == user.id)
            .count()
        )
        current_streak = calculate_user_streak(db=db, user=user)
        streak_count = max(user.current_streak or 0, user.longest_streak or 0, current_streak)

        metrics_map: Dict[str, int] = {
            "vocabulary_count": vocab_count,
            "mastered_count": mastered_count,
            "practice_count": practice_count,
            "review_count": review_count,
            "conversation_count": convo_count,
            "streak_count": streak_count,
        }

        items: List[AchievementResponse] = []
        unlocked_count = 0

        for item in ACHIEVEMENT_CATALOGUE:
            key = item["key"]
            target = item["target_threshold"]
            curr_val = metrics_map.get(item["metric_type"], 0)
            is_unlocked = key in unlocked_map
            achieved_at = unlocked_map[key].achieved_at if is_unlocked else None

            if is_unlocked:
                unlocked_count += 1
                curr_progress = target
                progress_pct = 100.0
            else:
                curr_progress = min(curr_val, target)
                progress_pct = min(100.0, round((curr_val / target) * 100, 1)) if target > 0 else 0.0

            items.append(
                AchievementResponse(
                    key=key,
                    title=item["title"],
                    description=item["description"],
                    category=item["category"],
                    icon=item["icon"],
                    target_threshold=target,
                    current_progress=curr_progress,
                    progress_percentage=progress_pct,
                    is_unlocked=is_unlocked,
                    achieved_at=achieved_at,
                )
            )

        total = len(ACHIEVEMENT_CATALOGUE)
        completion_percentage = round((unlocked_count / total) * 100, 1) if total > 0 else 0.0

        return AchievementListResponse(
            total=total,
            unlocked_count=unlocked_count,
            completion_percentage=completion_percentage,
            items=items,
        )

    @staticmethod
    def get_level_roadmap(user: User, max_level: int = 15) -> LevelRoadmapResponse:
        """
        Get level roadmap progression and milestones.
        """
        info = calculate_level_info(user.xp or 0)
        curr_lvl = info["level"]

        levels: List[LevelRoadmapItem] = []
        for lvl in range(1, max_level + 1):
            levels.append(
                LevelRoadmapItem(
                    level=lvl,
                    title=get_level_title(lvl),
                    xp_required=(lvl - 1) * 100,
                    is_unlocked=curr_lvl >= lvl,
                    is_current=curr_lvl == lvl,
                )
            )

        return LevelRoadmapResponse(
            current_level=curr_lvl,
            current_xp=user.xp or 0,
            level_title=info["title"],
            current_level_xp=info["current_level_xp"],
            next_level_xp=info["next_level_xp"],
            xp_within_level=info["xp_within_level"],
            progress_percentage=info["progress_percentage"],
            levels=levels,
        )

    @staticmethod
    def get_overview(db: Session, user: User) -> GamificationOverviewResponse:
        """
        Get complete gamification overview for the authenticated user.
        """
        achievements_res = GamificationService.get_achievements(db, user)
        level_info = calculate_level_info(user.xp or 0)

        # Streak info
        current_streak = calculate_user_streak(db=db, user=user)
        longest_streak = max(user.longest_streak or 0, current_streak)

        # Daily goal progress
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        p_today = (
            db.query(func.count(PracticeAttempt.id))
            .join(PracticeSession, PracticeAttempt.session_id == PracticeSession.id)
            .filter(PracticeSession.user_id == user.id, PracticeAttempt.created_at >= today_start)
            .scalar() or 0
        )
        r_today = (
            db.query(func.count(ReviewRecord.id))
            .filter(ReviewRecord.user_id == user.id, ReviewRecord.reviewed_at >= today_start)
            .scalar() or 0
        )
        c_today = (
            db.query(func.count(ConversationSession.id))
            .filter(ConversationSession.user_id == user.id, ConversationSession.started_at >= today_start)
            .scalar() or 0
        )
        w_today = (
            db.query(func.count(Vocabulary.id))
            .filter(Vocabulary.user_id == user.id, Vocabulary.created_at >= today_start)
            .scalar() or 0
        )
        daily_goal_progress = p_today + r_today + c_today + w_today
        daily_goal_target = user.daily_goal or 5
        is_goal_done = daily_goal_progress >= daily_goal_target

        # Recent unlocked achievements
        unlocked_items = [item for item in achievements_res.items if item.is_unlocked and item.achieved_at]
        unlocked_items.sort(key=lambda x: x.achieved_at or now, reverse=True)
        recent_achievements = unlocked_items[:4]

        # Next achievements (closest to unlocking)
        locked_items = [item for item in achievements_res.items if not item.is_unlocked]
        locked_items.sort(key=lambda x: x.progress_percentage, reverse=True)
        next_achievements = locked_items[:4]

        return GamificationOverviewResponse(
            level=level_info["level"],
            level_title=level_info["title"],
            total_xp=user.xp or 0,
            current_level_xp=level_info["current_level_xp"],
            next_level_xp=level_info["next_level_xp"],
            xp_within_level=level_info["xp_within_level"],
            xp_required_for_next_level=level_info["xp_required_for_next_level"],
            level_progress_percentage=level_info["progress_percentage"],
            current_streak=current_streak,
            longest_streak=longest_streak,
            daily_goal=daily_goal_target,
            daily_goal_progress=daily_goal_progress,
            is_daily_goal_completed=is_goal_done,
            unlocked_achievements_count=achievements_res.unlocked_count,
            total_achievements_count=achievements_res.total,
            achievement_completion_percentage=achievements_res.completion_percentage,
            recent_achievements=recent_achievements,
            next_achievements=next_achievements,
        )
