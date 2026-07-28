import { useState } from "react";

// Файлы лежат как `<base>-<ширина>.webp`, поэтому браузеру отдаём весь набор и он
// сам берёт нужный: телефону не за чем тянуть кадр под широкий экран.
function buildSrcSet(base, widths) {
  return widths.map((width) => `${base}-${width}.webp ${width}w`).join(", ");
}

// Если файла по пути нет, страница не должна выглядеть сломанной: вместо битой
// картинки рисуем градиент с иконкой — тот же приём, что у DoctorAvatar с инициалами.
export default function Photo({
  src,
  base,
  widths,
  sizes,
  alt,
  icon = "photo_camera",
  className = "",
  imgClassName = "",
  width,
  height,
  eager = false,
}) {
  const [broken, setBroken] = useState(false);
  const largest = widths && widths.length ? widths[widths.length - 1] : null;
  const url = base && largest ? `${base}-${largest}.webp` : src;

  if (!url || broken) {
    return (
      <div
        aria-hidden="true"
        className={`grid place-items-center bg-gradient-to-br from-primary-container to-secondary-container ${className}`}
      >
        <span className="material-symbols-outlined text-5xl text-on-primary-container/70">
          {icon}
        </span>
      </div>
    );
  }

  return (
    <img
      src={url}
      srcSet={base && largest ? buildSrcSet(base, widths) : undefined}
      sizes={base && largest ? sizes : undefined}
      alt={alt}
      width={width}
      height={height}
      loading={eager ? "eager" : "lazy"}
      decoding={eager ? "sync" : "async"}
      onError={() => setBroken(true)}
      className={`bg-surface-container object-cover ${className} ${imgClassName}`}
    />
  );
}
