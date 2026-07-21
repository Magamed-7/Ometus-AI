from fastapi import Depends

from app.api.auth import get_current_user
from app.core.errors import AppError


def require_role(role: str):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user.role != role:
            raise AppError(code="FORBIDDEN", message="Недостаточно прав", status_code=403)
        return current_user

    return role_checker
