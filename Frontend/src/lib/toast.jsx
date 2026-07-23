import { createContext, useCallback, useContext, useState } from "react";

const ToastContext = createContext(null);

const META = {
  success: { icon: "check_circle", cls: "text-primary" },
  error: { icon: "error", cls: "text-error" },
  info: { icon: "info", cls: "text-secondary" },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => setToasts((list) => list.filter((t) => t.id !== id)), []);

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
        {toasts.map((t) => {
          const meta = META[t.variant];

          return (
            <div
              key={t.id}
              className="pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-2xl border border-outline-variant bg-surface-container-lowest px-4 py-3 shadow-lg"
            >
              <span className={`material-symbols-outlined shrink-0 ${meta.cls}`}>{meta.icon}</span>
              <p className="flex-1 text-body-md text-on-surface">{t.message}</p>
              <button
                type="button"
                onClick={() => dismiss(t.id)}
                aria-label="Закрыть уведомление"
                className="shrink-0 text-on-surface-variant transition-colors hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-lg">close</span>
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
