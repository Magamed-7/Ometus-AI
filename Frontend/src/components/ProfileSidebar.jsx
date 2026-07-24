import { phone as formatPhone } from "../lib/format.js";
import { useT } from "../lib/i18n.jsx";
import Card from "./Card.jsx";

function initials(user) {
  const parts = [user.first_name, user.last_name].filter(Boolean);
  if (parts.length) return parts.map((p) => p[0]).join("").toUpperCase();
  return (user.email || "?")[0].toUpperCase();
}

export default function ProfileSidebar({ user, editing, onToggleEdit, onLogout }) {
  const t = useT();
  const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email;

  return (
    <Card className="p-md">
      <div className="mb-md flex items-center gap-md">
        <div className="grid h-20 w-20 shrink-0 place-items-center rounded-full bg-primary-container text-headline-md font-bold text-on-primary-container">
          {initials(user)}
        </div>
        <div className="min-w-0">
          <h1 className="truncate text-headline-md font-semibold text-on-surface">{fullName}</h1>
          <p className="text-body-md text-on-surface-variant">{formatPhone(user.phone)}</p>
        </div>
      </div>

      <hr className="mb-md border-outline-variant" />

      <div className="space-y-sm">
        <button
          type="button"
          onClick={onToggleEdit}
          className={`flex w-full items-center justify-between rounded-lg p-sm transition-colors ${
            editing
              ? "bg-surface-container-high font-bold text-primary"
              : "hover:bg-surface-container-low"
          }`}
        >
          <span className="flex items-center gap-sm">
            <span className="material-symbols-outlined">person</span>
            {t("account.editProfile")}
          </span>
          <span className="material-symbols-outlined">chevron_right</span>
        </button>
        <button
          type="button"
          onClick={onLogout}
          className="flex w-full items-center gap-sm rounded-lg p-sm text-error transition-colors hover:bg-error-container"
        >
          <span className="material-symbols-outlined">logout</span>
          {t("account.logout")}
        </button>
      </div>
    </Card>
  );
}
