import { useCallback, useEffect, useState } from "react";
import {
  completeAppointment,
  getDoctorToday,
  noShowAppointment,
} from "../../lib/api/appointments.js";
import { errorText } from "../../lib/api/errorText.js";
import { clock, phone as formatPhone } from "../../lib/format.js";
import { useT } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import Skeleton from "../../components/Skeleton.jsx";
import StatusPill from "../../components/StatusPill.jsx";

export default function DoctorToday() {
  const t = useT();
  const toast = useToast();
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [acting, setActing] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return getDoctorToday()
      .then(setAppointments)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

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

      {error ? (
        <ErrorState onRetry={load} />
      ) : loading ? (
        <div className="space-y-sm">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : appointments.length === 0 ? (
        <EmptyState icon="event_available" title={t("doctorCabinet.noToday")} />
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
                      <span className="material-symbols-outlined text-base">call</span>
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
