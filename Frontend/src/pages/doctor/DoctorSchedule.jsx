import { useCallback, useEffect, useState } from "react";
import { getDepartments } from "../../lib/api/departments.js";
import { getMySchedule } from "../../lib/api/schedules.js";
import { clock } from "../../lib/format.js";
import { useI18n } from "../../lib/i18n.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import Skeleton from "../../components/Skeleton.jsx";

export default function DoctorSchedule() {
  const { t } = useI18n();
  const [schedule, setSchedule] = useState([]);
  const [departments, setDepartments] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return Promise.all([getMySchedule(), getDepartments()])
      .then(([rows, deps]) => {
        setSchedule(rows);
        setDepartments(Object.fromEntries(deps.map((d) => [d.id, d.name])));
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const fulls = t("weekdays.full");
  const sorted = [...schedule].sort(
    (a, b) => a.weekday - b.weekday || String(a.start_time).localeCompare(String(b.start_time))
  );

  return (
    <div className="mx-auto max-w-5xl px-sm py-md md:px-lg">
      <h1 className="mb-md text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
        {t("doctorCabinet.scheduleTitle")}
      </h1>

      {error ? (
        <ErrorState onRetry={load} />
      ) : loading ? (
        <div className="space-y-sm">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <EmptyState icon="calendar_month" title={t("doctorCabinet.noSchedule")} />
      ) : (
        <div className="space-y-sm">
          {sorted.map((row) => (
            <Card key={row.id} className="flex flex-wrap items-center justify-between gap-sm p-md">
              <div className="flex items-center gap-md">
                <span className="w-24 font-bold text-on-surface">{fulls[row.weekday]}</span>
                <span className="text-body-md text-on-surface">
                  {clock(row.start_time)} – {clock(row.end_time)}
                </span>
              </div>
              <div className="flex items-center gap-sm text-label-md text-on-surface-variant">
                <span className="rounded-full bg-secondary-container px-2.5 py-1 text-on-secondary-container">
                  {departments[row.department_id] || `#${row.department_id}`}
                </span>
                <span>
                  {row.slot_duration}
                  {row.buffer_duration ? ` +${row.buffer_duration}` : ""} {t("doctorCabinet.minShort")}
                </span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
