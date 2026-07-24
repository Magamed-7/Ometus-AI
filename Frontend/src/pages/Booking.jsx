import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getDoctor } from "../lib/api/doctors.js";
import { avatarAccent } from "../lib/mocks/doctors.js";
import { useT } from "../lib/i18n.jsx";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import Skeleton from "../components/Skeleton.jsx";

function initials(name) {
  return (name || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export default function Booking() {
  const t = useT();
  const { doctorId } = useParams();
  const [doctor, setDoctor] = useState(null);
  const [loading, setLoading] = useState(Boolean(doctorId));
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    if (!doctorId) return Promise.resolve();
    setLoading(true);
    setError(false);
    return getDoctor(doctorId)
      .then(setDoctor)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [doctorId]);

  useEffect(() => {
    load();
  }, [load]);

  if (!doctorId) {
    return (
      <div className="mx-auto max-w-3xl px-md py-xl md:px-lg">
        <EmptyState
          icon="event"
          title={t("booking.pickDoctor")}
          action={
            <Link
              to="/doctors"
              className="mt-sm rounded-xl bg-primary px-lg py-3 font-bold text-on-primary transition-all hover:opacity-90"
            >
              {t("booking.toDoctors")}
            </Link>
          }
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
        <Skeleton className="h-32" />
        <Skeleton className="mt-md h-64" />
      </div>
    );
  }

  if (error || !doctor) {
    return (
      <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
        <ErrorState onRetry={load} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
      <h1 className="mb-md text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
        {t("booking.title")}
      </h1>
      <div className="grid grid-cols-1 gap-md lg:grid-cols-3">
        <div className="flex flex-col gap-md lg:col-span-2">
          <Card className="flex flex-col items-center gap-md p-md sm:flex-row sm:items-start">
            <div
              className={`grid h-24 w-24 shrink-0 place-items-center rounded-xl bg-gradient-to-br text-on-primary ${avatarAccent(
                doctor.id
              )}`}
            >
              <span className="text-headline-lg font-bold">{initials(doctor.full_name)}</span>
            </div>
            <div className="text-center sm:text-left">
              <span className="mb-xs inline-block w-fit rounded-full bg-secondary-container px-3 py-1 text-label-md font-semibold text-on-secondary-container">
                {doctor.specialization}
              </span>
              <h2 className="text-headline-md font-semibold text-on-surface">{doctor.full_name}</h2>
            </div>
          </Card>
          <Card className="p-md" id="date-section" />
          <Card className="p-md" id="slots-section" />
        </div>
        <div className="lg:col-span-1">
          <div className="sticky top-24">
            <Card className="p-md" id="summary" />
          </div>
        </div>
      </div>
    </div>
  );
}
