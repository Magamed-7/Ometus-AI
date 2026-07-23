import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "False") == "True"

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "True") == "True"
    EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD: str = os.getenv("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL: str = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
    BASE_URL: str = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    EMAIL_CODE_TTL_MINUTES: int = int(os.getenv("EMAIL_CODE_TTL_MINUTES", "10"))

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODELS: list[str] = os.getenv(
        "GROQ_MODELS", "llama-3.3-70b-versatile,llama-3.1-8b-instant,openai/gpt-oss-120b"
    ).split(",")
    GROQ_URL: str = os.getenv(
        "GROQ_URL", "https://api.groq.com/openai/v1/chat/completions"
    )

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODELS: list[str] = os.getenv(
        "GEMINI_MODELS", "gemini-3.5-flash,gemini-flash-latest,gemini-3.1-flash-lite"
    ).split(",")
    GEMINI_URL: str = os.getenv(
        "GEMINI_URL", "https://generativelanguage.googleapis.com/v1beta/models"
    )

    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:8000"
    ).split(",")


settings = Settings()
