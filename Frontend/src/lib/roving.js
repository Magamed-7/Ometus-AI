export function nextIndex(key, index, length) {
  if (length === 0) return null;
  if (key === "ArrowLeft" || key === "ArrowUp") return Math.max(0, index - 1);
  if (key === "ArrowRight" || key === "ArrowDown") return Math.min(length - 1, index + 1);
  if (key === "Home") return 0;
  if (key === "End") return length - 1;
  return null;
}
