import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDepartments } from "../lib/api/departments.js";
import { searchDoctors } from "../lib/api/doctors.js";
import { getFilials } from "../lib/api/filials.js";
import { useT } from "../lib/i18n.jsx";
import { CARD_WIDTHS, filialPhoto, SCENE_WIDTHS } from "../lib/photos.js";
import Card from "../components/Card.jsx";
import ErrorState from "../components/ErrorState.jsx";
import LoadingStatus from "../components/LoadingStatus.jsx";
import Photo from "../components/Photo.jsx";
import Skeleton from "../components/Skeleton.jsx";

const FILIAL_ICONS = ["apartment", "local_hospital", "monitoring"];

export default function About() {
  const t = useT();
  const [doctors, setDoctors] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [filials, setFilials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return Promise.all([searchDoctors(), getDepartments(), getFilials()])
      .then(([doctorList, departmentList, filialList]) => {
        setDoctors(doctorList);
        setDepartments(departmentList);
        setFilials(filialList);
      })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // цифры считаем по факту, а не берём из макета: клиника растёт, а выдуманное
  // «48 врачей» под настоящим списком врачей выглядит как обман
  const specializations = new Set(doctors.map((doctor) => doctor.specialization).filter(Boolean));

  const stats = [
    {
      icon: "stethoscope",
      value: doctors.length,
      label: t("about.statsDoctors"),
      note: t("about.statsDoctorsNote"),
    },
    {
      icon: "apartment",
      value: departments.length,
      label: t("about.statsDepartments"),
      note: t("about.statsDepartmentsNote"),
    },
    {
      icon: "workspace_premium",
      value: specializations.size,
      label: t("about.statsSpecialties"),
      note: t("about.statsSpecialtiesNote"),
    },
  ];

  const advantages = [
    t("about.advantageProtocols"),
    t("about.advantageLab"),
    t("about.advantageRecords"),
  ];

  return (
    <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
      <section className="grid grid-cols-1 items-center gap-lg lg:grid-cols-2">
        <div>
          <p className="mb-xs text-label-md font-bold uppercase tracking-widest text-primary">
            {t("about.missionLabel")}
          </p>
          <h1 className="text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
            {t("about.title")}
          </h1>
          <p className="mt-md max-w-note text-body-lg text-on-surface-variant">
            {t("about.intro")}
          </p>
          <dl className="mt-lg flex flex-wrap gap-lg">
            <div>
              <dt className="text-headline-md font-bold text-primary">{t("about.yearsValue")}</dt>
              <dd className="text-label-md text-on-surface-variant">{t("about.yearsLabel")}</dd>
            </div>
            <div>
              <dt className="text-headline-md font-bold text-primary">
                {t("about.supportValue")}
              </dt>
              <dd className="text-label-md text-on-surface-variant">{t("about.supportLabel")}</dd>
            </div>
          </dl>
        </div>
        <div className="relative">
          <Photo
            base="/img/about/team"
            widths={SCENE_WIDTHS}
            sizes="(min-width: 1024px) 50vw, 100vw"
            alt={t("about.teamPhotoAlt")}
            icon="groups"
            eager
            width="1228"
            height="768"
            className="aspect-[8/5] w-full rounded-2xl"
          />
          <Card className="absolute bottom-md left-md max-w-note bg-primary p-sm text-on-primary">
            <p className="text-body-md font-bold">{t("about.trustTitle")}</p>
            <p className="text-label-md opacity-90">{t("about.trustText")}</p>
          </Card>
        </div>
      </section>

      <section className="mt-xl" aria-labelledby="about-numbers">
        <h2
          id="about-numbers"
          className="mb-md text-center text-headline-md font-bold text-on-surface"
        >
          {t("about.numbersTitle")}
        </h2>
        {error ? (
          <ErrorState error={error} onRetry={load} />
        ) : loading ? (
          <div className="grid grid-cols-1 gap-md sm:grid-cols-3">
            <LoadingStatus />
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-40" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-md sm:grid-cols-3">
            {stats.map((stat) => (
              <Card key={stat.label} className="p-md text-center">
                <span
                  aria-hidden="true"
                  className="material-symbols-outlined text-4xl text-primary"
                >
                  {stat.icon}
                </span>
                <p className="mt-xs text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
                  {stat.value}
                </p>
                <p className="text-body-md font-semibold text-on-surface">{stat.label}</p>
                <p className="mt-xs text-label-md text-on-surface-variant">{stat.note}</p>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="mt-xl" aria-labelledby="about-filials">
        <div className="mb-md flex items-end justify-between gap-sm">
          <div>
            <p className="text-label-md font-bold uppercase tracking-widest text-primary">
              {t("about.filialsLabel")}
            </p>
            <h2 id="about-filials" className="text-headline-md font-bold text-on-surface">
              {t("about.filialsTitle")}
            </h2>
          </div>
          <Link
            to="/doctors"
            className="shrink-0 text-label-md font-semibold text-primary hover:underline"
          >
            {t("about.allDoctors")}
          </Link>
        </div>
        {loading ? (
          <div className="grid grid-cols-1 gap-md md:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-72" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-md md:grid-cols-3">
            {filials.map((filial, index) => (
              <Card key={filial.id} className="card-lift overflow-hidden">
                <Photo
                  base={filialPhoto(index)}
                  widths={CARD_WIDTHS}
                  sizes="(min-width: 768px) 33vw, 100vw"
                  alt={t("about.filialPhotoAlt", { name: filial.name })}
                  icon={FILIAL_ICONS[index % FILIAL_ICONS.length]}
                  width="640"
                  height="400"
                  className="aspect-[8/5] w-full"
                />
                <div className="p-md">
                  <h3 className="text-body-lg font-bold text-on-surface">{filial.name}</h3>
                  <p className="mt-xs flex items-start gap-xs text-label-md text-on-surface-variant">
                    <span aria-hidden="true" className="material-symbols-outlined text-base">
                      location_on
                    </span>
                    <span>
                      {filial.address}, {filial.city}
                    </span>
                  </p>
                  <p className="mt-xs flex items-center gap-xs text-label-md text-on-surface-variant">
                    <span aria-hidden="true" className="material-symbols-outlined text-base">
                      schedule
                    </span>
                    {/* часы работы у филиалов в базе пока пустые (STUBS #4) —
                        подсказка честнее выдуманного «08:00 — 20:00» */}
                    <span>{filial.opening_hours || t("about.hoursUnknown")}</span>
                  </p>
                  <Link
                    to={`/doctors?filial_id=${filial.id}`}
                    className="mt-md inline-block rounded-xl bg-primary px-md py-2 text-label-md font-semibold text-on-primary transition-all hover:opacity-90"
                  >
                    {t("about.filialDoctors")}
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="mt-xl" aria-labelledby="about-story">
        <Card className="grid grid-cols-1 gap-lg p-md lg:grid-cols-2 lg:p-lg">
          <div>
            <h2 id="about-story" className="text-headline-md font-bold text-on-surface">
              {t("about.storyTitle")}
            </h2>
            <p className="mt-sm text-body-md text-on-surface-variant">{t("about.storyFirst")}</p>
            <p className="mt-sm text-body-md text-on-surface-variant">{t("about.storySecond")}</p>
            <ul className="mt-md flex flex-col gap-xs">
              {advantages.map((item) => (
                <li key={item} className="flex items-start gap-xs text-body-md text-on-surface">
                  <span
                    aria-hidden="true"
                    className="material-symbols-outlined text-primary text-xl"
                  >
                    check_circle
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="grid grid-cols-2 gap-sm">
            <Photo
              base="/img/about/story-1"
              widths={CARD_WIDTHS}
              sizes="(min-width: 1024px) 25vw, 50vw"
              alt={t("about.storyPhotoOneAlt")}
              icon="history"
              width="641"
              height="604"
              className="aspect-square w-full rounded-xl"
            />
            <Photo
              base="/img/about/story-2"
              widths={CARD_WIDTHS}
              sizes="(min-width: 1024px) 25vw, 50vw"
              alt={t("about.storyPhotoTwoAlt")}
              icon="stethoscope"
              width="641"
              height="604"
              className="mt-lg aspect-square w-full rounded-xl"
            />
          </div>
        </Card>
      </section>
    </div>
  );
}
