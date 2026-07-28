from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import metrics
from app.ai.assistant import ask_llm, extract_json
from app.ai.dates import human_date, parse_natural_date
from app.core.clock import clinic_today
from app.services import (
    crud_ai_metric,
    crud_appointment,
    crud_department,
    crud_doctor,
    crud_filial,
    crud_report,
    crud_schedule,
)

MIN_CONFIDENCE = 0.5

DOCTOR_INTENTS = ("today", "day", "free", "load", "absences")
ADMIN_INTENTS = ("busiest", "summary", "ai_spend", "no_shows", "staff")

# Ключевые слова — запасной разбор на случай, когда модель молчит или не уверена.
# Без него любая осечка провайдера превращала ассистента сотрудника в одну и ту же
# фразу «не понял вопрос» на любой вопрос, включая готовые подсказки под полем ввода.
DOCTOR_KEYWORDS = {
    "free": ["свободн", "окн", "холи", "озод", "free", "slot", "availab"],
    "absences": ["отпуск", "больничн", "отсутств", "рухсат", "касал", "leave", "vacation", "sick"],
    "load": ["загруз", "сколько приём", "сколько принял", "статистик", "за месяц", "за недел",
             "сарбор", "load", "workload", "how many"],
    "today": ["сегодня", "имрӯз", "today"],
    "day": ["кто записан", "кто у меня", "запис", "приём", "прием", "навбат", "қабул",
            "booked", "appointment", "schedule"],
}

ADMIN_KEYWORDS = {
    "ai_spend": ["ии", "ai", "модел", "потрач", "расход", "стоим", "хароҷот", "spend", "cost", "token"],
    "no_shows": ["неяв", "не пришл", "не пришел", "наомад", "no show", "no_show", "missed"],
    "busiest": ["загружен", "больше всех", "самый", "топ", "сарбор", "busiest", "top", "most"],
    "staff": ["сколько врач", "состав", "отделен", "филиал", "штат", "шӯъба", "how many doctor",
              "staff", "branch", "department"],
    "summary": ["сводк", "итог", "обзор", "общая", "ҷамъбаст", "summary", "overview", "total"],
}

INTENT_PROMPT = (
    "Ты распознаёшь запрос сотрудника клиники и возвращаешь ТОЛЬКО JSON без пояснений "
    'и без markdown в формате: {{"intent": "<одно из: {intents}>", '
    '"confidence": <0..1>, "days": <целое число дней периода, если названо>, '
    '"date": "<YYYY-MM-DD, если названа конкретная дата>"}}. '
    "Если подходящего значения нет или ты не уверен — ставь confidence ниже 0.5. "
    "Значения intent: {hints}"
)

DOCTOR_HINTS = (
    "today — кто записан сегодня; "
    "day — кто записан на конкретный день; "
    "free — где остались свободные окна; "
    "load — сколько приёмов за период и как они закончились; "
    "absences — когда отпуска и больничные."
)

ADMIN_HINTS = (
    "busiest — самые загруженные врачи; "
    "summary — общая сводка по клинике за период; "
    "ai_spend — расходы на ИИ и количество запросов; "
    "no_shows — неявки пациентов; "
    "staff — сколько врачей, отделений и филиалов."
)

REPLY_PROMPT = (
    "Ты ассистент сотрудника клиники. Тебе дают готовые цифры из базы — перескажи их "
    "сотруднику коротко и по-деловому, на его языке. "
    "НЕ придумывай числа, которых нет в данных, и не меняй те, что есть. "
    "Данные полные и относятся именно к той дате и тому периоду, что в них указаны. "
    "НЕ пиши, что каких-то сведений нет в системе, и не рассуждай, за какие даты они есть: "
    "если дата в данных отличается от даты в вопросе, просто ответь про дату из данных. "
    "Диагнозы не ставь, лечение не назначай, медицинских советов не давай — "
    "это запрещено. Ответ — одно-два предложения, без markdown и без списков. "
    "Не пересказывай одно и то же разными словами."
)


def parse(raw: str | None, allowed):
    parsed = extract_json(raw) if raw else None

    if not isinstance(parsed, dict):
        return None

    if parsed.get("intent") not in allowed:
        return None

    try:
        confidence = float(parsed.get("confidence", 0))
    except (ValueError, TypeError):
        return None

    if confidence < MIN_CONFIDENCE:
        return None

    return {
        "intent": parsed["intent"],
        "days": parsed.get("days") if isinstance(parsed.get("days"), int) else None,
        "date": parsed.get("date") if isinstance(parsed.get("date"), str) else None,
    }


def match_intent(message: str, keywords: dict):
    lowered = message.lower()

    for intent, words in keywords.items():
        if any(word in lowered for word in words):
            return {"intent": intent, "days": None, "date": None}

    return None


async def classify(message: str, allowed, hints: str, keywords: dict):
    prompt = INTENT_PROMPT.format(intents=" | ".join(allowed), hints=hints)
    detected = parse(await ask_llm(message, {}, None, system_prompt=prompt), allowed)

    return detected or match_intent(message, keywords)


def parse_date(value: str | None):
    if not value:
        return None

    try:
        parsed = date.fromisoformat(value)
    except (ValueError, TypeError):
        return None

    today = clinic_today()

    if abs((parsed - today).days) > 366:
        return None

    return parsed


# модель регулярно отдаёт intent, но не дату: «на 30 число» она в YYYY-MM-DD не переводит.
# Без разбора самого текста вопрос про 30-е тихо отвечал про сегодня, и модель потом
# сама сочиняла объяснение, почему данных за 30-е «нет»
def resolve_date(intent: dict, message: str, forward: bool = True):
    return parse_date(intent.get("date")) or parse_natural_date(message, forward=forward)


def period(intent: dict | None, default_days: int = 30):
    days = (intent or {}).get("days") or default_days
    days = max(1, min(int(days), 366))
    today = clinic_today()
    return today - timedelta(days=days - 1), today, days


async def phrase(message: str, fallback: str, facts: dict, language: str):
    generated = await ask_llm(
        message,
        {**facts, "черновик_ответа": fallback},
        None,
        language,
        system_prompt=REPLY_PROMPT,
    )
    return generated or fallback


def describe_appointments(rows):
    return [{"время": str(row["time"])[:5], "статус": row["status"]} for row in rows[:20]]


async def build_doctor_answer(message: str, doctor, language: str, db: AsyncSession):
    intent = await classify(message, DOCTOR_INTENTS, DOCTOR_HINTS, DOCTOR_KEYWORDS)

    if intent is None:
        return {
            "action": "clarify",
            "reply": (
                "Не понял вопрос. Могу показать, кто записан сегодня или на конкретный "
                "день, где остались свободные окна, вашу загрузку за период и отпуска."
            ),
            "data": {},
        }

    kind = intent["intent"]

    if kind in ("today", "day"):
        day = resolve_date(intent, message) or clinic_today()
        rows = await crud_appointment.get_doctor_appointments(doctor.id, db, day=day)
        active = [row for row in rows if row["status"] == "booked"]
        facts = {
            "дата": human_date(day, language),
            "всего_записей": len(rows),
            "ожидают_приёма": len(active),
            "записи": describe_appointments(rows),
        }
        fallback = (
            f"На {human_date(day, language)} записей: {len(rows)}, ждут приёма: {len(active)}."
            if rows
            else f"На {human_date(day, language)} записей нет."
        )
        return {
            "action": "day",
            "reply": await phrase(message, fallback, facts, language),
            "data": {**facts, "приёмы": rows},
        }

    if kind == "free":
        day = resolve_date(intent, message) or clinic_today()
        plan = await crud_schedule.get_day_plan(doctor.id, day, db)
        facts = {
            "дата": human_date(day, language),
            "статус_дня": plan["status"],
            "свободно_слотов": plan.get("slots_free", 0),
            "занято_слотов": plan.get("slots_taken", 0),
        }

        if plan["status"] == "absent":
            fallback = f"{human_date(day, language)} у вас отпуск, приёма нет."
        elif plan["status"] == "off":
            fallback = f"{human_date(day, language)} — выходной, приёма нет."
        else:
            fallback = (
                f"На {human_date(day, language)} свободно слотов: {plan['slots_free']}, "
                f"занято: {plan['slots_taken']}."
            )

        return {"action": "free", "reply": await phrase(message, fallback, facts, language), "data": facts}

    if kind == "load":
        date_from, date_to, days = period(intent)
        rows = await crud_report.get_doctor_workload(db, date_from, date_to)
        mine = next((row for row in rows if row["doctor_id"] == doctor.id), None)
        counts = (
            {key: mine[key] for key in ("total", "completed", "cancelled", "no_show")}
            if mine
            else {}
        )
        facts = {
            "период_дней": days,
            "с": human_date(date_from, language),
            "по": human_date(date_to, language),
            **counts,
        }
        fallback = (
            f"За {days} дн. у вас {mine['total']} приёмов: состоялось {mine['completed']}, "
            f"отменено {mine['cancelled']}, не пришли {mine['no_show']}."
            if mine
            else f"За {days} дн. приёмов не было."
        )
        return {"action": "load", "reply": await phrase(message, fallback, facts, language), "data": facts}

    absences = await crud_schedule.get_absences(doctor.id, db)
    upcoming = [row for row in absences if row.date_to >= clinic_today()]
    facts = {
        "всего_отсутствий": len(absences),
        "предстоящих": [
            {
                "с": human_date(row.date_from, language),
                "по": human_date(row.date_to, language),
                "причина": row.reason,
            }
            for row in upcoming
        ],
    }
    fallback = (
        f"Впереди периодов отсутствия: {len(upcoming)}, ближайший с {human_date(upcoming[0].date_from, language)}."
        if upcoming
        else "Предстоящих отпусков и больничных не запланировано."
    )
    return {"action": "absences", "reply": await phrase(message, fallback, facts, language), "data": facts}


async def build_admin_answer(message: str, language: str, db: AsyncSession):
    intent = await classify(message, ADMIN_INTENTS, ADMIN_HINTS, ADMIN_KEYWORDS)

    if intent is None:
        return {
            "action": "clarify",
            "reply": (
                "Не понял вопрос. Могу показать самых загруженных врачей, сводку по клинике "
                "за период, неявки пациентов, расходы на ИИ и состав клиники."
            ),
            "data": {},
        }

    kind = intent["intent"]
    date_from, date_to, days = period(intent)

    if kind == "busiest":
        rows = await crud_report.get_doctor_workload(db, date_from, date_to)
        top = sorted(rows, key=lambda row: row["total"], reverse=True)[:5]
        facts = {
            "период_дней": days,
            "врачи": [
                {"имя": row["full_name"], "специализация": row["specialization"], "приёмов": row["total"]}
                for row in top
                if row["total"] > 0
            ],
        }
        fallback = (
            f"За {days} дн. больше всех принимал {top[0]['full_name']} — {top[0]['total']} приёмов."
            if top and top[0]["total"] > 0
            else f"За {days} дн. приёмов не было."
        )
        return {"action": "busiest", "reply": await phrase(message, fallback, facts, language), "data": facts}

    if kind == "summary":
        summary = await crud_report.get_appointments_summary(db, date_from, date_to)
        facts = {"период_дней": days, **{key: summary[key] for key in
                 ("total", "booked", "completed", "cancelled", "no_show", "doctors", "patients")}}
        fallback = (
            f"За {days} дн. {summary['total']} записей: состоялось {summary['completed']}, "
            f"отменено {summary['cancelled']}, неявок {summary['no_show']}. "
            f"Принимали {summary['doctors']} врачей, приходили {summary['patients']} пациентов."
        )
        return {"action": "summary", "reply": await phrase(message, fallback, facts, language), "data": facts}

    if kind == "no_shows":
        rows = await crud_report.get_doctor_workload(db, date_from, date_to)
        worst = sorted(rows, key=lambda row: row["no_show"], reverse=True)[:5]
        total = sum(row["no_show"] for row in rows)
        facts = {
            "период_дней": days,
            "всего_неявок": total,
            "врачи": [
                {"имя": row["full_name"], "неявок": row["no_show"]}
                for row in worst
                if row["no_show"] > 0
            ],
        }
        fallback = (
            f"За {days} дн. пациенты не пришли {total} раз."
            if total
            else f"За {days} дн. неявок не было."
        )
        return {"action": "no_shows", "reply": await phrase(message, fallback, facts, language), "data": facts}

    if kind == "ai_spend":
        costs = await crud_ai_metric.get_costs(db, date_from, date_to)
        calls = sum(row["calls"] for row in costs["by_model"])
        facts = {
            "период_дней": days,
            "запросов": calls,
            "потрачено_usd": str(costs["total_usd"]),
            "бюджет_usd": str(costs["budget_usd"]),
            "цены_заданы": costs["prices_configured"],
        }
        fallback = (
            f"За {days} дн. {calls} запросов к модели, потрачено ${costs['total_usd']}."
            if costs["prices_configured"]
            else f"За {days} дн. {calls} запросов к модели. Стоимость не посчитать: цены моделей не заданы в настройках."
        )
        return {"action": "ai_spend", "reply": await phrase(message, fallback, facts, language), "data": facts}

    doctors = await crud_doctor.search_doctors(db)
    departments = await crud_department.get_departments(db)
    filials = await crud_filial.get_filials(db)
    facts = {
        "врачей": len(doctors),
        "отделений": len(departments),
        "филиалов": len(filials),
    }
    fallback = (
        f"В клинике {len(doctors)} врачей, {len(departments)} отделений "
        f"и {len(filials)} филиалов."
    )
    return {"action": "staff", "reply": await phrase(message, fallback, facts, language), "data": facts}


# Вызовы модели из кабинета врача и админа раньше не считались вообще: буфер метрик
# заводил только пациентский поток, поэтому `record_call` видел None и молча всё выбрасывал.
# В админской аналитике не было видно ни одного запроса от сотрудников, хотя платим мы за них
# так же. Одна попытка сходить в модель — одна строка в `ai_llm_calls`, как и у пациента
async def with_metrics(user_id: int, db: AsyncSession, build):
    metrics.start_collecting()
    result = await build()
    await crud_ai_metric.save_calls(user_id, metrics.collected_calls(), db)
    return result


async def answer_doctor(message: str, doctor, language: str, db: AsyncSession):
    return await with_metrics(
        doctor.user_id, db, lambda: build_doctor_answer(message, doctor, language, db)
    )


async def answer_admin(message: str, user_id: int, language: str, db: AsyncSession):
    return await with_metrics(
        user_id, db, lambda: build_admin_answer(message, language, db)
    )
