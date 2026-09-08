from sqlalchemy.orm import Session
from models.user import User
from models.vocabulary import Vocabulary
from schemas.user import UserUpdate, UserProfile


class UserService:
    @staticmethod
    def get_profile(db: Session, user: User) -> UserProfile:
        """Get user profile with vocabulary summary stats."""
        total_words = db.query(Vocabulary).filter(Vocabulary.user_id == user.id).count()
        mastered_words = db.query(Vocabulary).filter(
            Vocabulary.user_id == user.id,
            Vocabulary.status == "mastered"
        ).count()
        active_words = db.query(Vocabulary).filter(
            Vocabulary.user_id == user.id,
            Vocabulary.status.in_(["practiced", "recalled", "reinforced"])
        ).count()

        profile_data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "english_level": user.english_level,
            "daily_goal": user.daily_goal,
            "timezone": user.timezone,
            "xp": user.xp,
            "level": user.level,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "last_active_date": user.last_active_date,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "total_words": total_words,
            "mastered_words": mastered_words,
            "active_words": active_words,
        }
        return UserProfile(**profile_data)

    @staticmethod
    def update_profile(db: Session, user: User, data: UserUpdate) -> User:
        """Update user profile settings."""
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.english_level is not None:
            user.english_level = data.english_level
        if data.daily_goal is not None:
            user.daily_goal = data.daily_goal
        if data.timezone is not None:
            user.timezone = data.timezone

        db.commit()
        db.refresh(user)
        return user
