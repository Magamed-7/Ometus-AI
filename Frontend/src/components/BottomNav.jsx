import { NavLink } from "react-router-dom";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { useT } from "../lib/i18n.jsx";

export default function BottomNav() {
  const t = useT();
  const { user } = useAuth();

  const items = [
    { to: "/", label: t("nav.home"), icon: "home_health", end: true },
    { to: "/doctors", label: t("nav.doctors"), icon: "medical_services" },
    { to: "/booking", label: t("nav.booking"), icon: "calendar_add_on" },
    { to: "/assistant", label: t("nav.assistant"), icon: "smart_toy" },
  ];

  if (user?.role === "doctor") {
    items.push({ to: "/doctor/today", label: t("nav.doctorToday"), icon: "event_available" });
  } else if (user?.role === "admin") {
    items.push({ to: "/admin/filials", label: t("nav.admin"), icon: "admin_panel_settings" });
  } else {
    items.push({ to: "/account", label: t("nav.account"), icon: "account_circle" });
  }

  return (
    <nav className="fixed bottom-0 left-0 z-40 flex w-full items-stretch gap-0.5 rounded-t-xl border-t border-outline-variant bg-surface px-1 py-2 shadow-lg md:hidden">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            `flex min-w-0 flex-1 flex-col items-center justify-center rounded-full px-1 py-1 transition-colors ${
              isActive
                ? "bg-primary-container text-on-primary-container"
                : "text-on-surface-variant"
            }`
          }
        >
          {({ isActive }) => (
            <>
              <span
                aria-hidden="true"
                className={`material-symbols-outlined text-xl ${isActive ? "filled" : ""}`}
              >
                {item.icon}
              </span>
              <span className="w-full truncate text-center text-[11px] font-semibold leading-tight">
                {item.label}
              </span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}
