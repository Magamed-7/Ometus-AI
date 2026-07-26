import json

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.emergency_guard import (
    EMERGENCY_MESSAGES,
    HIGH_SEVERITY_NOTES,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    assess_symptom_severity,
    is_emergency,
)
from app.ai.i18n import DEFAULT_LANGUAGE, pick_language, translate
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
from app.ai.specialization_map import find_fallback_specialists, match_specializations
from app.core.config import settings
from app.schemas.schema_ai import AskIn
from app.services import crud_ai_log, crud_appointment, crud_conversation

SYSTEM_PROMPT_TEMPLATE = (
    "Ты — ассистент регистратуры клиники Ometus. Твоя единственная задача — помочь пациенту "
    "найти врача нужной специализации и записаться на приём. Категорически запрещено ставить "
    "диагнозы, оценивать тяжесть состояния и давать медицинские рекомендации. Сопоставление "
    "симптома и специализации — техническое, а не медицинское заключение. Отвечай на {language} "
    "языке, коротко и по делу, опираясь только на переданные данные системы. Ничего не "
    "выдумывай: если данных нет, так и скажи."
)

SYSTEM_PROMPT = SYSTEM_PROMPT_TEMPLATE.format(language="русском")


def build_system_prompt(language: str):
    return SYSTEM_PROMPT_TEMPLATE.format(language=translate("answer_language", language))


def build_user_prompt(message: str, context: dict, history: list | None = None):
    prompt = f"Запрос пациента: {message}\n\n"

    if history:
        prompt += "История диалога:\n"
        for msg in history:
            prompt += f"- {msg.role}: {msg.content}\n"
        prompt += "\n"

    prompt += f"Данные системы: {json.dumps(context, ensure_ascii=False)}"
    return prompt


def read_gemini_text(data: dict):
    parts = data["candidates"][0]["content"]["parts"]
    return "\n".join(part["text"] for part in parts if part.get("text")).strip()


async def ask_groq(message: str, context: dict, history: list | None = None, language: str = DEFAULT_LANGUAGE):
    if not settings.GROQ_API_KEY:
        return None

    for model in settings.GROQ_MODELS:
        payload = {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": build_system_prompt(language)},
                {"role": "user", "content": build_user_prompt(message, context, history)},
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


async def ask_gemini(message: str, context: dict, history: list | None = None, language: str = DEFAULT_LANGUAGE):
    if not settings.GEMINI_API_KEY:
        return None

    payload = {
        "system_instruction": {"parts": [{"text": build_system_prompt(language)}]},
        "contents": [{"parts": [{"text": build_user_prompt(message, context, history)}]}],
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


async def ask_llm(message: str, context: dict, history: list | None = None, language: str = DEFAULT_LANGUAGE):
    return await ask_groq(message, context, history, language) or await ask_gemini(
        message, context, history, language
    )


async def build_reply(
    message: str,
    fallback: str,
    context: dict,
    history: list | None = None,
    language: str = DEFAULT_LANGUAGE,
):
    generated = await ask_llm(message, {**context, "черновик_ответа": fallback}, history, language)
    return generated or fallback


def describe_doctors(doctors: list):
    return ", ".join(f"{doctor['full_name']} (#{doctor['doctor_id']})" for doctor in doctors)


def describe_slots(slots: list):
    return ", ".join(f"{slot['date']} {slot['time'][:5]}" for slot in slots[:10])


def slot_hour(slot: dict):
    return int(slot["time"][:2])


def sort_slots_by_preference(slots: list, preferences: dict):
    if not preferences:
        return slots

    marked = [
        {**slot, "preferred": preferences.get(slot_hour(slot), 0) > 0} for slot in slots
    ]

    return sorted(marked, key=lambda slot: -preferences.get(slot_hour(slot), 0))


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


async def log_call(current_patient, tool_name: str, params: dict, result: dict, db: AsyncSession, severity: int = 0):
    await crud_ai_log.log_tool_call(current_patient.user_id, tool_name, params, result, db, severity)


async def suggest_checkup(current_patient, db: AsyncSession, language: str = DEFAULT_LANGUAGE):
    overdue = await crud_appointment.get_overdue_checkup(current_patient.id, db)

    if overdue is None:
        return None

    months = overdue["days_since_visit"] // 30

    return {
        "doctor_id": overdue["doctor_id"],
        "doctor_name": overdue["doctor_name"],
        "specialization": overdue["specialization"],
        "last_visit": overdue["last_visit"],
        "reply": translate(
            "checkup_reminder",
            language,
            doctor=overdue["doctor_name"],
            specialization=overdue["specialization"],
            months=months,
        ),
    }


async def resolve_conversation(data: AskIn, current_patient, db: AsyncSession):
    if data.conversation_id:
        conversation = await crud_conversation.get_conversation(data.conversation_id, db)

        if conversation is not None and conversation.patient_id == current_patient.id:
            return conversation

    return await crud_conversation.get_or_create_active_conversation(current_patient.id, db)


def pick_flow(data: AskIn):
    flows = {
        "cancel": cancel_flow,
        "reschedule": reschedule_flow,
        "my_appointments": my_appointments_flow,
        "doctor_schedule": doctor_schedule_flow,
    }

    if data.intent in flows:
        return flows[data.intent]

    if data.confirm:
        return confirm_booking

    if data.doctor_id:
        return show_slots

    return suggest_doctors


async def remember(
    conversation, message: str, result: dict, severity: int, language: str, db: AsyncSession
):
    result["conversation_id"] = conversation.id
    result["severity"] = severity
    result["language"] = language

    await crud_conversation.add_message(conversation.id, "user", message, db)
    await crud_conversation.add_message(conversation.id, "assistant", result.get("reply", ""), db)
    return result


async def ask(data: AskIn, current_patient, db: AsyncSession):
    conversation = await resolve_conversation(data, current_patient, db)
    history = await crud_conversation.get_conversation_history(conversation.id, limit=10, db=db)
    severity = data.severity or assess_symptom_severity(data.message)
    language = pick_language(data.language, data.message)

    if is_emergency(data.message):
        message = EMERGENCY_MESSAGES[language]
        await log_call(
            current_patient,
            "emergency_guard",
            {"message": data.message},
            tool_error("EMERGENCY", message),
            db,
            SEVERITY_CRITICAL,
        )
        emergency = {"action": "emergency", "reply": message}
        return await remember(
            conversation, data.message, emergency, SEVERITY_CRITICAL, language, db
        )

    flow = pick_flow(data)
    result = await flow(data, current_patient, db, history, severity, language)

    if severity == SEVERITY_HIGH:
        result["reply"] = f"{HIGH_SEVERITY_NOTES[language]} {result['reply']}"

    return await remember(conversation, data.message, result, severity, language, db)


def tool_failure(result: dict):
    return {
        "action": "error",
        "error_code": result["error"]["code"],
        "reply": result["error"]["message"],
    }


async def cancel_flow(
    data: AskIn,
    current_patient,
    db: AsyncSession,
    history: list = None,
    severity: int = 0,
    language: str = DEFAULT_LANGUAGE,
):
    if not data.appointment_id:
        return {"action": "clarify", "reply": translate("clarify_cancel", language)}

    result = await cancel_appointment(db, current_patient, data.appointment_id)
    await log_call(
        current_patient, "cancel_appointment", {"appointment_id": data.appointment_id}, result, db, severity
    )

    if not result["ok"]:
        return tool_failure(result)

    fallback = translate("cancelled", language, appointment_id=data.appointment_id)

    return {
        "action": "cancelled",
        "appointment": result["data"],
        "reply": await build_reply(
            data.message, fallback, {"отмена": result["data"]}, history, language
        ),
    }


async def reschedule_flow(
    data: AskIn,
    current_patient,
    db: AsyncSession,
    history: list = None,
    severity: int = 0,
    language: str = DEFAULT_LANGUAGE,
):
    if not data.appointment_id or not data.day or not data.slot_time:
        return {"action": "clarify", "reply": translate("clarify_reschedule", language)}

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
        severity,
    )

    if not result["ok"]:
        return tool_failure(result)

    appointment = result["data"]
    fallback = translate(
        "rescheduled",
        language,
        appointment_id=appointment["appointment_id"],
        date=appointment["date"],
        time=appointment["time"][:5],
    )

    return {
        "action": "rescheduled",
        "appointment": appointment,
        "reply": await build_reply(
            data.message, fallback, {"перенос": appointment}, history, language
        ),
    }


async def my_appointments_flow(
    data: AskIn,
    current_patient,
    db: AsyncSession,
    history: list = None,
    severity: int = 0,
    language: str = DEFAULT_LANGUAGE,
):
    result = await get_patient_appointments(db, current_patient, current_patient.id)
    await log_call(
        current_patient,
        "get_patient_appointments",
        {"patient_id": current_patient.id},
        result,
        db,
        severity,
    )

    if not result["ok"]:
        return tool_failure(result)

    appointments = result["data"]
    fallback = (
        translate("appointments", language, appointments=describe_appointments(appointments))
        if appointments
        else translate("no_appointments", language)
    )

    return {
        "action": "my_appointments",
        "appointments": appointments,
        "reply": await build_reply(
            data.message, fallback, {"записи": appointments[:10]}, history, language
        ),
    }


async def doctor_schedule_flow(
    data: AskIn,
    current_patient,
    db: AsyncSession,
    history: list = None,
    severity: int = 0,
    language: str = DEFAULT_LANGUAGE,
):
    if not data.doctor_id:
        return {"action": "clarify", "reply": translate("clarify_schedule", language)}

    result = await get_doctor_schedule(db, data.doctor_id)
    await log_call(
        current_patient, "get_doctor_schedule", {"doctor_id": data.doctor_id}, result, db, severity
    )

    if not result["ok"]:
        return tool_failure(result)

    schedule = result["data"]
    fallback = translate("schedule", language, schedule=describe_schedule(schedule))

    return {
        "action": "doctor_schedule",
        "schedule": schedule,
        "reply": await build_reply(
            data.message, fallback, {"расписание": schedule}, history, language
        ),
    }


async def confirm_booking(
    data: AskIn,
    current_patient,
    db: AsyncSession,
    history: list = None,
    severity: int = 0,
    language: str = DEFAULT_LANGUAGE,
):
    if not data.doctor_id or not data.day or not data.slot_time:
        return {"action": "clarify", "reply": translate("clarify_booking", language)}

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
        severity,
    )

    if not result["ok"]:
        return {
            "action": "error",
            "error_code": result["error"]["code"],
            "reply": result["error"]["message"],
        }

    appointment = result["data"]
    fallback = translate(
        "booked",
        language,
        doctor=appointment["doctor_name"],
        specialization=appointment["specialization"],
        department=appointment["department"],
        date=appointment["date"],
        time=appointment["time"][:5],
        appointment_id=appointment["appointment_id"],
    )

    return {
        "action": "booked",
        "appointment": appointment,
        "reply": await build_reply(
            data.message, fallback, {"запись": appointment}, history, language
        ),
    }


async def show_slots(
    data: AskIn,
    current_patient,
    db: AsyncSession,
    history: list = None,
    severity: int = 0,
    language: str = DEFAULT_LANGUAGE,
):
    result = await get_available_time(db, data.doctor_id, data.day)
    await log_call(
        current_patient,
        "get_available_time",
        {"doctor_id": data.doctor_id, "date": str(data.day) if data.day else None},
        result,
        db,
        severity,
    )

    if not result["ok"]:
        return {
            "action": "error",
            "error_code": result["error"]["code"],
            "reply": result["error"]["message"],
        }

    preferences = await crud_appointment.get_hour_preferences(current_patient.id, db)
    slots = sort_slots_by_preference(result["data"], preferences)
    fallback = translate("slots_found", language, slots=describe_slots(slots))

    return {
        "action": "slots",
        "slots": slots,
        "reply": await build_reply(
            data.message, fallback, {"свободные_слоты": slots[:10]}, history, language
        ),
    }


async def find_available_alternatives(db: AsyncSession, specialization: str):
    available = []

    for candidate in find_fallback_specialists(specialization):
        result = await find_doctors(db, candidate)

        if result["ok"] and result["data"]:
            available.append(candidate)

    return available


async def suggest_doctors(
    data: AskIn,
    current_patient,
    db: AsyncSession,
    history: list = None,
    severity: int = 0,
    language: str = DEFAULT_LANGUAGE,
):
    specializations = match_specializations(data.message, language)

    if not specializations and language != DEFAULT_LANGUAGE:
        specializations = match_specializations(data.message)

    if not specializations:
        return {"action": "clarify", "reply": translate("clarify_specialization", language)}

    if len(specializations) > 1:
        return {
            "action": "clarify",
            "reply": translate("clarify_choice", language) + ", ".join(specializations) + ".",
        }

    specialization = specializations[0]
    result = await find_doctors(db, specialization)
    await log_call(
        current_patient, "find_doctors", {"specialization": specialization}, result, db, severity
    )

    if not result["ok"]:
        if result["error"]["code"] == "DOCTORS_NOT_FOUND":
            alternatives = await find_available_alternatives(db, specialization)

            if alternatives:
                return {
                    "action": "clarify",
                    "specialization": specialization,
                    "alternatives": alternatives,
                    "reply": translate(
                        "no_specialist_alternatives",
                        language,
                        specialization=specialization,
                        alternatives=", ".join(alternatives),
                    ),
                }

        return {
            "action": "error",
            "specialization": specialization,
            "error_code": result["error"]["code"],
            "reply": result["error"]["message"],
        }

    doctors = result["data"]
    fallback = translate(
        "doctors_found",
        language,
        specialization=specialization,
        doctors=describe_doctors(doctors),
    )

    return {
        "action": "doctors",
        "specialization": specialization,
        "doctors": doctors,
        "reply": await build_reply(
            data.message,
            fallback,
            {"специализация": specialization, "врачи": doctors},
            history,
            language,
        ),
    }
