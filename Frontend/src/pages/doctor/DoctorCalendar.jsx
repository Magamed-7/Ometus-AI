import { useCallback, useEffect, useState } from "react";
import { getMyCalendar } from "../../lib/api/schedules.js";
import { clock, isoDate } from "../../lib/format.js";
import { useI18n } from "../../lib/i18n.jsx";
import Card from "../../components/Card.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";

const DAYS = 14;

// цвет несёт смысл вместе с подписью, а не вместо неё: одним цветом статус
// не отличить ни в чёрно-белой печати, ни при дальтонизме
const STATUS = {
  working: { icon: "event_available", tone: "border-primary/40 bg-primary-container/40" },
  override: { icon: "edit_calendar", tone: "border-tertiary/50 bg-tertiary-container/40" },
  absent: { icon: "beach_access", tone: "border-error/40 bg-error-container/40" },
  off: { icon: "event_busy", tone: "border-outline-variant bg-surface-container-low" },
};

function shift(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date;
}

export default function DoctorCalendar({ reloadKey }) {
  const { t, lang } = useI18n();
  const [offset, setOffset] = useState(0);
  const [days, setDays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return getMyCalendar(isoDate(shift(offset)), isoDate(shift(offset + DAYS - 1)))
      .then(setDays)
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [offset]);

  // ключ меняется, когда врач добавил отпуск или правил сетку: календарь обязан
  // пересчитаться сразу, иначе он и создаёт ощущение, что отпуск ни на что не влияет
  useEffect(() => {
    load();
  }, [load, reloadKey]);

  const shorts = t("weekdays.short");
  const today = isoDate(new Date());

  return (
    <section className="mt-lg" aria-labelledby="doctor-calendar">
      <div className="mb-md flex flex-wrap items-center justify-between gap-sm">
        <div>
          <h2 id="doctor-calendar" className="text-headline-md font-bold text-on-surface">
            {t("doctorCabinet.calendarTitle")}
          </h2>
          <p className="text-label-md text-on-surface-variant">
            {t("doctorCabinet.calendarHint")}
          </p>
        </div>
        <div className="flex items-center gap-xs">
          <button
            type="button"
            onClick={() => setOffset((prev) => prev - DAYS)}
            aria-label={t("doctorCabinet.calendarPrev")}
            className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container"
          >
            <span aria-hidden="true" className="material-symbols-outlined">chevron_left</span>
          </button>
          {offset !== 0 && (
            <button
              type="button"
              onClick={() => setOffset(0)}
              className="rounded-full border border-outline-variant px-md py-2 text-label-md font-semibold text-on-surface transition-colors hover:bg-surface-container"
            >
              {t("doctorCabinet.calendarToday")}
            </button>
          )}
          <button
            type="button"
            onClick={() => setOffset((prev) => prev + DAYS)}
            aria-label={t("doctorCabinet.calendarNext")}
            className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container"
          >
            <span aria-hidden="true" className="material-symbols-outlined">chevron_right</span>
          </button>
        </div>
      </div>

      <ul className="mb-md flex flex-wrap gap-sm">
        {Object.keys(STATUS).map((key) => (
          <li
            key={key}
            className={`flex items-center gap-xs rounded-full border px-sm py-1 text-label-md text-on-surface ${STATUS[key].tone}`}
          >
            <span aria-hidden="true" className="material-symbols-outlined text-base">
              {STATUS[key].icon}
            </span>
            {t(`doctorCabinet.status_${key}`)}
          </li>
        ))}
      </ul>

      {error ? (
        <ErrorState error={error} onRetry={load} />
      ) : loading ? (
        <div className="grid grid-cols-2 gap-sm sm:grid-cols-4 lg:grid-cols-7">
          <LoadingStatus />
          {Array.from({ length: DAYS }, (_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-sm sm:grid-cols-4 lg:grid-cols-7">
          {days.map((day) => {
            const look = STATUS[day.status] || STATUS.off;
            const isToday = day.date === today;

            return (
              <Card
                key={day.date}
                className={`flex flex-col gap-xs border p-sm ${look.tone} ${
                  isToday ? "ring-2 ring-primary" : ""
                }`}
              >
                <div className="flex items-baseline justify-between gap-xs">
                  <span className="text-headline-md font-bold text-on-surface">
                    {Number(day.date.slice(8, 10))}
                  </span>
                  <span className="text-label-md text-on-surface-variant">
                    {shorts[day.weekday]}
                  </span>
                </div>
                <span className="flex items-center gap-xs text-label-md font-semibold text-on-surface">
                  <span aria-hidden="true" className="material-symbols-outlined text-base">
                    {look.icon}
                  </span>
                  {t(`doctorCabinet.status_${day.status}`)}
                </span>
                {day.start_time && (
                  <span className="text-label-md text-on-surface-variant">
                    {clock(day.start_time)} – {clock(day.end_time)}
                  </span>
                )}
                {day.absence_reason && (
                  <span className="text-label-md text-on-surface-variant">
                    {day.absence_reason}
                  </span>
                )}
                {(day.slots_taken > 0 || day.slots_free > 0) && (
                  <span className="mt-auto text-label-md text-on-surface-variant">
                    {t("doctorCabinet.slotsCount", {
                      taken: day.slots_taken,
                      free: day.slots_free,
                    })}
                  </span>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </section>
  );
}
