import { Link } from "react-router-dom";
import { useT } from "../lib/i18n.jsx";
import Card from "../components/Card.jsx";

export default function NotFound() {
  const t = useT();

  return (
    <div className="mx-auto max-w-lg px-md py-xl md:px-lg">
      <Card className="flex flex-col items-center p-lg text-center">
        <span aria-hidden="true" className="material-symbols-outlined text-6xl text-primary">
          troubleshoot
        </span>
        <p className="mt-sm text-5xl font-bold text-primary">404</p>
        <h1 className="mt-xs text-headline-md font-bold text-on-surface">{t("notFound.title")}</h1>
        <p className="mt-sm text-body-md text-on-surface-variant">{t("notFound.text")}</p>
        <div className="mt-lg flex w-full flex-col gap-sm sm:flex-row">
          <Link
            to="/"
            className="flex-1 rounded-xl bg-primary py-3 font-bold text-on-primary transition-all hover:opacity-90 active:scale-95"
          >
            {t("notFound.home")}
          </Link>
          <Link
            to="/doctors"
            className="flex-1 rounded-xl border border-primary py-3 font-bold text-primary transition-all hover:bg-primary hover:text-on-primary active:scale-95"
          >
            {t("notFound.toDoctors")}
          </Link>
        </div>
      </Card>
    </div>
  );
}
