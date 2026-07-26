import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    target: "es2020",
    sourcemap: false,
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        // react и роутер меняются раз в полгода, а код приложения — каждый коммит:
        // держим их отдельными чанками, чтобы у вернувшегося пользователя они брались
        // из кеша. Раскладываем по id модуля, а не списком имён: со списком rollup
        // утаскивал react-dom в чанк роутера и «react» получался пустым на 30 байт
        manualChunks(id) {
          if (!id.includes("node_modules")) return null;
          if (id.includes("react-router")) return "router";
          return "react";
        },
      },
    },
  },
  server: {
    port: 5173,
  },
  preview: {
    port: 4173,
  },
});
