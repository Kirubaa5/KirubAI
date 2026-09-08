# MVP Scope — KirubAI

## 1. MVP Definition

The minimum viable product that delivers the core learning loop:

```
ADD WORD → LEARN → PRACTICE → REVIEW → MASTER
```

## 2. MVP Features

### ✅ Included in MVP

| # | Feature | Phase |
|---|---------|-------|
| 1 | User registration and login | Phase 2 |
| 2 | Add vocabulary words | Phase 2 |
| 3 | AI word explanation (meaning, POS, synonyms, forms, etc.) | Phase 3 |
| 4 | 10 conversational examples per word | Phase 3 |
| 5 | Scenario-based practice | Phase 4 |
| 6 | User types response | Phase 4 |
| 7 | AI evaluation and feedback | Phase 4 |
| 8 | Practice result storage | Phase 4 |
| 9 | Review scheduling (spaced repetition) | Phase 5 |
| 10 | Active recall in reviews | Phase 5 |
| 11 | Vocabulary status tracking | Phase 5 |
| 12 | Basic mastery score | Phase 5 |
| 13 | Basic dashboard (today's tasks, stats) | Phase 9 |

**MVP is complete after Phase 5** (core loop works). Phases 6+ add enrichment.

### ❌ Not in MVP (later phases)

| Feature | Phase |
|---------|-------|
| AI conversation mode | Phase 6 |
| Personalized learning | Phase 7 |
| RAG knowledge system | Phase 8 |
| Analytics / progress charts | Phase 9 |
| Gamification (XP, levels, achievements) | Phase 10 |
| Daily learning system / "Use My Vocabulary" | Phase 11 |
| Advanced AI evaluation | Phase 12 |

## 3. MVP User Journey

1. User registers
2. User adds a word (e.g., "hesitate")
3. System shows AI-generated explanation and examples
4. User starts practice → gets scenario → types response → gets AI feedback
5. System schedules review
6. Next day: user reviews word via active recall
7. System tracks mastery and adjusts schedule

## 4. MVP Quality Bar

Even though it's MVP:
- Frontend must look production-quality
- API must have proper error handling
- Tests must cover core business logic
- Mobile responsive required
- Loading/error/empty states required

## 5. MVP Tech Requirements

- Full auth system (JWT)
- PostgreSQL database
- FastAPI backend
- React frontend
- LLM provider abstraction (with mock for dev/test)
- At least one real LLM provider working
- Docker Compose for local development
- Test suite for core domain logic

## 6. What MVP Proves

1. Core learning loop works end-to-end
2. AI can generate useful explanations and evaluations
3. Practice-based learning is effective
4. Spaced repetition keeps words in memory
5. The product is more than a dictionary or flashcard app
