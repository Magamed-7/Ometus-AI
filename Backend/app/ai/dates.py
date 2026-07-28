import re
from datetime import date, timedelta

from app.core.clock import clinic_today

RELATIVE = {
    "послезавтра": 2,
    "позавчера": -2,
    "day after tomorrow": 2,
    "сегодня": 0,
    "завтра": 1,
    "вчера": -1,
    "пасфардо": 2,
    "дирӯз": -1,
    "имрӯз": 0,
    "фардо": 1,
    "yesterday": -1,
    "tomorrow": 1,
    "today": 0,
}

MONTHS = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "май": 5,
    "мая": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
    "januar": 1,
    "februar": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "septemb": 9,
    "octob": 10,
    "novemb": 11,
    "decemb": 12,
}

WEEKDAYS = {
    "понедельник": 0,
    "вторник": 1,
    "сред": 2,
    "четверг": 3,
    "пятниц": 4,
    "суббот": 5,
    "воскресен": 6,
    "душанбе": 0,
    "сешанбе": 1,
    "чоршанбе": 2,
    "панҷшанбе": 3,
    "якшанбе": 6,
    "ҷумъа": 4,
    "шанбе": 5,
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def longest_first(words):
    return sorted(words, key=len, reverse=True)


MONTH_NAMES = {
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
           "сентября", "октября", "ноября", "декабря"],
    "tg": ["январ", "феврал", "март", "апрел", "май", "июн", "июл", "август",
           "сентябр", "октябр", "ноябр", "декабр"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}


def human_date(day: date, language: str = "ru"):
    names = MONTH_NAMES.get(language) or MONTH_NAMES["ru"]

    if language == "en":
        return f"{names[day.month - 1]} {day.day}"

    return f"{day.day} {names[day.month - 1]}"

ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
NUMERIC = re.compile(r"\b(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\b")
DAY_AND_MONTH = re.compile(r"\b(\d{1,2})\s*(?:-?[а-яё]{0,2})?\s+([а-яёa-z]{3,})", re.IGNORECASE)
DAY_ONLY = re.compile(r"\b(\d{1,2})\s*(?:-?[а-яё]{0,2})?\s*(?:числ[оа]|рӯз|-го)\b", re.IGNORECASE)


def month_from(word: str):
    lowered = word.lower()

    for stem in longest_first(MONTHS):
        if lowered.startswith(stem):
            return MONTHS[stem]

    return None


def safe_date(year: int, month: int, day: int):
    try:
        return date(year, month, day)
    except ValueError:
        return None


def nearest(month: int, day: int, today: date, forward: bool):
    same_year = safe_date(today.year, month, day)

    if same_year is None:
        return None

    if forward and same_year < today:
        return safe_date(today.year + 1, month, day)

    if not forward and same_year > today:
        return safe_date(today.year - 1, month, day)

    return same_year


def nearest_day_of_month(day: int, today: date, forward: bool):
    step = 1 if forward else -1
    month = today.month
    year = today.year

    for _ in range(13):
        candidate = safe_date(year, month, day)

        if candidate is not None and ((forward and candidate >= today) or (not forward and candidate <= today)):
            return candidate

        month = month + step

        if month > 12:
            month, year = 1, year + 1
        elif month < 1:
            month, year = 12, year - 1

    return None


def nearest_weekday(weekday: int, today: date, forward: bool):
    if forward:
        return today + timedelta(days=(weekday - today.weekday()) % 7)

    return today - timedelta(days=(today.weekday() - weekday) % 7)


def parse_natural_date(text: str | None, forward: bool = True, today: date | None = None):
    if not text:
        return None

    today = today or clinic_today()
    lowered = text.lower()

    match = ISO.search(lowered)

    if match:
        return safe_date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    for word in longest_first(RELATIVE):
        if word in lowered:
            return today + timedelta(days=RELATIVE[word])

    match = NUMERIC.search(lowered)

    if match:
        day, month = int(match.group(1)), int(match.group(2))
        year = match.group(3)

        if year:
            year = int(year)
            return safe_date(year + 2000 if year < 100 else year, month, day)

        return nearest(month, day, today, forward)

    for match in DAY_AND_MONTH.finditer(lowered):
        month = month_from(match.group(2))

        if month is not None:
            return nearest(month, int(match.group(1)), today, forward)

    match = DAY_ONLY.search(lowered)

    if match:
        return nearest_day_of_month(int(match.group(1)), today, forward)

    for word in longest_first(WEEKDAYS):
        if word in lowered:
            return nearest_weekday(WEEKDAYS[word], today, forward)

    return None
