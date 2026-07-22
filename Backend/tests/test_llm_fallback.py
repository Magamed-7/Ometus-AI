import httpx
import pytest

import app.ai.assistant as assistant
from app.core.config import settings

GROQ_MODELS = ["groq-first", "groq-second"]
GEMINI_MODELS = ["gemini-first", "gemini-second"]

MESSAGE = "болит сердце"
CONTEXT = {"специализация": "кардиолог"}


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPError(f"status {self.status_code}")

    def json(self):
        return self.payload


def groq_reply(text):
    return FakeResponse(200, {"choices": [{"message": {"content": text}}]})


def gemini_reply(*parts):
    return FakeResponse(200, {"candidates": [{"content": {"parts": list(parts)}}]})


def model_of(call):
    if "generateContent" in call["url"]:
        return call["url"].rsplit("/", 1)[1].split(":")[0]

    return call["payload"]["model"]


@pytest.fixture
def calls(monkeypatch):
    recorded = []

    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-groq-key")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(settings, "GROQ_MODELS", GROQ_MODELS)
    monkeypatch.setattr(settings, "GEMINI_MODELS", GEMINI_MODELS)

    return recorded


@pytest.fixture
def transport(monkeypatch, calls):
    def install(handler):
        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def post(self, url, headers=None, json=None):
                calls.append({"url": url, "payload": json})
                return handler(model_of(calls[-1]))

        monkeypatch.setattr(assistant.httpx, "AsyncClient", FakeClient)

    return install


async def test_first_groq_model_answers(transport, calls):
    transport(lambda model: groq_reply("ответ от groq"))

    assert await assistant.ask_llm(MESSAGE, CONTEXT) == "ответ от groq"
    assert [model_of(call) for call in calls] == ["groq-first"]


async def test_broken_groq_model_falls_to_next(transport, calls):
    def handler(model):
        if model == "groq-first":
            return FakeResponse(503, {})

        return groq_reply("ответ запасной модели")

    transport(handler)

    assert await assistant.ask_llm(MESSAGE, CONTEXT) == "ответ запасной модели"
    assert [model_of(call) for call in calls] == ["groq-first", "groq-second"]


async def test_empty_groq_reply_falls_to_next(transport, calls):
    def handler(model):
        if model == "groq-first":
            return groq_reply("   ")

        return groq_reply("ответ запасной модели")

    transport(handler)

    assert await assistant.ask_llm(MESSAGE, CONTEXT) == "ответ запасной модели"
    assert [model_of(call) for call in calls] == ["groq-first", "groq-second"]


async def test_gemini_answers_when_all_groq_models_fail(transport, calls):
    def handler(model):
        if model in GROQ_MODELS:
            return FakeResponse(500, {})

        return gemini_reply({"text": "ответ от gemini"})

    transport(handler)

    assert await assistant.ask_llm(MESSAGE, CONTEXT) == "ответ от gemini"
    assert [model_of(call) for call in calls] == GROQ_MODELS + ["gemini-first"]


async def test_missing_gemini_model_falls_to_next(transport, calls):
    def handler(model):
        if model in GROQ_MODELS or model == "gemini-first":
            return FakeResponse(404, {})

        return gemini_reply({"text": "ответ второй модели gemini"})

    transport(handler)

    assert await assistant.ask_llm(MESSAGE, CONTEXT) == "ответ второй модели gemini"
    assert [model_of(call) for call in calls] == GROQ_MODELS + GEMINI_MODELS


async def test_gemini_thought_parts_are_skipped(transport, calls):
    def handler(model):
        if model in GROQ_MODELS:
            return FakeResponse(500, {})

        return gemini_reply({"thoughtSignature": "EqMNC"}, {"text": "ответ от gemini"})

    transport(handler)

    assert await assistant.ask_llm(MESSAGE, CONTEXT) == "ответ от gemini"


async def test_gemini_is_skipped_without_key(monkeypatch, transport, calls):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    transport(lambda model: FakeResponse(500, {}))

    assert await assistant.ask_llm(MESSAGE, CONTEXT) is None
    assert [model_of(call) for call in calls] == GROQ_MODELS


async def test_template_used_when_every_model_fails(transport, calls):
    transport(lambda model: FakeResponse(500, {}))

    reply = await assistant.build_reply(MESSAGE, "черновик ответа", CONTEXT)

    assert reply == "черновик ответа"
    assert [model_of(call) for call in calls] == GROQ_MODELS + GEMINI_MODELS
