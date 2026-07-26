// Заглушка STUBS #3 (пункты 64 и 138).
//
// В таблице `doctors` на бэкенде есть только `full_name` и `specialization`: ни фото,
// ни стажа, ни рейтинга, ни отзывов. Выдумывать эти поля в медицинском приложении нельзя —
// «стаж 12 лет» и «рейтинг 4.8» о настоящем враче это дезинформация, поэтому блоки с ними
// не рисуются вовсе, а вместо фотографии показываются инициалы на цветной подложке.
//
// Никаких данных о врачах здесь нет — только выбор цвета подложки по id, чтобы карточки
// не были одинаково серыми. Заглушка снимется, когда в `doctors` появятся `photo_url`,
// `experience_years`, `bio` и отдельная таблица отзывов.

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
