DEFAULT_LANGUAGE = "ru"
LANGUAGES = ["ru", "tg", "en"]

TAJIK_LETTERS = "ӣӯҳқғҷ"

TAJIK_MARKERS = [
    "ман ",
    "маро",
    "мехоҳам",
    "мехохам",
    "лозим",
    "дорам",
    "духтур",
    "табиб",
    "салом",
    "кай ",
    "чи хел",
    "кӯдак",
    "дард",
    "мекун",
    "мешав",
    "бемор",
    "касал",
    "навбат",
]


def detect_language(text: str):
    lowered = text.lower()

    if any(letter in lowered for letter in TAJIK_LETTERS):
        return "tg"

    if any(marker in lowered for marker in TAJIK_MARKERS):
        return "tg"

    if any("a" <= symbol <= "z" for symbol in lowered):
        return "en"

    return DEFAULT_LANGUAGE


def pick_language(explicit: str | None, text: str):
    if explicit in LANGUAGES:
        return explicit

    return detect_language(text)


REPLIES = {
    "ru": {
        "answer_language": "русском",
        "clarify_specialization": "Не понял, врач какой специализации нужен. Опишите, что беспокоит, "
        "или назовите специализацию — например, кардиолог.",
        "clarify_choice": "Уточните, пожалуйста, к какому специалисту записать: ",
        "clarify_cancel": "Уточните номер записи, которую нужно отменить.",
        "clarify_reschedule": "Чтобы перенести запись, нужны её номер, новая дата и время.",
        "clarify_booking": "Чтобы записать, нужны врач, дата и время. Уточните, пожалуйста.",
        "clarify_schedule": "Уточните, расписание какого врача показать.",
        "doctors_found": "По специализации «{specialization}» нашёл врачей: {count}. "
        "Выберите, кто удобнее, — покажу свободное время.",
        "no_specialist_alternatives": "Врача по специализации «{specialization}» в клинике нет. "
        "Могу предложить: {alternatives}. К кому записать?",
        "slots_found": "Вот свободное время у врача {doctor} на {date}. "
        "Выберите удобное, и я запишу.",
        "which_day": "На какой день записать к врачу {doctor}? Вот дни, когда он принимает.",
        "no_slots_today": "На {date} свободного времени нет, показываю ближайшие дни.",
        "booked": "Записал вас к врачу {doctor} ({specialization}), отделение {department}, "
        "{date} в {time}. Номер записи — {appointment_id}.",
        "cancelled": "Запись №{appointment_id} отменена.",
        "rescheduled": "Перенёс запись №{appointment_id} на {date} в {time}.",
        "appointments": "Ваши записи: {appointments}.",
        "no_appointments": "У вас пока нет записей.",
        "schedule": "Врач принимает: {schedule}.",
        "checkup_reminder": "Вы были у врача {doctor} ({specialization}) {months} мес. назад. "
        "Записаться на повторный приём?",
        "other_city_note": "В городе {city} такого специалиста нет, показываю врачей из других филиалов.",
    },
    "tg": {
        "answer_language": "тоҷикӣ",
        "clarify_specialization": "Нафаҳмидам, кадом мутахассис лозим аст. Шикоятатонро нависед "
        "ё номи мутахассисро гӯед — масалан, кардиолог.",
        "clarify_choice": "Лутфан аниқ кунед, ба кадом мутахассис навбат гирем: ",
        "clarify_cancel": "Рақами навбатеро, ки бекор кардан мехоҳед, гӯед.",
        "clarify_reschedule": "Барои интиқоли навбат рақам, санаи нав ва вақт лозим аст.",
        "clarify_booking": "Барои сабти ном духтур, сана ва вақт лозим аст. Лутфан аниқ кунед.",
        "clarify_schedule": "Аниқ кунед, ҷадвали кадом духтурро нишон диҳам.",
        "doctors_found": "Аз рӯи мутахассисии «{specialization}» духтурон ёфтам: {count}. "
        "Интихоб кунед, кадомаш қулай аст, — вақти холиро нишон медиҳам.",
        "no_specialist_alternatives": "Духтури «{specialization}» дар клиника нест. "
        "Пешниҳод карда метавонам: {alternatives}. Ба кадомаш навбат гирем?",
        "slots_found": "Вақти холии духтур {doctor} барои {date}. "
        "Вақти қулайро интихоб кунед, ман сабт мекунам.",
        "which_day": "Ба кадом рӯз ба духтур {doctor} навбат гирем? Инак рӯзҳои қабули ӯ.",
        "no_slots_today": "Барои {date} вақти холӣ нест, рӯзҳои наздиктаринро нишон медиҳам.",
        "booked": "Шуморо ба духтур {doctor} ({specialization}), шӯъбаи {department}, "
        "{date} соати {time} сабт кардам. Рақами навбат — {appointment_id}.",
        "cancelled": "Навбати №{appointment_id} бекор карда шуд.",
        "rescheduled": "Навбати №{appointment_id} ба {date} соати {time} гузаронида шуд.",
        "appointments": "Навбатҳои шумо: {appointments}.",
        "no_appointments": "Шумо ҳоло навбат надоред.",
        "schedule": "Духтур қабул мекунад: {schedule}.",
        "checkup_reminder": "Шумо {months} моҳ пеш дар назди духтур {doctor} ({specialization}) будед. "
        "Ба қабули такрорӣ навбат гирем?",
        "other_city_note": "Дар шаҳри {city} чунин мутахассис нест, духтурони филиалҳои дигарро нишон медиҳам.",
    },
    "en": {
        "answer_language": "English",
        "clarify_specialization": "I did not catch which specialist you need. Describe what bothers you "
        "or name the specialty — for example, cardiologist.",
        "clarify_choice": "Please clarify which specialist to book: ",
        "clarify_cancel": "Please tell me the number of the appointment to cancel.",
        "clarify_reschedule": "To reschedule I need the appointment number, a new date and time.",
        "clarify_booking": "To book I need the doctor, date and time. Please clarify.",
        "clarify_schedule": "Please tell me whose schedule to show.",
        "doctors_found": "Found doctors for «{specialization}»: {count}. "
        "Pick the one that suits you — I will show the available time.",
        "no_specialist_alternatives": "There is no «{specialization}» in the clinic. "
        "I can offer: {alternatives}. Who should I book?",
        "slots_found": "Here is the available time with {doctor} on {date}. "
        "Pick a slot and I will book it.",
        "which_day": "Which day should I book with {doctor}? Here are the days they see patients.",
        "no_slots_today": "There is no free time on {date}, showing the nearest days.",
        "booked": "Booked you with {doctor} ({specialization}), department {department}, "
        "on {date} at {time}. Appointment number — {appointment_id}.",
        "cancelled": "Appointment #{appointment_id} has been cancelled.",
        "rescheduled": "Appointment #{appointment_id} moved to {date} at {time}.",
        "appointments": "Your appointments: {appointments}.",
        "no_appointments": "You have no appointments yet.",
        "schedule": "The doctor sees patients: {schedule}.",
        "checkup_reminder": "You saw {doctor} ({specialization}) {months} months ago. "
        "Would you like to book a follow-up?",
        "other_city_note": "There is no such specialist in {city}, showing doctors from other branches.",
    },
}


def translate(key: str, language: str, **values):
    texts = REPLIES.get(language) or REPLIES[DEFAULT_LANGUAGE]
    template = texts.get(key) or REPLIES[DEFAULT_LANGUAGE][key]

    return template.format(**values) if values else template
