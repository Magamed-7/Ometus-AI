import { ru } from "../locales/ru.js";

export function errorText(t, error, fallback) {
  if (!error) return fallback || t("common.loadError");

  const code = error.code;

  if (code && ru.errors[code]) {
    // перевод берём по коду, а имена полей — с сервера: иначе на 422 остаётся
    // «проверьте введённые данные», и в форме на десять полей непонятно, какое из них
    return error.fields?.length
      ? `${t(`errors.${code}`)}: ${error.fields.join(", ")}`
      : t(`errors.${code}`);
  }

  return error.message || fallback || t("common.loadError");
}
