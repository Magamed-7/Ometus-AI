from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import assistant
from app.api.permissions import get_current_patient
from app.db.database import get_db
from app.schemas.schema_ai import AskIn, AskOut

ai_router = APIRouter(prefix="/api/ai", tags=["AI"])


@ai_router.post("/ask", response_model=AskOut)
async def ask_assistant(
    data: AskIn,
    patient=Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    return await assistant.ask(data, patient, db)
