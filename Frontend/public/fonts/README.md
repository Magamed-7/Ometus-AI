# Шрифт иконок

`material-symbols-subset.woff2` — Material Symbols Outlined, урезанный до иконок,
которые реально встречаются в коде. 59 КБ против 3,5 МБ полного вариативного шрифта.

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
# 1. собрать список иконок из кода
ICONS=$(grep -rhoP 'material-symbols-outlined[^>]*>\s*\K[a-z0-9_]+' src \
  | sort -u | paste -sd,)

# 2. забрать сабсет (имена обязаны идти по алфавиту, иначе 400)
curl -A "Mozilla/5.0" \
  "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=$ICONS&display=block" \
  -o ms.css

# 3. скачать woff2 по ссылке из ms.css
curl -o public/fonts/material-symbols-subset.woff2 "$(grep -o 'https://fonts.gstatic.com/[^)]*' ms.css)"
```

Часть иконок задаётся через проп (`icon="folder_open"` у `EmptyState`), их grep из шага 1
не видит — проверь глазами, что они в списке.

## Что сейчас в сабсете

```
add, add_comment, apartment, arrow_back, beach_access, calendar_month, call, chat,
check, check_circle, chevron_left, chevron_right, close, content_copy, dark_mode,
delete, directions, edit, edit_calendar, emergency, event, event_available,
event_busy, event_note, expand_more, filter_list, folder_open, groups,
health_and_safety, history, info, language, light_mode, local_hospital, location_on,
logout, mail, map, meeting_room, menu, monitoring, person, person_add, person_off,
pin_drop, progress_activity, refresh, save, schedule, search, search_off, send,
smart_toy, star, stethoscope, support_agent, task_alt, troubleshoot, verified,
wifi_off, workspace_premium
```
