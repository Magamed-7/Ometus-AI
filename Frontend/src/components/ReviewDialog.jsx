import { useState } from "react";
import { leaveReview } from "../lib/api/reviews.js";
import { errorText } from "../lib/api/errorText.js";
import { useI18n } from "../lib/i18n.jsx";
import { useToast } from "../lib/toast.jsx";
import Button from "./Button.jsx";

const STARS = [1, 2, 3, 4, 5];

export default function ReviewDialog({ appointment, doctorName, onClose, onSaved }) {
  const { t } = useI18n();
  const toast = useToast();
  const [rating, setRating] = useState(0);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    if (!rating || saving) return;

    setSaving(true);

    try {
      await leaveReview({
        appointment_id: appointment.id,
        rating,
        text: text.trim() || null,
      });
      toast.success(t("review.thanks"));
      onSaved();
    } catch (error) {
      toast.error(errorText(t, error));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="review-title"
      className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-md"
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <form
        onSubmit={submit}
        className="w-full max-w-note rounded-2xl border border-outline-variant bg-surface-container-lowest p-lg"
      >
        <h2 id="review-title" className="text-headline-md font-bold text-on-surface">
          {t("review.title")}
        </h2>
        <p className="mt-xs text-body-md text-on-surface-variant">
          {doctorName ? t("review.about", { doctor: doctorName }) : t("review.aboutVisit")}
        </p>

        <fieldset className="mt-md">
          <legend className="mb-xs text-label-md font-semibold text-on-surface">
            {t("review.rating")}
          </legend>
          {/* radio, а не набор кнопок: с клавиатуры оценка выбирается стрелками,
              и скринридер объявляет её как один вопрос с пятью вариантами */}
          <div className="flex gap-xs">
            {STARS.map((star) => (
              <label
                key={star}
                className="cursor-pointer"
                title={t("review.starsLabel", { count: star })}
              >
                <input
                  type="radio"
                  name="rating"
                  value={star}
                  checked={rating === star}
                  onChange={() => setRating(star)}
                  className="sr-only peer"
                />
                <span
                  aria-hidden="true"
                  className={`material-symbols-outlined text-4xl transition-colors peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-primary ${
                    star <= rating ? "filled text-tertiary" : "text-outline-variant"
                  }`}
                >
                  star
                </span>
                <span className="sr-only">{t("review.starsLabel", { count: star })}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <label className="mt-md block">
          <span className="mb-xs block text-label-md font-semibold text-on-surface">
            {t("review.text")} <span className="font-normal text-on-surface-variant">({t("common.optional")})</span>
          </span>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={4}
            maxLength={2000}
            placeholder={t("review.placeholder")}
            className="w-full rounded-xl border border-outline-variant bg-surface-container-lowest p-sm text-body-md text-on-surface"
          />
        </label>

        <p className="mt-xs text-label-md text-on-surface-variant">{t("review.privacy")}</p>

        <div className="mt-md flex flex-wrap gap-sm">
          <Button type="submit" icon="send" loading={saving} disabled={!rating}>
            {t("review.send")}
          </Button>
          <Button type="button" variant="ghost" onClick={onClose}>
            {t("common.cancel")}
          </Button>
        </div>
      </form>
    </div>
  );
}
