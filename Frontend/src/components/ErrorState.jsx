import { errorText } from "../lib/api/errorText.js";
import { useT } from "../lib/i18n.jsx";
import Button from "./Button.jsx";

export default function ErrorState({ error, message, onRetry }) {
  const t = useT();
  const offline = error && error.code === "NETWORK_ERROR";
  const text = message || (error ? errorText(t, error) : t("common.loadError"));

  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-outline-variant bg-surface-container-low px-md py-xl text-center"
    >
      <span aria-hidden="true" className="material-symbols-outlined text-5xl text-error">
        {offline ? "wifi_off" : "error"}
      </span>
      <p className="max-w-form text-body-lg text-on-surface">{text}</p>
      {offline && <p className="max-w-form text-body-md text-on-surface-variant">{t("common.offlineHint")}</p>}
      {onRetry && (
        <Button variant="outline" icon="refresh" onClick={onRetry}>
          {t("common.retry")}
        </Button>
      )}
    </div>
  );
}
