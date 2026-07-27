import { useState } from "react";

// Пока фотографии не залиты в public/img, страницы не должны выглядеть сломанными:
// вместо битой картинки рисуем градиент с иконкой — тот же приём, что у DoctorAvatar
// с инициалами. Как только файл появится по этому пути, он подставится сам.
export default function Photo({
  src,
  alt,
  icon = "photo_camera",
  className = "",
  imgClassName = "",
  width,
  height,
  eager = false,
}) {
  const [broken, setBroken] = useState(false);

  if (!src || broken) {
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
      src={src}
      alt={alt}
      width={width}
      height={height}
      loading={eager ? "eager" : "lazy"}
      onError={() => setBroken(true)}
      className={`bg-surface-container object-cover ${className} ${imgClassName}`}
    />
  );
}
