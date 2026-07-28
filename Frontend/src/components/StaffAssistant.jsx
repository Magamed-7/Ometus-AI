import { useState } from "react";
import { askAsAdmin, askAsDoctor } from "../lib/api/ai.js";
import { errorText } from "../lib/api/errorText.js";
import { useI18n } from "../lib/i18n.jsx";
import Card from "./Card.jsx";

// Один компонент на обе роли: вопросы разные, а поведение одинаковое —
// спросил, дождался, прочитал. Разводим только эндпоинт и набор подсказок.
const SUGGESTIONS = {
  doctor: ["today", "free", "load", "absences"],
  admin: ["busiest", "summary", "noShows", "aiSpend"],
};

export default function StaffAssistant({ role }) {
  const { t, lang } = useI18n();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [asking, setAsking] = useState(false);

  const ask = async (text) => {
    const message = (text ?? question).trim();
    if (!message || asking) return;

    setAsking(true);
    setAnswer(null);

    try {
      const send = role === "admin" ? askAsAdmin : askAsDoctor;
      const result = await send({ message, language: lang });
      setAnswer(result);
    } catch (error) {
      setAnswer({ action: "error", reply: errorText(t, error), data: {} });
    } finally {
      setAsking(false);
    }
  };

  return (
    <Card className="p-md">
      <div className="mb-sm flex items-center gap-xs">
        <span aria-hidden="true" className="material-symbols-outlined text-primary">
          smart_toy
        </span>
        <h3 className="text-body-lg font-bold text-on-surface">
          {t(`staffAi.${role}Title`)}
        </h3>
      </div>
      <p className="mb-md text-label-md text-on-surface-variant">{t(`staffAi.${role}Hint`)}</p>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          ask();
        }}
        className="flex flex-wrap gap-sm"
      >
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={t("staffAi.placeholder")}
          aria-label={t("staffAi.placeholder")}
          className="min-w-0 flex-1 rounded-xl border border-outline-variant bg-surface-container-lowest px-md py-3 text-body-md text-on-surface"
        />
        <button
          type="submit"
          disabled={asking || !question.trim()}
          className="rounded-xl bg-primary px-lg py-3 font-semibold text-on-primary transition-all hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {asking ? t("staffAi.asking") : t("staffAi.ask")}
        </button>
      </form>

      <div className="mt-sm flex flex-wrap gap-xs">
        {SUGGESTIONS[role].map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setQuestion(t(`staffAi.q_${key}`));
              ask(t(`staffAi.q_${key}`));
            }}
            className="rounded-full border border-outline-variant px-sm py-1.5 text-label-md text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
          >
            {t(`staffAi.q_${key}`)}
          </button>
        ))}
      </div>

      <div aria-live="polite" className="mt-md">
        {asking && (
          <p className="text-body-md text-on-surface-variant">{t("staffAi.thinking")}</p>
        )}
        {answer && !asking && (
          <div
            className={`rounded-xl p-md ${
              answer.action === "error"
                ? "bg-error-container text-on-error-container"
                : "bg-secondary-container text-on-secondary-container"
            }`}
          >
            <p className="text-body-md">{answer.reply}</p>
            {/* Ассистент говорит про то, что уже есть на этой же странице,
                поэтому список приёмов дублировать не нужно — хватает фразы. */}
            {answer.action !== "error" && answer.action !== "clarify" && (
              <p className="mt-xs text-label-md opacity-80">{t("staffAi.fromDatabase")}</p>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
