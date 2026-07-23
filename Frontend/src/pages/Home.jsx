import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useT } from "../lib/i18n.jsx";

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
  const [spec, setSpec] = useState("");
  const [filialId, setFilialId] = useState("");
  const [date, setDate] = useState("");

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
              <p className="mb-xl max-w-xl text-body-lg text-on-surface-variant">
                {t("home.subtitle")}
              </p>

              <form
                onSubmit={onSearch}
                className="flex flex-col items-stretch gap-xs rounded-xl border border-outline-variant bg-surface-container-lowest p-xs shadow-lg md:flex-row md:items-center md:p-sm"
              >
                <div className="grid flex-1 grid-cols-1 gap-xs md:grid-cols-3">
                  <div className="relative">
                    <span className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
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
                    <span className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
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
                    <span className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">
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
                  <span className="material-symbols-outlined">search</span>
                  {t("home.find")}
                </button>
              </form>
            </div>

            <div className="relative hidden flex-1 md:block">
              <div className="relative h-[460px] w-full overflow-hidden rounded-3xl bg-gradient-to-br from-primary to-primary-container shadow-2xl">
                <div className="absolute inset-0 grid place-items-center">
                  <span className="material-symbols-outlined text-[160px] text-on-primary/90">
                    health_and_safety
                  </span>
                </div>
              </div>
              <div className="animate-bounce-slow absolute -bottom-6 -left-6 flex items-center gap-sm rounded-2xl border border-outline-variant bg-surface-container-lowest p-md shadow-xl">
                <div className="grid h-12 w-12 place-items-center rounded-full bg-primary-container text-on-primary-container">
                  <span className="material-symbols-outlined">verified</span>
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
    </div>
  );
}
