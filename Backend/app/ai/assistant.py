import json

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.emergency_guard import EMERGENCY_MESSAGE, is_emergency
from app.ai.mcp_tools import book_appointment, find_doctors, get_available_time
from app.ai.specialization_map import match_specializations
from app.core.config import settings
from app.schemas.schema_ai import AskIn

SYSTEM_PROMPT = (
    "Ты — ассистент регистратуры клиники Ometus. Твоя единственная задача — помочь пациенту "
    "найти врача нужной специализации и записаться на приём. Категорически запрещено ставить "
    "диагнозы, оценивать тяжесть состояния и давать медицинские рекомендации. Сопоставление "
    "симптома и специализации — техническое, а не медицинское заключение. Отвечай на русском "
    "языке, коротко и по делу, опираясь только на переданные данные системы. Ничего не "
    "выдумывай: если данных нет, так и скажи."
)


async def ask_llm(message: str, context: dict):
    if not settings.GROQ_API_KEY:
        return None

    payload = {
        "model": settings.GROQ_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Запрос пациента: {message}\n\n"
                f"Данные системы: {json.dumps(context, ensure_ascii=False)}",
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                settings.GROQ_URL,
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


async def build_reply(message: str, fallback: str, context: dict):
    generated = await ask_llm(message, {**context, "черновик_ответа": fallback})
    return generated or fallback


def describe_doctors(doctors: list):
    return ", ".join(f"{doctor['full_name']} (#{doctor['doctor_id']})" for doctor in doctors)


def describe_slots(slots: list):
    return ", ".join(f"{slot['date']} {slot['time'][:5]}" for slot in slots[:10])


async def ask(data: AskIn, current_patient, db: AsyncSession):
    if is_emergency(data.message):
        return {"action": "emergency", "reply": EMERGENCY_MESSAGE}

    if data.confirm:
        return await confirm_booking(data, current_patient, db)

    if data.doctor_id:
        return await show_slots(data, db)

    return await suggest_doctors(data, db)


async def confirm_booking(data: AskIn, current_patient, db: AsyncSession):
    if not data.doctor_id or not data.day or not data.slot_time:
        return {
            "action": "clarify",
            "reply": "Чтобы записать, нужны врач, дата и время. Уточните, пожалуйста.",
        }

    result = await book_appointment(
        db, current_patient, data.doctor_id, current_patient.id, data.day, data.slot_time
    )

    if not result["ok"]:
        return {
            "action": "error",
            "error_code": result["error"]["code"],
            "reply": result["error"]["message"],
        }

    appointment = result["data"]
    fallback = (
        f"Записал вас к врачу {appointment['doctor_name']} "
        f"({appointment['specialization']}), отделение {appointment['department']}, "
        f"{appointment['date']} в {appointment['time'][:5]}. "
        f"Номер записи — {appointment['appointment_id']}."
    )

    return {
        "action": "booked",
        "appointment": appointment,
        "reply": await build_reply(data.message, fallback, {"запись": appointment}),
    }


async def show_slots(data: AskIn, db: AsyncSession):
    result = await get_available_time(db, data.doctor_id, data.day)

    if not result["ok"]:
        return {
            "action": "error",
            "error_code": result["error"]["code"],
            "reply": result["error"]["message"],
        }

    slots = result["data"]
    fallback = (
        f"Свободное время: {describe_slots(slots)}. "
        "Скажите, какое время подходит, и я оформлю запись."
    )

    return {
        "action": "slots",
        "slots": slots,
        "reply": await build_reply(data.message, fallback, {"свободные_слоты": slots[:10]}),
    }


async def suggest_doctors(data: AskIn, db: AsyncSession):
    specializations = match_specializations(data.message)

    if not specializations:
        return {
            "action": "clarify",
            "reply": "Не понял, врач какой специализации нужен. Опишите, что беспокоит, "
            "или назовите специализацию — например, кардиолог.",
        }

    if len(specializations) > 1:
        return {
            "action": "clarify",
            "reply": "Уточните, пожалуйста, к какому специалисту записать: "
            + ", ".join(specializations)
            + ".",
        }

    specialization = specializations[0]
    result = await find_doctors(db, specialization)

    if not result["ok"]:
        return {
            "action": "error",
            "specialization": specialization,
            "error_code": result["error"]["code"],
            "reply": result["error"]["message"],
        }

    doctors = result["data"]
    fallback = (
        f"По специализации «{specialization}» принимают: {describe_doctors(doctors)}. "
        "Выберите врача, и я покажу свободное время."
    )

    return {
        "action": "doctors",
        "specialization": specialization,
        "doctors": doctors,
        "reply": await build_reply(
            data.message, fallback, {"специализация": specialization, "врачи": doctors}
        ),
    }
