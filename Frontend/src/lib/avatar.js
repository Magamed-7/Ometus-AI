// Остаток заглушки STUBS #3.
//
// Фотография у врача теперь может быть: в `doctors` появилась колонка `photo_url`,
// и если она заполнена — показываем картинку. Если пусто или картинка не загрузилась,
// остаются инициалы на цветной подложке: это честнее, чем чужое лицо вместо врача.
//
// Стаж, рейтинг и отзывы по-прежнему не показываем — этих полей в базе нет,
// а выдумывать цифры о настоящем враче в медицинском приложении нельзя.

const ACCENTS = [
  "from-primary to-primary-container",
  "from-secondary to-secondary-container",
  "from-tertiary to-tertiary-container",
  "from-primary-container to-secondary",
];

export function avatarAccent(doctorId) {
  const index = Math.abs(Number(doctorId) || 0) % ACCENTS.length;
  return ACCENTS[index];
}

export function doctorInitials(name) {
  return (name || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export function doctorPhoto(doctor) {
  return doctor?.photo_url || null;
}
