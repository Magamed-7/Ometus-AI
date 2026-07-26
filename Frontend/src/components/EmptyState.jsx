export default function EmptyState({ icon = "inbox", title, text, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-outline-variant px-md py-xl text-center">
      <span aria-hidden="true" className="material-symbols-outlined text-5xl text-on-surface-variant/60">{icon}</span>
      {title && <p className="text-headline-md font-semibold text-on-surface">{title}</p>}
      {text && <p className="max-w-note text-body-md text-on-surface-variant">{text}</p>}
      {action}
    </div>
  );
}
