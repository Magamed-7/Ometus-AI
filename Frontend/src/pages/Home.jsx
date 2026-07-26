import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getFilials } from "../lib/api/filials.js";
import { searchDoctors } from "../lib/api/doctors.js";
import { phone } from "../lib/format.js";
import { useT } from "../lib/i18n.jsx";
import Card from "../components/Card.jsx";
import ErrorState from "../components/ErrorState.jsx";
import LoadingStatus from "../components/LoadingStatus.jsx";
import Skeleton from "../components/Skeleton.jsx";

const mapsUrl = (f) =>
  `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    `${f.name} ${f.city} ${f.address}`
  )}`;

const initials = (name) =>
  (name || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

const SPECIALIZATIONS = [
  "Кардиолог",
  "Невролог",
  "Педиатр",
  "Терапевт",
  "Хирург",
  "Офтальмолог",
  "ЛОР",
  "Гастроэнтеролог",
  "Эндокринолог",
  "Дерматолог",
  "Уролог",
  "Гинеколог",
  "Ортопед",
];

export default function Home() {
  const t = useT();
  const navigate = useNavigate();
  const [filials, setFilials] = useState([]);
  const [filialsLoading, setFilialsLoading] = useState(true);
  const [filialsError, setFilialsError] = useState(false);
  const [doctors, setDoctors] = useState([]);
  const [doctorsLoading, setDoctorsLoading] = useState(true);
  const [doctorsError, setDoctorsError] = useState(false);
  const [spec, setSpec] = useState("");
  const [filialId, setFilialId] = useState("");
  const [date, setDate] = useState("");

  const loadFilials = useCallback(() => {
    setFilialsLoading(true);
    setFilialsError(false);
    return getFilials()
      .then(setFilials)
      .catch((e) => setFilialsError(e))
      .finally(() => setFilialsLoading(false));
  }, []);

  const loadDoctors = useCallback(() => {
    setDoctorsLoading(true);
    setDoctorsError(false);
    return searchDoctors()
      .then((data) => setDoctors(data.slice(0, 6)))
      .catch((e) => setDoctorsError(e))
      .finally(() => setDoctorsLoading(false));
  }, []);

  useEffect(() => {
    loadFilials();
    loadDoctors();
  }, [loadFilials, loadDoctors]);

  const onSearch = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (spec) params.set("specialization", spec);
    if (filialId) params.set("filial_id", filialId);
    if (date) params.set("date", date);
    const qs = params.toString();
    navigate(qs ? `/doctors?${qs}` : "/doctors");
  };

  return (
    <div>
      <section className="relative overflow-hidden bg-surface-container-lowest py-xl md:py-32">
        <div className="hero-pattern pointer-events-none absolute inset-0" />
        <div className="relative z-10 mx-auto max-w-7xl px-lg">
          <div className="flex flex-col items-center gap-lg md:flex-row">
            <div className="flex-1 text-center md:text-left">
              <span className="mb-md inline-block rounded-full bg-secondary-container px-4 py-1 text-label-md font-semibold text-on-secondary-container">
                {t("home.badge")}
              </span>
              <h1 className="mb-sm text-headline-lg-mobile leading-tight text-on-surface md:text-headline-xl">
                {t("home.title")}
              </h1>
              <p className="mb-xl max-w-hero text-body-lg text-on-surface-variant">
                {t("home.subtitle")}
              </p>

              <form
                onSubmit={onSearch}
                className="flex flex-col items-stretch gap-xs rounded-xl border border-outline-variant bg-surface-container-lowest p-xs shadow-lg md:flex-row md:items-center md:p-sm"
              >
                <div className="grid flex-1 grid-cols-1 gap-xs md:grid-cols-3">
                  <div className="relative">
                    <span aria-hidden="true" className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
                      stethoscope
                    </span>
                    <select
                      value={spec}
                      onChange={(e) => setSpec(e.target.value)}
                      aria-label={t("home.specialty")}
                      className="w-full appearance-none rounded-lg bg-surface-container-low py-3 pl-10 pr-4 text-body-md focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="">{t("home.specialty")}</option>
                      {SPECIALIZATIONS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="relative">
                    <span aria-hidden="true" className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
                      location_on
                    </span>
                    <select
                      value={filialId}
                      onChange={(e) => setFilialId(e.target.value)}
                      aria-label={t("home.filial")}
                      className="w-full appearance-none rounded-lg bg-surface-container-low py-3 pl-10 pr-4 text-body-md focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="">{t("home.filial")}</option>
                      {filials.map((f) => (
                        <option key={f.id} value={f.id}>
                          {f.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="relative">
                    <span aria-hidden="true" className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
                      calendar_month
                    </span>
                    <input
                      type="date"
                      value={date}
                      onChange={(e) => setDate(e.target.value)}
                      aria-label={t("home.date")}
                      className="w-full rounded-lg bg-surface-container-low py-3 pl-10 pr-4 text-body-md focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="flex items-center justify-center gap-2 rounded-lg bg-primary px-lg py-3 font-bold text-on-primary transition-colors hover:bg-primary-container md:py-4"
                >
                  <span aria-hidden="true" className="material-symbols-outlined">search</span>
                  {t("home.find")}
                </button>
              </form>
            </div>

            <div className="relative hidden flex-1 md:block">
              <div className="relative h-[460px] w-full overflow-hidden rounded-3xl bg-gradient-to-br from-primary to-primary-container shadow-2xl">
                <div className="absolute inset-0 grid place-items-center">
                  <span aria-hidden="true" className="material-symbols-outlined text-[160px] text-on-primary/90">
                    health_and_safety
                  </span>
                </div>
              </div>
              <div className="animate-bounce-slow absolute -bottom-6 -left-6 flex items-center gap-sm rounded-2xl border border-outline-variant bg-surface-container-lowest p-md shadow-xl">
                <div className="grid h-12 w-12 place-items-center rounded-full bg-primary-container text-on-primary-container">
                  <span aria-hidden="true" className="material-symbols-outlined">verified</span>
                </div>
                <div>
                  <p className="font-bold text-on-surface">{t("home.badgeSpecialists")}</p>
                  <p className="text-label-md text-on-surface-variant">{t("home.badgeCategory")}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-lg py-xl">
        <div className="mb-lg flex items-end justify-between gap-sm">
          <div>
            <h2 className="mb-xs text-headline-lg-mobile text-on-surface md:text-headline-lg">
              {t("home.branchesTitle")}
            </h2>
            <p className="text-body-md text-on-surface-variant">{t("home.branchesSubtitle")}</p>
          </div>
        </div>
        {filialsError ? (
          <ErrorState error={filialsError} onRetry={loadFilials} />
        ) : (
        <div className="grid grid-cols-1 gap-md md:grid-cols-3">
          {filialsLoading && <LoadingStatus />}
          {filialsLoading
            ? [0, 1, 2].map((i) => <Skeleton key={i} className="h-72" />)
            : filials.map((f) => (
                <Card key={f.id} className="group overflow-hidden transition-all hover:shadow-xl">
                  <div className="relative h-40 overflow-hidden bg-gradient-to-br from-primary to-primary-container">
                    <div className="absolute inset-0 grid place-items-center">
                      <span aria-hidden="true" className="material-symbols-outlined text-6xl text-on-primary/90">
                        apartment
                      </span>
                    </div>
                  </div>
                  <div className="p-md">
                    <h3 className="mb-xs text-headline-md font-semibold text-on-surface">{f.name}</h3>
                    <div className="mb-md flex items-start gap-xs text-on-surface-variant">
                      <span aria-hidden="true" className="material-symbols-outlined mt-0.5 text-base text-primary">
                        location_on
                      </span>
                      <span className="text-body-md">
                        {f.city}, {f.address}
                      </span>
                    </div>
                    {/* STUBS #4: 26.07.2026 в `filials` появилось поле `opening_hours`, но у всех
                        филиалов оно пока пустое. Показываем настоящие часы, если они заполнены,
                        и подсказку «уточняйте» — если нет. Выдуманное «08:00 – 20:00, без
                        выходных», которое стояло здесь раньше, не возвращаем: по нему пациент
                        мог приехать к закрытым дверям. */}
                    <div className="mb-lg flex items-center gap-sm text-label-md">
                      <span className="flex items-center gap-1 text-on-surface-variant">
                        <span
                          aria-hidden="true"
                          className="material-symbols-outlined text-sm text-primary"
                        >
                          schedule
                        </span>
                        {f.opening_hours || t("home.hoursUnknown")}
                      </span>
                      {f.phone && (
                        <>
                          <span className="text-outline-variant">|</span>
                          <a
                            href={`tel:${f.phone}`}
                            className="text-on-surface-variant transition-colors hover:text-primary"
                          >
                            {phone(f.phone)}
                          </a>
                        </>
                      )}
                    </div>
                    <a
                      href={mapsUrl(f)}
                      target="_blank"
                      rel="noreferrer"
                      className="flex w-full items-center justify-center gap-2 rounded-xl border border-primary py-3 font-bold text-primary transition-all hover:bg-primary hover:text-on-primary"
                    >
                      <span aria-hidden="true" className="material-symbols-outlined text-lg">directions</span>
                      {t("home.route")}
                    </a>
                  </div>
                </Card>
              ))}
        </div>
        )}
      </section>

      <section className="bg-surface-container-low py-xl">
        <div className="mx-auto max-w-7xl px-lg">
          <div className="mb-lg flex flex-col justify-between gap-sm md:flex-row md:items-end">
            <div>
              <h2 className="mb-xs text-headline-lg-mobile text-on-surface md:text-headline-lg">
                {t("home.doctorsTitle")}
              </h2>
              <p className="text-body-md text-on-surface-variant">{t("home.doctorsSubtitle")}</p>
            </div>
            <Link
              to="/doctors"
              className="self-start rounded-full border border-outline bg-surface px-md py-2 text-label-md font-semibold text-on-surface transition-colors hover:bg-surface-variant md:self-auto"
            >
              {t("home.allDoctors")}
            </Link>
          </div>
          {doctorsError ? (
            <ErrorState error={doctorsError} onRetry={loadDoctors} />
          ) : (
          <div className="grid grid-cols-1 gap-md sm:grid-cols-2 md:grid-cols-3">
            {doctorsLoading && <LoadingStatus />}
            {doctorsLoading
              ? [0, 1, 2].map((i) => <Skeleton key={i} className="h-72" />)
              : doctors.map((d) => (
                  <Card key={d.id} className="flex flex-col items-center p-md text-center">
                    <div className="mb-md grid h-28 w-28 place-items-center rounded-full border-4 border-surface-container bg-primary-container text-on-primary-container">
                      <span className="text-headline-lg font-bold">{initials(d.full_name)}</span>
                    </div>
                    <h4 className="mb-base text-headline-md font-semibold text-on-surface">
                      {d.full_name}
                    </h4>
                    <p className="mb-lg text-label-md font-bold uppercase tracking-wider text-primary">
                      {d.specialization}
                    </p>
                    <Link
                      to={`/booking/${d.id}`}
                      className="mt-auto w-full rounded-xl bg-primary py-3 font-bold text-on-primary transition-all hover:bg-primary-container hover:shadow-lg"
                    >
                      {t("home.book")}
                    </Link>
                  </Card>
                ))}
          </div>
          )}
        </div>
      </section>
    </div>
  );
}
