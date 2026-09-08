# User Journey — KirubAI

## 1. First-Time User

```
Visit → Register → Onboarding → Add First Word → Learn → Practice → Dashboard
```

### 1.1 Registration
- Email/password registration
- Minimal fields: name, email, password
- Redirect to onboarding

### 1.2 Onboarding
- Brief explanation of how KirubAI works
- Ask about English level (self-assessment)
- Ask about learning goals (optional)
- Redirect to add first word

## 2. Core Learning Journey

### 2.1 Discover & Add Word

User encounters "hesitate" while reading an article.

1. User navigates to "Learn" or "Vocabulary"
2. Types "hesitate" in the add-word input
3. System validates word
4. Word is added with status: NEW

### 2.2 Learn

System shows the word learning page:

**Step 1 — Meaning**
- Simple definition
- Contextual meaning
- Part of speech
- Text pronunciation guide

**Step 2 — Word Details**
- Synonyms: pause, waver, falter
- Antonyms: decide, commit
- Word forms: hesitate (v), hesitation (n), hesitant (adj), hesitantly (adv)
- Collocations: hesitate to ask, don't hesitate, hesitate for a moment
- CEFR Level: B1

**Step 3 — Examples**
10 realistic conversational examples from varied situations:

| # | Context | Example |
|---|---------|---------|
| 1 | Friends | "I hesitated before asking her to join us." |
| 2 | Workplace | "Don't hesitate to reach out if you need help." |
| 3 | Interview | "I hesitated for a moment before answering the question." |
| 4 | Family | "She hesitated to tell her parents about the plan." |
| 5 | College | "He hesitated before raising his hand in class." |
| 6 | Shopping | "I hesitated between the two options." |
| 7 | Meeting | "The manager hesitated before approving the budget." |
| 8 | Travel | "We hesitated at the crossroad, unsure of the direction." |
| 9 | Phone call | "He hesitated on the phone, searching for the right words." |
| 10 | Daily life | "Don't hesitate — just go for it." |

**Step 4 — Interactive**
- User marks word as "understood"
- Status changes: NEW → LEARNED
- System prompts: "Ready to practice?"

### 2.3 Practice

**Scenario 1:**
> Your friend asks you to join a weekend trip, but you're not completely sure. Respond naturally.

User types: "I'm hesitating a bit because I have some work to finish, but I'll let you know by tonight."

**AI Evaluation:**
| Category | Score | Notes |
|----------|-------|-------|
| Vocabulary Usage | 8/10 | Used "hesitating" correctly |
| Grammar | 9/10 | Correct structure |
| Context | 9/10 | Appropriate for the scenario |
| Naturalness | 7/10 | Good but slightly formal for friends |

**Feedback:**
"Good use of 'hesitating'! For a casual friend conversation, you might say: 'I'm kind of hesitating because I've got work, but I'll let you know tonight.' Dropping 'a bit' and using 'kind of' make it sound more natural with friends."

**Scenario 2:**
> Your manager asks if you can lead a presentation next week. You're unsure about your schedule.

User types: "I'd like to, but I hesitate to commit right now because I need to check my schedule first."

**AI Evaluation → Feedback → Score**

After completing practice:
- Status changes: LEARNED → PRACTICED
- Practice results saved
- Review scheduled for next day

### 2.4 Review (Next Day)

**Active Recall Format:**
> Complete this sentence naturally: "Before making a big decision, she always _____ for a moment to think it through."

User types: "hesitates"

**Evaluation:** Correct recall ✓

**Usage Test:**
> Your colleague is overthinking a simple decision. Encourage them using the word you reviewed.

User types: "Don't hesitate too much — it's a simple choice, just go with your gut."

**Evaluation → Score → Feedback**

Status: PRACTICED → RECALLED
Next review: 3 days

### 2.5 Reinforcement Loop

Review intervals increase:
- Day 1 → Day 3 → Day 7 → Day 14 → Day 30

Each review uses:
- Active recall (not "here's the meaning")
- Contextual usage scenarios
- Natural conversation prompts

After consistent successful reviews:
- Status: RECALLED → REINFORCED → MASTERED

### 2.6 Conversation Practice

User enters Conversation mode.

**AI:** "Hey! How's your week going? I heard you were thinking about changing your schedule next semester."

**User:** "Yeah, I've been hesitating about it. On one hand, morning classes would be better, but I'm not sure I can wake up that early consistently."

**Post-conversation evaluation:**
- "hesitating" — used correctly and naturally ✓
- Context appropriate ✓
- Natural flow ✓

## 3. Daily Session

```
Open app → Dashboard → Today's tasks → [ Review | Practice | Learn new | Conversation ] → Progress update
```

### 3.1 Dashboard View

- 📋 3 words due for review
- 📝 1 word needs practice
- ✨ Word of the day: "persevere"
- 🔥 Streak: 7 days
- 📊 This week: 5 words learned, 12 reviews completed

### 3.2 Daily Flow

1. Complete due reviews (active recall)
2. Practice struggling words
3. Learn new word (if ready)
4. Optional conversation session
5. View updated progress

## 4. "Use My Vocabulary" Journey

User has learned: hesitate, reliable, confident, improve, overwhelmed

**System generates:**
> You're meeting with your project team. The deadline was moved up by a week. Your teammate suggests asking for an extension, but you think the team can handle it. Discuss this with your teammate.

User responds using multiple learned words naturally.

**Evaluation:** Which words were used, how naturally, suggestions for incorporating others.

## 5. Struggling Word Journey

Word "ubiquitous" — user fails recall 3 times.

1. Status: → STRUGGLING
2. Review interval shortened
3. Additional practice scenarios generated
4. Simpler context provided
5. More frequent review until successful

## 6. Edge Cases

- User adds a word they already know well → Practice first, if mastered quickly, fast-track
- User adds a misspelled word → Validation / suggestion
- User submits gibberish practice → AI detects and asks for retry
- User is inactive for weeks → Gentle review of previously learned words
- User adds many words at once → System prioritizes review over new words
