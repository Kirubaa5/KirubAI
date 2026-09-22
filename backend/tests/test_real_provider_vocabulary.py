import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from config import settings
from ai.provider import get_llm_provider, LLMProvider
from ai.mock_provider import MockLLMProvider, MOCK_VOCABULARY_DB
from ai.openai_provider import OpenAIProvider
from ai.gemini_provider import GeminiProvider
from ai.openrouter_provider import OpenRouterProvider
from ai.schemas import WordExplanationAI, ExampleSetAI, ConversationalExampleAI


class TestProviderFactoryConfiguration:
    def test_mock_provider_selected(self):
        """When LLM_PROVIDER=mock, get_llm_provider returns MockLLMProvider."""
        with patch.object(settings, "LLM_PROVIDER", "mock"):
            provider = get_llm_provider()
            assert isinstance(provider, MockLLMProvider)

    def test_openai_missing_key_raises_503_no_silent_fallback(self):
        """When LLM_PROVIDER=openai but OPENAI_API_KEY is empty, raise 503 configuration error."""
        with patch.object(settings, "LLM_PROVIDER", "openai"), patch.object(settings, "OPENAI_API_KEY", ""):
            with pytest.raises(HTTPException) as exc_info:
                get_llm_provider()
            assert exc_info.value.status_code == 503
            assert "OPENAI_API_KEY is not configured" in exc_info.value.detail

    def test_openai_configured_returns_openai_provider(self):
        """When LLM_PROVIDER=openai and OPENAI_API_KEY is set, return OpenAIProvider."""
        with patch.object(settings, "LLM_PROVIDER", "openai"), patch.object(settings, "OPENAI_API_KEY", "sk-test-key"):
            provider = get_llm_provider()
            assert isinstance(provider, OpenAIProvider)
            assert provider.api_key == "sk-test-key"
            assert provider.base_url == "https://api.openai.com/v1"

    def test_gemini_missing_key_raises_503_no_silent_fallback(self):
        """When LLM_PROVIDER=gemini but GEMINI_API_KEY is empty, raise 503 configuration error."""
        with patch.object(settings, "LLM_PROVIDER", "gemini"), patch.object(settings, "GEMINI_API_KEY", ""):
            with pytest.raises(HTTPException) as exc_info:
                get_llm_provider()
            assert exc_info.value.status_code == 503
            assert "GEMINI_API_KEY is not configured" in exc_info.value.detail

    def test_gemini_configured_returns_gemini_provider(self):
        """When LLM_PROVIDER=gemini and GEMINI_API_KEY is set, return GeminiProvider."""
        with patch.object(settings, "LLM_PROVIDER", "gemini"), patch.object(settings, "GEMINI_API_KEY", "gemini-test-key"):
            provider = get_llm_provider()
            assert isinstance(provider, GeminiProvider)
            assert provider.api_key == "gemini-test-key"
            assert "generativelanguage.googleapis.com" in provider.base_url

    def test_openrouter_missing_key_raises_503_no_silent_fallback(self):
        """When LLM_PROVIDER=openrouter but OPENROUTER_API_KEY is empty, raise 503 configuration error."""
        with patch.object(settings, "LLM_PROVIDER", "openrouter"), patch.object(settings, "OPENROUTER_API_KEY", ""):
            with pytest.raises(HTTPException) as exc_info:
                get_llm_provider()
            assert exc_info.value.status_code == 503
            assert "OPENROUTER_API_KEY is not configured" in exc_info.value.detail

    def test_openrouter_configured_returns_openrouter_provider(self):
        """When LLM_PROVIDER=openrouter and OPENROUTER_API_KEY is set, return OpenRouterProvider."""
        with patch.object(settings, "LLM_PROVIDER", "openrouter"), patch.object(settings, "OPENROUTER_API_KEY", "or-test-key"):
            provider = get_llm_provider()
            assert isinstance(provider, OpenRouterProvider)
            assert provider.api_key == "or-test-key"
            assert "openrouter.ai" in provider.base_url

    def test_unsupported_provider_raises_500(self):
        """When LLM_PROVIDER is invalid, raise 500 configuration error."""
        with patch.object(settings, "LLM_PROVIDER", "unsupported_provider"):
            with pytest.raises(HTTPException) as exc_info:
                get_llm_provider()
            assert exc_info.value.status_code == 500


class FakeRealLLMProvider(LLMProvider):
    """A mock real LLM provider simulating arbitrary AI vocabulary generation without relying on MOCK_VOCABULARY_DB."""

    async def generate(self, prompt: str, system_prompt=None, temperature=0.7, max_tokens=1000) -> str:
        return "Raw text response from real provider"

    async def generate_structured(self, prompt: str, response_schema, system_prompt=None, temperature=0.3):
        # Extract target word from prompt
        import re
        word = "habit"
        m = re.search(r'["\']([a-zA-Z\s\-]+)["\']', prompt)
        if m:
            word = m.group(1).strip()

        if issubclass(response_schema, WordExplanationAI):
            # Return high-quality, non-generic linguistic data customized to the requested word
            definitions = {
                "habit": ("A settled or regular tendency or practice, especially one that is hard to give up.", "noun", "HAB-it", "B1", 3.0),
                "xylophone": ("A musical instrument played by striking a row of wooden bars of graduated length with small mallets.", "noun", "ZY-luh-fohn", "B2", 6.0),
                "serendipity": ("The occurrence and development of events by chance in a happy or beneficial way.", "noun", "sair-un-DIP-ih-tee", "C1", 7.5),
                "ephemeral": ("Lasting for a very short time; fleeting or transitory.", "adjective", "ih-FEM-er-ul", "C2", 8.0),
                "ambiguous": ("Open to more than one interpretation; not having one obvious meaning.", "adjective", "am-BIG-yoo-us", "B2", 6.5),
                "inevitable": ("Certain to happen; unavoidable.", "adjective", "in-EV-ih-tuh-bul", "B2", 6.0),
                "contemplate": ("To look thoughtfully at something or think deeply about something for a long time.", "verb", "KON-tum-playt", "B2", 5.5),
                "run": ("To move along on foot at a speed faster than a walk.", "verb", "RUN", "A1", 1.5),
                "beautiful": ("Pleasing the senses or mind aesthetically.", "adjective", "BYOO-tih-ful", "A1", 2.0),
                "quickly": ("At a fast speed; rapidly or promptly.", "adverb", "KWIK-lee", "A2", 2.5),
                "decision": ("A conclusion or resolution reached after consideration.", "noun", "dih-SIZH-un", "B1", 3.5),
                "bank": ("A financial institution that receives deposits and channels money into lending activities.", "noun", "BANK", "A1", 2.0),
                "behavior": ("The way in which one acts or conducts oneself, especially toward others.", "noun", "bih-HAYV-yer", "B1", 3.5),
                "hesitate": ("To pause before saying or doing something because you are uncertain or nervous.", "verb", "HEZ-ih-tayt", "B1", 4.0),
            }

            def_info = definitions.get(word.lower(), (
                f"A legitimate English term referring to the specific lexical concept of {word}.",
                "noun",
                f"{word.upper()}",
                "B2",
                5.0,
            ))

            return WordExplanationAI(
                simple_meaning=def_info[0],
                contextual_meaning=f"Used in everyday conversation and professional settings to discuss {word} naturally.",
                part_of_speech=def_info[1],
                pronunciation_text=def_info[2],
                synonyms=[f"synonym-of-{word}-1", f"synonym-of-{word}-2", f"synonym-of-{word}-3"],
                antonyms=[f"antonym-of-{word}-1", f"antonym-of-{word}-2"],
                word_forms={"noun": f"{word}-noun", "verb": f"{word}-verb"},
                collocations=[f"develop a {word}", f"break a {word}", f"good {word}", f"daily {word}"],
                cefr_level=def_info[3],
                difficulty_score=def_info[4],
            )

        if issubclass(response_schema, ExampleSetAI):
            contexts = [
                "Workplace", "Friends", "Meeting", "Interview", "College",
                "Family", "Shopping", "Travel", "Phone call", "Daily life"
            ]
            examples = [
                ConversationalExampleAI(
                    context_label=ctx,
                    example_text=f"In this {ctx.lower()} scenario, understanding how {word} works helps communicate clearly.",
                )
                for ctx in contexts
            ]
            return ExampleSetAI(examples=examples)

        raise ValueError(f"Unsupported schema: {response_schema}")

    async def generate_conversation(self, messages, system_prompt=None, temperature=0.7, max_tokens=500) -> str:
        return "Conversation message from real provider"


@pytest.mark.asyncio
class TestAnyEnglishWordWithRealProvider:
    """Test the complete workflow across the test matrix for any valid English word using a configured real provider."""

    @pytest.mark.parametrize("test_word", [
        # Common
        "habit",
        "behavior",
        "hesitate",
        # Uncommon
        "xylophone",
        "serendipity",
        "ephemeral",
        # Academic
        "ambiguous",
        "inevitable",
        "contemplate",
        # Different parts of speech
        "run",
        "beautiful",
        "quickly",
        "decision",
        # Multiple meaning
        "bank",
    ])
    async def test_word_matrix_generation_with_real_provider(self, client: TestClient, auth_headers, test_word):
        """Verify ANY word from the test matrix succeeds and receives structured content with a real provider."""
        # 1. Add word
        res_add = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": test_word})
        assert res_add.status_code == 201
        vocab_id = res_add.json()["id"]

        # 2. Call learn endpoint with FakeRealLLMProvider injected
        fake_real_provider = FakeRealLLMProvider()
        with patch("services.learning_service.get_llm_provider", return_value=fake_real_provider):
            res_learn = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
            assert res_learn.status_code == 200
            data = res_learn.json()

            # Verify response invariants
            assert data["word"] == test_word.lower()
            assert data["details"] is not None
            assert len(data["details"]["simple_meaning"]) > 10
            assert "qualities and nature of" not in data["details"]["simple_meaning"].lower()
            assert len(data["examples"]) == 10
            assert all(test_word.lower() in ex["example_text"].lower() for ex in data["examples"])

    async def test_critical_regression_habit_not_in_mock_db_succeeds_with_real_provider(self, client: TestClient, auth_headers):
        """Critical regression test: 'habit' is NOT in MOCK_VOCABULARY_DB, but succeeds when real provider is configured."""
        assert "habit" not in MOCK_VOCABULARY_DB

        # 1. Add 'habit'
        res_add = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "habit"})
        assert res_add.status_code == 201
        vocab_id = res_add.json()["id"]

        # 2. Request learning content with real provider
        fake_real_provider = FakeRealLLMProvider()
        with patch("services.learning_service.get_llm_provider", return_value=fake_real_provider):
            res_learn = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
            assert res_learn.status_code == 200
            data = res_learn.json()

            assert data["word"] == "habit"
            assert "settled or regular tendency" in data["details"]["simple_meaning"].lower()
            assert len(data["examples"]) == 10

            # 3. Subsequent request returns cached data from DB without re-generating
            second_res = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
            assert second_res.status_code == 200
            assert second_res.json()["details"]["simple_meaning"] == data["details"]["simple_meaning"]

    async def test_mock_mode_unmocked_word_returns_controlled_503(self, client: TestClient, auth_headers):
        """In mock mode, unmocked word correctly returns HTTP 503 instead of fabricating content."""
        res_add = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "unprecedentedlyrareword"})
        assert res_add.status_code == 201
        vocab_id = res_add.json()["id"]

        with patch.object(settings, "LLM_PROVIDER", "mock"):
            res_learn = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
            assert res_learn.status_code == 503
            assert "not available in mock mode" in res_learn.json()["detail"]
