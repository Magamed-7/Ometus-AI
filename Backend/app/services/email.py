import asyncio
import logging
import secrets
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


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

    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT) as server:
        if settings.EMAIL_USE_TLS:
            server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.send_message(message)


async def deliver_verification_code(email: str, code: str) -> bool:
    # smtplib синхронный: вызванный прямо из async-эндпоинта, он на всё время разговора
    # с почтовым сервером блокирует event loop — на это время встаёт весь сервис.
    # Уносим в поток и никогда не роняем вызывающий код: пользователь в базе уже создан,
    # и падать после этого 500-й — значит оставить аккаунт, в который нельзя войти
    # и на который нельзя зарегистрироваться заново.
    try:
        await asyncio.to_thread(send_verification_code, email, code)
        return True
    except Exception as error:
        logger.warning("не удалось отправить код подтверждения на %s: %s", email, error)
        return False
