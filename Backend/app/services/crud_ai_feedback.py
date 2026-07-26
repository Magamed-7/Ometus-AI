from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_ai_feedback import AiFeedback
from app.models.model_conversation import Conversation, Message


async def get_message_for_patient(message_id: int, patient_id: int, db: AsyncSession):
    result = await db.execute(
        select(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Message.id == message_id)
        .where(Conversation.patient_id == patient_id)
    )
    return result.scalar_one_or_none()


async def save_feedback(
    message_id: int, patient_id: int, feedback: str, reason: str | None, db: AsyncSession
):
    result = await db.execute(
        select(AiFeedback)
        .where(AiFeedback.message_id == message_id)
        .where(AiFeedback.patient_id == patient_id)
    )
    entry = result.scalar_one_or_none()

    if entry is None:
        entry = AiFeedback(message_id=message_id, patient_id=patient_id)
        db.add(entry)

    entry.feedback = feedback
    entry.reason = reason

    await db.commit()
    await db.refresh(entry)
    return entry


async def get_summary(db: AsyncSession, date_from: date | None = None, date_to: date | None = None):
    query = select(AiFeedback.feedback, func.count(AiFeedback.id)).group_by(AiFeedback.feedback)

    if date_from:
        query = query.where(func.date(AiFeedback.created_at) >= date_from)

    if date_to:
        query = query.where(func.date(AiFeedback.created_at) <= date_to)

    counts = dict((await db.execute(query)).all())
    total = sum(counts.values())

    complaints = select(
        Message.content, AiFeedback.reason, AiFeedback.created_at
    ).join(Message, Message.id == AiFeedback.message_id).where(
        AiFeedback.feedback != "helpful"
    )

    if date_from:
        complaints = complaints.where(func.date(AiFeedback.created_at) >= date_from)

    if date_to:
        complaints = complaints.where(func.date(AiFeedback.created_at) <= date_to)

    problems = (await db.execute(complaints.order_by(AiFeedback.id.desc()).limit(20))).all()

    return {
        "total": total,
        "helpful": counts.get("helpful", 0),
        "partially": counts.get("partially", 0),
        "not_helpful": counts.get("not_helpful", 0),
        "helpful_rate": round(counts.get("helpful", 0) / total, 3) if total else None,
        "recent_complaints": [
            {"reply": reply, "reason": reason, "created_at": created_at}
            for reply, reason, created_at in problems
        ],
    }
