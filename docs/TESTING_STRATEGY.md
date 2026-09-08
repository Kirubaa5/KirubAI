# Testing Strategy — KirubAI

## 1. Testing Philosophy

- Testing is NOT optional
- Test deterministic logic heavily
- Use mock AI provider for automated tests
- No paid API calls in CI
- Focus on behavior, not implementation

## 2. Backend Testing

### Framework
- **Pytest** with async support (`pytest-asyncio`)
- **httpx** for async API testing
- **Factory Boy** for test data
- SQLite in-memory for test database (or test PostgreSQL)

### Test Categories

#### Unit Tests (Domain Layer)
Pure business logic with no dependencies.

```
tests/
├── domain/
│   ├── test_mastery.py          # Mastery score calculation
│   ├── test_review_scheduler.py # Spaced repetition intervals
│   ├── test_scoring.py          # Practice score calculation
│   ├── test_learning_state.py   # State machine transitions
│   └── test_xp.py               # XP calculations
```

**Coverage target:** 95%+ for domain layer

**Example:**
```python
def test_mastery_score_increases_with_practice():
    ...

def test_review_interval_resets_after_three_failures():
    ...

def test_vocabulary_cannot_skip_to_mastered():
    ...
```

#### Service Tests
Business logic with mocked dependencies.

```
tests/
├── services/
│   ├── test_vocabulary_service.py
│   ├── test_practice_service.py
│   ├── test_review_service.py
│   └── test_conversation_service.py
```

**Coverage target:** 80%+

#### API Tests
Full request/response cycle.

```
tests/
├── api/
│   ├── test_auth_api.py
│   ├── test_vocabulary_api.py
│   ├── test_practice_api.py
│   └── test_review_api.py
```

**What to test:**
- Correct status codes
- Response schema validation
- Authentication enforcement
- Input validation
- Error responses
- Edge cases (empty lists, not found, duplicates)

#### AI Tests
Mock provider behavior validation.

```
tests/
├── ai/
│   ├── test_provider.py
│   ├── test_explanation.py
│   ├── test_evaluation.py
│   └── test_mock_provider.py
```

**What to test:**
- Schema validation of AI responses
- Fallback behavior on invalid responses
- Error handling (timeout, rate limit)
- Mock provider returns expected shapes
- Prompt building functions

### Test Configuration

```python
# conftest.py
@pytest.fixture
def mock_llm():
    return MockLLMProvider()

@pytest.fixture
def db_session():
    # In-memory SQLite or test PostgreSQL
    ...

@pytest.fixture
def client(db_session, mock_llm):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_llm] = lambda: mock_llm
    return TestClient(app)
```

## 3. Frontend Testing

### Framework
- **Vitest** as test runner
- **React Testing Library** for component tests
- **MSW (Mock Service Worker)** for API mocking

### Test Categories

#### Component Tests
```
src/features/vocabulary/__tests__/
├── AddWordForm.test.tsx
├── VocabularyList.test.tsx
└── WordCard.test.tsx
```

**What to test:**
- Renders correctly
- User interactions (click, type, submit)
- Form validation
- Loading states displayed
- Error states displayed
- Empty states displayed

#### Hook Tests
```
src/hooks/__tests__/
├── useAuth.test.ts
└── useVocabulary.test.ts
```

#### Utility Tests
```
src/utils/__tests__/
├── formatters.test.ts
└── validators.test.ts
```

### API Mocking

```typescript
// src/test/handlers.ts (MSW)
export const handlers = [
  rest.get('/api/v1/vocabulary', (req, res, ctx) => {
    return res(ctx.json({ items: [...], total: 10, page: 1, per_page: 20, pages: 1 }))
  }),
  rest.post('/api/v1/vocabulary', (req, res, ctx) => {
    return res(ctx.status(201), ctx.json({ id: 'uuid', word: 'test', status: 'new' }))
  }),
]
```

## 4. What Must Be Tested

### Critical (must have tests)

| Area | Examples |
|------|----------|
| Mastery calculation | Input combinations → expected score |
| Spaced repetition intervals | Success/failure → correct next interval |
| State transitions | Valid/invalid transitions |
| Scoring | Score components → weighted result |
| Authentication | Login, register, token, protected routes |
| Input validation | Edge cases, invalid data |
| API error responses | 400, 401, 404, 409, 429 |

### Important (should have tests)

| Area | Examples |
|------|----------|
| Vocabulary CRUD | Add, list, delete, search |
| Practice flow | Start, submit, evaluate |
| Review flow | Get due, submit recall |
| Dashboard data | Correct aggregations |
| Form validation | Frontend Zod schemas |

### Nice to have

| Area | Examples |
|------|----------|
| UI component rendering | Buttons, cards, modals |
| Layout responsiveness | (manual or visual regression) |
| Accessibility | Axe audits |

## 5. Test Execution

### Local Development
```bash
# Backend
pytest                          # All tests
pytest tests/domain/            # Domain tests only
pytest -x                       # Stop on first failure
pytest --cov                    # With coverage

# Frontend
npm run test                    # All tests
npm run test -- --watch         # Watch mode
npm run test -- --coverage      # With coverage
```

### CI Pipeline
1. Run backend linting (ruff/flake8)
2. Run backend type checking (mypy)
3. Run backend tests with coverage
4. Run frontend linting (eslint)
5. Run frontend type checking (tsc)
6. Run frontend tests with coverage
7. Run build verification

## 6. Test Data

### Factory Patterns (Backend)
```python
class UserFactory:
    @staticmethod
    def create(**overrides):
        defaults = {
            "email": f"test-{uuid4().hex[:8]}@example.com",
            "full_name": "Test User",
            "hashed_password": hash_password("testpassword"),
        }
        defaults.update(overrides)
        return User(**defaults)
```

### Fixtures (Frontend)
```typescript
export const mockVocabulary = {
  id: 'test-uuid',
  word: 'hesitate',
  status: 'practiced',
  mastery_score: 0.45,
  practice_count: 3,
  // ...
}
```

## 7. Rules

1. Tests must pass before pushing
2. Tests must not depend on paid AI APIs
3. Tests must not depend on external services
4. Tests must be deterministic (no random failures)
5. Domain logic tests must cover edge cases
6. New features must include tests
7. Bug fixes must include regression tests
