const VARIANTS = {
  primary: "bg-primary text-on-primary hover:bg-primary-container shadow-sm",
  outline: "border border-primary text-primary hover:bg-primary hover:text-on-primary",
  danger: "bg-error text-on-error hover:brightness-110",
  ghost: "text-primary hover:bg-surface-container",
};

export default function Button({
  variant = "primary",
  icon,
  loading = false,
  disabled = false,
  children,
  className = "",
  ...props
}) {
  return (
    <button
      disabled={loading || disabled}
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-md text-label-md font-bold transition-all active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {loading ? (
        <span className="material-symbols-outlined animate-spin text-lg">progress_activity</span>
      ) : icon ? (
        <span className="material-symbols-outlined text-lg">{icon}</span>
      ) : null}
      {children}
    </button>
  );
}
