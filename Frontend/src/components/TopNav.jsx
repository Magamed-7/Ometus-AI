import { useEffect, useRef, useState } from "react";
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
  const headerRef = useRef(null);

  // высота шапки не константа: вторая строка появляется только с md, пунктов
  // в ней у врача больше, чем у пациента, а в узком окне добавляется полоска
  // прокрутки. Липким сайдбарам нужно точное число, поэтому меряем и отдаём
  // его в CSS, а не подбираем на глаз
  useEffect(() => {
    const element = headerRef.current;
    if (!element) return;

    const observer = new ResizeObserver(([entry]) => {
      const height = Math.round(entry.target.getBoundingClientRect().height);
      document.documentElement.style.setProperty("--header-h", `${height}px`);
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  // запись и ассистент — только для пациента: врач и админ записаться не могут,
  // а на странице ассистента их встречала плашка «только для пациентов».
  // У сотрудников свой ассистент — в «Приёме сегодня» и в аналитике
  const isStaff = user?.role === "doctor" || user?.role === "admin";

  const links = [
    { to: "/", label: t("nav.home"), end: true },
    { to: "/about", label: t("nav.about") },
    { to: "/services", label: t("nav.services") },
    { to: "/doctors", label: t("nav.doctors") },
  ];

  if (!isStaff) {
    links.push({ to: "/booking", label: t("nav.booking") });
    links.push({ to: "/assistant", label: t("nav.assistant") });
  }

  if (user?.role === "doctor") {
    links.push({ to: "/doctor/today", label: t("nav.doctorToday") });
    links.push({ to: "/doctor/schedule", label: t("nav.doctorSchedule") });
  } else if (user?.role === "admin") {
    links.push({ to: "/admin", label: t("nav.admin") });
  } else {
    links.push({ to: "/account", label: t("nav.account") });
  }

  // ищем через `search`, а не `specialization`: поле подписано «Поиск врача»,
  // и по фамилии оно обязано находить врача, а не только по названию специальности
  const onSearch = (e) => {
    e.preventDefault();
    const value = query.trim();
    navigate(value ? `/doctors?search=${encodeURIComponent(value)}` : "/doctors");
  };

  const onLogout = () => {
    logout();
    navigate("/");
  };

  // whitespace-nowrap обязателен: без него «О нас» и «Услуги и цены» при нехватке
  // места ломались по словам и текст шёл сверху вниз
  const linkClass = ({ isActive }) =>
    `whitespace-nowrap border-b-2 pb-1 text-label-md font-semibold transition-colors ${
      isActive
        ? "border-primary text-primary"
        : "border-transparent text-on-surface-variant hover:text-primary"
    }`;

  return (
    <header
      ref={headerRef}
      className="sticky top-0 z-40 border-b border-outline-variant bg-surface/95 backdrop-blur"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-sm px-sm py-1 md:px-lg">
        {/* бренд не сжимается и не обрезается: раньше на нём стоял truncate,
            и «Ometus Clinic» превращался в «Omet…» */}
        <NavLink
          to="/"
          className="shrink-0 whitespace-nowrap text-xl font-bold text-primary md:text-headline-md"
        >
          {t("brand.name")}
        </NavLink>

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
              aria-label={t("nav.logout")}
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

      {/* Навигация вынесена во вторую строку. В один ряд с брендом, поиском и кнопкой
          она не помещалась: у пациента это 7 пунктов, у врача 8, и при нехватке места
          подписи ломались по вертикали. Отдельная строка держит любое их число,
          а на телефоне она скрыта — там за навигацию отвечает нижняя панель.
          Обе строки прижаты по вертикали: вместе они должны укладываться в 96px,
          на которые рассчитаны `sticky top-24` у сайдбаров записи, врачей и кабинета. */}
      <nav
        aria-label={t("nav.sections")}
        className="nav-scroll hidden overflow-x-auto border-t border-outline-variant/60 md:block"
      >
        <div className="mx-auto flex max-w-7xl items-center gap-md px-sm py-1 md:px-lg lg:gap-lg">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
              {l.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </header>
  );
}
