from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import assistant
from app.api.permissions import get_current_patient
from app.db.database import get_db
from app.schemas.schema_ai import AskIn, AskOut
from app.services import crud_conversation

ai_router = APIRouter(prefix="/api/ai", tags=["AI"])


@ai_router.post("/ask", response_model=AskOut)
async def ask_assistant(
    data: AskIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await assistant.ask(data, patient, db)


@ai_router.get("/history/{conversation_id}")
async def get_history(
    conversation_id: int,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    conversation = await crud_conversation.get_conversation(conversation_id, db)
    if not conversation or conversation.patient_id != patient.id:
        return {"error": "conversation not found or access denied"}

    messages = await crud_conversation.get_conversation_history(conversation_id, limit=100, db=db)
    return {"conversation_id": conversation_id, "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]}
