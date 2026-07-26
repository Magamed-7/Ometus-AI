import { useT } from "../lib/i18n.jsx";

const CONFIG = {
  booked: { icon: "event_available", cls: "bg-primary-container text-on-primary-container" },
  completed: { icon: "task_alt", cls: "bg-secondary-container text-on-secondary-container" },
  cancelled: { icon: "cancel", cls: "bg-error-container text-on-error-container" },
  no_show: { icon: "person_off", cls: "bg-tertiary-container text-on-tertiary-container" },
};

export default function StatusPill({ status }) {
  const t = useT();
  const config = CONFIG[status] || CONFIG.booked;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-label-md font-semibold ${config.cls}`}
    >
      <span aria-hidden="true" className="material-symbols-outlined text-base">{config.icon}</span>
      {t(`status.${status}`)}
    </span>
  );
}
