# Product Specification — KirubAI

## 1. Vision

"Turn the words you know into words you use."

KirubAI is an AI-powered English vocabulary activation and conversation learning platform. It converts passive vocabulary into active, usable language skills through contextual learning, scenario-based practice, active recall, spaced repetition, and AI-driven conversation.

## 2. Target User

**Primary:**
- Non-native English speakers at Intermediate (B1) to Upper-Intermediate (B2) level
- Users who can understand and communicate in basic English
- Users who frequently discover unfamiliar words but cannot retain or use them
- College students, professionals, job seekers, self-learners

**Behavior:**
- Reads English content (articles, books, websites)
- Searches for unfamiliar words
- Understands meanings temporarily
- Forgets words or cannot recall them in conversation
- Continues using simple vocabulary despite knowing complex words

## 3. Core Problem

The problem is NOT "How do we teach English words?"

The problem IS: "How do we convert passive vocabulary into active vocabulary?"

**Passive vocabulary:** Words the user recognizes when seen but cannot recall or use naturally.

**Active vocabulary:** Words the user can recall and use naturally in speech and writing without conscious effort.

## 4. Product Identity

KirubAI IS:
- An AI-powered vocabulary activation system
- A contextual learning platform
- A scenario-based practice engine
- A text-based conversation coach
- A spaced repetition system optimized for usage, not recognition

KirubAI is NOT:
- A dictionary
- A generic chatbot
- A vocabulary list app
- A flashcard-only app
- A ChatGPT wrapper

## 5. Core Learning Loop

```
DISCOVER → UNDERSTAND → SEE IN CONTEXT → PRACTICE → RECALL → USE → RECEIVE FEEDBACK → REVIEW → REUSE → MASTER
```

Every feature must map to one or more stages of this loop.

## 6. Success Metrics

| Metric | Meaning |
|--------|---------|
| Words mastered | Words with repeated successful contextual usage |
| Active recall rate | % of words user can recall in scenarios |
| Practice completion | % of scenarios attempted |
| Review adherence | % of scheduled reviews completed |
| Vocabulary usage in conversation | Words used naturally in AI conversation |
| Daily streak | Consecutive days of learning activity |
| Retention rate (30-day) | % of learned words still recallable after 30 days |

## 7. Core Features

### 7.1 User System
- Registration / login
- Profile
- Learning preferences
- Data isolation per user

### 7.2 Vocabulary Management
- Add words manually
- Browse vocabulary
- Search, filter, sort
- View status and mastery per word
- View learning history

### 7.3 AI Vocabulary Learning
- Simple meaning
- Contextual meaning
- Part of speech
- Text pronunciation guide
- Synonyms, antonyms
- Word forms (verb/noun/adjective/adverb)
- Collocations
- Difficulty / CEFR level
- 10 realistic conversational examples from varied situations

### 7.4 Scenario Practice
- AI generates a realistic situation
- User types a natural response using the target word
- AI evaluates: vocabulary usage, grammar, context, naturalness, structure
- Score and constructive feedback
- Suggestion for a more natural version
- Multiple scenarios per word

### 7.5 Spaced Repetition & Review
- Deterministic scheduling (1, 3, 7, 14, 30 day intervals)
- Adaptive based on performance
- Active recall in review (not passive recognition)
- Review queue management
- Failed recall → shorter interval

### 7.6 AI Text Conversation
- Natural text conversation with AI
- AI aware of user's vocabulary
- Subtle opportunities to use learned words
- Post-conversation vocabulary usage evaluation
- No voice

### 7.7 Personalized Learning
- User learning pattern analysis
- Weak/strong vocabulary detection
- Practice recommendations
- Difficulty adjustment
- Personalized scenarios

### 7.8 RAG Knowledge System
- Grammar knowledge base
- English usage patterns
- Common mistakes
- Learning guidance
- Contextual references

### 7.9 Progress & Analytics
- Dashboard answering "What should I do today?"
- Total/active/mastered/struggling words
- Practice statistics
- Learning streaks
- Progress charts
- Weekly/monthly trends

### 7.10 Gamification
- Daily goals
- XP system
- Levels
- Streaks
- Achievement milestones

### 7.11 Daily Learning
- Daily learning plan
- Word of the day
- Daily review queue
- Mixed vocabulary practice
- "Use My Vocabulary" multi-word scenarios

## 8. Scope Exclusions

- Voice/speech features
- Real-time multiplayer
- Social features
- Paid subscriptions (for now)
- Mobile native apps (web responsive only)
- Content creation tools
- Teacher/admin dashboard

## 9. Platform

- Web application (responsive)
- Desktop, tablet, mobile browsers
- No native mobile app required

## 10. Deployment

- Frontend: Vercel
- Backend: Render
- Database: Supabase PostgreSQL
