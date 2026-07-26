import { useCallback, useEffect, useState } from "react";
import {
  completeAppointment,
  getDoctorAppointments,
  noShowAppointment,
} from "../../lib/api/appointments.js";
import { errorText } from "../../lib/api/errorText.js";
import { clock, isoDate, phone as formatPhone } from "../../lib/format.js";
import { useT } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Select } from "../../components/Field.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";
import StatusPill from "../../components/StatusPill.jsx";

const STATUSES = ["booked", "completed", "cancelled", "no_show"];

export default function DoctorToday() {
  const t = useT();
  const toast = useToast();
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [acting, setActing] = useState(null);
  const [day, setDay] = useState(() => isoDate(new Date()));
  const [status, setStatus] = useState("booked");

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return getDoctorAppointments({ day: day || undefined, status: status || undefined })
      .then(setAppointments)
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [day, status]);

  useEffect(() => {
    load();
  }, [load]);

  const act = async (id, fn) => {
    setActing(id);
    try {
      await fn(id);
      await load();
    } catch (e) {
      toast.error(errorText(t, e));
    } finally {
      setActing(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-sm py-md md:px-lg">
      <h1 className="mb-md text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
        {t("doctorCabinet.todayTitle")}
      </h1>

      <div className="mb-md grid gap-sm sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="doctor-day"
            className="text-label-md font-semibold text-on-surface-variant"
          >
            {t("doctorCabinet.filterDay")}
          </label>
          <input
            id="doctor-day"
            type="date"
            value={day}
            onChange={(e) => setDay(e.target.value)}
            className="min-h-11 w-full rounded-xl border border-outline-variant bg-surface-container-lowest px-4 py-2.5 text-body-md text-on-surface focus:border-primary focus:outline-none"
          />
        </div>
        <Select
          label={t("doctorCabinet.filterStatus")}
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">{t("common.all")}</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {t(`status.${s}`)}
            </option>
          ))}
        </Select>
      </div>

      {error ? (
        <ErrorState error={error} onRetry={load} />
      ) : loading ? (
        <div className="space-y-sm">
          <LoadingStatus />
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : appointments.length === 0 ? (
        <EmptyState
          icon="event_available"
          title={day === isoDate(new Date()) ? t("doctorCabinet.noToday") : t("doctorCabinet.noDay")}
          text={t("doctorCabinet.noDayText")}
          action={
            (day || status) && (
              <Button
                variant="outline"
                icon="refresh"
                onClick={() => {
                  setDay("");
                  setStatus("");
                }}
              >
                {t("common.reset")}
              </Button>
            )
          }
        />
      ) : (
        <div className="space-y-sm">
          {appointments.map((appointment) => (
            <Card key={appointment.id} className="flex flex-col gap-md p-md sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-md">
                <div className="grid h-14 w-14 shrink-0 place-items-center rounded-xl bg-primary-container text-headline-md font-bold text-on-primary-container">
                  {clock(appointment.time)}
                </div>
                <div>
                  <p className="font-bold text-on-surface">
                    {appointment.patient_name || `#${appointment.patient_id}`}
                  </p>
                  {appointment.patient_phone && (
                    <a
                      href={`tel:${appointment.patient_phone}`}
                      className="mt-0.5 inline-flex items-center gap-1 text-label-md text-on-surface-variant transition-colors hover:text-primary"
                    >
                      <span aria-hidden="true" className="material-symbols-outlined text-base">call</span>
                      {formatPhone(appointment.patient_phone)}
                    </a>
                  )}
                </div>
              </div>
              {appointment.status === "booked" ? (
                <div className="flex flex-wrap gap-sm">
                  <Button
                    icon="task_alt"
                    loading={acting === appointment.id}
                    onClick={() => act(appointment.id, completeAppointment)}
                  >
                    {t("doctorCabinet.complete")}
                  </Button>
                  <Button
                    variant="outline"
                    icon="person_off"
                    disabled={acting === appointment.id}
                    onClick={() => act(appointment.id, noShowAppointment)}
                  >
                    {t("doctorCabinet.noShow")}
                  </Button>
                </div>
              ) : (
                <StatusPill status={appointment.status} />
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
