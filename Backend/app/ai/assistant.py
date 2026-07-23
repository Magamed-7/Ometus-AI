import json

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.emergency_guard import EMERGENCY_MESSAGE, is_emergency
from app.ai.mcp_tools import (
    book_appointment,
    cancel_appointment,
    find_doctors,
    get_available_time,
    get_doctor_schedule,
    get_patient_appointments,
    reschedule_appointment,
    tool_error,
)
from app.ai.specialization_map import match_specializations
from app.core.config import settings
from app.schemas.schema_ai import AskIn
from app.services import crud_ai_log

SYSTEM_PROMPT = (
    "Ты — ассистент регистратуры клиники Ometus. Твоя единственная задача — помочь пациенту "
    "найти врача нужной специализации и записаться на приём. Категорически запрещено ставить "
    "диагнозы, оценивать тяжесть состояния и давать медицинские рекомендации. Сопоставление "
    "симптома и специализации — техническое, а не медицинское заключение. Отвечай на русском "
    "языке, коротко и по делу, опираясь только на переданные данные системы. Ничего не "
    "выдумывай: если данных нет, так и скажи."
)


def build_user_prompt(message: str, context: dict):
    return (
        f"Запрос пациента: {message}\n\n"
        f"Данные системы: {json.dumps(context, ensure_ascii=False)}"
    )


def read_gemini_text(data: dict):
    parts = data["candidates"][0]["content"]["parts"]
    return "\n".join(part["text"] for part in parts if part.get("text")).strip()


async def ask_groq(message: str, context: dict):
    if not settings.GROQ_API_KEY:
        return None

    for model in settings.GROQ_MODELS:
        payload = {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(message, context)},
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
                reply = response.json()["choices"][0]["message"]["content"].strip()

                if reply:
                    return reply
        except Exception:
            continue

    return None


async def ask_gemini(message: str, context: dict):
    if not settings.GEMINI_API_KEY:
        return None

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": build_user_prompt(message, context)}]}],
        "generationConfig": {"temperature": 0.2},
    }

    for model in settings.GEMINI_MODELS:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{settings.GEMINI_URL}/{model}:generateContent",
                    headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                    json=payload,
                )
                response.raise_for_status()
                reply = read_gemini_text(response.json())

                if reply:
                    return reply
        except Exception:
            continue

    return None


async def ask_llm(message: str, context: dict):
    return await ask_groq(message, context) or await ask_gemini(message, context)


async def build_reply(message: str, fallback: str, context: dict):
    generated = await ask_llm(message, {**context, "черновик_ответа": fallback})
    return generated or fallback


def describe_doctors(doctors: list):
    return ", ".join(f"{doctor['full_name']} (#{doctor['doctor_id']})" for doctor in doctors)


def describe_slots(slots: list):
    return ", ".join(f"{slot['date']} {slot['time'][:5]}" for slot in slots[:10])


WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def describe_appointments(appointments: list):
    return ", ".join(
        f"№{item['appointment_id']} — {item['date']} {item['time'][:5]} ({item['status']})"
        for item in appointments[:10]
    )


def describe_schedule(schedule: list):
    return ", ".join(
        f"{WEEKDAYS[item['weekday']]} {item['start_time'][:5]}–{item['end_time'][:5]}"
        for item in schedule
    )


async def log_call(current_patient, tool_name: str, params: dict, result: dict, db: AsyncSession):
    await crud_ai_log.log_tool_call(current_patient.user_id, tool_name, params, result, db)


async def ask(data: AskIn, current_patient, db: AsyncSession):
    if is_emergency(data.message):
        await log_call(
            current_patient,
            "emergency_guard",
            {"message": data.message},
            tool_error("EMERGENCY", EMERGENCY_MESSAGE),
            db,
        )
        return {"action": "emergency", "reply": EMERGENCY_MESSAGE}

    if data.intent == "cancel":
        return await cancel_flow(data, current_patient, db)

    if data.intent == "reschedule":
        return await reschedule_flow(data, current_patient, db)

    if data.intent == "my_appointments":
        return await my_appointments_flow(data, current_patient, db)

    if data.intent == "doctor_schedule":
        return await doctor_schedule_flow(data, current_patient, db)

    if data.confirm:
        return await confirm_booking(data, current_patient, db)

    if data.doctor_id:
        return await show_slots(data, current_patient, db)

    return await suggest_doctors(data, current_patient, db)


def tool_failure(result: dict):
    return {
        "action": "error",
        "error_code": result["error"]["code"],
        "reply": result["error"]["message"],
    }


async def cancel_flow(data: AskIn, current_patient, db: AsyncSession):
    if not data.appointment_id:
        return {"action": "clarify", "reply": "Уточните номер записи, которую нужно отменить."}

    result = await cancel_appointment(db, current_patient, data.appointment_id)
    await log_call(
        current_patient, "cancel_appointment", {"appointment_id": data.appointment_id}, result, db
    )

    if not result["ok"]:
        return tool_failure(result)

    fallback = f"Запись №{data.appointment_id} отменена."

    return {
        "action": "cancelled",
        "appointment": result["data"],
        "reply": await build_reply(data.message, fallback, {"отмена": result["data"]}),
    }


async def reschedule_flow(data: AskIn, current_patient, db: AsyncSession):
    if not data.appointment_id or not data.day or not data.slot_time:
        return {
            "action": "clarify",
            "reply": "Чтобы перенести запись, нужны её номер, новая дата и время.",
        }

    result = await reschedule_appointment(
        db, current_patient, data.appointment_id, data.day, data.slot_time
    )
    await log_call(
        current_patient,
        "reschedule_appointment",
        {
            "appointment_id": data.appointment_id,
            "date": str(data.day),
            "time": str(data.slot_time),
        },
        result,
        db,
    )

    if not result["ok"]:
        return tool_failure(result)

    appointment = result["data"]
    fallback = (
        f"Перенёс запись №{appointment['appointment_id']} на "
        f"{appointment['date']} в {appointment['time'][:5]}."
    )

    return {
        "action": "rescheduled",
        "appointment": appointment,
        "reply": await build_reply(data.message, fallback, {"перенос": appointment}),
    }


async def my_appointments_flow(data: AskIn, current_patient, db: AsyncSession):
    result = await get_patient_appointments(db, current_patient, current_patient.id)
    await log_call(
        current_patient,
        "get_patient_appointments",
        {"patient_id": current_patient.id},
        result,
        db,
    )

    if not result["ok"]:
        return tool_failure(result)

    appointments = result["data"]
    fallback = (
        f"Ваши записи: {describe_appointments(appointments)}."
        if appointments
        else "У вас пока нет записей."
    )

    return {
        "action": "my_appointments",
        "appointments": appointments,
        "reply": await build_reply(data.message, fallback, {"записи": appointments[:10]}),
    }


async def doctor_schedule_flow(data: AskIn, current_patient, db: AsyncSession):
    if not data.doctor_id:
        return {"action": "clarify", "reply": "Уточните, расписание какого врача показать."}

    result = await get_doctor_schedule(db, data.doctor_id)
    await log_call(
        current_patient, "get_doctor_schedule", {"doctor_id": data.doctor_id}, result, db
    )

    if not result["ok"]:
        return tool_failure(result)

    schedule = result["data"]
    fallback = f"Врач принимает: {describe_schedule(schedule)}."

    return {
        "action": "doctor_schedule",
        "schedule": schedule,
        "reply": await build_reply(data.message, fallback, {"расписание": schedule}),
    }


async def confirm_booking(data: AskIn, current_patient, db: AsyncSession):
    if not data.doctor_id or not data.day or not data.slot_time:
        return {
            "action": "clarify",
            "reply": "Чтобы записать, нужны врач, дата и время. Уточните, пожалуйста.",
        }

    result = await book_appointment(
        db, current_patient, data.doctor_id, current_patient.id, data.day, data.slot_time
    )
    await log_call(
        current_patient,
        "book_appointment",
        {
            "doctor_id": data.doctor_id,
            "patient_id": current_patient.id,
            "date": str(data.day),
            "time": str(data.slot_time),
        },
        result,
        db,
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


async def show_slots(data: AskIn, current_patient, db: AsyncSession):
    result = await get_available_time(db, data.doctor_id, data.day)
    await log_call(
        current_patient,
        "get_available_time",
        {"doctor_id": data.doctor_id, "date": str(data.day) if data.day else None},
        result,
        db,
    )

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


async def suggest_doctors(data: AskIn, current_patient, db: AsyncSession):
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
    await log_call(
        current_patient, "find_doctors", {"specialization": specialization}, result, db
    )

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
