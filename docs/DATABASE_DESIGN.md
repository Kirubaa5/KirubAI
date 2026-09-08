# Database Design — KirubAI

## 1. Overview

PostgreSQL database hosted on Supabase. Managed via SQLAlchemy ORM with Alembic migrations.

## 2. Entity Relationship Diagram

```
┌──────────┐     ┌──────────────┐     ┌──────────────────┐
│  users   │────<│  vocabulary  │────<│  word_details    │
└──────────┘     └──────┬───────┘     └──────────────────┘
                        │
            ┌───────────┼───────────────┐
            ▼           ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  practice_   │ │  review_     │ │  vocabulary_     │
│  sessions    │ │  records     │ │  examples        │
└──────┬───────┘ └──────────────┘ └──────────────────┘
       │
       ▼
┌──────────────┐
│  practice_   │
│  attempts    │
└──────────────┘

┌──────────┐     ┌────────────────────┐
│  users   │────<│ conversation_      │
└──────────┘     │ sessions           │
                 └──────┬─────────────┘
                        │
                        ▼
                 ┌────────────────────┐
                 │ conversation_      │
                 │ messages           │
                 └────────────────────┘

┌──────────┐     ┌────────────────────┐
│  users   │────<│ learning_progress  │
└──────────┘     └────────────────────┘

┌──────────┐     ┌────────────────────┐
│  users   │────<│ daily_activity     │
└──────────┘     └────────────────────┘

┌──────────┐     ┌────────────────────┐
│  users   │────<│ user_achievements  │
└──────────┘     └────────────────────┘
```

## 3. Table Definitions

### 3.1 users

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default gen |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| hashed_password | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(100) | NOT NULL |
| english_level | VARCHAR(20) | DEFAULT 'intermediate' |
| daily_goal | INTEGER | DEFAULT 5 |
| timezone | VARCHAR(50) | DEFAULT 'UTC' |
| xp | INTEGER | DEFAULT 0 |
| level | INTEGER | DEFAULT 1 |
| current_streak | INTEGER | DEFAULT 0 |
| longest_streak | INTEGER | DEFAULT 0 |
| last_active_date | DATE | NULLABLE |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now(), on update |

### 3.2 vocabulary

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| word | VARCHAR(100) | NOT NULL |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'new' |
| mastery_score | FLOAT | DEFAULT 0.0 |
| practice_count | INTEGER | DEFAULT 0 |
| successful_usage_count | INTEGER | DEFAULT 0 |
| failed_recall_count | INTEGER | DEFAULT 0 |
| last_practiced_at | TIMESTAMPTZ | NULLABLE |
| last_reviewed_at | TIMESTAMPTZ | NULLABLE |
| next_review_at | TIMESTAMPTZ | NULLABLE |
| review_interval_days | INTEGER | DEFAULT 1 |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

**Indexes:**
- `(user_id, word)` UNIQUE
- `(user_id, status)`
- `(user_id, next_review_at)`

**Status enum:** `new`, `learned`, `practiced`, `recalled`, `reinforced`, `mastered`, `struggling`

### 3.3 word_details

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| vocabulary_id | UUID | FK → vocabulary.id, UNIQUE |
| simple_meaning | TEXT | NOT NULL |
| contextual_meaning | TEXT | NULLABLE |
| part_of_speech | VARCHAR(30) | NULLABLE |
| pronunciation_text | VARCHAR(100) | NULLABLE |
| synonyms | JSONB | DEFAULT '[]' |
| antonyms | JSONB | DEFAULT '[]' |
| word_forms | JSONB | DEFAULT '{}' |
| collocations | JSONB | DEFAULT '[]' |
| cefr_level | VARCHAR(5) | NULLABLE |
| difficulty_score | FLOAT | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### 3.4 vocabulary_examples

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| vocabulary_id | UUID | FK → vocabulary.id |
| example_text | TEXT | NOT NULL |
| context_label | VARCHAR(50) | NOT NULL |
| order_index | INTEGER | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Index:** `(vocabulary_id, order_index)`

### 3.5 practice_sessions

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| vocabulary_id | UUID | FK → vocabulary.id |
| session_type | VARCHAR(30) | NOT NULL |
| status | VARCHAR(20) | DEFAULT 'active' |
| total_attempts | INTEGER | DEFAULT 0 |
| successful_attempts | INTEGER | DEFAULT 0 |
| average_score | FLOAT | NULLABLE |
| started_at | TIMESTAMPTZ | DEFAULT now() |
| completed_at | TIMESTAMPTZ | NULLABLE |

**Session types:** `scenario`, `recall`, `multi_word`, `daily`

### 3.6 practice_attempts

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| session_id | UUID | FK → practice_sessions.id |
| vocabulary_id | UUID | FK → vocabulary.id |
| scenario_text | TEXT | NOT NULL |
| user_response | TEXT | NOT NULL |
| vocabulary_usage_score | FLOAT | NOT NULL |
| grammar_score | FLOAT | NOT NULL |
| context_score | FLOAT | NOT NULL |
| naturalness_score | FLOAT | NOT NULL |
| overall_score | FLOAT | NOT NULL |
| feedback | TEXT | NOT NULL |
| improved_version | TEXT | NULLABLE |
| is_successful | BOOLEAN | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### 3.7 review_records

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| vocabulary_id | UUID | FK → vocabulary.id |
| review_type | VARCHAR(20) | NOT NULL |
| recall_successful | BOOLEAN | NOT NULL |
| response_text | TEXT | NULLABLE |
| score | FLOAT | NULLABLE |
| feedback | TEXT | NULLABLE |
| previous_interval_days | INTEGER | NOT NULL |
| new_interval_days | INTEGER | NOT NULL |
| previous_status | VARCHAR(20) | NOT NULL |
| new_status | VARCHAR(20) | NOT NULL |
| reviewed_at | TIMESTAMPTZ | DEFAULT now() |

**Review types:** `recall`, `usage`, `mixed`

### 3.8 conversation_sessions

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| topic | VARCHAR(200) | NULLABLE |
| target_vocabulary | JSONB | DEFAULT '[]' |
| vocabulary_used | JSONB | DEFAULT '[]' |
| vocabulary_usage_count | INTEGER | DEFAULT 0 |
| status | VARCHAR(20) | DEFAULT 'active' |
| message_count | INTEGER | DEFAULT 0 |
| started_at | TIMESTAMPTZ | DEFAULT now() |
| ended_at | TIMESTAMPTZ | NULLABLE |

### 3.9 conversation_messages

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| session_id | UUID | FK → conversation_sessions.id |
| role | VARCHAR(20) | NOT NULL |
| content | TEXT | NOT NULL |
| vocabulary_detected | JSONB | DEFAULT '[]' |
| order_index | INTEGER | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Roles:** `user`, `assistant`, `system`

### 3.10 learning_progress

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| date | DATE | NOT NULL |
| words_learned | INTEGER | DEFAULT 0 |
| words_practiced | INTEGER | DEFAULT 0 |
| words_reviewed | INTEGER | DEFAULT 0 |
| reviews_successful | INTEGER | DEFAULT 0 |
| reviews_failed | INTEGER | DEFAULT 0 |
| practice_attempts | INTEGER | DEFAULT 0 |
| conversation_messages | INTEGER | DEFAULT 0 |
| xp_earned | INTEGER | DEFAULT 0 |
| time_spent_minutes | INTEGER | DEFAULT 0 |

**Index:** `(user_id, date)` UNIQUE

### 3.11 daily_activity

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| date | DATE | NOT NULL |
| is_active | BOOLEAN | DEFAULT false |
| activity_types | JSONB | DEFAULT '[]' |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Index:** `(user_id, date)` UNIQUE

### 3.12 user_achievements

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| achievement_key | VARCHAR(50) | NOT NULL |
| achieved_at | TIMESTAMPTZ | DEFAULT now() |

**Index:** `(user_id, achievement_key)` UNIQUE

## 4. Key Design Decisions

### 4.1 UUID Primary Keys
All tables use UUID primary keys for:
- Easy distributed generation
- No sequential ID exposure
- Safe for API exposure

### 4.2 Relational over JSON
Most structured data is stored relationally. JSONB is used only for:
- Flexible lists (synonyms, antonyms, collocations, word forms)
- Detected vocabulary arrays
- Activity type lists

### 4.3 Vocabulary Status as Application State
Status transitions are controlled by application domain logic, not by AI or direct DB mutation.

### 4.4 Separate word_details Table
AI-generated word details are stored separately to:
- Keep the vocabulary table lean
- Allow regeneration without affecting core vocabulary state
- Potential sharing across users in the future

### 4.5 Denormalized Counts
`practice_count`, `successful_usage_count`, `failed_recall_count` on vocabulary table are denormalized for query performance. Updated via application logic on each practice/review.

## 5. Migration Strategy

- Alembic for all schema changes
- Each phase creates its own migration
- Never edit production migrations after deployment
- Downgrade support for each migration
