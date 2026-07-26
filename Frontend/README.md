# Ometus Clinic — фронтенд

Интерфейс к бэкенду Ometus (`../Backend`): поиск врачей, запись на приём, кабинеты пациента,
врача и администратора, AI-ассистент. Три языка (русский, тоҷикӣ, English), светлая и тёмная тема.

## Стек

| | |
|---|---|
| Сборка | Vite 5 |
| Каркас | React 18 + react-router-dom 6 |
| Стили | Tailwind 4 (`@tailwindcss/vite`), токены Material 3 от исходного цвета `#006194` |
| Иконки | Material Symbols Outlined |
| Языки | свой i18n на контексте (`useT`, `lib/locales/*`), русский по умолчанию и как запасной |

Сторонних UI-библиотек нет: кнопки, поля, модалки и статусы написаны руками в `src/components`.

## Запуск

Нужен Node 18+ и поднятый бэкенд на `http://127.0.0.1:8000`.

```bash
npm install
cp .env.example .env      # при необходимости поменяйте VITE_API_URL
npm run dev               # http://localhost:5173
```

Бэкенд разрешает CORS только с `http://localhost:5173` (см. `CORS_ORIGINS` в `Backend/.env`),
поэтому dev-сервер должен слушать именно этот порт. Если запускать `npm run preview` (порт 4173),
запросы к API упрутся в CORS — это не поломка фронтенда.

### Сборка

```bash
npm run build             # dist/
npm run preview           # раздать собранное локально
```

`VITE_API_URL` подставляется **на сборке**: после `npm run build` поменять адрес бэкенда нельзя,
нужно пересобрать.

### Docker

```bash
docker build -t ometus-frontend --build-arg VITE_API_URL=http://127.0.0.1:8000 .
docker run -p 8080:80 ometus-frontend
```

Двухступенчатая сборка: `node:22-alpine` собирает, `nginx:alpine` раздаёт. В `nginx.conf` есть
`try_files … /index.html` — без него перезагрузка страницы на вложенном маршруте вроде
`/admin/appointments` вернула бы 404 от nginx.

## Что где лежит

```
src/
  main.jsx                провайдеры: тема → язык → тосты → роутер → авторизация
  App.jsx                 все маршруты
  styles.css              @theme со светлыми и тёмными токенами, focus-visible, reduced-motion
  lib/
    config.js             VITE_API_URL
    i18n.jsx              useT / useI18n, подстановка {var}
    theme.jsx             класс dark на html, память в localStorage
    format.js             даты, время, телефон под язык
    motion.js             prefers-reduced-motion
    roving.js             шаг по стрелкам для сеток выбора
    avatar.js             цвет подложки под инициалы врача
    password.js           генерация пароля врача (см. «Заглушки»)
    toast.jsx             уведомления
    locales/              ru.js, tg.js, en.js
    auth/                 tokens.js (localStorage), AuthContext.jsx
    api/                  client.js + модуль на каждый раздел API
  components/             оболочка (TopNav, BottomNav, Footer, Layout) и общие элементы
  pages/                  страницы; doctor/ — кабинет врача, admin/ — админка
```

`Plan/` (план, список заглушек, макет Stitch) в git не попадает — он в `.gitignore`.

## Маршруты и роли

| Маршрут | Кто видит |
|---|---|
| `/`, `/doctors`, `/doctors/:id`, `/booking/:doctorId`, `/assistant` | все |
| `/login`, `/register`, `/verify-email` | все |
| `/account` | авторизованный (кабинет пациента) |
| `/doctor/today`, `/doctor/schedule` | роль `doctor` |
| `/admin/{filials,departments,doctors,appointments,reports}` | роль `admin` |

Разграничение на фронте — `ProtectedRoute` и `RoleRoute`; настоящая проверка прав всё равно
на бэкенде, интерфейс просто не показывает лишнего.

## Работа с API

`lib/api/client.js` добавляет `Authorization: Bearer`, разбирает конверт ошибок
`{error: {code, message, status}}` и на 401 сам обновляет токен через `POST /api/auth/refresh`,
после чего один раз повторяет запрос. Если refresh тоже не годится — токены чистятся и
пользователь уходит на `/login`.

Ошибки переводятся **по коду** (`errors.*` в локалях), а текст с сервера показывается только
если кода нет в словаре: бэкенд отвечает по-русски, а интерфейс трёхъязычный.

## Демо-доступы

Пароль у всех — `secret1234`:

| Почта | Роль |
|---|---|
| `patient@ometus.tj` | пациент |
| `admin@ometus.tj` | администратор |
| `farkhod.saidov@ometus.tj` и ещё 30 | врачи |

## Доступность

Skip-link на содержимое, видимая обводка фокуса, стрелки в календаре и сетке слотов
(`role="radiogroup"` + roving tabindex), `aria-hidden` на декоративных иконках — иначе скринридер
читает лигатуры вроде «check_circle», — озвучка загрузки (`role="status"`) и ошибок (`role="alert"`),
поддержка `prefers-reduced-motion`. Раскладка проверена на 375px: горизонтальной прокрутки страницы
нет, а таблицы админки скроллятся внутри своего контейнера.

## Заглушки

Актуальный список — `Plan/STUBS.md` (вне git). Коротко о том, чего нет в API:

- **повторная отправка кода подтверждения** — эндпоинта нет, на странице честная подсказка вместо
  кнопки, которая ничего не делает;
- **фото, стаж и рейтинг врача** — таких полей в `doctors` нет, поэтому блоки не рисуются вовсе:
  выдумывать цифры о настоящем враче нельзя;
- **часы работы филиала** — полей нет, вместо выдуманного «08:00 – 20:00» показывается настоящий
  телефон филиала;
- **пароль врача** генерирует браузер (`lib/password.js`) и показывает администратору один раз:
  `POST /api/admin/doctors` ждёт пароль в запросе и обратно его не возвращает;
- **документы пациента** — таблицы в базе нет, вкладка честно пустая (по ТЗ §10 это вне рамок).
