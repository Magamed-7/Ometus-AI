import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { searchDoctors } from "../lib/api/doctors.js";
import { useT } from "../lib/i18n.jsx";
import DoctorCard from "../components/DoctorCard.jsx";
import ErrorState from "../components/ErrorState.jsx";
import Skeleton from "../components/Skeleton.jsx";

export default function Doctors() {
  const t = useT();
  const [params] = useSearchParams();
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [allSpecs, setAllSpecs] = useState([]);
  const [spec, setSpec] = useState(params.get("specialization") || "");

  const filialId = params.get("filial_id") || "";
  const departmentId = params.get("department_id") || "";

  useEffect(() => {
    searchDoctors()
      .then((data) => {
        const unique = [...new Set(data.map((d) => d.specialization).filter(Boolean))];
        setAllSpecs(unique.sort((a, b) => a.localeCompare(b, "ru")));
      })
      .catch(() => {});
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return searchDoctors({
      specialization: spec,
      filial_id: filialId,
      department_id: departmentId,
    })
      .then(setDoctors)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [spec, filialId, departmentId]);

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

      <div className="flex flex-col gap-lg lg:flex-row">
        <aside className="w-full flex-shrink-0 lg:w-72">
          <div className="sticky top-24 rounded-xl border border-outline-variant bg-surface-container-lowest p-md">
            <div className="mb-md flex items-center gap-xs">
              <span className="material-symbols-outlined text-primary">filter_list</span>
              <h2 className="text-headline-md font-semibold text-on-surface">
                {t("doctors.filters")}
              </h2>
            </div>

            <div>
              <label
                htmlFor="spec-filter"
                className="mb-xs block text-label-md font-semibold text-on-surface-variant"
              >
                {t("doctors.specialization")}
              </label>
              <select
                id="spec-filter"
                value={spec}
                onChange={(e) => setSpec(e.target.value)}
                className="w-full rounded-lg border border-outline-variant bg-surface-container-low p-2.5 text-body-md focus:border-primary focus:outline-none"
              >
                <option value="">{t("doctors.anySpecialization")}</option>
                {allSpecs.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </aside>

        <div className="flex-grow">
          {error ? (
            <ErrorState onRetry={load} />
          ) : (
            <div className="grid grid-cols-1 gap-md sm:grid-cols-2 xl:grid-cols-3">
              {loading
                ? [0, 1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-64" />)
                : doctors.map((d) => <DoctorCard key={d.id} doctor={d} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
