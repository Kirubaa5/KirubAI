from datetime import datetime, timezone, timedelta
from typing import Tuple

# Standard review interval sequence in days (1d -> 3d -> 7d -> 14d -> 30d)
REVIEW_INTERVALS = [1, 3, 7, 14, 30]


def calculate_next_review(
    current_interval_days: int,
    recall_successful: bool,
    consecutive_successes: int = 0,
    consecutive_failures: int = 0,
) -> Tuple[int, datetime]:
    """
    Pure function to calculate the next review interval and datetime.
    Follows deterministic spaced repetition rules from docs/LEARNING_ENGINE.md.

    - Progression: 1 -> 3 -> 7 -> 14 -> 30 days
    - Success beyond 30 days: 1.5x previous interval (capped at 90 days)
    - Streak bonus: >= 3 consecutive successes multiplies interval by 1.2x
    - Failure reduction:
        - 1 failure: max(1, current // 2)
        - 2 consecutive failures: max(1, current // 3)
        - >= 3 consecutive failures: reset to 1 day
    """
    if recall_successful:
        try:
            current_index = REVIEW_INTERVALS.index(current_interval_days)
            if current_index < len(REVIEW_INTERVALS) - 1:
                new_interval = REVIEW_INTERVALS[current_index + 1]
            else:
                # Beyond max interval — extend by 1.5x capped at 90
                new_interval = min(current_interval_days * 1.5, 90)
        except ValueError:
            # Not in standard intervals — find closest next
            new_interval = next(
                (i for i in REVIEW_INTERVALS if i > current_interval_days),
                min(current_interval_days * 1.5, 90),
            )

        # Bonus for streaks
        if consecutive_successes >= 3:
            new_interval = int(new_interval * 1.2)

        # Cap maximum interval at 90 days
        new_interval = min(new_interval, 90)
    else:
        # Failed — reduce interval
        if consecutive_failures >= 3:
            new_interval = 1  # Reset to minimum
        elif consecutive_failures == 2:
            new_interval = max(1, current_interval_days // 3)
        else:
            new_interval = max(1, current_interval_days // 2)

    new_interval_int = min(90, max(1, int(new_interval)))
    next_review = datetime.now(timezone.utc) + timedelta(days=new_interval_int)
    return new_interval_int, next_review


def calculate_mastery(
    practice_count: int,
    successful_practice_count: int,
    consecutive_successful_recalls: int,
    unique_contexts_used: int = 1,
    reviews_completed_on_time: int = 1,
    total_reviews_due: int = 1,
    days_since_added: int = 1,
) -> float:
    """
    Calculate deterministic vocabulary mastery score (0.0 to 1.0).
    Follows weights specified in docs/LEARNING_ENGINE.md:
      - practice_success_rate: 0.25
      - recall_streak: 0.25
      - usage_diversity: 0.20
      - review_consistency: 0.15
      - time_factor: 0.15
    """
    weights = {
        "practice_success_rate": 0.25,
        "recall_streak": 0.25,
        "usage_diversity": 0.20,
        "review_consistency": 0.15,
        "time_factor": 0.15,
    }

    practice_score = min(1.0, successful_practice_count / max(practice_count, 1))
    recall_score = min(1.0, consecutive_successful_recalls / 5.0)
    diversity_score = min(1.0, unique_contexts_used / 5.0)
    consistency_score = min(1.0, reviews_completed_on_time / max(total_reviews_due, 1))
    time_score = min(1.0, days_since_added / 30.0)

    mastery = (
        weights["practice_success_rate"] * practice_score
        + weights["recall_streak"] * recall_score
        + weights["usage_diversity"] * diversity_score
        + weights["review_consistency"] * consistency_score
        + weights["time_factor"] * time_score
    )

    return min(1.0, max(0.0, round(mastery, 3)))


def determine_status_transition(
    current_status: str,
    recall_successful: bool,
    consecutive_successes: int,
    consecutive_failures: int,
    mastery_score: float = 0.0,
) -> str:
    """
    Determine next status transition based on review result.
    State machine from docs/LEARNING_ENGINE.md:
      - PRACTICED -> RECALLED (on first successful review)
      - RECALLED -> REINFORCED (2 consecutive successful reviews)
      - REINFORCED -> MASTERED (3+ consecutive successful reviews AND mastery >= 0.8)
      - Any (except NEW) -> STRUGGLING (2+ consecutive failed recalls)
      - STRUGGLING -> PRACTICED (on successful recall/practice)
    """
    if recall_successful:
        if current_status == "struggling":
            return "practiced"
        elif current_status in ("new", "learned", "practiced"):
            return "recalled"
        elif current_status == "recalled":
            if consecutive_successes >= 2:
                return "reinforced"
            return "recalled"
        elif current_status == "reinforced":
            if consecutive_successes >= 3 and mastery_score >= 0.8:
                return "mastered"
            return "reinforced"
        elif current_status == "mastered":
            return "mastered"
        return "recalled"
    else:
        if consecutive_failures >= 2 and current_status != "new":
            return "struggling"
        return current_status
