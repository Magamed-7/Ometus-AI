import asyncio
import logging
import secrets
import smtplib
from datetime import date, time
from email.message import EmailMessage

from app.core.config import settings
from app.services import notifications

logger = logging.getLogger(__name__)


def generate_code():
    return "".join(secrets.choice("0123456789") for _ in range(6))


def send_email(to: str, subject: str, body: str):
    # общий транспорт: SMTP-соединение и заголовки одни на все письма,
    # а каждый тип письма отличается только темой и текстом
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.DEFAULT_FROM_EMAIL
    message["To"] = to
    message.set_content(body)

    with smtplib.SMTP(
        settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT
    ) as server:
        if settings.EMAIL_USE_TLS:
            server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.send_message(message)


def send_verification_code(email: str, code: str):
    send_email(
        email,
        "Код подтверждения — Ometus",
        "Здравствуйте!\n\n"
        f"Ваш код подтверждения: {code}\n\n"
        f"Код действителен {settings.EMAIL_CODE_TTL_MINUTES} минут.\n"
        "Если вы не запрашивали этот код — просто проигнорируйте это письмо.",
    )


def send_appointment_cancelled(
    email: str, doctor_name: str, day: date, slot_time: time, patient_name: str | None = None
):
    # Причину отсутствия врача пациенту не пишем: «больничный» — это сведения о здоровье
    # сотрудника, и рассылать их по клиентской базе нельзя. Пациенту важно другое:
    # приём не состоится, деньги/время планировать заново, записаться можно тут же.
    greeting = f"Здравствуйте, {patient_name}!" if patient_name else "Здравствуйте!"

    send_email(
        email,
        "Приём отменён — Ometus",
        f"{greeting}\n\n"
        f"К сожалению, приём у врача {doctor_name} "
        f"{day.strftime('%d.%m.%Y')} в {slot_time.strftime('%H:%M')} не состоится: "
        "врач не сможет принять вас в этот день.\n\n"
        "Запись отменена, платить за неё не нужно. "
        "Выбрать другое время можно в личном кабинете или по телефону клиники.\n\n"
        "Извините за неудобство.",
    )


async def deliver_verification_code(email: str, code: str) -> bool:
    # smtplib синхронный: вызванный прямо из async-эндпоинта, он на всё время разговора
    # с почтовым сервером блокирует event loop — на это время встаёт весь сервис.
    # Уносим в поток и никогда не роняем вызывающий код: пользователь в базе уже создан,
    # и падать после этого 500-й — значит оставить аккаунт, в который нельзя войти
    # и на который нельзя зарегистрироваться заново.
    await notifications.publish(email, {"status": "sending"})

    try:
        await asyncio.to_thread(send_verification_code, email, code)
    except Exception as error:
        logger.warning("не удалось отправить код подтверждения на %s: %s", email, error)
        await notifications.publish(email, {"status": "failed"})
        return False

    await notifications.publish(email, {"status": "sent"})
    return True


async def deliver_appointment_cancelled(
    email: str, doctor_name: str, day: date, slot_time: time, patient_name: str | None = None
) -> bool:
    # тот же принцип, что и с кодами: в поток и без исключений наружу. Запись уже отменена
    # в базе, и падать из-за недоступного SMTP нельзя — врач не должен получить 500
    # на оформлении больничного из-за того, что у одного пациента не принял почтовый сервер
    try:
        await asyncio.to_thread(
            send_appointment_cancelled, email, doctor_name, day, slot_time, patient_name
        )
    except Exception as error:
        logger.warning("не удалось отправить письмо об отмене на %s: %s", email, error)
        return False

    return True
