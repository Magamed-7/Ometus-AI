import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getDoctor, getDoctorDepartments } from "../lib/api/doctors.js";
import { getFilials } from "../lib/api/filials.js";
import DoctorAvatar from "../components/DoctorAvatar.jsx";
import { useT } from "../lib/i18n.jsx";
import Card from "../components/Card.jsx";
import ErrorState from "../components/ErrorState.jsx";
import LoadingStatus from "../components/LoadingStatus.jsx";
import Skeleton from "../components/Skeleton.jsx";


export default function DoctorDetail() {
  const t = useT();
  const { id } = useParams();
  const [doctor, setDoctor] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [filials, setFilials] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return Promise.all([getDoctor(id), getDoctorDepartments(id), getFilials()])
      .then(([doc, deps, fils]) => {
        setDoctor(doc);
        setDepartments(deps);
        setFilials(Object.fromEntries(fils.map((f) => [f.id, f])));
      })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-md py-lg md:px-lg">
        <LoadingStatus />
        <Skeleton className="h-40" />
        <Skeleton className="mt-md h-52" />
      </div>
    );
  }

  if (error || !doctor) {
    return (
      <div className="mx-auto max-w-4xl px-md py-lg md:px-lg">
        <ErrorState error={error} onRetry={load} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-md py-lg md:px-lg">
      <Link
        to="/doctors"
        className="mb-md inline-flex items-center gap-1 text-label-md font-semibold text-on-surface-variant transition-colors hover:text-primary"
      >
        <span aria-hidden="true" className="material-symbols-outlined text-lg">arrow_back</span>
        {t("doctors.title")}
      </Link>

      <Card className="flex flex-col items-center gap-md p-lg text-center sm:flex-row sm:text-left">
        <DoctorAvatar
          doctor={doctor}
          className="h-24 w-24 rounded-full"
          textClass="text-headline-lg"
        />
        <div className="flex-grow">
          <h1 className="text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
            {doctor.full_name}
          </h1>
          <p className="mt-xs text-label-md font-bold uppercase tracking-wider text-primary">
            {doctor.specialization}
          </p>
        </div>
        <Link
          to={`/booking/${doctor.id}`}
          className="w-full rounded-xl bg-primary px-lg py-3 text-center font-bold text-on-primary shadow-md transition-all hover:opacity-90 active:scale-95 sm:w-auto"
        >
          {t("doctors.book")}
        </Link>
      </Card>

      <h2 className="mb-md mt-lg text-headline-md font-semibold text-on-surface">
        {t("doctors.departmentsOf")}
      </h2>
      <div className="grid grid-cols-1 gap-sm sm:grid-cols-2">
        {departments.map((dep) => {
          const filial = filials[dep.filial_id];
          return (
            <Card key={dep.id} className="flex items-start gap-sm p-md">
              <span aria-hidden="true" className="material-symbols-outlined mt-0.5 text-primary">meeting_room</span>
              <div>
                <p className="font-semibold text-on-surface">{dep.name}</p>
                {filial && (
                  <p className="mt-base flex items-center gap-1 text-label-md text-on-surface-variant">
                    <span aria-hidden="true" className="material-symbols-outlined text-sm">location_on</span>
                    {filial.name}, {filial.city}
                  </p>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
