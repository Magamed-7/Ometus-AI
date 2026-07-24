import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { searchDoctors } from "../lib/api/doctors.js";
import { useT } from "../lib/i18n.jsx";
import Card from "../components/Card.jsx";
import ErrorState from "../components/ErrorState.jsx";
import Skeleton from "../components/Skeleton.jsx";

export default function Doctors() {
  const t = useT();
  const [params] = useSearchParams();
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const specialization = params.get("specialization") || "";
  const filialId = params.get("filial_id") || "";
  const departmentId = params.get("department_id") || "";

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return searchDoctors({
      specialization,
      filial_id: filialId,
      department_id: departmentId,
    })
      .then(setDoctors)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [specialization, filialId, departmentId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
      <header className="mb-lg">
        <h1 className="mb-base text-headline-lg-mobile text-on-surface md:text-headline-xl">
          {t("doctors.title")}
        </h1>
        <p className="max-w-2xl text-body-lg text-on-surface-variant">{t("doctors.subtitle")}</p>
      </header>

      {error ? (
        <ErrorState onRetry={load} />
      ) : (
        <div className="grid grid-cols-1 gap-md sm:grid-cols-2 xl:grid-cols-3">
          {loading
            ? [0, 1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-64" />)
            : doctors.map((d) => (
                <Card key={d.id} className="flex flex-col p-md">
                  <h3 className="text-headline-md font-semibold text-on-surface">{d.full_name}</h3>
                  <p className="mt-base text-label-md font-bold uppercase tracking-wider text-primary">
                    {d.specialization}
                  </p>
                  <Link
                    to={`/booking/${d.id}`}
                    className="mt-md rounded-xl bg-primary py-3 text-center font-bold text-on-primary transition-all hover:opacity-90 active:scale-95"
                  >
                    {t("doctors.book")}
                  </Link>
                </Card>
              ))}
        </div>
      )}
    </div>
  );
}
