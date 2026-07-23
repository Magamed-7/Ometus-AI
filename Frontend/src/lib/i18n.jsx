import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { ru } from "./locales/ru.js";
import { tg } from "./locales/tg.js";
import { en } from "./locales/en.js";

const dicts = { ru, tg, en };

export const LANGS = [
  { code: "ru", label: "RU", name: "Русский" },
  { code: "tg", label: "TJ", name: "Тоҷикӣ" },
  { code: "en", label: "EN", name: "English" },
];

const I18nContext = createContext({ lang: "ru", setLang: () => {}, t: (key) => key });

function resolve(dict, key) {
  return key.split(".").reduce((obj, part) => (obj == null ? undefined : obj[part]), dict);
}

function readLang() {
  try {
    const saved = localStorage.getItem("ometus-lang");
    if (saved && dicts[saved]) return saved;
  } catch (e) {}
  return "ru";
}

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(readLang);

  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      localStorage.setItem("ometus-lang", lang);
    } catch (e) {}
  }, [lang]);

  const t = useCallback(
    (key, vars) => {
      let str = resolve(dicts[lang], key);
      if (str === undefined) str = resolve(dicts.ru, key);
      if (str === undefined) return key;
      if (vars) {
        for (const name in vars) str = str.replaceAll(`{${name}}`, vars[name]);
      }
      return str;
    },
    [lang]
  );

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export const useI18n = () => useContext(I18nContext);

export const useT = () => useContext(I18nContext).t;
