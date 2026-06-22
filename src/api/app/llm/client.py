from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

from app.config import Settings, settings


class LLMUnavailableError(RuntimeError):
    """Raised when no real LLM provider is configured or usable."""


@dataclass(frozen=True)
class LLMProviderConfig:
    base_url: str
    api_key: str
    model: str


class LLMClient:
    def __init__(self, app_settings: Settings | None = None) -> None:
        self.settings = app_settings or settings

    def is_enabled(self) -> bool:
        try:
            self._provider_config()
        except LLMUnavailableError:
            return False
        return True

    def provider_name(self) -> str:
        return self.settings.llm_provider

    def complete(self, *, system: str, user: str, max_tokens: int = 1200) -> str:
        provider = self._provider_config()
        OpenAI = _openai_client_class()

        client = OpenAI(
            base_url=provider.base_url,
            api_key=provider.api_key,
            timeout=self.settings.llm_timeout,
        )
        last_error = "LLM returned an empty response."
        for attempt in range(self.settings.llm_max_retries + 1):
            response = client.chat.completions.create(
                model=provider.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self.settings.llm_temperature,
                max_tokens=max_tokens,
            )
            content = _extract_response_text(response)
            if content:
                return content
            last_error = _empty_response_error(response)
            if attempt < self.settings.llm_max_retries:
                time.sleep(0.8 * (attempt + 1))
        raise LLMUnavailableError(last_error)

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1200,
    ) -> dict[str, Any]:
        content = self.complete(system=system, user=user, max_tokens=max_tokens)
        parsed = _parse_json_object(content)
        if parsed is None:
            raise LLMUnavailableError(f"LLM response is not a JSON object: {content[:500]}")
        return parsed

    def complete_json_text(self, *, system: str, user: str, max_tokens: int = 1200) -> str:
        return self.complete(system=system, user=user, max_tokens=max_tokens)

    def _provider_config(self) -> LLMProviderConfig:
        provider = self.settings.llm_provider.lower()
        if provider in {"none", ""}:
            raise LLMUnavailableError("A real LLM provider is required. Set LLM_PROVIDER to openai_compatible or deepseek.")

        if provider == "deepseek":
            if not self.settings.deepseek_api_key:
                raise LLMUnavailableError("DEEPSEEK_API_KEY is missing.")
            return LLMProviderConfig(
                base_url=self.settings.deepseek_base_url,
                api_key=self.settings.deepseek_api_key,
                model=self.settings.deepseek_model,
            )

        if provider in {"openai_compatible", "sensenova"}:
            if not self.settings.openai_compatible_api_key:
                raise LLMUnavailableError("OPENAI_COMPATIBLE_API_KEY is missing.")
            if not self.settings.openai_compatible_base_url:
                raise LLMUnavailableError("OPENAI_COMPATIBLE_BASE_URL is missing.")
            if not self.settings.openai_compatible_model:
                raise LLMUnavailableError("OPENAI_COMPATIBLE_MODEL is missing.")
            return LLMProviderConfig(
                base_url=self.settings.openai_compatible_base_url,
                api_key=self.settings.openai_compatible_api_key,
                model=self.settings.openai_compatible_model,
            )

        raise LLMUnavailableError(f"Unsupported LLM_PROVIDER: {self.settings.llm_provider}")


def _parse_json_object(content: str) -> dict[str, Any] | None:
    stripped = content.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        stripped = fenced.group(1)
    else:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            stripped = stripped[start : end + 1]
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _openai_client_class() -> Any:
    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover - depends on local environment
        raise LLMUnavailableError("The openai package is not installed. Run pip install -r requirements.txt.") from exc
    return OpenAI


def parse_json_object(content: str) -> dict[str, Any] | None:
    return _parse_json_object(content)


def _extract_response_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    for choice in choices:
        message = getattr(choice, "message", None)
        if message is None:
            continue
        text = _extract_message_text(message)
        if text:
            return text
    return ""


def _extract_message_text(message: Any) -> str:
    direct_content = getattr(message, "content", None)
    text = _content_to_text(direct_content)
    if text:
        return text

    for attr in ("reasoning_content", "text", "output_text"):
        value = getattr(message, attr, None)
        text = _content_to_text(value)
        if text:
            return text

    if hasattr(message, "model_dump"):
        dumped = message.model_dump()
        for key in ("content", "reasoning_content", "text", "output_text"):
            text = _content_to_text(dumped.get(key))
            if text:
                return text

    if isinstance(message, dict):
        for key in ("content", "reasoning_content", "text", "output_text"):
            text = _content_to_text(message.get(key))
            if text:
                return text
    return ""


def _content_to_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
            else:
                text = getattr(item, "text", None) or getattr(item, "content", None)
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part.strip() for part in parts if part and part.strip()).strip()
    return ""


def _empty_response_error(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    details: list[str] = []
    for choice in choices:
        finish_reason = getattr(choice, "finish_reason", None)
        if finish_reason:
            details.append(f"finish_reason={finish_reason}")
        message = getattr(choice, "message", None)
        if message is not None and hasattr(message, "model_dump"):
            dumped = message.model_dump()
            non_empty_keys = [key for key, value in dumped.items() if value]
            if non_empty_keys:
                details.append(f"message_fields={','.join(non_empty_keys)}")
    suffix = f" ({'; '.join(details)})" if details else ""
    return f"LLM returned an empty response{suffix}."


llm_client = LLMClient()
