from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_conversation import Conversation, Message


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


async def add_message(conversation_id: int, role: str, content: str, db: AsyncSession):
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )

    db.add(message)
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
