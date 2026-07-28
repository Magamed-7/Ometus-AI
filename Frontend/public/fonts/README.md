# Шрифт иконок

`material-symbols-subset.woff2` — Material Symbols Outlined, урезанный до иконок,
которые реально встречаются в коде. 77 КБ против 3,5 МБ полного вариативного шрифта.

## Зачем локально, а не с Google Fonts

Иконка рисуется лигатурой: в разметке стоит слово `search`, глиф подставляет шрифт.
Пока шрифт не загрузился, на экране висят сами слова — на главной это выглядело как
«search», «logout», «language» в шапке и «health_and_safety» во весь блок hero.
С Google Fonts отваливались обе половины сразу: и таблица стилей с `font-family`,
и сам woff2, а `Ctrl+F5` сбрасывает кэш и показывал поломку каждый раз.

Локальный файл + `font-display: block` в `src/styles.css` убирают и сеть, и мигание.

## Как пересобрать после добавления новой иконки

Новой иконки в сабсете нет — вместо неё снова будет слово. После добавления:

```bash
# 1. собрать список иконок из кода — ОБА способа записи
ICONS=$({ grep -rhoP 'material-symbols-outlined[^>]*>\s*\K[a-z0-9_]+' src;
          grep -rhoP 'icon\s*[:=]\s*["'"'"']\K[a-z0-9_]+' src; } | sort -u | paste -sd,)

# 2. забрать сабсет (имена обязаны идти по алфавиту, иначе 400)
curl -A "Mozilla/5.0" \
  "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=$ICONS&display=block" \
  -o ms.css

# 3. скачать woff2 по ссылке из ms.css
curl -o public/fonts/material-symbols-subset.woff2 "$(grep -o 'https://fonts.gstatic.com/[^)]*' ms.css)"
```

**Второй grep в шаге 1 обязателен.** Без него из списка выпадают иконки, которые
передаются пропом — `icon="folder_open"` у `EmptyState` и `icon: "home_health"`
в массивах `BottomNav`/`TopNav`. Именно так 28.07.2026 в сабсет не попали 13 иконок,
и вся нижняя навигация на телефоне показывала слова `home_health`, `medical_services`,
`calendar_add_on`, `account_circle` вместо значков.

## Как проверить, что ничего не потерялось

Ширина глифа равна кеглю. Если лигатуры в шрифте нет, браузер рисует само слово,
и оно заметно шире. В консоли на любой странице:

```js
const bad = [];
for (const n of ["home_health", "science", "account_circle" /* … весь список */]) {
  const s = document.createElement("span");
  s.className = "material-symbols-outlined";
  s.style.cssText = "position:absolute;left:-9999px;font-size:24px";
  s.textContent = n;
  document.body.appendChild(s);
  if (s.getBoundingClientRect().width > 40) bad.push(n);
  s.remove();
}
console.log(bad); // должен быть пустым
```

## Что сейчас в сабсете (74)

```
account_circle, add, add_comment, admin_panel_settings, apartment, arrow_back,
beach_access, calendar_add_on, calendar_month, call, cancel, chat, check, check_circle,
chevron_left, chevron_right, clinical_notes, close, content_copy, dark_mode, delete,
directions, edit, edit_calendar, emergency, error, event, event_available, event_busy,
event_note, expand_more, filter_list, folder_open, groups, health_and_safety, history,
home_health, inbox, info, language, light_mode, local_hospital, location_on, logout,
mail, map, medical_services, meeting_room, menu, monitoring, person, person_add,
person_off, photo_camera, pin_drop, progress_activity, refresh, save, schedule, science,
search, search_off, send, smart_toy, star, stethoscope, support_agent, task_alt,
thumb_down, thumb_up, troubleshoot, verified, wifi_off, workspace_premium
```
