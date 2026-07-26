from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_ai_task import AiTask


async def create_task(patient_id: int, request: dict, db: AsyncSession):
    task = AiTask(
        id=str(uuid4()),
        patient_id=patient_id,
        status="pending",
        request_json=request,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(task_id: str, db: AsyncSession):
    result = await db.execute(select(AiTask).where(AiTask.id == task_id))
    return result.scalar_one_or_none()


async def finish_task(task_id: str, result: dict, db: AsyncSession):
    task = await get_task(task_id, db)

    if task is None:
        return None

    task.status = "done"
    task.result_json = result
    task.finished_at = datetime.now()

    await db.commit()
    await db.refresh(task)
    return task


async def fail_task(task_id: str, error: str, db: AsyncSession):
    task = await get_task(task_id, db)

    if task is None:
        return None

    task.status = "failed"
    task.error = error[:500]
    task.finished_at = datetime.now()

    await db.commit()
    await db.refresh(task)
    return task
