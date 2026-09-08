# AI Architecture — KirubAI

## 1. Design Principles

1. **Provider Independence:** Never couple to a single LLM provider
2. **Structured Outputs:** Always validate AI responses with schemas
3. **Deterministic Logic Separation:** AI generates content; application logic determines state
4. **Cost Efficiency:** Minimize unnecessary AI calls
5. **Graceful Degradation:** Handle AI failures without crashing the application
6. **Testability:** Mock AI provider for all automated tests

## 2. LLM Provider Abstraction

```python
class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a text response."""

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[BaseModel],
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> BaseModel:
        """Generate a structured response validated against a Pydantic schema."""

    @abstractmethod
    async def generate_conversation(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate a conversational response given message history."""
```

### Implementations

| Provider | Class | Use Case |
|----------|-------|----------|
| OpenAI | `OpenAIProvider` | Primary production provider |
| Google Gemini | `GeminiProvider` | Alternative / cost optimization |
| OpenRouter | `OpenRouterProvider` | Multi-model access |
| Mock | `MockLLMProvider` | Testing and development |

### Provider Selection

```python
# config.py
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")  # openai | gemini | openrouter | mock

def get_llm_provider() -> LLMProvider:
    match LLM_PROVIDER:
        case "openai": return OpenAIProvider(api_key=OPENAI_API_KEY)
        case "gemini": return GeminiProvider(api_key=GEMINI_API_KEY)
        case "openrouter": return OpenRouterProvider(api_key=OPENROUTER_API_KEY)
        case "mock": return MockLLMProvider()
        case _: raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")
```

## 3. AI Use Cases

### 3.1 Word Explanation

**Input:** word (str)
**Output:** Structured `WordExplanation`

```python
class WordExplanation(BaseModel):
    simple_meaning: str
    contextual_meaning: str
    part_of_speech: str
    pronunciation_text: str
    synonyms: list[str]
    antonyms: list[str]
    word_forms: dict[str, str]
    collocations: list[str]
    cefr_level: str
    difficulty_score: float  # 1.0 - 10.0
```

**Prompt strategy:** System prompt defines the role (English language expert). User prompt provides the word and requests structured output.

**Temperature:** 0.3 (consistent, factual)

### 3.2 Conversational Examples

**Input:** word (str), count (int = 10)
**Output:** Structured `ExampleSet`

```python
class VocabularyExample(BaseModel):
    context_label: str  # e.g., "Friends", "Workplace"
    example_text: str

class ExampleSet(BaseModel):
    examples: list[VocabularyExample]
```

**Prompt strategy:** Request examples from specific real-life situations (college, workplace, friends, family, interviews, etc.)

**Temperature:** 0.7 (varied, creative)

### 3.3 Scenario Generation

**Input:** word (str), context (optional), difficulty (optional)
**Output:** Structured `Scenario`

```python
class Scenario(BaseModel):
    situation: str
    prompt: str  # What the user should do
    context_hint: str  # Optional subtle hint
```

**Temperature:** 0.7

### 3.4 Answer Evaluation

**Input:** word (str), scenario (str), user_response (str)
**Output:** Structured `Evaluation`

```python
class Evaluation(BaseModel):
    vocabulary_usage_score: float   # 0-10
    grammar_score: float            # 0-10
    context_score: float            # 0-10
    naturalness_score: float        # 0-10
    overall_score: float            # 0-10
    feedback: str
    improved_version: str
    vocabulary_used_correctly: bool
```

**Temperature:** 0.3 (consistent evaluation)

### 3.5 Conversation

**Input:** message history, user vocabulary, topic
**Output:** str (conversational response)

**System prompt includes:**
- Role: Natural English conversation partner
- User's vocabulary list (selected subset)
- Instruction to create natural opportunities for vocabulary use
- Instruction to NOT explicitly tell user to use a word

**Temperature:** 0.8 (natural, varied)

### 3.6 Conversation Evaluation

**Input:** full conversation, target vocabulary
**Output:** Structured `ConversationEvaluation`

```python
class VocabularyUsageDetail(BaseModel):
    word: str
    used: bool
    quality: float | None  # 0-10 if used
    context: str | None

class ConversationEvaluation(BaseModel):
    vocabulary_details: list[VocabularyUsageDetail]
    overall_fluency: float  # 0-10
    feedback: str
```

**Temperature:** 0.3

## 4. Prompt Management

Prompts are stored as Python modules in `backend/ai/prompts/`:

```python
# backend/ai/prompts/explanation.py

SYSTEM_PROMPT = """You are an expert English language teacher..."""

def build_explanation_prompt(word: str) -> str:
    return f"""Explain the English word "{word}" for a non-native speaker..."""
```

### Prompt Design Principles
- Clear role definition in system prompt
- Explicit output format requirements
- Examples where helpful
- Constraints to prevent hallucination
- No unnecessary verbosity

## 5. Response Validation

All structured AI responses are validated:

```python
async def get_word_explanation(self, word: str) -> WordExplanation:
    response = await self.provider.generate_structured(
        prompt=build_explanation_prompt(word),
        response_schema=WordExplanation,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.3,
    )
    return response  # Already validated by Pydantic
```

### Fallback on Validation Failure:
1. Retry with explicit formatting instruction (1 retry max)
2. If still fails, return error to user with a friendly message
3. Log the failure for monitoring

## 6. Mock Provider

```python
class MockLLMProvider(LLMProvider):
    """Returns deterministic responses for testing."""

    async def generate_structured(self, prompt, response_schema, **kwargs):
        # Return pre-defined responses based on schema type
        if response_schema == WordExplanation:
            return WordExplanation(
                simple_meaning="To pause before doing something",
                contextual_meaning="To show uncertainty",
                part_of_speech="verb",
                pronunciation_text="HEZ-ih-tayt",
                synonyms=["pause", "waver"],
                antonyms=["decide", "commit"],
                word_forms={"noun": "hesitation", "adjective": "hesitant"},
                collocations=["hesitate to ask", "don't hesitate"],
                cefr_level="B1",
                difficulty_score=3.5,
            )
        # ... other schemas
```

## 7. Error Handling

```python
class AIError(Exception):
    """Base AI error."""

class AIProviderError(AIError):
    """Provider-level error (API down, auth failed)."""

class AIResponseError(AIError):
    """Invalid response from AI."""

class AIRateLimitError(AIError):
    """Rate limit exceeded."""

class AITimeoutError(AIError):
    """Request timed out."""
```

### Handling Strategy:
| Error | Action |
|-------|--------|
| Rate limit | Retry after backoff (max 2 retries) |
| Timeout | Retry once, then error to user |
| Invalid response | Retry once with stricter prompt, then error |
| Provider down | Return error with friendly message |
| Auth failure | Log critical, return error |

## 8. Cost Optimization

1. **Cache word explanations:** Once generated, store in `word_details`. Don't regenerate.
2. **Use appropriate models:**
   - Expensive (GPT-4 / Gemini Pro): evaluation, conversation
   - Cheap (GPT-3.5 / Gemini Flash): explanation, examples
3. **Limit context in conversations:** Send recent messages + summary, not full history
4. **Structured outputs:** Prevent verbose responses that waste tokens
5. **No unnecessary AI calls:** Review scheduling, mastery calculation, XP — all deterministic

## 9. RAG Integration

### Knowledge Base Contents
- English grammar rules and explanations
- Common usage patterns
- Collocations database
- Common mistakes by non-native speakers
- Learning tips and strategies

### Pipeline
```
Query → Embed (Sentence Transformers) → Search (FAISS) → Retrieve top-k → Augment prompt → Generate
```

### When to Use RAG
- Grammar explanations that go beyond word-level
- "Why is this wrong?" questions
- Learning guidance
- Common mistake patterns

### When NOT to Use RAG
- Simple word explanation (direct LLM is sufficient)
- Scenario generation
- Basic conversation
- Scoring/evaluation

## 10. Separation of Concerns

| Responsibility | Owner |
|---------------|-------|
| Generate explanation | AI |
| Generate examples | AI |
| Generate scenario | AI |
| Evaluate response | AI |
| Generate conversation | AI |
| **Calculate mastery** | **Application logic** |
| **Schedule review** | **Application logic** |
| **Transition vocabulary status** | **Application logic** |
| **Calculate XP** | **Application logic** |
| **Track streaks** | **Application logic** |
| **Persist data** | **Application logic** |

The LLM NEVER directly:
- Writes to the database
- Transitions vocabulary state
- Calculates review dates
- Assigns mastery scores
- Awards XP

All AI outputs pass through the service/domain layer before affecting persistent state.
