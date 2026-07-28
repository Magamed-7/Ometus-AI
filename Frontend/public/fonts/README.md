# Шрифт иконок

`material-symbols-subset.woff2` — Material Symbols Outlined, урезанный до иконок,
которые реально встречаются в коде. 82 КБ против 3,5 МБ полного вариативного шрифта.

## Зачем локально, а не с Google Fonts

Иконка рисуется лигатурой: в разметке стоит слово `search`, глиф подставляет шрифт.
Пока шрифт не загрузился, на экране висят сами слова — на главной это выглядело как
«search», «logout», «language» в шапке и «health_and_safety» во весь блок hero.
С Google Fonts отваливались обе половины сразу: и таблица стилей с `font-family`,
и сам woff2, а `Ctrl+F5` сбрасывает кэш и показывал поломку каждый раз.

Локальный файл + `font-display: block` в `src/styles.css` убирают и сеть, и мигание.

## Как пересобрать после добавления новой иконки

Новой иконки в сабсете нет — вместо неё снова будет слово. Список имён собирает
`scripts/collect-icons.mjs`: он смотрит три способа записи и сверяет найденное
с официальным каталогом Material Symbols.

```bash
cd Frontend

# 1. каталог всех существующих имён (нужен, чтобы отсеять не-иконки, см. ниже)
curl -sS -A "Mozilla/5.0" \
  "https://fonts.google.com/metadata/icons?incomplete=true&key=material_symbols" \
  -o /tmp/icons_meta.json

# 2. собрать имена из кода (в stderr — счётчик и что отброшено)
ICONS=$(node scripts/collect-icons.mjs src /tmp/icons_meta.json)

# 3. забрать сабсет. UA обязателен и обязан быть свежим: со старым «Mozilla/5.0»
#    Google отдаёт семь статических ttf вместо одного вариативного woff2,
#    а `font-variation-settings` в styles.css рассчитан именно на вариативный
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
curl -sS -A "$UA" \
  "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=$ICONS&display=block" \
  -o /tmp/ms.css

# 4. скачать woff2 по ссылке из ms.css
curl -sS -o public/fonts/material-symbols-subset.woff2 \
  "$(grep -o 'https://fonts.gstatic.com/[^)]*' /tmp/ms.css)"
```

### Три способа записи, и почему их именно три

| Как записано | Пример | Где |
|---|---|---|
| текстом между тегами | `<span className="material-symbols-outlined">search</span>` | почти везде |
| пропом | `icon="folder_open"`, `icon: "home_health"` | `EmptyState`, `BottomNav`, `AdminShell` |
| выражением | `{show ? "visibility_off" : "visibility"}` | `Field`, `Assistant`, `BottomNav` |

Третий способ раньше не собирался вообще. Из-за него 28.07.2026 в сабсет не попали
`visibility`/`visibility_off` (кнопка «показать пароль» на логине и регистрации
рисовала слово `VISIBILITY` во всю ширину поля) и `help` в ассистенте. Первые два
способа до этого точно так же теряли иконки нижней навигации.

**Сверка с каталогом обязательна.** Третий шаблон вытаскивает из выражения все строки
подряд, включая условие: из `theme === "dark" ? "light_mode" : "dark_mode"` вылезает
и `dark`. Незнакомое имя роняет весь запрос сабсета в 400, и виноватого потом искать
долго — поэтому имена пересекаются с официальным списком, а отброшенное печатается
в stderr, чтобы опечатка в настоящем имени не утонула молча.

## Как проверить, что ничего не потерялось

Ширина глифа равна кеглю. Если лигатуры в шрифте нет, браузер рисует само слово,
и оно заметно шире.

**Проверять обязательно с обходом кэша.** Адрес файла не меняется при пересборке,
поэтому браузер продолжает рисовать старый шрифт и после `Ctrl+F5` — новые иконки
показываются словами, хотя в файле они уже есть. Ложный «не починилось» ловится
именно здесь. Грузим шрифт отдельным `FontFace` с меткой времени в адресе:

```js
const face = new FontFace("MSTest", `url(/fonts/material-symbols-subset.woff2?v=${Date.now()})`);
await face.load();
document.fonts.add(face);

const bad = [];
for (const n of ["home_health", "visibility", "help" /* … весь список */]) {
  const s = document.createElement("span");
  s.style.cssText =
    "position:absolute;left:-9999px;font-family:MSTest;font-size:24px;font-feature-settings:'liga'";
  s.textContent = n;
  document.body.appendChild(s);
  if (s.getBoundingClientRect().width > 40) bad.push(n);
  s.remove();
}
console.log(bad); // должен быть пустым
```

## Что сейчас в сабсете (75)

```
account_circle, add, add_comment, admin_panel_settings, apartment, arrow_back,
beach_access, calendar_add_on, calendar_month, call, cancel, chat, check_circle,
chevron_left, chevron_right, clinical_notes, close, content_copy, dark_mode, delete,
directions, edit, edit_calendar, emergency, error, event, event_available, event_busy,
event_note, expand_more, filter_list, folder_open, groups, health_and_safety, help,
history, home_health, inbox, info, language, light_mode, local_hospital, location_on,
logout, mail, medical_services, meeting_room, monitoring, payments, person, person_add,
person_off, photo_camera, pin_drop, progress_activity, refresh, save, schedule, science,
search, search_off, send, smart_toy, star, stethoscope, table_rows, task_alt, thumb_down,
thumb_up, troubleshoot, verified, visibility, visibility_off, wifi_off, workspace_premium
```

Из прежнего списка ушли `check`, `map`, `menu` и `support_agent` — в коде их больше нет.
