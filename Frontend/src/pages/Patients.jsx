import Accordion from "../components/Accordion.jsx";
import Card from "../components/Card.jsx";
import Photo from "../components/Photo.jsx";
import { useT } from "../lib/i18n.jsx";
import { SCENE_WIDTHS } from "../lib/photos.js";

function Bullets({ items }) {
  return (
    <ul className="flex flex-col gap-xs">
      {items.map((item) => (
        <li key={item} className="flex items-start gap-xs">
          <span aria-hidden="true" className="material-symbols-outlined text-xl text-primary">
            check_circle
          </span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function Patients() {
  const t = useT();

  const preparation = [
    {
      question: t("patients.bloodTitle"),
      answer: (
        <Bullets
          items={[
            t("patients.bloodFasting"),
            t("patients.bloodAlcohol"),
            t("patients.bloodWater"),
            t("patients.bloodSmoking"),
          ]}
        />
      ),
    },
    {
      question: t("patients.biochemTitle"),
      answer: (
        <>
          <p className="mb-sm">{t("patients.biochemIntro")}</p>
          <Bullets
            items={[
              t("patients.biochemFasting"),
              t("patients.biochemDrugs"),
              t("patients.biochemRest"),
            ]}
          />
        </>
      ),
    },
    {
      question: t("patients.ultrasoundTitle"),
      answer: (
        <Bullets
          items={[
            t("patients.ultrasoundDiet"),
            t("patients.ultrasoundFasting"),
            t("patients.ultrasoundAfternoon"),
          ]}
        />
      ),
    },
  ];

  const rights = [
    { icon: "verified", title: t("patients.rightPrivacy"), text: t("patients.rightPrivacyText") },
    { icon: "info", title: t("patients.rightInformed"), text: t("patients.rightInformedText") },
    { icon: "person", title: t("patients.rightChoice"), text: t("patients.rightChoiceText") },
    { icon: "close", title: t("patients.rightRefusal"), text: t("patients.rightRefusalText") },
  ];

  return (
    <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
      <section className="grid grid-cols-1 items-center gap-lg lg:grid-cols-2">
        <div>
          <h1 className="text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
            {t("patients.title")}
          </h1>
          <p className="mt-sm max-w-note text-body-lg text-on-surface-variant">
            {t("patients.intro")}
          </p>
        </div>
        <Photo
          base="/img/patients/consultation"
          widths={SCENE_WIDTHS}
          sizes="(min-width: 1024px) 50vw, 100vw"
          alt={t("patients.photoAlt")}
          icon="clinical_notes"
          eager
          width="1228"
          height="768"
          className="aspect-[8/5] w-full rounded-2xl"
        />
      </section>

      <div className="mt-xl grid grid-cols-1 gap-lg lg:grid-cols-3">
        <div className="flex flex-col gap-xl lg:col-span-2">
          <section aria-labelledby="patients-preparation">
            <h2
              id="patients-preparation"
              className="mb-md flex items-center gap-xs text-headline-md font-bold text-on-surface"
            >
              <span aria-hidden="true" className="material-symbols-outlined text-primary">
                troubleshoot
              </span>
              {t("patients.preparationTitle")}
            </h2>
            <Accordion items={preparation} defaultOpen={-1} />
          </section>

          <section aria-labelledby="patients-rights">
            <h2
              id="patients-rights"
              className="mb-md flex items-center gap-xs text-headline-md font-bold text-on-surface"
            >
              <span aria-hidden="true" className="material-symbols-outlined text-primary">
                task_alt
              </span>
              {t("patients.rightsTitle")}
            </h2>
            <div className="grid grid-cols-1 gap-md sm:grid-cols-2">
              {rights.map((right) => (
                <Card key={right.title} className="p-md">
                  <span
                    aria-hidden="true"
                    className="material-symbols-outlined text-2xl text-primary"
                  >
                    {right.icon}
                  </span>
                  <h3 className="mt-xs text-body-lg font-bold text-on-surface">{right.title}</h3>
                  <p className="mt-xs text-body-md text-on-surface-variant">{right.text}</p>
                </Card>
              ))}
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-md">
          {/* В макете тут были логотипы Bupa, Allianz и Cigna. Это настоящие компании,
              и заявлять партнёрство, которого нет, нельзя — блок оставлен нейтральным,
              со ссылкой на регистратуру, где скажут актуальный список. */}
          <Card className="p-md">
            <h2 className="flex items-center gap-xs text-body-lg font-bold text-on-surface">
              <span aria-hidden="true" className="material-symbols-outlined text-primary">
                workspace_premium
              </span>
              {t("patients.insuranceTitle")}
            </h2>
            <p className="mt-xs text-body-md text-on-surface-variant">
              {t("patients.insuranceText")}
            </p>
            <a
              href="tel:+992446000000"
              className="mt-md inline-block rounded-xl border border-outline-variant px-md py-2 text-label-md font-semibold text-on-surface transition-all hover:bg-surface-container"
            >
              {t("patients.insuranceAsk")}
            </a>
          </Card>

          <Card className="bg-primary p-md text-on-primary">
            <h2 className="text-body-lg font-bold">{t("patients.helpTitle")}</h2>
            <p className="mt-xs text-label-md opacity-90">{t("patients.helpText")}</p>
            <a
              href="tel:+992446000000"
              className="mt-md flex items-center gap-xs text-headline-md font-bold"
            >
              <span aria-hidden="true" className="material-symbols-outlined">call</span>
              +992 44 600 00 00
            </a>
          </Card>

          <Card className="p-md">
            <h2 className="text-body-lg font-bold text-on-surface">{t("patients.bringTitle")}</h2>
            <div className="mt-sm text-body-md text-on-surface-variant">
              <Bullets
                items={[
                  t("patients.bringPassport"),
                  t("patients.bringInsurance"),
                  t("patients.bringResults"),
                  t("patients.bringDrugs"),
                ]}
              />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
