import { Link } from "react-router-dom";
import { useT } from "../lib/i18n.jsx";
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

export default function DoctorCard({ doctor, footer }) {
  const t = useT();

  return (
    <Card className="flex flex-col p-md">
      <div className="flex items-center gap-md">
        <div className="grid h-16 w-16 shrink-0 place-items-center rounded-full bg-primary-container text-on-primary-container">
          <span className="text-headline-md font-bold">{initials(doctor.full_name)}</span>
        </div>
        <div className="min-w-0">
          <h3 className="truncate text-headline-md font-semibold text-on-surface">
            {doctor.full_name}
          </h3>
          <p className="mt-base text-label-md font-bold uppercase tracking-wider text-primary">
            {doctor.specialization}
          </p>
        </div>
      </div>

      <div className="mt-md flex flex-grow flex-col justify-end gap-md">
        {footer}
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
