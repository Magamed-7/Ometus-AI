from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router_admin import admin_router
from app.api.router_ai import ai_router
from app.api.router_appointments import appointments_router
from app.api.router_auth import auth_router
from app.api.router_departments import departments_router
from app.api.router_doctors import doctors_router
from app.api.router_filials import filials_router
from app.api.router_medical_records import medical_records_router
from app.api.router_schedules import schedules_router
from app.api.router_users import users_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.security import decode_token
import app.db.database as database
from app.services import crud_admin_log

app = FastAPI(title="Ometus — Hospital Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(filials_router)
app.include_router(departments_router)
app.include_router(doctors_router)
app.include_router(schedules_router)
app.include_router(appointments_router)
app.include_router(medical_records_router)
app.include_router(ai_router)
app.include_router(admin_router)


@app.middleware("http")
async def audit_admin_actions(request: Request, call_next):
    response = await call_next(request)

    # Пишем только удавшиеся изменения под /api/admin: для AI аудит был (ai_query_log),
    # а админ мог поменять чужое расписание, снести отделение или раздать роли бесследно.
    # Middleware вместо правки двух десятков эндпоинтов — так ни один не забудется
    if (
        request.method in ("POST", "PUT", "PATCH", "DELETE")
        and request.url.path.startswith("/api/admin")
        and response.status_code < 400
    ):
        payload = decode_token((request.headers.get("authorization") or "").removeprefix("Bearer "))

        if payload and payload.get("sub"):
            async with database.get_session_factory()() as session:
                await crud_admin_log.log_action(
                    admin_user_id=int(payload["sub"]),
                    action=request.method,
                    entity=request.url.path,
                    db=session,
                    payload={"query": str(request.url.query)} if request.url.query else None,
                )

    return response
