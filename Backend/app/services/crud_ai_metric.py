from datetime import date

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_ai_metric import AiLlmCall


async def save_calls(user_id: int, calls: list, db: AsyncSession):
    if not calls:
        return []

    entries = [
        AiLlmCall(
            user_id=user_id,
            provider=call["provider"],
            model=call["model"],
            success=call["success"],
            duration_ms=call["duration_ms"],
            prompt_tokens=call.get("prompt_tokens"),
            completion_tokens=call.get("completion_tokens"),
            error=call.get("error"),
        )
        for call in calls
    ]

    db.add_all(entries)
    await db.commit()
    return entries


async def get_metrics(db: AsyncSession, date_from: date | None = None, date_to: date | None = None):
    query = select(
        AiLlmCall.provider,
        AiLlmCall.model,
        func.count(AiLlmCall.id),
        func.sum(cast(AiLlmCall.success, Integer)),
        func.avg(AiLlmCall.duration_ms),
        func.sum(AiLlmCall.prompt_tokens),
        func.sum(AiLlmCall.completion_tokens),
    ).group_by(AiLlmCall.provider, AiLlmCall.model)

    if date_from:
        query = query.where(func.date(AiLlmCall.created_at) >= date_from)

    if date_to:
        query = query.where(func.date(AiLlmCall.created_at) <= date_to)

    result = await db.execute(query)

    return [
        {
            "provider": provider,
            "model": model,
            "calls": calls,
            "succeeded": successes or 0,
            "failed": calls - (successes or 0),
            "success_rate": round((successes or 0) / calls, 3) if calls else 0,
            "avg_duration_ms": int(avg_duration or 0),
            "prompt_tokens": prompt_tokens or 0,
            "completion_tokens": completion_tokens or 0,
        }
        for provider, model, calls, successes, avg_duration, prompt_tokens, completion_tokens in result.all()
    ]
