from abc import ABC, abstractmethod
from typing import TypeVar, Type, List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import HTTPException, status
from config import settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate a raw text response from the model."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> T:
        """Generate a structured response validated against a Pydantic schema."""
        pass

    @abstractmethod
    async def generate_conversation(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Generate a conversational response given message history."""
        pass


def get_llm_provider() -> LLMProvider:
    """
    Factory function to select and instantiate the configured LLM provider.

    Strict Configuration Guarantee:
    - mock: Returns MockLLMProvider for deterministic offline tests.
    - openai: Requires OPENAI_API_KEY. Raises 503 if missing (never silently falls back).
    - gemini: Requires GEMINI_API_KEY. Raises 503 if missing (never silently falls back).
    - openrouter: Requires OPENROUTER_API_KEY. Raises 503 if missing (never silently falls back).
    """
    provider_name = (settings.LLM_PROVIDER or "mock").lower().strip()

    if provider_name == "mock":
        from ai.mock_provider import MockLLMProvider
        return MockLLMProvider()

    if provider_name == "openai":
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI provider is selected (LLM_PROVIDER=openai), but OPENAI_API_KEY is not configured in the environment. Please set OPENAI_API_KEY.",
            )
        from ai.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
        )

    if provider_name == "gemini":
        if not settings.GEMINI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini provider is selected (LLM_PROVIDER=gemini), but GEMINI_API_KEY is not configured in the environment. Please set GEMINI_API_KEY.",
            )
        from ai.gemini_provider import GeminiProvider
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model=getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
        )

    if provider_name == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter provider is selected (LLM_PROVIDER=openrouter), but OPENROUTER_API_KEY is not configured in the environment. Please set OPENROUTER_API_KEY.",
            )
        from ai.openrouter_provider import OpenRouterProvider
        return OpenRouterProvider(
            api_key=settings.OPENROUTER_API_KEY,
            model=getattr(settings, "OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported LLM provider '{settings.LLM_PROVIDER}'. Supported values: mock, openai, gemini, openrouter.",
    )
