import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { findNearestSlot } from "../lib/api/schedules.js";
import { clock, formatDateShort, isoDate } from "../lib/format.js";
import DoctorAvatar from "./DoctorAvatar.jsx";
import { useI18n } from "../lib/i18n.jsx";
import Card from "./Card.jsx";


export default function DoctorCard({ doctor }) {
  const { t, lang } = useI18n();
  const [nearest, setNearest] = useState(undefined);

  useEffect(() => {
    let active = true;
    findNearestSlot(doctor.id)
      .then((slot) => active && setNearest(slot))
      .catch(() => active && setNearest(null));
    return () => {
      active = false;
    };
  }, [doctor.id]);

  const nearestLabel =
    nearest &&
    `${nearest.day === isoDate(new Date()) ? t("booking.today") : formatDateShort(nearest.day, lang)}, ${clock(
      nearest.time
    )}`;

  return (
    <Card className="card-lift flex flex-col p-md">
      <div className="flex items-center gap-md">
        <DoctorAvatar doctor={doctor} className="h-16 w-16 rounded-full" />
        <div className="min-w-0">
          <Link
            to={`/doctors/${doctor.id}`}
            className="block truncate text-headline-md font-semibold text-on-surface transition-colors hover:text-primary"
          >
            {doctor.full_name}
          </Link>
          <p className="mt-base text-label-md font-bold uppercase tracking-wider text-primary">
            {doctor.specialization}
          </p>
        </div>
      </div>

      <div className="mt-md flex flex-grow flex-col justify-end gap-md">
        {nearest ? (
          <div className="flex w-fit items-center gap-xs rounded-lg bg-tertiary-container px-2 py-1 text-on-tertiary-container">
            <span aria-hidden="true" className="material-symbols-outlined text-sm">event_available</span>
            <span className="text-label-md font-bold">
              {t("doctors.nearest")}: {nearestLabel}
            </span>
          </div>
        ) : nearest === null ? (
          <div className="flex w-fit items-center gap-xs rounded-lg bg-surface-container px-2 py-1 text-on-surface-variant">
            <span aria-hidden="true" className="material-symbols-outlined text-sm">event_busy</span>
            <span className="text-label-md">{t("doctors.noSlots")}</span>
          </div>
        ) : null}
        <Link
          to={`/booking/${doctor.id}`}
          className="rounded-xl bg-primary py-3 text-center font-bold text-on-primary shadow-md transition-all hover:opacity-90 active:scale-95"
        >
          {t("doctors.book")}
        </Link>
      </div>
    </Card>
  );
}
