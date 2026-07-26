import { useId, useState } from "react";
import { useT } from "../lib/i18n.jsx";

const baseInput =
  "min-h-11 w-full rounded-xl border bg-surface-container-lowest px-4 py-2.5 text-body-md text-on-surface placeholder:text-on-surface-variant/60 transition-colors focus:border-primary focus:outline-none";

function Label({ id, label, required }) {
  if (!label) return null;
  return (
    <label htmlFor={id} className="text-label-md font-semibold text-on-surface-variant">
      {label}
      {required && <span className="text-error"> *</span>}
    </label>
  );
}

export function Field({ label, error, hint, required, type = "text", className = "", ...props }) {
  const t = useT();
  const id = useId();
  const [show, setShow] = useState(false);
  const isPassword = type === "password";
  const inputType = isPassword ? (show ? "text" : "password") : type;

  // сообщение об ошибке надо не только показать, но и связать с полем:
  // без aria-describedby скринридер прочитает поле, но промолчит о причине отказа
  const messageId = error || hint ? `${id}-message` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <Label id={id} label={label} required={required} />
      <div className="relative">
        <input
          id={id}
          type={inputType}
          aria-invalid={error ? true : undefined}
          aria-describedby={messageId}
          className={`${baseInput} ${isPassword ? "pr-11" : ""} ${
            error ? "border-error" : "border-outline-variant"
          } ${className}`}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShow((s) => !s)}
            aria-label={show ? t("common.hidePassword") : t("common.showPassword")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-primary"
          >
            <span aria-hidden="true" className="material-symbols-outlined text-lg">
              {show ? "visibility_off" : "visibility"}
            </span>
          </button>
        )}
      </div>
      {error ? (
        <p id={messageId} className="text-label-md text-error">
          {error}
        </p>
      ) : hint ? (
        <p id={messageId} className="text-label-md text-on-surface-variant">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export function Select({ label, error, required, children, className = "", ...props }) {
  const id = useId();
  const messageId = error ? `${id}-message` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <Label id={id} label={label} required={required} />
      <select
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={messageId}
        className={`${baseInput} appearance-none ${
          error ? "border-error" : "border-outline-variant"
        } ${className}`}
        {...props}
      >
        {children}
      </select>
      {error && (
        <p id={messageId} className="text-label-md text-error">
          {error}
        </p>
      )}
    </div>
  );
}

export function Checkbox({ label, className = "", ...props }) {
  const id = useId();

  return (
    <label htmlFor={id} className="flex cursor-pointer items-center gap-2 text-body-md text-on-surface">
      <input
        id={id}
        type="checkbox"
        className={`h-5 w-5 rounded border-outline-variant text-primary focus:ring-primary ${className}`}
        {...props}
      />
      {label}
    </label>
  );
}
