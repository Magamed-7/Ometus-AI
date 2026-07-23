const INTL = { ru: "ru-RU", tg: "ru-RU", en: "en-US" };

const intl = (lang) => INTL[lang] || "ru-RU";

export function formatDate(value, lang = "ru") {
  if (!value) return "—";

  return new Date(value).toLocaleDateString(intl(lang), {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function formatDateShort(value, lang = "ru") {
  if (!value) return "—";

  return new Date(value).toLocaleDateString(intl(lang), { day: "numeric", month: "short" });
}

export function clock(value) {
  if (!value) return "—";

  return String(value).slice(0, 5);
}

export function isoDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function parseIso(value) {
  return new Date(`${value}T00:00:00`);
}

export function weekdayIndex(value) {
  const day = parseIso(value).getDay();
  return (day + 6) % 7;
}

export function phone(value) {
  if (!value) return "—";

  const digits = String(value).replace(/\D/g, "");

  if (digits.length === 12 && digits.startsWith("992")) {
    return `+992 ${digits.slice(3, 5)} ${digits.slice(5, 8)} ${digits.slice(8, 10)} ${digits.slice(10)}`;
  }

  return value;
}
