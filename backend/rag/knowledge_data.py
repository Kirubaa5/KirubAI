from typing import List
from rag.models import KnowledgeDocument

CURATED_KNOWLEDGE_DOCUMENTS: List[KnowledgeDocument] = [
    KnowledgeDocument(
        id="DOC-GRAM-001",
        title="Gerunds After Prepositional Phrasal Verbs ('Look forward to')",
        category="grammar",
        topic="Verbs with Preposition 'to'",
        summary="In phrasal expressions where 'to' functions as a preposition (such as 'look forward to' and 'object to'), follow with a gerund (-ing) or noun phrase, never a bare infinitive.",
        content="""When 'to' is part of a phrasal verb or fixed expression, it acts as a preposition rather than an infinitive marker.
Prepositions in English must be followed by a noun, pronoun, or gerund (-ing form of a verb).
Common expressions with prepositional 'to':
- look forward to + gerund / noun (e.g. looking forward to seeing you)
- be/get used to + gerund / noun (e.g. used to working late)
- object to + gerund / noun (e.g. object to paying extra fees)
- committed to + gerund / noun (e.g. committed to improving quality)

Test Rule: If you can replace the verb phrase with the noun 'it' or 'something' (e.g. 'I look forward to IT'), the expression requires a gerund ('I look forward to hearing from you').""",
        rules=[
            "Preposition 'to' + Gerund (-ing) or Noun Phrase",
            "Do not use bare infinitives (base verb) after prepositional phrasal verbs",
        ],
        tags=["look forward to", "gerund", "preposition", "verbs", "infinitive", "phrasal verbs", "used to", "object to"],
        correct_examples=[
            "I look forward to meeting you next Tuesday.",
            "Our team is looking forward to collaborating on this initiative.",
            "She is not used to waking up so early in the morning.",
            "We object to changing the project scope at this stage.",
        ],
        common_mistakes=[
            "INCORRECT: 'I look forward to meet you.' -> CORRECT: 'I look forward to meeting you.'",
            "INCORRECT: 'We look forward to hear your response.' -> CORRECT: 'We look forward to hearing your response.'",
            "INCORRECT: 'I am used to work long hours.' -> CORRECT: 'I am used to working long hours.'",
        ],
        source="KirubAI Grammar Guide: Prepositional Complementation",
    ),
    KnowledgeDocument(
        id="DOC-GRAM-002",
        title="Transitive Verbs without Redundant Prepositions ('Discuss', 'Explain', 'Emphasize')",
        category="grammar",
        topic="Direct Transitive Verbs",
        summary="Transitive verbs like 'discuss', 'explain', 'emphasize', 'contact', and 'reach' take direct objects without prepositions like 'about', 'to', or 'with'.",
        content="""Many non-native English speakers erroneously insert prepositions after transitive verbs by translating literally from their native languages or confusing verbs with related nouns.
- 'Discuss' means 'talk about'. Adding 'about' after 'discuss' is redundant. (Use 'discuss something' OR 'talk about something' OR 'have a discussion about something').
- 'Explain' takes a direct object or 'explain something TO someone' (Never 'explain me something').
- 'Emphasize' means 'place emphasis on'. Do not say 'emphasize on'.
- 'Contact' and 'call' take direct objects (e.g. 'contact the support team', not 'contact with the support team').""",
        rules=[
            "Discuss + [Direct Object] (No 'about')",
            "Explain + [Direct Object] + TO + [Person] (Not 'explain me')",
            "Emphasize + [Direct Object] (No 'on')",
            "Contact / Call + [Direct Object] (No 'with')",
        ],
        tags=["discuss", "explain", "emphasize", "contact", "transitive verbs", "prepositions", "redundancy", "common mistakes"],
        correct_examples=[
            "We will discuss the quarterly roadmap during Monday's standup.",
            "Could you please explain this concept to me?",
            "The keynote speaker emphasized the importance of continuous learning.",
            "Please contact our operations manager if you encounter any blockers.",
        ],
        common_mistakes=[
            "INCORRECT: 'Let's discuss about the proposal.' -> CORRECT: 'Let's discuss the proposal.'",
            "INCORRECT: 'Can you explain me this problem?' -> CORRECT: 'Can you explain this problem to me?'",
            "INCORRECT: 'The article emphasizes on cybersecurity.' -> CORRECT: 'The article emphasizes cybersecurity.'",
            "INCORRECT: 'I will contact with you soon.' -> CORRECT: 'I will contact you soon.'",
        ],
        source="KirubAI Usage Reference: Transitive Verbs & Redundant Prepositions",
    ),
    KnowledgeDocument(
        id="DOC-GRAM-003",
        title="Temporal Prepositions: 'Since' vs. 'For' in Perfect Tenses",
        category="grammar",
        topic="Perfect Tense Time Markers",
        summary="'Since' indicates a specific starting point in time, while 'for' measures the total elapsed duration of a time period.",
        content="""Both 'since' and 'for' are frequently used with the Present Perfect and Present Perfect Continuous tenses to express actions that started in the past and continue into the present.
- 'Since' + Starting Point: Used with dates, specific times, events, or clock hours (e.g. since 2019, since Monday, since 8:00 AM, since graduated).
- 'For' + Duration: Used with a quantity or span of time (e.g. for 5 years, for two months, for three hours, for a long time).

Mental Model:
- 'Since' is a single pin on a timeline marking where the action started.
- 'For' is a ruler measuring the length of the time segment.""",
        rules=[
            "Since + Specific Time Point / Date / Event",
            "For + Time Duration / Span / Number of units",
            "Use with Present Perfect (have + past participle) when action continues to present",
        ],
        tags=["since", "for", "present perfect", "time prepositions", "duration", "tenses", "grammar rules"],
        correct_examples=[
            "I have worked at this software company since October 2021.",
            "She has lived in Berlin for nearly seven years.",
            "We have been debugging this issue since 9 AM.",
            "The team has been testing the release for three consecutive days.",
        ],
        common_mistakes=[
            "INCORRECT: 'I have been living here since 3 years.' -> CORRECT: 'I have been living here for 3 years.'",
            "INCORRECT: 'They have known each other for last summer.' -> CORRECT: 'They have known each other since last summer.'",
            "INCORRECT: 'I am working here since 2 years.' -> CORRECT: 'I have been working here for 2 years.'",
        ],
        source="KirubAI Tenses & Time Prepositions Manual",
    ),
    KnowledgeDocument(
        id="DOC-COLL-001",
        title="Collocations: 'Make' vs. 'Do' Core Distinctions",
        category="collocations",
        topic="Verb Collocations: Make vs Do",
        summary="'Make' is primarily used for producing, creating, deciding, and originating results, whereas 'do' applies to performing tasks, duties, repetitive actions, and general activities.",
        content="""The choice between 'make' and 'do' is governed by established English collocations rather than random preference.
- USE 'MAKE' for:
  * Creating tangible/intangible results: make coffee, make a cake, make a plan, make a list
  * Decisions & choices: make a decision, make a choice, make a commitment
  * Communication & sound: make a speech, make a suggestion, make a complaint, make noise
  * Relationships & reactions: make friends, make an impression, make someone smile
  * Money & business outcome: make money, make a profit, make an investment

- USE 'DO' for:
  * Work, jobs & obligations: do homework, do chores, do research, do business, do taxes
  * Repetitive non-creative actions: do exercise, do the dishes, do laundry
  * Vague/general actions with pronouns: do something, do nothing, do anything, do everything
  * Personal care: do your hair, do your nails""",
        rules=[
            "Make = Creation, Decision, Outcome, Communication",
            "Do = Tasks, Chores, Work, General Action",
        ],
        tags=["make", "do", "collocations", "word choice", "business english", "vocabulary patterns"],
        correct_examples=[
            "We must make a firm decision before the deadline.",
            "Our researchers are doing groundbreaking work in natural language processing.",
            "She made an outstanding suggestion during today's retrospective.",
            "Can you do me a quick favor and review this draft?",
        ],
        common_mistakes=[
            "INCORRECT: 'Do a decision' -> CORRECT: 'Make a decision'",
            "INCORRECT: 'Make research' -> CORRECT: 'Do research' or 'Conduct research'",
            "INCORRECT: 'Make homework' -> CORRECT: 'Do homework'",
            "INCORRECT: 'Do a mistake' -> CORRECT: 'Make a mistake'",
        ],
        source="KirubAI Collocations Dictionary & Usage Corpus",
    ),
    KnowledgeDocument(
        id="DOC-COLL-002",
        title="High-Impact Professional & Workplace Collocations",
        category="collocations",
        topic="Professional Workplace Collocations",
        summary="Fixed multi-word combinations common in professional, engineering, and business communications that enhance clarity and executive presence.",
        content="""Using natural collocations makes your English sound fluent, authoritative, and native-like in professional environments.
Key categories of professional collocations:
- Decision Making: 'reach a consensus', 'weigh the options', 'make an informed decision', 'defer judgment'
- Project Management: 'meet a deadline', 'fall behind schedule', 'allocate resources', 'mitigate risks'
- Problem Solving: 'address a concern', 'troubleshoot an issue', 'bridge the gap', 'streamline operations'
- Team & Alignment: 'align on objectives', 'touch base with', 'foster collaboration', 'solicit feedback'""",
        rules=[
            "Use established verb-noun pairings rather than literal translations",
            "Pair formal adjectives with nouns: 'pivotal moment', 'stringent requirements', 'viable alternative'",
        ],
        tags=["workplace", "business english", "collocations", "professional", "meetings", "project management"],
        correct_examples=[
            "After extensive debate, the engineering leadership reached a consensus.",
            "We have implemented automated checks to mitigate risks ahead of deployment.",
            "Let's touch base tomorrow morning to ensure everyone is aligned on priorities.",
            "The updated pipeline streamlined our deployment operations substantially.",
        ],
        common_mistakes=[
            "INCORRECT: 'Get a consensus' -> CORRECT: 'Reach a consensus'",
            "INCORRECT: 'Solve the deadline' -> CORRECT: 'Meet the deadline'",
            "INCORRECT: 'Decrease the risks' -> PREFERRED: 'Mitigate the risks' or 'Reduce risks'",
        ],
        source="KirubAI Business English & Collocations Guide",
    ),
    KnowledgeDocument(
        id="DOC-MIST-001",
        title="Confusing Word Pairs: 'Affect' vs. 'Effect'",
        category="common_mistakes",
        topic="Word Confusion: Affect vs Effect",
        summary="'Affect' is almost always a verb (to influence), while 'effect' is almost always a noun (the result).",
        content="""The confusion between 'affect' and 'effect' arises because both words are pronounced similarly and relate to change.
- AFFECT (Verb): To influence, act upon, or produce a change in something.
  Example: 'The economic slowdown affected tech hiring.'
- EFFECT (Noun): The result, outcome, or consequence produced by a cause.
  Example: 'The positive effects of regular exercise are well documented.'

Memory Device — The RAVEN Acronym:
- R: Remember
- A: Affect is a
- V: Verb
- E: Effect is a
- N: Noun

Idiomatic Exception: 'In effect' (in operation) and 'take effect' (become valid) use the noun 'effect'.""",
        rules=[
            "Affect = Verb (Action/Influence)",
            "Effect = Noun (End result/Consequence)",
            "Use RAVEN mnemonic: Remember Affect Verb, Effect Noun",
        ],
        tags=["affect", "effect", "confusing words", "common mistakes", "vocabulary", "word pairs", "raven"],
        correct_examples=[
            "How will the new compliance regulation affect our engineering roadmap?",
            "The direct effect of the software optimization was a 40% reduction in latency.",
            "Climate fluctuations adversely affect agricultural productivity.",
            "The new pricing tier takes effect on the first of next month.",
        ],
        common_mistakes=[
            "INCORRECT: 'This change will have a positive affect on morale.' -> CORRECT: 'This change will have a positive effect on morale.'",
            "INCORRECT: 'How did the announcement effect your plans?' -> CORRECT: 'How did the announcement affect your plans?'",
        ],
        source="KirubAI Essential Word Distinctions Reference",
    ),
    KnowledgeDocument(
        id="DOC-MIST-002",
        title="Quantifiers: 'Fewer' vs. 'Less' & 'Many' vs. 'Much'",
        category="common_mistakes",
        topic="Countable vs Uncountable Quantifiers",
        summary="Use 'fewer' and 'many' with countable plural nouns; use 'less' and 'much' with uncountable/mass nouns.",
        content="""Quantifiers must match the grammatical noun type:
- Countable Nouns (things you can count individually: emails, bugs, candidates, days):
  * Use 'FEWER' (fewer bugs, fewer emails, fewer people)
  * Use 'MANY' (many tasks, many questions)
  * Use 'NUMBER OF' (the number of applicants)

- Uncountable Nouns (mass concepts, substances, abstracts: information, time, data, feedback, money, advice):
  * Use 'LESS' (less time, less memory, less information, less friction)
  * Use 'MUCH' (much progress, much experience)
  * Use 'AMOUNT OF' (the amount of feedback)

Rule of Thumb: If the noun can be made plural with an '-s' (e.g. words, errors), use 'fewer' / 'many'.""",
        rules=[
            "Fewer / Many + Countable Plural Nouns (items with distinct counts)",
            "Less / Much + Uncountable Mass Nouns (continuous concepts, time, money, info)",
        ],
        tags=["fewer", "less", "many", "much", "countable", "uncountable", "quantifiers", "grammar"],
        correct_examples=[
            "There were fewer errors in this release than in the previous sprint.",
            "We require less memory bandwidth after optimizing our query structure.",
            "How many test cases have passed so far?",
            "She received much valuable feedback on her presentation draft.",
        ],
        common_mistakes=[
            "INCORRECT: 'There are less people in the meeting today.' -> CORRECT: 'There are fewer people in the meeting today.'",
            "INCORRECT: 'How much bugs are still open?' -> CORRECT: 'How many bugs are still open?'",
            "INCORRECT: 'He gave me many advices.' -> CORRECT: 'He gave me a lot of advice' or 'many pieces of advice'.",
        ],
        source="KirubAI Quantifiers & Noun Types Reference",
    ),
    KnowledgeDocument(
        id="DOC-MIST-003",
        title="Spelling & Grammar: 'Lose' vs. 'Loose'",
        category="common_mistakes",
        topic="Homophones & Spelling Pitfalls: Lose vs Loose",
        summary="'Lose' (one 'o') is a verb meaning to misplace or suffer a defeat; 'loose' (two 'o's) is an adjective meaning not tight.",
        content="""One of the most widespread written errors among both native and non-native English speakers is mixing up 'lose' and 'loose'.
- LOSE (/luːz/ - rhyming with 'choose'): Verb.
  * Meaning: To fail to keep, misplace, or be defeated.
  * Forms: lose, lost, lost, losing.
  * Examples: lose focus, lose money, lose a game, lose track of time.

- LOOSE (/luːs/ - rhyming with 'goose'): Adjective (or occasionally verb).
  * Meaning: Free, unfastened, not firmly fitted or tight.
  * Examples: loose fitting clothes, loose screw, loose connection, turn loose.

Memory Hook: 'Loose' has extra space because it has an extra 'o' (like a loose belt). 'Lose' lost its second 'o'!""",
        rules=[
            "Lose = Verb (Misplace, fail to win, surrender)",
            "Loose = Adjective (Not tight, detached, free)",
        ],
        tags=["lose", "loose", "spelling", "common mistakes", "word confusion", "vocabulary"],
        correct_examples=[
            "Be careful not to lose your passport while traveling.",
            "A loose ethernet cable caused intermittent network drops.",
            "If we don't adapt our strategy, we might lose market share.",
            "Wear loose, comfortable clothing during long flights.",
        ],
        common_mistakes=[
            "INCORRECT: 'I don't want to loose my progress.' -> CORRECT: 'I don't want to lose my progress.'",
            "INCORRECT: 'The nut is to lose on the bolt.' -> CORRECT: 'The nut is too loose on the bolt.'",
        ],
        source="KirubAI Spelling & Precision Guide",
    ),
    KnowledgeDocument(
        id="DOC-TIPS-001",
        title="Active Recall & Spaced Repetition for Accelerated Vocabulary Acquisition",
        category="learning_tips",
        topic="Evidence-Based Learning Strategies",
        summary="Active generation and spaced retrieval intervals produce 3x higher long-term retention than passive re-reading or memorization.",
        content="""Cognitive science demonstrates that the brain builds lasting neural pathways through retrieval effort (the 'Testing Effect').
1. Active Recall vs. Passive Review:
   - Passive (ineffective): Re-reading word definitions or example sentences. Creates the illusion of competence without deep storage.
   - Active (effective): Generating sentences, answering situational prompts, or recalling cloze tests from memory.

2. Spaced Repetition Intervals:
   - Reviewing right before the forgetting threshold (1 day -> 3 days -> 7 days -> 14 days -> 30 days -> 60 days) cements memories into long-term declarative storage.

3. Contextual Dual-Coding:
   - Associate new words with vivid situational contexts (e.g. workplace dilemma, travel negotiation) rather than isolated flashcard translations.""",
        rules=[
            "Always produce output (write or speak) rather than passively reading definitions",
            "Review words across expanding intervals (Leitner/SM-2 spaced repetition)",
            "Embed words into full conversational scenarios immediately after learning",
        ],
        tags=["learning tips", "active recall", "spaced repetition", "retention", "memory", "learning strategy"],
        correct_examples=[
            "Practicing a new word in 3 real-world scenarios immediately after reading its definition.",
            "Testing active recall 24 hours later, then 7 days later, and then 30 days later.",
        ],
        common_mistakes=[
            "PASSIVE HABIT: Highlighting word lists repeatedly without writing original sentences.",
            "CRAMMING: Studying 50 words in one night and never reviewing them in subsequent weeks.",
        ],
        source="KirubAI Cognitive Learning Framework & Retention Methodology",
    ),
    KnowledgeDocument(
        id="DOC-TIPS-002",
        title="Transition Words & Cohesion Markers in Professional Writing",
        category="learning_tips",
        topic="Discourse Markers & Cohesion",
        summary="Use precise transition words (furthermore, conversely, consequently, nevertheless) to logically connect thoughts and elevate executive communication.",
        content="""Cohesive devices guide the reader through your logical reasoning. Using nuanced transitions prevents choppy, disconnected sentences.
Categories of Cohesive Devices:
- Addition & Elaboration: 'Furthermore', 'Moreover', 'In addition to', 'Specifically'
- Contrast & Concession: 'However', 'Conversely', 'Nevertheless', 'On the other hand', 'While it is true that'
- Cause & Consequence: 'Consequently', 'As a result', 'Therefore', 'Thus', 'Owing to'
- Sequencing & Structuring: 'First and foremost', 'Subsequently', 'In conclusion', 'To summarize'

Punctuation Rule: When beginning a sentence with a transition word like 'However', 'Furthermore', or 'Consequently', always follow with a comma.""",
        rules=[
            "Begin transition words at start of sentences with a trailing comma (e.g. 'Consequently, ...')",
            "Match the transition word to the exact logical relationship (do not use 'however' when adding info)",
        ],
        tags=["transition words", "cohesion", "professional writing", "learning tips", "linking words", "discourse"],
        correct_examples=[
            "Furthermore, adopting automated testing will reduce regression defects.",
            "The initial deployment was delayed; nevertheless, user satisfaction remained high.",
            "Consequently, we decided to refactor the core authentication service.",
        ],
        common_mistakes=[
            "INCORRECT PUNCTUATION: 'However we should wait.' -> CORRECT: 'However, we should wait.'",
            "WRONG CONNECTOR: Using 'Moreover' when expressing a contradiction instead of 'However' or 'Conversely'.",
        ],
        source="KirubAI Professional Discourse & Composition Manual",
    ),
]
