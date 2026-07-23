import { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext({ theme: "light", toggle: () => {} });

function readTheme() {
  try {
    const saved = localStorage.getItem("ometus-theme");
    if (saved === "dark" || saved === "light") return saved;
  } catch (e) {}
  return "light";
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(readTheme);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    root.classList.toggle("light", theme !== "dark");
    try {
      localStorage.setItem("ometus-theme", theme);
    } catch (e) {}
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return <ThemeContext.Provider value={{ theme, toggle }}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);
