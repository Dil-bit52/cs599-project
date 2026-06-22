from __future__ import annotations

from dataclasses import dataclass

import app.llm.client as client_module
from app.config import settings
from app.llm.client import LLMClient


@dataclass(frozen=True)
class FakeSettings:
    llm_provider: str = "openai_compatible"
    openai_compatible_api_key: str = "test-key"
    openai_compatible_base_url: str = "https://example.invalid/v1"
    openai_compatible_model: str = "test-model"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = settings.deepseek_base_url
    deepseek_model: str = settings.deepseek_model
    llm_timeout: float = 1
    llm_temperature: float = 0
    llm_max_retries: int = 1


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content

    def model_dump(self) -> dict[str, str]:
        return {"content": self.content}


class FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = FakeMessage(content)
        self.finish_reason = "stop"


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return FakeResponse("")
        return FakeResponse("OK")


class FakeChat:
    def __init__(self) -> None:
        self.completions = FakeCompletions()


class FakeOpenAI:
    last_instance: "FakeOpenAI | None" = None

    def __init__(self, **_: object) -> None:
        self.chat = FakeChat()
        FakeOpenAI.last_instance = self


def test_llm_client_retries_empty_response(monkeypatch) -> None:
    monkeypatch.setattr(client_module, "_openai_client_class", lambda: FakeOpenAI)

    llm = LLMClient(FakeSettings())  # type: ignore[arg-type]
    assert llm.complete(system="test", user="test", max_tokens=10) == "OK"
    assert FakeOpenAI.last_instance is not None
    assert FakeOpenAI.last_instance.chat.completions.calls == 2
