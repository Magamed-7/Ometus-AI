import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { askAssistant } from "../lib/api/ai.js";
import { errorText } from "../lib/api/errorText.js";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { useI18n } from "../lib/i18n.jsx";

function BotAvatar() {
  return (
    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-primary-container text-on-primary-container">
      <span className="material-symbols-outlined filled">smart_toy</span>
    </div>
  );
}

function UserBubble({ text }) {
  return (
    <div className="flex max-w-[85%] flex-row-reverse gap-sm self-end">
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-secondary text-on-secondary">
        <span className="material-symbols-outlined">person</span>
      </div>
      <div className="rounded-2xl rounded-tr-none bg-primary-container p-md text-on-primary-container">
        <p className="text-body-md">{text}</p>
      </div>
    </div>
  );
}

function AssistantBubble({ data }) {
  return (
    <div className="flex max-w-[85%] gap-sm">
      <BotAvatar />
      <div className="flex w-full flex-col gap-sm">
        <div className="rounded-2xl rounded-tl-none border border-outline-variant bg-surface-container-lowest p-md">
          <p className="whitespace-pre-line text-body-md text-on-surface">{data.reply}</p>
        </div>
      </div>
    </div>
  );
}

function ThinkingBubble({ label }) {
  return (
    <div className="flex max-w-[85%] gap-sm">
      <BotAvatar />
      <div className="flex items-center gap-1 rounded-2xl rounded-tl-none border border-outline-variant bg-surface-container-lowest px-md py-md">
        <span className="material-symbols-outlined animate-spin text-lg text-primary">
          progress_activity
        </span>
        <span className="text-body-md text-on-surface-variant">{label}</span>
      </div>
    </div>
  );
}

export default function Assistant() {
  const { t } = useI18n();
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
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const send = async (text) => {
    const message = text.trim();
    if (!message || sending) return;

    if (!user) {
      navigate("/login", { state: { from: location } });
      return;
    }

    setInput("");
    setMessages((list) => [
      ...list,
      { id: `u-${Date.now()}`, role: "user", data: { text: message } },
    ]);
    setSending(true);

    try {
      const answer = await askAssistant({ message });
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

  const onSubmit = (e) => {
    e.preventDefault();
    send(input);
  };

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-sm py-sm md:px-lg">
      <div className="flex flex-grow flex-col gap-md pb-xl">
        {messages.map((msg) =>
          msg.role === "user" ? (
            <UserBubble key={msg.id} text={msg.data.text} />
          ) : (
            <AssistantBubble key={msg.id} data={msg.data} />
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
            <span className="material-symbols-outlined text-outline">chat</span>
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
            <span className="material-symbols-outlined text-sm">send</span>
          </button>
        </form>
      </div>
    </div>
  );
}
