import { Link } from "react-router-dom";
import { useT } from "../lib/i18n.jsx";

export default function Footer() {
  const t = useT();

  return (
    <footer className="border-t border-outline-variant bg-surface-container-low">
      <div className="mx-auto flex max-w-7xl flex-col justify-between gap-lg px-lg py-xl md:flex-row">
        <div className="max-w-note">
          <span className="mb-sm block text-headline-md font-bold text-primary">
            {t("brand.name")}
          </span>
          <p className="mb-md text-body-md text-on-surface-variant">{t("footer.tagline")}</p>
          <p className="text-label-md font-semibold text-on-surface">{t("footer.rights")}</p>
        </div>

        <div className="flex flex-col gap-xs">
          <p className="mb-xs text-label-md font-bold text-on-surface">{t("footer.info")}</p>
          <Link to="/about" className="text-label-md text-on-surface-variant hover:text-primary">
            {t("nav.about")}
          </Link>
          <Link to="/services" className="text-label-md text-on-surface-variant hover:text-primary">
            {t("services.title")}
          </Link>
          <Link to="/doctors" className="text-label-md text-on-surface-variant hover:text-primary">
            {t("nav.doctors")}
          </Link>
          <Link to="/booking" className="text-label-md text-on-surface-variant hover:text-primary">
            {t("nav.booking")}
          </Link>
          <a href="#" className="text-label-md text-on-surface-variant hover:text-primary">
            {t("footer.privacy")}
          </a>
          <Link to="/patients" className="text-label-md text-on-surface-variant hover:text-primary">
            {t("patients.title")}
          </Link>
          <Link to="/reviews" className="text-label-md text-on-surface-variant hover:text-primary">
            {t("reviews.title")}
          </Link>
          <Link to="/faq" className="text-label-md text-on-surface-variant hover:text-primary">
            {t("footer.faq")}
          </Link>
        </div>

        <div className="flex flex-col gap-sm">
          <p className="text-label-md font-bold text-on-surface">{t("footer.hotline")}</p>
          <a href="tel:+992446000000" className="text-headline-md font-bold text-primary">
            +992 44 600 00 00
          </a>
          <div className="flex gap-sm">
            <a
              href="tel:+992446000000"
              aria-label={t("footer.hotline")}
              className="grid h-10 w-10 place-items-center rounded-full border border-outline-variant bg-surface-container-lowest text-primary transition-colors hover:bg-primary-container hover:text-on-primary-container"
            >
              <span aria-hidden="true" className="material-symbols-outlined text-lg">call</span>
            </a>
            <a
              href="mailto:info@ometus.tj"
              aria-label={t("footer.contacts")}
              className="grid h-10 w-10 place-items-center rounded-full border border-outline-variant bg-surface-container-lowest text-primary transition-colors hover:bg-primary-container hover:text-on-primary-container"
            >
              <span aria-hidden="true" className="material-symbols-outlined text-lg">mail</span>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
