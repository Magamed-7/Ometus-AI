import { useT } from "../lib/i18n.jsx";
import { useTheme } from "../lib/theme.jsx";

export default function ThemeToggle() {
  const t = useT();
  const { theme, toggle } = useTheme();

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === "dark" ? t("nav.themeLight") : t("nav.themeDark")}
      className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-outline-variant text-on-surface-variant transition-colors hover:border-primary hover:text-primary"
    >
      <span aria-hidden="true" className="material-symbols-outlined text-xl">
        {theme === "dark" ? "light_mode" : "dark_mode"}
      </span>
    </button>
  );
}
