from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class LevelInfoResponse(BaseModel):
    level: int
    title: str
    total_xp: int
    current_level_xp: int
    next_level_xp: int
    xp_within_level: int
    xp_required_for_next_level: int
    progress_percentage: float

    model_config = ConfigDict(from_attributes=True)


class LevelRoadmapItem(BaseModel):
    level: int
    title: str
    xp_required: int
    is_unlocked: bool
    is_current: bool

    model_config = ConfigDict(from_attributes=True)


class LevelRoadmapResponse(BaseModel):
    current_level: int
    current_xp: int
    level_title: str
    current_level_xp: int
    next_level_xp: int
    xp_within_level: int
    progress_percentage: float
    levels: List[LevelRoadmapItem]

    model_config = ConfigDict(from_attributes=True)


class AchievementResponse(BaseModel):
    key: str
    title: str
    description: str
    category: str
    icon: str
    target_threshold: int
    current_progress: int
    progress_percentage: float
    is_unlocked: bool
    achieved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AchievementListResponse(BaseModel):
    total: int
    unlocked_count: int
    completion_percentage: float
    items: List[AchievementResponse]

    model_config = ConfigDict(from_attributes=True)


class GamificationOverviewResponse(BaseModel):
    level: int
    level_title: str
    total_xp: int
    current_level_xp: int
    next_level_xp: int
    xp_within_level: int
    xp_required_for_next_level: int
    level_progress_percentage: float
    current_streak: int
    longest_streak: int
    daily_goal: int
    daily_goal_progress: int
    is_daily_goal_completed: bool
    unlocked_achievements_count: int
    total_achievements_count: int
    achievement_completion_percentage: float
    recent_achievements: List[AchievementResponse]
    next_achievements: List[AchievementResponse]

    model_config = ConfigDict(from_attributes=True)
