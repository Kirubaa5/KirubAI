# System Architecture — KirubAI

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        CLIENT                            │
│  React + TypeScript + Vite + Tailwind CSS                │
│  SPA served from Vercel                                  │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTPS / REST API
                       ▼
┌──────────────────────────────────────────────────────────┐
│                     API GATEWAY                          │
│  FastAPI Application (Render)                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Middleware: Auth, CORS, Rate Limiting, Logging     │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌─────────┬──────────┬──────────┬──────────┬────────┐  │
│  │  Auth   │ Vocab    │ Practice │ Review   │ Conv.  │  │
│  │ Router  │ Router   │ Router   │ Router   │ Router │  │
│  └────┬────┴────┬─────┴────┬─────┴────┬─────┴───┬───┘  │
│       │         │          │          │          │       │
│  ┌────▼─────────▼──────────▼──────────▼──────────▼───┐  │
│  │              SERVICE LAYER                         │  │
│  │  AuthService, VocabService, PracticeService,       │  │
│  │  ReviewService, ConversationService,               │  │
│  │  LearningService, DashboardService,                │  │
│  │  ProgressService, GamificationService              │  │
│  └───────────────────┬───────────────────────────────┘  │
│                      │                                   │
│  ┌───────────────────▼───────────────────────────────┐  │
│  │            DOMAIN / BUSINESS LOGIC                 │  │
│  │  MasteryCalculator, ReviewScheduler,               │  │
│  │  ScoringEngine, LearningStateManager,              │  │
│  │  XPCalculator                                      │  │
│  └───────────────────┬───────────────────────────────┘  │
│                      │                                   │
│  ┌────────────┐  ┌───▼────────────┐  ┌───────────────┐  │
│  │  LLM       │  │  DATA ACCESS   │  │  RAG          │  │
│  │  Provider   │  │  (SQLAlchemy)  │  │  Engine       │  │
│  │  Abstraction│  │                │  │  (FAISS)      │  │
│  └─────┬──────┘  └───────┬────────┘  └───────┬───────┘  │
│        │                 │                    │          │
└────────┼─────────────────┼────────────────────┼──────────┘
         ▼                 ▼                    ▼
   ┌──────────┐    ┌──────────────┐     ┌──────────────┐
   │ LLM APIs │    │ PostgreSQL   │     │ Vector Store │
   │ (OpenAI, │    │ (Supabase)   │     │ (FAISS)      │
   │  Gemini) │    │              │     │              │
   └──────────┘    └──────────────┘     └──────────────┘
```

## 2. Frontend Architecture

```
src/
├── main.tsx                  # App entry point
├── App.tsx                   # Root component, routing
├── index.css                 # Global styles (Tailwind)
│
├── components/               # Shared UI components
│   ├── ui/                   # Button, Input, Modal, Card, Badge, etc.
│   ├── layout/               # AppLayout, Sidebar, Header, Footer
│   └── common/               # ErrorState, EmptyState, LoadingState, Skeleton
│
├── pages/                    # Route-level page components
│   ├── DashboardPage.tsx
│   ├── LearnPage.tsx
│   ├── PracticePage.tsx
│   ├── ReviewPage.tsx
│   ├── ConversationPage.tsx
│   ├── VocabularyPage.tsx
│   ├── ProgressPage.tsx
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   └── NotFoundPage.tsx
│
├── features/                 # Domain-specific modules
│   ├── auth/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/
│   │   ├── schemas/
│   │   └── types/
│   ├── vocabulary/
│   ├── practice/
│   ├── review/
│   ├── conversation/
│   ├── dashboard/
│   ├── progress/
│   └── gamification/
│
├── hooks/                    # Global hooks
├── stores/                   # Zustand stores
├── services/                 # API client, etc.
├── api/                      # API configuration, interceptors
├── types/                    # Shared TypeScript types
├── schemas/                  # Shared Zod schemas
├── utils/                    # Utility functions
└── lib/                      # Third-party wrappers
```

### Key Frontend Patterns

- **State Management:** Zustand for client state, TanStack Query for server state
- **Forms:** React Hook Form + Zod validation
- **Routing:** React Router v6 with protected routes
- **API:** Axios with interceptors for auth tokens, error handling
- **Components:** Headless patterns where needed, Tailwind for styling
- **Error Boundaries:** At page and feature level

## 3. Backend Architecture

```
backend/
├── main.py                   # FastAPI app entry point
├── config.py                 # Environment configuration
├── database.py               # Database connection, session
│
├── routers/                  # API route handlers
│   ├── auth.py
│   ├── users.py
│   ├── vocabulary.py
│   ├── practice.py
│   ├── reviews.py
│   ├── conversations.py
│   ├── dashboard.py
│   └── progress.py
│
├── services/                 # Business logic services
│   ├── auth_service.py
│   ├── vocabulary_service.py
│   ├── practice_service.py
│   ├── review_service.py
│   ├── conversation_service.py
│   ├── learning_service.py
│   ├── dashboard_service.py
│   ├── progress_service.py
│   └── gamification_service.py
│
├── domain/                   # Pure business logic (no I/O)
│   ├── mastery.py            # Mastery state machine, scoring
│   ├── review_scheduler.py   # Spaced repetition logic
│   ├── scoring.py            # Practice scoring
│   ├── learning_state.py     # Vocabulary state transitions
│   └── xp.py                 # XP / gamification calculations
│
├── ai/                       # AI integration
│   ├── provider.py           # LLMProvider abstract base
│   ├── openai_provider.py
│   ├── gemini_provider.py
│   ├── openrouter_provider.py
│   ├── mock_provider.py      # For testing
│   ├── prompts/              # Prompt templates
│   │   ├── explanation.py
│   │   ├── examples.py
│   │   ├── scenario.py
│   │   ├── evaluation.py
│   │   └── conversation.py
│   └── schemas.py            # AI response validation schemas
│
├── rag/                      # RAG system
│   ├── engine.py
│   ├── embeddings.py
│   ├── ingestion.py
│   └── retrieval.py
│
├── models/                   # SQLAlchemy ORM models
│   ├── user.py
│   ├── vocabulary.py
│   ├── practice.py
│   ├── review.py
│   ├── conversation.py
│   ├── progress.py
│   └── gamification.py
│
├── schemas/                  # Pydantic request/response schemas
│   ├── auth.py
│   ├── user.py
│   ├── vocabulary.py
│   ├── practice.py
│   ├── review.py
│   ├── conversation.py
│   └── progress.py
│
├── middleware/                # Custom middleware
│   ├── auth.py
│   └── rate_limit.py
│
├── utils/                    # Utilities
│   ├── security.py
│   └── helpers.py
│
├── migrations/               # Alembic migrations
│   ├── env.py
│   └── versions/
│
└── tests/                    # Test suite
    ├── conftest.py
    ├── test_auth.py
    ├── test_vocabulary.py
    ├── test_practice.py
    ├── test_review.py
    ├── test_mastery.py
    ├── test_scheduling.py
    └── test_scoring.py
```

### Key Backend Patterns

- **Service Layer:** All business logic goes through services, never directly in routers
- **Domain Layer:** Pure functions for deterministic logic (mastery, scheduling, scoring)
- **AI Layer:** Abstracted behind LLMProvider interface; never called from routers directly
- **Repository Pattern (implicit):** SQLAlchemy ORM models + service layer queries
- **Schema Separation:** Pydantic schemas separate from SQLAlchemy models
- **Dependency Injection:** FastAPI's `Depends()` for DB sessions, auth, services

## 4. Data Flow

### Adding a Word
```
Frontend → POST /vocabulary → VocabService.add_word() → DB insert → Response
```

### Learning a Word
```
Frontend → GET /vocabulary/{id}/learn → VocabService → AI Provider (explanation + examples) → Response
```

### Practice Session
```
Frontend → POST /practice/start → PracticeService → AI Provider (scenario) → Response
Frontend → POST /practice/submit → PracticeService → AI Provider (evaluation) → ScoringEngine → DB save → Response
```

### Review
```
Frontend → GET /reviews/due → ReviewService → ReviewScheduler.get_due() → DB query → Response
Frontend → POST /reviews/submit → ReviewService → AI Provider (evaluate) → ReviewScheduler.update() → LearningStateManager → DB save → Response
```

## 5. Cross-Cutting Concerns

### Authentication
- JWT-based authentication
- Access token (short-lived) + Refresh token (long-lived)
- Stored in httpOnly cookies or Authorization header

### Error Handling
- Global exception handler in FastAPI
- Structured error responses: `{ detail, code, errors? }`
- HTTP status codes used correctly
- No raw stack traces in production

### Logging
- Structured logging (JSON format in production)
- Request/response logging
- AI call logging (latency, tokens, errors)
- Error logging with context

### Rate Limiting
- Per-user rate limits on AI-heavy endpoints
- Global rate limits on auth endpoints

## 6. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend framework | React + Vite | Fast dev, large ecosystem |
| CSS | Tailwind | Utility-first, consistent |
| State (client) | Zustand | Lightweight, simple API |
| State (server) | TanStack Query | Caching, refetching, mutations |
| Backend framework | FastAPI | Async, typed, fast |
| ORM | SQLAlchemy 2.0 | Mature, typed, Alembic support |
| Database | PostgreSQL | Relational, robust, Supabase |
| AI Interface | Custom abstraction | Provider independence |
| Vector DB | FAISS | Free, local, sufficient scale |
| Containerization | Docker Compose | Local dev parity |

## 7. Scalability Notes

Current architecture supports:
- Single server deployment (sufficient for MVP and early users)
- Horizontal scaling via Render auto-scaling if needed
- Database connection pooling via SQLAlchemy
- AI call queuing can be added if needed
- Vector store can be upgraded to managed service if needed

Architecture does NOT need to support:
- Real-time (WebSocket) for MVP
- Multi-region deployment
- Event sourcing
- Microservices
