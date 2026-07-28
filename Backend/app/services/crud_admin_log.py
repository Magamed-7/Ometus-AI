import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_admin_log import AdminActionLog


def jsonable(payload):
    return json.loads(json.dumps(payload, default=str)) if payload is not None else None


async def log_action(
    admin_user_id: int,
    action: str,
    entity: str,
    db: AsyncSession,
    entity_id: int | None = None,
    payload: dict | None = None,
):
    db.add(
        AdminActionLog(
            admin_user_id=admin_user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            payload_json=jsonable(payload),
        )
    )
    await db.commit()


async def get_actions(db: AsyncSession, limit: int = 50, offset: int = 0):
    result = await db.execute(
        select(AdminActionLog).order_by(AdminActionLog.id.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()
