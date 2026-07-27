import { formatDateShort } from "../lib/format.js";
import { useI18n } from "../lib/i18n.jsx";
import Skeleton from "./Skeleton.jsx";

export default function ChatHistoryList({
  chats,
  activeId,
  loading,
  onSelect,
  onNew,
  onRename,
  onDelete,
}) {
  const { t, lang } = useI18n();

  return (
    <div className="flex h-full flex-col gap-sm">
      <button
        type="button"
        onClick={onNew}
        className="flex min-h-11 items-center justify-center gap-2 rounded-xl bg-primary px-md text-label-md font-bold text-on-primary transition-all active:scale-95"
      >
        <span aria-hidden="true" className="material-symbols-outlined text-lg">add_comment</span>
        {t("assistant.newChat")}
      </button>

      {loading ? (
        <div className="flex flex-col gap-xs">
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
        </div>
      ) : chats.length === 0 ? (
        <p className="px-xs text-label-md text-on-surface-variant">{t("assistant.noChats")}</p>
      ) : (
        <ul className="flex flex-col gap-xs overflow-y-auto">
          {chats.map((chat) => {
            const active = chat.id === activeId;

            return (
              <li
                key={chat.id}
                className={`group flex items-start gap-1 rounded-xl border p-xs transition-colors ${
                  active
                    ? "border-primary bg-primary-container/15"
                    : "border-outline-variant bg-surface-container-low hover:border-primary"
                }`}
              >
                <button
                  type="button"
                  onClick={() => onSelect(chat)}
                  aria-current={active ? "true" : undefined}
                  className="min-w-0 flex-1 text-left"
                >
                  <span className="block truncate text-label-md font-semibold text-on-surface">
                    {chat.title || t("assistant.untitled")}
                  </span>
                  {chat.preview && (
                    <span className="mt-0.5 block truncate text-label-md font-normal text-on-surface-variant">
                      {chat.preview}
                    </span>
                  )}
                  <span className="mt-0.5 block text-label-md font-normal text-on-surface-variant/70">
                    {formatDateShort(chat.updated_at, lang)}
                  </span>
                </button>
                <span className="flex shrink-0 flex-col">
                  <button
                    type="button"
                    onClick={() => onRename(chat)}
                    aria-label={t("assistant.renameChat")}
                    title={t("assistant.renameChat")}
                    className="grid h-8 w-8 place-items-center rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-primary"
                  >
                    <span aria-hidden="true" className="material-symbols-outlined text-lg">edit</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(chat)}
                    aria-label={t("assistant.deleteChat")}
                    title={t("assistant.deleteChat")}
                    className="grid h-8 w-8 place-items-center rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-error"
                  >
                    <span aria-hidden="true" className="material-symbols-outlined text-lg">delete</span>
                  </button>
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
