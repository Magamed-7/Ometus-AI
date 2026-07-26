export default function Skeleton({ className = "" }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-lg bg-surface-container-high ${className}`}
    />
  );
}
