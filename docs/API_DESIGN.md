# API Design — KirubAI

## 1. Base Configuration

- **Base URL:** `/api/v1`
- **Format:** JSON
- **Authentication:** JWT Bearer token
- **Error Format:** `{ "detail": "message", "code": "ERROR_CODE", "errors": [...] }`

## 2. Authentication

### POST /api/v1/auth/register
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "user": { "id": "uuid", "email": "...", "full_name": "..." },
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/login
```json
{ "email": "...", "password": "..." }
```

**Response (200):**
```json
{
  "user": { "id": "uuid", "email": "...", "full_name": "..." },
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/refresh
Refresh access token.

### GET /api/v1/auth/me
Get current authenticated user.

## 3. Users

### GET /api/v1/users/profile
Get user profile with learning stats.

### PATCH /api/v1/users/profile
Update profile settings.

```json
{
  "full_name": "...",
  "english_level": "intermediate",
  "daily_goal": 5,
  "timezone": "Asia/Kolkata"
}
```

## 4. Vocabulary

### GET /api/v1/vocabulary
List user's vocabulary with pagination, filtering, sorting.

**Query params:** `page`, `per_page`, `status`, `sort_by`, `search`, `order`

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "word": "hesitate",
      "status": "practiced",
      "mastery_score": 0.45,
      "practice_count": 3,
      "successful_usage_count": 2,
      "next_review_at": "2024-01-15T10:00:00Z",
      "created_at": "2024-01-10T08:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### POST /api/v1/vocabulary
Add a new word.

```json
{ "word": "hesitate" }
```

**Response (201):**
```json
{
  "id": "uuid",
  "word": "hesitate",
  "status": "new",
  "mastery_score": 0.0,
  "created_at": "..."
}
```

### GET /api/v1/vocabulary/{id}
Get vocabulary item with details.

### DELETE /api/v1/vocabulary/{id}
Remove a word.

### GET /api/v1/vocabulary/{id}/learn
Get AI-generated learning content for a word.

**Response (200):**
```json
{
  "word": "hesitate",
  "details": {
    "simple_meaning": "To pause before doing something because you are uncertain.",
    "contextual_meaning": "To show uncertainty or reluctance in making a decision or taking action.",
    "part_of_speech": "verb",
    "pronunciation_text": "HEZ-ih-tayt",
    "synonyms": ["pause", "waver", "falter", "dither"],
    "antonyms": ["decide", "commit", "act"],
    "word_forms": {
      "verb": "hesitate",
      "noun": "hesitation",
      "adjective": "hesitant",
      "adverb": "hesitantly"
    },
    "collocations": ["hesitate to ask", "don't hesitate", "hesitate for a moment"],
    "cefr_level": "B1",
    "difficulty_score": 3.5
  },
  "examples": [
    { "context_label": "Friends", "example_text": "I hesitated before asking her to join us.", "order_index": 0 },
    ...
  ]
}
```

### POST /api/v1/vocabulary/{id}/mark-learned
Mark word as learned (transitions from NEW → LEARNED).

## 5. Practice

### POST /api/v1/practice/start
Start a practice session for a word.

```json
{
  "vocabulary_id": "uuid",
  "session_type": "scenario"
}
```

**Response (201):**
```json
{
  "session_id": "uuid",
  "scenario": "Your friend asks you to join a weekend trip, but you're not completely sure. Respond naturally.",
  "target_word": "hesitate"
}
```

### POST /api/v1/practice/{session_id}/submit
Submit a practice attempt.

```json
{
  "response": "I'm hesitating a bit because I have some work to finish."
}
```

**Response (200):**
```json
{
  "attempt_id": "uuid",
  "scores": {
    "vocabulary_usage": 8.0,
    "grammar": 9.0,
    "context": 9.0,
    "naturalness": 7.0,
    "overall": 8.25
  },
  "feedback": "Good use of 'hesitating'! ...",
  "improved_version": "I'm kind of hesitating because I have work...",
  "is_successful": true,
  "can_continue": true,
  "next_scenario": "Your manager asks if you can take on extra work..."
}
```

### GET /api/v1/practice/sessions
List practice sessions with optional filters.

### GET /api/v1/practice/{session_id}
Get practice session with all attempts.

### POST /api/v1/practice/{session_id}/complete
End a practice session.

### POST /api/v1/practice/multi-word
Start a multi-word practice ("Use My Vocabulary").

```json
{
  "vocabulary_ids": ["uuid1", "uuid2", "uuid3"]
}
```

## 6. Reviews

### GET /api/v1/reviews/due
Get words due for review.

**Response (200):**
```json
{
  "due_count": 5,
  "items": [
    {
      "vocabulary_id": "uuid",
      "word": "hesitate",
      "status": "practiced",
      "last_reviewed_at": "2024-01-12T08:00:00Z",
      "review_interval_days": 3,
      "review_type": "recall"
    }
  ]
}
```

### POST /api/v1/reviews/submit
Submit a review response.

```json
{
  "vocabulary_id": "uuid",
  "review_type": "recall",
  "response_text": "hesitate"
}
```

**Response (200):**
```json
{
  "recall_successful": true,
  "score": 9.0,
  "feedback": "Correct! ...",
  "new_status": "recalled",
  "new_interval_days": 7,
  "next_review_at": "2024-01-22T10:00:00Z"
}
```

### GET /api/v1/reviews/history
Review history with pagination.

## 7. Conversations

### POST /api/v1/conversations/start
Start a conversation session.

```json
{
  "topic": "career planning",
  "use_vocabulary": true
}
```

**Response (201):**
```json
{
  "session_id": "uuid",
  "initial_message": "Hey! I heard you're thinking about...",
  "target_vocabulary": ["hesitate", "confident", "improve"]
}
```

### POST /api/v1/conversations/{session_id}/message
Send a message in conversation.

```json
{ "content": "Yeah, I've been hesitating about it..." }
```

**Response (200):**
```json
{
  "message_id": "uuid",
  "response": "That makes sense. What's making you...",
  "vocabulary_detected": ["hesitate"]
}
```

### POST /api/v1/conversations/{session_id}/end
End conversation and get evaluation.

**Response (200):**
```json
{
  "evaluation": {
    "vocabulary_used": ["hesitate", "confident"],
    "vocabulary_missed": ["improve"],
    "usage_quality": { "hesitate": 8.5, "confident": 7.0 },
    "overall_fluency": 7.5,
    "feedback": "Great conversation! ..."
  }
}
```

### GET /api/v1/conversations
List conversation sessions.

### GET /api/v1/conversations/{session_id}
Get conversation with all messages.

## 8. Dashboard

### GET /api/v1/dashboard
Get dashboard summary.

**Response (200):**
```json
{
  "today": {
    "reviews_due": 5,
    "words_to_practice": 2,
    "daily_goal_progress": 3,
    "daily_goal_target": 5,
    "word_of_the_day": { "word": "resilient", "meaning": "..." }
  },
  "stats": {
    "total_words": 42,
    "mastered_words": 8,
    "active_words": 25,
    "struggling_words": 3,
    "current_streak": 7,
    "total_xp": 1250,
    "level": 5
  },
  "recent_activity": [
    { "type": "practice", "word": "hesitate", "score": 8.5, "at": "..." },
    { "type": "review", "word": "confident", "result": "success", "at": "..." }
  ]
}
```

## 9. Progress

### GET /api/v1/progress/overview
Overall learning progress.

### GET /api/v1/progress/weekly
Weekly learning stats.

### GET /api/v1/progress/monthly
Monthly learning trends.

### GET /api/v1/progress/vocabulary-breakdown
Vocabulary by status breakdown.

## 10. Common Patterns

### Pagination
All list endpoints support:
```
?page=1&per_page=20
```

Response includes: `total`, `page`, `per_page`, `pages`

### Sorting
```
?sort_by=created_at&order=desc
```

### Filtering
Endpoint-specific filters via query params.

### Error Responses

**400 Bad Request:**
```json
{ "detail": "Validation error", "code": "VALIDATION_ERROR", "errors": [...] }
```

**401 Unauthorized:**
```json
{ "detail": "Not authenticated", "code": "NOT_AUTHENTICATED" }
```

**404 Not Found:**
```json
{ "detail": "Word not found", "code": "NOT_FOUND" }
```

**409 Conflict:**
```json
{ "detail": "Word already exists", "code": "DUPLICATE_WORD" }
```

**429 Too Many Requests:**
```json
{ "detail": "Rate limit exceeded", "code": "RATE_LIMITED" }
```

**500 Internal Server Error:**
```json
{ "detail": "Internal server error", "code": "INTERNAL_ERROR" }
```

## 11. Rate Limits

| Endpoint Group | Limit |
|---------------|-------|
| Auth | 10 req/min |
| AI-heavy (learn, practice, conversation) | 20 req/min |
| CRUD (vocabulary, reviews) | 60 req/min |
| Dashboard/progress | 30 req/min |
