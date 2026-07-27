from datetime import UTC, datetime

from sqlalchemy import delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_ai_feedback import AiFeedback
from app.models.model_conversation import Conversation, Message

TITLE_LIMIT = 60


def make_title(message: str):
    text = " ".join(message.split())

    if len(text) <= TITLE_LIMIT:
        return text

    return text[:TITLE_LIMIT].rstrip() + "…"


async def create_conversation(patient_id: int, db: AsyncSession):
    conversation = Conversation(patient_id=patient_id)

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def get_conversation(conversation_id: int, db: AsyncSession):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


async def get_empty_conversation(patient_id: int, db: AsyncSession):
    has_messages = exists().where(Message.conversation_id == Conversation.id)
    result = await db.execute(
        select(Conversation)
        .where(Conversation.patient_id == patient_id)
        .where(~has_messages)
        .order_by(Conversation.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def start_conversation(patient_id: int, db: AsyncSession):
    empty = await get_empty_conversation(patient_id, db)

    if empty is not None:
        return empty

    return await create_conversation(patient_id, db)


async def get_or_create_active_conversation(patient_id: int, db: AsyncSession):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.patient_id == patient_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .limit(1)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        return await create_conversation(patient_id, db)

    return conversation


async def add_message(
    conversation_id: int,
    role: str,
    content: str,
    db: AsyncSession,
    action: str | None = None,
    payload: dict | None = None,
):
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        action=action,
        payload=payload,
    )

    db.add(message)
    conversation = await get_conversation(conversation_id, db)

    if conversation is not None:
        conversation.updated_at = datetime.now(UTC)

        if not conversation.title and role == "user":
            conversation.title = make_title(content)

    await db.commit()
    await db.refresh(message)
    return message


async def get_conversation_history(conversation_id: int, limit: int = 10, db: AsyncSession = None):
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    messages = result.scalars().all()

    return list(reversed(messages))


async def get_recent_conversations(patient_id: int, limit: int = 5, db: AsyncSession = None):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.patient_id == patient_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .limit(limit)
    )
    return result.scalars().all()


def conversation_row(conversation, messages: int, preview: str | None, first: str | None = None):
    title = conversation.title or (make_title(first) if first else None)

    return {
        "id": conversation.id,
        "title": title,
        "messages": messages,
        "preview": preview,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }


async def describe_conversation(conversation, db: AsyncSession):
    messages, first_id, last_id = (
        await db.execute(
            select(
                func.count(Message.id), func.min(Message.id), func.max(Message.id)
            ).where(Message.conversation_id == conversation.id)
        )
    ).one()

    contents = await read_contents([first_id, last_id], db)

    return conversation_row(
        conversation, messages, contents.get(last_id), contents.get(first_id)
    )


async def read_contents(ids: list, db: AsyncSession):
    wanted = [message_id for message_id in ids if message_id]

    if not wanted:
        return {}

    found = await db.execute(select(Message.id, Message.content).where(Message.id.in_(wanted)))
    return dict(found.all())


async def list_conversations(patient_id: int, db: AsyncSession, limit: int = 50, offset: int = 0):
    rows = (
        await db.execute(
            select(
                Conversation,
                func.count(Message.id).label("messages"),
                func.min(Message.id).label("first_message_id"),
                func.max(Message.id).label("last_message_id"),
            )
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .where(Conversation.patient_id == patient_id)
            .group_by(Conversation.id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()

    contents = await read_contents(
        [row.first_message_id for row in rows] + [row.last_message_id for row in rows], db
    )

    return [
        conversation_row(
            row.Conversation,
            row.messages,
            contents.get(row.last_message_id),
            contents.get(row.first_message_id),
        )
        for row in rows
    ]


async def rename_conversation(conversation, title: str, db: AsyncSession):
    conversation.title = make_title(title)
    conversation.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(conversation)
    return conversation


async def delete_conversation(conversation, db: AsyncSession):
    messages = select(Message.id).where(Message.conversation_id == conversation.id)

    await db.execute(delete(AiFeedback).where(AiFeedback.message_id.in_(messages)))
    await db.execute(delete(Message).where(Message.conversation_id == conversation.id))
    await db.delete(conversation)
    await db.commit()
