# DEVELOPMENT RULES

## Core Principles

### 1. Build First, Explain Later
- Prioritize implementation over documentation
- Test before claiming completion
- Fix failures before moving forward
- Never skip verification

### 2. Strict Phase System
- Only work on the current phase
- Never implement future phases early
- After completing a phase: STOP
- Wait for explicit approval: "PHASE X VERIFIED. MOVE TO PHASE X+1"

### 3. Token Efficiency
- Minimize narration
- Focus tokens on: code, testing, debugging, verification
- No long explanations before coding
- No repetition of requirements
- Concise phase reports

### 4. Quality Standards
- Every feature must have tests
- Run build/typecheck/lint before completion
- Handle errors, loading states, empty states
- Mobile responsive required
- Accessibility required

## Text-Only Scope

**DO NOT IMPLEMENT:**
- Voice features
- Speech recognition
- Text-to-speech
- Audio processing
- Microphone input
- Pronunciation audio

**ENTIRE PRODUCT IS TEXT-BASED**

Architecture must allow future voice integration without rewriting core systems.

## AI vs Application Responsibility

**AI Handles:**
- Explanations
- Examples
- Scenarios
- Conversation
- Evaluation
- Feedback

**Application Handles:**
- Users
- Authentication
- Database state
- Review scheduling
- Mastery calculation
- Business logic
- Validation

**CRITICAL:** LLM never directly controls database state.

## Technology Constraints

- Use LLM provider abstraction (never couple to one provider)
- Use structured outputs with validation
- PostgreSQL only
- No unnecessary dependencies
- No unnecessary abstractions
- Free/open-source tools preferred

## Frontend Quality

**Avoid:**
- Generic centered cards
- Excessive rounded corners
- Random gradients
- Glassmorphism
- AI-demo aesthetics
- Template layouts
- Fake statistics

**Build:**
- Production-quality SaaS UI
- Strong visual hierarchy
- Consistent spacing
- Clean typography
- Restrained colors
- Meaningful states
- Realistic content

## Learning Philosophy

- Prioritize active recall over passive recognition
- Mastery requires repeated successful contextual usage
- One correct answer ≠ mastered
- Create opportunities for natural vocabulary use
- Evaluate usage in realistic scenarios

## Security

- No secrets in code
- No API keys in Git
- Environment variables for configuration
- Input validation
- Authentication/authorization
- User data isolation
- No raw stack traces to users

## Testing

- Unit tests for business logic
- Integration tests for APIs
- Component tests for UI
- Mock AI provider for tests
- No paid AI calls in automated tests
- Test deterministic logic heavily (mastery, scheduling, scoring)

## Git

- Small logical commits
- Professional commit messages
- Never commit secrets
- Never commit .env files
- Push after verification passes
- Do not push broken code

## Performance & Cost

- Minimize unnecessary AI calls
- Use deterministic logic where possible
- Cache appropriately
- Use cheaper models for simple tasks
- Structured prompts
- Avoid huge context unnecessarily

## Code Quality

- Clear naming
- Small functions
- Single responsibility
- Type safety
- Schema validation
- Error handling
- Testable logic

## Absolute Rules

1. Build before explaining
2. Test before claiming completion
3. Never skip verification
4. Never implement future phases
5. Keep product text-based
6. Keep architecture extensible
7. LLM never directly mutates database
8. Frontend must look production-ready
9. Mobile responsiveness required
10. Accessibility required
11. Error/loading/empty states required
12. Use mocked AI for tests
13. STOP after every phase
