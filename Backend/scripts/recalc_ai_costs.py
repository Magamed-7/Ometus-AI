import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.ai.pricing import PRICES, calculate_cost
from app.db.database import get_session_factory
from app.models import model_user
from app.models.model_ai_metric import AiLlmCall


async def recalc():
    if not PRICES:
        print("LLM_PRICES не заданы, пересчитывать не по чему")
        return

    factory = get_session_factory()

    async with factory() as db:
        calls = (await db.execute(select(AiLlmCall).order_by(AiLlmCall.id))).scalars().all()
        changed = 0
        total = 0

        for call in calls:
            cost = calculate_cost(
                call.provider, call.model, call.prompt_tokens, call.completion_tokens
            )
            total += cost

            if call.cost_usd != cost:
                call.cost_usd = cost
                changed += 1

        await db.commit()
        print(f"вызовов: {len(calls)}, пересчитано: {changed}, всего потрачено: ${total}")


if __name__ == "__main__":
    asyncio.run(recalc())
