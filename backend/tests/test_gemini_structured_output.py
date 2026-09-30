import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from config import settings
from ai.gemini_provider import GeminiProvider
from ai.openai_provider import extract_json_payload, format_schema_structure
from ai.schemas import WordExplanationAI, ExampleSetAI, ConversationalExampleAI, EvaluationAI


@pytest.fixture
def mock_gemini_provider():
    return GeminiProvider(api_key="test-gemini-key", model="gemini-2.0-flash")


@pytest.fixture
def sample_word_explanation_dict():
    return {
        "simple_meaning": "To pause before saying or doing something because you are uncertain.",
        "contextual_meaning": "Commonly used in professional and personal contexts to describe hesitation.",
        "part_of_speech": "verb",
        "pronunciation_text": "HEZ-ih-tayt",
        "synonyms": ["pause", "waver", "delay"],
        "antonyms": ["proceed", "advance"],
        "word_forms": {"verb": "hesitate", "noun": "hesitation", "adjective": "hesitant"},
        "collocations": ["hesitate to ask", "don't hesitate", "hesitate for a moment"],
        "cefr_level": "B1",
        "difficulty_score": 4.0,
    }


@pytest.fixture
def sample_examples_dict():
    contexts = [
        "Workplace", "Friends", "Meeting", "Interview", "College",
        "Family", "Shopping", "Travel", "Phone call", "Daily life"
    ]
    return {
        "examples": [
            {"context_label": ctx, "example_text": f"In this {ctx.lower()} scenario, you should not hesitate."}
            for ctx in contexts
        ]
    }


class TestExtractJsonPayload:
    def test_clean_json_string(self):
        raw = '{"key": "value", "num": 42}'
        assert extract_json_payload(raw) == raw

    def test_markdown_json_code_block(self):
        raw = '```json\n{\n  "key": "value"\n}\n```'
        assert extract_json_payload(raw) == '{\n  "key": "value"\n}'

    def test_markdown_code_block_without_json_tag(self):
        raw = '```\n{"key": "value"}\n```'
        assert extract_json_payload(raw) == '{"key": "value"}'

    def test_preamble_and_postamble_with_fences(self):
        raw = 'Here is the result:\n```json\n{"key": "value"}\n```\nHope this helps!'
        assert extract_json_payload(raw) == '{"key": "value"}'

    def test_unfenced_with_conversational_text(self):
        raw = 'Sure, here is your JSON object: {"key": "value", "items": [1, 2]} thanks!'
        assert extract_json_payload(raw) == '{"key": "value", "items": [1, 2]}'

    def test_json_array_extraction(self):
        raw = '```json\n[{"id": 1}, {"id": 2}]\n```'
        assert extract_json_payload(raw) == '[{"id": 1}, {"id": 2}]'


class TestFormatSchemaStructure:
    def test_formats_word_explanation_schema(self):
        structure = format_schema_structure(WordExplanationAI)
        assert "simple_meaning" in structure
        assert "contextual_meaning" in structure
        assert "part_of_speech" in structure
        assert "pronunciation_text" in structure
        assert "cefr_level" in structure
        assert "difficulty_score" in structure
        assert "Required top-level keys" in structure

    def test_formats_nested_schema(self):
        structure = format_schema_structure(ExampleSetAI)
        assert "examples" in structure
        assert "ConversationalExampleAI" in structure


@pytest.mark.asyncio
class TestGeminiProviderStructuredGeneration:
    async def test_generate_structured_success_pure_json(self, mock_gemini_provider, sample_word_explanation_dict):
        """Gemini returns pure JSON string matching WordExplanationAI schema."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(sample_word_explanation_dict)
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
            result = await mock_gemini_provider.generate_structured(
                prompt="Explain the word 'hesitate'",
                response_schema=WordExplanationAI,
            )

            assert isinstance(result, WordExplanationAI)
            assert result.simple_meaning == sample_word_explanation_dict["simple_meaning"]
            assert result.part_of_speech == "verb"
            assert result.difficulty_score == 4.0

            # Verify request payload passed response_format
            call_kwargs = mock_post.call_args.kwargs
            payload = call_kwargs["json"]
            assert payload["response_format"] == {"type": "json_object"}
            assert payload["model"] == "gemini-2.0-flash"
            assert payload["temperature"] == 0.3

    async def test_generate_structured_with_markdown_fences(self, mock_gemini_provider, sample_word_explanation_dict):
        """Gemini returns JSON enclosed inside markdown code fences."""
        fenced_content = f"```json\n{json.dumps(sample_word_explanation_dict, indent=2)}\n```"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": fenced_content}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await mock_gemini_provider.generate_structured(
                prompt="Explain the word 'hesitate'",
                response_schema=WordExplanationAI,
            )

            assert isinstance(result, WordExplanationAI)
            assert result.simple_meaning == sample_word_explanation_dict["simple_meaning"]
            assert result.cefr_level == "B1"

    async def test_generate_structured_wrapped_in_data_container(self, mock_gemini_provider, sample_word_explanation_dict):
        """Gemini returns valid instance wrapped inside a 'data' container key."""
        wrapped = {"data": sample_word_explanation_dict}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(wrapped)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await mock_gemini_provider.generate_structured(
                prompt="Explain the word 'hesitate'",
                response_schema=WordExplanationAI,
            )

            assert isinstance(result, WordExplanationAI)
            assert result.simple_meaning == sample_word_explanation_dict["simple_meaning"]

    async def test_generate_structured_example_set(self, mock_gemini_provider, sample_examples_dict):
        """Gemini returns valid ExampleSetAI with 10 conversational examples."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(sample_examples_dict)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await mock_gemini_provider.generate_structured(
                prompt="Generate 10 examples for 'hesitate'",
                response_schema=ExampleSetAI,
            )

            assert isinstance(result, ExampleSetAI)
            assert len(result.examples) == 10
            assert result.examples[0].context_label == "Workplace"

    async def test_generate_structured_malformed_json_raises_502(self, mock_gemini_provider):
        """When Gemini returns unparseable JSON, raise HTTP 502 Bad Gateway."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Not a valid JSON {unclosed"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(HTTPException) as exc_info:
                await mock_gemini_provider.generate_structured(
                    prompt="Explain 'hesitate'",
                    response_schema=WordExplanationAI,
                )
            assert exc_info.value.status_code == 502
            assert "Failed to parse structured AI output from Gemini" in exc_info.value.detail

    async def test_generate_structured_schema_properties_descriptor_raises_502(self, mock_gemini_provider):
        """When Gemini returns a schema definition instead of data values, raise HTTP 502 Bad Gateway."""
        schema_descriptor_output = {
            "description": "Structured AI output for word explanation.",
            "properties": {
                "simple_meaning": {"description": "Clear definition", "type": "string"},
                "contextual_meaning": {"description": "Contextual usage", "type": "string"},
                "part_of_speech": {"description": "Part of speech", "type": "string"},
            },
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(schema_descriptor_output)}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(HTTPException) as exc_info:
                await mock_gemini_provider.generate_structured(
                    prompt="Explain 'hesitate'",
                    response_schema=WordExplanationAI,
                )
            assert exc_info.value.status_code == 502
            assert "Failed to parse structured AI output from Gemini" in exc_info.value.detail

    async def test_gemini_http_status_error_raises_502(self, mock_gemini_provider):
        """When Gemini API returns an upstream HTTP error (e.g. 400 Bad Request), raise 502 Bad Gateway."""
        request = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")
        response = httpx.Response(status_code=400, text="Bad Request to Gemini API", request=request)
        http_err = httpx.HTTPStatusError(message="400 Bad Request", request=request, response=response)

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=http_err):
            with pytest.raises(HTTPException) as exc_info:
                await mock_gemini_provider.generate(prompt="Hello Gemini")
            assert exc_info.value.status_code == 502
            assert "Gemini API error (400)" in exc_info.value.detail

    async def test_gemini_connection_error_raises_503(self, mock_gemini_provider):
        """When Gemini API has a network connection failure, raise 503 Service Unavailable."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.ConnectError("Connection refused")):
            with pytest.raises(HTTPException) as exc_info:
                await mock_gemini_provider.generate(prompt="Hello Gemini")
            assert exc_info.value.status_code == 503
            assert "Gemini connection error" in exc_info.value.detail

    async def test_missing_api_key_raises_503_immediately(self):
        """GeminiProvider with no API key raises 503 Service Unavailable immediately without making network calls."""
        provider = GeminiProvider(api_key="")
        with pytest.raises(HTTPException) as exc_info:
            await provider.generate(prompt="Hello")
        assert exc_info.value.status_code == 503
        assert "Gemini API key is missing" in exc_info.value.detail


@pytest.mark.asyncio
class TestLearnEndpointEndToEndWithGemini:
    async def test_learn_page_content_generation_with_gemini(
        self,
        client: TestClient,
        auth_headers,
        sample_word_explanation_dict,
        sample_examples_dict,
    ):
        """End-to-end integration: User accesses Learn page with LLM_PROVIDER=gemini and generates valid content."""
        # 1. Add vocabulary word
        res_add = client.post("/api/v1/vocabulary", headers=auth_headers, json={"word": "resilient"})
        assert res_add.status_code == 201
        vocab_id = res_add.json()["id"]

        # 2. Mock Gemini API responses for WordExplanationAI and ExampleSetAI
        explanation_payload = dict(sample_word_explanation_dict)
        explanation_payload["simple_meaning"] = "Able to withstand or recover quickly from difficult conditions."
        explanation_payload["part_of_speech"] = "adjective"
        explanation_payload["pronunciation_text"] = "ri-ZIL-yunt"
        explanation_payload["collocations"] = ["remain resilient", "resilient economy", "highly resilient", "build resilience"]

        examples_payload = {
            "examples": [
                {"context_label": ex["context_label"], "example_text": f"The team remained resilient during the challenging project."}
                for ex in sample_examples_dict["examples"]
            ]
        }

        async def mock_post_dispatcher(*args, **kwargs):
            payload = kwargs.get("json", {})
            prompt_content = str(payload.get("messages", []))

            mock_res = MagicMock()
            mock_res.status_code = 200
            mock_res.raise_for_status = MagicMock()

            if "conversational examples" in prompt_content.lower() or "context_label" in prompt_content:
                mock_res.json.return_value = {
                    "choices": [{"message": {"content": f"```json\n{json.dumps(examples_payload)}\n```"}}]
                }
            else:
                mock_res.json.return_value = {
                    "choices": [{"message": {"content": f"```json\n{json.dumps(explanation_payload)}\n```"}}]
                }
            return mock_res

        # 3. Invoke learn endpoint with LLM_PROVIDER=gemini
        with patch.object(settings, "LLM_PROVIDER", "gemini"), \
             patch.object(settings, "GEMINI_API_KEY", "valid-gemini-key"), \
             patch("httpx.AsyncClient.post", side_effect=mock_post_dispatcher):

            res_learn = client.get(f"/api/v1/vocabulary/{vocab_id}/learn", headers=auth_headers)
            assert res_learn.status_code == 200
            data = res_learn.json()

            assert data["word"] == "resilient"
            assert data["details"] is not None
            assert "withstand or recover quickly" in data["details"]["simple_meaning"]
            assert data["details"]["part_of_speech"] == "adjective"
            assert len(data["examples"]) == 10
            assert all("resilient" in ex["example_text"].lower() for ex in data["examples"])
