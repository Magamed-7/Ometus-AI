import { useState } from "react";
import { avatarAccent, doctorInitials, doctorPhoto } from "../lib/avatar.js";
import { useI18n } from "../lib/i18n.jsx";

// размеры задаёт вызывающий через className, чтобы карточка, страница врача
// и сводка записи не разъезжались: у них аватар разного размера и скругления
export default function DoctorAvatar({ doctor, className = "", textClass = "text-headline-md" }) {
  const { t } = useI18n();
  const [broken, setBroken] = useState(false);
  const photo = broken ? null : doctorPhoto(doctor);
  const id = doctor?.id ?? doctor?.doctor_id;

  if (photo) {
    return (
      <img
        src={photo}
        alt={t("doctors.photoAlt", { name: doctor.full_name })}
        width="96"
        height="96"
        loading="lazy"
        onError={() => setBroken(true)}
        className={`shrink-0 bg-surface-container object-cover ${className}`}
      />
    );
  }

  return (
    <div
      className={`grid shrink-0 place-items-center bg-gradient-to-br text-on-primary ${avatarAccent(
        id
      )} ${className}`}
    >
      <span className={`font-bold ${textClass}`}>{doctorInitials(doctor?.full_name)}</span>
    </div>
  );
}
