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
    MultiWordScenarioAI,
    TargetWordEvaluationAI,
    MultiWordEvaluationAI,
    DiagnosticErrorAI,
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
    "fear": {
        "simple_meaning": "An unpleasant emotion caused by the threat of danger, pain, or harm.",
        "contextual_meaning": "Used when describing apprehension, anxiety, or reluctance to take risks in personal and professional situations.",
        "part_of_speech": "noun / verb",
        "pronunciation_text": "FEER",
        "synonyms": ["dread", "anxiety", "apprehension", "terror", "fright"],
        "antonyms": ["courage", "bravery", "confidence", "fearlessness"],
        "word_forms": {
            "noun": "fear",
            "verb": "fear",
            "adjective": "fearful",
            "adverb": "fearfully",
        },
        "collocations": [
            "overcome fear",
            "face one's fear",
            "fear of failure",
            "fear of the unknown",
        ],
        "cefr_level": "A2",
        "difficulty_score": 2.5,
        "examples": [
            ("Workplace", "He overcame his fear of public speaking and delivered a compelling presentation to the board."),
            ("Friends", "I confessed my fear of heights to my friends before we visited the observation tower."),
            ("Meeting", "The team addressed the leadership's fear regarding project timeline delays directly."),
            ("Interview", "She explained how acknowledging her initial fear helped her prepare thoroughly for leadership roles."),
            ("College", "Many freshmen experience a fear of falling behind during their first semester."),
            ("Family", "My father reminded us that fear is natural when taking on major life transitions."),
            ("Shopping", "Online shoppers sometimes experience fear of payment fraud when trying unfamiliar sites."),
            ("Travel", "We didn't let the fear of getting lost stop us from exploring the historic city center."),
            ("Phone call", "He called to ease his mother's fear about his international flight in bad weather."),
            ("Daily life", "Learning to act despite fear is one of the most empowering habits you can develop."),
        ],
    },
    "resilient": {
        "simple_meaning": "Able to withstand or recover quickly from difficult conditions or setbacks.",
        "contextual_meaning": "Used to describe individuals, systems, or organizations that adapt positively to challenges.",
        "part_of_speech": "adjective",
        "pronunciation_text": "ri-ZIL-yunt",
        "synonyms": ["tough", "durable", "hardy", "adaptable", "tenacious"],
        "antonyms": ["fragile", "vulnerable", "weak"],
        "word_forms": {
            "adjective": "resilient",
            "noun": "resilience",
            "adverb": "resiliently",
        },
        "collocations": [
            "remain resilient",
            "resilient economy",
            "highly resilient",
            "build resilience",
        ],
        "cefr_level": "B2",
        "difficulty_score": 6.0,
        "examples": [
            ("Workplace", "Our engineering infrastructure proved remarkably resilient during the unexpected traffic surge."),
            ("Friends", "She is one of the most resilient people I know, always bouncing back with optimism."),
            ("Meeting", "The executive emphasized that building a resilient supply chain is our top priority this year."),
            ("Interview", "He highlighted a situation where his resilient mindset enabled him to turnaround a failing project."),
            ("College", "Students who remain resilient during exam periods achieve better long-term academic outcomes."),
            ("Family", "Our family stayed resilient throughout the challenging move to a new country."),
            ("Shopping", "I chose this outdoor backpack because it is made from exceptionally resilient materials."),
            ("Travel", "Local communities were resilient in rebuilding historical landmarks after the storm."),
            ("Phone call", "She called to assure her colleagues that the operations team remains resilient and on track."),
            ("Daily life", "Developing resilient daily habits helps you navigate unexpected life stress smoothly."),
        ],
    },
    "eloquent": {
        "simple_meaning": "Fluent or persuasive in speaking or writing.",
        "contextual_meaning": "Used to describe speeches, writing, or individuals that convey thoughts with grace and persuasive force.",
        "part_of_speech": "adjective",
        "pronunciation_text": "EL-uh-kwunt",
        "synonyms": ["articulate", "fluent", "expressive", "persuasive"],
        "antonyms": ["inarticulate", "hesitant", "clumsy"],
        "word_forms": {
            "adjective": "eloquent",
            "noun": "eloquence",
            "adverb": "eloquently",
        },
        "collocations": [
            "eloquent speaker",
            "eloquent speech",
            "speak eloquently",
            "eloquent defense",
        ],
        "cefr_level": "C1",
        "difficulty_score": 7.0,
        "examples": [
            ("Workplace", "The keynote speaker gave an eloquent summary of technological innovation and its future."),
            ("Friends", "My friend wrote an eloquent letter of appreciation that touched everyone who read it."),
            ("Meeting", "The product manager made an eloquent case for why user experience must take precedence."),
            ("Interview", "Her eloquent answers demonstrated both deep technical knowledge and leadership clarity."),
            ("College", "The literature professor delivered an eloquent lecture on Renaissance poetry."),
            ("Family", "My uncle gave an eloquent toast at the anniversary dinner that brought tears of joy."),
            ("Shopping", "The boutique catalog featured eloquent descriptions of each handcrafted item."),
            ("Travel", "Our tour guide shared eloquent stories about the ancient architecture of the temple."),
            ("Phone call", "He was very eloquent on the phone, clearly resolving all client questions."),
            ("Daily life", "Practicing writing regularly helps anyone become more eloquent and precise in speech."),
        ],
    },
    "pragmatic": {
        "simple_meaning": "Dealing with things sensibly and realistically based on practical considerations rather than theory.",
        "contextual_meaning": "Used when prioritizing workable, tangible solutions over idealistic or impractical concepts.",
        "part_of_speech": "adjective",
        "pronunciation_text": "prag-MAT-ik",
        "synonyms": ["practical", "realistic", "sensible", "down-to-earth", "utilitarian"],
        "antonyms": ["idealistic", "impractical", "unrealistic", "dogmatic"],
        "word_forms": {
            "adjective": "pragmatic",
            "noun": "pragmatism",
            "adverb": "pragmatically",
        },
        "collocations": [
            "pragmatic approach",
            "pragmatic solution",
            "pragmatic decision",
            "remain pragmatic",
        ],
        "cefr_level": "B2",
        "difficulty_score": 6.5,
        "examples": [
            ("Workplace", "We took a pragmatic approach to the deadline by shipping core features first."),
            ("Friends", "She gave me pragmatic advice on budgeting for my upcoming vacation."),
            ("Meeting", "The committee agreed that a pragmatic compromise was better than an endless stalemate."),
            ("Interview", "He demonstrated a pragmatic balance between innovation and system stability."),
            ("College", "The business professor encouraged students to evaluate case studies pragmatically."),
            ("Family", "My parents adopted a pragmatic plan to renovate the house room by room."),
            ("Shopping", "Choosing a reliable, fuel-efficient vehicle was a pragmatic choice for our daily commute."),
            ("Travel", "Packing light is always the most pragmatic way to travel between multiple cities."),
            ("Phone call", "The consultant offered a pragmatic perspective on how to reduce operational overhead."),
            ("Daily life", "Adopting a pragmatic routine helps reduce decision fatigue throughout the workweek."),
        ],
    },
    "lucid": {
        "simple_meaning": "Expressed clearly and easy to understand; showing an ability to think clearly.",
        "contextual_meaning": "Used to describe clear writing, articulate explanations, or coherent thinking.",
        "part_of_speech": "adjective",
        "pronunciation_text": "LOO-sid",
        "synonyms": ["clear", "comprehensible", "transparent", "coherent", "intelligible"],
        "antonyms": ["confusing", "vague", "ambiguous", "obscure"],
        "word_forms": {
            "adjective": "lucid",
            "noun": "lucidity",
            "adverb": "lucidly",
        },
        "collocations": [
            "lucid explanation",
            "lucid dream",
            "remain lucid",
            "lucid writing style",
        ],
        "cefr_level": "C1",
        "difficulty_score": 7.0,
        "examples": [
            ("Workplace", "The architect provided a lucid diagram that made the system interactions simple to grasp."),
            ("Friends", "I appreciated her lucid advice when I was feeling confused about career choices."),
            ("Meeting", "The financial analyst gave a lucid breakdown of the quarterly revenue variance."),
            ("Interview", "The candidate gave a remarkably lucid explanation of how distributed databases work."),
            ("College", "The physics textbook is renowned for its lucid introduction to quantum mechanics."),
            ("Family", "Even in his nineties, my grandfather maintained a sharp and lucid memory."),
            ("Shopping", "The user manual included lucid step-by-step assembly instructions with diagrams."),
            ("Travel", "The local transit map offered a lucid overview of all train and bus routes."),
            ("Phone call", "The technical support representative gave lucid directions that fixed the router in minutes."),
            ("Daily life", "Writing a daily summary helps keep your thoughts structured and lucid."),
        ],
    },
    "meticulous": {
        "simple_meaning": "Showing great attention to detail; very careful and precise.",
        "contextual_meaning": "Used to describe thorough, high-precision work, craftsmanship, or disciplined investigation.",
        "part_of_speech": "adjective",
        "pronunciation_text": "muh-TIK-yuh-lus",
        "synonyms": ["thorough", "diligent", "scrupulous", "precise", "exact", "painstaking"],
        "antonyms": ["careless", "sloppy", "negligent", "hasty"],
        "word_forms": {
            "adjective": "meticulous",
            "noun": "meticulousness",
            "adverb": "meticulously",
        },
        "collocations": [
            "meticulous attention to detail",
            "meticulous research",
            "meticulous planning",
            "meticulously organized",
        ],
        "cefr_level": "B2",
        "difficulty_score": 6.5,
        "examples": [
            ("Workplace", "Her meticulous code reviews caught critical security edge cases before deployment."),
            ("Friends", "He planned our road trip with meticulous care, booking every hotel and scenic stop."),
            ("Meeting", "The quality assurance lead presented a meticulous audit of all test results."),
            ("Interview", "She highlighted her meticulous approach to data verification and financial reporting."),
            ("College", "The graduate student conducted meticulous laboratory experiments over eighteen months."),
            ("Family", "My grandmother kept meticulous family recipe journals that have lasted for generations."),
            ("Shopping", "The artisan crafted each leather wallet with meticulous hand-stitching."),
            ("Travel", "Thanks to our meticulous itinerary, we navigated three countries without a single delay."),
            ("Phone call", "The lawyer asked meticulous questions to ensure the contract terms were watertight."),
            ("Daily life", "Keeping a meticulous schedule allows you to balance ambitious goals with rest."),
        ],
    },
    "collaborate": {
        "simple_meaning": "To work jointly with others on an activity or project to produce something.",
        "contextual_meaning": "Used in team environments, cross-functional projects, and partnerships.",
        "part_of_speech": "verb",
        "pronunciation_text": "kuh-LAB-uh-rayt",
        "synonyms": ["cooperate", "team up", "work together", "partner", "coordinate"],
        "antonyms": ["compete", "work independently", "oppose"],
        "word_forms": {
            "verb": "collaborate",
            "noun": "collaboration",
            "adjective": "collaborative",
            "adverb": "collaboratively",
        },
        "collocations": [
            "collaborate closely",
            "collaborate on a project",
            "collaborate with stakeholders",
            "willingness to collaborate",
        ],
        "cefr_level": "B1",
        "difficulty_score": 4.5,
        "examples": [
            ("Workplace", "Designers and developers collaborate closely to create intuitive product interfaces."),
            ("Friends", "A few friends decided to collaborate on creating a community podcast."),
            ("Meeting", "The departments met to collaborate on a unified response to the customer feedback."),
            ("Interview", "He described how he collaborated across time zones with international engineering teams."),
            ("College", "Students collaborate on group research presentations throughout the semester."),
            ("Family", "The siblings collaborated to plan a memorable surprise party for their parents."),
            ("Shopping", "The fashion brand collaborated with local artists to launch an exclusive collection."),
            ("Travel", "Local guides collaborated with conservationists to establish eco-friendly hiking trails."),
            ("Phone call", "She called her business partner to collaborate on the client pitch deck."),
            ("Daily life", "Learning to collaborate effectively is one of the most rewarding skills in modern work."),
        ],
    },
    "innovative": {
        "simple_meaning": "Featuring new methods, advanced ideas, or original creative approaches.",
        "contextual_meaning": "Used when highlighting progressive solutions, cutting-edge technology, or novel perspectives.",
        "part_of_speech": "adjective",
        "pronunciation_text": "IN-uh-vay-tiv",
        "synonyms": ["groundbreaking", "creative", "inventive", "novel", "pioneering"],
        "antonyms": ["traditional", "conventional", "outdated", "uninspired"],
        "word_forms": {
            "adjective": "innovative",
            "noun": "innovation",
            "verb": "innovate",
            "adverb": "innovatively",
        },
        "collocations": [
            "innovative solution",
            "innovative technology",
            "innovative approach",
            "highly innovative",
        ],
        "cefr_level": "B2",
        "difficulty_score": 5.5,
        "examples": [
            ("Workplace", "The company introduced an innovative feature that streamlined the customer checkout experience."),
            ("Friends", "She shared an innovative recipe that turned leftover ingredients into a delicious dinner."),
            ("Meeting", "The engineering team pitched an innovative architecture to improve system scalability."),
            ("Interview", "He showcased an innovative automation pipeline he built in his previous role."),
            ("College", "University researchers developed an innovative method for solar energy storage."),
            ("Family", "Our family came up with an innovative schedule to share household responsibilities fairly."),
            ("Shopping", "The store features innovative smart devices designed to reduce home energy use."),
            ("Travel", "The airline introduced an innovative mobile app that simplified international boarding."),
            ("Phone call", "He phoned his colleague to discuss an innovative concept for the new advertising campaign."),
            ("Daily life", "Finding innovative ways to solve small daily hurdles keeps your mind sharp and engaged."),
        ],
    },
}


def _infer_part_of_speech(word: str) -> str:
    """Infer the most plausible grammatical category based on standard English morphology."""
    w = word.strip().lower()
    if w.endswith("ly"):
        return "adverb"
    if any(w.endswith(sfx) for sfx in ("tion", "sion", "ment", "ness", "ance", "ence", "ity", "ship", "ism", "er", "or", "dom", "hood")):
        return "noun"
    if any(w.endswith(sfx) for sfx in ("ful", "less", "able", "ible", "ous", "ive", "ic", "al", "ish", "ent", "ant")):
        return "adjective"
    if any(w.endswith(sfx) for sfx in ("ize", "ise", "ate", "ify", "en")):
        return "verb"
    return "noun / verb"


def _get_dynamic_mock_explanation(word: str) -> WordExplanationAI:
    """Generate meaningful, non-hallucinated mock data for any word not in the curated DB."""
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

    pos = _infer_part_of_speech(clean)

    if pos == "adverb":
        simple_meaning = f"In a manner characterized by '{clean}'; describes how an action or process is carried out."
        collocations = [f"act {clean}", f"speak {clean}", f"clearly {clean}", f"consistently {clean}"]
    elif pos == "noun":
        simple_meaning = f"The state, quality, concept, or condition associated with '{clean}'."
        collocations = [f"experience {clean}", f"sense of {clean}", f"understand {clean}", f"manage {clean}"]
    elif pos == "adjective":
        simple_meaning = f"Characterized by or exhibiting the qualities and nature of '{clean}'."
        collocations = [f"highly {clean}", f"truly {clean}", f"{clean} approach", f"{clean} impact"]
    elif pos == "verb":
        simple_meaning = f"To demonstrate, carry out, or engage in the action of '{clean}'."
        collocations = [f"learn to {clean}", f"manage to {clean}", f"effectively {clean}", f"begin to {clean}"]
    else:
        simple_meaning = f"A core English term used to express the state, quality, or action of '{clean}'."
        collocations = [f"understand {clean}", f"experience {clean}", f"clearly {clean}", f"manage {clean}"]

    contextual_meaning = f"Used in professional, academic, and daily communication when expressing ideas involving '{clean}'."

    # Return safe, non-fabricated linguistic structure
    return WordExplanationAI(
        simple_meaning=simple_meaning,
        contextual_meaning=contextual_meaning,
        part_of_speech=pos,
        pronunciation_text=clean.upper(),
        synonyms=[],
        antonyms=[],
        word_forms={"base": clean},
        collocations=collocations,
        cefr_level="B1",
        difficulty_score=5.0,
    )


def _analyze_text_diagnostics(text: str) -> List[DiagnosticErrorAI]:
    """Deterministically extract linguistic diagnostic errors from text across 5 categories: grammar, collocation, semantic, tone, and spelling."""
    if not text:
        return []

    errors: List[DiagnosticErrorAI] = []
    text_clean = text.strip()

    # 1. Collocation Rules
    if re.search(r'\bdiscuss\s+about\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(discuss\s+about)\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "discuss about"
        errors.append(
            DiagnosticErrorAI(
                error_type="collocation",
                original_text=span,
                explanation="'Discuss' is a transitive verb that directly takes an object without the preposition 'about'.",
                suggested_correction="discuss",
                severity="medium",
            )
        )

    if re.search(r'\b(?:do|did|doing|does)\s+(?:a\s+)?decision\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b((?:do|did|doing|does)\s+(?:a\s+)?decision)\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "do a decision"
        errors.append(
            DiagnosticErrorAI(
                error_type="collocation",
                original_text=span,
                explanation="Standard English collocation requires the verb 'make' with 'decision' (e.g., 'make a decision').",
                suggested_correction="make a decision",
                severity="medium",
            )
        )

    if re.search(r'\b(?:make|made|making)\s+homework\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b((?:make|made|making)\s+homework)\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "make homework"
        errors.append(
            DiagnosticErrorAI(
                error_type="collocation",
                original_text=span,
                explanation="Academic tasks and chores pair with 'do', resulting in 'do homework' rather than 'make homework'.",
                suggested_correction="do homework",
                severity="medium",
            )
        )

    if re.search(r'\b(?:make|made|making)\s+research\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b((?:make|made|making)\s+research)\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "make research"
        errors.append(
            DiagnosticErrorAI(
                error_type="collocation",
                original_text=span,
                explanation="Natural academic collocation prefers 'conduct research' or 'do research' rather than 'make research'.",
                suggested_correction="conduct research",
                severity="medium",
            )
        )

    if re.search(r'\bpay\s+attention\s+on\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(pay\s+attention\s+on)\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "pay attention on"
        errors.append(
            DiagnosticErrorAI(
                error_type="collocation",
                original_text=span,
                explanation="The fixed prepositional collocation is 'pay attention to', not 'on'.",
                suggested_correction="pay attention to",
                severity="medium",
            )
        )

    # 2. Grammar Rules
    if re.search(r'\blook\s+forward\s+to\s+([a-zA-Z]+)\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(look\s+forward\s+to\s+([a-zA-Z]+))\b', text_clean, re.IGNORECASE)
        if m:
            verb_after = m.group(2).lower()
            if not verb_after.endswith("ing") and verb_after in ("meet", "hear", "see", "receive", "start", "work", "join", "discuss"):
                errors.append(
                    DiagnosticErrorAI(
                        error_type="grammar",
                        original_text=m.group(1),
                        explanation="In 'look forward to', 'to' acts as a preposition requiring a gerund (-ing form), not a base infinitive.",
                        suggested_correction=f"look forward to {verb_after}ing",
                        severity="medium",
                    )
                )

    if re.search(r'\bsince\s+\d+\s+(?:years?|months?|days?|hours?|weeks?)\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(since\s+\d+\s+(?:years?|months?|days?|hours?|weeks?))\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "since 5 years"
        duration_part = span.split(" ", 1)[1] if " " in span else "5 years"
        errors.append(
            DiagnosticErrorAI(
                error_type="grammar",
                original_text=span,
                explanation="'Since' designates a specific starting time point; use 'for' to describe a duration of elapsed time.",
                suggested_correction=f"for {duration_part}",
                severity="medium",
            )
        )

    if re.search(r'\bmore\s+(?:better|easier|faster|harder|bigger|smaller)\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(more\s+(?:better|easier|faster|harder|bigger|smaller))\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "more better"
        adj = span.split()[-1]
        errors.append(
            DiagnosticErrorAI(
                error_type="grammar",
                original_text=span,
                explanation="Double comparative: adjectives that already have comparative forms should not be preceded by 'more'.",
                suggested_correction=adj,
                severity="low",
            )
        )

    if re.search(r'\bto\s+much\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(to\s+much)\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "to much"
        errors.append(
            DiagnosticErrorAI(
                error_type="grammar",
                original_text=span,
                explanation="'Too' with double 'o' is required when indicating an excessive amount or degree.",
                suggested_correction="too much",
                severity="low",
            )
        )

    # 3. Semantic Rules
    if re.search(r'\b(?:will\s+effect|can\s+effect|to\s+effect|effect\s+our|effect\s+the|effect\s+this)\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(will\s+effect|can\s+effect|to\s+effect|effect\s+our|effect\s+the|effect\s+this)\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "effect our"
        errors.append(
            DiagnosticErrorAI(
                error_type="semantic",
                original_text=span,
                explanation="'Affect' is the verb meaning to influence or produce a change; 'effect' is the noun consequence.",
                suggested_correction=span.replace("effect", "affect").replace("Effect", "Affect"),
                severity="high",
            )
        )

    if re.search(r'\bloose\s+(?:my|the|our|your|a)\s+(?:job|mind|game|money|chance|opportunity|keys?)\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(loose\s+(?:my|the|our|your|a)\s+(?:job|mind|game|money|chance|opportunity|keys?))\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "loose"
        errors.append(
            DiagnosticErrorAI(
                error_type="semantic",
                original_text=span,
                explanation="'Loose' means not tight or unfastened; 'lose' is the verb meaning to misplace or suffer loss.",
                suggested_correction=span.replace("loose", "lose").replace("Loose", "Lose"),
                severity="medium",
            )
        )

    # 4. Tone Rules
    if re.search(r'\b(?:gonna|wanna|kinda|gotta)\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(gonna|wanna|kinda|gotta)\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "gonna"
        replacements = {"gonna": "going to", "wanna": "want to", "kinda": "kind of", "gotta": "have to"}
        correction = replacements.get(span.lower(), "going to")
        errors.append(
            DiagnosticErrorAI(
                error_type="tone",
                original_text=span,
                explanation="Informal conversational contraction; using full phrasing creates a more professional and articulate register.",
                suggested_correction=correction,
                severity="low",
            )
        )

    if re.search(r'\b(?:hey\s+guys|sup|wassup)\b', text_clean, re.IGNORECASE):
        m = re.search(r'\b(hey\s+guys|sup|wassup)\b', text_clean, re.IGNORECASE)
        span = m.group(1) if m else "hey guys"
        errors.append(
            DiagnosticErrorAI(
                error_type="tone",
                original_text=span,
                explanation="Casual conversational greeting; in professional or workplace scenarios, standard greetings maintain clarity.",
                suggested_correction="hello team",
                severity="low",
            )
        )

    # 5. Spelling Rules
    spelling_checks = [
        ("hestitate", "hesitate", "Misspelled verb: 'hesitate' is spelled with 'si', not 'sti'."),
        ("vividely", "vividly", "Misspelled adverb: 'vividly' does not have an 'e' before 'ly'."),
        ("hasle", "hassle", "Misspelled noun: standard spelling is 'hassle' with double 's'."),
        ("hassell", "hassle", "Misspelled noun: standard spelling is 'hassle' with double 's'."),
        ("perservere", "persevere", "Misspelled verb: 'persevere' does not contain an 'r' before 'v'."),
        ("persever", "persevere", "Misspelled verb: 'persevere' ends with 'vere'."),
        ("meticolous", "meticulous", "Misspelled adjective: standard spelling is 'meticulous'."),
    ]
    for misspelled, corrected, expl in spelling_checks:
        if re.search(r'\b' + re.escape(misspelled) + r'\b', text_clean, re.IGNORECASE):
            m = re.search(r'\b(' + re.escape(misspelled) + r')\b', text_clean, re.IGNORECASE)
            span = m.group(1) if m else misspelled
            errors.append(
                DiagnosticErrorAI(
                    error_type="spelling",
                    original_text=span,
                    explanation=expl,
                    suggested_correction=corrected,
                    severity="low",
                )
            )

    return errors


def _build_actionable_tips(errors: List[DiagnosticErrorAI]) -> List[str]:
    """Generate concise, actionable linguistic recommendations based on errors."""
    if not errors:
        return [
            "Incorporate sophisticated discourse markers to create smooth transitions between your thoughts.",
            "Experiment with nuanced idioms and varied syntactic structures to elevate your natural fluency.",
        ]

    tips = []
    types_found = {e.error_type for e in errors}
    if "collocation" in types_found:
        tips.append("Pay close attention to verb-noun and prepositional collocations (e.g. 'discuss' takes a direct object without 'about').")
    if "grammar" in types_found:
        tips.append("Review phrasal verbs and prepositions that require gerund (-ing) forms.")
    if "semantic" in types_found:
        tips.append("Distinguish carefully between sound-alike words with different grammatical categories (e.g. affect vs. effect).")
    if "tone" in types_found:
        tips.append("Adjust your vocabulary register to match the professional or academic scenario context.")
    if "spelling" in types_found:
        tips.append("Double-check spelling of target root words and morphological suffixes.")

    return tips[:3]


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
        ("Workplace", f"In our team meeting, we discussed how '{clean}' impacts our project roadmap and key deliverables."),
        ("Friends", f"I caught up with my friend to share how understanding '{clean}' helped me navigate a recent challenge."),
        ("Meeting", f"The project lead highlighted '{clean}' as an important consideration for the upcoming quarter."),
        ("Interview", f"During the interview, the candidate explained how they approach '{clean}' in collaborative environments."),
        ("College", f"In today's seminar, the professor analyzed the concept of '{clean}' through real-world case studies."),
        ("Family", f"My family had an open conversation about how to handle '{clean}' with empathy and patience."),
        ("Shopping", f"The store representative clearly explained all details to ensure there was no confusion regarding '{clean}'."),
        ("Travel", f"While traveling abroad, we learned how different cultures perceive and respond to '{clean}'."),
        ("Phone call", f"She called to give an update on the situation and how they plan to address '{clean}' moving forward."),
        ("Daily life", f"Reflecting on '{clean}' each day helps develop stronger communication and self-awareness."),
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
            diag_errors = _analyze_text_diagnostics(user_text)
            tips = _build_actionable_tips(diag_errors)

            if contains_word and len(user_text) > 5:
                grammar_deduction = sum(1.5 for e in diag_errors if e.error_type in ("grammar", "spelling"))
                collocation_deduction = sum(1.5 for e in diag_errors if e.error_type in ("collocation", "semantic", "tone"))
                grammar_score = max(5.0, round(8.5 - grammar_deduction, 1))
                naturalness_score = max(5.0, round(8.5 - collocation_deduction, 1))
                vocab_score = 9.0
                context_score = 9.0
                overall_score = round(vocab_score * 0.3 + grammar_score * 0.2 + context_score * 0.25 + naturalness_score * 0.25, 1)
                cefr_level = "B1" if diag_errors else ("C1" if len(user_text) > 80 else "B2")

                return EvaluationAI(
                    vocabulary_usage_score=vocab_score,
                    grammar_score=grammar_score,
                    context_score=context_score,
                    naturalness_score=naturalness_score,
                    overall_score=overall_score,
                    feedback=f"Excellent usage of the target word '{word}'! Your sentence is contextually appropriate and natural.",
                    improved_version=f"I would like to clarify that when using '{word}', expressing your intent clearly makes the response very compelling.",
                    vocabulary_used_correctly=True,
                    errors=diag_errors,
                    cefr_level=cefr_level,
                    actionable_tips=tips,
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
                    errors=diag_errors,
                    cefr_level="A2",
                    actionable_tips=tips,
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

            diag_errors = _analyze_text_diagnostics(transcript)
            tips = _build_actionable_tips(diag_errors)
            cefr_level = "B2" if (used_words and not diag_errors) else ("B1" if used_words else "A2")

            return ConversationEvaluationAI(
                vocabulary_details=details,
                vocabulary_used=used_words,
                vocabulary_missed=missed_words,
                usage_quality=usage_quality,
                overall_fluency=overall_fluency,
                feedback=feedback,
                errors=diag_errors,
                cefr_level=cefr_level,
                actionable_tips=tips,
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

        if issubclass(response_schema, MultiWordScenarioAI):
            words_list = []
            tw_raw = re.search(r'target words:?\s*([^\n\.]+)', prompt, re.IGNORECASE)
            if tw_raw:
                extracted = re.findall(r'"([a-zA-Z\s\-]+)"', tw_raw.group(1))
                if extracted:
                    words_list = list(dict.fromkeys([w.strip() for w in extracted if w.strip()]))
                else:
                    words_list = list(dict.fromkeys([w.strip().strip("'\"") for w in tw_raw.group(1).split(",") if w.strip()]))

            if not words_list:
                tw_match = re.findall(r'"([a-zA-Z\s\-]+)"', prompt)
                words_list = list(dict.fromkeys([
                    w.strip() for w in tw_match
                    if w.strip().lower() not in ("use my vocabulary", "situation", "prompt", "target_words", "context_hint")
                ]))

            if not words_list:
                words_list = ["hesitate", "vividly", "hassle"]

            words_str = ", ".join(f"'{w}'" for w in words_list)
            return MultiWordScenarioAI(
                situation=f"Your team is coordinating a critical project sprint where timeline constraints and quality benchmarks must be balanced. Several members are debating the best approach.",
                prompt=f"Write a collaborative message to your team outlining your proposed solution, naturally incorporating all of the target words: {words_str}.",
                target_words=words_list,
                context_hint="Maintain a professional and constructive tone, connecting your arguments logically so all words fit naturally into the context.",
            )

        if issubclass(response_schema, MultiWordEvaluationAI):
            target_words_list = []
            tw_raw = re.search(r'targeting:\s*([^\n\.]+)', prompt, re.IGNORECASE)
            if tw_raw:
                extracted = re.findall(r'"([a-zA-Z\s\-]+)"', tw_raw.group(1))
                if extracted:
                    target_words_list = list(dict.fromkeys([w.strip() for w in extracted if w.strip()]))
                else:
                    target_words_list = list(dict.fromkeys([w.strip().strip("'\"") for w in tw_raw.group(1).split(",") if w.strip()]))

            if not target_words_list:
                tw_match = re.findall(r'"([a-zA-Z\s\-]+)"', prompt)
                if tw_match:
                    target_words_list = list(dict.fromkeys([
                        w.strip()
                        for w in tw_match
                        if w.strip().lower() not in (
                            "use my vocabulary", "situation", "prompt", "target_words",
                            "context_hint", "word_evaluations", "word", "used", "used_correctly",
                            "used_naturally", "score", "feedback", "improved_version", "is_successful"
                        )
                    ]))

            if not target_words_list:
                target_words_list = ["hesitate", "vividly", "hassle"]

            # Extract user response
            user_text = ""
            resp_m = re.search(r'Learner\'s response:\s*\n?["\']?(.*?)["\']?\s*(?:\nInstructions|Evaluate|$)', prompt, re.DOTALL)
            if resp_m:
                user_text = resp_m.group(1).strip()

            word_evals = []
            user_text_lower = user_text.lower()
            used_count = 0

            for tw in target_words_list:
                stem = tw.lower()[:4] if len(tw) >= 4 else tw.lower()
                is_used = tw.lower() in user_text_lower or stem in user_text_lower
                if is_used and len(user_text) > 5:
                    used_count += 1
                    word_evals.append(
                        TargetWordEvaluationAI(
                            word=tw,
                            used=True,
                            used_correctly=True,
                            used_naturally=True,
                            score=9.0,
                            feedback=f"Target word '{tw}' was used accurately with natural phrasing.",
                        )
                    )
                else:
                    word_evals.append(
                        TargetWordEvaluationAI(
                            word=tw,
                            used=False,
                            used_correctly=False,
                            used_naturally=False,
                            score=2.0,
                            feedback=f"Target word '{tw}' was not detected or needs clearer contextual usage.",
                        )
                    )

            total_targets = len(target_words_list)
            usage_rate = used_count / max(total_targets, 1)

            if used_count == total_targets and len(user_text) > 10:
                vocab_score = 9.0
                grammar_score = 8.5
                context_score = 9.0
                naturalness_score = 8.5
                overall_score = 8.8
                is_successful = True
                feedback = f"Outstanding work! You successfully incorporated all {total_targets} target words into a cohesive, natural response."
                improved_version = f"To further refine your message: 'I wouldn't hesitate to proceed with this pragmatic approach; remembering our past challenges vividly helps us avoid unnecessary hassle.'"
            elif used_count > 0 and len(user_text) > 10:
                vocab_score = round(min(10.0, max(4.0, usage_rate * 8.0 + 1.0)), 1)
                grammar_score = 7.5
                context_score = 8.0
                naturalness_score = 7.5
                overall_score = round(vocab_score * 0.35 + grammar_score * 0.20 + context_score * 0.25 + naturalness_score * 0.20, 1)
                is_successful = overall_score >= 6.0 and used_count >= max(1, total_targets // 2)
                feedback = f"Good effort! You incorporated {used_count} of {total_targets} target words effectively. Review the missed words to achieve complete synthesis."
                improved_version = f"A complete synthesis incorporating all target words: 'We should not hesitate to implement this solution, keeping our goals vividly in mind while minimizing team hassle.'"
            else:
                vocab_score = 2.5
                grammar_score = 6.0
                context_score = 5.0
                naturalness_score = 5.0
                overall_score = 4.2
                is_successful = False
                feedback = f"Please ensure you explicitly use all target words ({', '.join(target_words_list)}) in your response to demonstrate active mastery."
                improved_version = f"Example incorporating all target words: 'Don't hesitate to reach out if this process causes any hassle, so we can vividly demonstrate our progress.'"

            diag_errors = _analyze_text_diagnostics(user_text)
            tips = _build_actionable_tips(diag_errors)
            cefr_level = "B2" if (is_successful and not diag_errors) else ("B1" if is_successful else "A2")

            return MultiWordEvaluationAI(
                word_evaluations=word_evals,
                vocabulary_usage_score=vocab_score,
                grammar_score=grammar_score,
                context_score=context_score,
                naturalness_score=naturalness_score,
                overall_score=overall_score,
                feedback=feedback,
                improved_version=improved_version,
                is_successful=is_successful,
                errors=diag_errors,
                cefr_level=cefr_level,
                actionable_tips=tips,
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

