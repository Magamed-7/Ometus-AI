import { useEffect } from "react";
import { useT } from "../lib/i18n.jsx";

export default function Modal({ title, onClose, children, footer }) {
  const t = useT();

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };

    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-md"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="flex max-h-[90vh] w-full max-w-dialog flex-col overflow-hidden rounded-t-2xl border border-outline-variant bg-surface-container-lowest sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-outline-variant p-md">
          <h2 className="text-headline-md font-semibold text-on-surface">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("common.close")}
            className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant hover:bg-surface-container"
          >
            <span aria-hidden="true" className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-md">{children}</div>

        {footer && <div className="flex gap-sm border-t border-outline-variant p-md">{footer}</div>}
      </div>
    </div>
  );
}
