from datetime import date, timedelta

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from decimal import Decimal

from app.ai.pricing import MONTHLY_BUDGET, PRICES, calculate_cost
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
            cost_usd=calculate_cost(
                call["provider"],
                call["model"],
                call.get("prompt_tokens"),
                call.get("completion_tokens"),
            ),
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
        func.sum(AiLlmCall.cost_usd),
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
            "cost_usd": cost or Decimal("0"),
        }
        for provider, model, calls, successes, avg_duration, prompt_tokens, completion_tokens, cost in result.all()
    ]


async def get_daily(db: AsyncSession, date_from: date, date_to: date):
    result = await db.execute(
        select(
            func.date(AiLlmCall.created_at),
            func.count(AiLlmCall.id),
            func.sum(cast(AiLlmCall.success, Integer)),
            func.sum(AiLlmCall.cost_usd),
            func.avg(AiLlmCall.duration_ms),
            func.sum(AiLlmCall.prompt_tokens),
            func.sum(AiLlmCall.completion_tokens),
        )
        .where(func.date(AiLlmCall.created_at) >= date_from)
        .where(func.date(AiLlmCall.created_at) <= date_to)
        .group_by(func.date(AiLlmCall.created_at))
    )

    counted = {str(row[0]): row for row in result.all()}

    days = []
    current = date_from

    while current <= date_to:
        row = counted.get(current.isoformat())
        calls = row[1] if row else 0
        succeeded = (row[2] or 0) if row else 0
        days.append(
            {
                "date": current,
                "calls": calls,
                "succeeded": succeeded,
                "failed": calls - succeeded,
                "cost_usd": (row[3] or Decimal("0")) if row else Decimal("0"),
                "avg_duration_ms": int(row[4] or 0) if row else 0,
                "prompt_tokens": (row[5] or 0) if row else 0,
                "completion_tokens": (row[6] or 0) if row else 0,
            }
        )
        current = current + timedelta(days=1)

    return days


async def get_costs(db: AsyncSession, date_from: date | None = None, date_to: date | None = None):
    rows = await get_metrics(db, date_from, date_to)
    total = sum((row["cost_usd"] for row in rows), Decimal("0"))
    budget = MONTHLY_BUDGET

    return {
        "total_usd": total,
        "budget_usd": budget,
        "budget_used_percent": (
            round(float(total / budget * 100), 2) if budget > 0 else None
        ),
        "over_budget": bool(budget > 0 and total > budget),
        "prices_configured": bool(PRICES),
        "by_model": rows,
    }
