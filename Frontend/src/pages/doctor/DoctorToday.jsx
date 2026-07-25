import { useT } from "../../lib/i18n.jsx";

export default function DoctorToday() {
  const t = useT();

  return (
    <div className="mx-auto max-w-5xl px-sm py-md md:px-lg">
      <h1 className="mb-md text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
        {t("doctorCabinet.todayTitle")}
      </h1>
    </div>
  );
}
