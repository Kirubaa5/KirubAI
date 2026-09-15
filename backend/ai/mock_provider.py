import re
from typing import TypeVar, Type, List, Dict, Optional
from pydantic import BaseModel
from ai.provider import LLMProvider
from ai.schemas import (
    WordExplanationAI,
    ConversationalExampleAI,
    ExampleSetAI,
    ScenarioAI,
    PersonalizedScenarioAI,
    EvaluationAI,
    ReviewEvaluationAI,
    VocabularyUsageDetailAI,
    ConversationEvaluationAI,
    KnowledgeExplanationAI,
)

T = TypeVar("T", bound=BaseModel)


# Curated vocabulary database for realistic mock responses
MOCK_VOCABULARY_DB: Dict[str, Dict] = {
    "hesitate": {
        "simple_meaning": "To pause before saying or doing something because you are uncertain or nervous.",
        "contextual_meaning": "Used when someone shows reluctance or pauses to make a thoughtful choice in professional, academic, or social situations.",
        "part_of_speech": "verb",
        "pronunciation_text": "HEZ-ih-tayt",
        "synonyms": ["pause", "waver", "falter", "dither", "delay"],
        "antonyms": ["proceed", "decide", "commit", "plunge"],
        "word_forms": {
            "verb": "hesitate",
            "noun": "hesitation",
            "adjective": "hesitant",
            "adverb": "hesitantly",
        },
        "collocations": [
            "hesitate to ask",
            "don't hesitate",
            "hesitate for a moment",
            "without hesitation",
        ],
        "cefr_level": "B1",
        "difficulty_score": 4.0,
        "examples": [
            ("Workplace", "Please don't hesitate to reach out if you have any questions regarding the project."),
            ("Friends", "I hesitated for a second before telling my friend the truth about what happened."),
            ("Meeting", "The team lead hesitated before approving the final budget proposal."),
            ("Interview", "I hesitated briefly to gather my thoughts before answering the technical question."),
            ("College", "She hesitated to raise her hand in class even though she knew the correct answer."),
            ("Family", "My parents didn't hesitate to support my decision to study abroad."),
            ("Shopping", "I hesitated between the two laptops because both had great reviews."),
            ("Travel", "We hesitated at the intersection, unsure of which road would lead to the hotel."),
            ("Phone call", "He hesitated on the phone when I asked if he was free this weekend."),
            ("Daily life", "When an opportunity presents itself, you shouldn't hesitate to seize it."),
        ],
    },
    "vividly": {
        "simple_meaning": "In a way that produces very clear, detailed, and powerful images in the mind.",
        "contextual_meaning": "Used when describing strong memories, dreams, or detailed explanations that make something feel real and present.",
        "part_of_speech": "adverb",
        "pronunciation_text": "VIV-id-lee",
        "synonyms": ["clearly", "distinctly", "graphically", "memorably", "powerfully"],
        "antonyms": ["vaguely", "faintly", "dimly", "hazily"],
        "word_forms": {
            "adverb": "vividly",
            "adjective": "vivid",
            "noun": "vividness",
        },
        "collocations": [
            "remember vividly",
            "describe vividly",
            "recall vividly",
            "vividly illustrate",
        ],
        "cefr_level": "B2",
        "difficulty_score": 5.5,
        "examples": [
            ("Workplace", "She vividly presented the quarterly results, highlighting key metrics with clear charts."),
            ("Friends", "I vividly remember our high school road trip like it was yesterday."),
            ("Meeting", "The director vividly outlined the future vision for the company over the next five years."),
            ("Interview", "During the interview, he vividly recounted a challenging project he had successfully delivered."),
            ("College", "The professor vividly explained the economic theory with real-world analogies."),
            ("Family", "My grandfather vividly described what life was like in the village decades ago."),
            ("Shopping", "I can still vividly recall the vibrant colors in the bustling downtown market."),
            ("Travel", "Looking back, we vividly picture the sunset over the coastline from that cliff."),
            ("Phone call", "He vividly narrated the unexpected incident that happened on his morning commute."),
            ("Daily life", "Dreams from last night are still vividly playing in the back of my mind."),
        ],
    },
    "hassle": {
        "simple_meaning": "A situation that causes minor difficulties, inconvenience, or unnecessary effort.",
        "contextual_meaning": "Commonly used in casual or workplace contexts to express frustration over tedious procedures or irritating tasks.",
        "part_of_speech": "noun",
        "pronunciation_text": "HASS-ul",
        "synonyms": ["nuisance", "inconvenience", "bother", "trouble", "annoyance"],
        "antonyms": ["convenience", "ease", "simplicity", "pleasure"],
        "word_forms": {
            "noun": "hassle",
            "verb": "hassle",
            "adjective": "hassle-free",
        },
        "collocations": [
            "too much hassle",
            "worth the hassle",
            "hassle-free experience",
            "avoid the hassle",
        ],
        "cefr_level": "B2",
        "difficulty_score": 5.0,
        "examples": [
            ("Workplace", "Setting up the legacy software environment turned out to be quite a hassle."),
            ("Friends", "Finding a restaurant on Friday evening without a reservation was a real hassle."),
            ("Meeting", "The manager apologized for the administrative hassle caused by the new system update."),
            ("Interview", "She explained how automated workflows helped eliminate daily operational hassle for her team."),
            ("College", "Registering for electives during the first week of semester was an enormous hassle."),
            ("Family", "Moving to a new apartment is always a big hassle, but we finally settled in."),
            ("Shopping", "Returning the damaged package through the post office was surprisingly hassle-free."),
            ("Travel", "Going through airport security during peak holiday travel can be a major hassle."),
            ("Phone call", "I spent twenty minutes on hold with customer service to avoid the hassle of visiting the branch."),
            ("Daily life", "Cooking elaborate meals every weekday is too much of a hassle after long work hours."),
        ],
    },
    "persevere": {
        "simple_meaning": "To continue making an effort to do or achieve something despite difficulties, failure, or opposition.",
        "contextual_meaning": "Used to describe tenacity and continuous determination in the face of hardship or obstacles.",
        "part_of_speech": "verb",
        "pronunciation_text": "per-suh-VEER",
        "synonyms": ["persist", "endure", "carry on", "keep going", "prevail"],
        "antonyms": ["give up", "quit", "surrender", "abandon"],
        "word_forms": {
            "verb": "persevere",
            "noun": "perseverance",
            "adjective": "perseverant",
        },
        "collocations": [
            "persevere with a task",
            "persevere through hardship",
            "persevere in one's efforts",
            "courage to persevere",
        ],
        "cefr_level": "B2",
        "difficulty_score": 6.0,
        "examples": [
            ("Workplace", "Despite early project setbacks, the engineering team persevered and met the deadline."),
            ("Friends", "She encouraged her friend to persevere with the job search despite several rejections."),
            ("Meeting", "The stakeholders agreed that we must persevere with our long-term strategy."),
            ("Interview", "He shared a story of how he persevered through complex technical roadblocks."),
            ("College", "The student persevered through challenging calculus courses to earn her degree."),
            ("Family", "My parents persevered through difficult financial years to support our education."),
            ("Shopping", "I persevered until I finally tracked down the rare out-of-print book online."),
            ("Travel", "We persevered on the steep trail until we reached the breathtaking mountain peak."),
            ("Phone call", "He called to reassure me that if I persevere, good results will follow."),
            ("Daily life", "Learning a new language is tough, but you will succeed if you persevere every day."),
        ],
    },
}


def _get_dynamic_mock_explanation(word: str) -> WordExplanationAI:
    """Generate meaningful dynamic mock data for any word not in the curated DB."""
    clean = word.strip().lower()
    if clean in MOCK_VOCABULARY_DB:
        data = MOCK_VOCABULARY_DB[clean]
        return WordExplanationAI(
            simple_meaning=data["simple_meaning"],
            contextual_meaning=data["contextual_meaning"],
            part_of_speech=data["part_of_speech"],
            pronunciation_text=data["pronunciation_text"],
            synonyms=data["synonyms"],
            antonyms=data["antonyms"],
            word_forms=data["word_forms"],
            collocations=data["collocations"],
            cefr_level=data["cefr_level"],
            difficulty_score=data["difficulty_score"],
        )

    # General fallback for any unexpected word (does not copy 'hesitate' attributes)
    return WordExplanationAI(
        simple_meaning=f"The general meaning, usage, and definition of the English term '{clean}'.",
        contextual_meaning=f"Used in everyday or professional communication when expressing concepts related to '{clean}'.",
        part_of_speech="word",
        pronunciation_text=f"/{clean}/",
        synonyms=[f"term related to {clean}", f"concept of {clean}"],
        antonyms=[],
        word_forms={"base": clean},
        collocations=[f"use '{clean}' in context", f"understand '{clean}'"],
        cefr_level="B1",
        difficulty_score=5.0,
    )


def _get_dynamic_mock_examples(word: str) -> ExampleSetAI:
    """Generate 10 distinct conversational examples for a word."""
    clean = word.strip().lower()
    if clean in MOCK_VOCABULARY_DB and "examples" in MOCK_VOCABULARY_DB[clean]:
        examples = [
            ConversationalExampleAI(context_label=label, example_text=text)
            for label, text in MOCK_VOCABULARY_DB[clean]["examples"]
        ]
        return ExampleSetAI(examples=examples)

    contexts = [
        ("Workplace", f"During the meeting, the manager mentioned how '{clean}' applied to our current workflow."),
        ("Friends", f"My friend asked me what I meant when I used the word '{clean}' earlier."),
        ("Meeting", f"We discussed the importance of understanding '{clean}' in this specific context."),
        ("Interview", f"The interviewer was impressed when the candidate used '{clean}' accurately."),
        ("College", f"In our seminar today, the professor highlighted '{clean}' as a key concept."),
        ("Family", f"We had an interesting family discussion centered around the idea of '{clean}'."),
        ("Shopping", f"The store associate explained the terms clearly so there was no confusion about '{clean}'."),
        ("Travel", f"While traveling, we noticed how people in different regions interpret '{clean}'."),
        ("Phone call", f"On the phone, she made sure to clarify her perspective on '{clean}'."),
        ("Daily life", f"Incorporating '{clean}' into daily conversations helps build confidence in English."),
    ]
    return ExampleSetAI(
        examples=[ConversationalExampleAI(context_label=ctx, example_text=txt) for ctx, txt in contexts]
    )


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM provider for tests and offline development."""

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        _ = (system_prompt, temperature, max_tokens)
        if "Start an engaging" in prompt or "topic:" in prompt.lower():
            topic_match = re.search(r'topic:\s*["\']?([^"\'\n]+)["\']?', prompt, re.IGNORECASE)
            topic = topic_match.group(1).strip() if topic_match else "career planning"
            return f"Hey! I'm really looking forward to discussing {topic} with you today. To get us started, what has been on your mind regarding this recently?"
        return "This is a mocked LLM text response."

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> T:
        _ = (system_prompt, temperature)
        # Check prompt for target word
        word = "hesitate"
        word_match = re.search(r'(?:word\s*["\']|target English word\s*["\'])([a-zA-Z\s\-]+)["\']', prompt)
        if word_match:
            word = word_match.group(1).strip()
        elif "Explain the English word" in prompt or "word \"" in prompt:
            m = re.search(r'word\s*["\']?([a-zA-Z\s\-]+)["\']?', prompt)
            if m:
                word = m.group(1).strip()

        if issubclass(response_schema, WordExplanationAI):
            return _get_dynamic_mock_explanation(word)

        if issubclass(response_schema, ExampleSetAI):
            return _get_dynamic_mock_examples(word)

        if issubclass(response_schema, ScenarioAI):
            return ScenarioAI(
                situation=f"In a team discussion, you are asked to share your thoughts on the project direction, where using '{word}' is particularly relevant.",
                prompt=f"Respond politely and professionally to your team, naturally incorporating the target word '{word}'.",
                context_hint=f"Focus on clear communication and use '{word}' in a natural context.",
            )

        if issubclass(response_schema, PersonalizedScenarioAI):
            domain_match = re.search(r'Target Domain(?:/Context)?:\s*([^\n]+)', prompt, re.IGNORECASE)
            domain = domain_match.group(1).strip() if domain_match else "Workplace"
            level_match = re.search(r'Learner CEFR Level:\s*([A-Za-z0-9]+)', prompt, re.IGNORECASE)
            cefr = level_match.group(1).strip().upper() if level_match else "B1"

            if "travel" in domain.lower():
                situation = f"You are checking into an international hotel and want to inquire politely about room upgrades or itinerary adjustments using the word '{word}'."
                prompt_text = f"Speak with the hotel concierge and naturally incorporate '{word}' in your request."
                hint = "Use a friendly and courteous tone suitable for travel."
            elif "tech" in domain.lower() or "ai" in domain.lower() or "software" in domain.lower():
                situation = f"During a sprint planning meeting, your engineering team is discussing architectural trade-offs where you want to highlight '{word}'."
                prompt_text = f"Explain your technical perspective to the team lead while using '{word}' naturally."
                hint = "Keep your communication clear, structured, and collaborative."
            else:
                situation = f"You are collaborating with colleagues on a project deadline and need to convey your thoughts clearly using '{word}'."
                prompt_text = f"Share your update with your team and naturally integrate '{word}'."
                hint = "Maintain a professional, constructive tone."

            return PersonalizedScenarioAI(
                situation=situation,
                prompt=prompt_text,
                context_hint=hint,
                domain=domain,
                cefr_level=cefr,
            )

        if issubclass(response_schema, EvaluationAI):
            user_text = ""
            resp_m = re.search(r'Learner\'s response:\s*\n?["\']?(.*?)["\']?\s*(?:\n|Evaluate)', prompt, re.DOTALL)
            if resp_m:
                user_text = resp_m.group(1).strip()

            word_root = word.lower()[:4] if len(word) >= 4 else word.lower()
            contains_word = word.lower() in user_text.lower() or word_root in user_text.lower()

            if contains_word and len(user_text) > 5:
                return EvaluationAI(
                    vocabulary_usage_score=9.0,
                    grammar_score=8.5,
                    context_score=9.0,
                    naturalness_score=8.5,
                    overall_score=8.7,
                    feedback=f"Excellent usage of the target word '{word}'! Your sentence is contextually appropriate and natural.",
                    improved_version=f"I would like to clarify that when using '{word}', expressing your intent clearly makes the response very compelling.",
                    vocabulary_used_correctly=True,
                )
            else:
                return EvaluationAI(
                    vocabulary_usage_score=2.0,
                    grammar_score=6.0,
                    context_score=5.0,
                    naturalness_score=5.5,
                    overall_score=4.2,
                    feedback=f"Make sure to explicitly use the target word '{word}' or one of its grammatical forms in your response.",
                    improved_version=f"To include the target word, you could say: 'We should consider how '{word}' affects our current plan.'",
                    vocabulary_used_correctly=False,
                )

        if issubclass(response_schema, ReviewEvaluationAI):
            user_text = ""
            resp_m = re.search(r'Learner\'s response:\s*\n?["\']?(.*?)["\']?\s*(?:\n|Instructions|$)', prompt, re.DOTALL)
            if resp_m:
                user_text = resp_m.group(1).strip()

            word_root = word.lower()[:4] if len(word) >= 4 else word.lower()
            contains_word = word.lower() in user_text.lower() or word_root in user_text.lower()

            if contains_word and len(user_text) > 0:
                return ReviewEvaluationAI(
                    is_correct=True,
                    score=10.0 if user_text.lower() == word.lower() else 9.0,
                    feedback=f"Excellent! You accurately recalled '{word}'.",
                    recalled_word=word,
                )
            else:
                return ReviewEvaluationAI(
                    is_correct=False,
                    score=3.0,
                    feedback=f"Not quite. The target word was '{word}'. Keep practicing to strengthen your memory!",
                    recalled_word=None,
                )

        if issubclass(response_schema, ConversationEvaluationAI):
            # Parse target words from prompt
            target_words_list = []
            tw_match = re.search(r'Target Vocabulary Words:\s*([^\n]+)', prompt)
            if tw_match:
                raw_words = tw_match.group(1).split(",")
                for rw in raw_words:
                    clean = rw.strip().strip("'\"")
                    if clean and clean.lower() != "none":
                        target_words_list.append(clean)

            # Parse transcript from prompt
            transcript = ""
            tr_match = re.search(r'Conversation Transcript:\s*\n?(.*?)(?:\nEvaluation Instructions:|$)', prompt, re.DOTALL)
            if tr_match:
                transcript = tr_match.group(1).lower()

            used_words = []
            missed_words = []
            details = []
            usage_quality = {}

            for tw in target_words_list:
                # Check if word or stem appears in transcript
                tw_stem = tw.lower()[:4] if len(tw) >= 4 else tw.lower()
                if tw.lower() in transcript or tw_stem in transcript:
                    used_words.append(tw)
                    quality = 8.5
                    usage_quality[tw] = quality
                    details.append(
                        VocabularyUsageDetailAI(
                            word=tw,
                            used=True,
                            quality=quality,
                            context=f"Used naturally in conversation: '{tw}'",
                        )
                    )
                else:
                    missed_words.append(tw)
                    details.append(
                        VocabularyUsageDetailAI(
                            word=tw,
                            used=False,
                            quality=None,
                            context=None,
                        )
                    )

            overall_fluency = 8.0 if used_words else 7.0
            feedback = (
                f"Great conversation! You naturally incorporated {len(used_words)} target vocabulary words and communicated your ideas effectively."
                if used_words
                else "Good conversation! You communicated your ideas clearly. Try incorporating the suggested target words in your next chat to reinforce your vocabulary."
            )

            return ConversationEvaluationAI(
                vocabulary_details=details,
                vocabulary_used=used_words,
                vocabulary_missed=missed_words,
                usage_quality=usage_quality,
                overall_fluency=overall_fluency,
                feedback=feedback,
            )

        if issubclass(response_schema, KnowledgeExplanationAI):
            q_match = re.search(r'Learner\'s Question / Query:\s*\n?["\']?(.*?)["\']?\s*(?:\n|Target Word|Category Focus|TRUSTED KNOWLEDGE|$)', prompt)
            query_target = q_match.group(1).lower() if q_match else prompt.lower()

            if "discuss" in query_target or "discuss about" in query_target:
                return KnowledgeExplanationAI(
                    summary="'Discuss' is a transitive verb that directly takes an object without the preposition 'about'.",
                    detailed_explanation="'Discuss' already means 'to talk about'. Adding 'about' after 'discuss' is redundant. While 'talk about' or 'have a discussion about' take 'about', the verb 'discuss' takes a direct object.",
                    rule_applied="Transitive Verb Direct Object Rule",
                    correct_usage=[
                        "Let's discuss the project milestones tomorrow.",
                        "We need to discuss our marketing strategy.",
                        "They had a long discussion about the budget.",
                    ],
                    incorrect_usage=[
                        "'Let's discuss about the problem' (Incorrect: redundant preposition 'about')",
                    ],
                    learning_tip="Remember: 'Discuss = Talk about'. If you wouldn't say 'talk about about', don't say 'discuss about'!",
                    groundedness_confidence=0.98,
                )
            elif "look forward to" in query_target:
                return KnowledgeExplanationAI(
                    summary="'Look forward to' is a phrasal verb where 'to' acts as a preposition, requiring a noun phrase or a gerund (-ing form), not a bare infinitive.",
                    detailed_explanation="In English, when 'to' is a preposition (as in 'look forward to', 'used to', 'object to'), the subsequent verb must be in the gerund form (-ing). Using the base form of the verb after 'look forward to' is one of the most frequent errors among English learners.",
                    rule_applied="Gerund after Prepositional Phrasal Verb",
                    correct_usage=[
                        "I look forward to meeting you next week.",
                        "We look forward to hearing your feedback.",
                        "She looks forward to starting her new role.",
                    ],
                    incorrect_usage=[
                        "'I look forward to meet you' (Incorrect: base verb used after preposition 'to')",
                        "'We look forward to hear from you' (Incorrect: must use gerund 'hearing')",
                    ],
                    learning_tip="Test it with a noun: if you can say 'I look forward to IT / THIS DAY', you must say 'I look forward to DOING it'!",
                    groundedness_confidence=0.95,
                )
            elif "make" in query_target and "do" in query_target:
                return KnowledgeExplanationAI(
                    summary="'Make' is generally used for creating or producing something new, while 'do' is used for actions, obligations, tasks, and repetitive activities.",
                    detailed_explanation="Collocations with 'make' involve producing tangible or intangible results (make a decision, make a mistake, make progress). Collocations with 'do' relate to work, chores, and general unspecified actions (do homework, do business, do research).",
                    rule_applied="Make vs. Do Collocation Distinctions",
                    correct_usage=[
                        "We need to make a strategic decision before Friday.",
                        "Our team did extensive research before launching the feature.",
                        "She made a great suggestion during the meeting.",
                    ],
                    incorrect_usage=[
                        "'Do a decision' (Incorrect: use 'make a decision')",
                        "'Make homework' (Incorrect: use 'do homework')",
                    ],
                    learning_tip="'Make' creates something that didn't exist before; 'do' performs an action or task.",
                    groundedness_confidence=0.94,
                )
            elif "since" in query_target and "for" in query_target:
                return KnowledgeExplanationAI(
                    summary="'Since' refers to a specific starting point in time, whereas 'for' refers to the total duration of a time period.",
                    detailed_explanation="Both 'since' and 'for' are frequently used with Perfect tenses. Use 'since' with a fixed point (since 2020, since yesterday, since 9 AM). Use 'for' with an elapsed duration (for 5 years, for two weeks, for three hours).",
                    rule_applied="Temporal Prepositions: Fixed Point vs. Duration",
                    correct_usage=[
                        "I have lived in London since 2018.",
                        "She has worked as an engineer for six years.",
                        "They have been discussing this issue since this morning.",
                    ],
                    incorrect_usage=[
                        "'I have lived here since 5 years' (Incorrect: 5 years is a duration, use 'for')",
                        "'I have been waiting for 9 AM' (Incorrect: 9 AM is a starting point, use 'since')",
                    ],
                    learning_tip="'Since' = Starting point (dots on a timeline); 'For' = For duration (measuring tape).",
                    groundedness_confidence=0.96,
                )
            elif "affect" in query_target and "effect" in query_target:
                return KnowledgeExplanationAI(
                    summary="'Affect' is almost always a verb meaning to influence or produce a change, while 'effect' is almost always a noun meaning the result or consequence.",
                    detailed_explanation="An easy way to distinguish them: Action = Affect (verb). End result = Effect (noun). When something affects you, it produces an effect on your life.",
                    rule_applied="Affect (Verb) vs. Effect (Noun) Distinction",
                    correct_usage=[
                        "The economic policy will affect interest rates significantly.",
                        "The positive effects of regular study become apparent over time.",
                        "His feedback greatly affected our project direction.",
                    ],
                    incorrect_usage=[
                        "'This change will effect our timeline' (Incorrect: 'affect' is needed as the verb)",
                        "'The medicine had a strange affect' (Incorrect: 'effect' is needed as the noun)",
                    ],
                    learning_tip="Use the acronym RAVEN: Remember Affect is a Verb, Effect is a Noun!",
                    groundedness_confidence=0.97,
                )
            else:
                # Generic robust structured explanation for any other query
                return KnowledgeExplanationAI(
                    summary=f"Analysis of English usage and grammatical structure regarding the provided query.",
                    detailed_explanation="English grammatical rules dictate standard structure, subject-verb agreement, and natural prepositional pairing. Following standard collocations and syntax improves clarity and native-like flow in communication.",
                    rule_applied="Standard English Syntax & Collocation Rules",
                    correct_usage=[
                        "She communicated her ideas clearly during the presentation.",
                        "They made significant progress on their language goals.",
                    ],
                    incorrect_usage=[
                        "Avoid mixing up direct transitive verbs with redundant prepositions.",
                    ],
                    learning_tip="Look for fixed collocations and practice using the full phrase in complete sentences.",
                    groundedness_confidence=0.88,
                )

        raise ValueError(f"Unsupported mock schema: {response_schema}")

    async def generate_conversation(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        _ = (system_prompt, temperature, max_tokens)
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        if "hesitat" in last_user_msg.lower():
            return "It's completely normal to feel that way. What helps you move past hesitation and make a decision?"
        elif "confident" in last_user_msg.lower():
            return "Confidence is key in those situations! How has being confident helped you succeed in your goals?"
        elif "improve" in last_user_msg.lower():
            return "Continuous improvement is a fantastic mindset. What specific areas are you focusing on improving next?"
        elif last_user_msg:
            return "That's a very thoughtful point! How do you usually approach situations like that in your daily life?"

        return "Hello! I'm excited to chat with you today. What are your thoughts on this topic?"

