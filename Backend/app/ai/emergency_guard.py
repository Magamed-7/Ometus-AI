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

EMERGENCY_KEYWORDS_TG = [
    "беҳуш",
    "нафас намекашад",
    "нафас гирифта наметавонам",
    "хунравӣ",
    "хун меравад",
    "сакта",
    "инфаркт",
    "инсулт",
    "тарканҷ",
    "заҳролуд",
    "дарди сина",
    "сӯхтагӣ",
    "гап зада наметавонад",
    "худкушӣ",
    "ёрии таъҷилӣ",
    "таъҷилӣ",
]

EMERGENCY_KEYWORDS_EN = [
    "unconscious",
    "not breathing",
    "cannot breathe",
    "can not breathe",
    "can't breathe",
    "choking",
    "bleeding",
    "heart attack",
    "stroke",
    "seizure",
    "poisoning",
    "overdose",
    "anaphyla",
    "chest pain",
    "severe burn",
    "suicide",
    "kill myself",
    "ambulance",
    "emergency",
]

ALL_EMERGENCY_KEYWORDS = EMERGENCY_KEYWORDS + EMERGENCY_KEYWORDS_TG + EMERGENCY_KEYWORDS_EN

EMERGENCY_MESSAGES = {
    "ru": (
        "Судя по описанию, ситуация может быть экстренной. Не ждите планового приёма — "
        "немедленно вызовите скорую помощь по номеру 03 или 112 либо обратитесь в ближайший "
        "приёмный покой."
    ),
    "tg": (
        "Аз рӯи тавсиф вазъият метавонад таъҷилӣ бошад. Навбати нақшавиро интизор нашавед — "
        "фавран ба ёрии таъҷилӣ бо рақами 03 ё 112 занг занед ё ба наздиктарин "
        "шӯъбаи қабул муроҷиат кунед."
    ),
    "en": (
        "This may be an emergency. Do not wait for a scheduled appointment — "
        "call an ambulance on 03 or 112 immediately, or go to the nearest emergency room."
    ),
}

EMERGENCY_MESSAGE = EMERGENCY_MESSAGES["ru"]


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

HIGH_SEVERITY_NOTES = {
    "ru": (
        "Судя по описанию, тянуть не стоит — подберу ближайшее время. "
        "Если станет хуже, обратитесь в скорую."
    ),
    "tg": (
        "Аз рӯи тавсиф кашол додан лозим нест — наздиктарин вақтро пешниҳод мекунам. "
        "Агар ҳолат бадтар шавад, ба ёрии таъҷилӣ муроҷиат кунед."
    ),
    "en": (
        "This should not wait — I will look for the nearest available time. "
        "If it gets worse, call an ambulance."
    ),
}

HIGH_SEVERITY_NOTE = HIGH_SEVERITY_NOTES["ru"]


SERVICE_KEYWORDS = ["скорая", "скорую", "ёрии таъҷилӣ", "таъҷилӣ", "ambulance"]
NEGATIONS = ["не нужна", "не нужен", "не надо", "не требуется", "без ", "not ", "no need", "лозим нест"]


def is_negated(normalized: str, keyword: str):
    position = normalized.find(keyword)

    if position == -1:
        return False

    before = normalized[max(0, position - 30) : position]
    return any(negation in before for negation in NEGATIONS)


def is_emergency(text: str):
    normalized = normalize(text)
    matched = [keyword for keyword in ALL_EMERGENCY_KEYWORDS if keyword in normalized]

    if not matched:
        return False

    if all(
        keyword in SERVICE_KEYWORDS and is_negated(normalized, keyword) for keyword in matched
    ):
        return False

    return True


def assess_symptom_severity(text: str):
    if is_emergency(text):
        return SEVERITY_CRITICAL

    normalized = normalize(text)

    if any(keyword in normalized for keyword in HIGH_SYMPTOMS):
        return SEVERITY_HIGH

    if any(keyword in normalized for keyword in MODERATE_SYMPTOMS):
        return SEVERITY_MODERATE

    return SEVERITY_LOW
