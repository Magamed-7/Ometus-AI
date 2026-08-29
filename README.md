<div align="center">

# Ometus Clinic

**Clinic management software for a multi-branch medical practice, with an AI assistant that knows when to shut up and tell you to call a doctor.**

Doctors, schedules, appointments, patient records, and a medical AI assistant with a hard-coded emergency guard, running live for a real clinic network.

[**Open ometus.glossa.best**](https://ometus.glossa.best) &nbsp;·&nbsp; [Author: Magamed-7](https://github.com/Magamed-7) &nbsp;·&nbsp; [Email](mailto:teachermaga7@gmail.com)

**[English](#english)** &nbsp;|&nbsp; **[Русский](#русский)** &nbsp;|&nbsp; **[Тоҷикӣ](#тоҷикӣ)**

</div>

---

## English

### What this actually is

Ometus is booking and records software for a clinic that operates across multiple branches (filials), each with its own departments, doctors, and schedules. It handles doctor specialization and department assignment, working schedules and absences, patient records, appointment booking, and an admin audit log. On top of that sits an AI assistant patients can talk to, backed by real conversation history, per-response cost tracking, and a dedicated emergency-detection guard that intercepts anything that looks like a medical emergency before the AI gets to improvise an answer. This runs live for a real clinic, not a mocked demo.

### Architecture

- **FastAPI backend**, organized by domain: `filials`, `departments`, `doctors` (with specialization and schedule/absence models), `patients`, `appointments`, `medical_records`, `users`/`auth`
- **AI assistant subsystem**, isolated under its own `app/ai/` package:
  - `emergency_guard.py` — a hard safety layer that flags emergency-shaped input before the model responds, so the assistant cannot leave a genuine emergency to a chatbot
  - `pricing.py` and `model_ai_metric.py` — every AI call is logged with its cost, so usage is auditable, not a black box
  - `model_conversation.py` / `crud_conversation.py` — full conversation history is persisted, not thrown away after the response
  - `model_ai_feedback.py` — patients can rate assistant responses, feeding back into quality tracking
- **`model_admin_log.py`** — an audit trail of administrative actions, because a clinic's admin panel needs accountability
- **PostgreSQL** with Alembic migrations
- **Email + notifications service** for appointment confirmations and cancellations
- **React frontend** (Vite build)

### What I personally built

I designed the full data model and built the FastAPI backend end to end, including the AI assistant subsystem with its emergency guard and cost-metering, the multi-filial/department/doctor-schedule domain model, the medical records and appointment flow, and the React frontend. I also ran a security pass on this codebase and fixed a real issue where the JWT secret silently fell back to a hardcoded default instead of failing closed, visible in the commit history.

### Running it

```bash
cd Backend
cp .env.example .env   # fill in real secrets, including a real JWT_SECRET_KEY
docker build -t ometus-backend .
docker run --env-file .env -p 8000:8000 ometus-backend
```

The frontend lives in `Frontend/` (`npm install && npm run dev`).

### Contact

Looking at this for a role or a project: [github.com/Magamed-7](https://github.com/Magamed-7) · [teachermaga7@gmail.com](mailto:teachermaga7@gmail.com)

---

## Русский

### Что это

Ometus, это система записи и учёта для клиники, работающей сразу в нескольких филиалах, у каждого свои отделения, врачи и расписания. Система ведёт специализации врачей и привязку к отделениям, рабочие графики и отсутствия, карты пациентов, запись на приём и журнал административных действий. Поверх этого работает AI-ассистент, с которым может общаться пациент: с реальной историей диалогов, учётом стоимости каждого ответа и отдельным защитным модулем, который распознаёт признаки экстренной ситуации раньше, чем модель успеет что-то "придумать" в ответ. Это работает для настоящей клиники, а не в демо-режиме.

### Архитектура

- **Бэкенд на FastAPI**, разложен по доменам: `filials` (филиалы), `departments` (отделения), `doctors` (со специализацией, расписанием и отсутствиями), `patients`, `appointments`, `medical_records`, `users`/`auth`
- **Подсистема AI-ассистента**, вынесена в отдельный пакет `app/ai/`:
  - `emergency_guard.py` — защитный слой, который распознаёт признаки экстренной ситуации до ответа модели, чтобы настоящую неотложку не оставили на чат-бота
  - `pricing.py` и `model_ai_metric.py` — каждый вызов AI логируется вместе со стоимостью, использование прозрачно, а не чёрный ящик
  - `model_conversation.py` / `crud_conversation.py` — вся история диалога сохраняется, а не выбрасывается после ответа
  - `model_ai_feedback.py` — пациенты могут оценивать ответы ассистента, это идёт в отслеживание качества
- **`model_admin_log.py`** — аудит административных действий, потому что админ-панели клиники нужна подотчётность
- **PostgreSQL** с миграциями через Alembic
- **Сервис email и уведомлений** для подтверждений и отмен записи
- **Frontend на React** (сборка на Vite)

### Что сделал лично я

Я спроектировал модель данных и построил бэкенд на FastAPI целиком, включая подсистему AI-ассистента с защитой от экстренных ситуаций и учётом стоимости, доменную модель филиалов/отделений/расписаний врачей, карты пациентов и поток записи на приём, а также фронтенд на React. Также провёл security-аудит кодовой базы и закрыл реальную уязвимость: JWT-секрет незаметно откатывался на захардкоженное значение по умолчанию вместо явного отказа, это видно в истории коммитов.

### Запуск

```bash
cd Backend
cp .env.example .env   # заполнить реальные секреты, включая настоящий JWT_SECRET_KEY
docker build -t ometus-backend .
docker run --env-file .env -p 8000:8000 ometus-backend
```

Фронтенд лежит в `Frontend/` (`npm install && npm run dev`).

### Контакты

Если смотрите этот проект по работе или заказу: [github.com/Magamed-7](https://github.com/Magamed-7) · [teachermaga7@gmail.com](mailto:teachermaga7@gmail.com)

---

## Тоҷикӣ

### Ин чист

Ometus як системаи навбатгирӣ ва баҳисобгирӣ барои клиникаест, ки дар якчанд филиал кор мекунад, ҳар яке бо шуъбаҳо, духтурон ва ҷадвали худ. Система тахассуси духтурон ва тааллуқияти онҳо ба шуъба, ҷадвали корӣ ва набудани духтурро (absence), карти беморон, навбатгирӣ ва журнали амалҳои маъмуриро пеш мебарад. Дар болои он AI-ёрдамчӣ кор мекунад, ки бемор метавонад бо ӯ сӯҳбат кунад: бо таърихи воқеии гуфтугӯ, ҳисоби арзиши ҳар ҷавоб ва модули алоҳидае, ки нишонаҳои ҳолати фавриро пеш аз ҷавоби модел муайян мекунад. Ин барои клиникаи воқеӣ кор мекунад, на дар реҷаи демо.

### Меъморӣ

- **Бэкенд дар FastAPI**, аз рӯи домен тақсим шудааст: `filials` (филиалҳо), `departments` (шуъбаҳо), `doctors` (бо тахассус, ҷадвал ва набудан), `patients`, `appointments`, `medical_records`, `users`/`auth`
- **Зерсистемаи AI-ёрдамчӣ**, дар бастаи алоҳидаи `app/ai/`:
  - `emergency_guard.py` — қабати муҳофизатие, ки нишонаҳои ҳолати фавриро пеш аз ҷавоби модел муайян мекунад
  - `pricing.py` ва `model_ai_metric.py` — ҳар занги AI бо арзиши он сабт мешавад, истифода шаффоф аст
  - `model_conversation.py` / `crud_conversation.py` — таърихи пурраи гуфтугӯ нигоҳ дошта мешавад
  - `model_ai_feedback.py` — беморон метавонанд ҷавоби ёрдамчиро баҳо диҳанд
- **`model_admin_log.py`** — аудити амалҳои маъмурӣ
- **PostgreSQL** бо миграция тавассути Alembic
- **Хидмати email ва огоҳиномаҳо** барои тасдиқ ва бекории навбат
- **Frontend дар React** (сохта бо Vite)

### Ман шахсан чӣ сохтам

Ман модели додаҳоро тарҳрезӣ кардам ва бэкендро дар FastAPI аз аввал то охир сохтам, аз ҷумла зерсистемаи AI-ёрдамчӣ бо муҳофизати ҳолати фаврӣ ва ҳисоби арзиш, модели домении филиалҳо/шуъбаҳо/ҷадвали духтурон, карти беморон ва раванди навбатгирӣ, инчунин frontend дар React. Инчунин аудити амниятӣ гузаронидам ва масъалаи воқеиро бартараф кардам: сирри JWT бесадо ба қимати пешфарзи сахтгузошта бармегашт, ки ҳоло ислоҳ шудааст.

### Роҳандозӣ

```bash
cd Backend
cp .env.example .env   # сирри воқеиро пур кунед, аз ҷумла JWT_SECRET_KEY-и воқеӣ
docker build -t ometus-backend .
docker run --env-file .env -p 8000:8000 ometus-backend
```

Frontend дар `Frontend/` ҷойгир аст (`npm install && npm run dev`).

### Тамос

Агар ин лоиҳаро барои кор ё фармоиш дида истодаед: [github.com/Magamed-7](https://github.com/Magamed-7) · [teachermaga7@gmail.com](mailto:teachermaga7@gmail.com)
