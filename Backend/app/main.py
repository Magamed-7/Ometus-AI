from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router_admin import admin_router
from app.api.router_auth import auth_router
from app.api.router_filials import filials_router
from app.api.router_users import users_router
from app.core.config import settings
from app.core.errors import register_exception_handlers

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
app.include_router(admin_router)
