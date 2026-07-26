import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { useT } from "../lib/i18n.jsx";
import LangSwitcher from "./LangSwitcher.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

export default function TopNav() {
  const t = useT();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const links = [
    { to: "/", label: t("nav.home"), end: true },
    { to: "/doctors", label: t("nav.doctors") },
    { to: "/booking", label: t("nav.booking") },
    { to: "/assistant", label: t("nav.assistant") },
  ];

  if (user?.role === "doctor") {
    links.push({ to: "/doctor/today", label: t("nav.doctorToday") });
    links.push({ to: "/doctor/schedule", label: t("nav.doctorSchedule") });
  } else if (user?.role === "admin") {
    links.push({ to: "/admin", label: t("nav.admin") });
  } else {
    links.push({ to: "/account", label: t("nav.account") });
  }

  const onSearch = (e) => {
    e.preventDefault();
    const value = query.trim();
    navigate(value ? `/doctors?specialization=${encodeURIComponent(value)}` : "/doctors");
  };

  const onLogout = () => {
    logout();
    navigate("/");
  };

  const linkClass = ({ isActive }) =>
    `text-label-md font-semibold transition-colors ${
      isActive
        ? "text-primary border-b-2 border-primary pb-1"
        : "text-on-surface-variant hover:text-primary"
    }`;

  return (
    <header className="sticky top-0 z-40 border-b border-outline-variant bg-surface/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-xs px-sm py-xs md:gap-md md:px-lg">
        <div className="flex min-w-0 items-center gap-md">
          <NavLink to="/" className="truncate text-xl font-bold text-primary md:text-headline-md">
            {t("brand.name")}
          </NavLink>
          <nav className="ml-lg hidden gap-md md:flex">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
                {l.label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="flex shrink-0 items-center gap-xs">
          <form onSubmit={onSearch} className="relative hidden items-center lg:flex">
            <span aria-hidden="true" className="material-symbols-outlined absolute left-3 text-on-surface-variant">
              search
            </span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("nav.searchPlaceholder")}
              aria-label={t("nav.searchPlaceholder")}
              className="w-56 rounded-full border border-outline-variant bg-surface-container py-2 pl-10 pr-4 text-body-md focus:border-primary focus:outline-none"
            />
          </form>

          <LangSwitcher />
          <ThemeToggle />

          {user ? (
            <button
              type="button"
              onClick={onLogout}
              className="flex h-11 items-center gap-1 rounded-full bg-primary px-md text-label-md font-semibold text-on-primary transition-all hover:bg-primary-container active:scale-95"
            >
              <span aria-hidden="true" className="material-symbols-outlined text-lg">logout</span>
              <span className="hidden sm:inline">{t("nav.logout")}</span>
            </button>
          ) : (
            <NavLink
              to="/login"
              className="flex h-11 items-center rounded-full bg-primary px-md text-label-md font-semibold text-on-primary transition-all hover:bg-primary-container active:scale-95"
            >
              {t("nav.login")}
            </NavLink>
          )}
        </div>
      </div>
    </header>
  );
}
