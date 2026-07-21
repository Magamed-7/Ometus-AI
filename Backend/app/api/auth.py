from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import decode_token, oauth2_scheme
from app.db.database import get_db
from app.services.crud_user import get_by_id


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    if token is None:
        raise AppError(code="NOT_AUTHENTICATED", message="Требуется авторизация", status_code=401)

    payload = decode_token(token)

    if payload is None or payload.get("type") != "access":
        raise AppError(code="NOT_AUTHENTICATED", message="Требуется авторизация", status_code=401)

    user = await get_by_id(int(payload["sub"]), db)

    if user is None:
        raise AppError(code="NOT_AUTHENTICATED", message="Требуется авторизация", status_code=401)

    return user
