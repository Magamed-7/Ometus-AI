import { useEffect, useRef, useState } from "react";
import { useT } from "../lib/i18n.jsx";

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
          <p className="text-body-md text-on-surface">{data.reply}</p>
        </div>
      </div>
    </div>
  );
}

export default function Assistant() {
  const t = useT();
  const [messages, setMessages] = useState([
    { id: "welcome", role: "assistant", data: { action: "welcome", reply: t("assistant.subtitle") } },
  ]);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-md pt-md">
        <form className="flex items-center gap-xs rounded-2xl border border-outline-variant bg-surface-container-lowest p-xs shadow-lg focus-within:ring-2 focus-within:ring-primary">
          <div className="flex flex-grow items-center px-sm">
            <span className="material-symbols-outlined text-outline">chat</span>
            <input
              className="w-full bg-transparent px-sm py-sm text-body-md focus:outline-none"
              placeholder={t("assistant.placeholder")}
              aria-label={t("assistant.placeholder")}
            />
          </div>
          <button
            type="submit"
            className="flex items-center gap-sm rounded-xl bg-primary px-lg py-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
          >
            <span className="hidden sm:inline">{t("assistant.send")}</span>
            <span className="material-symbols-outlined text-sm">send</span>
          </button>
        </form>
      </div>
    </div>
  );
}
