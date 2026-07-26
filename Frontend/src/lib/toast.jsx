import { createContext, useCallback, useContext, useState } from "react";
import { useT } from "./i18n.jsx";

const ToastContext = createContext(null);

const META = {
  success: { icon: "check_circle", cls: "text-primary" },
  error: { icon: "error", cls: "text-error" },
  info: { icon: "info", cls: "text-secondary" },
};

export function ToastProvider({ children }) {
  const t = useT();
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback(
    (id) => setToasts((list) => list.filter((item) => item.id !== id)),
    []
  );

  const push = useCallback(
    (variant, message) => {
      const id = Date.now() + Math.random();
      setToasts((list) => [...list, { id, variant, message }]);
      setTimeout(() => dismiss(id), 4500);
    },
    [dismiss]
  );

  const toast = {
    success: (message) => push("success", message),
    error: (message) => push("error", message),
    info: (message) => push("info", message),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex flex-col items-center gap-2 p-4 sm:items-end"
      >
        {toasts.map((item) => {
          const meta = META[item.variant];

          return (
            <div
              key={item.id}
              role={item.variant === "error" ? "alert" : "status"}
              className="pointer-events-auto flex w-full max-w-note items-start gap-3 rounded-2xl border border-outline-variant bg-surface-container-lowest px-4 py-3 shadow-lg"
            >
              <span
                aria-hidden="true"
                className={`material-symbols-outlined shrink-0 ${meta.cls}`}
              >
                {meta.icon}
              </span>
              <p className="flex-1 text-body-md text-on-surface">{item.message}</p>
              <button
                type="button"
                onClick={() => dismiss(item.id)}
                aria-label={t("common.close")}
                className="shrink-0 text-on-surface-variant transition-colors hover:text-on-surface"
              >
                <span aria-hidden="true" className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);

  if (context === null) throw new Error("useToast должен использоваться внутри ToastProvider");

  return context;
}
