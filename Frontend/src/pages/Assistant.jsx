import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { askAssistant } from "../lib/api/ai.js";
import { errorText } from "../lib/api/errorText.js";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { clock, formatDate } from "../lib/format.js";
import { useI18n } from "../lib/i18n.jsx";
import { scrollBehavior } from "../lib/motion.js";

function BotAvatar() {
  return (
    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-primary-container text-on-primary-container">
      <span aria-hidden="true" className="material-symbols-outlined filled">smart_toy</span>
    </div>
  );
}

function UserBubble({ text }) {
  return (
    <div className="flex max-w-[85%] flex-row-reverse gap-sm self-end">
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-secondary text-on-secondary">
        <span aria-hidden="true" className="material-symbols-outlined">person</span>
      </div>
      <div className="rounded-2xl rounded-tr-none bg-primary-container p-md text-on-primary-container">
        <p className="text-body-md">{text}</p>
      </div>
    </div>
  );
}

function DoctorsAnswer({ t, data, onPickDoctor }) {
  return (
    <div className="flex flex-col gap-xs">
      {data.doctors.map((doctor) => (
        <div
          key={doctor.doctor_id}
          className="flex items-center justify-between gap-sm rounded-xl border border-outline-variant bg-surface-container-low p-sm"
        >
          <div className="min-w-0">
            <p className="truncate font-bold text-on-surface">{doctor.full_name}</p>
            <p className="text-label-md text-on-surface-variant">{doctor.specialization}</p>
          </div>
          <button
            type="button"
            onClick={() => onPickDoctor(doctor)}
            className="shrink-0 rounded-lg bg-primary px-md py-2 text-label-md font-bold text-on-primary transition-opacity hover:opacity-90"
          >
            {t("assistant.showSlots")}
          </button>
        </div>
      ))}
    </div>
  );
}

function SlotsAnswer({ t, lang, data, onPickSlot }) {
  const byDate = {};
  for (const slot of data.slots) {
    (byDate[slot.date] = byDate[slot.date] || []).push(slot);
  }

  return (
    <div className="flex flex-col gap-sm rounded-xl border border-outline-variant bg-surface-container-low p-sm">
      {Object.entries(byDate).map(([date, slots]) => (
        <div key={date}>
          <p className="mb-xs text-label-md font-semibold text-on-surface-variant">
            {formatDate(date, lang)}
          </p>
          <div className="grid grid-cols-3 gap-xs sm:grid-cols-4">
            {slots.map((slot) => (
              <button
                key={`${date}-${slot.time}`}
                type="button"
                onClick={() => onPickSlot(data, slot)}
                className="rounded-lg border border-outline-variant bg-surface-container-lowest py-2 text-label-md font-bold text-on-surface transition-colors hover:border-primary hover:text-primary"
              >
                {clock(slot.time)}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function BookedAnswer({ t, lang, appointment }) {
  return (
    <div className="rounded-xl border border-primary/40 bg-primary-container/10 p-md">
      <div className="mb-sm flex items-center gap-sm text-primary">
        <span aria-hidden="true" className="material-symbols-outlined filled">check_circle</span>
        <p className="font-bold">{t("booking.successTitle")}</p>
      </div>
      <div className="space-y-1 text-body-md text-on-surface">
        <p className="font-bold">{appointment.doctor_name}</p>
        {appointment.specialization && (
          <p className="text-label-md text-on-surface-variant">{appointment.specialization}</p>
        )}
        {appointment.department && (
          <p className="text-label-md text-on-surface-variant">{appointment.department}</p>
        )}
        <p className="pt-xs font-semibold text-primary">
          {formatDate(appointment.date, lang)}, {clock(appointment.time)}
        </p>
      </div>
      <Link
        to="/account"
        className="mt-sm inline-flex rounded-lg bg-primary px-md py-2 text-label-md font-bold text-on-primary transition-opacity hover:opacity-90"
      >
        {t("booking.toAccount")}
      </Link>
    </div>
  );
}

function EmergencyAnswer({ t, reply }) {
  return (
    <div className="flex max-w-[85%] gap-sm">
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-error-container text-on-error-container">
        <span aria-hidden="true" className="material-symbols-outlined filled">emergency</span>
      </div>
      <div className="flex w-full flex-col gap-sm rounded-2xl rounded-tl-none border border-error bg-error-container p-md text-on-error-container">
        <p className="font-bold uppercase tracking-wide">{t("assistant.emergencyTitle")}</p>
        <p className="whitespace-pre-line text-body-md">{reply}</p>
        <a
          href="tel:103"
          className="inline-flex w-fit items-center gap-xs rounded-lg bg-error px-md py-2 text-label-md font-bold text-on-error transition-opacity hover:opacity-90"
        >
          <span aria-hidden="true" className="material-symbols-outlined text-lg">call</span>
          103
        </a>
      </div>
    </div>
  );
}

function AssistantBubble({ data, t, lang, onPickDoctor, onPickSlot }) {
  if (data.action === "emergency") return <EmergencyAnswer t={t} reply={data.reply} />;

  const isError = data.action === "error";
  const isClarify = data.action === "clarify";

  return (
    <div className="flex max-w-[85%] gap-sm">
      <BotAvatar />
      <div className="flex w-full flex-col gap-sm">
        <div
          className={`flex gap-sm rounded-2xl rounded-tl-none border p-md ${
            isError
              ? "border-error/40 bg-error-container/30"
              : "border-outline-variant bg-surface-container-lowest"
          }`}
        >
          {(isError || isClarify) && (
            <span
              aria-hidden="true"
              className={`material-symbols-outlined text-lg ${
                isError ? "text-error" : "text-secondary"
              }`}
            >
              {isError ? "error" : "help"}
            </span>
          )}
          <p className="whitespace-pre-line text-body-md text-on-surface">{data.reply}</p>
        </div>
        {data.action === "doctors" && data.doctors?.length > 0 && (
          <DoctorsAnswer t={t} data={data} onPickDoctor={onPickDoctor} />
        )}
        {data.action === "slots" && data.slots?.length > 0 && (
          <SlotsAnswer t={t} lang={lang} data={data} onPickSlot={onPickSlot} />
        )}
        {data.action === "booked" && data.appointment && (
          <BookedAnswer t={t} lang={lang} appointment={data.appointment} />
        )}
      </div>
    </div>
  );
}

function ThinkingBubble({ label }) {
  return (
    <div className="flex max-w-[85%] gap-sm">
      <BotAvatar />
      <div className="flex items-center gap-1 rounded-2xl rounded-tl-none border border-outline-variant bg-surface-container-lowest px-md py-md">
        <span aria-hidden="true" className="material-symbols-outlined animate-spin text-lg text-primary">
          progress_activity
        </span>
        <span className="text-body-md text-on-surface-variant">{label}</span>
      </div>
    </div>
  );
}

export default function Assistant() {
  const { t, lang } = useI18n();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [messages, setMessages] = useState([
    { id: "welcome", role: "assistant", data: { action: "welcome", reply: t("assistant.subtitle") } },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: scrollBehavior() });
  }, [messages, sending]);

  const runAsk = async (payload, userText) => {
    if (sending) return;

    if (!user) {
      navigate("/login", { state: { from: location } });
      return;
    }

    if (userText) {
      setMessages((list) => [
        ...list,
        { id: `u-${Date.now()}`, role: "user", data: { text: userText } },
      ]);
    }
    setSending(true);

    try {
      const answer = await askAssistant(payload);
      if (payload.doctor_id) answer._doctorId = payload.doctor_id;
      setMessages((list) => [
        ...list,
        { id: `a-${Date.now()}`, role: "assistant", data: answer },
      ]);
    } catch (e) {
      setMessages((list) => [
        ...list,
        {
          id: `e-${Date.now()}`,
          role: "assistant",
          data: { action: "error", reply: errorText(t, e) },
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const send = (text) => {
    const message = text.trim();
    if (!message) return;
    setInput("");
    runAsk({ message }, message);
  };

  const onPickDoctor = (doctor) => {
    runAsk({ message: t("assistant.showSlots"), doctor_id: doctor.doctor_id }, doctor.full_name);
  };

  const onPickSlot = (data, slot) => {
    const label = t("assistant.book", { time: clock(slot.time) });
    runAsk(
      { message: label, doctor_id: data._doctorId, date: slot.date, time: slot.time, confirm: true },
      label
    );
  };

  const onSubmit = (e) => {
    e.preventDefault();
    send(input);
  };

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-sm py-sm md:px-lg">
      <div className="mb-sm flex items-start gap-sm rounded-xl border border-outline-variant bg-surface-container-low p-sm">
        <span aria-hidden="true" className="material-symbols-outlined text-secondary">info</span>
        <div>
          <p className="text-label-md font-bold text-on-surface">{t("assistant.title")}</p>
          <p className="text-label-md text-on-surface-variant">{t("assistant.disclaimer")}</p>
        </div>
      </div>
      <div className="flex flex-grow flex-col gap-md pb-xl">
        {messages.map((msg) =>
          msg.role === "user" ? (
            <UserBubble key={msg.id} text={msg.data.text} />
          ) : (
            <AssistantBubble
              key={msg.id}
              data={msg.data}
              t={t}
              lang={lang}
              onPickDoctor={onPickDoctor}
              onPickSlot={onPickSlot}
            />
          )
        )}
        {sending && <ThinkingBubble label={t("assistant.thinking")} />}
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-md pt-md">
        {messages.length <= 1 && !sending && (
          <div className="mb-sm flex flex-wrap items-center gap-xs">
            <span className="text-label-md text-on-surface-variant">{t("assistant.suggestions")}</span>
            {["assistant.s1", "assistant.s2", "assistant.s3"].map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => send(t(key))}
                className="rounded-full border border-outline-variant bg-surface-container-low px-md py-1.5 text-label-md font-semibold text-on-surface-variant transition-colors hover:border-primary hover:text-primary"
              >
                {t(key)}
              </button>
            ))}
          </div>
        )}
        <form
          onSubmit={onSubmit}
          className="flex items-center gap-xs rounded-2xl border border-outline-variant bg-surface-container-lowest p-xs shadow-lg focus-within:ring-2 focus-within:ring-primary"
        >
          <div className="flex flex-grow items-center px-sm">
            <span aria-hidden="true" className="material-symbols-outlined text-outline">chat</span>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
              className="w-full bg-transparent px-sm py-sm text-body-md focus:outline-none disabled:opacity-60"
              placeholder={t("assistant.placeholder")}
              aria-label={t("assistant.placeholder")}
            />
          </div>
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="flex items-center gap-sm rounded-xl bg-primary px-lg py-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span className="hidden sm:inline">{t("assistant.send")}</span>
            <span aria-hidden="true" className="material-symbols-outlined text-sm">send</span>
          </button>
        </form>
      </div>
    </div>
  );
}
