import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Accordion from "../components/Accordion.jsx";
import Card from "../components/Card.jsx";
import Photo from "../components/Photo.jsx";
import { getFilials } from "../lib/api/filials.js";
import { phone as formatPhone } from "../lib/format.js";
import { useT } from "../lib/i18n.jsx";
import { CARD_WIDTHS, SCENE_WIDTHS } from "../lib/photos.js";

const HOTLINE = "+992446000000";

const mapsUrl = (filial) =>
  `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    `${filial.name} ${filial.city} ${filial.address}`
  )}`;

export default function Faq() {
  const t = useT();
  const [filial, setFilial] = useState(null);

  // адрес и телефон берём из базы, а не из макета: филиалы переезжают,
  // а вшитая в вёрстку улица потом молча врёт
  useEffect(() => {
    getFilials()
      .then((list) => setFilial(list[0] || null))
      .catch(() => {});
  }, []);

  const items = [
    {
      question: t("faq.bookQuestion"),
      answer: (
        <>
          <p>{t("faq.bookAnswer")}</p>
          <div className="mt-sm flex flex-wrap gap-sm">
            <Link
              to="/doctors"
              className="rounded-xl bg-primary px-md py-2 text-label-md font-semibold text-on-primary transition-all hover:opacity-90"
            >
              {t("faq.bookOnline")}
            </Link>
            <Link
              to="/assistant"
              className="rounded-xl border border-outline-variant px-md py-2 text-label-md font-semibold text-on-surface transition-all hover:bg-surface-container"
            >
              {t("faq.askAssistant")}
            </Link>
          </div>
        </>
      ),
    },
    {
      question: t("faq.bringQuestion"),
      answer: (
        <>
          <p>{t("faq.bringAnswer")}</p>
          <ul className="mt-sm flex flex-col gap-xs">
            {[t("faq.bringPassport"), t("faq.bringRecords")].map((item) => (
              <li key={item} className="flex items-start gap-xs">
                <span aria-hidden="true" className="material-symbols-outlined text-xl text-primary">
                  check_circle
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </>
      ),
    },
    { question: t("faq.cancelQuestion"), answer: <p>{t("faq.cancelAnswer")}</p> },
    { question: t("faq.durationQuestion"), answer: <p>{t("faq.durationAnswer")}</p> },
    { question: t("faq.weekendQuestion"), answer: <p>{t("faq.weekendAnswer")}</p> },
  ];

  return (
    <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
      <section className="grid grid-cols-1 items-center gap-lg lg:grid-cols-2">
        <div>
          <p className="mb-xs text-label-md font-bold uppercase tracking-widest text-primary">
            {t("faq.label")}
          </p>
          <h1 className="text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
            {t("faq.title")}
          </h1>
          <p className="mt-md max-w-note text-body-lg text-on-surface-variant">{t("faq.intro")}</p>
        </div>
        <Photo
          base="/img/faq/consultation"
          widths={SCENE_WIDTHS}
          sizes="(min-width: 1024px) 50vw, 100vw"
          alt={t("faq.photoAlt")}
          icon="chat"
          eager
          width="1228"
          height="768"
          className="aspect-[8/5] w-full rounded-2xl"
        />
      </section>

      <div className="mt-xl grid grid-cols-1 gap-lg lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Accordion items={items} />
        </div>

        <div className="flex flex-col gap-md">
          <Card className="bg-primary p-md text-on-primary">
            <h2 className="text-body-lg font-bold">{t("faq.helpTitle")}</h2>
            <p className="mt-xs text-label-md opacity-90">{t("faq.helpText")}</p>
            <a
              href={`tel:${filial?.phone || HOTLINE}`}
              className="mt-md flex items-center gap-xs text-headline-md font-bold"
            >
              <span aria-hidden="true" className="material-symbols-outlined">call</span>
              {formatPhone(filial?.phone || HOTLINE)}
            </a>
            <Link
              to="/assistant"
              className="mt-md inline-flex items-center gap-xs rounded-xl bg-on-primary px-md py-2 text-label-md font-semibold text-primary transition-all hover:opacity-90"
            >
              <span aria-hidden="true" className="material-symbols-outlined text-lg">
                smart_toy
              </span>
              {t("faq.askAssistant")}
            </Link>
          </Card>

          <Card className="p-md">
            <p className="text-label-md font-bold uppercase tracking-widest text-primary">
              {t("faq.locationLabel")}
            </p>
            {/* в макете тут лежал скриншот Google Maps — чужие тайлы в сборку
                не кладём, поэтому снимок здания клиники и ссылка на настоящую карту */}
            <Photo
              base="/img/about/building"
              widths={CARD_WIDTHS}
              sizes="(min-width: 1024px) 25vw, 100vw"
              alt={t("faq.buildingAlt")}
              icon="apartment"
              width="640"
              height="400"
              className="mt-sm aspect-[8/5] w-full rounded-xl"
            />
            {filial && (
              <>
                <p className="mt-sm flex items-start gap-xs text-label-md text-on-surface-variant">
                  <span aria-hidden="true" className="material-symbols-outlined text-base">
                    pin_drop
                  </span>
                  <span>
                    {filial.name}, {filial.address}, {filial.city}
                  </span>
                </p>
                <div className="mt-sm flex flex-wrap gap-sm">
                  <a
                    href={mapsUrl(filial)}
                    target="_blank"
                    rel="noreferrer"
                    className="text-label-md font-semibold text-primary hover:underline"
                  >
                    {t("faq.openMap")}
                  </a>
                  <Link
                    to="/about"
                    className="text-label-md font-semibold text-primary hover:underline"
                  >
                    {t("faq.allBranches")}
                  </Link>
                </div>
              </>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
