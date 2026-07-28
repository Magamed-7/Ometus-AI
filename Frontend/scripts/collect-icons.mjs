import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const [src, catalogue] = process.argv.slice(2);

if (!src || !catalogue) {
  console.error("использование: node scripts/collect-icons.mjs <src> <icons_meta.json>");
  process.exit(1);
}

// 1. текст прямо между тегами: <span className="material-symbols-outlined">search</span>
const INLINE = /material-symbols-outlined[^>]*>\s*([a-z0-9_]+)\s*</g;
// 2. иконка приходит пропом: icon="folder_open" / icon: "home_health"
const PROP = /icon\s*[:=]\s*["']([a-z0-9_]+)["']/g;
// 3. иконка выбирается выражением: {show ? "visibility_off" : "visibility"}
const EXPR = /material-symbols-outlined[^>]*>\s*\{([\s\S]*?)\}\s*</g;
const STRING = /["']([a-z0-9_]+)["']/g;

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return walk(path);
    return /\.jsx?$/.test(name) ? [path] : [];
  });
}

const raw = readFileSync(catalogue, "utf8");
const known = new Set(JSON.parse(raw.slice(raw.indexOf("{"))).icons.map((icon) => icon.name));

const found = new Set();

for (const path of walk(src)) {
  const text = readFileSync(path, "utf8");
  for (const [, name] of text.matchAll(INLINE)) found.add(name);
  for (const [, name] of text.matchAll(PROP)) found.add(name);
  for (const [, expression] of text.matchAll(EXPR)) {
    for (const [, name] of expression.matchAll(STRING)) found.add(name);
  }
}

// третий шаблон хватает из выражения все строки подряд, включая условие
// (`theme === "dark" ? ...`), поэтому имена сверяем с официальным каталогом:
// незнакомое имя роняет весь запрос сабсета в 400, и виноватого потом искать долго
const icons = [...found].filter((name) => known.has(name)).sort();
const dropped = [...found].filter((name) => !known.has(name)).sort();

console.log(icons.join(","));
console.error(`иконок: ${icons.length}`);
console.error(`отброшено как не-иконки: ${dropped.join(", ") || "нет"}`);
