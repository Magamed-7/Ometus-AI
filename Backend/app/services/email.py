import secrets
import smtplib
from email.message import EmailMessage

from app.core.config import settings


def generate_code():
    return "".join(secrets.choice("0123456789") for _ in range(6))


def send_verification_code(email: str, code: str):
    message = EmailMessage()
    message["Subject"] = "Код подтверждения — Ometus"
    message["From"] = settings.DEFAULT_FROM_EMAIL
    message["To"] = email
    message.set_content(
        "Здравствуйте!\n\n"
        f"Ваш код подтверждения: {code}\n\n"
        f"Код действителен {settings.EMAIL_CODE_TTL_MINUTES} минут.\n"
        "Если вы не запрашивали этот код — просто проигнорируйте это письмо."
    )

    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
        if settings.EMAIL_USE_TLS:
            server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.send_message(message)
