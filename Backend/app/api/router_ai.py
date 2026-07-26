from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import assistant
from app.api.permissions import get_current_patient
from app.core.errors import AppError
from app.db.database import get_db
from app.ai.i18n import DEFAULT_LANGUAGE
from app.schemas.schema_ai import (
    AiTaskOut,
    AskIn,
    AskOut,
    CheckupSuggestionOut,
    ConversationHistoryOut,
    FeedbackIn,
    FeedbackOut,
)
from app.services import crud_ai_feedback, crud_ai_task, crud_conversation

ai_router = APIRouter(prefix="/api/ai", tags=["AI"])


@ai_router.post("/ask", response_model=AskOut)
async def ask_assistant(
    data: AskIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await assistant.ask(data, patient, db)


@ai_router.post("/feedback", response_model=FeedbackOut)
async def leave_feedback(
    data: FeedbackIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    message = await crud_ai_feedback.get_message_for_patient(data.message_id, patient.id, db)

    if message is None:
        raise AppError(code="MESSAGE_NOT_FOUND", message="Сообщение не найдено", status_code=404)

    if message.role != "assistant":
        raise AppError(
            code="FEEDBACK_NOT_APPLICABLE",
            message="Оценить можно только ответ ассистента",
            status_code=400,
        )

    return await crud_ai_feedback.save_feedback(
        data.message_id, patient.id, data.feedback, data.reason, db
    )


@ai_router.post("/ask-async", response_model=AiTaskOut)
async def ask_assistant_async(
    data: AskIn,
    background_tasks: BackgroundTasks,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    task = await crud_ai_task.create_task(
        patient.id, data.model_dump(mode="json", by_alias=True), db
    )
    background_tasks.add_task(assistant.run_ask_task, task.id, data, patient.id)
    return task


@ai_router.get("/tasks/{task_id}", response_model=AiTaskOut)
async def get_ai_task(
    task_id: str,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    task = await crud_ai_task.get_task(task_id, db)

    if task is None or task.patient_id != patient.id:
        raise AppError(code="TASK_NOT_FOUND", message="Задача не найдена", status_code=404)

    return task


@ai_router.get("/suggestion", response_model=CheckupSuggestionOut | None)
async def get_checkup_suggestion(
    language: str = DEFAULT_LANGUAGE,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await assistant.suggest_checkup(patient, db, language)


@ai_router.get("/history/{conversation_id}", response_model=ConversationHistoryOut)
async def get_history(
    conversation_id: int,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    conversation = await crud_conversation.get_conversation(conversation_id, db)

    if conversation is None or conversation.patient_id != patient.id:
        raise AppError(
            code="CONVERSATION_NOT_FOUND", message="Диалог не найден", status_code=404
        )

    messages = await crud_conversation.get_conversation_history(conversation_id, limit=100, db=db)

    return {"conversation_id": conversation_id, "messages": messages}
