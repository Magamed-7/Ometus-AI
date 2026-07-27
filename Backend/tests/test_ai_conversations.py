import pytest

import app.ai.assistant as assistant

from tests.test_ai_tools import ask, setup_doctor, setup_patient

CONVERSATIONS_URL = "/api/ai/conversations"


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    async def fake_ask_llm(message, context, history=None, language="ru", system_prompt=None):
        return None

    monkeypatch.setattr(assistant, "ask_llm", fake_ask_llm)


async def test_first_message_becomes_the_chat_title(client, db):
    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await ask(client, headers, "болит сердце")
    chats = (await client.get(CONVERSATIONS_URL, headers=headers)).json()

    assert len(chats) == 1
    assert chats[0]["title"] == "болит сердце"
    assert chats[0]["messages"] == 2


async def test_long_first_message_is_cut_for_the_title(client, db):
    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    await ask(client, headers, "болит сердце " * 20)
    chats = (await client.get(CONVERSATIONS_URL, headers=headers)).json()

    assert len(chats[0]["title"]) <= 61
    assert chats[0]["title"].endswith("…")


async def test_new_chat_starts_empty_and_does_not_reuse_the_old_one(client, db):
    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    first = (await ask(client, headers, "болит сердце")).json()["conversation_id"]
    started = (await client.post(CONVERSATIONS_URL, headers=headers)).json()

    assert started["id"] != first
    assert started["messages"] == 0
    assert started["title"] is None

    second = (
        await ask(client, headers, "болит горло", conversation_id=started["id"])
    ).json()["conversation_id"]

    assert second == started["id"]


async def test_new_chat_twice_gives_the_same_empty_chat(client, db):
    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    first = (await client.post(CONVERSATIONS_URL, headers=headers)).json()
    second = (await client.post(CONVERSATIONS_URL, headers=headers)).json()

    assert first["id"] == second["id"]


async def test_history_keeps_each_chat_apart(client, db):
    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    heart = (await ask(client, headers, "болит сердце")).json()["conversation_id"]
    started = (await client.post(CONVERSATIONS_URL, headers=headers)).json()["id"]
    await ask(client, headers, "болит горло", conversation_id=started)

    first = (await client.get(f"/api/ai/history/{heart}", headers=headers)).json()
    second = (await client.get(f"/api/ai/history/{started}", headers=headers)).json()

    assert [m["content"] for m in first["messages"] if m["role"] == "user"] == ["болит сердце"]
    assert [m["content"] for m in second["messages"] if m["role"] == "user"] == ["болит горло"]
    assert first["title"] == "болит сердце"


async def test_answered_chat_moves_to_the_top_of_the_list(client, db):
    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    older = (await ask(client, headers, "болит сердце")).json()["conversation_id"]
    newer = (await client.post(CONVERSATIONS_URL, headers=headers)).json()["id"]
    await ask(client, headers, "болит горло", conversation_id=newer)
    await ask(client, headers, "а какое время свободно", conversation_id=older)

    chats = (await client.get(CONVERSATIONS_URL, headers=headers)).json()

    assert [chat["id"] for chat in chats] == [older, newer]
    assert chats[0]["preview"]


async def test_chat_can_be_renamed(client, db):
    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    conversation_id = (await ask(client, headers, "болит сердце")).json()["conversation_id"]
    response = await client.put(
        f"{CONVERSATIONS_URL}/{conversation_id}", json={"title": "Кардиолог"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Кардиолог"
    assert response.json()["messages"] == 2


async def test_empty_title_is_rejected(client, db):
    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    conversation_id = (await ask(client, headers, "болит сердце")).json()["conversation_id"]
    response = await client.put(
        f"{CONVERSATIONS_URL}/{conversation_id}", json={"title": ""}, headers=headers
    )

    assert response.status_code == 422


async def test_deleting_a_chat_removes_its_messages_and_ratings(client, db):
    from sqlalchemy import select

    from app.models.model_ai_feedback import AiFeedback
    from app.models.model_conversation import Message

    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    body = (await ask(client, headers, "болит сердце")).json()
    await client.post(
        "/api/ai/feedback",
        json={"message_id": body["message_id"], "feedback": "helpful"},
        headers=headers,
    )

    response = await client.delete(f"{CONVERSATIONS_URL}/{body['conversation_id']}", headers=headers)

    assert response.status_code == 200
    assert (await client.get(CONVERSATIONS_URL, headers=headers)).json() == []

    messages = await db.execute(
        select(Message).where(Message.conversation_id == body["conversation_id"])
    )
    ratings = await db.execute(select(AiFeedback).where(AiFeedback.message_id == body["message_id"]))

    assert messages.scalars().all() == []
    assert ratings.scalars().all() == []


async def test_ask_returns_the_id_of_its_own_reply(client, db):
    await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)

    body = (await ask(client, headers, "болит сердце")).json()
    history = (await client.get(f"/api/ai/history/{body['conversation_id']}", headers=headers)).json()
    replies = [message for message in history["messages"] if message["role"] == "assistant"]

    assert body["message_id"] == replies[-1]["id"]


async def test_chats_of_another_patient_are_invisible(client, db):
    await setup_doctor(client, db)
    patient_id, owner_headers = await setup_patient(client)
    other_id, other_headers = await setup_patient(client, email="other@ometus.test")

    owner_chat = (await ask(client, owner_headers, "болит сердце")).json()["conversation_id"]

    assert (await client.get(CONVERSATIONS_URL, headers=other_headers)).json() == []

    renamed = await client.put(
        f"{CONVERSATIONS_URL}/{owner_chat}", json={"title": "чужое"}, headers=other_headers
    )
    deleted = await client.delete(f"{CONVERSATIONS_URL}/{owner_chat}", headers=other_headers)

    assert renamed.status_code == 404
    assert deleted.status_code == 404


async def test_doctor_has_no_chat_list(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)

    response = await client.get(CONVERSATIONS_URL, headers=doctor_headers)

    assert response.status_code == 403
