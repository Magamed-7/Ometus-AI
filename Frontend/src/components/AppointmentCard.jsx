import { clock, formatDate, parseIso } from "../lib/format.js";
import { useI18n } from "../lib/i18n.jsx";
import Card from "./Card.jsx";
import StatusPill from "./StatusPill.jsx";

function daysUntil(iso) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((parseIso(iso) - today) / 86400000);
}

export default function AppointmentCard({ appointment, doctor, department, filial, children }) {
  const { t, lang } = useI18n();
  const days = daysUntil(appointment.date);

  return (
    <Card className="p-md">
      <div className="mb-md flex flex-col justify-between gap-sm md:flex-row md:items-center">
        <StatusPill status={appointment.status} />
        <div className="md:text-right">
          <p className="text-headline-md font-semibold text-primary">
            {formatDate(appointment.date, lang)}, {clock(appointment.time)}
          </p>
          {appointment.status === "booked" && days > 0 && (
            <p className="text-label-md text-on-surface-variant">{t("account.inDays", { n: days })}</p>
          )}
        </div>
      </div>

      <div className="mb-md grid gap-md md:grid-cols-2">
        <div>
          <p className="text-label-md text-on-surface-variant">{t("booking.doctor")}</p>
          <p className="font-bold text-on-surface">{doctor?.full_name || "—"}</p>
          {doctor?.specialization && (
            <p className="text-label-md text-on-surface-variant">{doctor.specialization}</p>
          )}
        </div>
        <div>
          <p className="text-label-md text-on-surface-variant">{t("doctors.filial")}</p>
          <p className="font-bold text-on-surface">{filial?.name || "—"}</p>
          <p className="text-label-md text-on-surface-variant">
            {[department?.name, filial?.address].filter(Boolean).join(" · ")}
          </p>
        </div>
      </div>

      {children}
    </Card>
  );
}
