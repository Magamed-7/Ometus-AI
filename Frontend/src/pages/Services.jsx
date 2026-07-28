import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDepartments } from "../lib/api/departments.js";
import { getFilials } from "../lib/api/filials.js";
import { getServices } from "../lib/api/services.js";
import { useT } from "../lib/i18n.jsx";
import { SCENE_WIDTHS } from "../lib/photos.js";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import LoadingStatus from "../components/LoadingStatus.jsx";
import Photo from "../components/Photo.jsx";
import Skeleton from "../components/Skeleton.jsx";

const CATEGORIES = [
  { key: "consultation", icon: "stethoscope" },
  { key: "diagnostics", icon: "troubleshoot" },
  { key: "analysis", icon: "science" },
  { key: "treatment", icon: "health_and_safety" },
];

function money(value, currency, t) {
  // цена приходит строкой из Numeric — приводим к числу только для показа,
  // считать в браузере ничего не нужно
  const amount = Number(value);
  // сомони пишем словом, остальные валюты — кодом: выдумывать перевод
  // для валюты, которой в базе ещё не было, не за чем
  const label = currency === "TJS" ? t("services.currencyTJS") : currency;
  return Number.isFinite(amount) ? `${amount.toFixed(0)} ${label}` : `${value} ${label}`;
}

export default function Services() {
  const t = useT();
  const [services, setServices] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [filials, setFilials] = useState([]);
  const [category, setCategory] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [filialId, setFilialId] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    getDepartments()
      .then(setDepartments)
      .catch(() => {});
    getFilials()
      .then(setFilials)
      .catch(() => {});
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return getServices({
      category,
      department_id: departmentId,
      filial_id: filialId,
      search: search.trim(),
    })
      .then(setServices)
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [category, departmentId, filialId, search]);

  useEffect(() => {
    const timer = setTimeout(load, search ? 300 : 0);
    return () => clearTimeout(timer);
  }, [load, search]);

  const groups = CATEGORIES.map((item) => ({
    ...item,
    title: t(`services.category_${item.key}`),
    rows: services.filter((service) => service.category === item.key),
  })).filter((group) => group.rows.length > 0);

  return (
    <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
      <section className="grid grid-cols-1 items-center gap-lg lg:grid-cols-2">
        <div>
          <h1 className="text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
            {t("services.title")}
          </h1>
          <p className="mt-sm max-w-note text-body-lg text-on-surface-variant">
            {t("services.intro")}
          </p>
        </div>
        <Photo
          base="/img/services/reception"
          widths={SCENE_WIDTHS}
          sizes="(min-width: 1024px) 50vw, 100vw"
          alt={t("services.photoAlt")}
          icon="local_hospital"
          eager
          width="1228"
          height="768"
          className="aspect-[8/5] w-full rounded-2xl"
        />
      </section>

      <Card className="mt-lg flex flex-wrap items-end gap-sm p-md">
        <label className="flex flex-col gap-0.5">
          <span className="text-label-md text-on-surface-variant">{t("services.byFilial")}</span>
          <select
            value={filialId}
            onChange={(event) => setFilialId(event.target.value)}
            className="rounded-lg border border-outline-variant bg-surface-container-lowest px-sm py-2 text-body-md text-on-surface"
          >
            <option value="">{t("services.allFilials")}</option>
            {filials.map((filial) => (
              <option key={filial.id} value={filial.id}>
                {filial.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-0.5">
          <span className="text-label-md text-on-surface-variant">
            {t("services.byDepartment")}
          </span>
          <select
            value={departmentId}
            onChange={(event) => setDepartmentId(event.target.value)}
            className="rounded-lg border border-outline-variant bg-surface-container-lowest px-sm py-2 text-body-md text-on-surface"
          >
            <option value="">{t("services.allDepartments")}</option>
            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-1 flex-col gap-0.5">
          <span className="text-label-md text-on-surface-variant">{t("services.search")}</span>
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t("services.searchPlaceholder")}
            className="rounded-lg border border-outline-variant bg-surface-container-lowest px-sm py-2 text-body-md text-on-surface"
          />
        </label>
      </Card>

      <div className="mt-lg grid grid-cols-1 gap-lg lg:grid-cols-4">
        <nav aria-label={t("services.categories")} className="lg:col-span-1">
          <Card className="p-sm">
            <p className="px-sm py-xs text-label-md font-bold uppercase tracking-widest text-primary">
              {t("services.categories")}
            </p>
            <button
              type="button"
              onClick={() => setCategory("")}
              aria-current={category === "" ? "true" : undefined}
              className={`flex w-full items-center gap-xs rounded-lg px-sm py-2 text-left text-body-md transition-colors ${
                category === ""
                  ? "bg-primary-container text-on-primary-container font-semibold"
                  : "text-on-surface hover:bg-surface-container"
              }`}
            >
              <span aria-hidden="true" className="material-symbols-outlined text-lg">
                filter_list
              </span>
              {t("services.allCategories")}
            </button>
            {CATEGORIES.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setCategory(item.key)}
                aria-current={category === item.key ? "true" : undefined}
                className={`flex w-full items-center gap-xs rounded-lg px-sm py-2 text-left text-body-md transition-colors ${
                  category === item.key
                    ? "bg-primary-container text-on-primary-container font-semibold"
                    : "text-on-surface hover:bg-surface-container"
                }`}
              >
                <span aria-hidden="true" className="material-symbols-outlined text-lg">
                  {item.icon}
                </span>
                {t(`services.category_${item.key}`)}
              </button>
            ))}
          </Card>
        </nav>

        <div className="lg:col-span-3">
          {error ? (
            <ErrorState error={error} onRetry={load} />
          ) : loading ? (
            <div className="flex flex-col gap-sm">
              <LoadingStatus />
              {[0, 1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : groups.length === 0 ? (
            <EmptyState
              icon="search_off"
              title={t("services.emptyTitle")}
              text={t("services.emptyText")}
            />
          ) : (
            <div className="flex flex-col gap-lg">
              {groups.map((group) => (
                <section key={group.key} aria-labelledby={`group-${group.key}`}>
                  <h2
                    id={`group-${group.key}`}
                    className="mb-sm flex items-center gap-xs text-headline-md font-bold text-on-surface"
                  >
                    <span aria-hidden="true" className="material-symbols-outlined text-primary">
                      {group.icon}
                    </span>
                    {group.title}
                  </h2>
                  <div className="flex flex-col gap-sm">
                    {group.rows.map((service) => (
                      <Card
                        key={service.id}
                        className="flex flex-col gap-sm p-md sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0">
                          <h3 className="text-body-lg font-semibold text-on-surface">
                            {service.name}
                          </h3>
                          {service.description && (
                            <p className="mt-0.5 text-label-md text-on-surface-variant">
                              {service.description}
                            </p>
                          )}
                          {service.duration_minutes && (
                            <p className="mt-xs flex items-center gap-xs text-label-md text-on-surface-variant">
                              <span
                                aria-hidden="true"
                                className="material-symbols-outlined text-base"
                              >
                                schedule
                              </span>
                              {t("services.minutes", { count: service.duration_minutes })}
                            </p>
                          )}
                        </div>
                        <div className="flex shrink-0 items-center gap-md">
                          <p className="text-headline-md font-bold text-on-surface">
                            {money(service.price, service.currency, t)}
                          </p>
                          <Link
                            to="/doctors"
                            className="rounded-xl bg-primary px-md py-2 text-label-md font-semibold text-on-primary transition-all hover:opacity-90"
                          >
                            {t("services.book")}
                          </Link>
                        </div>
                      </Card>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      </div>

      <Card className="mt-xl bg-primary p-lg text-center text-on-primary">
        <h2 className="text-headline-md font-bold">{t("services.ctaTitle")}</h2>
        <p className="mx-auto mt-xs max-w-note text-body-md opacity-90">{t("services.ctaText")}</p>
        <div className="mt-md flex flex-wrap justify-center gap-sm">
          <Link
            to="/assistant"
            className="rounded-xl bg-on-primary px-lg py-3 font-semibold text-primary transition-all hover:opacity-90"
          >
            {t("services.ctaAssistant")}
          </Link>
          <a
            href="tel:+992446000000"
            className="rounded-xl border border-on-primary/40 px-lg py-3 font-semibold text-on-primary transition-all hover:bg-on-primary/10"
          >
            {t("services.ctaCall")}
          </a>
        </div>
      </Card>
    </div>
  );
}
