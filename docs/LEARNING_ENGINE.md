# Learning Engine — KirubAI

## 1. Vocabulary State Machine

```
         ┌──────────────────────────────────────────┐
         │                                          │
         ▼                                          │
       ┌─────┐    ┌─────────┐    ┌───────────┐     │
       │ NEW │───>│ LEARNED │───>│ PRACTICED │─────┤
       └─────┘    └─────────┘    └─────┬─────┘     │
                                       │            │
                                       ▼            │
                                ┌──────────┐        │
                                │ RECALLED │        │
                                └─────┬────┘        │
                                      │             │
                                      ▼             │
                               ┌────────────┐       │
                               │ REINFORCED │       │
                               └──────┬─────┘       │
                                      │             │
                                      ▼             │
                               ┌──────────┐         │
                               │ MASTERED │         │
                               └──────────┘         │
                                                    │
     ┌────────────┐                                 │
     │ STRUGGLING │ <───── (failed recall from any) │
     └──────┬─────┘                                 │
            │                                       │
            └───────────────────────────────────────┘
              (successful practice/recall returns
               to appropriate state)
```

### Transition Rules

| From | To | Trigger |
|------|----|---------|
| NEW | LEARNED | User completes learning content and marks understood |
| LEARNED | PRACTICED | User completes at least 1 successful practice attempt |
| PRACTICED | RECALLED | User successfully recalls word in first scheduled review |
| RECALLED | REINFORCED | User successfully recalls in 2 consecutive reviews |
| REINFORCED | MASTERED | User successfully uses word in 3+ reviews AND conversation |
| Any (except NEW) | STRUGGLING | 2+ consecutive failed recalls |
| STRUGGLING | PRACTICED | User completes successful practice session |

### Key Rules
- Status transitions are **one-directional** (except STRUGGLING which can return)
- A single correct answer NEVER triggers MASTERED
- MASTERED requires evidence of repeated successful contextual usage
- All transitions happen in application code, not in AI

## 2. Mastery Score

Mastery score: `0.0` to `1.0`

### Calculation

```python
def calculate_mastery(vocab) -> float:
    """
    Mastery score based on multiple factors.
    All inputs come from application state, not AI.
    """
    weights = {
        "practice_success_rate": 0.25,
        "recall_streak": 0.25,
        "usage_diversity": 0.20,
        "review_consistency": 0.15,
        "time_factor": 0.15,
    }

    practice_score = min(1.0, successful_attempts / max(practice_count, 1))
    recall_score = min(1.0, consecutive_successful_recalls / 5)
    diversity_score = min(1.0, unique_contexts_used / 5)
    consistency_score = min(1.0, reviews_completed_on_time / max(total_reviews_due, 1))
    time_score = min(1.0, days_since_added / 30)  # Words need time

    mastery = sum(
        weights[k] * v for k, v in {
            "practice_success_rate": practice_score,
            "recall_streak": recall_score,
            "usage_diversity": diversity_score,
            "review_consistency": consistency_score,
            "time_factor": time_score,
        }.items()
    )

    return round(mastery, 3)
```

### Score Interpretation

| Range | Meaning |
|-------|---------|
| 0.0 - 0.2 | New / barely started |
| 0.2 - 0.4 | Learning / early practice |
| 0.4 - 0.6 | Practicing / some recall |
| 0.6 - 0.8 | Good recall / approaching mastery |
| 0.8 - 1.0 | Mastered / consistent usage |

## 3. Spaced Repetition

### Base Intervals

```python
REVIEW_INTERVALS = [1, 3, 7, 14, 30]  # days
```

### Algorithm

```python
def calculate_next_review(
    current_interval_days: int,
    recall_successful: bool,
    consecutive_successes: int,
    consecutive_failures: int,
) -> tuple[int, datetime]:
    """
    Returns (new_interval_days, next_review_datetime).
    Pure function — no side effects.
    """
    if recall_successful:
        # Find next interval in the sequence
        try:
            current_index = REVIEW_INTERVALS.index(current_interval_days)
            if current_index < len(REVIEW_INTERVALS) - 1:
                new_interval = REVIEW_INTERVALS[current_index + 1]
            else:
                # Beyond max interval — extend by 1.5x
                new_interval = min(current_interval_days * 1.5, 90)
        except ValueError:
            # Not in standard intervals — find closest next
            new_interval = next(
                (i for i in REVIEW_INTERVALS if i > current_interval_days),
                min(current_interval_days * 1.5, 90)
            )

        # Bonus for streaks
        if consecutive_successes >= 3:
            new_interval = int(new_interval * 1.2)
    else:
        # Failed — reduce interval
        if consecutive_failures >= 3:
            new_interval = 1  # Reset to minimum
        elif consecutive_failures == 2:
            new_interval = max(1, current_interval_days // 3)
        else:
            new_interval = max(1, current_interval_days // 2)

    next_review = datetime.utcnow() + timedelta(days=int(new_interval))
    return (int(new_interval), next_review)
```

### Properties
- Fully deterministic
- Testable without AI
- Adapts to performance
- Bounds maximum interval at 90 days
- Resets to 1 day after 3 consecutive failures

## 4. Practice Scoring

### Score Components

| Component | Weight | Range |
|-----------|--------|-------|
| Vocabulary Usage | 30% | 0-10 |
| Grammar | 20% | 0-10 |
| Context Appropriateness | 25% | 0-10 |
| Naturalness | 25% | 0-10 |

### Overall Score

```python
def calculate_overall_score(
    vocabulary_usage: float,
    grammar: float,
    context: float,
    naturalness: float,
) -> float:
    weighted = (
        vocabulary_usage * 0.30 +
        grammar * 0.20 +
        context * 0.25 +
        naturalness * 0.25
    )
    return round(weighted, 1)
```

### Success Threshold

A practice attempt is `successful` if:
- `overall_score >= 6.0` AND
- `vocabulary_usage_score >= 5.0`

Rationale: The user must use the target word correctly, not just write a grammatically correct sentence.

## 5. Review Types

### Recall Review
- System presents a context/hint
- User must recall the word
- Binary: success or failure

### Usage Review
- System presents a scenario
- User must use the word naturally
- Evaluated by AI (like practice)
- Score determines success

### Mixed Review
- Combination of recall + usage
- Used for reinforcement and mastery stages

## 6. Daily Learning Plan

### Priority Order
1. **Due reviews** (most important — retention)
2. **Struggling words practice** (targeted improvement)
3. **New word learning** (up to daily goal)
4. **Optional conversation** (reinforcement)

### Daily Goal
Default: 5 activities/day (configurable per user)

Activities that count:
- Completing a review
- Completing a practice attempt
- Learning a new word
- Having a conversation of 5+ messages

## 7. XP System

| Activity | XP |
|----------|-----|
| Learn new word | 10 XP |
| Complete practice (successful) | 15 XP |
| Complete practice (unsuccessful) | 5 XP |
| Complete review (successful) | 10 XP |
| Complete review (unsuccessful) | 3 XP |
| Conversation (per session) | 20 XP |
| Daily goal completed | 25 XP (bonus) |
| Streak maintained | 5 XP per day |

### Level Thresholds

```python
def xp_for_level(level: int) -> int:
    """XP required to reach a given level."""
    return level * 100  # Level 1: 100, Level 2: 200, etc.
```

## 8. Streak Rules

- A day counts as "active" if at least 1 learning activity was completed
- Streaks are calculated based on consecutive active days
- Timezone-aware: uses user's configured timezone
- Missing a day resets the streak to 0
- Longest streak is tracked separately

## 9. "Use My Vocabulary" Feature

### Word Selection
System selects 3-5 words from user's vocabulary that are:
- Status: PRACTICED, RECALLED, or REINFORCED (not NEW, LEARNED, or MASTERED)
- Haven't been used in multi-word practice recently
- Varied difficulty levels

### Scenario Design
AI generates ONE scenario that naturally requires multiple target words.

### Evaluation
Each word is individually evaluated:
- Was it used?
- Was it used correctly?
- Was it used naturally?

Score per word contributes to individual vocabulary mastery.

## 10. Testing Requirements for Learning Logic

All functions in the domain layer MUST be testable without AI:

```python
# Example test
def test_review_interval_increases_on_success():
    new_interval, _ = calculate_next_review(
        current_interval_days=3,
        recall_successful=True,
        consecutive_successes=1,
        consecutive_failures=0,
    )
    assert new_interval == 7

def test_review_interval_decreases_on_failure():
    new_interval, _ = calculate_next_review(
        current_interval_days=7,
        recall_successful=False,
        consecutive_successes=0,
        consecutive_failures=1,
    )
    assert new_interval == 3  # 7 // 2 = 3

def test_mastery_requires_multiple_successes():
    # Cannot reach MASTERED with single success
    ...
```

## 11. Performance Considerations

- Mastery recalculation: only on practice/review events, not on every query
- Review queue: query by `next_review_at <= now()`, indexed
- Daily stats: denormalized in `learning_progress` table, updated incrementally
- Vocabulary counts by status: can be computed from DB, cached at dashboard level
