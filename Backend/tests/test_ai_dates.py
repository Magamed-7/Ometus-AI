from datetime import date

from app.ai.dates import parse_natural_date
from app.ai.staff import match_intent, ADMIN_KEYWORDS, DOCTOR_KEYWORDS

TODAY = date(2026, 7, 28)


def parse(text, forward=True):
    return parse_natural_date(text, forward=forward, today=TODAY)


def test_bare_day_number_becomes_the_nearest_such_day():
    assert parse("Где остались свободные окна на 30 число ?") == date(2026, 7, 30)


def test_a_day_that_already_passed_rolls_into_the_next_month():
    assert parse("кто записан на 5 число") == date(2026, 8, 5)


def test_day_with_a_month_name():
    assert parse("покажи свободное время на 5 августа") == date(2026, 8, 5)


def test_month_name_in_english():
    assert parse("free slots on 3 august") == date(2026, 8, 3)


def test_numeric_date_with_and_without_a_year():
    assert parse("на 30.07") == date(2026, 7, 30)
    assert parse("на 30.07.2027") == date(2027, 7, 30)


def test_iso_date_wins():
    assert parse("что там на 2026-08-11") == date(2026, 8, 11)


def test_relative_words():
    assert parse("что у меня завтра") == date(2026, 7, 29)
    assert parse("а послезавтра") == date(2026, 7, 30)
    assert parse("кто был вчера", forward=False) == date(2026, 7, 27)
    assert parse("имрӯз чӣ хел") == TODAY
    assert parse("what about tomorrow") == date(2026, 7, 29)


# «завтра» лежит внутри «послезавтра», «шанбе» — внутри «якшанбе»: если перебирать
# ключи в произвольном порядке, короткий срабатывает первым и дата уезжает
def test_longer_words_win_over_the_ones_nested_in_them():
    assert parse("послезавтра") == date(2026, 7, 30)
    assert parse("позавчера", forward=False) == date(2026, 7, 26)
    assert parse("якшанбе") == date(2026, 8, 2)
    assert parse("шанбе") == date(2026, 8, 1)


def test_weekday_by_name():
    assert parse("что в пятницу").weekday() == 4
    assert parse("on friday").weekday() == 4


def test_numbers_that_are_not_dates_are_left_alone():
    assert parse("моя загрузка за 30 дней") is None
    assert parse("сколько у меня приёмов") is None
    assert parse("") is None
    assert parse(None) is None


def test_doctor_keywords_catch_the_prompt_chips():
    chips = {
        "Кто у меня сегодня?": "today",
        "Где остались свободные окна?": "free",
        "Моя загрузка за месяц": "load",
        "Когда у меня отпуска?": "absences",
    }

    for message, expected in chips.items():
        assert match_intent(message, DOCTOR_KEYWORDS)["intent"] == expected


def test_admin_keywords_catch_the_prompt_chips():
    chips = {
        "Сколько потрачено на ИИ?": "ai_spend",
        "Кто из врачей самый загруженный?": "busiest",
        "Сколько было неявок?": "no_shows",
        "Сколько врачей в клинике?": "staff",
    }

    for message, expected in chips.items():
        assert match_intent(message, ADMIN_KEYWORDS)["intent"] == expected


def test_keywords_stay_silent_on_nonsense():
    assert match_intent("погода на марсе", DOCTOR_KEYWORDS) is None
    assert match_intent("погода на марсе", ADMIN_KEYWORDS) is None
