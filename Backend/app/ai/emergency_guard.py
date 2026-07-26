from app.ai.specialization_map import normalize

EMERGENCY_KEYWORDS = [
    "без сознани",
    "потерял сознание",
    "теряю сознание",
    "не дышит",
    "не могу дышать",
    "задыха",
    "кровотеч",
    "кровь идет",
    "инфаркт",
    "инсульт",
    "судорог",
    "отравлени",
    "передозиров",
    "анафилакт",
    "аллергический шок",
    "боль в груди",
    "давит в груди",
    "сильный ожог",
    "перестал говорить",
    "отнялась рука",
    "отнялась нога",
    "покончить с собой",
    "суицид",
    "скорая",
    "скорую",
]

EMERGENCY_MESSAGE = (
    "Судя по описанию, ситуация может быть экстренной. Не ждите планового приёма — "
    "немедленно вызовите скорую помощь по номеру 03 или 112 либо обратитесь в ближайший "
    "приёмный покой."
)


CRITICAL_SYMPTOMS = [
    "без сознани",
    "потерял сознание",
    "теряю сознание",
    "не дышит",
    "не могу дышать",
    "задыха",
    "кровотеч",
    "кровь идет",
    "инфаркт",
    "инсульт",
    "судорог",
    "отравлени",
    "передозиров",
    "анафилакт",
    "аллергический шок",
    "покончить с собой",
    "суицид",
]

HIGH_SYMPTOMS = [
    "боль в груди",
    "давит в груди",
    "острая боль",
    "сильный ожог",
    "перестал говорить",
    "отнялась рука",
    "отнялась нога",
    "парализ",
    "сильное кровотечение",
    "сильная боль",
]

MODERATE_SYMPTOMS = [
    "высокая температура",
    "лихорадка",
    "сильный кашель",
    "боль в животе",
    "рвота",
    "понос",
    "головная боль",
    "сильная слабость",
    "одышка",
    "тошнота",
]


def assess_symptom_severity(text: str) -> int:
    normalized = normalize(text)

    if any(keyword in normalized for keyword in CRITICAL_SYMPTOMS):
        return 3

    if any(keyword in normalized for keyword in HIGH_SYMPTOMS):
        return 2

    if any(keyword in normalized for keyword in MODERATE_SYMPTOMS):
        return 1

    return 0


def is_emergency(text: str):
    normalized = normalize(text)
    return any(keyword in normalized for keyword in EMERGENCY_KEYWORDS)
