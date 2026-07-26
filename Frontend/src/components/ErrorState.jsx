import { useT } from "../lib/i18n.jsx";
import Button from "./Button.jsx";

export default function ErrorState({ message, onRetry }) {
  const t = useT();

  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-outline-variant bg-surface-container-low px-md py-xl text-center"
    >
      <span aria-hidden="true" className="material-symbols-outlined text-5xl text-error">error</span>
      <p className="max-w-md text-body-lg text-on-surface">{message || t("common.loadError")}</p>
      {onRetry && (
        <Button variant="outline" icon="refresh" onClick={onRetry}>
          {t("common.retry")}
        </Button>
      )}
    </div>
  );
}
