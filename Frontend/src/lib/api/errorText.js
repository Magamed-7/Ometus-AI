import { ru } from "../locales/ru.js";

export function errorText(t, error, fallback) {
  if (!error) return fallback || t("common.loadError");

  const code = error.code;

  if (code && ru.errors[code]) return t(`errors.${code}`);

  return error.message || fallback || t("common.loadError");
}
