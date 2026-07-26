import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useT } from "../lib/i18n.jsx";

const TITLES = {
  "/": "nav.home",
  "/doctors": "nav.doctors",
  "/booking": "nav.booking",
  "/assistant": "nav.assistant",
  "/account": "nav.account",
  "/login": "auth.signIn",
  "/register": "auth.signUp",
  "/verify-email": "auth.verifyTitle",
  "/doctor/today": "nav.doctorToday",
  "/doctor/schedule": "nav.doctorSchedule",
  "/admin/filials": "nav.adminFilials",
  "/admin/departments": "nav.adminDepartments",
  "/admin/doctors": "nav.adminDoctors",
  "/admin/appointments": "admin.appointments",
  "/admin/reports": "nav.adminReports",
  "/admin": "nav.admin",
};

function titleKey(pathname) {
  if (TITLES[pathname]) return TITLES[pathname];
  if (pathname.startsWith("/doctors/")) return "doctors.profile";
  if (pathname.startsWith("/booking/")) return "nav.booking";
  return "notFound.title";
}

export default function DocumentTitle() {
  const { pathname } = useLocation();
  const t = useT();

  useEffect(() => {
    const key = titleKey(pathname);
    document.title = key ? `${t(key)} — Ometus Clinic` : "Ometus Clinic";
  }, [pathname, t]);

  return null;
}
