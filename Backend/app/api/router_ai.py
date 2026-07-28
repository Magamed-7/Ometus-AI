from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import assistant, staff
from app.api.permissions import (
    get_current_doctor,
    get_current_patient,
    require_role,
)
from app.core.errors import AppError
from app.db.database import get_db
from app.ai.i18n import DEFAULT_LANGUAGE, pick_language
from app.schemas.schema_ai import (
    AiTaskOut,
    AskIn,
    AskOut,
    CheckupSuggestionOut,
    ConversationHistoryOut,
    ConversationOut,
    ConversationRenameIn,
    FeedbackIn,
    FeedbackOut,
    StaffAskIn,
    StaffAskOut,
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


@ai_router.post("/doctor/ask", response_model=StaffAskOut)
async def ask_as_doctor(
    data: StaffAskIn,
    doctor=Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    # доступ ограничен на слое данных: всё внутри спрашивается по `doctor.id`,
    # так что чужих пациентов ассистент не покажет даже при удачной подсказке модели
    language = pick_language(data.language, data.message)
    return await staff.answer_doctor(data.message, doctor, language, db)


@ai_router.post("/admin/ask", response_model=StaffAskOut)
async def ask_as_admin(
    data: StaffAskIn,
    current_user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    language = pick_language(data.language, data.message)
    return await staff.answer_admin(data.message, language, db)


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


async def load_own_conversation(conversation_id: int, patient, db: AsyncSession):
    conversation = await crud_conversation.get_conversation(conversation_id, db)

    if conversation is None or conversation.patient_id != patient.id:
        raise AppError(
            code="CONVERSATION_NOT_FOUND", message="Диалог не найден", status_code=404
        )

    return conversation


@ai_router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await crud_conversation.list_conversations(patient.id, db, limit=limit, offset=offset)


@ai_router.post("/conversations", response_model=ConversationOut)
async def start_conversation(
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    conversation = await crud_conversation.start_conversation(patient.id, db)
    return crud_conversation.conversation_row(conversation, 0, None)


@ai_router.put("/conversations/{conversation_id}", response_model=ConversationOut)
async def rename_conversation(
    conversation_id: int,
    data: ConversationRenameIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    conversation = await load_own_conversation(conversation_id, patient, db)
    await crud_conversation.rename_conversation(conversation, data.title, db)
    return await crud_conversation.describe_conversation(conversation, db)


@ai_router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    conversation = await load_own_conversation(conversation_id, patient, db)
    await crud_conversation.delete_conversation(conversation, db)
    return {"message": "Диалог удалён"}


@ai_router.get("/history/{conversation_id}", response_model=ConversationHistoryOut)
async def get_history(
    conversation_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    conversation = await load_own_conversation(conversation_id, patient, db)
    messages = await crud_conversation.get_conversation_history(conversation_id, limit=limit, db=db)

    return {
        "conversation_id": conversation_id,
        "title": conversation.title,
        "messages": messages,
    }
