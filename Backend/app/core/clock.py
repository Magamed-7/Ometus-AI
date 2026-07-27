from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings

CLINIC_TZ = ZoneInfo(settings.CLINIC_TIMEZONE)


def clinic_now() -> datetime:
    return datetime.now(CLINIC_TZ).replace(tzinfo=None)


def clinic_today():
    return clinic_now().date()
