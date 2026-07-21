from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router_auth import auth_router
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
