import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import ChatHistoryList from "../components/ChatHistoryList.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import { Field } from "../components/Field.jsx";
import Button from "../components/Button.jsx";
import Modal from "../components/Modal.jsx";
import {
  askAssistant,
  deleteConversation,
  getConversationHistory,
  listConversations,
  rateReply,
  renameConversation,
  startConversation,
} from "../lib/api/ai.js";
import { errorText } from "../lib/api/errorText.js";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { clock, formatDate } from "../lib/format.js";
import { useI18n } from "../lib/i18n.jsx";
import { scrollBehavior } from "../lib/motion.js";
import { useToast } from "../lib/toast.jsx";

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
        <p className="whitespace-pre-line text-body-md">{text}</p>
      </div>
    </div>
  );
}

function AnswerHeading({ text }) {
  return (
    <p className="px-xs text-label-md font-bold uppercase tracking-wide text-on-surface-variant">
      {text}
    </p>
  );
}

function DoctorsAnswer({ t, data, onPickDoctor }) {
  const heading = data.specialization
    ? t("assistant.doctorsHeading", { specialization: data.specialization })
    : t("assistant.doctorsHeadingPlain");

  return (
    <div className="flex flex-col gap-xs">
      <AnswerHeading text={heading} />
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

const slotKey = (slot) => `${slot.date} ${slot.time}`;

// сервер отдаёт слоты в порядке рекомендации — сначала часы, в которые пациент
// обычно ходит. Сетку времени так читать нельзя (09:40 приходится искать глазами),
// поэтому показываем по возрастанию, а рекомендованные помечаем. Если порядок
// сервера и так хронологический, никакой рекомендации не было — метки не ставим
function recommendedSlots(slots) {
  const sorted = [...slots].sort((a, b) => slotKey(a).localeCompare(slotKey(b)));
  const reordered = slots.some((slot, index) => slotKey(slot) !== slotKey(sorted[index]));

  return new Set(reordered ? slots.slice(0, 3).map(slotKey) : []);
}

function SlotsAnswer({ t, lang, data, onPickSlot }) {
  const byDate = {};
  const recommended = recommendedSlots(data.slots);

  for (const slot of data.slots) {
    (byDate[slot.date] = byDate[slot.date] || []).push(slot);
  }

  for (const date in byDate) {
    byDate[date].sort((a, b) => a.time.localeCompare(b.time));
  }

  const firstDate = data.slots[0]?.date;
  const heading = data._doctorName
    ? t("assistant.slotsHeadingDoctor", {
        doctor: data._doctorName,
        date: formatDate(firstDate, lang),
      })
    : t("assistant.slotsHeading", { date: formatDate(firstDate, lang) });

  return (
    <div className="flex flex-col gap-sm rounded-xl border border-outline-variant bg-surface-container-low p-sm">
      <AnswerHeading text={heading} />
      {Object.entries(byDate).map(([date, slots]) => (
        <div key={date}>
          <p className="mb-xs text-label-md font-semibold text-on-surface-variant">
            {formatDate(date, lang)}
          </p>
          <div className="grid grid-cols-3 gap-xs sm:grid-cols-4">
            {slots.map((slot) => {
              const isRecommended = recommended.has(slotKey(slot));

              return (
                <button
                  key={`${date}-${slot.time}`}
                  type="button"
                  onClick={() => onPickSlot(data, slot)}
                  title={isRecommended ? t("assistant.usualTime") : undefined}
                  className={`flex items-center justify-center gap-1 rounded-lg border py-2 text-label-md font-bold transition-colors hover:border-primary hover:text-primary ${
                    isRecommended
                      ? "border-primary/50 bg-primary-container/15 text-primary"
                      : "border-outline-variant bg-surface-container-lowest text-on-surface"
                  }`}
                >
                  {clock(slot.time)}
                  {isRecommended && (
                    <span className="sr-only">{t("assistant.usualTime")}</span>
                  )}
                </button>
              );
            })}
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

function Rating({ t, rating, onRate }) {
  const options = [
    { value: "helpful", icon: "thumb_up", label: t("assistant.helpful") },
    { value: "not_helpful", icon: "thumb_down", label: t("assistant.notHelpful") },
  ];

  return (
    <div className="flex items-center gap-1">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onRate(option.value)}
          aria-label={option.label}
          aria-pressed={rating === option.value}
          title={option.label}
          className={`grid h-8 w-8 place-items-center rounded-lg transition-colors hover:bg-surface-container ${
            rating === option.value ? "text-primary" : "text-on-surface-variant/70"
          }`}
        >
          <span
            aria-hidden="true"
            className={`material-symbols-outlined text-lg ${
              rating === option.value ? "filled" : ""
            }`}
          >
            {option.icon}
          </span>
        </button>
      ))}
    </div>
  );
}

function AssistantBubble({ data, t, lang, rating, onRate, onPickDoctor, onPickSlot, onAsk }) {
  if (data.action === "emergency") return <EmergencyAnswer t={t} reply={data.reply} />;

  const isError = data.action === "error";
  const isClarify = data.action === "clarify";

  return (
    <div className="flex max-w-[85%] gap-sm">
      <BotAvatar />
      <div className="flex w-full flex-col gap-sm">
        {data.reply && (
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
        )}
        {/* врачи приходят не только с action doctors: уточняющий вопрос по нескольким
            специализациям тоже несёт карточки, чтобы пациент сразу видел, кто есть */}
        {data.doctors?.length > 0 && (
          <DoctorsAnswer t={t} data={data} onPickDoctor={onPickDoctor} />
        )}
        {data.suggestions?.length > 0 && (
          <div className="flex flex-wrap gap-xs">
            {data.suggestions.map((name) => (
              <button
                key={name}
                type="button"
                onClick={() => onAsk(name)}
                className="rounded-full border border-outline-variant bg-surface-container-low px-md py-1.5 text-label-md font-semibold text-on-surface-variant transition-colors hover:border-primary hover:text-primary"
              >
                {name}
              </button>
            ))}
          </div>
        )}
        {data.action === "slots" && data.slots?.length > 0 && (
          <SlotsAnswer t={t} lang={lang} data={data} onPickSlot={onPickSlot} />
        )}
        {data.action === "booked" && data.appointment && (
          <BookedAnswer t={t} lang={lang} appointment={data.appointment} />
        )}
        {data.message_id && <Rating t={t} rating={rating} onRate={onRate} />}
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

// история хранит только текст сообщений: карточки врачей и сетка слотов собираются
// из ответа на живой запрос и в базе не лежат, поэтому старая переписка
// восстанавливается текстом — выдумывать под неё врачей и время нельзя
function restoreMessages(messages) {
  return messages.map((message) =>
    message.role === "user"
      ? { id: `u-${message.id}`, role: "user", data: { text: message.content } }
      : {
          id: `a-${message.id}`,
          role: "assistant",
          data: { action: "history", reply: message.content, message_id: message.id },
        }
  );
}

export default function Assistant() {
  const { t, lang } = useI18n();
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const isPatient = user?.role === "patient";

  const [chats, setChats] = useState([]);
  const [chatsLoading, setChatsLoading] = useState(false);
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [ratings, setRatings] = useState({});
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [listOpen, setListOpen] = useState(false);
  const [renaming, setRenaming] = useState(null);
  const [renameTitle, setRenameTitle] = useState("");
  const [removing, setRemoving] = useState(null);
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: scrollBehavior() });
  }, [messages, sending]);

  const loadChats = useCallback(async () => {
    const list = await listConversations();
    setChats(list);
    return list;
  }, []);

  const openChat = useCallback(
    async (id) => {
      setChatId(id);
      setHistoryLoading(true);

      try {
        const history = await getConversationHistory(id);
        setMessages(restoreMessages(history.messages));
      } catch (e) {
        setMessages([]);
        toast.error(errorText(t, e));
      } finally {
        setHistoryLoading(false);
      }
    },
    [t, toast]
  );

  // при входе на страницу открываем последний диалог: в этом и смысл памяти —
  // пациент продолжает разговор, а не начинает каждый раз с нуля
  useEffect(() => {
    if (!isPatient) {
      setChats([]);
      setChatId(null);
      setMessages([]);
      return;
    }

    let cancelled = false;
    setChatsLoading(true);

    loadChats()
      .then((list) => {
        if (cancelled || list.length === 0) return;
        return openChat(list[0].id);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setChatsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isPatient, loadChats, openChat]);

  const runAsk = async (payload, userText, meta) => {
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
      const answer = await askAssistant({
        ...payload,
        conversation_id: chatId,
        language: lang,
      });
      if (payload.doctor_id) answer._doctorId = payload.doctor_id;
      if (meta) Object.assign(answer, meta);
      setChatId(answer.conversation_id);
      setMessages((list) => [
        ...list,
        { id: `a-${Date.now()}`, role: "assistant", data: answer },
      ]);
      loadChats().catch(() => {});
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
    runAsk(
      { message: t("assistant.showSlots"), doctor_id: doctor.doctor_id },
      doctor.full_name,
      { _doctorName: doctor.full_name }
    );
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

  const onRate = async (messageId, feedback) => {
    setRatings((current) => ({ ...current, [messageId]: feedback }));

    try {
      await rateReply(messageId, feedback);
      toast.success(t("assistant.rated"));
    } catch (e) {
      setRatings((current) => ({ ...current, [messageId]: undefined }));
      toast.error(errorText(t, e));
    }
  };

  const onNewChat = async () => {
    setListOpen(false);

    try {
      const chat = await startConversation();
      setChatId(chat.id);
      setMessages([]);
      await loadChats();
    } catch (e) {
      toast.error(errorText(t, e));
    }
  };

  const onSelectChat = (chat) => {
    setListOpen(false);
    if (chat.id !== chatId) openChat(chat.id);
  };

  const onRenameChat = (chat) => {
    setListOpen(false);
    setRenameTitle(chat.title || "");
    setRenaming(chat);
  };

  const submitRename = async (e) => {
    e.preventDefault();
    const title = renameTitle.trim();
    if (!title) return;

    setBusy(true);

    try {
      await renameConversation(renaming.id, title);
      await loadChats();
      setRenaming(null);
    } catch (e) {
      toast.error(errorText(t, e));
    } finally {
      setBusy(false);
    }
  };

  const confirmDelete = async () => {
    setBusy(true);

    try {
      await deleteConversation(removing.id);
      const list = await loadChats();
      setRemoving(null);

      if (removing.id === chatId) {
        if (list.length > 0) {
          await openChat(list[0].id);
        } else {
          setChatId(null);
          setMessages([]);
        }
      }
    } catch (e) {
      toast.error(errorText(t, e));
    } finally {
      setBusy(false);
    }
  };

  const chatPanel = (
    <ChatHistoryList
      chats={chats}
      activeId={chatId}
      loading={chatsLoading}
      onSelect={onSelectChat}
      onNew={onNewChat}
      onRename={onRenameChat}
      onDelete={(chat) => {
        setListOpen(false);
        setRemoving(chat);
      }}
    />
  );

  const empty = messages.length === 0 && !historyLoading;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 gap-md px-sm py-sm md:px-lg">
      {isPatient && (
        <aside className="hidden w-72 shrink-0 lg:block">
          <div className="sticky top-md max-h-[calc(100vh-6rem)] overflow-y-auto rounded-xl border border-outline-variant bg-surface-container-low p-sm">
            <h2 className="mb-sm px-xs text-label-md font-bold uppercase tracking-wide text-on-surface-variant">
              {t("assistant.chats")}
            </h2>
            {chatPanel}
          </div>
        </aside>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="mb-sm flex items-start gap-sm rounded-xl border border-outline-variant bg-surface-container-low p-sm">
          <span aria-hidden="true" className="material-symbols-outlined text-secondary">info</span>
          <div className="min-w-0 flex-1">
            <p className="text-label-md font-bold text-on-surface">{t("assistant.title")}</p>
            <p className="text-label-md text-on-surface-variant">{t("assistant.disclaimer")}</p>
          </div>
          {isPatient && (
            <button
              type="button"
              onClick={() => setListOpen(true)}
              className="flex shrink-0 items-center gap-1 rounded-lg border border-outline-variant px-sm py-1.5 text-label-md font-semibold text-on-surface-variant hover:border-primary hover:text-primary lg:hidden"
            >
              <span aria-hidden="true" className="material-symbols-outlined text-lg">history</span>
              {t("assistant.chats")}
            </button>
          )}
        </div>

        {user && !isPatient && (
          <div
            role="status"
            className="mb-sm rounded-xl border border-outline-variant bg-surface-container-low p-sm text-label-md text-on-surface-variant"
          >
            {t("assistant.patientsOnly")}
          </div>
        )}

        <div className="flex flex-grow flex-col gap-md pb-xl">
          {empty && (
            <AssistantBubble
              data={{ action: "welcome", reply: t("assistant.subtitle") }}
              t={t}
              lang={lang}
              onPickDoctor={onPickDoctor}
              onPickSlot={onPickSlot}
            />
          )}
          {historyLoading && <ThinkingBubble label={t("common.loading")} />}
          {messages.map((msg) =>
            msg.role === "user" ? (
              <UserBubble key={msg.id} text={msg.data.text} />
            ) : (
              <AssistantBubble
                key={msg.id}
                data={msg.data}
                t={t}
                lang={lang}
                rating={ratings[msg.data.message_id]}
                onRate={(feedback) => onRate(msg.data.message_id, feedback)}
                onPickDoctor={onPickDoctor}
                onPickSlot={onPickSlot}
                onAsk={send}
              />
            )
          )}
          {sending && <ThinkingBubble label={t("assistant.thinking")} />}
          <div ref={endRef} />
        </div>

        <div className="sticky bottom-md pt-md">
          {empty && !sending && (
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
                disabled={sending || (user && !isPatient)}
                className="focus-in-parent w-full bg-transparent px-sm py-sm text-body-md disabled:opacity-60"
                placeholder={t("assistant.placeholder")}
                aria-label={t("assistant.placeholder")}
              />
            </div>
            <button
              type="submit"
              disabled={sending || !input.trim() || (user && !isPatient)}
              className="flex items-center gap-sm rounded-xl bg-primary px-lg py-sm font-semibold text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="hidden sm:inline">{t("assistant.send")}</span>
              <span aria-hidden="true" className="material-symbols-outlined text-sm">send</span>
            </button>
          </form>
        </div>
      </div>

      {listOpen && (
        <Modal title={t("assistant.chats")} onClose={() => setListOpen(false)}>
          {chatPanel}
        </Modal>
      )}

      {renaming && (
        <Modal
          title={t("assistant.renameChat")}
          onClose={() => setRenaming(null)}
          footer={
            <>
              <Button variant="outline" onClick={() => setRenaming(null)} className="flex-1">
                {t("common.cancel")}
              </Button>
              <Button
                loading={busy}
                disabled={!renameTitle.trim()}
                onClick={submitRename}
                className="flex-1"
              >
                {t("common.save")}
              </Button>
            </>
          }
        >
          <form onSubmit={submitRename}>
            <Field
              label={t("assistant.chatTitle")}
              value={renameTitle}
              maxLength={120}
              onChange={(e) => setRenameTitle(e.target.value)}
              autoFocus
            />
          </form>
        </Modal>
      )}

      {removing && (
        <ConfirmDialog
          title={t("assistant.deleteChat")}
          text={t("assistant.deleteChatText", {
            title: removing.title || t("assistant.untitled"),
          })}
          loading={busy}
          onConfirm={confirmDelete}
          onClose={() => setRemoving(null)}
        />
      )}
    </div>
  );
}
