import { NavLink, Outlet } from "react-router-dom";
import { useT } from "../../lib/i18n.jsx";

const SECTIONS = [
  { to: "/admin/filials", icon: "apartment", key: "nav.adminFilials" },
  { to: "/admin/departments", icon: "meeting_room", key: "nav.adminDepartments" },
  { to: "/admin/doctors", icon: "stethoscope", key: "nav.adminDoctors" },
  { to: "/admin/appointments", icon: "event_note", key: "admin.appointments" },
  { to: "/admin/reports", icon: "monitoring", key: "nav.adminReports" },
];

export default function AdminShell() {
  const t = useT();

  const linkClass = ({ isActive }) =>
    `flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-label-md font-semibold transition-colors ${
      isActive
        ? "bg-primary text-on-primary"
        : "bg-surface-container text-on-surface-variant hover:text-primary"
    }`;

  return (
    <div className="mx-auto max-w-7xl px-sm py-md md:px-lg">
      <h1 className="mb-md text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
        {t("nav.admin")}
      </h1>

      <nav className="mb-lg flex gap-xs overflow-x-auto pb-1">
        {SECTIONS.map((section) => (
          <NavLink key={section.to} to={section.to} className={linkClass}>
            <span aria-hidden="true" className="material-symbols-outlined text-lg">{section.icon}</span>
            {t(section.key)}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  );
}
