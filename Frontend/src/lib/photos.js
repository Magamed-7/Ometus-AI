// Фотографии лежат в `public/img` наборами `<путь>-<ширина>.webp`.
// Исходники Stitch шире 1228px не бывают, поэтому верхняя ступень — 1228:
// растягивать кадр выше родного размера смысла нет, резкости это не добавит.
export const SCENE_WIDTHS = [400, 640, 960, 1228];
export const CARD_WIDTHS = [400, 640];

// Филиалы идут в том же порядке, что и выдача `GET /api/filials`: Центр, Сомони, Север.
export const FILIAL_PHOTOS = [
  "/img/filials/filial-1",
  "/img/filials/filial-2",
  "/img/filials/filial-3",
];

export function filialPhoto(index) {
  return FILIAL_PHOTOS[index % FILIAL_PHOTOS.length];
}
