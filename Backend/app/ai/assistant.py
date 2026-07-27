import json
from datetime import date, datetime
from time import perf_counter

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import metrics

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
from app.services import (
    crud_ai_log,
    crud_ai_metric,
    crud_appointment,
    crud_conversation,
    crud_doctor,
)

SYSTEM_PROMPT_TEMPLATE = (
    "Ты — ассистент регистратуры клиники Ometus. Твоя единственная задача — помочь пациенту "
    "найти врача нужной специализации и записаться на приём. Категорически запрещено ставить "
    "диагнозы, оценивать тяжесть состояния и давать медицинские рекомендации. Сопоставление "
    "симптома и специализации — техническое, а не медицинское заключение. Отвечай на {language} "
    "языке, коротко и по делу, опираясь только на переданные данные системы. Ничего не "
    "выдумывай: если данных нет, так и скажи. "
    "Пиши тепло и коротко, 1–2 предложения, как живой администратор клиники. "
    "Списки врачей, времени и дат НЕ перечисляй: их показывает интерфейс карточками. "
    "Если знаешь имя пациента, обратись по нему. "
    "Не повторяй одну и ту же фразу подряд — смотри историю диалога. "
    "Не используй markdown, звёздочки и эмодзи."
)

SYSTEM_PROMPT = SYSTEM_PROMPT_TEMPLATE.format(language="русском")

EMR_CONTEXT_KEY = "история_болезни"

EMR_PROMPT_NOTE = (
    " В данных системы может быть история болезни пациента. Она дана исключительно для "
    "выбора подходящего специалиста. Категорически запрещено комментировать заболевания, "
    "аллергии и лекарства, оценивать их и давать любые советы по лечению."
)


def build_system_prompt(language: str, with_emr: bool = False):
    prompt = SYSTEM_PROMPT_TEMPLATE.format(language=translate("answer_language", language))
    return prompt + EMR_PROMPT_NOTE if with_emr else prompt


def build_user_prompt(message: str, context: dict, history: list | None = None):
    prompt = f"Запрос пациента: {message}\n\n"

    if history:
        prompt += "История диалога:\n"
        for msg in history:
            prompt += f"- {msg.role}: {msg.content}\n"
        prompt += "\n"

    prompt += f"Данные системы: {json.dumps(context, ensure_ascii=False)}"
    return prompt


def elapsed_ms(started: float):
    return int((perf_counter() - started) * 1000)


def read_gemini_text(data: dict):
    parts = data["candidates"][0]["content"]["parts"]
    return "\n".join(part["text"] for part in parts if part.get("text")).strip()


async def ask_groq(
    message: str,
    context: dict,
    history: list | None = None,
    language: str = DEFAULT_LANGUAGE,
    system_prompt: str | None = None,
):
    if not settings.GROQ_API_KEY:
        return None

    for model in settings.GROQ_MODELS:
        payload = {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    or build_system_prompt(language, EMR_CONTEXT_KEY in context),
                },
                {"role": "user", "content": build_user_prompt(message, context, history)},
            ],
        }
        started = perf_counter()

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    settings.GROQ_URL,
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
                reply = body["choices"][0]["message"]["content"].strip()
                usage = body.get("usage") or {}

                metrics.record_call(
                    "groq",
                    model,
                    bool(reply),
                    elapsed_ms(started),
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    None if reply else "empty reply",
                )

                if reply:
                    return reply
        except Exception as error:
            metrics.record_call("groq", model, False, elapsed_ms(started), error=str(error)[:200])
            continue

    return None


async def ask_gemini(
    message: str,
    context: dict,
    history: list | None = None,
    language: str = DEFAULT_LANGUAGE,
    system_prompt: str | None = None,
):
    if not settings.GEMINI_API_KEY:
        return None

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": system_prompt
                    or build_system_prompt(language, EMR_CONTEXT_KEY in context)
                }
            ]
        },
        "contents": [{"parts": [{"text": build_user_prompt(message, context, history)}]}],
        "generationConfig": {"temperature": 0.2},
    }

    for model in settings.GEMINI_MODELS:
        started = perf_counter()

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{settings.GEMINI_URL}/{model}:generateContent",
                    headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
                reply = read_gemini_text(body)
                usage = body.get("usageMetadata") or {}

                metrics.record_call(
                    "gemini",
                    model,
                    bool(reply),
                    elapsed_ms(started),
                    usage.get("promptTokenCount"),
                    usage.get("candidatesTokenCount"),
                    None if reply else "empty reply",
                )

                if reply:
                    return reply
        except Exception as error:
            metrics.record_call("gemini", model, False, elapsed_ms(started), error=str(error)[:200])
            continue

    return None


async def ask_llm(
    message: str,
    context: dict,
    history: list | None = None,
    language: str = DEFAULT_LANGUAGE,
    system_prompt: str | None = None,
):
    return await ask_groq(
        message, context, history, language, system_prompt
    ) or await ask_gemini(message, context, history, language, system_prompt)


def first_name_of(current_patient):
    full_name = (current_patient.full_name or "").strip()
    return full_name.split()[0] if full_name else None


async def build_reply(
    message: str,
    fallback: str,
    context: dict,
    history: list | None = None,
    language: str = DEFAULT_LANGUAGE,
    current_patient=None,
):
    context = {**context, "черновик_ответа": fallback}
    name = first_name_of(current_patient) if current_patient else None

    if name:
        context["имя_пациента"] = name

    generated = await ask_llm(message, context, history, language)
    return generated or fallback


def state_change_reply(fallback: str):
    return fallback


CONTEXT_DOCTORS_LIMIT = 5
CONTEXT_SLOTS_LIMIT = 6


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


KNOWN_INTENTS = ["cancel", "reschedule", "my_appointments", "doctor_schedule", "find_doctor"]

MIN_INTENT_CONFIDENCE = 0.6

INTENT_SYSTEM_PROMPT = (
    "Ты — классификатор намерений пациента в регистратуре клиники. "
    "Верни ТОЛЬКО JSON без пояснений и без markdown в формате: "
    '{"primary": "<intent>", "parameters": {"appointment_id": null, "doctor_id": null, '
    '"date": null, "time": null}, "confidence": <0..1>}. '
    f"Допустимые intent: {', '.join(KNOWN_INTENTS)}. "
    "cancel — отменить запись, reschedule — перенести, my_appointments — показать свои записи, "
    "doctor_schedule — расписание врача, find_doctor — найти врача или время приёма. "
    "Заполняй parameters только теми значениями, которые пациент назвал явно. "
    "Если намерение неясно, ставь низкий confidence."
)


def extract_json(raw: str):
    cleaned = raw.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1] if "```" in cleaned[3:] else cleaned[3:]
        cleaned = cleaned.removeprefix("json").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end < start:
        return None

    try:
        return json.loads(cleaned[start : end + 1])
    except (ValueError, TypeError):
        return None


def parse_intent(raw: str | None):
    if not raw:
        return None

    parsed = extract_json(raw)

    if not isinstance(parsed, dict):
        return None

    primary = parsed.get("primary")

    if primary not in KNOWN_INTENTS:
        return None

    try:
        confidence = float(parsed.get("confidence", 0))
    except (ValueError, TypeError):
        return None

    if confidence < MIN_INTENT_CONFIDENCE:
        return None

    parameters = parsed.get("parameters")

    return {
        "primary": primary,
        "confidence": confidence,
        "parameters": parameters if isinstance(parameters, dict) else {},
    }


async def classify_intent(message: str, history: list | None = None):
    raw = await ask_llm(message, {}, history, system_prompt=INTENT_SYSTEM_PROMPT)
    return parse_intent(raw)


MIN_SPECIALTY_CONFIDENCE = 0.5

SPECIALTY_SYSTEM_PROMPT = (
    "Ты сопоставляешь жалобу пациента со специализацией врача из списка. "
    "Это техническое сопоставление, а не диагноз: болезнь не называй, лечение не предлагай. "
    "Верни ТОЛЬКО JSON без пояснений и без markdown в формате: "
    '{"specialization": "<название>", "confidence": <0..1>}. '
    "Бери значение строго из списка допустимых специализаций. "
    "Если подходящей в списке нет или ты не уверен — ставь confidence ниже 0.5."
)


def parse_specialty(raw: str | None, known: list):
    if not raw:
        return None

    parsed = extract_json(raw)

    if not isinstance(parsed, dict):
        return None

    name = parsed.get("specialization")

    if not isinstance(name, str):
        return None

    name = name.strip().lower()

    if name not in known:
        return None

    try:
        confidence = float(parsed.get("confidence", 0))
    except (ValueError, TypeError):
        return None

    if confidence < MIN_SPECIALTY_CONFIDENCE:
        return None

    return name


async def classify_specialization(message: str, known: list, history: list | None = None):
    if not known:
        return None

    prompt = f"{SPECIALTY_SYSTEM_PROMPT} Допустимые специализации: {', '.join(known)}."
    raw = await ask_llm(message, {}, history, system_prompt=prompt)
    return parse_specialty(raw, known)


def serialise_result(result: dict):
    return json.loads(json.dumps(result, ensure_ascii=False, default=str))


async def run_ask_task(task_id: str, data: AskIn, patient_id: int):
    from app.db.database import get_session_factory
    from app.services import crud_ai_task, crud_patient

    factory = get_session_factory()

    async with factory() as db:
        try:
            patient = await crud_patient.get_by_id(patient_id, db)

            if patient is None:
                await crud_ai_task.fail_task(task_id, "Пациент не найден", db)
                return

            result = await ask(data, patient, db)
            await crud_ai_task.finish_task(task_id, serialise_result(result), db)
        except Exception as error:
            await crud_ai_task.fail_task(task_id, str(error), db)


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


def read_int(parameters: dict, key: str):
    value = parameters.get(key)

    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def read_date(parameters: dict):
    value = parameters.get("date")

    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def read_time(parameters: dict):
    value = parameters.get("time")

    if not isinstance(value, str):
        return None

    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue

    return None


def apply_intent(data: AskIn, detected: dict):
    parameters = detected["parameters"]

    if detected["primary"] != "find_doctor":
        data.intent = detected["primary"]

    data.appointment_id = data.appointment_id or read_int(parameters, "appointment_id")
    data.doctor_id = data.doctor_id or read_int(parameters, "doctor_id")
    data.day = data.day or read_date(parameters)
    data.slot_time = data.slot_time or read_time(parameters)
    return data


def needs_classification(data: AskIn, language: str):
    if data.intent or data.confirm:
        return False

    return not match_specializations(data.message, language)


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


PAYLOAD_FIELDS = [
    "doctors",
    "slots",
    "appointment",
    "specialization",
    "alternatives",
    "suggestions",
    "error_code",
    "doctor_id",
    "doctor_name",
]

PAYLOAD_SLOTS_LIMIT = 20


def render_payload(result: dict):
    payload = {field: result[field] for field in PAYLOAD_FIELDS if result.get(field)}

    if len(payload.get("slots", [])) > PAYLOAD_SLOTS_LIMIT:
        payload["slots"] = payload["slots"][:PAYLOAD_SLOTS_LIMIT]

    return payload or None


async def remember(
    conversation,
    message: str,
    result: dict,
    severity: int,
    language: str,
    current_patient,
    db: AsyncSession,
):
    result["conversation_id"] = conversation.id
    result["severity"] = severity
    result["language"] = language

    await crud_conversation.add_message(conversation.id, "user", message, db)
    answer = await crud_conversation.add_message(
        conversation.id,
        "assistant",
        result.get("reply", ""),
        db,
        action=result.get("action"),
        payload=render_payload(result),
    )
    result["message_id"] = answer.id
    await crud_ai_metric.save_calls(current_patient.user_id, metrics.collected_calls(), db)
    return result


async def ask(data: AskIn, current_patient, db: AsyncSession):
    metrics.start_collecting()
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
            conversation, data.message, emergency, SEVERITY_CRITICAL, language, current_patient, db
        )

    detected = (
        await classify_intent(data.message, history)
        if needs_classification(data, language)
        else None
    )

    if detected:
        data = apply_intent(data, detected)

    flow = pick_flow(data)
    result = await flow(data, current_patient, db, history, severity, language)

    if detected:
        result["detected_intent"] = detected["primary"]
        result["intent_confidence"] = detected["confidence"]

    if severity == SEVERITY_HIGH:
        result["reply"] = f"{HIGH_SEVERITY_NOTES[language]} {result['reply']}"

    return await remember(
        conversation, data.message, result, severity, language, current_patient, db
    )


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
        "reply": state_change_reply(fallback),
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
        "reply": state_change_reply(fallback),
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
            data.message,
            fallback,
            {"записи": appointments[:10]},
            history,
            language,
            current_patient,
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
            data.message,
            fallback,
            {"расписание": schedule},
            history,
            language,
            current_patient,
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
        "reply": state_change_reply(fallback),
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
    note = ""

    if not result["ok"] and data.day and result["error"]["code"] == "NO_SLOTS":
        nearest = await get_available_time(db, data.doctor_id)

        if nearest["ok"]:
            result = nearest
            note = translate("no_slots_today", language, date=data.day) + " "

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
    doctor = await crud_doctor.get_by_id(data.doctor_id, db)
    fallback = note + translate(
        "slots_found",
        language,
        doctor=doctor.full_name if doctor else "",
        date=slots[0]["date"],
    )

    return {
        "action": "slots",
        "slots": slots,
        "doctor_id": data.doctor_id,
        "doctor_name": doctor.full_name if doctor else None,
        "reply": await build_reply(
            data.message,
            fallback,
            {"свободные_слоты": slots[:CONTEXT_SLOTS_LIMIT]},
            history,
            language,
            current_patient,
        ),
    }


async def load_emr_context(current_patient, db: AsyncSession):
    if not current_patient.ai_consent:
        return None

    from app.services import crud_medical_record

    records = await crud_medical_record.get_records(current_patient.id, db)

    if not records:
        return None

    grouped = {}

    for record in records:
        entry = f"{record.name} ({record.note})" if record.note else record.name
        grouped.setdefault(record.kind, []).append(entry)

    return grouped


async def find_available_alternatives(db: AsyncSession, specialization: str):
    available = []

    for candidate in find_fallback_specialists(specialization):
        result = await find_doctors(db, candidate)

        if result["ok"] and result["data"]:
            available.append(candidate)

    return available


async def specialties_with_doctors(db: AsyncSession, specializations: list, city: str | None):
    found = {}

    for name in specializations:
        result = await find_doctors(db, name, city=city)

        if result["ok"] and result["data"]:
            found[name] = result["data"]

    return found


def merge_doctors(found: dict):
    merged = {}

    for doctors in found.values():
        for doctor in doctors:
            merged.setdefault(doctor["doctor_id"], doctor)

    return list(merged.values())


async def collect_alternatives(db: AsyncSession, specializations: list):
    alternatives = []

    for name in specializations:
        for candidate in await find_available_alternatives(db, name):
            if candidate not in alternatives:
                alternatives.append(candidate)

    return alternatives


async def clarify_between_specialties(
    db: AsyncSession, specializations: list, found: dict, language: str
):
    if found:
        return {
            "action": "clarify",
            "suggestions": list(found),
            "doctors": merge_doctors(found),
            "reply": translate("clarify_choice", language) + ", ".join(found) + ".",
        }

    alternatives = await collect_alternatives(db, specializations)

    if alternatives:
        return {
            "action": "clarify",
            "specialization": specializations[0],
            "alternatives": alternatives,
            "reply": translate(
                "no_specialist_alternatives",
                language,
                specialization=", ".join(specializations),
                alternatives=", ".join(alternatives),
            ),
        }

    return {
        "action": "clarify",
        "suggestions": specializations,
        "reply": translate("clarify_choice", language) + ", ".join(specializations) + ".",
    }


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
        known = await crud_doctor.list_specializations(db)
        guessed = await classify_specialization(data.message, known, history)

        if guessed:
            specializations = [guessed]

    if not specializations:
        return {
            "action": "clarify",
            "suggestions": await crud_doctor.popular_specializations(db),
            "reply": translate("clarify_specialization", language),
        }

    if len(specializations) > 1:
        found = await specialties_with_doctors(db, specializations, data.city)

        if len(found) == 1:
            specializations = list(found)
        else:
            return await clarify_between_specialties(db, specializations, found, language)

    specialization = specializations[0]
    emr = await load_emr_context(current_patient, db)
    result = await find_doctors(db, specialization, city=data.city)
    await log_call(
        current_patient,
        "find_doctors",
        {"specialization": specialization, "city": data.city, "emr_used": bool(emr)},
        result,
        db,
        severity,
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
        "doctors_found", language, specialization=specialization, count=len(doctors)
    )

    if doctors[0].get("other_city"):
        fallback = f"{translate('other_city_note', language, city=data.city)} {fallback}"

    context = {"специализация": specialization, "врачи": doctors[:CONTEXT_DOCTORS_LIMIT]}

    if emr:
        context[EMR_CONTEXT_KEY] = emr

    return {
        "action": "doctors",
        "specialization": specialization,
        "doctors": doctors,
        "emr_used": bool(emr),
        "reply": await build_reply(
            data.message, fallback, context, history, language, current_patient
        ),
    }
