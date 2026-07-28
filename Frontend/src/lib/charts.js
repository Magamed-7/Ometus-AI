import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";

// регистрируем поимённо, а не через `registerables`: в бандл попадает только то,
// что реально рисуется, круговых и радарных диаграмм здесь нет
Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip
);

// Палитры прогнаны валидатором на обеих подложках (белая и #0a0e12) и проходят
// все шесть проверок: полоса светлоты, насыщенность, различимость при дальтонизме,
// различимость при обычном зрении и контраст с фоном. Менять цвета по одному нельзя —
// проверка идёт для набора целиком, соседние пары считаются попарно.
const LIGHT = ["#2563EB", "#0D9488", "#D97706", "#9333EA"];
const DARK = ["#4585EF", "#12A594", "#C07E1E", "#A65CE8"];

// порядок закреплён за сущностью, а не за местом в списке: если фильтр уберёт
// «отменённые», у остальных статусов цвет не поедет
export const STATUS_ORDER = ["booked", "completed", "cancelled", "no_show"];

export function isDark() {
  return document.documentElement.classList.contains("dark");
}

export function palette() {
  return isDark() ? DARK : LIGHT;
}

export function statusColor(status) {
  const index = STATUS_ORDER.indexOf(status);
  return palette()[index < 0 ? 0 : index];
}

function cssVar(name, fallback) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

export function chartInk() {
  return {
    text: cssVar("--color-on-surface", isDark() ? "#e2e8f0" : "#191c20"),
    muted: cssVar("--color-on-surface-variant", isDark() ? "#94a3b8" : "#42474e"),
    grid: isDark() ? "rgba(148, 163, 184, 0.16)" : "rgba(66, 71, 78, 0.14)",
    surface: cssVar("--color-surface-container-lowest", isDark() ? "#0a0e12" : "#ffffff"),
  };
}

// общие настройки: сетка приглушена, оси без рамки, подпись не на каждой точке —
// цифры читаются во всплывающей подсказке, а не заслоняют сам график
export function baseOptions({ stacked = false, currency = false } = {}) {
  const ink = chartInk();

  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          color: ink.muted,
          usePointStyle: true,
          pointStyle: "circle",
          boxWidth: 8,
          padding: 16,
          font: { family: "Inter, sans-serif", size: 12 },
        },
      },
      tooltip: {
        backgroundColor: ink.surface,
        titleColor: ink.text,
        bodyColor: ink.muted,
        borderColor: ink.grid,
        borderWidth: 1,
        padding: 12,
        cornerRadius: 12,
        usePointStyle: true,
        callbacks: currency
          ? { label: (item) => `${item.dataset.label}: $${Number(item.raw).toFixed(4)}` }
          : undefined,
      },
    },
    scales: {
      x: {
        stacked,
        grid: { display: false },
        border: { display: false },
        ticks: { color: ink.muted, font: { family: "Inter, sans-serif", size: 11 } },
      },
      y: {
        stacked,
        beginAtZero: true,
        grid: { color: ink.grid },
        border: { display: false },
        ticks: {
          color: ink.muted,
          font: { family: "Inter, sans-serif", size: 11 },
          precision: currency ? undefined : 0,
        },
      },
    },
  };
}

// столбики тонкие, с скруглённым верхом, и разделены двухпиксельным зазором
// цвета подложки — иначе соседние сегменты стопки сливаются в одну полосу
export const BAR_MARK = {
  borderRadius: 4,
  borderSkipped: false,
  maxBarThickness: 28,
  borderWidth: 2,
};

export const LINE_MARK = {
  borderWidth: 2,
  pointRadius: 0,
  pointHoverRadius: 5,
  pointHitRadius: 16,
  tension: 0.3,
};
