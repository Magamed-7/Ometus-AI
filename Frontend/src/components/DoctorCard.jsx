import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { findNearestSlot } from "../lib/api/schedules.js";
import { clock, formatDateShort, isoDate } from "../lib/format.js";
import { avatarAccent } from "../lib/mocks/doctors.js";
import { useI18n } from "../lib/i18n.jsx";
import Card from "./Card.jsx";

function initials(name) {
  return (name || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

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
    <Card className="flex flex-col p-md">
      <div className="flex items-center gap-md">
        <div
          className={`grid h-16 w-16 shrink-0 place-items-center rounded-full bg-gradient-to-br text-on-primary ${avatarAccent(
            doctor.id
          )}`}
        >
          <span className="text-headline-md font-bold">{initials(doctor.full_name)}</span>
        </div>
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
