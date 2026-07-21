from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.model_user import User
from app.schemas.schema_user import UserOut, UserUpdateIn
from app.services import crud_user

users_router = APIRouter(prefix="/api/users", tags=["Users"])


@users_router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@users_router.put("/me", response_model=UserOut)
async def update_me(
    data: UserUpdateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud_user.update_user(current_user, data, db)
