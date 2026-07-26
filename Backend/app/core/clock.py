from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings

# Даты и время записей — это настенные часы клиники: «27 июля, 09:00» значит девять утра
# в Душанбе, а не в UTC. Сервер же может стоять где угодно, и datetime.now() на нём
# вернёт своё локальное время — на UTC-сервере расхождение с Душанбе пять часов,
# и половина рабочего дня выглядела бы «уже прошедшей».
CLINIC_TZ = ZoneInfo(settings.CLINIC_TIMEZONE)


def clinic_now() -> datetime:
    # без tzinfo: в базе date/time лежат naive, сравнивать надо с таким же naive
    return datetime.now(CLINIC_TZ).replace(tzinfo=None)


def clinic_today():
    return clinic_now().date()
