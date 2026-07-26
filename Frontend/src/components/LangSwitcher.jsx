import { useEffect, useRef, useState } from "react";
import { LANGS, useI18n } from "../lib/i18n.jsx";

export default function LangSwitcher() {
  const { lang, setLang } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const current = LANGS.find((l) => l.code === lang) || LANGS[0];

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Выбрать язык"
        className="flex h-11 items-center gap-1 rounded-full border border-outline-variant px-3 text-label-md font-semibold text-on-surface-variant transition-colors hover:border-primary hover:text-primary"
      >
        <span aria-hidden="true" className="material-symbols-outlined text-lg">language</span>
        {current.label}
      </button>
      {open && (
        <ul
          role="listbox"
          className="absolute right-0 z-50 mt-2 w-40 overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest py-1 shadow-lg"
        >
          {LANGS.map((l) => (
            <li key={l.code} role="option" aria-selected={l.code === lang}>
              <button
                type="button"
                onClick={() => {
                  setLang(l.code);
                  setOpen(false);
                }}
                className={`flex w-full items-center justify-between px-4 py-2 text-body-md transition-colors hover:bg-surface-container ${
                  l.code === lang ? "text-primary font-semibold" : "text-on-surface"
                }`}
              >
                {l.name}
                <span className="text-label-md text-on-surface-variant">{l.label}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
