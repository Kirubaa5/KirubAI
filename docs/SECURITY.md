# Security — KirubAI

## 1. Authentication

### JWT-Based Auth
- Access token: short-lived (30 minutes)
- Refresh token: long-lived (7 days)
- Tokens contain: user_id, email, exp, iat
- Signed with HS256 using a strong secret key

### Password Security
- Hashed with **bcrypt** (cost factor 12)
- Minimum 8 characters
- No plaintext storage ever
- No password in logs

### Session Management
- Stateless JWT (no server-side session store)
- Token rotation on refresh
- Revocation via short expiry + refresh blacklist (optional for MVP)

## 2. Authorization

### User Isolation
- Every database query filters by `user_id`
- Users cannot access other users' vocabulary, practice, or conversation data
- API endpoints extract user from JWT, never from request body

### Route Protection
- Public routes: `/auth/register`, `/auth/login`, `/health`
- All other routes require valid JWT
- FastAPI dependency: `get_current_user` injected into protected routes

## 3. Input Validation

### Backend
- All request bodies validated with **Pydantic** schemas
- String length limits on all text fields
- Email format validation
- Word validation (alphabetic, reasonable length)
- User response length limits (prevent abuse)
- No raw SQL injection possible (SQLAlchemy ORM)

### Frontend
- All forms validated with **Zod** schemas
- Client-side validation mirrors server-side rules
- Server-side validation is the source of truth

## 4. API Security

### CORS
```python
origins = [
    "http://localhost:5173",     # Local dev
    "https://kirubai.vercel.app",  # Production
]
```
- Strict origin list
- No `*` in production
- Credentials allowed

### Rate Limiting
| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 10/min |
| `/auth/register` | 5/min |
| AI endpoints | 20/min per user |
| General API | 60/min per user |

### Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security` (production)
- `Content-Security-Policy` (production)

## 5. Data Protection

### Environment Variables
Required secrets:
```
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=<strong-random-secret>
LLM_API_KEY=<provider-key>
```

All secrets via environment variables only:
- `.env` for local development (gitignored)
- `.env.example` committed (no real values)
- Render/Vercel environment config for production

### What Never Gets Committed
- `.env`
- API keys
- Database credentials
- JWT secrets
- User data
- Backups

### Database
- Connection via SSL in production
- Connection pooling via SQLAlchemy
- No raw SQL queries
- Parameterized queries only (via ORM)
- UUID primary keys (no sequential exposure)

## 6. AI Input Safety

### Prompt Injection Prevention
- User inputs are always placed in clearly delimited sections of prompts
- System prompts are not user-modifiable
- AI-generated content is treated as data, not code
- AI responses pass through application logic before affecting state

### AI Output Handling
- All AI responses validated against Pydantic schemas
- Invalid responses rejected, not blindly stored
- AI never directly modifies database
- Scores from AI are bounded (0-10) and validated

## 7. Frontend Security

- No API keys in frontend code
- No secrets in environment variables prefixed with `VITE_` (except public config)
- Auth tokens stored in memory (Zustand) or httpOnly cookies
- XSS prevention via React's default escaping
- No `dangerouslySetInnerHTML` without sanitization
- Dependency auditing (`npm audit`)

## 8. Error Handling Security

- No stack traces exposed to users in production
- Generic error messages for unexpected errors
- Detailed logging on server side only
- Validation errors return field-level details (safe)
- Auth errors return generic "invalid credentials" (no user enumeration)

## 9. Production Checklist

- [ ] DEBUG=false
- [ ] Strong JWT secret (32+ chars)
- [ ] CORS restricted to production domain
- [ ] HTTPS enforced
- [ ] Rate limiting enabled
- [ ] Database SSL enabled
- [ ] Environment variables set (not hardcoded)
- [ ] .env not committed
- [ ] npm audit clean
- [ ] No unused dependencies
- [ ] Error pages don't leak info
- [ ] Logging configured (no sensitive data)
