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


HIGH_SYMPTOMS = [
    "острая боль",
    "сильная боль",
    "парализ",
    "температура 39",
    "температура 40",
    "сильная рвота",
    "не могу встать",
    "не проходит боль",
]

MODERATE_SYMPTOMS = [
    "высокая температура",
    "лихорадка",
    "сильный кашель",
    "боль в животе",
    "рвота",
    "понос",
    "головная боль",
    "слабость",
    "одышка",
    "тошнота",
]

SEVERITY_CRITICAL = 3
SEVERITY_HIGH = 2
SEVERITY_MODERATE = 1
SEVERITY_LOW = 0

HIGH_SEVERITY_NOTE = (
    "Судя по описанию, тянуть не стоит — подберу ближайшее время. "
    "Если станет хуже, обратитесь в скорую."
)


def is_emergency(text: str):
    normalized = normalize(text)
    return any(keyword in normalized for keyword in EMERGENCY_KEYWORDS)


def assess_symptom_severity(text: str):
    if is_emergency(text):
        return SEVERITY_CRITICAL

    normalized = normalize(text)

    if any(keyword in normalized for keyword in HIGH_SYMPTOMS):
        return SEVERITY_HIGH

    if any(keyword in normalized for keyword in MODERATE_SYMPTOMS):
        return SEVERITY_MODERATE

    return SEVERITY_LOW
