import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { searchDoctors } from "../lib/api/doctors.js";
import { getFilials } from "../lib/api/filials.js";
import { useT } from "../lib/i18n.jsx";
import DoctorCard from "../components/DoctorCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import LoadingStatus from "../components/LoadingStatus.jsx";
import Skeleton from "../components/Skeleton.jsx";

export default function Doctors() {
  const t = useT();
  const [params, setParams] = useSearchParams();
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [allSpecs, setAllSpecs] = useState([]);
  const [filials, setFilials] = useState([]);

  // Адрес — единственный источник правды. Раньше фильтры дублировались в состоянии,
  // которое читало адрес только при монтировании, а отдельный эффект писал это состояние
  // обратно в адрес. Из-за этого повторный поиск из шапки затирался: страница уже открыта,
  // компонент не пересоздаётся, и второй запрос просто не доходил до загрузки.
  const spec = params.get("specialization") || "";
  const departmentId = params.get("department_id") || "";
  const search = params.get("search") || "";
  const filialKey = params.getAll("filial_id").join(",");
  const filialIds = filialKey ? filialKey.split(",") : [];

  const patch = (mutate) => {
    const next = new URLSearchParams(params);
    mutate(next);
    setParams(next, { replace: true });
  };

  const setSpec = (value) =>
    patch((next) => (value ? next.set("specialization", value) : next.delete("specialization")));

  useEffect(() => {
    searchDoctors()
      .then((data) => {
        const unique = [...new Set(data.map((d) => d.specialization).filter(Boolean))];
        setAllSpecs(unique.sort((a, b) => a.localeCompare(b, "ru")));
      })
      .catch(() => {});
    getFilials()
      .then(setFilials)
      .catch(() => {});
  }, []);

  const toggleFilial = (id) =>
    patch((next) => {
      const current = next.getAll("filial_id");
      const updated = current.includes(id)
        ? current.filter((value) => value !== id)
        : [...current, id];
      next.delete("filial_id");
      for (const value of updated) next.append("filial_id", value);
    });

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    const ids = filialKey ? filialKey.split(",") : [""];
    return Promise.all(
      ids.map((fid) =>
        searchDoctors({
          specialization: spec,
          filial_id: fid,
          department_id: departmentId,
          search,
        })
      )
    )
      .then((lists) => {
        const merged = new Map();
        for (const doctor of lists.flat()) merged.set(doctor.id, doctor);
        setDoctors([...merged.values()]);
      })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [spec, filialKey, departmentId, search]);

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
              <span aria-hidden="true" className="material-symbols-outlined text-primary">filter_list</span>
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

            {filials.length > 0 && (
              <div className="mt-md">
                <span className="mb-xs block text-label-md font-semibold text-on-surface-variant">
                  {t("doctors.filial")}
                </span>
                <div className="mt-xs space-y-sm">
                  {filials.map((f) => (
                    <label
                      key={f.id}
                      className="group flex cursor-pointer items-center gap-sm"
                    >
                      <input
                        type="checkbox"
                        checked={filialIds.includes(String(f.id))}
                        onChange={() => toggleFilial(String(f.id))}
                        className="h-5 w-5 rounded border-outline-variant text-primary focus:ring-primary"
                      />
                      <span className="text-body-md text-on-surface transition-colors group-hover:text-primary">
                        {f.name}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {(spec || search || filialIds.length > 0) && (
              <button
                type="button"
                onClick={() => setParams(new URLSearchParams(), { replace: true })}
                className="mt-md w-full rounded-lg bg-secondary-container py-3 font-bold text-on-secondary-container transition-all hover:bg-surface-container-high"
              >
                {t("doctors.reset")}
              </button>
            )}
          </div>
        </aside>

        <div className="flex-grow">
          {search && (
            <div className="mb-md flex flex-wrap items-center gap-sm">
              <span className="flex items-center gap-xs rounded-full bg-secondary-container px-md py-2 text-label-md font-semibold text-on-secondary-container">
                <span aria-hidden="true" className="material-symbols-outlined text-base">
                  search
                </span>
                {search}
                <button
                  type="button"
                  onClick={() => patch((next) => next.delete("search"))}
                  aria-label={t("doctors.clearSearch")}
                  className="ml-xs grid h-5 w-5 place-items-center rounded-full transition-colors hover:bg-on-secondary-container/20"
                >
                  <span aria-hidden="true" className="material-symbols-outlined text-base">
                    close
                  </span>
                </button>
              </span>
              {!loading && (
                <span className="text-label-md text-on-surface-variant">
                  {t("doctors.found", { count: doctors.length })}
                </span>
              )}
            </div>
          )}
          {error ? (
            <ErrorState error={error} onRetry={load} />
          ) : loading ? (
            <div className="grid grid-cols-1 gap-md sm:grid-cols-2 xl:grid-cols-3">
              <LoadingStatus />
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-64" />
              ))}
            </div>
          ) : doctors.length === 0 ? (
            <EmptyState icon="search_off" title={t("doctors.empty")} />
          ) : (
            <div className="grid grid-cols-1 gap-md sm:grid-cols-2 xl:grid-cols-3">
              {doctors.map((d) => (
                <DoctorCard key={d.id} doctor={d} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
