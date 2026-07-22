from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_ai_log import AiQueryLog


async def log_tool_call(
    user_id: int, tool_name: str, params: dict, result: dict, db: AsyncSession
):
    entry = AiQueryLog(
        user_id=user_id,
        tool_name=tool_name,
        params_json=params,
        status="ok" if result["ok"] else "error",
        message=None if result["ok"] else result["error"]["code"],
    )

    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def get_user_logs(user_id: int, db: AsyncSession):
    result = await db.execute(
        select(AiQueryLog)
        .where(AiQueryLog.user_id == user_id)
        .order_by(AiQueryLog.id.desc())
    )
    return result.scalars().all()
