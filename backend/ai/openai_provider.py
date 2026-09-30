import json
import re
from typing import TypeVar, Type, List, Dict, Any, Optional
from pydantic import BaseModel
import httpx
from fastapi import HTTPException, status
from ai.provider import LLMProvider
from config import settings

T = TypeVar("T", bound=BaseModel)


def extract_json_payload(content: str) -> str:
    """Extract clean JSON substring from LLM response text, stripping markdown code blocks and wrapping text."""
    clean = content.strip()
    # Match markdown code blocks: ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean, re.IGNORECASE)
    if m:
        clean = m.group(1).strip()

    if not (clean.startswith("{") and clean.endswith("}")) and not (clean.startswith("[") and clean.endswith("]")):
        first_brace = clean.find("{")
        last_brace = clean.rfind("}")
        first_bracket = clean.find("[")
        last_bracket = clean.rfind("]")

        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            if last_brace != -1 and last_brace > first_brace:
                clean = clean[first_brace:last_brace + 1]
        elif first_bracket != -1:
            if last_bracket != -1 and last_bracket > first_bracket:
                clean = clean[first_bracket:last_bracket + 1]

    return clean


def format_schema_structure(response_schema: Type[BaseModel]) -> str:
    """Create a structured instance guide from Pydantic model schema for LLM prompting."""
    schema_dict = response_schema.model_json_schema()
    defs = schema_dict.get("$defs", {})

    def resolve_field_type(prop: dict) -> str:
        if "$ref" in prop:
            ref_name = prop["$ref"].split("/")[-1]
            return f"object ({ref_name})"
        prop_type = prop.get("type")
        if prop_type == "array":
            items = prop.get("items", {})
            if "$ref" in items:
                item_ref = items["$ref"].split("/")[-1]
                return f"list of {item_ref} objects"
            return f"list of {items.get('type', 'string')}"
        if prop_type == "object":
            return "dictionary"
        return prop_type or "string"

    properties = schema_dict.get("properties", {})
    required_fields = schema_dict.get("required", list(properties.keys()))

    sample_dict = {}
    for name, prop in properties.items():
        desc = prop.get("description", "")
        ftype = resolve_field_type(prop)
        sample_dict[name] = f"<{ftype}> - {desc}" if desc else f"<{ftype}>"

    lines = [
        "Expected JSON Output Structure (provide real data values for each key, NOT schema definitions):",
        json.dumps(sample_dict, indent=2),
        f"\nRequired top-level keys: {json.dumps(required_fields)}",
    ]

    if defs:
        lines.append("\nNested Object Formats:")
        for def_name, def_schema in defs.items():
            def_props = def_schema.get("properties", {})
            def_sample = {k: f"<{resolve_field_type(v)}> - {v.get('description', '')}" for k, v in def_props.items()}
            lines.append(f"{def_name}: {json.dumps(def_sample, indent=2)}")

    return "\n".join(lines)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key is missing. Please configure OPENAI_API_KEY in your environment.",
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenAI API error ({e.response.status_code}): {e.response.text[:200]}",
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"OpenAI connection error: {str(e)}",
            )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> T:
        schema_guideline = format_schema_structure(response_schema)
        augmented_prompt = (
            f"{prompt}\n\n"
            f"Output requirements:\n"
            f"{schema_guideline}\n\n"
            f"CRITICAL INSTRUCTIONS:\n"
            f"1. Return ONLY a single valid JSON object containing the required keys and real data values.\n"
            f"2. Do NOT output a JSON schema, schema metadata ('type', 'properties', 'description'), or wrapper keys.\n"
            f"3. Do NOT include markdown explanations or conversational text before or after the JSON."
        )

        content = await self.generate(
            prompt=augmented_prompt,
            system_prompt=system_prompt or "You are an expert English language educator. Return only pure JSON containing the requested data.",
            temperature=temperature,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        clean_json = extract_json_payload(content)

        try:
            parsed = json.loads(clean_json)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to parse structured AI output from OpenAI as valid JSON: {str(e)}. Raw output: {clean_json[:200]}",
            )

        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenAI returned non-object JSON (expected JSON object). Raw output: {clean_json[:200]}",
            )

        # 1. Direct validation against Pydantic schema
        try:
            return response_schema.model_validate(parsed)
        except Exception as direct_err:
            # 2. Check if output is wrapped in a container key
            for wrapper_key in ("data", "result", "response", "output", "properties", response_schema.__name__.lower()):
                if wrapper_key in parsed and isinstance(parsed[wrapper_key], dict):
                    try:
                        return response_schema.model_validate(parsed[wrapper_key])
                    except Exception:
                        pass

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to parse structured AI output from OpenAI: {str(direct_err)}. Raw output: {clean_json[:200]}",
            )

    async def generate_conversation(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key is missing. Please configure OPENAI_API_KEY in your environment.",
            )

        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": all_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenAI API error ({e.response.status_code}): {e.response.text[:200]}",
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"OpenAI connection error: {str(e)}",
            )
